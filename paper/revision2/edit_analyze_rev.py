"""ME-REVISE-2: anchored edits of revision/analyze_rev.py for review 2 (each anchor must match exactly once).

    python -B revision2/edit_analyze_rev.py        (run once; a second run fails on its first anchor)
1. width: the paired-by-seed contrast beside the registered Welch one (finding 2, DEVIATIONS R4), with macros;
2. the fixed-symmetry anchor: the recentred run asym_fixedsp0.05 of phase e5fix, never the unrecentred base (finding 4);
3. pooled reset statistics beside the macro-averages, and the worst lost-update layer's identity (finding 7);
4. tables: the width table with both contrasts and within the page, the spec and D1 tables within the page (finding 6),
   the energy table's labels (finding 8).
"""
import pathlib

p = pathlib.Path(__file__).resolve().parent.parent / "revision" / "analyze_rev.py"
s = p.read_bytes().decode()
SUBS = []
SUBS.append(("width_paired_fn", '''def e4():
    rs = load("e4")''', '''def width_paired(task, gl, gh):
    """REVISION 2 (DEVIATIONS R4, added after review 2): the endpoint contrast paired by seed (the arms of one seed share
    the logical initialisation and the data order across widths), with the registered decision order."""
    m = LINE[task]
    if any(not math.isfinite(x) for x in gl + gh):
        return dict(verdict="INCONCLUSIVE (a run diverged)")
    dd = [h - l for h, l in zip(gh, gl)]
    n = len(dd)
    D, se = st.fmean(dd), st.stdev(dd) / math.sqrt(n)
    t90 = tq(T95, n - 1)
    lo90, hi90 = D - t90 * se, D + t90 * se
    if -m < lo90 and hi90 < m:
        v = "EQUIVALENT"
    elif lo90 > 0:
        v = "GROWS"
    elif hi90 < 0:
        v = "SHRINKS"
    elif hi90 < m:
        v = "NO EVIDENCE OF GROWTH BEYOND THE MARGIN"
    else:
        v = "INCONCLUSIVE"
    return dict(D=D, se=se, df=n - 1, ci90=[lo90, hi90], margin=m, verdict=v, diffs=dd)


def e4():
    rs = load("e4")'''))
SUBS.append(("width_paired_use",
             '''                res[a] = dict(widths=per, test=width_verdict(task, per[ws[0]]["gaps"], per[ws[-1]]["gaps"]))''',
             '''                res[a] = dict(widths=per, test=width_verdict(task, per[ws[0]]["gaps"], per[ws[-1]]["gaps"]),
                              paired=width_paired(task, per[ws[0]]["gaps"], per[ws[-1]]["gaps"]))'''))
SUBS.append(("width_paired_macros", '''            for w, c in x["widths"].items():
                macros[name(f"e4 {t} {a} w{w} gap")] = fmt(c["gap"]["mean"])''', '''            Pd = x["paired"]
            macros[name(f"e4 {t} {a} paired verdict")] = Pd["verdict"].lower()
            if "D" in Pd:
                macros[name(f"e4 {t} {a} paired lo")], macros[name(f"e4 {t} {a} paired hi")] = fmt(Pd["ci90"][0]), fmt(Pd["ci90"][1])
            for w, c in x["widths"].items():
                macros[name(f"e4 {t} {a} w{w} gap")] = fmt(c["gap"]["mean"])'''))
SUBS.append(("width_paired_counts", '''        vs = [x["test"]["verdict"] for x in d["arms"].values()]
        for v in set(vs):
            macros[name(f"e4 {t} n {v}")] = str(vs.count(v))''', '''        vs = [x["test"]["verdict"] for x in d["arms"].values()]
        for v in set(vs):
            macros[name(f"e4 {t} n {v}")] = str(vs.count(v))
        vp = [x["paired"]["verdict"] for x in d["arms"].values()]
        for v in set(vp):
            macros[name(f"e4 {t} n paired {v}")] = str(vp.count(v))'''))
SUBS.append(("e5fix_load", '''    rs = load("e5")
    e3r = load("e3")''', '''    rs = load("e5") + load("e5fix")  # REVISION 2: e5fix = the recentred base (0.05) and the zero point (PLAN-REVISION-2.md)
    e3r = load("e3")'''))
SUBS.append(("e5fix_anchor", '''            if ax == "asym_fixedsp":
                vals[basev] = cells.get("base")  # the base differs only by the re-centring: kept as the anchor
''', '''            # REVISION 2 (review 2 finding 4): the v2 code copied the unrecentred base in as this axis's anchor; the anchor
            # is now the recentred run asym_fixedsp0.05 itself (absent -> the axis is not established)
'''))
SUBS.append(("e5_status_noanchor", '''            if vals.get(basev) is None or vals[basev]["label"] != "PASS":
                status = "not established (the base point does not pass)"''', '''            if vals.get(basev) is None:
                status = "not established (no run at the base value)"
            elif vals[basev]["label"] != "PASS":
                status = "not established (the base point does not pass)"'''))
