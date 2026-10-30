"""REVISION (lane ME-REVISE, 2026-10-26): copied from paper/sim/memsim.py (commit ef7e0630f, unchanged there) and repaired
after the independent review (RESPONSE-TO-REVIEW.md). Every legacy behaviour stays selectable and is the default, so an old
record replays bit for bit (sim/test_rev.py); the repaired runs select the new behaviour explicitly and record it:
  - random streams: Streams (split mode) gives the logical init, the data order, each tile's device population and the
    pulse/noise draws their own generators; mode 'legacy' is the original single shared generator;
  - the A reset (UpdateCfg.tt_reset): 'ideal' (= True, the original jump to the symmetry point, charged 2 BL pulses: labelled
    IDEAL RESET), 'alt' (BL alternating up/down pulse pairs applied through the device dynamics), 'pulse' (sign-directed
    pulse trains from the transfer read toward the read zero, re-read and corrected tt_reset_iters times in all, at most
    tt_reset_max pulses, through the device dynamics),
    'none' (= False); 'alt' and 'pulse' charge exactly the pulses they apply;
  - published-style TTv2 option: tt_h_forget (a buffer element that fired is zeroed, the aihwkit forget_buffer default);
  - DeviceSpec.bounds_model 'aihwkit': the LinearStepDevice of aihwkit (shifted hard bounds u_lo/u_hi with relative
    spread, slopes scaled by the mean bounds, absolute slope spread gamma_*_dtod, additive step spread, unit gain);
  - pulse_counts clipping statistics (calls whose pre-clamp probability exceeded 1, lost update fraction), no device sync.

Paper lane ME-PAPER: derived from lane ME's memsim.py by paper/sim/derive_memsim.py (anchors named there).
Adds: per-device spread of the saturation (gamma_d2d), a fixed weight scale (alpha), Tiki-Taka v1 (Gokmen and
Haensch 2020), chopped TTv2 and AGAD (Rasch et al. 2024). The SGD and TTv2 paths are unchanged (checked bit for bit).

Lane ME (X1000 phase 2): device-aware training with three-terminal electrochemical weights.

Own code, torch only, no aihwkit. Every analog weight update goes through a device model:
a limited number of levels (pulse step 2/n_states over the nominal range), an up/down step
asymmetry, a weight-dependent (saturating) step, cycle-to-cycle write noise, device-to-device
spread, a symmetry-point reference with calibration error, and drift (relaxation toward the
bare state). Forward and backward passes are ideal digital reads (fp32): the lane's question is
the UPDATE, and read/ADC noise is out of scope (PLAN.md).

Units. Each device has a normalised state u in [-1, 1] (its own bounds). One nominal pulse moves
u by k = 2/n_states at mid-range. Conductance g = gmin + (u+1)/2 (gmax-gmin), gmin/gmax spread per
device; the weight read is w = alpha * (g - g_ref), g_ref = g(u*) + calibration error, u* the
device's symmetry point (where an up and a down pulse cancel).

Update (RPU stochastic-pulse scheme, Gokmen and Vlasov 2016): for a batch of samples (rows of x
and of the back-propagated error d), each sample fires up to BL pulse slots; a weight receives a
coincidence with probability p_x,i * p_d,j per slot. The up count of weight ij is the sum over
samples whose x_i*d_j < 0 (descent direction positive), the down count the sum over the others;
both are applied (asymmetry is never cancelled digitally). Counts are drawn as Poisson with the
requested mean. This is a surrogate, not a pulse-by-pulse simulation: the mean is exact only while no
slot probability clips, and per-cell draws ignore the correlations of shared row and column pulse
streams, so the larger variance is not claimed to be conservative (the paper, Section 3.2; its update
probes compare the surrogate with literal pulse streams). Up and down pulses of one batch are applied
as uniformly interleaved:
du/ds = A - B u over s in [0, 1] is solved exactly (A, B below).
"""
import math
from dataclasses import dataclass, field, asdict

import torch


