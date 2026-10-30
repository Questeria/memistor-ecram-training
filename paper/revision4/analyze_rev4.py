"""ME-REVISE-4 analysis (PLAN-REVISION-4.md): experiment A2-M (MNIST MO-ECRAM SGD as matched triples on one GPU) and the
version-5 layout of the probe tables.

    H:/x1000/bench/venv/Scripts/python.exe -B revision4/analyze_rev4.py            (results, macros, tables)
    H:/x1000/bench/venv/Scripts/python.exe -B revision4/analyze_rev4.py --selftest (the matching rule on planted mismatches)

Reads records/revision/runs/{e3,fid}, records/revision3/runs/{fidr,fidprobe3,fidprobe3-probes} and records/revision4/runs/fidm
(the A2-M runs, copied in by name from the desk's scratch tree). Writes records/revision4/RESULTS-REV4.json,
tex/numbers_rev4.tex (\\RZ... macros) and tex/tables/rev4_{a2m,probe_sur,probe_seq,dep}.tex.

The matching rule: a seed enters a comparison labelled matched only if its FP-SGD control, surrogate and stream records carry
equal init_sha256, equal data_sha256 and the same GPU; otherwise Mismatch is raised naming the seed (v4's A2-R join fails it).
"""
import glob
import json
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(P, "revision"))
sys.path.insert(0, os.path.join(P, "revision3"))
sys.path.insert(0, os.path.join(P, "sim"))
import analyze_rev as AR  # noqa: E402
import analyze_rev3 as A3  # noqa: E402

R4 = os.path.join(P, "records", "revision4")
TEX = AR.TEX
fmt = AR.fmt
T, D, A = "mnist", "ecram_mo_kim2019", "sgd"


class Mismatch(Exception):
    pass


def jl(p):
    return json.load(open(p, "rb"))


def role(r):
    if r["task"] != T:
        return None
    if r["arm"] == "fp_sgd" and r["algo"] == "sgd":
        return "fp"
    if r["arm"] == "device" and r["spec"]["name"] == D and r["algo"] == A:
        return "seq" if r.get("pulse_mode") == "seq" else "sur"
    return None


def triples(recs):
    by = {}
    for r in recs:
        k = role(r)
        if k:
            assert k not in by.setdefault(r["seed"], {}), ("duplicate", r["seed"], k)
            by[r["seed"]][k] = r
    return by


def check_matched(seed, tri):
    """The rule of PLAN-REVISION-4.md section 1: all three roles present, equal hashes, one GPU."""
    miss = [k for k in ("fp", "sur", "seq") if k not in tri]
    if miss:
        raise Mismatch(f"seed {seed}: missing {miss}")
    for key in ("init_sha256", "data_sha256", "device"):
        vals = {k: tri[k].get(key) for k in ("fp", "sur", "seq")}
        if None in vals.values() or len(set(vals.values())) != 1:
            raise Mismatch(f"seed {seed}: {key} differs or is missing: " + ", ".join(f"{k}={str(v)[:16]}" for k, v in vals.items()))


def cell(by, seeds):
    for s in seeds:
        check_matched(s, by[s])
    g = {k: [AR.gap(T, AR.metric(by[s]["fp"]), AR.metric(by[s][k])) for s in seeds] for k in ("sur", "seq")}
    cq, cs = AR.ci(g["seq"]), AR.ci(g["sur"])
    cd = AR.ci([x - y for x, y in zip(g["seq"], g["sur"])])
    return dict(seeds=list(seeds), gap_seq=g["seq"], gap_sur=g["sur"], seq=cq, sur=cs, dgap=cd,
                seq_label=AR.label(T, cq), sur_label=AR.label(T, cs), material=abs(cd["mean"]) > AR.LINE[T] / 2,
                device=by[seeds[0]]["fp"].get("device"),
                acc={k: [AR.metric(by[s][k]) for s in seeds] for k in ("fp", "sur", "seq")})


def load_dir(d):
    return [jl(f) for f in sorted(glob.glob(os.path.join(d, "*.json")))]


def sources():
    e3 = [r for r in AR.load("e3") if role(r)]
    fid = [r for r in AR.load("fid") if role(r)]
    fidr = [r for r in A3.load3("fidr") if role(r)]
    fidm = load_dir(os.path.join(R4, "runs", "fidm"))
    return e3, fid, fidr, fidm


