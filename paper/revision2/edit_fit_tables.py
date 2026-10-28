"""ME-REVISE-2: fit the four tables that still overflowed in build b4b (LaTeX log: catalog 111 pt, probe 68 pt, width 84 pt,
spec 7 pt) by restructuring, not shrinking; and an emergency stretch for a 3.6 pt paragraph. Anchored; run once."""
import pathlib

P = pathlib.Path(__file__).resolve().parent.parent
E = {}


def sub(f, a, b):
    E.setdefault(f, []).append((a, b))


SHORT = '{"ecram_li_tang2018": "Li", "ecram_mo_kim2019": "MO", "protonic_onen2022": "Prot."}'
# width table: short arm names, scriptsize, short verdicts
sub("revision/analyze_rev.py", '''    VA = {"EQUIVALENT": "EQ", "GROWS": "GROWS", "SHRINKS": "SHRINKS", "NO EVIDENCE OF GROWTH BEYOND THE MARGIN": "NG",
          "INCONCLUSIVE": "INC"}''', '''    VA = {"EQUIVALENT": "EQ", "GROWS": "GR", "SHRINKS": "SH", "NO EVIDENCE OF GROWTH BEYOND THE MARGIN": "NG",
          "INCONCLUSIVE": "INC"}
    SH = ''' + SHORT)
sub("revision/analyze_rev.py", '''            rows.append(f"{'CIFAR' if t == 'cifar' else 'LM'} & {DEVLAB.get(dv, dv)} {ALGLAB.get(al, al)} & {gs} & "''',
    '''            rows.append(f"{'CIFAR' if t == 'cifar' else 'LM'} & {SH.get(dv, dv)} {ALGLAB.get(al, al)} & {gs} & "''')
sub("revision/analyze_rev.py", '''"\\\\begin{table*}[t]\\\\centering\\\\footnotesize\\\\caption{Revised width study: mean gap''',
    '''"\\\\begin{table*}[t]\\\\centering\\\\scriptsize\\\\caption{Revised width study (Li = Li-ECRAM, Prot. = protonic-inspired): mean gap''')
sub("revision/analyze_rev.py", '''Verdicts (margins 2 pp, 5 \\\\%): EQ = equivalent at the "
        "endpoints, NG = no evidence of growth beyond the margin, INC = inconclusive.''',
    '''Verdicts (margins 2 pp, 5 \\\\%): EQ = equivalent at the "
        "endpoints, GR = grows, SH = shrinks, NG = no evidence of growth beyond the margin, INC = inconclusive.''')
sub("revision/analyze_rev.py", '"\\\\begin{tabular}{llp{9.2cm}l}', '"\\\\begin{tabular}{llp{8.8cm}l}')
# catalog: no Model column, spreads in the caption
sub("revision2/analyze_rev2.py", '''        g = f"{s.get('gamma_up', 0):.2f}/{s.get('gamma_dn', 0):.2f}"
        if ai:
            g += f" ($\\\\pm${s.get('gamma_up_dtod', 0):g})"''', '''        g = f"{s.get('gamma_up', 0):.2f}/{s.get('gamma_dn', 0):.2f}"''')
sub("revision2/analyze_rev2.py", '''        a = f"{s.get('asym', 0):g}" + (f" ($\\\\pm${s['asym_d2d']:g})" if s.get("asym_d2d") else "")''',
    '''        a = f"{s.get('asym', 0):g}"''')
sub("revision2/analyze_rev2.py", '''        rows.append(f"{DEVLAB[d]} & {e.get('label', '').split(' (')[0]} & {'AIHWKIT' if ai else 'paper'} & {s['n_states']:.0f} & {a} & {g} & "''',
    '''        rows.append(f"{DEVLAB[d]}{'$^*$' if ai else ''} & {e.get('label', '').split(' (')[0]} & {s['n_states']:.0f} & {a} & {g} & "''')