@dataclass
class DeviceSpec:
    n_states: float = 1e9          # levels over the nominal range (range / mid-range step)
    asym: float = 0.0              # global up/down step asymmetry: up = k(1+a/2), down = k(1-a/2)
    asym_d2d: float = 0.0          # device-to-device spread (std) of asym
    gamma_up: float = 0.0          # saturation: up step = k_up (1 - gamma_up u)
    gamma_dn: float = 0.0          # down step = k_dn (1 + gamma_dn u)
    c2c: float = 0.0               # cycle-to-cycle write noise: std per pulse / mean step
    d2d: float = 0.0               # device-to-device spread (std) of the step size
    bound_d2d: float = 0.0         # device-to-device spread of gmin, gmax
    tau_steps: float = math.inf    # drift: relaxation time (training steps) toward u = -1 (bare)
    ref_err: float = 0.0           # symmetry-point reference calibration error (std, in u units)
    ideal_float: bool = False      # bypass the device: w += exact digital update (control arm)
    gamma_d2d: float = 0.0         # device-to-device spread (relative std) of gamma_up and gamma_dn, drawn independently
    name: str = "custom"
    # REVISION: the aihwkit LinearStepDevice parameterisation (bounds_model "aihwkit"); ignored by "paper"
    bounds_model: str = "paper"    # paper | aihwkit
    u_lo: float = -1.0             # mean lower hard bound (aihwkit w_min)
    u_hi: float = 1.0              # mean upper hard bound (aihwkit w_max)
    gamma_up_dtod: float = 0.0     # absolute std of gamma_up across devices (aihwkit gamma_up_dtod)
    gamma_dn_dtod: float = 0.0     # absolute std of gamma_dn across devices (aihwkit gamma_down_dtod)
    recenter_sp: bool = False      # paper model: re-centre each device's range on its symmetry point (fixed-SP sweeps)

    def as_dict(self):
        d = asdict(self)
        for kk, v in d.items():
            if isinstance(v, float) and math.isinf(v):
                d[kk] = "inf"
        return d


def _phi(B):
    # (1 - exp(-B)) / B, stable at B -> 0
    small = B < 1e-6
    Bs = torch.where(small, torch.ones_like(B), B)
    return torch.where(small, 1.0 - 0.5 * B, -torch.expm1(-Bs) / Bs)


