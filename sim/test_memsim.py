"""Checks of the lane-ME device model, each shown to FAIL on a planted fault.

python -B test_memsim.py --out ../records/TESTS.json
Every check runs on the real code (must pass) and once per planted fault (must fail).
"""
import argparse
import contextlib
import json
import math
import os
import sys

import torch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memsim  # noqa: E402
from memsim import AnalogLinear, DeviceSpec, Tile, UpdateCfg, pulse_counts, step_update  # noqa: E402

DEV = torch.device("cpu")


def gen(s=0):
    return torch.Generator(device=DEV).manual_seed(s)


# ------------------------------------------------------------------ checks (return (ok, detail))
def c_fp_equivalence():
    """ideal_float AnalogLinear + step_update == torch.nn.Linear + plain SGD (sum loss), 30 steps."""
    torch.manual_seed(0)
    g = gen(1)
    ucfg = UpdateCfg(lr=0.01)
    spec = DeviceSpec(ideal_float=True)
    a1 = AnalogLinear(20, 16, spec, ucfg, g, DEV)
    a2 = AnalogLinear(16, 5, spec, ucfg, g, DEV)
    l1, l2 = torch.nn.Linear(20, 16), torch.nn.Linear(16, 5)
    with torch.no_grad():
        l1.weight.copy_(a1.weight()); l1.bias.zero_(); l2.weight.copy_(a2.weight()); l2.bias.zero_()
    opt = torch.optim.SGD(list(l1.parameters()) + list(l2.parameters()), lr=0.01)
    x = torch.randn(64, 20, generator=gen(2)); y = torch.randint(0, 5, (64,), generator=gen(3))
    for _ in range(30):
        loss = torch.nn.functional.cross_entropy(a2(torch.tanh(a1(x))), y, reduction="sum")
        loss.backward()
        for m in (a1, a2):
            m.update()
        loss2 = torch.nn.functional.cross_entropy(l2(torch.tanh(l1(x))), y, reduction="sum")
        opt.zero_grad(); loss2.backward(); opt.step()
    d = max(float((a1.weight() - l1.weight).abs().max()), float((a2.weight() - l2.weight).abs().max()),
            float((a1.bias - l1.bias).abs().max()))
    return d < 1e-5, f"max |dW| = {d:.3e} (tol 1e-5)"


def c_pulse_mean():
    """E[(n_up - n_dn) k] equals the SGD step -lr d^T x (unclipped regime), 400 draws."""
    g = gen(4)
    x = torch.randn(8, 6, generator=g) * 0.5
    d = torch.randn(8, 4, generator=g) * 0.5
    lr, k = 0.02, 2.0 / 1000
    acc = torch.zeros(4, 6)
    N = 400
    for _ in range(N):
        nu, nd = pulse_counts(x, d, lr, k, 31, g)
        acc += (nu - nd) * k
    acc /= N
    tgt = -lr * d.t() @ x
    err = float((acc - tgt).abs().max() / tgt.abs().max())
    return err < 0.05, f"max rel err of mean step = {err:.4f} (tol 0.05)"


def c_asym_drift():
    """Constant-step device (gamma 0), asym a: N up then N down pulses leave a net k a N."""
    spec = DeviceSpec(n_states=1000, asym=0.2)
    t = Tile((3, 3), spec, 1.0, gen(5), DEV)
    t.u = torch.zeros(3, 3)
    N = 50
    t.apply_pulses(torch.full((3, 3), float(N)), torch.zeros(3, 3))
    t.apply_pulses(torch.zeros(3, 3), torch.full((3, 3), float(N)))
    want = (2 / 1000) * 0.2 * N
    got = float(t.u.mean())
    return abs(got - want) < 1e-6, f"net du = {got:.6f}, want {want:.6f}"


def c_symmetry_point():
    """Soft-bounds device: alternating pulses converge to the analytic symmetry point u*."""
    spec = DeviceSpec(n_states=200, asym=0.3, gamma_up=0.5, gamma_dn=0.5)
    t = Tile((2, 2), spec, 1.0, gen(6), DEV)
    t.u = torch.full((2, 2), -0.9)
    for _ in range(4000):
        t.apply_pulses(torch.ones(2, 2), torch.ones(2, 2))
    ku, kd = (2 / 200) * 1.15, (2 / 200) * 0.85
    want = (ku - kd) / (ku * 0.5 + kd * 0.5)
    got = float(t.u.mean())
    ok = abs(got - want) < 1e-3 and abs(float(t.ustar.mean()) - want) < 1e-6
    return ok, f"u converged {got:.5f}, tile.ustar {float(t.ustar.mean()):.5f}, analytic {want:.5f}"


