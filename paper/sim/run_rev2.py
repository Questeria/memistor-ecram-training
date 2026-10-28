"""ME-REVISE-2: run_rev.py with the explicit pulse stream and update-fidelity probes (PLAN-REVISION-2.md, experiment A).

    python -B run_rev2.py [--pulse surrogate|seq] [--seq-layers all|i,j] [--probe-steps a,b --probe-layers i,j
                          --probe-draws R --probe-out file.json] <run_rev.py arguments>

--pulse seq: the analog layers named by --seq-layers update with pulse_seq_rev2.seq_apply (per-sample Bernoulli line
firings, exact same-sign trains, samples in order) instead of the aggregate Poisson surrogate; everything else (bias,
chopper, transfer, reset, drift, the other layers) is run_rev.py unchanged. --pulse surrogate (default) is run_rev.py
exactly: the patch then calls the original update, and the probes draw from their own generator (the run's streams are
not touched, checked by test_rev2.py).

A probe, at a layer's update number in --probe-steps, takes that batch's x, d and the update target's state and applies the
batch R times from the same state by three methods: the surrogate (memsim_rev.pulse_counts + Tile.apply_pulses), `seq` and
the literal `slot` stream (`slot` replays each `seq` draw's line firings). It records, per method, the realised update in
nominal steps against the requested one, its variance and its cross-cell correlation, and each method's distance to `slot`.
The record of the run gets pulse_mode, seq_layers and the probe file name.
"""
import argparse
import json
import math
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import memsim_rev as MR  # noqa: E402
import pulse_seq_rev2 as PS  # noqa: E402

CFG = dict(seq=False, seq_layers=None, probe_steps=set(), probe_layers=set(), draws=16, probe_seed=12345,
           fault_probe_shared_gen=False)  # the last: a planted fault for test_rev2.py only
PROBES = []
_COUNT = [0]
_orig_init = MR.AnalogLinear.__init__
_orig_update = MR.AnalogLinear.update


def _init(self, *a, **k):
    _orig_init(self, *a, **k)
    self._li = _COUNT[0]
    _COUNT[0] += 1
    self._nupd = 0


def _params(tile):
    if getattr(tile, "_P", None) is None:
        tile._P = PS.dev_params(tile)
    return tile._P


def _offcorr(res, dim):
    """Mean off-diagonal correlation of the residuals res (R, out, in) among cells sharing a row (dim=2: sum over inputs)
    or a column (dim=1)."""
    n = res.shape[dim]
    if n < 2:
        return None
    s = res.sum(dim)
    off = (s * s).sum() - (res * res).sum()
    v = (res * res).mean()
    if float(v) <= 0:
        return None
    pairs = res.numel() / n * n * (n - 1)
    return float(off / pairs / v)


def _summ(L, Q, Pexp):
    S = torch.stack(L).double()
    m = S.mean(0)
    v = S.var(0, unbiased=True)
    res = S - m
    nQ, nP = float((Q * Q).sum()), float((Pexp * Pexp).sum())
    mm = float((m * m).sum())
    return dict(mean=m, var=v, gain_req=float((m * Q).sum()) / nQ if nQ else None,
                cos_req=float((m * Q).sum()) / math.sqrt(nQ * mm) if nQ and mm else None,
                gain_policy=float((m * Pexp).sum()) / nP if nP else None,
                var_mean=float(v.mean()), rho_row=_offcorr(res, 2), rho_col=_offcorr(res, 1), mean_norm=math.sqrt(mm))


@torch.no_grad()
def _probe(layer, tgt, x, d):
    u = layer.ucfg
    xx = x * layer.chop if layer.chop is not None else x
    lr = u.lr * (u.tt_lr_ratio if layer.A is not None else 1.0) / tgt.alpha
    px, pd, eta = PS.line_probs(xx, d, lr, tgt.k_nom, u.BL)
    P = _params(tgt)
    u0 = tgt.u.clone()
    k = tgt.k_nom
    g = torch.Generator(device=u0.device).manual_seed(CFG["probe_seed"] + 100003 * layer._li + layer._nupd)
    if CFG["fault_probe_shared_gen"]:
        g = layer.gen
    sur, seq, slot = [], [], []
    for _ in range(CFG["draws"]):
        n_up, n_dn = MR.pulse_counts(xx, d, lr, k, u.BL, g)
        keep_u, keep_g = tgt.u, tgt.ngen
        tgt.u, tgt.ngen = u0.clone(), g
        tgt.apply_pulses(n_up, n_dn)
        sur.append((tgt.u - u0) / k)
        tgt.u, tgt.ngen = keep_u, keep_g
        fire = []
        seq.append((PS.seq_apply(u0, P, px, pd, u.BL, g, ngen=g, keep_fire=fire) - u0) / k)
        slot.append((PS.slot_apply(u0, P, px, pd, u.BL, g, ngen=g, fire=fire) - u0) / k)
    Q = (-eta * (d.t() @ xx)).double()
    Pexp = (-u.BL * (pd.t() @ px)).double()
    want = float(eta * (d.abs().sum(1) * xx.abs().sum(1)).sum())
    got = float(u.BL * (pd.abs().sum(1) * px.abs().sum(1)).sum())
    pmax = math.sqrt(eta / u.BL) * math.sqrt(float(xx.abs().max()) * float(d.abs().max()))
    out = dict(layer=layer._li, update=layer._nupd, shape=list(u0.shape), rows=int(x.shape[0]), draws=CFG["draws"],
               target="A" if layer.A is not None else "C", lost_frac=1 - got / want if want > 0 else 0.0,
               pmax_preclip=pmax, requested_norm=math.sqrt(float((Q * Q).sum())),
               policy_norm=math.sqrt(float((Pexp * Pexp).sum())), u0_absmean=float(u0.abs().mean()))
    ss = {nm: _summ(L, Q, Pexp) for nm, L in (("surrogate", sur), ("seq", seq), ("slot", slot))}
    ref = ss["slot"]
    R = CFG["draws"]
    for nm, s in ss.items():
        dm = s["mean"] - ref["mean"]
        rn = float(ref["mean"].norm())
        ok = ref["var"] > 1e-12
        vr = (s["var"][ok] / ref["var"][ok]) if bool(ok.any()) else None
        s["vs_slot_rel_mean_err"] = float(dm.norm()) / rn if rn else None
        s["vs_slot_noise_floor"] = math.sqrt(float((s["var"].sum() + ref["var"].sum()) / R)) / rn if rn else None
        s["vs_slot_var_ratio_median"] = float(vr.median()) if vr is not None else None
        out[nm] = {kk: vv for kk, vv in s.items() if kk not in ("mean", "var")}
    PROBES.append(out)