class Tile:
    """One crossbar of devices holding an (out, in) weight matrix."""

    def __init__(self, shape, spec: DeviceSpec, alpha: float, gen: torch.Generator, device, ngen=None):
        # gen: this tile's device population (and programming error); ngen: the cycle-to-cycle write noise.
        # Legacy: one shared generator for both (ngen None).
        self.spec, self.alpha, self.gen, self.dev = spec, float(alpha), gen, device
        self.ngen = gen if ngen is None else ngen
        out_f, in_f = shape
        r = lambda: torch.randn(shape, generator=gen, device=device)
        self.k_nom = 2.0 / spec.n_states
        self.aihw = spec.bounds_model == "aihwkit"
        if self.aihw:
            self._init_aihwkit(r)
            return
        self.lo, self.hi = -1.0, 1.0
        step = (1.0 + spec.d2d * r()).clamp_min(0.1)
        a = spec.asym + spec.asym_d2d * r()
        self.k_up = self.k_nom * step * (1.0 + a / 2)
        self.k_dn = self.k_nom * step * (1.0 - a / 2)
        self.k_up.clamp_(min=1e-12)
        self.k_dn.clamp_(min=1e-12)
        self.gmax = 1.0 + spec.bound_d2d * r()
        self.gmin = -1.0 + spec.bound_d2d * r()
        bad = self.gmax - self.gmin < 0.2
        self.gmax = torch.where(bad, self.gmin + 0.2, self.gmax)
        gu, gd = spec.gamma_up, spec.gamma_dn
        if spec.gamma_d2d > 0:  # per-device saturation slopes (the RPU-baseline model of Gokmen and Haensch 2020)
            gu = (gu * (1.0 + spec.gamma_d2d * r())).clamp_min(0.0)
            gd = (gd * (1.0 + spec.gamma_d2d * r())).clamp_min(0.0)
        self.gu, self.gd = gu, gd
        den = self.k_up * gu + self.k_dn * gd
        if spec.gamma_up == 0 and spec.gamma_dn == 0:
            # constant-step device: no symmetry point exists (with asymmetry it drifts to a bound); its reference is
            # mid-range (DEVIATIONS.md D1: a reference at the bound let the weight move one way only)
            ustar = torch.zeros_like(self.k_up)
        else:
            ustar = ((self.k_up - self.k_dn) / den.clamp_min(1e-30)).clamp(-1.0, 1.0)
            if spec.recenter_sp:
                # REVISION: re-centre the state range on each device's symmetry point (c = -u*): the same up/down
                # dynamics about u*, with the full signed range kept, so asymmetry is not confounded with range loss
                us0 = (self.k_up - self.k_dn) / den.clamp_min(1e-30)
                f_up = (1.0 - gu * us0).clamp_min(0.05)
                f_dn = (1.0 + gd * us0).clamp_min(0.05)
                self.k_up, self.k_dn = self.k_up * f_up, self.k_dn * f_dn
                self.gu, self.gd = gu / f_up, gd / f_dn
                ustar = torch.zeros_like(self.k_up)
        self.ustar = ustar
        self.g_ref = self.g_of(ustar) + spec.ref_err * r() * (self.gmax - self.gmin) / 2
        self.u = ustar.clone()  # programmed to the reference first (weight 0), then to the init

    def _init_aihwkit(self, r):
        """aihwkit LinearStepDevice (presets EcRamPresetDevice, EcRamMOPresetDevice; mean_bound_reference, mult_noise):
        up step k (1 + b + s xi)(1 - g_up w / w_max), down k (1 - b + s xi)(1 + g_dn w / |w_min|), b = up_down + dtod xi',
        g_up = |gamma_up + gamma_up_dtod xi|, hard bounds w_max (1 + w_max_dtod xi), w_min (1 + w_min_dtod xi), weight = state."""
        s = self.spec
        step = 1.0 + s.d2d * r()
        b = s.asym / 2 + (s.asym_d2d / 2) * r()  # asym_d2d = 2 up_down_dtod (DeviceSpec convention up = k(1 + a/2))
        self.k_up = (self.k_nom * (step + b)).clamp_(min=1e-12)
        self.k_dn = (self.k_nom * (step - b)).clamp_(min=1e-12)
        self.hi = s.u_hi * (1.0 + s.bound_d2d * r())
        self.lo = s.u_lo * (1.0 + s.bound_d2d * r())
        bad = self.hi - self.lo < 0.2
        self.hi = torch.where(bad, self.lo + 0.2, self.hi)
        self.gmin, self.gmax = self.lo, self.hi
        self.gu = (s.gamma_up + s.gamma_up_dtod * r()).abs() / s.u_hi
        self.gd = (s.gamma_dn + s.gamma_dn_dtod * r()).abs() / abs(s.u_lo)
        den = self.k_up * self.gu + self.k_dn * self.gd
        if s.gamma_up == 0 and s.gamma_dn == 0 and s.gamma_up_dtod == 0 and s.gamma_dn_dtod == 0:
            ustar = torch.zeros_like(self.k_up)
        else:
            ustar = torch.max(torch.min((self.k_up - self.k_dn) / den.clamp_min(1e-30), self.hi), self.lo)
        self.ustar = ustar
        self.g_ref = ustar + s.ref_err * r() * (self.hi - self.lo) / 2
        self.u = ustar.clone()

    def clip(self, u):
        if self.aihw:
            return torch.max(torch.min(u, self.hi), self.lo)
        return u.clamp(-1.0, 1.0)

    def clip_cols(self, u, idx):
        """clip() for the columns idx only (u holds just those columns; review 8: clip() against the whole tile's bounds failed)"""
        if self.aihw:
            return torch.max(torch.min(u, self.hi[:, idx]), self.lo[:, idx])
        return u.clamp(-1.0, 1.0)

    def g_of(self, u):
        if self.aihw:
            return u
        return self.gmin + (u + 1.0) * 0.5 * (self.gmax - self.gmin)

    def u_of_g(self, g):
        if self.aihw:
            return g
        return (2.0 * (g - self.gmin) / (self.gmax - self.gmin) - 1.0)

    def weight(self):
        return self.alpha * (self.g_of(self.u) - self.g_ref)

    def program(self, w_target):
        """Initial programming (closed-loop write-verify, assumed exact up to one step)."""
        g = self.g_ref + w_target / self.alpha
        u = self.clip(self.u_of_g(g))
        if not self.spec.ideal_float:
            u = u + (torch.rand(u.shape, generator=self.gen, device=self.dev) - 0.5) * self.k_nom
        self.u = self.clip(u)

    def _step(self, u0, n_up, n_dn, k_up, k_dn, gu, gd):
        s = self.spec
        A = k_up * n_up - k_dn * n_dn
        B = k_up * gu * n_up + k_dn * gd * n_dn
        u1 = u0 * torch.exp(-B) + A * _phi(B)
        if s.c2c > 0:
            su = k_up * (1 - gu * u0).clamp_min(0)
            sd = k_dn * (1 + gd * u0).clamp_min(0)
            var = n_up * su * su + n_dn * sd * sd
            u1 = u1 + s.c2c * var.sqrt() * torch.randn(u0.shape, generator=self.ngen, device=self.dev)
        return u1

    def apply_pulses(self, n_up, n_dn):
        """Apply n_up up-pulses and n_dn down-pulses (tensors of counts, shape of the tile)."""
        self.u = self.clip(self._step(self.u, n_up, n_dn, self.k_up, self.k_dn, self.gu, self.gd))

    def apply_pulses_cols(self, idx, n_up, n_dn):
        """REVISION: the same device dynamics on the columns idx only (n_up, n_dn of shape (out, len(idx)))."""
        col = lambda t: t[:, idx] if torch.is_tensor(t) and t.dim() == 2 else t
        u1 = self._step(self.u[:, idx], n_up, n_dn, col(self.k_up), col(self.k_dn), col(self.gu), col(self.gd))
        if self.aihw:
            u1 = torch.max(torch.min(u1, self.hi[:, idx]), self.lo[:, idx])
        else:
            u1 = u1.clamp(-1.0, 1.0)
        self.u[:, idx] = u1

    def drift(self, steps=1.0):
        t = self.spec.tau_steps
        if math.isfinite(t):
            f = math.exp(-steps / t)
            self.u = self.lo + (self.u - self.lo) * f if self.aihw else -1.0 + (self.u + 1.0) * f

    def apply_exact(self, dw):
        """Control arm: exact digital update (ideal_float)."""
        g = self.g_of(self.u) + dw / self.alpha
        self.u = self.u_of_g(g)  # no clamp: ideal float arm has no bounds


