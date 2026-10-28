"""Checks of the paper's simulator additions, each shown to FAIL on a planted fault (the pattern of test_memsim.py).

python -B test_paper.py --out ../records/TESTS-PAPER.json
  c_identity_sgd_ttv2   the SGD and TTv2 paths equal lane ME's memsim.py bit for bit (same seed, non-ideal device)
  c_gamma_d2d_sp        per-device saturation slopes: alternating pulses converge to each device's own symmetry point
  c_offset_rejection    a static offset read from A: TTv2 (no reset) integrates it, c-TTv2 cancels most, AGAD nearly all
  c_family_learns       TTv1, c-TTv2 and AGAD on a soft-bounds device fit a linear map (< 5 % of the untrained error)
  c_ttv1_direction      one TTv1 transfer moves C along +lambda A (sign and size, expected-count regime)
"""
import argparse
import contextlib
import importlib.util
import json
import math
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import memsim  # noqa: E402
from memsim import AnalogLinear, DeviceSpec, Tile, UpdateCfg  # noqa: E402

DEV = torch.device("cpu")
OLD_PATH = os.path.join(os.environ.get("ME_LANE_ME") or os.path.join(HERE, "..", ".."), "sim", "memsim.py")


def gen(s=0):
    return torch.Generator(device=DEV).manual_seed(s)


def _old():
    spec = importlib.util.spec_from_file_location("memsim_laneME", OLD_PATH)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _train(mod, algo, steps=60):
    g = gen(21)
    spec = mod.DeviceSpec(n_states=300, asym=0.1, asym_d2d=0.02, gamma_up=0.3, gamma_dn=0.5, c2c=0.4, d2d=0.1,
                          bound_d2d=0.05, tau_steps=5000.0, ref_err=0.02)
    uc = mod.UpdateCfg(lr=0.01, algo=algo, tt_lambda=0.1, tt_lr_ratio=10.0, tt_period=4)
    m1 = mod.AnalogLinear(12, 10, spec, uc, g, DEV)
    m2 = mod.AnalogLinear(10, 3, spec, uc, g, DEV)
    xg = gen(22)
    for _ in range(steps):
        x = torch.randn(16, 12, generator=xg)
        y = torch.randint(0, 3, (16,), generator=xg)
        loss = torch.nn.functional.cross_entropy(m2(torch.tanh(m1(x))), y, reduction="sum")
        loss.backward()
        for m in (m1, m2):
            m.update(); m.drift(1.0)
    return torch.cat([m1.weight().flatten(), m2.weight().flatten(), m1.bias, m2.bias])


def c_identity_sgd_ttv2():
    old = _old()
    res = []
    for algo in ("sgd", "ttv2"):
        a, b = _train(old, algo), _train(memsim, algo)
        res.append((algo, bool(torch.equal(a, b)), float((a - b).abs().max())))
    ok = all(r[1] for r in res)
    return ok, "; ".join(f"{al}: identical={eq} max|d|={d:.3e}" for al, eq, d in res)


def c_gamma_d2d_sp():
    spec = DeviceSpec(n_states=200, asym=0.0, gamma_up=1.0, gamma_dn=1.0, gamma_d2d=0.4)
    t = Tile((20, 20), spec, 1.0, gen(23), DEV)
    t.u = torch.full((20, 20), 0.6)
    for _ in range(3000):
        t.apply_pulses(torch.ones(20, 20), torch.ones(20, 20))
    want = (t.k_up - t.k_dn) / (t.k_up * t.gu + t.k_dn * t.gd)
    err = float((t.u - want).abs().max())
    spread = float(t.gu.std())
    ok = err < 2e-3 and spread > 0.2 and float((t.ustar - want).abs().max()) < 1e-6
    return ok, f"max |u - u*_ij| {err:.2e} (tol 2e-3); std of gamma_up {spread:.3f} (> 0.2)"