def v4_join(e3, fid, fidr):
    """v4's A2-R pairing (analyze_rev3.a2r): E3's control and surrogate, the stream from the pod for seeds 0-2 and from the
    desk's P2000 for seeds 3-4."""
    by = triples(e3)
    for r in fid:
        if r["seed"] <= 2:
            by[r["seed"]]["seq"] = r
    for r in fidr:
        if r["seed"] >= 3:
            by[r["seed"]]["seq"] = r
    return by


def a2m():
    e3, fid, fidr, fidm = sources()
    m = triples(fidm)
    seeds = sorted(m)
    res = dict(p2200=cell(m, seeds))
    pod = triples(e3 + fid)
    res["pod_n3"] = cell(pod, [0, 1, 2])
    try:
        cell(v4_join(e3, fid, fidr), [0, 1, 2, 3, 4])
        res["v4_join_refused"] = None
    except Mismatch as e:
        res["v4_join_refused"] = str(e)
    # realisations of one seed on two GPUs (descriptive, no attribution)
    rows = []
    for s in seeds:
        row = dict(seed=s, p2200_gap_sur=res["p2200"]["gap_sur"][seeds.index(s)], p2200_gap_seq=res["p2200"]["gap_seq"][seeds.index(s)],
                   p2200_acc=dict(fp=AR.metric(m[s]["fp"]), sur=AR.metric(m[s]["sur"]), seq=AR.metric(m[s]["seq"])))
        if s in (0, 1, 2):
            row.update(pod_gap_sur=res["pod_n3"]["gap_sur"][s], pod_gap_seq=res["pod_n3"]["gap_seq"][s],
                       pod_acc=dict(fp=AR.metric(pod[s]["fp"]), sur=AR.metric(pod[s]["sur"]), seq=AR.metric(pod[s]["seq"])))
        rows.append(row)
    res["by_seed"] = rows
    dif = [abs(r["p2200_gap_" + k] - r["pod_gap_" + k]) for r in rows if "pod_gap_seq" in r for k in ("sur", "seq")]
    res["realisation_gap_diff_max"] = max(dif) if dif else None
    # the predicted cause: the P2200's hashes differ from the A4000's (E3) and the P2000's (A2-R) for every seed
    a4000 = {r["seed"]: (r["init_sha256"], r["data_sha256"]) for r in e3}
    p2000 = {r["seed"]: (r["init_sha256"], r["data_sha256"]) for r in fidr}
    pred = {}
    for s in seeds:
        h = (m[s]["fp"]["init_sha256"], m[s]["fp"]["data_sha256"])
        pred[s] = dict(init_differs_a4000=h[0] != a4000[s][0], data_differs_a4000=h[1] != a4000[s][1],
                       init_differs_p2000=(h[0] != p2000[s][0]) if s in p2000 else None,
                       data_differs_p2000=(h[1] != p2000[s][1]) if s in p2000 else None)
    res["prediction"] = pred
    res["prediction_holds"] = all(v is not False for p in pred.values() for v in p.values())
    return res


def table_a2m(R):
    rows = []
    for r in R["by_seed"]:
        a = r["p2200_acc"]
        pod = (f"{fmt(r['pod_gap_sur'])} & {fmt(r['pod_gap_seq'])}" if "pod_gap_seq" in r else "-- & --")
        rows.append(f"{r['seed']} & {fmt(100 * a['fp'])} & {fmt(100 * a['sur'])} & {fmt(100 * a['seq'])} & "
                    f"{fmt(r['p2200_gap_sur'])} & {fmt(r['p2200_gap_seq'])} & {pod}\\\\")
    c = R["p2200"]
    rows.append(f"\\midrule mean [95\\,\\%] & & & & {fmt(c['sur']['mean'])} [{fmt(c['sur']['lo'])}, {fmt(c['sur']['hi'])}] & "
                f"{fmt(c['seq']['mean'])} [{fmt(c['seq']['lo'])}, {fmt(c['seq']['hi'])}] & & \\\\")
    return ("% generated by revision4/analyze_rev4.py (do not edit)\n"
            "\\begin{table}[t]\\centering\\footnotesize\\setlength{\\tabcolsep}{3pt}\\caption{Experiment A2-M: MNIST MO-ECRAM "
            "SGD as matched triples on one GPU (Quadro P2200): per seed, the FP-SGD control's, the surrogate's and the "
            "per-sample stream's test accuracy (\\%) and the two gaps to the control (pp); every seed's three runs share their "
            "initialisation and example order (equal hashes, checked). Right: the same seeds' gaps from the pod's matched "
            "triples (RTX A4000), a different random realisation of each seed.}\\label{tab:rev4_a2m}\n"
            "\\fitbox{\\begin{tabular}{rrrrllll}\\toprule & \\multicolumn{5}{c}{P2200} & \\multicolumn{2}{c}{pod (A4000)}\\\\"
            "\\cmidrule(lr){2-6}\\cmidrule(lr){7-8} Seed & FP-SGD & sur. & seq & gap sur. & gap seq & gap sur. & gap seq\\\\"
            "\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}}\\end{table}\n")