@dataclass
class UpdateCfg:
    lr: float = 0.01
    BL: int = 31                   # pulse slots per sample
    algo: str = "sgd"              # sgd | ttv1 | ttv2 | cttv2 | agad
    tt_lr_ratio: float = 1.0       # A-array lr / lr
    tt_lambda: float = 0.2         # transfer gain into H (per read)
    tt_period: int = 64            # every column of A is read once per tt_period batches
    tt_gamma: float = 0.0          # forward weight = C + tt_gamma * A
    tt_max_pulses: int = 31        # C pulses per transfer per weight (one pulse train)
    tt_reset: bool = True          # reset the read A columns to their symmetry point after a read
    tt_cols: int = 0               # columns of A read per batch (0: ceil(in / tt_period)); TTv1 with ns = 1: the batch size
    tt_rho: float = 0.1            # chopper flip probability per read (cttv2, agad)
    agad_beta: float = 0.5         # AGAD leaky average of the A reads (1: the last read only)
    # REVISION. tt_reset also takes "ideal" (= True: IDEAL RESET), "alt", "pulse", "none" (= False); see the module doc.
    tt_reset_max: int = 62         # "pulse": at most this many pulses per weight per reset (2 BL, the old charged budget)
    tt_reset_iters: int = 2        # "pulse": read-correct iterations (each after the first costs one extra read of the columns)
    tt_h_forget: bool = False      # published-style TTv2: zero a buffer element after it fired (else keep the remainder)