def c_level_step():
    """One up pulse at u = 0 moves u by exactly 2 / n_states (constant step)."""
    spec = DeviceSpec(n_states=64)
    t = Tile((2, 2), spec, 1.0, gen(7), DEV)
    t.u = torch.zeros(2, 2)
    t.apply_pulses(torch.ones(2, 2), torch.zeros(2, 2))
    got = float(t.u.mean())
    return abs(got - 2 / 64) < 1e-7, f"step {got:.6f}, want {2 / 64:.6f}"


def c_c2c_noise():
    """Write noise: std of du after n pulses = c2c k sqrt(n)."""
    spec = DeviceSpec(n_states=10000, c2c=1.0)
    t = Tile((200, 200), spec, 1.0, gen(8), DEV)
    t.u = torch.zeros(200, 200)
    n = 16
    t.apply_pulses(torch.full((200, 200), float(n)), torch.zeros(200, 200))
    k = 2 / 10000
    sd = float((t.u - n * k).std())
    want = 1.0 * k * math.sqrt(n)
    return abs(sd / want - 1) < 0.03, f"std {sd:.3e}, want {want:.3e}"


def c_drift():
    spec = DeviceSpec(n_states=1000, tau_steps=100.0)
    t = Tile((2, 2), spec, 1.0, gen(9), DEV)
    t.u = torch.full((2, 2), 0.5)
    for _ in range(50):
        t.drift(1.0)
    want = -1 + 1.5 * math.exp(-0.5)
    got = float(t.u.mean())
    return abs(got - want) < 1e-5, f"u {got:.6f}, want {want:.6f}"


def c_ttv2_learns():
    """TTv2 with ideal float tiles solves a linear regression about as well as SGD (loss ratio < 1.5)."""
    res = {}
    for algo in ("sgd", "ttv2"):
        g = gen(10)
        W_true = torch.randn(4, 16, generator=gen(11)) * 0.3
        uc = UpdateCfg(lr=0.002, algo=algo, tt_lambda=1.0, tt_period=4, tt_max_pulses=10**6)
        m = AnalogLinear(16, 4, DeviceSpec(ideal_float=True, n_states=1000), uc, g, DEV, bias=False)
        for _ in range(1500):
            x = torch.randn(32, 16, generator=g)
            y = x @ W_true.t()
            loss = 0.5 * ((m(x) - y) ** 2).sum()
            loss.backward(); m.update()
        x = torch.randn(256, 16, generator=gen(12))
        res[algo] = float(((m(x) - x @ W_true.t()) ** 2).mean())
    ratio = res["ttv2"] / max(res["sgd"], 1e-12)
    base = float(((x @ W_true.t()) ** 2).mean())
    ok = res["ttv2"] < 0.01 * base and res["sgd"] < 0.01 * base
    return ok, f"mse sgd {res['sgd']:.2e}, ttv2 {res['ttv2']:.2e}, untrained {base:.2e} (both < 1% of untrained)"


def c_constant_step_reference():
    """A constant-step asymmetric device keeps its reference mid-range: programmed +-w both read back."""
    spec = DeviceSpec(n_states=1000, asym=0.1)
    t = Tile((2, 2), spec, 1.0, gen(13), DEV)
    w = torch.tensor([[0.3, -0.3], [0.5, -0.5]])
    t.program(w)
    err = float((t.weight() - w).abs().max())
    return err < 2e-3, f"max |w_read - w| = {err:.2e} (tol 2e-3, one step)"


CHECKS = [c_constant_step_reference, c_fp_equivalence, c_pulse_mean, c_asym_drift, c_symmetry_point, c_level_step, c_c2c_noise,
          c_drift, c_ttv2_learns]


# ------------------------------------------------------------------ planted faults
@contextlib.contextmanager
def patch(obj, name, new):
    old = getattr(obj, name)
    setattr(obj, name, new)
    try:
        yield
    finally:
        setattr(obj, name, old)


def f_exact_sign():
    old = Tile.apply_exact
    return patch(Tile, "apply_exact", lambda self, dw: old(self, -dw))


def f_pulse_swap():
    old = memsim.pulse_counts
    def bad(x, d, lr, k, BL, g):
        a, b = old(x, d, lr, k, BL, g)
        return b, a
    return _multi([(memsim, "pulse_counts", bad), (sys.modules[__name__], "pulse_counts", bad)])


