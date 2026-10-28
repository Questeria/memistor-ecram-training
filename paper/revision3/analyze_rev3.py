"""ME-REVISE-3 analysis (PLAN-REVISION-3.md), after revision2/analyze_rev2.py.

    H:/x1000/bench/venv/Scripts/python.exe -B revision3/analyze_rev3.py

Reads records/revision/ (E3, E4 results, fid) and records/revision3/runs/{fidprobe3,fidprobe3-probes,fidr} (the desk runs of
experiments A1-P and A2-R), records/revision2/RESULTS-REV2.json (the r6 probes, for comparison). Writes
records/revision3/RESULTS-REV3.json, tex/numbers_rev3.tex (macros \\RY...) and tex/tables/rev3_{probe,dep,fid}.tex.
"""
import glob
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(P, "revision"))
sys.path.insert(0, os.path.join(P, "sim"))
import analyze_rev as AR  # noqa: E402

R3 = os.path.join(P, "records", "revision3")
TEX = AR.TEX
fmt, DEVLAB, ALGLAB = AR.fmt, AR.DEVLAB, AR.ALGLAB
TASKL = {"mnist": "MNIST", "cifar": "CIFAR", "lm": "LM"}
SH = {"ecram_li_tang2018": "Li", "ecram_mo_kim2019": "MO", "protonic_onen2022": "Prot."}
LAB1 = {"PASS": "P", "FAIL": "F", "UNRESOLVED": "U", "N/A": "--"}
# the registered lines (PLAN-REVISION-2.md section 2, unchanged by PLAN-REVISION-3.md)
LINES = {"surrogate": (0.10, 0.10, 0.5, 2.0), "seq": (0.05, 0.05, 0.8, 1.25)}
DEP_SMALL = 0.05  # PLAN-REVISION-3.md: "small" only if slot's excess RMS correlation <= 0.05 on every probe


def load3(phase):
    out = []
    for f in sorted(glob.glob(os.path.join(R3, "runs", phase, "*.json"))):
        out.append(json.load(open(f, "rb")))
    return out


def words(n):
    return ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve"][n] \
        if 0 <= n <= 12 else str(n)


