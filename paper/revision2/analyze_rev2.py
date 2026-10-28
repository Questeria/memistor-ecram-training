"""ME-REVISE-2 analysis (PLAN-REVISION-2.md), written before the records of sitting r6 were read.

    python -B revision2/analyze_rev2.py     (after revision/analyze_rev.py, which re-derives the E5 axes with phase e5fix)

Reads records/revision/runs/{e3,e5,e5fix,fid,fidprobe,fidprobe-probes}, CHOICES-REVISION.json, CATALOG-REV.json,
RESULTS-REVISION.json. Writes records/revision2/RESULTS-REV2.json, tex/numbers_rev2.tex (macros \\RX...) and the tables
tex/tables/rev2_{probe,fid,selection,catalog}.tex.
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

REC = AR.REC
R2 = os.path.join(P, "records", "revision2")
TEX = AR.TEX
fmt, DEVLAB, ALGLAB = AR.fmt, AR.DEVLAB, AR.ALGLAB
TASKL = {"mnist": "MNIST", "cifar": "CIFAR", "lm": "LM"}


def mname(s):
    return "RX" + AR.name(s)[2:]


# ------------------------------------------------------------------ A1: update-fidelity probes
def probes():
    out = []
    for f in sorted(glob.glob(os.path.join(REC, "runs", "fidprobe-probes", "*.probes.json"))):
        d = json.load(open(f, "rb"))
        run = json.load(open(os.path.join(REC, "runs", "fidprobe", d["run"]), "rb"))
        for p in d["probes"]:
            sl = p["slot"]
            row = dict(task=run["task"], device=run["spec"]["name"], algo=run["algo"], layer=p["layer"], update=p["update"],
                       shape=p["shape"], rows=p["rows"], draws=p["draws"], lost_frac=p["lost_frac"],
                       pmax=p["pmax_preclip"], slot_gain_req=sl["gain_req"], slot_rho_row=sl["rho_row"],
                       slot_rho_col=sl["rho_col"])
            for m, (gl, el, vlo, vhi) in (("surrogate", (0.10, 0.10, 0.5, 2.0)), ("seq", (0.05, 0.05, 0.8, 1.25))):
                q = p[m]
                gr = q["gain_req"] / sl["gain_req"] - 1 if sl["gain_req"] else None
                err, fl = q["vs_slot_rel_mean_err"], q["vs_slot_noise_floor"]
                exc = math.sqrt(max(0.0, err * err - fl * fl)) if err is not None and fl is not None else None
                vr = q["vs_slot_var_ratio_median"]
                ok = (gr is not None and abs(gr) <= gl and (exc is None or exc <= el) and vr is not None and vlo <= vr <= vhi)
                row[m] = dict(gain_req=q["gain_req"], gain_ratio_minus1=gr, rel_mean_err=err, noise_floor=fl, excess=exc,
                              var_ratio=vr, rho_row=q["rho_row"], rho_col=q["rho_col"], passes=ok,
                              fails_on=[k for k, bad in (("gain", gr is None or abs(gr) > gl),
                                                         ("mean", exc is not None and exc > el),
                                                         ("variance", vr is None or not vlo <= vr <= vhi)) if bad])
            out.append(row)
    # the probe runs are surrogate runs: their metric against E3's record of the same seed (the probes must not perturb)
    same = []
    e3 = {(r["task"], r["spec"]["name"], r["algo"], r["seed"]): r["metric"] for r in AR.load("e3") if r["arm"] == "device"}
    for r in AR.load("fidprobe"):
        k = (r["task"], r["spec"]["name"], r["algo"], r["seed"])
        same.append(dict(run=r["tag"], equal_to_e3=e3.get(k) == r["metric"], metric=r["metric"], e3=e3.get(k)))
    return out, same


# ------------------------------------------------------------------ A2: training with the seq stream
def fid():
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
        dg = [x - y for x, y in zip(gq, gs)]
        c = AR.ci(dg) if dg and all(math.isfinite(x) for x in dg) else None
        cells[f"{t}__{d}__{a}"] = dict(task=t, device=d, algo=a, seeds=seeds, gap_seq=gq, gap_sur=gs, dgap=dg, dgap_ci=c,
                                       gap_seq_mean=st.fmean(gq) if gq else None, gap_sur_mean=st.fmean(gs) if gs else None,
                                       material=bool(c and abs(c["mean"]) > AR.LINE[t] / 2))
    swaps = []
    for t in ("mnist", "cifar"):
        ks = [k for k, c in cells.items() if c["task"] == t]
        for i, a in enumerate(ks):
            for b in ks[i + 1:]:
                A, B = cells[a], cells[b]
                if abs(A["gap_sur_mean"] - B["gap_sur_mean"]) > AR.LINE[t] / 2 and \
                        (A["gap_sur_mean"] - B["gap_sur_mean"]) * (A["gap_seq_mean"] - B["gap_seq_mean"]) < 0:
                    swaps.append([a, b])
    mat = [k for k, c in cells.items() if c["material"]]
    return dict(cells=cells, material_cells=mat, rank_swaps=swaps,
                verdict="MATERIAL" if (mat or swaps) else "NOT MATERIAL")


# ------------------------------------------------------------------ B: the recentred base against the unrecentred one
def fixsp():
    res = json.load(open(os.path.join(REC, "RESULTS-REVISION.json"), "rb"))["e5"]
    e3 = AR.load("e3")
    fp = {(r["task"], r["seed"]): AR.metric(r) for r in e3 if AR.arm_key(r) == "fp"}
    base = {(r["task"], r["algo"], r["seed"]): AR.metric(r) for r in AR.load("e5") if r["spec"]["name"] == "base"}
    rec = {(r["task"], r["algo"], r["spec"]["name"], r["seed"]): AR.metric(r) for r in AR.load("e5fix")}
    out = {}
    for key, sheet in res.items():
        ax = sheet["axes"].get("asym_fixedsp")
        t, a = sheet["task"], sheet["algo"]
        seeds = sorted(s for (tt, aa, nm, s) in rec if tt == t and aa == a and nm == "asym_fixedsp0.05")
        d = [AR.gap(t, fp[(t, s)], rec[(t, a, "asym_fixedsp0.05", s)]) - AR.gap(t, fp[(t, s)], base[(t, a, s)])
             for s in seeds if (t, a, s) in base]
        out[key] = dict(axis=ax, recentred_minus_unrecentred=AR.ci(d) if len(d) > 1 else None, diffs=d)
    return out


# ------------------------------------------------------------------ tables from the choices and the catalog
def selection_table():
    ch = json.load(open(os.path.join(REC, "CHOICES-REVISION.json"), "rb"))
    import memsim_rev as MR  # noqa: E402  (the UpdateCfg defaults the runs used)
    U = MR.UpdateCfg()
    rows = []
    for al in ("ttv2", "cttv2", "agad"):
        c = ch["tt"][al]
        u = c["ucfg"]
        rs = u.get("tt_reset", "none")
        rdesc = (f"pulse (at most {U.tt_reset_max} pulses, {U.tt_reset_iters} read-correct iterations)" if rs == "pulse"
                 else rs)
        extra = f", $\\rho$ {u['tt_rho']:g}" if "tt_rho" in u else ""
        extra += f", $\\beta$ {u['agad_beta']:g}" if "agad_beta" in u else ""
        rows.append(f"{ALGLAB[al]} & $\\lambda$ {u['tt_lambda']:g}, $A$ lr $\\times${u['tt_lr_ratio']:g}, period "
                    f"{u['tt_period']}{extra} & {rdesc} & {100 * c['val_acc']:.1f}\\\\")
    lr = ch["lr"]
    ad = ch["adam_lr"]
    lrs = (f"FP-SGD: MNIST {lr['mnist']['128']['lr']:g}; CIFAR $c=16/32/64$: "
           + "/".join(f"{lr['cifar'][w]['lr']:g}" for w in ("16", "32", "64")) + "; LM $d=64/128/256$: "
           + "/".join(f"{lr['lm'][w]['lr']:g}" for w in ("64", "128", "256"))
           + f". Adam: MNIST {ad['mnist']['lr']:g}, CIFAR {ad['cifar']['lr']:g}, LM {ad['lm']['lr']:g}.")
    dv = []
    for t, ws in (("cifar", ("16", "32", "64")), ("lm", ("64", "128", "256"))):
        for arm in sorted(ch["devlr"][t][ws[0]]):
            d, a = arm.rsplit("__", 1)
            dv.append(f"{TASKL[t]} {DEVLAB[d]} {ALGLAB[a]}: " + "/".join(f"{ch['devlr'][t][w][arm]['lr']:g}" for w in ws))
    body = ("% generated by revision2/analyze_rev2.py from records/revision/CHOICES-REVISION.json (do not edit)\n"
            "\\begin{table}[t]\\centering\\footnotesize\\caption{Revised settings (repaired simulator), chosen on MNIST "
            "validation with the mid device, seed 0; every E3, E4 and E5 record carries exactly these settings. All TT-family "
            f"runs use BL {U.BL} pulse slots per sample and at most {U.tt_max_pulses} transfer pulses per weight. Better "
            f"chopped algorithm: {ALGLAB[ch['best_chopped']]}; S-ALGO: {ALGLAB[ch['s_algo']]}.}}\\label{{tab:rev_selection}}\n"
            "\\begin{tabular}{p{1.1cm}p{4.2cm}p{4.6cm}r}\\toprule Alg. & Setting & $A$ reset & Val.\\ \\%\\\\\\midrule\n"
            + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n\n\\medskip\\raggedright\\footnotesize Learning rates. "
            + lrs + " Width arms (E4), narrow/mid/wide: " + "; ".join(dv) + ".\n\\end{table}\n")
    open(os.path.join(TEX, "tables", "rev2_selection.tex"), "wb").write(body.encode("utf-8"))


def catalog_table():
    c = json.load(open(os.path.join(REC, "CATALOG-REV.json"), "rb"))["entries"]
    rows = []
    for d in AR.DEVS:
        e = c[d]
        s = e["spec"]
        ai = s.get("bounds_model") == "aihwkit"
        g = f"{s.get('gamma_up', 0):.2f}/{s.get('gamma_dn', 0):.2f}"
        b = f"[{s['u_lo']:.2f}, {s['u_hi']:.2f}]" if ai else "[-1, 1]"
        a = f"{s.get('asym', 0):g}"
        rows.append(f"{DEVLAB[d]}{'$^*$' if ai else ''} & {e.get('label', '').split(' (')[0]} & {s['n_states']:.0f} & {a} & {g} & "
                    f"{b} & {s.get('c2c', 0):g} & {s.get('d2d', 0):g} & {s.get('ref_err', 0):g}\\\\")
    body = ("% generated by revision2/analyze_rev2.py from records/revision/CATALOG-REV.json (do not edit)\n"
            "\\begin{table*}[t]\\centering\\footnotesize\\caption{Revised device catalog, the configuration of every revised run "
            "(simulator units; provenance per field in records/revision/CATALOG-REV.json). $^*$ AIHWKIT's presets mapped one to "
            "one onto its LinearStepDevice (shifted bounds, bound-scaled slopes, device spread 0.05 of the slopes and 0.02 of "
            "the asymmetry); the others use the paper's model with bounds $[-1,1]$. Columns: levels $n_{\\mathrm{st}}$, asymmetry $a$ (device "
            "spread), saturation $\\gamma_+/\\gamma_-$, bounds, write noise $c_{2c}$, step spread $\\sigma_{\\mathrm{d2d}}$, "
            "reference error $\\sigma_r$; no drift. The original field-copy catalog is Table~\\ref{tab:catalog} "
            "(Appendix~\\ref{app:original}).}\\label{tab:rev_catalog}\n\\begin{tabular}{llrllllll}\\toprule Device & Label & "
            "$n_{\\mathrm{st}}$ & $a$ & $\\gamma_+/\\gamma_-$ & bounds & $c_{2c}$ & $\\sigma_{\\mathrm{d2d}}$ & $\\sigma_r$"
            "\\\\\\midrule\n" + "\n".join(rows).replace("_", "\\_").replace("$\\_", "$_").replace("\\_{", "_{")
            + "\n\\bottomrule\\end{tabular}\\end{table*}\n")
    open(os.path.join(TEX, "tables", "rev2_catalog.tex"), "wb").write(body.encode("utf-8"))


# ------------------------------------------------------------------ tables and macros of A and B
def tables_ab(PR, F):
    rows = []
    for p in PR:
        s, q = p["surrogate"], p["seq"]
        SH = {"ecram_li_tang2018": "Li", "ecram_mo_kim2019": "MO", "protonic_onen2022": "Prot."}
        rows.append(f"{TASKL[p['task']]} {SH[p['device']]} {ALGLAB[p['algo']]} & {p['layer']} ({p['shape'][0]}$\\times$"
                    f"{p['shape'][1]}) & {p['update']} & {100 * p['lost_frac']:.1f} & {p['slot_gain_req']:.3f} & "
                    f"{fmt(100 * s['gain_ratio_minus1'], 1)} / {fmt(100 * q['gain_ratio_minus1'], 1)} & "
                    f"{fmt(s['excess'])} / {fmt(q['excess'])} & {fmt(s['var_ratio'])} / {fmt(q['var_ratio'])} & "
                    f"{'yes' if s['passes'] else 'no'} / {'yes' if q['passes'] else 'no'}\\\\")
    open(os.path.join(TEX, "tables", "rev2_probe.tex"), "wb").write((
        "% generated by revision2/analyze_rev2.py (do not edit)\n"
        "\\begin{table*}[t]\\centering\\scriptsize\\caption{Update fidelity (experiment A1; Li = Li-ECRAM, MO = MO-ECRAM, Prot. = protonic-inspired): one training batch applied repeatedly "
        "from the same state by the aggregate surrogate (sur.), the per-sample stream (seq) and the literal pulse-by-pulse stream "
        "(slot). Lost = unsigned requested pulse mass removed by the probability clipping (\\%); $g$ = the slot stream's realised "
        "gain along the requested update; then surrogate / seq against slot: gain difference (\\%), excess relative mean "
        "difference beyond the sampling floor, median per-cell variance ratio; faithful by the pre-registered lines (gain within 10 \\%, excess $\\le$ 0.10, variance ratio "
        "in [0.5, 2]; for seq 5 \\%, 0.05, [0.8, 1.25]).}\\label{tab:rev2_probe}\n"
        "\\begin{tabular}{lllrrrrrl}\\toprule Case & Layer & Upd. & Lost & $g$ & $\\Delta g$ & excess & var.\\ ratio & "
        "faithful\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\\end{table*}\n").encode("utf-8"))
    rows = []
    for k, c in F["cells"].items():
        ci = c["dgap_ci"]
        rows.append(f"{TASKL[c['task']]} & {DEVLAB[c['device']]} {ALGLAB[c['algo']]} & {fmt(c['gap_sur_mean'])} & "
                    f"{fmt(c['gap_seq_mean'])} & {fmt(ci['mean']) if ci else '--'} [{fmt(ci['lo']) if ci else '--'}, "
                    f"{fmt(ci['hi']) if ci else '--'}] & {'yes' if c['material'] else 'no'}\\\\")
    open(os.path.join(TEX, "tables", "rev2_fid.tex"), "wb").write((
        "% generated by revision2/analyze_rev2.py (do not edit)\n"
        "\\begin{table}[t]\\centering\\footnotesize\\caption{Training fidelity (experiment A2): mean gap to FP-SGD (pp, seeds 0--2) "
        "with the aggregate surrogate (E3's records) and with the per-sample pulse stream (MNIST: every analog layer; CIFAR: the "
        "two fully connected layers), the paired difference with its 95 \\% interval, and whether it is material (|mean| "
        "$>$ 1 pp).}\\label{tab:rev2_fid}\n\\begin{tabular}{llrrlc}\\toprule Task & Cell & surrogate & stream & difference [95 \\%] & "
        "material\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\\end{table}\n").encode("utf-8"))


def macros(PR, same, F, X):
    m = {}
    m["RXProbeN"] = str(len(PR))
    m["RXProbeSurPassN"] = str(sum(p["surrogate"]["passes"] for p in PR))
    m["RXProbeSeqPassN"] = str(sum(p["seq"]["passes"] for p in PR))
    if PR:
        m["RXProbeLostMax"] = fmt(100 * max(p["lost_frac"] for p in PR), 1)
        m["RXProbeGainMin"] = fmt(min(p["slot_gain_req"] for p in PR), 3)
        m["RXProbeGainMax"] = fmt(max(p["slot_gain_req"] for p in PR), 3)
        m["RXProbeSurGainDevMax"] = fmt(100 * max(abs(p["surrogate"]["gain_ratio_minus1"]) for p in PR), 1)
        m["RXProbeSeqGainDevMax"] = fmt(100 * max(abs(p["seq"]["gain_ratio_minus1"]) for p in PR), 1)
        vr = [p["surrogate"]["var_ratio"] for p in PR if p["surrogate"]["var_ratio"] is not None]
        m["RXProbeSurVarMin"], m["RXProbeSurVarMax"] = fmt(min(vr)), fmt(max(vr))
        m["RXProbeSlotRhoMax"] = fmt(max(abs(p["slot_rho_row"] or 0) for p in PR), 3)
        fails = sorted({f for p in PR for f in p["surrogate"]["fails_on"]})
        m["RXProbeSurFailsOn"] = ", ".join(fails) if fails else "none"
    bad = [p for p in PR if not p["surrogate"]["passes"]]
    m["RXProbeSurFailList"] = "; ".join(
        f"{TASKL[p['task']]} {DEVLAB[p['device']]} {ALGLAB[p['algo']]} layer {p['layer']} at update {p['update']} "
        f"({100 * p['lost_frac']:.1f}\\,\\% lost, realised gain {p['slot_gain_req']:.3f}, surrogate gain "
        f"{100 * p['surrogate']['gain_ratio_minus1']:+.1f}\\,\\%, excess mean difference {p['surrogate']['excess']:.2f})"
        for p in bad) or "none"
    ok = [p for p in PR if p["surrogate"]["passes"]]
    if ok:
        m["RXProbeOkLostMax"] = fmt(100 * max(p["lost_frac"] for p in ok), 1)
    seqvr = [p["seq"]["var_ratio"] for p in PR if p["seq"]["var_ratio"] is not None]
    if seqvr:
        m["RXProbeSeqVarMin"], m["RXProbeSeqVarMax"] = fmt(min(seqvr), 3), fmt(max(seqvr), 3)
    m["RXProbeSlotRhoMaxAll"] = fmt(max(max(abs(p["slot_rho_row"] or 0), abs(p.get("slot_rho_col") or 0)) for p in PR), 3) if PR else "--"
    # GPU run-to-run reproducibility: E5's base runs repeat E3's protonic-inspired configuration exactly (same seed, init, data)
    e3 = {(r["task"], r["algo"], r["seed"]): AR.metric(r) for r in AR.load("e3")
          if r["arm"] == "device" and r["spec"]["name"] == "protonic_onen2022"}
    for t in ("cifar", "lm"):
        d = [abs(AR.metric(r) / e3[(t, r["algo"], r["seed"])] - 1) for r in AR.load("e5")
             if r["spec"]["name"] == "base" and r["task"] == t and (t, r["algo"], r["seed"]) in e3]
        if d:
            m[f"RXRepro{t.title()}MaxPct"] = fmt(100 * max(d), 2)
            m[f"RXRepro{t.title()}N"] = str(len(d))
    m["RXProbeRunsEqualEThree"] = str(sum(s["equal_to_e3"] for s in same))
    m["RXProbeRunsN"] = str(len(same))
    m["RXFidVerdict"] = F["verdict"].lower()
    m["RXFidCellsN"] = str(len(F["cells"]))
    m["RXFidMaterialN"] = str(len(F["material_cells"]))
    m["RXFidSwapsN"] = str(len(F["rank_swaps"]))
    dm = [abs(c["dgap_ci"]["mean"]) for c in F["cells"].values() if c["dgap_ci"]]
    for t in ("mnist", "cifar"):
        v = [abs(c["dgap_ci"]["mean"]) for c in F["cells"].values() if c["dgap_ci"] and c["task"] == t]
        if v:
            m[f"RXFid{t.title()}MaxAbs"] = fmt(max(v))
    if dm:
        m["RXFidMaxAbs"] = fmt(max(dm))
    for k, c in F["cells"].items():
        if c["dgap_ci"]:
            m[mname(f"fid {k} d")] = fmt(c["dgap_ci"]["mean"])
            m[mname(f"fid {k} lo")], m[mname(f"fid {k} hi")] = fmt(c["dgap_ci"]["lo"]), fmt(c["dgap_ci"]["hi"])
            m[mname(f"fid {k} sur")], m[mname(f"fid {k} seq")] = fmt(c["gap_sur_mean"]), fmt(c["gap_seq_mean"])
    tt = [abs(c["dgap_ci"]["mean"]) for c in F["cells"].values() if c["dgap_ci"] and c["algo"] != "sgd"]
    if tt:
        m["RXFidTtMaxAbs"] = fmt(max(tt))
    m["RXFidMaterialList"] = "; ".join(f"{TASKL[F['cells'][k]['task']]} {DEVLAB[F['cells'][k]['device']]} {ALGLAB[F['cells'][k]['algo']]}" for k in F["material_cells"]) or "none"
    for k, x in X.items():
        ax = x["axis"]
        if ax:
            m[mname(f"fix {k} status")] = ax["status"]
            for v, pnt in ax["points"].items():
                kk = v.replace(".", "p")
                m[mname(f"fix {k} at {kk} gap")] = fmt(pnt["gap"]["mean"])
                m[mname(f"fix {k} at {kk} label")] = pnt["label"]
        c = x["recentred_minus_unrecentred"]
        if c:
            m[mname(f"fix {k} rmu")], m[mname(f"fix {k} rmu lo")], m[mname(f"fix {k} rmu hi")] = \
                fmt(c["mean"]), fmt(c["lo"]), fmt(c["hi"])
    return m


def superseded_copies():
    """Review 2: an isolated version-1 table must say that it is superseded. tex/tables/v1s_<name>.tex = the v1 table (made by
    analyze.py from the v1 records, unchanged) with "Version 1 (superseded)." put at the start of its caption."""
    for n in ("catalog", "e2", "main", "scale", "spec", "spec_rel", "pairs", "energy"):
        s = open(os.path.join(TEX, "tables", n + ".tex"), "rb").read().decode("utf-8")
        assert s.count("\\caption{") == 1, n
        s = s.replace("\\caption{", "\\caption{Version 1 (superseded). ")
        s = "% made by revision2/analyze_rev2.py from tables/" + n + ".tex (caption prefix only; do not edit)\n" + s
        open(os.path.join(TEX, "tables", "v1s_" + n + ".tex"), "wb").write(s.encode("utf-8"))


def main():
    os.makedirs(R2, exist_ok=True)
    superseded_copies()
    PR, same = probes()
    F = fid()
    X = fixsp()
    selection_table()
    catalog_table()
    tables_ab(PR, F)
    m = macros(PR, same, F, X)
    res = dict(schema="altone.x1000.me-revision2.results.v1", probes=PR, probe_runs_vs_e3=same, fid=F, fixsp=X)
    open(os.path.join(R2, "RESULTS-REV2.json"), "wb").write((json.dumps(res, indent=1, default=str) + "\n").encode("utf-8"))
    open(os.path.join(TEX, "numbers_rev2.tex"), "wb").write((
        "% generated by revision2/analyze_rev2.py from records/revision/ (do not edit)\n" +
        "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in sorted(m.items()))).encode("utf-8"))
    print("probes", len(PR), "sur pass", m["RXProbeSurPassN"], "seq pass", m["RXProbeSeqPassN"], "| fid", F["verdict"],
          "material", F["material_cells"], "swaps", F["rank_swaps"])
    for k, x in X.items():
        print("fixsp", k, x["axis"]["status"] if x["axis"] else None, x["axis"]["weakest_passing"] if x["axis"] else None,
              x["recentred_minus_unrecentred"] and fmt(x["recentred_minus_unrecentred"]["mean"]))


if __name__ == "__main__":
    main()