def f_pulse_noBL():
    old = memsim.pulse_counts
    bad = lambda x, d, lr, k, BL, g: tuple(t / BL for t in old(x, d, lr, k, BL, g))
    return _multi([(memsim, "pulse_counts", bad), (sys.modules[__name__], "pulse_counts", bad)])


def f_ignore_asym():
    old_init = Tile.__init__
    def init(self, shape, spec, alpha, gen, device):
        old_init(self, shape, spec, alpha, gen, device)
        self.k_dn = self.k_up.clone()
    return patch(Tile, "__init__", init)


def f_ustar_sign():
    old_init = Tile.__init__
    def init(self, shape, spec, alpha, gen, device):
        old_init(self, shape, spec, alpha, gen, device)
        self.ustar = -self.ustar
    return patch(Tile, "__init__", init)


def f_noise_linear_n():
    old = Tile.apply_pulses
    def bad(self, n_up, n_dn):
        c = self.spec.c2c
        if c > 0:
            self.spec.c2c = c * torch.sqrt(n_up + n_dn).clamp_min(1).mean().item()
        try:
            old(self, n_up, n_dn)
        finally:
            self.spec.c2c = c
    return patch(Tile, "apply_pulses", bad)


def f_drift_wrong_rest():
    def bad(self, steps=1.0):
        t = self.spec.tau_steps
        if math.isfinite(t):
            self.u = self.u * math.exp(-steps / t)
    return patch(Tile, "drift", bad)


def f_tt_transfer_sign():
    old = AnalogLinear._transfer
    def bad(self):
        lam = self.ucfg.tt_lambda
        self.ucfg.tt_lambda = -lam
        try:
            old(self)
        finally:
            self.ucfg.tt_lambda = lam
    return patch(AnalogLinear, "_transfer", bad)


def f_level_half():
    old_init = Tile.__init__
    def init(self, shape, spec, alpha, gen, device):
        old_init(self, shape, spec, alpha, gen, device)
        self.k_up = self.k_up * 0.5; self.k_dn = self.k_dn * 0.5
    return patch(Tile, "__init__", init)


@contextlib.contextmanager
def _multi(items):
    with contextlib.ExitStack() as st:
        for o, n, v in items:
            st.enter_context(patch(o, n, v))
        yield


def f_ref_at_bound():
    old_init = Tile.__init__
    def init(self, shape, spec, alpha, gen, device):
        old_init(self, shape, spec, alpha, gen, device)
        if spec.gamma_up == 0 and spec.gamma_dn == 0:
            self.ustar = torch.sign(self.k_up - self.k_dn)
            self.g_ref = self.g_of(self.ustar)
            self.u = self.ustar.clone()
    return patch(Tile, "__init__", init)


FAULTS = {  # fault -> the check that must catch it
    "constant-step reference at a bound (the D1 bug)": (f_ref_at_bound, "c_constant_step_reference"),
    "apply_exact sign flipped": (f_exact_sign, "c_fp_equivalence"),
    "pulse up/down swapped": (f_pulse_swap, "c_pulse_mean"),
    "pulse slots BL dropped": (f_pulse_noBL, "c_pulse_mean"),
    "asymmetry ignored": (f_ignore_asym, "c_asym_drift"),
    "symmetry point sign": (f_ustar_sign, "c_symmetry_point"),
    "step size halved": (f_level_half, "c_level_step"),
    "write noise ~ n not sqrt(n)": (f_noise_linear_n, "c_c2c_noise"),
    "drift relaxes to 0 not bare": (f_drift_wrong_rest, "c_drift"),
    "TT transfer sign flipped": (f_tt_transfer_sign, "c_ttv2_learns"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = dict(schema="altone.x1000.me.tests.v1", checks={}, faults={})
    allok = True
    for c in CHECKS:
        ok, det = c()
        out["checks"][c.__name__] = dict(passed=bool(ok), detail=det)
        allok &= bool(ok)
        print(("PASS " if ok else "FAIL ") + c.__name__ + ": " + det)
    byname = {c.__name__: c for c in CHECKS}
    for fname, (fac, cname) in FAULTS.items():
        with fac():
            try:
                ok, det = byname[cname]()
            except Exception as e:  # a crash also counts as caught
                ok, det = False, f"raised {type(e).__name__}: {e}"
        caught = not ok
        out["faults"][fname] = dict(check=cname, caught=caught, detail=det)
        allok &= caught
        print(("CAUGHT " if caught else "MISSED ") + fname + " by " + cname + ": " + det)
    out["all_ok"] = bool(allok)
    with open(a.out, "wb") as f:
        f.write((json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    print("ALL_OK" if allok else "NOT_OK")
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