# ------------------------------------------------------------------ A1-P: paired probes (desk)
def probes3():
    old = {(p["task"], p["layer"], p["update"]): p for p in
           json.load(open(os.path.join(P, "records", "revision2", "RESULTS-REV2.json"), "rb"))["probes"]}
    out, same = [], []
    e3 = {(r["task"], r["spec"]["name"], r["algo"], r["seed"]): r for r in AR.load("e3") if r["arm"] == "device"}
    for f in sorted(glob.glob(os.path.join(R3, "runs", "fidprobe3-probes", "*.probes.json"))):
        d = json.load(open(f, "rb"))
        run = json.load(open(os.path.join(R3, "runs", "fidprobe3", d["run"]), "rb"))
        k = (run["task"], run["spec"]["name"], run["algo"], run["seed"])
        same.append(dict(run=run["tag"], device=run.get("device"), metric=run["metric"], e3=e3[k]["metric"],
                         e3_device=e3[k].get("device"), equal_to_e3=run["metric"] == e3[k]["metric"]))
        for p in d["probes"]:
            sl = p["slot"]
            row = dict(task=run["task"], device=run["spec"]["name"], algo=run["algo"], layer=p["layer"], update=p["update"],
                       shape=p["shape"], rows=p["rows"], draws=p["draws"], lost_frac=p["lost_frac"], pmax=p["pmax_preclip"],
                       slot_gain_req=sl["gain_req"], draws_sha256=p.get("draws_sha256"))
            for m, floor in (("surrogate", "independent"), ("seq", "paired")):
                gl, el, vlo, vhi = LINES[m]
                q, qp = p[m], p[m]["paired"]
                gr, exc, vr = qp["gain_ratio_minus1"], qp["excess_" + floor], q["vs_slot_var_ratio_median"]
                meets = abs(gr) <= gl and exc <= el and vr is not None and vlo <= vr <= vhi
                at95 = meets and qp["excess_" + floor + "_p95"] <= el and -gl <= qp["gain_ratio_minus1_p025"] and \
                    qp["gain_ratio_minus1_p975"] <= gl
                row[m] = dict(floor=floor, gain_ratio_minus1=gr, gain_lo=qp["gain_ratio_minus1_p025"],
                              gain_hi=qp["gain_ratio_minus1_p975"], rel_mean_err=qp["rel_mean_err"],
                              floor_independent=qp["floor_independent"], floor_paired=qp["floor_paired"],
                              excess=exc, excess_p95=qp["excess_" + floor + "_p95"],
                              excess_independent=qp["excess_independent"], excess_paired=qp["excess_paired"],
                              var_ratio=vr, meets=meets, at95=at95,
                              fails_on=[kk for kk, bad in (("gain", abs(gr) > gl), ("mean", exc > el),
                                                           ("variance", vr is None or not vlo <= vr <= vhi)) if bad])
            dep = {}
            for m in ("surrogate", "seq", "slot"):
                for ln in ("row", "col"):
                    x = p[m]["dep"][ln]
                    dep[f"{m}_{ln}"] = x
            for m in ("seq", "slot"):
                for ln in ("row", "col"):
                    a, b = dep[f"{m}_{ln}"], dep[f"surrogate_{ln}"]
                    dep[f"{m}_{ln}_excess_rms"] = math.sqrt(max(0.0, a["mean_sq"] - b["mean_sq"])) if a and b else None
            dep["v3_pooled_slot_row"], dep["v3_pooled_slot_col"] = sl["rho_row"], sl["rho_col"]
            row["dep"] = dep
            o = old.get((run["task"], p["layer"], p["update"]))
            row["r6"] = dict(surrogate_passes=o["surrogate"]["passes"], seq_passes_v3=o["seq"]["passes"],
                             seq_rel_mean_err=o["seq"]["rel_mean_err"], seq_floor_independent=o["seq"]["noise_floor"]) if o else None
            out.append(row)
    return out, same


# ------------------------------------------------------------------ A2: labels of both arms at n = 3, reversals
def fid3():
    e3 = AR.load("e3")
    fp = {(r["task"], r["seed"]): AR.metric(r) for r in e3 if AR.arm_key(r) == "fp"}
    sur = {(r["task"], r["spec"]["name"], r["algo"], r["seed"]): AR.metric(r) for r in e3 if r["arm"] == "device"}
    seq = {}
    for r in AR.load("fid"):
        seq.setdefault((r["task"], r["spec"]["name"], r["algo"]), {})[r["seed"]] = AR.metric(r)
    cells = {}
    for (t, d, a), by in sorted(seq.items()):
        seeds = sorted(s for s in by if (t, s) in fp and (t, d, a, s) in sur)
        gq = [AR.gap(t, fp[(t, s)], by[s]) for s in seeds]
        gs = [AR.gap(t, fp[(t, s)], sur[(t, d, a, s)]) for s in seeds]
        cq, cs, cd = AR.ci(gq), AR.ci(gs), AR.ci([x - y for x, y in zip(gq, gs)])
        cells[f"{t}__{d}__{a}"] = dict(task=t, device=d, algo=a, seeds=seeds, sur=cs, seq=cq, dgap=cd,
                                       sur_label=AR.label(t, cs), seq_label=AR.label(t, cq),
                                       material=abs(cd["mean"]) > AR.LINE[t] / 2)
    trans = [k for k, c in cells.items() if c["sur_label"] != c["seq_label"]]
    rev = []
    for t in ("mnist", "cifar"):
        ks = [k for k in cells if cells[k]["task"] == t]
        for i, a in enumerate(ks):
            for b in ks[i + 1:]:
                ds = cells[a]["sur"]["mean"] - cells[b]["sur"]["mean"]
                dq = cells[a]["seq"]["mean"] - cells[b]["seq"]["mean"]
                if ds * dq < 0:
                    rev.append(dict(a=a, b=b, sur_sep=ds, seq_sep=dq, registered=abs(ds) > AR.LINE[t] / 2))
    return dict(cells=cells, transitions=trans, reversals=rev,
                registered_reversals=[r for r in rev if r["registered"]],
                material_cells=[k for k, c in cells.items() if c["material"]])


