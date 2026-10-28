"""ME-REVISE-3 (PLAN-REVISION-3.md section 1, experiment A1-P): run_rev2.py with a probe that keeps what a paired analysis
needs. run_rev2.py is imported unchanged; only its probe function is replaced.

    python -B run_rev3.py [--probe-boot B] [--probe-boot-seed S] [--draws-dir DIR] <run_rev2.py arguments>

The draws are made exactly as run_rev2._probe makes them (same probe generator seeding, same order per draw: surrogate,
`seq`, `slot` replaying `seq`'s line firings), and the v3 summary fields are kept. Added per probe and method:

- `paired`: against `slot`, the relative mean difference, the INDEPENDENT floor (v3) and the PAIRED floor
  sqrt(sum_cells var_r(m_r - slot_r) / R) / ||mean slot|| with both excesses; the gain ratio g(m)/g(slot) - 1; bootstrap over
  whole draws (the same draw indices for m and slot) for the excess under each floor and the gain ratio.
- `dep`: per-pair Pearson correlations of the draws among cells sharing a row (same output index) and a column (same input),
  summarised without cancellation: mean square and RMS over all pairs, the mean sign-aligned correlation r_jk sgn(P_j) sgn(P_k)
  (P the policy-expected update), the plain signed mean, per-line RMS median and maximum, and the number of pairs.
- the draws (float32 .npz: sur, seq, slot, Q, Pexp, u0) in --draws-dir with their SHA-256.
"""
import hashlib
import json
import math
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import memsim_rev as MR  # noqa: E402
import pulse_seq_rev2 as PS  # noqa: E402
import run_rev2 as RR  # noqa: E402

CFG3 = dict(boot=2000, boot_seed=2027, draws_dir="", fault_slot_fresh=False, fault_seq_bias=0.0, fault_pooled_corr=False)


def gain(m, Q):
    nQ = float((Q * Q).sum())
    return float((m * Q).sum()) / nQ if nQ else None


def paired(Sm, Ss, Q, boot, seed):
    """Sm, Ss: (R, ...) draws of a method and of slot, paired by draw index. Returns the point estimates and the bootstrap."""
    R = Sm.shape[0]
    Sm, Ss = Sm.reshape(R, -1).double(), Ss.reshape(R, -1).double()
    q = Q.reshape(-1).double()

    def est(w):
        # w: (B, R) multinomial resample counts (sum R); returns per-resample err, floor_ind, floor_pair, gain ratio
        D = Sm - Ss
        mD = w @ D / R
        mS = w @ Ss / R
        mM = w @ Sm / R
        vD = ((w @ (D * D)) - R * mD * mD) / (R - 1)
        vS = ((w @ (Ss * Ss)) - R * mS * mS) / (R - 1)
        vM = ((w @ (Sm * Sm)) - R * mM * mM) / (R - 1)
        rn = mS.norm(dim=1)
        err = mD.norm(dim=1) / rn
        fi = torch.sqrt((vM.sum(1) + vS.sum(1)).clamp_min(0) / R) / rn
        fp = torch.sqrt(vD.sum(1).clamp_min(0) / R) / rn
        nq = float((q * q).sum())
        gr = (mM @ q) / (mS @ q) - 1 if nq else torch.full_like(rn, float("nan"))
        return err, fi, fp, gr

    one = torch.ones((1, R), dtype=torch.float64, device=Sm.device)
    err, fi, fp, gr = (float(t[0]) for t in est(one))
    ex = lambda e, f: math.sqrt(max(0.0, e * e - f * f))
    out = dict(rel_mean_err=err, floor_independent=fi, floor_paired=fp, excess_independent=ex(err, fi),
               excess_paired=ex(err, fp), gain_ratio_minus1=gr, boot=boot)
    if boot:
        g = torch.Generator().manual_seed(seed)
        E_i, E_p, G = [], [], []
        for b0 in range(0, boot, 50):
            nb = min(50, boot - b0)
            idx = torch.randint(0, R, (nb, R), generator=g)
            w = torch.zeros((nb, R), dtype=torch.float64)
            w.scatter_add_(1, idx, torch.ones((nb, R), dtype=torch.float64))
            e, f_i, f_p, r = est(w.to(Sm.device))
            E_i.append(torch.sqrt((e * e - f_i * f_i).clamp_min(0)).cpu())
            E_p.append(torch.sqrt((e * e - f_p * f_p).clamp_min(0)).cpu())
            G.append(r.cpu())
        E_i, E_p, G = torch.cat(E_i), torch.cat(E_p), torch.cat(G)
        qt = lambda t, p: float(torch.quantile(t[torch.isfinite(t)], p))
        out.update(excess_independent_p95=qt(E_i, 0.95), excess_paired_p95=qt(E_p, 0.95),
                   gain_ratio_minus1_p025=qt(G, 0.025), gain_ratio_minus1_p975=qt(G, 0.975))
    return out