def reset_mode(v):
    if v is True or v == "ideal":
        return "ideal"
    if v is False or v in ("none", None):
        return "none"
    if v in ("alt", "pulse"):
        return v
    raise ValueError(f"tt_reset {v!r}")


def pulse_counts(x, d, lr, k_nom, BL, gen, stats=None):
    """x: (M, in), d: (M, out) error (dL/dy, summed loss). Descent: dw = -lr * d^T x (in weight units of
    the tile divided by alpha, done by the caller). Returns expected-mean Poisson counts n_up, n_dn (out, in).
    Update management: per batch, scale the x and d streams equally so the largest single-sample
    coincidence probability per slot is <= 1 and the mean pulse number matches lr / k_nom."""
    # target expected pulses for weight ij: (lr / k_nom) * sum_b |x_bi d_bj|, split by sign
    eta = lr / k_nom
    mx = x.abs().max().clamp_min(1e-12)
    md = d.abs().max().clamp_min(1e-12)
    # p_x = cx |x|, p_d = cd |d|, BL cx cd = eta; balance cx mx = cd md (Gokmen update management)
    c = math.sqrt(eta / BL)
    cx = c * torch.sqrt(md / mx)
    cd = c * torch.sqrt(mx / md)
    px = (cx * x).clamp(-1.0, 1.0)
    pd = (cd * d).clamp(-1.0, 1.0)
    xp, xn = px.clamp_min(0), (-px).clamp_min(0)
    dp, dn = pd.clamp_min(0), (-pd).clamp_min(0)
    # descent direction: dw_ij proportional to -d_j x_i: up when x_i d_j < 0
    lam_up = BL * (dn.t() @ xp + dp.t() @ xn)
    lam_dn = BL * (dp.t() @ xp + dn.t() @ xn)
    if stats is not None:  # slot occupancy per line per sample (energy model input)
        stats["px"] = stats.get("px", 0.0) + px.abs().mean(1).sum()
        stats["pd"] = stats.get("pd", 0.0) + pd.abs().mean(1).sum()
        if stats.get("_clip", False):  # REVISION: clipping (no device sync; row/column sums, no extra matmul)
            pmax = c * torch.sqrt(mx * md)  # the largest pre-clamp probability (equal on both streams after balancing)
            want = eta * (d.abs().sum(1) * x.abs().sum(1)).sum()  # sum_ij of the requested mean |pulses|
            got = BL * (pd.abs().sum(1) * px.abs().sum(1)).sum()
            stats["clip_calls"] = stats.get("clip_calls", 0.0) + (pmax > 1.0).float()
            stats["calls"] = stats.get("calls", 0.0) + 1.0
            stats["want"] = stats.get("want", 0.0) + want
            stats["got"] = stats.get("got", 0.0) + got
    n_up = torch.poisson(lam_up, generator=gen)
    n_dn = torch.poisson(lam_dn, generator=gen)
    return n_up, n_dn


class Streams:
    """REVISION: independent random streams per seed. 'split': init (logical weights, in layer order), data (sample order,
    LM windows), noise (pulse counts, write noise, reset noise, chopper flips), and one generator per (layer, tile) for the
    device population and programming error, so every arm of a seed gets the same logical init and data order, and one
    device gets the same population whatever the algorithm. 'legacy': the original single shared generator."""

    IDS = {"init": 1, "data": 2, "noise": 3, "tile": 4}

    def __init__(self, seed, mode="split", device=None):
        self.seed, self.mode, self.device = int(seed), mode, device
        self.layer = 0
        if mode == "legacy":
            g = torch.Generator(device=device).manual_seed(int(seed))
            self.init = self.data = self.noise = g
        elif mode == "split":
            self.init, self.data, self.noise = (self._g(self.IDS[k]) for k in ("init", "data", "noise"))
        else:
            raise ValueError(mode)
        self.init_log = []  # logical initial weights per layer (hashed by the runner)

    def _g(self, *key):
        h = self.seed
        for k in key:
            h = (h * 1_000_003 + 7919 * (k + 1)) % (2 ** 61 - 1)
        return torch.Generator(device=self.device).manual_seed(h)

    def tile(self, layer, role):
        if self.mode == "legacy":
            return self.init
        return self._g(self.IDS["tile"], layer, {"C": 0, "A": 1}[role])

    def next_layer(self):
        self.layer += 1
        return self.layer - 1