def probe_tables(PR):
    """Table 6 of v4 split in two (surrogate; seq) and Table 7, all at footnotesize (PLAN-REVISION-4.md section 3)."""
    TASKL, SH, ALGLAB = A3.TASKL, A3.SH, AR.ALGLAB
    case = lambda p: f"{TASKL[p['task']]} {SH[p['device']]} {ALGLAB[p['algo']]} & {p['layer']} & {p['update']}"
    sur, seq, dep = [], [], []
    for p in PR:
        s, q, dp = p["surrogate"], p["seq"], p["dep"]
        sur.append(f"{case(p)} & {100 * p['lost_frac']:.1f} & "
                   f"{fmt(100 * s['gain_ratio_minus1'], 1)} [{fmt(100 * s['gain_lo'], 1)}, {fmt(100 * s['gain_hi'], 1)}] & "
                   f"{fmt(s['excess'])} ({fmt(s['excess_p95'])}) & {fmt(s['var_ratio'])} & {'yes' if s['meets'] else 'no'}"
                   f"{' (95)' if s['at95'] else ''}\\\\")
        seq.append(f"{case(p)} & "
                   f"{fmt(100 * q['gain_ratio_minus1'], 1)} [{fmt(100 * q['gain_lo'], 1)}, {fmt(100 * q['gain_hi'], 1)}] & "
                   f"{fmt(q['rel_mean_err'], 3)} & {fmt(q['floor_independent'], 3)} / {fmt(q['floor_paired'], 3)} & "
                   f"{fmt(q['excess'], 3)} ({fmt(q['excess_p95'], 3)}) & {fmt(q['var_ratio'])} & "
                   f"{'yes' if q['meets'] else 'no'}{' (95)' if q['at95'] else ''}\\\\")
        f3 = lambda x: fmt(x, 3) if x is not None else "--"
        two = lambda k, f=None: f"{f3(dp[k + '_row'][f] if f else dp[k + '_row'])} / " \
                                f"{f3((dp[k + '_col'][f] if dp[k + '_col'] else None) if f else dp[k + '_col'])}"
        dep.append(f"{case(p)} & {two('slot', 'rms')} & {two('surrogate', 'rms')} & "
                   f"{f3(dp['slot_row_excess_rms'])} / {f3(dp['slot_col_excess_rms'])} & {two('slot', 'mean_aligned')} & "
                   f"{two('slot', 'line_rms_max')} & {f3(dp['v3_pooled_slot_row'])} / {f3(dp['v3_pooled_slot_col'])}\\\\")
    n95 = ("``(95)'': the bootstrap 95th percentile of the excess and the bootstrap 95 \\% gain interval are also within their "
           "lines; it does not cover the variance ratio (a point estimate) and is not a joint 95 \\% guarantee for every line.")
    head = "% generated by revision4/analyze_rev4.py (do not edit)\n\\begin{table}[t]\\centering\\footnotesize\\setlength{\\tabcolsep}{3pt}"
    t_sur = (head + "\\caption{Update fidelity of the aggregate surrogate against the literal pulse stream (experiment A1-P; "
             "desk rerun of A1 with the draws kept, 16 draws per probe; Li = Li-ECRAM, MO = MO-ECRAM, Prot. = "
             "protonic-inspired). Lost = requested pulse mass removed by the probability clipping (\\%). The surrogate's draws "
             "are independent of the stream's, so the independent sampling floor applies: gain difference (\\%, bootstrap "
             "95 \\% interval over draws), excess relative mean difference beyond the floor (bootstrap 95th percentile), "
             "median variance ratio, and whether the point estimates meet the registered lines (10 \\%, 0.10, [0.5, 2]). "
             + n95 + "}\\label{tab:rev4_probe_sur}\n"
             "\\fitbox{\\begin{tabular}{lrrrlllc}\\toprule Case & L. & Upd. & Lost & $\\Delta g$ \\% & excess & var. & "
             "meets\\\\\\midrule\n" + "\n".join(sur) + "\n\\bottomrule\\end{tabular}}\\end{table}\n")
    t_seq = (head + "\\caption{Update fidelity of the per-sample stream (seq) against the literal pulse stream, paired by draw "
             "(shared line firings; experiment A1-P, the probes of Table~\\ref{tab:rev4_probe_sur}): gain difference (\\%, "
             "bootstrap 95 \\% interval), raw relative mean difference, independent / paired sampling floor, excess beyond "
             "the PAIRED floor (bootstrap 95th percentile), median variance ratio, and whether the point estimates meet the "
             "registered lines (5 \\%, 0.05, [0.8, 1.25]). " + n95 + "}\\label{tab:rev3_probe}\n"
             "\\fitbox{\\begin{tabular}{lrrlllllc}\\toprule Case & L. & Upd. & $\\Delta g$ \\% & raw & floor ind./pair. & "
             "excess & var. & meets\\\\\\midrule\n" + "\n".join(seq) +
             "\n\\bottomrule\\end{tabular}}\\end{table}\n")
    t_dep = ("% generated by revision4/analyze_rev4.py (do not edit)\n\\begin{table*}[t]\\centering\\footnotesize"
             "\\setlength{\\tabcolsep}{3pt}\\caption{Cross-cell dependence of the literal stream's draws (experiment A1-P), "
             "among cells sharing a row / a column, from per-pair Pearson correlations over all pairs (they cannot cancel): "
             "root-mean-square correlation of the literal stream and of the surrogate (whose cells are independent, so its "
             "value is the sampling null at the same number of draws), the excess RMS beyond that null, taken in quadrature "
             r"($\sqrt{\max(0,\,\mathrm{RMS}_{\mathrm{slot}}^2-\mathrm{RMS}_{\mathrm{null}}^2)}$), the mean correlation "
             "aligned with the signs of the expected update, the largest per-line RMS, and the version-3 statistic (a pooled, "
             "signed normalised covariance, which can cancel).}\\label{tab:rev3_dep}\n"
             "\\fitbox{\\begin{tabular}{lrrcccccc}\\toprule Case & L. & Upd. & RMS slot & RMS sur.\\ (null) & excess RMS & "
             "aligned mean & max line RMS & v3 pooled\\\\\\midrule\n" + "\n".join(dep) +
             "\n\\bottomrule\\end{tabular}}\\end{table*}\n")
    return {"rev4_probe_sur.tex": t_sur, "rev4_probe_seq.tex": t_seq, "rev4_dep.tex": t_dep}