SUBS.append(("reset_pooled", '''    if resid:
        m["RVResetResidMean"], m["RVResetResidMax"] = fmt(st.fmean(resid)), fmt(max(resid))
        m["RVResetShareMean"] = fmt(100 * st.fmean(share), 1)''', '''    if resid:
        m["RVResetResidMean"], m["RVResetResidMax"] = fmt(st.fmean(resid)), fmt(max(resid))
        m["RVResetShareMean"] = fmt(100 * st.fmean(share), 1)
    # REVISION 2: pooled over reset events (each reset weight is re-read tt_reset_iters - 1 times, so the event count is
    # reset_extra_reads / (iters - 1)) and over pulses; and per device
    wr = nr = rp = tp = 0.0
    per = {}
    for r in load("e3"):
        if r["arm"] != "device" or r["spec"]["name"] not in DEVS:
            continue
        it = (r.get("ucfg") or {}).get("tt_reset_iters", 2)
        pl = [l for l in r["layers"] if l.get("reset") == "pulse" and l.get("reset_resid_steps") is not None]
        if not pl:
            continue
        q = per.setdefault(r["spec"]["name"], [0.0, 0.0, 0.0])
        for l in pl:
            n = l["reset_extra_reads"] / max(1, it - 1)
            wr += l["reset_resid_steps"] * n
            nr += n
            q[0] += l["reset_resid_steps"] * n
            q[1] += n
            q[2] = max(q[2], l["reset_resid_steps"])
        rp += sum(l.get("reset_pulses", 0.0) for l in r["layers"])
        tp += sum(l["pulses"] for l in r["layers"])
    if nr:
        m["RVResetResidPooled"] = fmt(wr / nr)
        m["RVResetSharePooled"] = fmt(100 * rp / tp, 2)
        for dname, q in per.items():
            m[name(f"reset resid pooled {dname}")] = fmt(q[0] / q[1], 1)
            m[name(f"reset resid max {dname}")] = fmt(q[2], 0)
    lostl = [(l.get("update_lost_frac", 0.0), r["task"], r["spec"]["name"], r["algo"], i) for r in load("e3")
             if r["arm"] == "device" and r["spec"]["name"] in DEVS for i, l in enumerate(r["layers"])]
    w = max(lostl)
    m["RVLostWorstTask"], m["RVLostWorstDev"], m["RVLostWorstAlg"] = w[1].upper(), DEVLAB[w[2]], ALGLAB[w[3]]'''))
SUBS.append(("width_table", '''    rows = []
    for t, d in E4.items():
        for a, x in d["arms"].items():
            dv, al = a.rsplit("__", 1)
            gs = " & ".join(cellfmt(x["widths"][w]) for w in d["widths"])
            T = x["test"]
            rows.append(f"{'CIFAR' if t == 'cifar' else 'LM'} & {DEVLAB.get(dv, dv)} & {ALGLAB.get(al, al)} & {gs} & "
                        f"{fmt(T.get('D'))} [{fmt((T.get('ci90') or [None])[0])}, {fmt((T.get('ci90') or [None, None])[1])}] & "
                        f"{T['verdict'].replace('NO EVIDENCE OF GROWTH BEYOND THE MARGIN', 'no growth $>$ margin')}\\\\\\\\")
    open(os.path.join(TEX, "tables", "rev_width.tex"), "wb").write((
        "\\\\begin{table*}[t]\\\\centering\\\\scriptsize\\\\caption{Revised width study: gap per width (5 seeds, each arm at its own "
        "selected learning rate), the endpoint contrast $D$ (widest minus narrowest) with its 90 \\\\% Welch interval, and the "
        "pre-registered equivalence verdict (margins 2 pp CIFAR, 5 \\\\% LM).}\\\\label{tab:rev_width}\\n\\\\begin{tabular}{lllccccl}"
        "\\\\toprule Task & Device & Alg. & narrow & mid & wide & $D$ [90 \\\\%] & verdict\\\\\\\\\\\\midrule\\n" + "\\n".join(rows) +
        "\\n\\\\bottomrule\\\\end{tabular}\\\\end{table*}\\n").encode("utf-8"))''', '''    rows = []
    VA = {"EQUIVALENT": "EQ", "GROWS": "GROWS", "SHRINKS": "SHRINKS", "NO EVIDENCE OF GROWTH BEYOND THE MARGIN": "NG",
          "INCONCLUSIVE": "INC"}
    for t, d in E4.items():
        for a, x in d["arms"].items():
            dv, al = a.rsplit("__", 1)
            gs = " / ".join(fmt(x["widths"][w]["gap"]["mean"]) for w in d["widths"])
            iv = lambda T: (f"{fmt(T.get('D'))} [{fmt((T.get('ci90') or [None])[0])}, "
                            f"{fmt((T.get('ci90') or [None, None])[1])}] {VA.get(T['verdict'], T['verdict'])}")
            rows.append(f"{'CIFAR' if t == 'cifar' else 'LM'} & {DEVLAB.get(dv, dv)} {ALGLAB.get(al, al)} & {gs} & "
                        f"{iv(x['test'])} & {iv(x['paired'])}\\\\\\\\")
    open(os.path.join(TEX, "tables", "rev_width.tex"), "wb").write((
        "\\\\begin{table*}[t]\\\\centering\\\\footnotesize\\\\caption{Revised width study: mean gap at the narrow / mid / wide "
        "width (5 seeds, each arm at its own selected learning rate; CIFAR $c=16/32/64$ in pp, LM $d=64/128/256$ in \\\\%), and "
        "the endpoint contrast $D$ (widest minus narrowest) with its 90 \\\\% interval and verdict, by the pre-registered Welch "
        "test and, added after review 2 (deviation R4), paired by seed. Verdicts (margins 2 pp, 5 \\\\%): EQ = equivalent at the "
        "endpoints, NG = no evidence of growth beyond the margin, INC = inconclusive. An endpoint test says nothing about the "
        "middle width.}\\\\label{tab:rev_width}\\n\\\\begin{tabular}{llccc}"
        "\\\\toprule Task & Arm & gap narrow / mid / wide & Welch $D$ [90 \\\\%] & paired $D$ [90 \\\\%]\\\\\\\\\\\\midrule\\n"
        + "\\n".join(rows) + "\\n\\\\bottomrule\\\\end{tabular}\\\\end{table*}\\n").encode("utf-8"))'''))