@torch.no_grad()
def _update(self):
    x, d, u = self._x, self._d, self.ucfg
    if x is None or d is None:
        return
    self._nupd += 1
    tgt = self.A if self.A is not None else self.C
    if self._li in CFG["probe_layers"] and self._nupd in CFG["probe_steps"] and not tgt.spec.ideal_float:
        _probe(self, tgt, x, d)
    if not CFG["seq"] or tgt.spec.ideal_float or (CFG["seq_layers"] is not None and self._li not in CFG["seq_layers"]):
        return _orig_update(self)
    # the seq path: memsim_rev.AnalogLinear.update with the pulse draw and its application replaced
    if self.bias is not None:
        self.bias -= u.lr * d.sum(0)
    lr_t = u.lr * (u.tt_lr_ratio if self.A is not None else 1.0)
    if self.chop is not None:
        x = x * self.chop
    px, pd, eta = PS.line_probs(x, d, lr_t / tgt.alpha, tgt.k_nom, u.BL)
    st = self.stats
    st["px"] = st.get("px", 0.0) + px.abs().mean(1).sum()
    st["pd"] = st.get("pd", 0.0) + pd.abs().mean(1).sum()
    pmax = math.sqrt(eta / u.BL) * torch.sqrt(x.abs().max().clamp_min(1e-12) * d.abs().max().clamp_min(1e-12))
    st["clip_calls"] = st.get("clip_calls", 0.0) + (pmax > 1.0).float()
    st["calls"] = st.get("calls", 0.0) + 1.0
    st["want"] = st.get("want", 0.0) + eta * (d.abs().sum(1) * x.abs().sum(1)).sum()
    st["got"] = st.get("got", 0.0) + u.BL * (pd.abs().sum(1) * px.abs().sum(1)).sum()
    u1, nu, nd = PS.seq_apply(tgt.u, _params(tgt), px, pd, u.BL, self.gen, ngen=tgt.ngen, return_counts=True)
    tgt.u = u1
    self.n_pulses = self.n_pulses + (nu.sum() + nd.sum())
    if self.A is not None:
        self._transfer()
    self._x = self._d = None


MR.AnalogLinear.__init__ = _init
MR.AnalogLinear.update = _update


def main(argv=None):
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--pulse", default="surrogate", choices=["surrogate", "seq"])
    ap.add_argument("--seq-layers", default="all")
    ap.add_argument("--probe-steps", default="")
    ap.add_argument("--probe-layers", default="")
    ap.add_argument("--probe-draws", type=int, default=16)
    ap.add_argument("--probe-seed", type=int, default=12345)
    ap.add_argument("--probe-out", default="")
    a, rest = ap.parse_known_args(argv)
    ints = lambda s: {int(v) for v in s.split(",") if v.strip()}
    CFG.update(seq=a.pulse == "seq", seq_layers=None if a.seq_layers == "all" else ints(a.seq_layers),
               probe_steps=ints(a.probe_steps), probe_layers=ints(a.probe_layers), draws=a.probe_draws,
               probe_seed=a.probe_seed)
    _COUNT[0] = 0
    PROBES.clear()
    import run_rev  # noqa: E402  (imported after the patch; its main parses sys.argv)
    sys.argv = [os.path.join(HERE, "run_rev.py")] + rest
    run_rev.main()
    out = rest[rest.index("--out") + 1]
    rec = json.load(open(out, "rb"))
    rec.update(pulse_mode=a.pulse, seq_layers=a.seq_layers if a.pulse == "seq" else None,
               schema_revision2="altone.x1000.me-revision2.run.v1")
    if a.probe_out:
        with open(a.probe_out, "wb") as f:
            f.write((json.dumps(dict(run=os.path.basename(out), probes=PROBES), indent=1) + "\n").encode("utf-8"))
        rec["probe_file"] = os.path.basename(a.probe_out)
        rec["probe_n"] = len(PROBES)
    with open(out, "wb") as f:
        f.write((json.dumps(rec, indent=1, sort_keys=True) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