def write_probe_tables(PR, outdir):
    os.makedirs(outdir, exist_ok=True)
    for n, t in probe_tables(PR).items():
        open(os.path.join(outdir, n), "wb").write(t.encode("utf-8"))


def macros(R):
    c, pc = R["p2200"], R["pod_n3"]
    m = {"RZAtwoMN": str(len(c["seeds"])), "RZAtwoMGpu": c["device"].replace("Quadro ", "Quadro~"),
         "RZAtwoMSeqGap": fmt(c["seq"]["mean"]), "RZAtwoMSeqLo": fmt(c["seq"]["lo"]), "RZAtwoMSeqHi": fmt(c["seq"]["hi"]),
         "RZAtwoMSeqLabel": c["seq_label"], "RZAtwoMSurGap": fmt(c["sur"]["mean"]), "RZAtwoMSurLo": fmt(c["sur"]["lo"]),
         "RZAtwoMSurHi": fmt(c["sur"]["hi"]), "RZAtwoMSurLabel": c["sur_label"], "RZAtwoMD": fmt(c["dgap"]["mean"]),
         "RZAtwoMDLo": fmt(c["dgap"]["lo"]), "RZAtwoMDHi": fmt(c["dgap"]["hi"]),
         "RZAtwoMMaterial": "material" if c["material"] else "not material",
         "RZAtwoMSurSd": fmt(st.stdev(c["gap_sur"])), "RZAtwoMSeqSd": fmt(st.stdev(c["gap_seq"])),
         "RZPodNThreeD": fmt(pc["dgap"]["mean"]), "RZPodNThreeDLo": fmt(pc["dgap"]["lo"]),
         "RZPodNThreeDHi": fmt(pc["dgap"]["hi"]), "RZPodNThreeDLo": fmt(pc["dgap"]["lo"]), "RZPodNThreeDHi": fmt(pc["dgap"]["hi"]), "RZRealGapDiffMax": fmt(R["realisation_gap_diff_max"]),
         "RZSeedZeroPodSeq": fmt(100 * R["by_seed"][0]["pod_acc"]["seq"]),
         "RZSeedZeroPTwoTwoSeq": fmt(100 * R["by_seed"][0]["p2200_acc"]["seq"])}
    dr = jl(os.path.join(R4, "DRAW-REBUILD.json"))  # revision4/rebuild_draw_tables.py --json (the 12 draw files)
    assert dr["all_identical"], "the draw rebuild must reproduce the tables before the paper cites it"
    m["RZDrawN"] = str(len(dr["files"]))
    m["RZDrawBytes"] = f"{sum(f['bytes'] for f in dr['files']):,}".replace(",", "{,}")
    return m