SUBS.append(("spec_width", '"\\\\begin{tabular}{llp{11cm}l}', '"\\\\begin{tabular}{llp{9.2cm}l}'))
SUBS.append(("d1_cols", '''    V = [("old", "original"), ("rev", "seed-matched, ideal reset"), ("rev_pulse", "pulse reset"), ("rev_alt", "alt.\\\\ pairs"),
         ("rev_none", "no reset"), ("rev_pub", "published-style")]''', '''    V = [("old", "orig."), ("rev", "ideal"), ("rev_pulse", "pulse"), ("rev_alt", "alt."),
         ("rev_none", "none"), ("rev_pub", "publ.")]'''))
SUBS.append(("d1_devs", '''        for dev, dl in (("protonic_onen2022", "Protonic-insp."), ("ecram_li_tang2018_papermap", "Li-ECRAM (old map)"),
                        ("ecram_li_tang2018", "Li-ECRAM (AIHWKIT map)")):''', '''        for dev, dl in (("protonic_onen2022", "Protonic-insp."), ("ecram_li_tang2018_papermap", "Li (old map)"),
                        ("ecram_li_tang2018", "Li (AIHWKIT)")):'''))
SUBS.append(("d1_caption", '''P/F/U against 2 pp) at the original selections. Columns: the original simulator; the repaired random streams with the "
        "original ideal reset; then the reset replaced by the pulse reset, 31 alternating pulse pairs, or none; the "
        "published-style TTv2.''', '''P/F/U against 2 pp) at the original selections. Columns: orig. = the original simulator; ideal = the repaired "
        "random streams with the original ideal reset; then the reset replaced by the pulse reset (pulse), 31 alternating pulse "
        "pairs (alt.), or none; publ. = the published-style TTv2.'''))
SUBS.append(("energy_cells", '''                    cells.append(f"{v['chip_12p4']:.0f} / {v['system_6p94']:.0f}" if q["label"] == "PASS" else "n.r.")''',
             '''                    cells.append(f"{v['chip_12p4']:.0f} / {v['system_6p94']:.0f}" if q["label"] == "PASS" else
                                 ("fail" if q["label"] == "FAIL" else "n.e."))'''))
SUBS.append(("energy_caption", '''"\\\\begin{table*}[t]\\\\centering\\\\scriptsize\\\\caption{Conditional energy projection at equal quality: the GPU-to-analog "
        "energy ratio per weight per row (12.4 TOPS/W chip figure / 6.94 TOPS/W system figure of the same inference chip), "
        "printed only where the cell PASSES against the baseline; n.r. = the quality is not reached (FAIL or UNRESOLVED).}"''',
             '''"\\\\begin{table*}[t]\\\\centering\\\\scriptsize\\\\caption{Conditional energy ratios for cells that pass the stated "
        "non-inferiority margin under ideal reads: the GPU-to-analog energy ratio per weight per row (12.4 TOPS/W measured "
        "chip figure / 6.94 TOPS/W projected system figure of the same inference chip, which includes estimated digital "
        "processing), printed only where the cell PASSES against the baseline; fail = the cell FAILS the margin; n.e. = the "
        "criterion is not established (UNRESOLVED). No finite-read operating point is demonstrated.}"'''))
for name_, a, b in SUBS:
    assert s.count(a) == 1, (name_, s.count(a))
    s = s.replace(a, b)
p.write_bytes(s.encode())
print("ok", len(SUBS))
