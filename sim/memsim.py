"""Lane ME (X1000 phase 2): device-aware training with three-terminal electrochemical weights.

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
    name: str = "custom"

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

    def __init__(self, shape, spec: DeviceSpec, alpha: float, gen: torch.Generator, device):
        self.spec, self.alpha, self.gen, self.dev = spec, float(alpha), gen, device
        out_f, in_f = shape
        r = lambda: torch.randn(shape, generator=gen, device=device)
        self.k_nom = 2.0 / spec.n_states
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
        den = self.k_up * gu + self.k_dn * gd
        if gu == 0 and gd == 0:
            # constant-step device: no symmetry point exists (with asymmetry it drifts to a bound); its reference is
            # mid-range (DEVIATIONS.md D1: a reference at the bound let the weight move one way only)
            ustar = torch.zeros_like(self.k_up)
        else:
            ustar = ((self.k_up - self.k_dn) / den.clamp_min(1e-30)).clamp(-1.0, 1.0)
        self.ustar = ustar
        self.g_ref = self.g_of(ustar) + spec.ref_err * r() * (self.gmax - self.gmin) / 2
        self.u = ustar.clone()  # programmed to the reference first (weight 0), then to the init

    def g_of(self, u):
        return self.gmin + (u + 1.0) * 0.5 * (self.gmax - self.gmin)

    def u_of_g(self, g):
        return (2.0 * (g - self.gmin) / (self.gmax - self.gmin) - 1.0)

    def weight(self):
        return self.alpha * (self.g_of(self.u) - self.g_ref)

    def program(self, w_target):
        """Initial programming (closed-loop write-verify, assumed exact up to one step)."""
        g = self.g_ref + w_target / self.alpha
        u = self.u_of_g(g).clamp(-1.0, 1.0)
        if not self.spec.ideal_float:
            u = u + (torch.rand(u.shape, generator=self.gen, device=self.dev) - 0.5) * self.k_nom
        self.u = u.clamp(-1.0, 1.0)

    def apply_pulses(self, n_up, n_dn):
        """Apply n_up up-pulses and n_dn down-pulses (tensors of counts, shape of the tile)."""
        s = self.spec
        u0 = self.u
        A = self.k_up * n_up - self.k_dn * n_dn
        B = self.k_up * s.gamma_up * n_up + self.k_dn * s.gamma_dn * n_dn
        u1 = u0 * torch.exp(-B) + A * _phi(B)
        if s.c2c > 0:
            su = self.k_up * (1 - s.gamma_up * u0).clamp_min(0)
            sd = self.k_dn * (1 + s.gamma_dn * u0).clamp_min(0)
            var = n_up * su * su + n_dn * sd * sd
            u1 = u1 + s.c2c * var.sqrt() * torch.randn(u0.shape, generator=self.gen, device=self.dev)
        self.u = u1.clamp(-1.0, 1.0)

    def drift(self, steps=1.0):
        t = self.spec.tau_steps
        if math.isfinite(t):
            f = math.exp(-steps / t)
            self.u = -1.0 + (self.u + 1.0) * f

    def apply_exact(self, dw):
        """Control arm: exact digital update (ideal_float)."""
        g = self.g_of(self.u) + dw / self.alpha
        self.u = self.u_of_g(g)  # no clamp: ideal float arm has no bounds


@dataclass
class UpdateCfg:
    lr: float = 0.01
    BL: int = 31                   # pulse slots per sample
    algo: str = "sgd"              # sgd | ttv2
    tt_lr_ratio: float = 1.0       # A-array lr / lr
    tt_lambda: float = 0.2         # transfer gain into H (per read)
    tt_period: int = 64            # every column of A is read once per tt_period batches
    tt_gamma: float = 0.0          # forward weight = C + tt_gamma * A
    tt_max_pulses: int = 31        # C pulses per transfer per weight (one pulse train)
    tt_reset: bool = True          # reset the read A columns to their symmetry point after a read


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
        stats["px"] = stats.get("px", 0.0) + float(px.abs().mean(1).sum())
        stats["pd"] = stats.get("pd", 0.0) + float(pd.abs().mean(1).sum())
    n_up = torch.poisson(lam_up, generator=gen)
    n_dn = torch.poisson(lam_dn, generator=gen)
    return n_up, n_dn


class AnalogLinear(torch.nn.Module):
    """y = x W^T + b with W read from device tiles; b digital (fp32 SGD)."""

    def __init__(self, in_f, out_f, spec, ucfg: UpdateCfg, gen, device, bias=True, init_gain=1.0,
                 range_frac=0.4):
        super().__init__()
        self.in_f, self.out_f, self.ucfg, self.gen = in_f, out_f, ucfg, gen
        bound = init_gain * math.sqrt(3.0 / in_f)
        alpha = bound / range_frac  # init occupies +-range_frac of the device range
        w0 = (torch.rand((out_f, in_f), generator=gen, device=device) * 2 - 1) * bound
        self.C = Tile((out_f, in_f), spec, alpha, gen, device)
        self.C.program(w0)
        self.A = None
        if ucfg.algo == "ttv2":
            self.A = Tile((out_f, in_f), spec, alpha, gen, device)
            self.A.program(torch.zeros_like(w0))
            self.H = torch.zeros((out_f, in_f), device=device)
            self.col_ptr = 0
        self.bias = torch.zeros(out_f, device=device) if bias else None
        self._x = None
        self._d = None
        self.n_pulses = 0.0  # total device pulses applied (C and A)
        self.stats = {}  # px, pd: sums over rows of the mean slot probability per row / column line

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
        if tgt.spec.ideal_float:
            tgt.apply_exact(-lr_t * (d.t() @ x))
        else:
            n_up, n_dn = pulse_counts(x, d, lr_t / tgt.alpha, tgt.k_nom, u.BL, self.gen, self.stats)
            tgt.apply_pulses(n_up, n_dn)
            self.n_pulses += float(n_up.sum() + n_dn.sum())
        if self.A is not None:
            self._transfer()
        self._x = self._d = None

    @torch.no_grad()
    def _transfer(self):
        """TTv2 (Gokmen 2021): read columns of A, accumulate lambda * A_col in the digital buffer H
        (in units of C's nominal pulse), fire up to tt_max_pulses pulses into C where |H| >= 1."""
        u = self.ucfg
        ncols = max(1, math.ceil(self.in_f / u.tt_period))
        idx = torch.arange(self.col_ptr, self.col_ptr + ncols, device=self.H.device) % self.in_f
        self.col_ptr = int((self.col_ptr + ncols) % self.in_f)
        wA = self.A.weight()[:, idx]
        self.H[:, idx] += u.tt_lambda * wA / (self.C.alpha * self.C.k_nom)
        if u.tt_reset:
            # reset by alternating pulses: lands on the device's symmetry point (its read zero is off by
            # the reference error), with one pulse of write noise
            us = self.A.ustar[:, idx]
            if not self.A.spec.ideal_float:
                us = us + self.A.spec.c2c * self.A.k_nom * torch.randn(us.shape, generator=self.gen, device=us.device)
            self.A.u[:, idx] = us.clamp(-1.0, 1.0)
            self.n_pulses += float(us.numel()) * 2 * u.BL  # reset cost: one up and one down train
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
                self.n_pulses += float(n.abs().sum())
            self.H[:, idx] = h - n

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
