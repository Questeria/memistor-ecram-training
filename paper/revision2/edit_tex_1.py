"""ME-REVISE-2: anchored text corrections that need no new run (review 2 findings 2, 3, 5-8 and the additional points).
Each anchor must match exactly once. Run once: python -B revision2/edit_tex_1.py"""
import pathlib

T = pathlib.Path(__file__).resolve().parent.parent / "tex"
E = {}


def sub(f, a, b):
    E.setdefault(f, []).append((a, b))


# ---- finding 6: the three bare placeholders (p. 5)
sub("sec_methods.tex", "ends at RVorderUpDn, the reverse order at RVorderDnUp, and the batch solution at RVorderBatch)",
    "ends at \\RVorderUpDn, the reverse order at \\RVorderDnUp, and the batch solution at \\RVorderBatch)")
# ---- the revised catalog takes the main-table position; the field copy goes to the superseded appendix
sub("sec_methods.tex", "Table~\\ref{tab:catalog} lists the devices. Every field carries a provenance label:",
    "Table~\\ref{tab:rev_catalog} lists the devices as every revised run uses them. Every field carries a provenance label:")
sub("sec_methods.tex", "In Table~\\ref{tab:catalog} the Li-ECRAM and MO-ECRAM rows show the original field\ncopy; the revised runs use",
    "The original field copy of the Li-ECRAM and MO-ECRAM\nrows is kept, labelled as superseded, in Table~\\ref{tab:catalog} (Appendix~\\ref{app:original}); the revised runs use")
sub("sec_methods.tex", "\\input{tables/catalog.tex}", "\\input{tables/rev2_catalog.tex}")
# ---- clipping and reset: the averaging units (finding 7) and the policy wording (finding 1)
sub("sec_main.tex", """      in any layer's mean). This is the hardware's pulse budget, not a simulator error, but it means the effective $A$ rate is
      capped in those layers.""",
    """      in any layer's mean). These are means over the device runs of one layer; the worst single layer record loses
      \\RVLostMaxPct\\,\\% (\\RVLostWorstDev{} \\RVLostWorstAlg, \\RVLostWorstTask{} output layer). The logged fraction is the
      discarded unsigned expected pulse mass, not the norm of the lost signed gradient after cancellation. Clipping the line
      probabilities at one is the update-management policy chosen here (pulse length and update management are configurable
      choices~\\cite{rasch2021aihwkit}), not a property of the devices; it caps the effective $A$ rate in those layers, and the
      aggregate update itself is an approximation (Section~\\ref{sec:fidelity}).""")
sub("sec_main.tex", """\\item \\textbf{Reset residual.} With at most 62 pulses per weight, the pulse reset leaves a mean residual of
      \\RVResetResidMean{} nominal steps on the read $A$ columns; reset pulses are \\RVResetShareMean\\,\\% of all pulses of the
      pulse-reset runs.""",
    """\\item \\textbf{Reset residual.} With at most 62 pulses per weight, the pulse reset leaves a residual on the read $A$
      columns. Averaged with every layer and run weighted equally (a macro-average of the per-layer means), it is
      \\RVResetResidMean{} nominal steps; pooled over all reset events it is \\RVResetResidPooled{} (Li-ECRAM
      \\RVResetResidPooledEcramLiTangTwoZeroOneEight, protonic-inspired \\RVResetResidPooledProtonicOnenTwoZeroTwoTwo, MO-ECRAM
      \\RVResetResidPooledEcramMoKimTwoZeroOneNine); the largest layer mean is \\RVResetResidMax{} (MO-ECRAM). Reset pulses are
      \\RVResetShareMean\\,\\% of all pulses as the mean of the per-run fractions, and \\RVResetSharePooled\\,\\% pooled (all reset
      pulses over all pulses). The macro-averages say what a typical layer and run see; the pooled numbers what the arrays
      receive in total.""")
sub("sec_main.tex", "performance. The FP-SGD seed standard deviation is",
    "performance. The mean digital baselines are \\RVMnistFp\\,\\% and \\RVMnistAdamMetric\\,\\% on MNIST, \\RVCifarFp\\,\\% and\n"
    "\\RVCifarAdamMetric\\,\\% on CIFAR, and \\RVLmFp{} and \\RVLmAdamMetric{} bits per byte on the LM (FP-SGD and Adam). The FP-SGD seed standard deviation is")