def main():
    if "--selftest" in sys.argv:
        print(json.dumps(selftest()))
        return
    R = a2m()
    PR, same = A3.probes3()
    R["probe_runs_vs_e3"] = same
    st_ = selftest()
    assert st_["all_caught"], st_
    R["selftest"] = st_
    R["schema"] = "altone.x1000.me-revision4.results.v1"
    open(os.path.join(R4, "RESULTS-REV4.json"), "wb").write((json.dumps(R, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    m = macros(R)
    open(os.path.join(TEX, "numbers_rev4.tex"), "wb").write(
        ("% generated by revision4/analyze_rev4.py (do not edit)\n" +
         "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in sorted(m.items()))).encode("utf-8"))
    open(os.path.join(TEX, "tables", "rev4_a2m.tex"), "wb").write(table_a2m(R).encode("utf-8"))
    write_probe_tables(PR, os.path.join(TEX, "tables"))
    c = R["p2200"]
    print("A2-M", c["device"], "seq", c["seq_label"], fmt(c["seq"]["mean"]), "sur", c["sur_label"], fmt(c["sur"]["mean"]),
          "d", fmt(c["dgap"]["mean"]), [fmt(c["dgap"]["lo"]), fmt(c["dgap"]["hi"])], "material", c["material"],
          "| v4 join refused:", bool(R["v4_join_refused"]), "| prediction", R["prediction_holds"],
          "| realisation diff max", fmt(R["realisation_gap_diff_max"]))


def selftest():
    """The matching rule must refuse each planted mismatch and v4's join, and accept the pod's matched seeds 0-2."""
    e3, fid, fidr, _ = sources()
    pod = triples(e3 + fid)
    out = {}

    def refused(by, seeds):
        try:
            cell(by, seeds)
            return False
        except Mismatch:
            return True
    out["pod_n3_accepted"] = not refused(pod, [0, 1, 2])
    out["v4_join_refused"] = refused(v4_join(e3, fid, fidr), [0, 1, 2, 3, 4])
    for key in ("init_sha256", "data_sha256", "device"):
        bad = {s: {k: dict(v) for k, v in t.items()} for s, t in pod.items()}
        bad[1]["seq"][key] = "x"
        out[f"planted_{key}_refused"] = refused(bad, [0, 1, 2])
    bad = {s: dict(t) for s, t in pod.items()}
    del bad[2]["fp"]
    out["missing_control_refused"] = refused(bad, [0, 1, 2])
    out["all_caught"] = all(out.values())
    return out


if __name__ == "__main__":
    main()