def _offset_H(algo, reads=200):
    spec = DeviceSpec(ideal_float=True, n_states=1000)
    uc = UpdateCfg(lr=0.01, algo=algo, tt_lambda=0.1, tt_period=1, tt_reset=False, tt_rho=0.5, agad_beta=1.0,
                   tt_max_pulses=0)
    m = AnalogLinear(8, 6, spec, uc, gen(24), DEV, bias=False)
    V = 0.05
    m.A.u = m.A.u_of_g(m.A.g_ref + V / m.A.alpha)  # A reads a static offset V everywhere, no gradient
    for _ in range(reads):
        m._transfer()
    return float(m.H.abs().mean())


def c_offset_rejection():
    h = {a: _offset_H(a) for a in ("ttv2", "cttv2", "agad")}
    rc, ra = h["cttv2"] / h["ttv2"], h["agad"] / h["ttv2"]
    ok = rc < 0.35 and ra < 0.5 * rc
    return ok, f"|H| ttv2 {h['ttv2']:.3g}; c-TTv2/TTv2 {rc:.3f} (< 0.35); AGAD/TTv2 {ra:.4f} (< half of c-TTv2's)"


def _fit(algo, steps=1500):
    g = gen(25)
    W_true = torch.randn(4, 16, generator=gen(26)) * 0.15
    spec = DeviceSpec(n_states=1000, gamma_up=0.5, gamma_dn=0.5, c2c=0.1, ref_err=0.0)
    kw = dict(tt_lambda=0.1, tt_lr_ratio=10.0, tt_period=4, tt_rho=0.1, agad_beta=0.5)
    if algo == "ttv1":
        kw = dict(tt_lambda=0.02, tt_gamma=1.0, tt_cols=4, tt_reset=False)
    if algo in ("cttv2", "agad"):
        kw["tt_reset"] = False
    m = AnalogLinear(16, 4, spec, UpdateCfg(lr=0.002, algo=algo, **kw), g, DEV, bias=False)
    for _ in range(steps):
        x = torch.randn(32, 16, generator=g)
        loss = 0.5 * ((m(x) - x @ W_true.t()) ** 2).sum()
        loss.backward(); m.update()
    x = torch.randn(256, 16, generator=gen(27))
    return float(((m(x) - x @ W_true.t()) ** 2).mean()), float(((x @ W_true.t()) ** 2).mean())


def c_family_learns():
    out, ok = [], True
    for algo in ("ttv1", "cttv2", "agad"):
        mse, base = _fit(algo)
        ok &= mse < 0.05 * base
        out.append(f"{algo} {mse / base:.4f}")
    return ok, "mse / untrained: " + ", ".join(out) + " (each < 0.05)"


def c_ttv1_direction():
    spec = DeviceSpec(n_states=2000)
    uc = UpdateCfg(lr=0.01, algo="ttv1", tt_lambda=0.5, tt_gamma=1.0, tt_cols=6, tt_reset=False)
    acc = torch.zeros(5, 6)
    N = 300
    for s in range(N):
        m = AnalogLinear(6, 5, spec, uc, gen(100 + s), DEV, bias=False)
        tgt = torch.linspace(-0.04, 0.04, 30).reshape(5, 6)
        m.A.u = m.A.u_of_g(m.A.g_ref + tgt / m.A.alpha)
        c0 = m.C.weight().clone()
        m._transfer()
        acc += m.C.weight() - c0
    acc /= N
    want = 0.5 * (m.A.weight())
    err = float((acc - want).abs().max() / want.abs().max())
    return err < 0.1, f"max rel err of the mean C change vs +lambda A = {err:.3f} (tol 0.1)"


CHECKS = [c_identity_sgd_ttv2, c_gamma_d2d_sp, c_offset_rejection, c_family_learns, c_ttv1_direction]


@contextlib.contextmanager
def patch(obj, name, new):
    old = getattr(obj, name)
    setattr(obj, name, new)
    try:
        yield
    finally:
        setattr(obj, name, old)


def f_identity_gamma():  # the saturation term of the down branch uses gamma_up
    old_init = Tile.__init__
    def init(self, shape, spec, alpha, g, device):
        old_init(self, shape, spec, alpha, g, device)
        self.gd = self.gu
    return patch(Tile, "__init__", init)