# ------------------------------------------------------------------ A2-R: MNIST MO-ECRAM SGD with the stream at five seeds
def a2r():
    t, d, a = "mnist", "ecram_mo_kim2019", "sgd"
    e3 = AR.load("e3")
    fp = {r["seed"]: AR.metric(r) for r in e3 if AR.arm_key(r) == "fp" and r["task"] == t}
    sur = {r["seed"]: AR.metric(r) for r in e3 if r["arm"] == "device" and r["task"] == t and r["spec"]["name"] == d
           and r["algo"] == a}
    pod = {r["seed"]: r for r in AR.load("fid") if r["task"] == t and r["spec"]["name"] == d and r["algo"] == a}
    desk = {r["seed"]: r for r in load3("fidr") if r["task"] == t and r["spec"]["name"] == d and r["algo"] == a}
    if not desk:
        return None
    rep = None
    if 0 in desk and 0 in pod:
        rep = dict(desk=AR.metric(desk[0]), pod=AR.metric(pod[0]), equal=AR.metric(desk[0]) == AR.metric(pod[0]),
                   desk_device=desk[0].get("device"), pod_device=pod[0].get("device"),
                   gap_diff_pp=AR.gap(t, fp[0], desk[0]["metric"]["acc"]) - AR.gap(t, fp[0], pod[0]["metric"]["acc"]))
    seqm = {s: AR.metric(pod[s]) for s in (0, 1, 2) if s in pod}
    seqm.update({s: AR.metric(desk[s]) for s in (3, 4) if s in desk})
    seeds = sorted(s for s in seqm if s in fp and s in sur)
    gq = [AR.gap(t, fp[s], seqm[s]) for s in seeds]
    gs = [AR.gap(t, fp[s], sur[s]) for s in seeds]
    cq, cs, cd = AR.ci(gq), AR.ci(gs), AR.ci([x - y for x, y in zip(gq, gs)])
    alt = None
    if 0 in desk and 0 in seeds:  # sensitivity: the desk's seed 0 in place of the pod's
        ga = [AR.gap(t, fp[s], AR.metric(desk[0]) if s == 0 else seqm[s]) for s in seeds]
        ca, cda = AR.ci(ga), AR.ci([x - y for x, y in zip(ga, gs)])
        alt = dict(seq=ca, seq_label=AR.label(t, ca), dgap=cda, material=abs(cda["mean"]) > AR.LINE[t] / 2)
    e3sd = st.stdev(gs) if len(gs) > 1 else None
    return dict(alt_desk_seed0=alt, sur_gap_sd=e3sd, seeds=seeds, seq_source={s: ("pod" if s <= 2 else "desk") for s in seeds}, gap_seq=gq, gap_sur=gs,
                seq=cq, sur=cs, dgap=cd, seq_label=AR.label(t, cq), sur_label=AR.label(t, cs),
                material=abs(cd["mean"]) > AR.LINE[t] / 2, reproduction_seed0=rep,
                desk_seconds={s: desk[s].get("seconds") for s in desk})


# ------------------------------------------------------------------ width: arms whose growth beyond the margin is not excluded
def width3():
    e4 = json.load(open(os.path.join(P, "records", "revision", "RESULTS-REVISION.json"), "rb"))["e4"]["cifar"]["arms"]
    return dict(not_excluded_paired=sorted(k for k, v in e4.items() if v["paired"]["ci90"][1] >= v["paired"]["margin"]),
                grows_paired=sorted(k for k, v in e4.items() if v["paired"]["verdict"] == "GROWS"))


def cellname(k):
    t, d, a = k.split("__")
    return f"{TASKL[t]} {DEVLAB[d]} {ALGLAB[a]}"