def dep(S, sgn, dim):
    """Per-pair Pearson correlations among cells sharing a line: dim=2 pairs cells of one output index (a row of the
    weight), dim=1 cells of one input index. Exact over all pairs through each line's R x R Gram matrix."""
    S = S.double()
    R = S.shape[0]
    res = S - S.mean(0)
    sd = res.std(0, unbiased=True)
    ok = sd > 1e-12
    if CFG3["fault_pooled_corr"]:  # planted fault: one pooled scale instead of per-cell standardisation
        z = res / res.pow(2).mean().sqrt()
    else:
        z = torch.where(ok, res / sd.clamp_min(1e-30), torch.zeros_like(res))
    s = torch.where(ok, sgn.double(), torch.zeros_like(sd))
    if dim == 1:
        z, ok, s = z.transpose(1, 2), ok.t(), s.t()
    # z: (R, L, n) with L lines of n cells each
    n = ok.sum(1).double()  # valid cells per line
    G = torch.einsum("rln,sln->lrs", z, z)
    sumsq = (G * G).sum((1, 2)) / (R - 1) ** 2 - n  # sum over ordered pairs j != k of r_jk^2
    tot = (z.sum(2) ** 2).sum(0) / (R - 1) - n  # sum over j != k of r_jk
    al = ((z * s).sum(2) ** 2).sum(0) / (R - 1) - n  # sum over j != k of sgn_j sgn_k r_jk
    pairs = n * (n - 1)
    P = float(pairs.sum())
    if P <= 0:
        return None
    has = pairs > 0
    per = torch.sqrt((sumsq[has] / pairs[has]).clamp_min(0))
    ms = float(sumsq.sum()) / P
    return dict(pairs=P, mean_sq=ms, rms=math.sqrt(max(0.0, ms)), mean_signed=float(tot.sum()) / P,
                mean_aligned=float(al.sum()) / P, line_rms_median=float(per.median()), line_rms_max=float(per.max()),
                lines=int(has.sum()), null_mean_sq_gaussian=1.0 / (R - 1))