sub("revision2/analyze_rev2.py", '''"(simulator units; provenance per field in records/revision/CATALOG-REV.json). Li- and MO-ECRAM are AIHWKIT's "
            "presets mapped one to one onto its LinearStepDevice (shifted bounds, bound-scaled slopes, slope spread); the "
            "others use the paper's model with bounds $[-1,1]$.''', '''"(simulator units; provenance per field in records/revision/CATALOG-REV.json). $^*$ AIHWKIT's presets mapped one to "
            "one onto its LinearStepDevice (shifted bounds, bound-scaled slopes, device spread 0.05 of the slopes and 0.02 of "
            "the asymmetry); the others use the paper's model with bounds $[-1,1]$.''')
sub("revision2/analyze_rev2.py", '''"(Appendix~\\\\ref{app:original}).}\\\\label{tab:rev_catalog}\\n\\\\begin{tabular}{lllrllllll}\\\\toprule Device & Label & "
            "Model & $n_{\\\\mathrm{st}}$''', '''"(Appendix~\\\\ref{app:original}).}\\\\label{tab:rev_catalog}\\n\\\\begin{tabular}{llrllllll}\\\\toprule Device & Label & "
            "$n_{\\\\mathrm{st}}$''')
# probe table: one short case column, no rho column (the text gives its maximum)
sub("revision2/analyze_rev2.py", '''        rows.append(f"{TASKL[p['task']]} {DEVLAB[p['device']]} {ALGLAB[p['algo']]} & {p['layer']} ({p['shape'][0]}$\\\\times$"
                    f"{p['shape'][1]}) & {p['update']} & {100 * p['lost_frac']:.1f} & {p['slot_gain_req']:.3f} & "''',
    '''        SH = ''' + SHORT + '''
        rows.append(f"{TASKL[p['task']]} {SH[p['device']]} {ALGLAB[p['algo']]} & {p['layer']} ({p['shape'][0]}$\\\\times$"
                    f"{p['shape'][1]}) & {p['update']} & {100 * p['lost_frac']:.1f} & {p['slot_gain_req']:.3f} & "''')
sub("revision2/analyze_rev2.py", '''                    f"{fmt(s['excess'])} / {fmt(q['excess'])} & {fmt(s['var_ratio'])} / {fmt(q['var_ratio'])} & "
                    f"{fmt(p['slot_rho_row'], 3)} / {fmt(s['rho_row'], 3)} & "''',
    '''                    f"{fmt(s['excess'])} / {fmt(q['excess'])} & {fmt(s['var_ratio'])} / {fmt(q['var_ratio'])} & "''')
sub("revision2/analyze_rev2.py", '''median per-cell variance ratio; $\\\\rho$ = mean residual correlation among cells "
        "sharing a row (slot / sur.); faithful''', '''median per-cell variance ratio; faithful''')
sub("revision2/analyze_rev2.py", '''"\\\\begin{tabular}{lllrrrrrrl}\\\\toprule Case & Layer & Upd. & Lost & $g$ & $\\\\Delta g$ & excess & var.\\\\ ratio & $\\\\rho_{\\\\mathrm{row}}$ & "
        "faithful''', '''"\\\\begin{tabular}{lllrrrrrl}\\\\toprule Case & Layer & Upd. & Lost & $g$ & $\\\\Delta g$ & excess & var.\\\\ ratio & "
        "faithful''')
sub("revision2/analyze_rev2.py", '''"\\\\begin{table*}[t]\\\\centering\\\\scriptsize\\\\caption{Update fidelity (experiment A1)''',
    '''"\\\\begin{table*}[t]\\\\centering\\\\scriptsize\\\\caption{Update fidelity (experiment A1; Li = Li-ECRAM, MO = MO-ECRAM, Prot. = protonic-inspired)''')
sub("tex/preamble.tex", "\\usepackage[section]{placeins}", "\\usepackage[section]{placeins}\n\\setlength{\\emergencystretch}{1.5em}")
for f, L in E.items():
    p = P / f
    s = p.read_bytes().decode("utf-8")
    for a, b in L:
        assert s.count(a) == 1, (f, a[:80], s.count(a))
        s = s.replace(a, b)
    p.write_bytes(s.encode("utf-8"))
print("ok", sum(len(v) for v in E.values()))