sub("sec_main.tex", "general requirement that devices saturate: a sufficiently precise symmetric device can implement SGD, as the MNIST row shows.",
    "general requirement that devices saturate: a sufficiently precise symmetric device can implement SGD, as the MNIST row shows.\n"
    "This reference keeps stochastic pulse counts, bounds, transfer thresholds and the selected update management, so it is not an\n"
    "exact-update, algorithm-only TT reference, and its MNIST success does not show that every other failure is an unavoidable\n"
    "device limitation.")
sub("sec_main.tex", "\\begin{figure}[t]\\centering\n\\includegraphics[width=\\linewidth]{figs/fig_rev_main}",
    "\\begin{figure}[!ht]\\centering\n\\includegraphics[width=\\linewidth]{figs/fig_rev_main}")
# ---- width (finding 2 and the alpha direction)
sub("sec_scale.tex", """width; FP-SGD uses its own selected rate (Table~\\ref{tab:rev_width}). The initial weight scale grows with the width as in the
rest of the paper ($\\alpha$ set from the initialisation bound), which is one mapping policy, not every fixed physical mapping.""",
    """width; FP-SGD uses its own selected rate (Table~\\ref{tab:rev_width}; the rates are in Table~\\ref{tab:rev_selection}). As in the
rest of the paper, each layer's weight scale $\\alpha$ is set from its initialisation bound, so it falls as $1/\\sqrt{\\text{fan-in}}$
when the width raises a layer's fan-in (layers with a fixed fan-in keep theirs); this is one mapping policy, not every fixed
physical mapping.""")
sub("sec_scale.tex", """and covered large non-monotonic changes.""",
    """and covered large non-monotonic changes. The pre-registered contrast is Welch's, which treats the two widths' seed samples as
independent. They are not: every arm of a seed shares the logical initialisation and the data order across widths. Beside the
registered result we therefore report the contrast paired by seed, with the same decision order, as a sensitivity analysis
added after the second review (deviation R4). Both test the endpoints only; neither covers the middle width.""")
sub("sec_scale.tex", """Five seeds are not enough to settle a 2\\,pp margin on this subset.""",
    """Five seeds are not enough to settle a 2\\,pp margin on this subset. Paired by seed, the Li-ECRAM c-TTv2 equivalence survives
(90\\,\\% interval [\\RVEFourCifarEcramLiTangTwoZeroOneEightCttvTwoPairedLo, \\RVEFourCifarEcramLiTangTwoZeroOneEightCttvTwoPairedHi]),
and protonic-inspired c-TTv2 \\emph{grows} ([\\RVEFourCifarProtonicOnenTwoZeroTwoTwoCttvTwoPairedLo,
\\RVEFourCifarProtonicOnenTwoZeroTwoTwoCttvTwoPairedHi]): growth below or at the margin, since the interval includes 2\\,pp. Both of its
endpoint cells still pass against their own FP-SGD controls; a gap that moves from more negative to less negative can grow while
both cells stay acceptable. Li-ECRAM TTv2 stays inconclusive, so for it growth beyond the margin is not excluded.""")
sub("sec_scale.tex", """\\paragraph{What can be said.} Across a factor of four in width, after per-arm learning-rate selection, our pre-registered test
detected no growth of the device gap on either task; on CIFAR it established equivalence for one arm only, and on the LM the
apparent shrinkage reflects the FP-SGD baseline at a fixed budget. Width is not resolved by this study.""",
    """\\paragraph{What can be said.} Across a factor of four in width, after per-arm learning-rate selection, no arm's gap grows
detectably beyond the margin. Endpoint equivalence is established for one CIFAR arm only (Li-ECRAM c-TTv2, by both contrasts);
the paired analysis detects sub-margin growth for one other CIFAR arm (protonic-inspired c-TTv2), which the registered Welch test
does not; for one arm (Li-ECRAM TTv2) growth beyond the margin is not excluded. On the LM the apparent shrinkage reflects the FP-SGD
baseline at a fixed budget. Width dependence is unresolved by this study.""")
# ---- abstract, discussion, conclusion: the width and energy wording (findings 2, 8)
sub("sec_abstract.tex", """does: on the language model the best analog result is \\RVLmAdamBestGap\\,\\% worse in bits per byte. After per-arm tuning we detect
no growth of the gap with width over a factor of four, without establishing equivalence.""",
    """does: on the language model the best analog result is \\RVLmAdamBestGap\\,\\% worse in bits per byte. After per-arm tuning no
arm's gap grows detectably beyond the margin over a factor of four in width; endpoint equivalence was established for one CIFAR
pairing only, and an analysis paired by seed detects sub-margin growth for another.""")
sub("sec_abstract.tex", """\\RVenSysMin--\\RVenChipMax$\\times$ less energy per weight-row than an H100, reported only where the quality is reached.""",
    """\\RVenSysMin--\\RVenChipMax$\\times$ less energy per weight-row than an H100, reported only for cells that pass the margin under
ideal reads.""")
sub("sec_discussion.tex", """\\item \\textbf{Width} is not resolved: no growth was detected over a factor of four after per-arm tuning, equivalence was
      established for one CIFAR arm, and the LM's shrinking gap reflects a weaker FP-SGD baseline at the largest width.""",
    """\\item \\textbf{Width} is not resolved: after per-arm tuning no arm's gap grows detectably beyond the margin over a factor of
      four, endpoint equivalence was established for one CIFAR arm only, a paired-by-seed analysis detects sub-margin growth for
      another, and the LM's shrinking gap reflects a weaker FP-SGD baseline at the largest width.""")