def f_gamma_d2d_shared():  # one spread drawn for the whole tile instead of per device
    old_init = Tile.__init__
    def init(self, shape, spec, alpha, g, device):
        old_init(self, shape, spec, alpha, g, device)
        if torch.is_tensor(self.gu):
            self.gu = torch.full_like(self.gu, float(self.gu.mean()))
            self.gd = torch.full_like(self.gd, float(self.gd.mean()))
    return patch(Tile, "__init__", init)


def _xfer_patch(mutate):
    old = AnalogLinear._transfer
    def bad(self):
        mutate(self, "pre")
        try:
            return old(self)
        finally:
            mutate(self, "post")
    return patch(AnalogLinear, "_transfer", bad)


def f_no_demod():  # the read is not multiplied by the chopper sign
    store = {}
    def mut(self, when):
        if self.chop is None:
            return
        if when == "pre":
            store["c"] = self.chop
            self.chop = torch.ones_like(self.chop)
            self._true_chop = store["c"]
        else:
            # flips that happened on the all-ones stand-in are carried to the real chopper
            flipped = self.chop < 0
            c = store["c"]
            c[flipped] = -c[flipped]
            self.chop = c
    return _xfer_patch(mut)


def f_no_flip():  # the chopper never flips (rho ignored)
    def mut(self, when):
        if when == "pre":
            self._rho = self.ucfg.tt_rho
            self.ucfg.tt_rho = 0.0
        else:
            self.ucfg.tt_rho = self._rho
    return _xfer_patch(mut)


def f_agad_no_ref():  # AGAD's reference is never updated (stays 0)
    def mut(self, when):
        if when == "post" and getattr(self, "Pref", None) is not None:
            self.Pref.zero_()
    return _xfer_patch(mut)


def f_no_modulation():  # the inputs of the A update are not chopped (the read is still demodulated)
    return patch(AnalogLinear, "update", _update_without_modulation)


def _update_without_modulation(self):
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
        n_up, n_dn = memsim.pulse_counts(x, d, lr_t / tgt.alpha, tgt.k_nom, u.BL, self.gen, self.stats)
        tgt.apply_pulses(n_up, n_dn)
    if self.A is not None:
        self._transfer()
    self._x = self._d = None


def f_ttv1_sign():
    old = AnalogLinear._transfer_v1
    def bad(self, idx):
        lam = self.ucfg.tt_lambda
        self.ucfg.tt_lambda = -lam
        try:
            old(self, idx)
        finally:
            self.ucfg.tt_lambda = lam
    return patch(AnalogLinear, "_transfer_v1", bad)


FAULTS = {
    "down-branch saturation uses gamma_up": (f_identity_gamma, "c_identity_sgd_ttv2"),
    "gamma spread shared by the whole tile": (f_gamma_d2d_shared, "c_gamma_d2d_sp"),
    "chopper demodulation missing": (f_no_demod, "c_offset_rejection"),
    "chopper never flips": (f_no_flip, "c_offset_rejection"),
    "AGAD reference never set": (f_agad_no_ref, "c_offset_rejection"),
    "A-update inputs not chopped": (f_no_modulation, "c_family_learns"),
    "TTv1 transfer sign flipped": (f_ttv1_sign, "c_ttv1_direction"),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = dict(schema="altone.x1000.me-paper.tests.v1", checks={}, faults={})
    allok = True
    for c in CHECKS:
        ok, det = c()
        out["checks"][c.__name__] = dict(passed=bool(ok), detail=det)
        allok &= bool(ok)
        print(("PASS " if ok else "FAIL ") + c.__name__ + ": " + det, flush=True)
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
        print(("CAUGHT " if caught else "MISSED ") + fname + " by " + cname + ": " + det, flush=True)
    out["all_ok"] = bool(allok)
    with open(a.out, "wb") as f:
        f.write((json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    print("ALL_OK" if allok else "NOT_OK")
    sys.exit(0 if allok else 1)


if __name__ == "__main__":
    main()