def tables(PR, F):
    rows = []
    for p in PR:
        s, q = p["surrogate"], p["seq"]
        rows.append(f"{TASKL[p['task']]} {SH[p['device']]} {ALGLAB[p['algo']]} & {p['layer']} & {p['update']} & "
                    f"{100 * p['lost_frac']:.1f} & "
                    f"{fmt(100 * s['gain_ratio_minus1'], 1)} [{fmt(100 * s['gain_lo'], 1)}, {fmt(100 * s['gain_hi'], 1)}] & "
                    f"{fmt(s['excess'])} ({fmt(s['excess_p95'])}) & {fmt(s['var_ratio'])} & "
                    f"{'yes' if s['meets'] else 'no'} & "
                    f"{fmt(100 * q['gain_ratio_minus1'], 1)} [{fmt(100 * q['gain_lo'], 1)}, {fmt(100 * q['gain_hi'], 1)}] & "
                    f"{fmt(q['rel_mean_err'], 3)} & {fmt(q['floor_independent'], 3)} / {fmt(q['floor_paired'], 3)} & "
                    f"{fmt(q['excess'], 3)} ({fmt(q['excess_p95'], 3)}) & {fmt(q['var_ratio'])} & "
                    f"{'yes' if q['meets'] else 'no'}{' (95)' if q['at95'] else ''}\\\\")
    open(os.path.join(TEX, "tables", "rev3_probe.tex"), "wb").write((
        "% generated by revision3/analyze_rev3.py (do not edit)\n"
        "\\begin{table*}[t]\\centering\\scriptsize\\setlength{\\tabcolsep}{3pt}\\caption{Update fidelity, analysed paired "
        "(experiment A1-P; desk rerun of A1 with the draws kept, 16 draws per probe; Li = Li-ECRAM, MO = MO-ECRAM, Prot. = "
        "protonic-inspired). Lost = requested pulse mass removed by the probability clipping (\\%). Surrogate against the "
        "literal stream (its draws are independent of the stream's, so the independent sampling floor applies): gain difference "
        "(\\%, bootstrap 95 \\% interval over draws), excess relative mean difference beyond the floor (bootstrap 95th "
        "percentile), median variance ratio, and whether it meets the registered lines (10 \\%, 0.10, [0.5, 2]). Per-sample "
        "stream (seq) against the literal stream, paired by draw (shared line firings): gain difference, raw relative mean "
        "difference, independent / paired floor, excess beyond the PAIRED floor (95th percentile), variance ratio, and "
        "whether it meets the registered lines (5 \\%, 0.05, [0.8, 1.25]; ``(95)'': also the 95th percentile of the excess "
        "and the gain interval).}\\label{tab:rev3_probe}\n"
        "\\fitbox{\\begin{tabular}{lrrrllrclrcllc}\\toprule & & & & \\multicolumn{4}{c}{surrogate} & \\multicolumn{6}{c}{seq "
        "(paired)}\\\\\\cmidrule(lr){5-8}\\cmidrule(lr){9-14} Case & L. & Upd. & Lost & $\\Delta g$ \\% & excess & var. & "
        "meets & $\\Delta g$ \\% & raw & floor ind./pair. & excess & var. & meets\\\\\\midrule\n" + "\n".join(rows) +
        "\n\\bottomrule\\end{tabular}}\\end{table*}\n").encode("utf-8"))
    rows = []
    for p in PR:
        dp = p["dep"]
        f3 = lambda x: fmt(x, 3) if x is not None else "--"
        rows.append(f"{TASKL[p['task']]} {SH[p['device']]} {ALGLAB[p['algo']]} & {p['layer']} & {p['update']} & "
                    f"{f3(dp['slot_row']['rms'])} / {f3(dp['slot_col']['rms'] if dp['slot_col'] else None)} & "
                    f"{f3(dp['surrogate_row']['rms'])} / {f3(dp['surrogate_col']['rms'] if dp['surrogate_col'] else None)} & "
                    f"{f3(dp['slot_row_excess_rms'])} / {f3(dp['slot_col_excess_rms'])} & "
                    f"{f3(dp['slot_row']['mean_aligned'])} / {f3(dp['slot_col']['mean_aligned'] if dp['slot_col'] else None)} & "
                    f"{f3(dp['slot_row']['line_rms_max'])} / {f3(dp['slot_col']['line_rms_max'] if dp['slot_col'] else None)} & "
                    f"{f3(dp['v3_pooled_slot_row'])} / {f3(dp['v3_pooled_slot_col'])}\\\\")
    open(os.path.join(TEX, "tables", "rev3_dep.tex"), "wb").write((
        "% generated by revision3/analyze_rev3.py (do not edit)\n"
        "\\begin{table*}[t]\\centering\\scriptsize\\caption{Cross-cell dependence of the literal stream's draws (experiment "
        "A1-P), among cells sharing a row / a column, from per-pair Pearson correlations over all pairs (they cannot cancel): "
        "root-mean-square correlation of the literal stream and of the surrogate (whose cells are independent, so its value is "
        "the sampling null at the same number of draws), the excess RMS beyond that null, the mean correlation aligned with the "
        "signs of the expected update, the largest per-line RMS, and the version-3 statistic (a pooled, signed normalised "
        "covariance, which can cancel).}\\label{tab:rev3_dep}\n"
        "\\fitbox{\\begin{tabular}{lrrcccccc}\\toprule Case & L. & Upd. & RMS slot & RMS sur.\\ (null) & excess RMS & aligned mean & "
        "max line RMS & v3 pooled\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}}\\end{table*}\n").encode("utf-8"))
    rows = []
    for k, c in F["cells"].items():
        s, q, d = c["sur"], c["seq"], c["dgap"]
        rows.append(f"{TASKL[c['task']]} & {DEVLAB[c['device']]} {ALGLAB[c['algo']]} & {fmt(s['mean'])} [{fmt(s['lo'])}, "
                    f"{fmt(s['hi'])}] {LAB1[c['sur_label']]} & {fmt(q['mean'])} [{fmt(q['lo'])}, {fmt(q['hi'])}] "
                    f"{LAB1[c['seq_label']]} & {fmt(d['mean'])} [{fmt(d['lo'])}, {fmt(d['hi'])}] & "
                    f"{'yes' if c['material'] else 'no'}\\\\")
    open(os.path.join(TEX, "tables", "rev3_fid.tex"), "wb").write((
        "% generated by revision3/analyze_rev3.py (do not edit)\n"
        "\\begin{table*}[t]\\centering\\footnotesize\\caption{Training fidelity (experiment A2), seeds 0--2 on both arms: mean "
        "gap to FP-SGD (pp) with its 95 \\% interval and label against the 2\\,pp line (P pass, U unresolved, F fail), with the "
        "aggregate surrogate (E3's records) and with the per-sample pulse stream (MNIST: every analog layer; CIFAR: the two "
        "fully connected layers); the paired difference with its 95 \\% interval; material by the registered rule (|mean| "
        "$>$ 1\\,pp). The labels are at $n=3$; the main table's labels are at $n=5$.}\\label{tab:rev3_fid}\n"
        "\\fitbox{\\begin{tabular}{lllll c}\\toprule Task & Cell & surrogate & stream & difference & material\\\\\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\\end{tabular}}\\end{table*}\n").encode("utf-8"))