sub("sec_discussion.tex", """\\item \\textbf{Energy} is a conditional projection set almost entirely by borrowed read efficiencies, and it is reported only
      where the quality is reached; against Adam on the LM it is never reached.""",
    """\\item \\textbf{Energy} is a conditional projection set almost entirely by borrowed read efficiencies, and it is reported only
      for cells that pass the stated margin under ideal reads; against Adam on the LM no cell does.""")
sub("sec_roadmap.tex", """No
growth of the gap with width was detected over a factor of four, without establishing equivalence.""",
    """After
per-arm tuning no arm's gap grows detectably beyond the margin over a factor of four in width; endpoint equivalence was established
for one CIFAR pairing only, and a paired-by-seed analysis detects sub-margin growth for another.""")
sub("sec_roadmap.tex", """reached
only where the quality is.""", """reported
only for cells that pass the margin under ideal reads.""")
sub("sec_roadmap.tex", """The remaining questions are experimental: the reset, the reference and the read path in real arrays.""",
    """The remaining questions are computational and methodological (the fidelity of the update surrogate beyond the cases tested
here, dependence-aware statistics, the construction of controls) as well as experimental (the reset, the reference and the read
path in real arrays).""")
# ---- energy (finding 8)
sub("sec_energy.tex", """sustained on one chip, and 6.94\\,TOPS/W for the authors' five-chip system once communication, unused tiles and digital
      work are counted (buses and regulators excluded). We report both.""",
    """sustained, measured on one chip, and 6.94\\,TOPS/W, the authors' \\emph{projected} full-system figure for their five-chip
      system: the chips were not integrated with digital processing, whose time and energy the authors estimate from their
      architecture model, and external components such as system buses and voltage regulators are excluded. We report both.""")
sub("sec_energy.tex", """\\paragraph{Energy to equal quality.} A low energy per operation is worth nothing if the target quality is not reached. We
therefore report the ratio only for cells that PASS against the stated baseline (Table~\\ref{tab:rev_energy}):""",
    """\\paragraph{Conditional ratios for cells that pass the margin.} A low energy per operation is worth nothing without the
accuracy. PASS means that the whole confidence interval of the gap lies within the stated non-inferiority margin under ideal reads,
not that the losses are equal; we therefore print the ratio only for cells that PASS against the stated baseline
(Table~\\ref{tab:rev_energy}), mark FAIL cells as missing the margin and UNRESOLVED cells as ``criterion not established'':""")
sub("sec_energy.tex", """\\textbf{On the LM no analog cell reaches
      Adam's quality, so no energy-to-equal-quality ratio exists against the stronger digital baseline.}""",
    """\\textbf{On the LM no analog cell passes
      the margin against Adam, so no conditional ratio exists against the stronger digital baseline.}""")