class AnalogLinear(torch.nn.Module):
    """y = x W^T + b with W read from device tiles; b digital (fp32 SGD)."""

    def __init__(self, in_f, out_f, spec, ucfg: UpdateCfg, gen, device, bias=True, init_gain=1.0,
                 range_frac=0.4, alpha=None, streams=None):
        super().__init__()
        if streams is None:  # legacy call: one shared generator
            streams = Streams.__new__(Streams)
            streams.mode, streams.init, streams.data, streams.noise, streams.layer, streams.init_log = \
                "legacy", gen, gen, gen, 0, []
        gen = streams.noise
        self.in_f, self.out_f, self.ucfg, self.gen = in_f, out_f, ucfg, gen
        li = streams.next_layer()
        split = streams.mode == "split"
        bound = init_gain * math.sqrt(3.0 / in_f)
        alpha = bound / range_frac if alpha is None else float(alpha)  # init at +-range_frac of the range unless fixed
        w0 = (torch.rand((out_f, in_f), generator=streams.init, device=device) * 2 - 1) * bound
        streams.init_log.append(w0)
        self.C = Tile((out_f, in_f), spec, alpha, streams.tile(li, "C"), device, ngen=gen if split else None)
        self.C.program(w0)
        self.A = None
        self.chop = None
        self.reset = reset_mode(ucfg.tt_reset)
        self.n_reset_pulses = 0.0  # pulses applied (or charged, ideal) by A resets
        self.reset_resid = 0.0     # sum over reset weights of |A read after the reset| in C nominal steps
        self.n_reset = 0.0
        self.n_reset_reads = 0.0   # extra column reads by the 'pulse' reset (beyond the transfer's own read)
        if ucfg.algo in ("ttv1", "ttv2", "cttv2", "agad"):
            self.A = Tile((out_f, in_f), spec, alpha, streams.tile(li, "A"), device, ngen=gen if split else None)
            self.A.program(torch.zeros_like(w0))
            self.H = torch.zeros((out_f, in_f), device=device)
            self.col_ptr = 0
        if ucfg.algo in ("cttv2", "agad"):
            self.chop = torch.ones(in_f, device=device)  # chopper signs c_j on the inputs (Rasch et al. 2024)
        if ucfg.algo == "agad":
            self.P = torch.zeros((out_f, in_f), device=device)     # leaky average of the A reads
            self.Pref = torch.zeros((out_f, in_f), device=device)  # the reference, set from P at a chopper flip
        self.bias = torch.zeros(out_f, device=device) if bias else None
        self._x = None
        self._d = None
        self.n_pulses = 0.0  # total device pulses applied (C and A)
        self.stats = {"_clip": True}  # px, pd: sums over rows of the mean slot probability per row / column line; REVISION: clipping

    def weight(self):
        w = self.C.weight()
        if self.A is not None and self.ucfg.tt_gamma != 0:
            w = w + self.ucfg.tt_gamma * self.A.weight()
        return w

    def forward(self, x):
        shp = x.shape
        x2 = x.reshape(-1, shp[-1])
        W = self.weight()
        x2c = x2.detach()
        y = x2 @ W.t()
        if self.bias is not None:
            y = y + self.bias
        if torch.is_grad_enabled() and y.requires_grad:
            self._x = x2c
            y.register_hook(self._save_d)
        elif torch.is_grad_enabled():
            # input does not require grad (first layer): attach a leaf to catch the output grad
            y = y.requires_grad_(True)
            self._x = x2c
            y.register_hook(self._save_d)
        return y.reshape(*shp[:-1], self.out_f)

    def _save_d(self, g):
        self._d = g.detach()

    @torch.no_grad()
    def update(self):
        x, d, u = self._x, self._d, self.ucfg
        if x is None or d is None:
            return
        if self.bias is not None:
            self.bias -= u.lr * d.sum(0)
        tgt = self.A if self.A is not None else self.C
        lr_t = u.lr * (u.tt_lr_ratio if self.A is not None else 1.0)
        if self.chop is not None:
            x = x * self.chop  # modulate the inputs: the A update sees c * x
        if tgt.spec.ideal_float:
            tgt.apply_exact(-lr_t * (d.t() @ x))
        else:
            n_up, n_dn = pulse_counts(x, d, lr_t / tgt.alpha, tgt.k_nom, u.BL, self.gen, self.stats)
            tgt.apply_pulses(n_up, n_dn)
            self.n_pulses = self.n_pulses + (n_up.sum() + n_dn.sum())
        if self.A is not None:
            self._transfer()
        self._x = self._d = None

    @torch.no_grad()
    def _transfer(self):
        """TTv2 (Gokmen 2021): read columns of A, accumulate lambda * A_col in the digital buffer H
        (in units of C's nominal pulse), fire up to tt_max_pulses pulses into C where |H| >= 1."""
        u = self.ucfg
        ncols = max(1, math.ceil(self.in_f / u.tt_period)) if u.tt_cols <= 0 else min(self.in_f, u.tt_cols)
        idx = torch.arange(self.col_ptr, self.col_ptr + ncols, device=self.H.device) % self.in_f
        self.col_ptr = int((self.col_ptr + ncols) % self.in_f)
        if u.algo == "ttv1":
            return self._transfer_v1(idx)
        wA = self.A.weight()[:, idx]
        z = wA
        if u.algo == "agad":  # dynamic reference: z = c (w_A - p_ref); p <- (1 - beta) p + beta w_A
            z = wA - self.Pref[:, idx]
            self.P[:, idx] = (1.0 - u.agad_beta) * self.P[:, idx] + u.agad_beta * wA
        if self.chop is not None:
            z = z * self.chop[idx]  # demodulate with the column's chopper sign
        self.H[:, idx] += u.tt_lambda * z / (self.C.alpha * self.C.k_nom)
        if self.reset == "ideal":
            # IDEAL RESET (the original): jumps to the device's symmetry point (its read zero is off by the reference
            # error), with one pulse of write noise, and is CHARGED 2 BL pulses that it does not apply
            us = self.A.ustar[:, idx]
            if not self.A.spec.ideal_float:
                us = us + self.A.spec.c2c * self.A.k_nom * torch.randn(us.shape, generator=self.gen, device=us.device)
            self.A.u[:, idx] = self.A.clip_cols(us, idx)
            self.n_pulses += float(us.numel()) * 2 * u.BL  # reset cost: one up and one down train
            self.n_reset_pulses += float(us.numel()) * 2 * u.BL
        elif self.reset in ("alt", "pulse"):
            self._reset_pulsed(idx, wA)
        h = self.H[:, idx]
        n = torch.trunc(h).clamp(-u.tt_max_pulses, u.tt_max_pulses)
        if bool((n != 0).any()):
            if self.C.spec.ideal_float:
                full = torch.zeros_like(self.H)
                full[:, idx] = n * self.C.alpha * self.C.k_nom
                self.C.apply_exact(full)
            else:
                n_up = torch.zeros_like(self.H)
                n_dn = torch.zeros_like(self.H)
                n_up[:, idx] = n.clamp_min(0)
                n_dn[:, idx] = (-n).clamp_min(0)
                # C pulses only touch the read columns; apply on the whole tile (zero counts elsewhere)
                self.C.apply_pulses(n_up, n_dn)
                self.n_pulses = self.n_pulses + n.abs().sum()
            if u.tt_h_forget:  # published-style: a buffer element that fired is forgotten
                self.H[:, idx] = torch.where(n != 0, torch.zeros_like(h), h)
            else:
                self.H[:, idx] = h - n
        if self.chop is not None:  # flip each read column's chopper with probability rho
            flip = torch.rand(idx.shape, generator=self.gen, device=idx.device) < u.tt_rho
            c = self.chop[idx]
            self.chop[idx] = torch.where(flip, -c, c)
            if u.algo == "agad":
                self.Pref[:, idx] = torch.where(flip[None, :], self.P[:, idx], self.Pref[:, idx])

    @torch.no_grad()
    def _reset_pulsed(self, idx, wA):
        """REVISION: a reset made of pulses that go through the device dynamics and are charged as applied.
        'alt': BL up and BL down pulses, uniformly interleaved (zero-shifting: converges to the symmetry point at the rate
        exp(-(k_up g_up + k_dn g_dn)) per pair). 'pulse': from the transfer's own read wA (relative to the reference), one
        sign-directed train of round(|wA| / (alpha k_nom)) pulses toward the read zero, re-read and corrected up to
        tt_reset_iters times in all, at most tt_reset_max pulses in all; the nominal
        step is assumed, so the state-dependent step, the device's own step and write noise leave a residual."""
        u, A = self.ucfg, self.A
        if A.spec.ideal_float:  # a digital A: the reset is exact and free
            A.u[:, idx] = A.u_of_g(A.g_ref)[:, idx]
            return
        if self.reset == "alt":
            n_up = torch.full_like(wA, float(u.BL))
            A.apply_pulses_cols(idx, n_up, n_up)
            cnt = 2.0 * n_up.sum()
        else:
            cnt, left, r = 0.0, torch.full_like(wA, float(u.tt_reset_max)), wA
            for it in range(max(1, u.tt_reset_iters)):  # read-correct iterations (the first read is the transfer's)
                if it > 0:
                    r = A.weight()[:, idx]
                    self.n_reset_reads += float(r.numel())
                n = torch.round(r / (A.alpha * A.k_nom))
                n = torch.max(torch.min(n, left), -left)
                n_dn = n.clamp_min(0)     # a positive read needs down pulses
                n_up = (-n).clamp_min(0)
                A.apply_pulses_cols(idx, n_up, n_dn)
                left = left - n.abs()
                cnt = cnt + n.abs().sum()
        self.n_pulses = self.n_pulses + cnt
        self.n_reset_pulses = self.n_reset_pulses + cnt
        self.reset_resid = self.reset_resid + (A.weight()[:, idx].abs() / (A.alpha * A.k_nom)).sum()
        self.n_reset += float(wA.numel())

    @torch.no_grad()
    def _transfer_v1(self, idx):
        """Tiki-Taka v1 (Gokmen and Haensch 2020): read columns j of A and add tt_lambda * A[:, j] to C[:, j] by a pulsed
        outer product with the one-hot input e_j (no digital buffer; A is not reset); forward weight C + tt_gamma A."""
        u = self.ucfg
        v = self.A.weight()[:, idx]  # (out, ncols)
        X = torch.zeros((idx.numel(), self.in_f), device=v.device)
        X[torch.arange(idx.numel(), device=v.device), idx] = 1.0
        if self.C.spec.ideal_float:
            self.C.apply_exact(u.tt_lambda * (v @ X))
        else:  # pulse_counts descends (dw = -lr d^T x), so d = -v^T gives dw = +lr v e_j^T
            n_up, n_dn = pulse_counts(X, -v.t(), u.tt_lambda / self.C.alpha, self.C.k_nom, u.BL, self.gen)
            self.C.apply_pulses(n_up, n_dn)
            self.n_pulses = self.n_pulses + (n_up.sum() + n_dn.sum())

    @torch.no_grad()
    def drift(self, steps=1.0):
        self.C.drift(steps)
        if self.A is not None:
            self.A.drift(steps)


def analog_layers(model):
    return [m for m in model.modules() if isinstance(m, AnalogLinear)]


def step_update(model, digital_params, lr):
    with torch.no_grad():
        for m in analog_layers(model):
            m.update()
            m.drift(1.0)
        for p in digital_params:
            if p.grad is not None:
                p -= lr * p.grad
                p.grad = None