def macros(PR, same, F, A, W):
    m = {}
    if PR:
        m["RYProbeN"] = str(len(PR))
        m["RYProbeSurMeetsN"] = str(sum(p["surrogate"]["meets"] for p in PR))
        m["RYProbeSurAtNinetyFiveN"] = str(sum(p["surrogate"]["at95"] for p in PR))
        m["RYProbeSeqMeetsN"] = str(sum(p["seq"]["meets"] for p in PR))
        m["RYProbeSeqAtNinetyFiveN"] = str(sum(p["seq"]["at95"] for p in PR))
        m["RYProbeSeqMeetsWord"] = words(sum(p["seq"]["meets"] for p in PR))
        m["RYProbeSeqExcessMax"] = fmt(max(p["seq"]["excess"] for p in PR), 3)
        m["RYProbeSeqExcessPNinetyFiveMax"] = fmt(max(p["seq"]["excess_p95"] for p in PR), 3)
        m["RYProbeSeqRawMax"] = fmt(max(p["seq"]["rel_mean_err"] for p in PR), 3)
        m["RYProbeSeqGainDevMax"] = fmt(100 * max(abs(p["seq"]["gain_ratio_minus1"]) for p in PR), 1)
        m["RYProbeSeqGainCiMax"] = fmt(100 * max(max(abs(p["seq"]["gain_lo"]), abs(p["seq"]["gain_hi"])) for p in PR), 1)
        vr = [p["seq"]["var_ratio"] for p in PR]
        m["RYProbeSeqVarMin"], m["RYProbeSeqVarMax"] = fmt(min(vr), 3), fmt(max(vr), 3)
        ratio = sorted(p["seq"]["floor_paired"] / p["seq"]["floor_independent"] for p in PR)
        m["RYProbeFloorRatioMin"], m["RYProbeFloorRatioMax"] = fmt(ratio[0]), fmt(ratio[-1])
        bad = [p for p in PR if not p["seq"]["meets"]]
        m["RYProbeSeqFailList"] = "; ".join(
            f"{TASKL[p['task']]} {DEVLAB[p['device']]} {ALGLAB[p['algo']]} layer {p['layer']} at update {p['update']} "
            f"(excess {p['seq']['excess']:.3f}, fails on {', '.join(p['seq']['fails_on'])})" for p in bad) or "none"
        m["RYProbeSeqFailTasks"] = ", ".join(sorted({TASKL[p["task"]] for p in bad})) or "none"
        sb = [p for p in PR if not p["surrogate"]["meets"]]
        m["RYProbeSurFailList"] = "; ".join(
            f"{TASKL[p['task']]} {DEVLAB[p['device']]} {ALGLAB[p['algo']]} layer {p['layer']} at update {p['update']} "
            f"({100 * p['lost_frac']:.1f}\\,\\% lost, gain {100 * p['surrogate']['gain_ratio_minus1']:+.1f}\\,\\%, "
            f"excess {p['surrogate']['excess']:.2f})" for p in sb) or "none"
        ok = [p for p in PR if p["surrogate"]["meets"]]
        if ok:
            m["RYProbeOkLostMax"] = fmt(100 * max(p["lost_frac"] for p in ok), 1)
        sv = [p["surrogate"]["var_ratio"] for p in PR]
        m["RYProbeSurVarMin"], m["RYProbeSurVarMax"] = fmt(min(sv)), fmt(max(sv))
        ch = [p for p in PR if p["r6"] and p["r6"]["surrogate_passes"] != p["surrogate"]["meets"]]
        m["RYProbeSurChangedN"] = str(len(ch))
        m["RYProbeSurChangedList"] = "; ".join(
            f"{TASKL[p['task']]} layer {p['layer']} at update {p['update']} (r6 {'pass' if p['r6']['surrogate_passes'] else 'fail'}, "
            f"desk {'pass' if p['surrogate']['meets'] else 'fail'})" for p in ch) or "none"
        ex = [x for p in PR for x in (p["dep"]["slot_row_excess_rms"], p["dep"]["slot_col_excess_rms"]) if x is not None]
        rms = [x["rms"] for p in PR for x in (p["dep"]["slot_row"], p["dep"]["slot_col"]) if x]
        nul = [x["rms"] for p in PR for x in (p["dep"]["surrogate_row"], p["dep"]["surrogate_col"]) if x]
        al = [x["mean_aligned"] for p in PR for x in (p["dep"]["slot_row"], p["dep"]["slot_col"]) if x]
        lm = [x["line_rms_max"] for p in PR for x in (p["dep"]["slot_row"], p["dep"]["slot_col"]) if x]
        m["RYDepExcessMax"] = fmt(max(ex), 3)
        m["RYDepSlotRmsMin"], m["RYDepSlotRmsMax"] = fmt(min(rms), 3), fmt(max(rms), 3)
        m["RYDepNullRmsMin"], m["RYDepNullRmsMax"] = fmt(min(nul), 3), fmt(max(nul), 3)
        m["RYDepAlignedMin"], m["RYDepAlignedMax"] = fmt(min(al), 3), fmt(max(al), 3)
        m["RYDepLineRmsMax"] = fmt(max(lm), 3)
        m["RYDepSmall"] = "yes" if max(ex) <= DEP_SMALL else "no"
        big = [p for p in PR if max(x or 0 for x in (p["dep"]["slot_row_excess_rms"], p["dep"]["slot_col_excess_rms"])) > DEP_SMALL]
        m["RYDepLargeN"] = str(len(big))
        m["RYDepLargeList"] = "; ".join(f"{TASKL[p['task']]} layer {p['layer']} at update {p['update']}" for p in big) or "none"
        a95 = [p for p in PR if p["seq"]["at95"]]
        m["RYProbeSeqAtNinetyFiveList"] = "; ".join(f"{TASKL[p['task']]} layer {p['layer']} at update {p['update']}" for p in a95) or "none"
        n95 = [p for p in PR if p["seq"]["meets"] and not p["seq"]["at95"]]
        m["RYProbeSeqNotNinetyFiveList"] = "; ".join(f"{TASKL[p['task']]} layer {p['layer']} at update {p['update']}" for p in n95) or "none"
        m["RYDepVthreePooledMax"] = fmt(max(max(abs(p["dep"]["v3_pooled_slot_row"] or 0), abs(p["dep"]["v3_pooled_slot_col"] or 0))
                                            for p in PR), 3)
        m["RYProbeRunsN"] = str(len(same))
        m["RYProbeRunsEqualEThree"] = str(sum(s["equal_to_e3"] for s in same))
        m["RYProbeRunsEqualEThreeList"] = ", ".join(TASKL[s["run"].split("__")[1].split("_")[0]] for s in same if s["equal_to_e3"]) or "none"
    # A2 at n = 3 on both arms
    m["RYFidTransN"] = str(len(F["transitions"]))
    m["RYFidTransList"] = "; ".join(f"{cellname(k)} ({F['cells'][k]['sur_label']} with the surrogate, "
                                    f"{F['cells'][k]['seq_label']} with the stream)" for k in F["transitions"]) or "none"
    m["RYFidRevN"] = str(len(F["reversals"]))
    m["RYFidRevWord"] = words(len(F["reversals"]))
    m["RYFidRegRevN"] = str(len(F["registered_reversals"]))
    m["RYFidRevList"] = "; ".join(
        f"{cellname(r['a'])} and {cellname(r['b'])} (separation {fmt(r['sur_sep'])} to {fmt(r['seq_sep'])}\\,pp)"
        for r in F["reversals"]) or "none"
    m["RYFidRevSepMax"] = fmt(max((abs(r["sur_sep"]) for r in F["reversals"]), default=0.0))
    for k, c in F["cells"].items():
        nm = AR.name(f"fid {k}")[2:]
        for arm in ("sur", "seq"):
            m[f"RY{nm}{arm.title()}Lo"], m[f"RY{nm}{arm.title()}Hi"] = fmt(c[arm]["lo"]), fmt(c[arm]["hi"])
            m[f"RY{nm}{arm.title()}Label"] = c[f"{arm}_label"]
    if A:
        m["RYAtwoRSeqGap"], m["RYAtwoRSeqLo"], m["RYAtwoRSeqHi"] = fmt(A["seq"]["mean"]), fmt(A["seq"]["lo"]), fmt(A["seq"]["hi"])
        m["RYAtwoRSurGap"], m["RYAtwoRSurLo"], m["RYAtwoRSurHi"] = fmt(A["sur"]["mean"]), fmt(A["sur"]["lo"]), fmt(A["sur"]["hi"])
        m["RYAtwoRSeqLabel"], m["RYAtwoRSurLabel"] = A["seq_label"], A["sur_label"]
        m["RYAtwoRD"], m["RYAtwoRDLo"], m["RYAtwoRDHi"] = fmt(A["dgap"]["mean"]), fmt(A["dgap"]["lo"]), fmt(A["dgap"]["hi"])
        m["RYAtwoRMaterial"] = "material" if A["material"] else "not material"
        m["RYAtwoRN"] = str(len(A["seeds"]))
        rp = A["reproduction_seed0"]
        if rp:
            m["RYAtwoRSeedZeroEqual"] = "reproduces" if rp["equal"] else "does not reproduce"
            m["RYAtwoRSeedZeroDiff"] = fmt(abs(rp["gap_diff_pp"]))
            m["RYAtwoRSeedZeroDesk"], m["RYAtwoRSeedZeroPod"] = fmt(100 * rp["desk"], 2), fmt(100 * rp["pod"], 2)
        al = A["alt_desk_seed0"]
        if al:
            m["RYAtwoRAltSeqGap"], m["RYAtwoRAltSeqLo"], m["RYAtwoRAltSeqHi"] = fmt(al["seq"]["mean"]), fmt(al["seq"]["lo"]), fmt(al["seq"]["hi"])
            m["RYAtwoRAltLabel"], m["RYAtwoRAltD"] = al["seq_label"], fmt(al["dgap"]["mean"])
            m["RYAtwoRAltMaterial"] = "material" if al["material"] else "not material"
        m["RYAtwoRSurSd"] = fmt(A["sur_gap_sd"])
    m["RYWidthNotExcludedN"] = words(len(W["not_excluded_paired"]))
    return m