sub("sec_energy.tex", """The comparison is at a fixed training budget; reaching a quality at a different number of steps is not modelled.""",
    """The comparison is at a fixed training budget; reaching a quality at a different number of steps is not modelled. No joint
finite-read operating point of accuracy and energy, and no energy-to-target training trajectory, is demonstrated; finite
precision, tiling and utilisation, reference maintenance, the digital TT state, update scheduling and full-system costs stay
outside the ratio.""")
# ---- validation: keep only the qualified AGAD reading
sub("sec_validation.tex", "\\item AGAD is unaffected: \\REOnebAgadSrZero\\% versus \\REOnebAgadSrFive\\%.",
    "\\item AGAD reads \\REOnebAgadSrZero\\% versus \\REOnebAgadSrFive\\% (no change detected with two seeds).")
# ---- body: saved, not released, records
sub("body.tex", "author reviewed the results and the text. All numbers were produced by scripts from the released records.",
    "author reviewed the results and the text. All numbers were produced by scripts from the saved records.")
sub("body.tex", "Claude's role in this section. All numbers were produced by scripts from the released records.",
    "Claude's role in this section. All numbers were produced by scripts from the saved records.")
# ---- appendix B: the revised settings; the v1 table moves to the superseded appendix (finding 3)
sub("app_selection.tex", "\\input{tables/e2.tex}", "Table~\\ref{tab:rev_selection} gives the revised selections that every revised run uses (the "
    "original selection table is Table~\\ref{tab:e2}, Appendix~\\ref{app:original}).\n\n\\input{tables/rev2_selection.tex}")
sub("app_selection.tex", "      \\item TTv2: $\\lambda\\in\\{0.1,0.3,1,3\\}$ and a period of 16 or 64 batches, with or without a matched $A$ learning rate;\n"
    "      \\item c-TTv2: $\\lambda\\in\\{0.1,0.3\\}$, $\\rho\\in\\{0.05,0.2\\}$, with or without reset;",
    "      \\item TTv2: $\\lambda\\in\\{0.1,0.3,1,3\\}$ and a period of 16 or 64 batches, with or without a matched $A$ learning rate;\n"
    "            in the revision also with the pulse reset or none;\n"
    "      \\item c-TTv2: $\\lambda\\in\\{0.1,0.3\\}$, $\\rho\\in\\{0.05,0.2\\}$, with the pulse reset or none;")
sub("app_selection.tex", "\\item \\textbf{CIFAR and LM learning rates} were chosen per width (Section~\\ref{sec:scale}).",
    "\\item \\textbf{CIFAR and LM learning rates} were chosen per width (Section~\\ref{sec:scale}); Adam's on a grid of\n"
    "      $\\{3\\times10^{-4},10^{-3},3\\times10^{-3}\\}$ per task with the edge rule.")
sub("app_original.tex", "\\input{tables/main.tex}\n\\input{tables/scale.tex}\n\\input{tables/spec.tex}\n\\input{tables/spec_rel.tex}\n"
    "\\input{tables/pairs.tex}\n\\input{tables/energy.tex}",
    "\\input{tables/v1s_catalog.tex}\n\\input{tables/v1s_e2.tex}\n\\input{tables/v1s_main.tex}\n\\input{tables/v1s_scale.tex}\n"
    "\\input{tables/v1s_spec.tex}\n\\input{tables/v1s_spec_rel.tex}\n\\input{tables/v1s_pairs.tex}\n\\input{tables/v1s_energy.tex}")
sub("app_original.tex", "\\caption{Original simulator: gap to the exact-update baseline", "\\caption{Version 1 (superseded). Original simulator: gap to the exact-update baseline")
# ---- availability list: long typewriter paths broke the line (63 pt overfull)
sub("body.tex", "\\section{Code and data availability}\\label{sec:availability}", "\\section{Code and data availability}\\label{sec:availability}\n\\begin{sloppypar}")
sub("body.tex", "\\section*{Author contributions and use of AI}",
    "\\end{sloppypar}\n\n\\section*{Author contributions and use of AI}")
# ---- floats stay in their section (the revised figure printed on p. 32 in v2)
sub("preamble.tex", "\\usepackage{booktabs}", "\\usepackage{booktabs}\n\\usepackage[section]{placeins}")
sub("preamble.tex", "\\input{numbers_rev}", "\\input{numbers_rev}\n\\input{numbers_rev2}")

for f, L in E.items():
    p = T / f
    s = p.read_bytes().decode("utf-8")
    for a, b in L:
        assert s.count(a) == 1, (f, a[:60], s.count(a))
        s = s.replace(a, b)
    p.write_bytes(s.encode("utf-8"))
print("ok", sum(len(v) for v in E.values()), "edits in", len(E), "files")