@torch.no_grad()
def _probe3(layer, tgt, x, d):
    """run_rev2._probe's draws, plus the paired analysis, the dependence summaries and the saved draws."""
    u = layer.ucfg
    xx = x * layer.chop if layer.chop is not None else x
    lr = u.lr * (u.tt_lr_ratio if layer.A is not None else 1.0) / tgt.alpha
    px, pd, eta = PS.line_probs(xx, d, lr, tgt.k_nom, u.BL)
    P = RR._params(tgt)
    u0 = tgt.u.clone()
    k = tgt.k_nom
    g = torch.Generator(device=u0.device).manual_seed(RR.CFG["probe_seed"] + 100003 * layer._li + layer._nupd)
    if RR.CFG["fault_probe_shared_gen"]:  # planted fault (test_rev3.py only), as in run_rev2._probe
        g = layer.gen
    sur, seq, slot = [], [], []
    for _ in range(RR.CFG["draws"]):
        n_up, n_dn = MR.pulse_counts(xx, d, lr, k, u.BL, g)
        keep_u, keep_g = tgt.u, tgt.ngen
        tgt.u, tgt.ngen = u0.clone(), g
        tgt.apply_pulses(n_up, n_dn)
        sur.append((tgt.u - u0) / k)
        tgt.u, tgt.ngen = keep_u, keep_g
        fire = []
        dq = (PS.seq_apply(u0, P, px, pd, u.BL, g, ngen=g, keep_fire=fire) - u0) / k
        seq.append(dq * (1.0 + CFG3["fault_seq_bias"]))
        slot.append((PS.slot_apply(u0, P, px, pd, u.BL, g, ngen=g, fire=None if CFG3["fault_slot_fresh"] else fire) - u0) / k)
    n_before = len(RR.PROBES)
    # the v3 probe record from the same draws (run_rev2's own summary code)
    Q = (-eta * (d.t() @ xx)).double()
    Pexp = (-u.BL * (pd.t() @ px)).double()
    want = float(eta * (d.abs().sum(1) * xx.abs().sum(1)).sum())
    got = float(u.BL * (pd.abs().sum(1) * px.abs().sum(1)).sum())
    pmax = math.sqrt(eta / u.BL) * math.sqrt(float(xx.abs().max()) * float(d.abs().max()))
    out = dict(layer=layer._li, update=layer._nupd, shape=list(u0.shape), rows=int(x.shape[0]), draws=RR.CFG["draws"],
               target="A" if layer.A is not None else "C", lost_frac=1 - got / want if want > 0 else 0.0,
               pmax_preclip=pmax, requested_norm=math.sqrt(float((Q * Q).sum())),
               policy_norm=math.sqrt(float((Pexp * Pexp).sum())), u0_absmean=float(u0.abs().mean()))
    ss = {nm: RR._summ(L, Q, Pexp) for nm, L in (("surrogate", sur), ("seq", seq), ("slot", slot))}
    ref = ss["slot"]
    R = RR.CFG["draws"]
    stk = {nm: torch.stack(L).double() for nm, L in (("surrogate", sur), ("seq", seq), ("slot", slot))}
    sgn = torch.sign(Pexp)
    for i, (nm, s) in enumerate(ss.items()):
        dm = s["mean"] - ref["mean"]
        rn = float(ref["mean"].norm())
        okv = ref["var"] > 1e-12
        vr = (s["var"][okv] / ref["var"][okv]) if bool(okv.any()) else None
        s["vs_slot_rel_mean_err"] = float(dm.norm()) / rn if rn else None
        s["vs_slot_noise_floor"] = math.sqrt(float((s["var"].sum() + ref["var"].sum()) / R)) / rn if rn else None
        s["vs_slot_var_ratio_median"] = float(vr.median()) if vr is not None else None
        rec = {kk: vv for kk, vv in s.items() if kk not in ("mean", "var")}
        if nm != "slot":
            rec["paired"] = paired(stk[nm], stk["slot"], Q, CFG3["boot"],
                                   CFG3["boot_seed"] + 7919 * layer._li + 31 * layer._nupd + i)
        rec["dep"] = dict(row=dep(stk[nm], sgn, 2), col=dep(stk[nm], sgn, 1))
        out[nm] = rec
    if CFG3["draws_dir"]:
        import numpy as np
        os.makedirs(CFG3["draws_dir"], exist_ok=True)
        fn = os.path.join(CFG3["draws_dir"], f"{CFG3.get('tag', 'run')}__L{layer._li}__U{layer._nupd}.npz")
        f32 = lambda t: t.float().cpu().numpy()
        np.savez_compressed(fn, surrogate=f32(stk["surrogate"]), seq=f32(stk["seq"]), slot=f32(stk["slot"]), Q=f32(Q),
                            Pexp=f32(Pexp), u0=f32(u0))
        out["draws_file"] = os.path.basename(fn)
        out["draws_sha256"] = hashlib.sha256(open(fn, "rb").read()).hexdigest()
    assert len(RR.PROBES) == n_before
    RR.PROBES.append(out)


RR._probe = _probe3


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)

    def take(flag, conv, default):
        if flag in argv:
            i = argv.index(flag)
            v = conv(argv[i + 1])
            del argv[i:i + 2]
            return v
        return default

    CFG3["boot"] = take("--probe-boot", int, 2000)
    CFG3["boot_seed"] = take("--probe-boot-seed", int, 2027)
    CFG3["draws_dir"] = take("--draws-dir", str, "")
    CFG3["tag"] = argv[argv.index("--tag") + 1] if "--tag" in argv else "run"
    RR.main(argv)
    out = argv[argv.index("--out") + 1]
    rec = json.load(open(out, "rb"))
    rec.update(schema_revision3="altone.x1000.me-revision3.run.v1", probe_boot=CFG3["boot"])
    with open(out, "wb") as f:
        f.write((json.dumps(rec, indent=1, sort_keys=True) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