def superseded_v3():
    """The version-3 A1 table (r6 probes; its seq floor ignored the pairing) kept for the record, captioned as superseded."""
    BS = chr(92)
    s = open(os.path.join(TEX, "tables", "rev2_probe.tex"), "rb").read().decode("utf-8")
    assert s.count(BS + "caption{") == 1 and s.count(BS + "label{tab:rev2_probe}") == 1
    s = s.replace(BS + "caption{", BS + "caption{Version 3 (superseded: its sampling floor for seq treated the paired draws as independent). ")
    s = s.replace(BS + "label{tab:rev2_probe}", BS + "label{tab:v3s_rev2_probe}")
    s = "% made by revision3/analyze_rev3.py from tables/rev2_probe.tex (caption prefix and label only; do not edit)" + chr(10) + s
    open(os.path.join(TEX, "tables", "v3s_rev2_probe.tex"), "wb").write(s.encode("utf-8"))


def main():
    os.makedirs(R3, exist_ok=True)
    superseded_v3()
    PR, same = probes3()
    F = fid3()
    A = a2r()
    W = width3()
    tables(PR, F)
    m = macros(PR, same, F, A, W)
    res = dict(schema="altone.x1000.me-revision3.results.v1", probes=PR, probe_runs_vs_e3=same, fid=F, a2r=A, width=W,
               lines=LINES, dep_small_line=DEP_SMALL)
    open(os.path.join(R3, "RESULTS-REV3.json"), "wb").write((json.dumps(res, indent=1, default=str) + "\n").encode("utf-8"))
    open(os.path.join(TEX, "numbers_rev3.tex"), "wb").write((
        "% generated by revision3/analyze_rev3.py from records/revision/ and records/revision3/ (do not edit)\n" +
        "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in sorted(m.items()))).encode("utf-8"))
    print("probes", len(PR), "sur meets", m.get("RYProbeSurMeetsN"), "seq meets", m.get("RYProbeSeqMeetsN"),
          "seq at95", m.get("RYProbeSeqAtNinetyFiveN"), "dep small", m.get("RYDepSmall"), "| transitions", F["transitions"],
          "reversals", len(F["reversals"]), "registered", len(F["registered_reversals"]), "| a2r",
          A and (A["seq_label"], fmt(A["dgap"]["mean"]), A["material"], A["reproduction_seed0"]))


if __name__ == "__main__":
    main()
