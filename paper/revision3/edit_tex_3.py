"""ME-REVISE-3: anchored text corrections for version 4 (review 3; PLAN-REVISION-3.md). Each anchor must match exactly once.
The version-3 tex is copied to tex/v3/ first (once). Run once: python -B revision3/edit_tex_3.py"""
import pathlib
import shutil

PAPER = pathlib.Path(__file__).resolve().parent.parent
T = PAPER / "tex"
E = {}


def sub(f, a, b):
    E.setdefault(f, []).append((a, b))


# ---------------------------------------------------------------- finding 3: the width interval (abstract, scale, discussion, roadmap)
sub("sec_abstract.tex", "endpoint equivalence was established for one CIFAR pairing only, and an analysis\n"
    "paired by seed detects sub-margin growth for another.",
    "endpoint equivalence was established for one CIFAR pairing only, and an analysis\n"
    "paired by seed detects growth for another without resolving its size against the margin.")
sub("sec_scale.tex", "\\RVEFourCifarProtonicOnenTwoZeroTwoTwoCttvTwoPairedHi]): growth below or at the margin, since the interval includes 2\\,pp. Both of its",
    "\\RVEFourCifarProtonicOnenTwoZeroTwoTwoCttvTwoPairedHi]): the growth is detected, but its size against the margin is\n"
    "unresolved: the interval includes 2\\,pp, so growth beyond the margin is not excluded. Both of its")
sub("sec_scale.tex", "Li-ECRAM TTv2 stays inconclusive, so for it growth beyond the margin is not excluded.",
    "Li-ECRAM TTv2 stays inconclusive, so growth beyond the margin is not excluded for it either.")
sub("sec_scale.tex", "the paired analysis detects sub-margin growth for one other CIFAR arm (protonic-inspired c-TTv2), which the registered Welch test\n"
    "does not; for one arm (Li-ECRAM TTv2) growth beyond the margin is not excluded.",
    "the paired analysis detects growth for one other CIFAR arm (protonic-inspired c-TTv2), which the registered Welch test\n"
    "does not, without resolving its size against the margin; for \\RYWidthNotExcludedN{} arms (protonic-inspired c-TTv2 and\n"
    "Li-ECRAM TTv2) growth beyond the margin is not excluded.")
sub("sec_discussion.tex", "a paired-by-seed analysis detects sub-margin growth for\n      another,",
    "a paired-by-seed analysis detects growth for\n      another without resolving its size against the margin (growth beyond it is not excluded there or for\n"
    "      Li-ECRAM TTv2),")
sub("sec_roadmap.tex", "for one CIFAR pairing only, and a paired-by-seed analysis detects sub-margin growth for another.",
    "for one CIFAR pairing only, and a paired-by-seed analysis detects growth for another, of a size not resolved against\n"
    "the margin.")

# ---------------------------------------------------------------- minor: which mean the reset bullet uses
sub("sec_discussion.tex", "it leaves a residual (mean\n      \\RVResetResidMean{} nominal steps)",
    "it leaves a residual (mean over runs\n      \\RVResetResidMean{} nominal steps, pooled over all reset events \\RVResetResidPooled)")

# ---------------------------------------------------------------- finding 5: availability and revision history
sub("body.tex", "\\item the plans (\\texttt{PLAN-PAPER.md}, \\texttt{PLAN-REVISION.md}), their deviations (\\texttt{DEVIATIONS-PAPER.md}) and the\n"
    "      response to the independent review (\\texttt{RESPONSE-TO-REVIEW.md});\n"
    "\\item the original simulator and the repaired one (\\texttt{sim/*\\_rev.py}), with their checks;",
    "\\item the plans (\\texttt{PLAN-PAPER.md}, \\texttt{PLAN-REVISION.md}, \\texttt{PLAN-REVISION-2.md},\n"
    "      \\texttt{PLAN-REVISION-3.md}), their deviations (\\texttt{DEVIATIONS-PAPER.md}) and the responses to the three\n"
    "      independent reviews (\\texttt{RESPONSE-TO-REVIEW.md}, \\texttt{RESPONSE-TO-REVIEW-2.md},\n"
    "      \\texttt{RESPONSE-TO-REVIEW-3.md});\n"
    "\\item the original simulator and the repaired one (\\texttt{sim/*\\_rev.py}), the explicit pulse streams and probes\n"
    "      (\\texttt{sim/*\\_rev2.py}, \\texttt{sim/*\\_rev3.py}), with their checks;")
sub("body.tex", "\\texttt{revision/analyze\\_d1.py}, \\texttt{revision/compare\\_curves.py}, \\texttt{energy/energy\\_rev.py});",
    "\\texttt{revision/analyze\\_d1.py}, \\texttt{revision/compare\\_curves.py}, \\texttt{energy/energy\\_rev.py},\n"
    "      \\texttt{revision2/analyze\\_rev2.py}, \\texttt{revision3/analyze\\_rev3.py});")
sub("app_revision.tex", "technical review (October 26, 2026) recommended major revision with thirteen findings. Version 2 (this paper) answers them; the\n"
    "full response, finding by finding,",
    "technical review (October 26, 2026) recommended major revision with thirteen findings. Version 2 answered them; the\n"
    "full response, finding by finding,")
sub("app_revision.tex", "are recorded in \\texttt{DEVIATIONS-PAPER.md}.\n",
    "are recorded in \\texttt{DEVIATIONS-PAPER.md}. Version 3 (October 26, 2026) answered a second review (eight findings;\n"
    "\\texttt{RESPONSE-TO-REVIEW-2.md}, plan \\texttt{PLAN-REVISION-2.md}): the pulse-fidelity experiments of\n"
    "Section~\\ref{sec:fidelity}, the recentred fixed-symmetry control, the width contrasts paired by seed and the revised\n"
    "settings tables. Version 4 (October 27, 2026; this paper) answers a third review (five findings;\n"
    "\\texttt{RESPONSE-TO-REVIEW-3.md}, plan \\texttt{PLAN-REVISION-3.md}, committed before its runs): the per-sample stream is\n"
    "compared with the literal one paired by draw, with bootstrap bounds, in a desk rerun of the update probes that keeps the\n"
    "draws; the cross-cell dependence is measured by per-pair correlations that cannot cancel; the training comparison reports\n"
    "both arms' labels and every rank reversal; the open training rerun of the one material cell was done; and an interval that\n"
    "includes the width margin is no longer read as growth below it.\n")

# ---------------------------------------------------------------- part B (written after the A1-P and A2-R results)
FID_HEAD = "\\paragraph{Update level (A1).}"
FID_TAIL = r"""\paragraph{Update level (A1).} At two points of training, one batch's inputs, errors and array state were taken from surrogate
training runs and applied repeatedly from the same state by three methods: the surrogate; the explicit stream applied pulse by
pulse (Bernoulli line firings, the per-pulse device step, write noise and bounds after every pulse; the literal stream); and a
per-sample form of the same stream (seq), which replays the literal stream's line firings. Within one sample every pulse of a
cell has the same sign, so seq applies the sample's train in closed form. Its write noise is an approximation: it is added once
per sample at the pre-sample state (standard deviation $c_{2c}\sqrt{n}$ times the local step for $n$ pulses), and the bounds are
applied after each sample, where the literal stream applies noise and bounds after every pulse. The cases cover clipped and
unclipped layers: MNIST Li-ECRAM c-TTv2 (first and output layer), CIFAR MO-ECRAM AGAD (fully connected and output layer; the
worst-clipped layer of the main table) and the LM protonic-inspired c-TTv2 (embedding and output layer), \RYProbeN{} probes.
Version 3 compared seq with the literal stream as if their draws were independent, although they share the line firings, so
its sampling floor could hide a real difference (Table~\ref{tab:v3s_rev2_probe}, Appendix~\ref{app:revision}). The probes were
therefore run again with the draws kept, 16 per probe, and seq is now compared paired by draw, with bootstrap bounds over whole
draws (Table~\ref{tab:rev3_probe}; \texttt{PLAN-REVISION-3.md}).
\begin{itemize}
\item The surrogate, whose draws are independent of the literal stream's, meets the pre-registered lines (realised gain along
      the requested update within 10\,\%, mean difference beyond sampling noise at most 0.10, median variance ratio in
      $[0.5, 2]$) on \RYProbeSurMeetsN{} of \RYProbeN{} probes, including layers that lose up to \RYProbeOkLostMax\,\% of the
      requested pulse mass to clipping; its variance ratio lies between \RYProbeSurVarMin{} and \RYProbeSurVarMax. These are
      point estimates: with 16 draws its bootstrap bounds stay within the lines on \RYProbeSurAtNinetyFiveN{} of them.
\item It fails on the two probes of the most clipped layer: \RYProbeSurFailList. There almost nothing of the requested update
      survives the clipping, and the surrogate's Poisson counts, which can exceed the slot budget that caps the stream, no longer
      match it (review 2's limiting case: Poisson(31) exceeds 31 with probability 0.4524).
\item Paired by draw, seq meets its registered lines (gain within 5\,\%, excess at most 0.05, variance ratio in
      $[0.8, 1.25]$) on \RYProbeSeqMeetsN{} of \RYProbeN{} probes. The paired floor, \RYProbeFloorRatioMin--\RYProbeFloorRatioMax{}
      times the independent one, accounts for the raw relative difference (at most \RYProbeSeqRawMax) up to an excess of at
      most \RYProbeSeqExcessMax; gains agree within \RYProbeSeqGainDevMax\,\% and variance ratios lie in
      \RYProbeSeqVarMin--\RYProbeSeqVarMax. The bootstrap bounds stay within the lines on \RYProbeSeqAtNinetyFiveN{} probes
      (\RYProbeSeqAtNinetyFiveList). On the others (\RYProbeSeqNotNinetyFiveList) 16 draws cannot exclude a mean discrepancy of
      up to \RYProbeSeqExcessPNinetyFiveMax. Seq therefore meets our registered diagnostic thresholds; that is a diagnostic,
      not a demonstration that it is equivalent to the literal stream.
\item Shared lines make the literal stream's cells dependent; the surrogate's independent draws do not reproduce this.
      Measured by per-pair correlations, which cannot cancel (Table~\ref{tab:rev3_dep}), the root-mean-square correlation among
      cells sharing a line exceeds the surrogate's sampling null by up to \RYDepExcessMax{} (mean correlation aligned with the
      expected update's signs up to \RYDepAlignedMax), by more than 0.05 on \RYDepLargeN{} of \RYProbeN{} probes
      (\RYDepLargeList). The statistic of version 3, a pooled, signed normalised covariance, stays within \RYDepVthreePooledMax{}
      in absolute value on the same draws, because positive and negative terms cancel and unequal cell variances are pooled.
      The cross-cell dependence is therefore not small everywhere; the per-cell lines above do not test it, and whether it
      matters for training is what A2 measures.
\end{itemize}
The probes draw from a generator of their own. On the pod (version 3) the MNIST and CIFAR probe runs reproduced their main-table
records exactly; on the desk (Quadro P2200) \RYProbeRunsEqualEThree{} of \RYProbeRunsN{} do, because rounding differs between GPU
generations, so the probed states differ slightly from version 3's. LM training is not bitwise reproducible even on one card
type: configurations repeated exactly in the records differ by up to \RXReproLmMaxPct\,\% in bits per byte (CIFAR
\RXReproCifarMaxPct\,\%).

\paragraph{Training level (A2).} The same selections, learning rates and seeds as the main table were trained with the
per-sample stream (MNIST: every analog layer, three devices $\times$ SGD, c-TTv2, AGAD; CIFAR: the two fully connected layers,
whose rows are one per image, for Li-ECRAM and protonic-inspired c-TTv2 and MO-ECRAM AGAD; the convolutional layers keep the
surrogate), seeds 0--2, and compared seed by seed with the main table's surrogate runs; both arms are labelled at the same three
seeds (Table~\ref{tab:rev3_fid}). The pre-registered rule calls the change material if any cell's mean gap moves by more than
half the line (1\,pp) or two cells whose gaps differ by more than 1\,pp swap order.
\begin{itemize}
\item By that rule the result is \textbf{material}, through one cell: \RXFidMaterialList, whose gap moves from
      \RXFidMnistEcramMoKimTwoZeroOneNineSgdSur{} to \RXFidMnistEcramMoKimTwoZeroOneNineSgdSeq\,pp
      (difference \RXFidMnistEcramMoKimTwoZeroOneNineSgdD\,pp, 95\,\% interval [\RXFidMnistEcramMoKimTwoZeroOneNineSgdLo,
      \RXFidMnistEcramMoKimTwoZeroOneNineSgdHi]). At three seeds both of its arms are
      \RYFidMnistEcramMoKimTwoZeroOneNineSgdSurLabel{} (surrogate [\RYFidMnistEcramMoKimTwoZeroOneNineSgdSurLo,
      \RYFidMnistEcramMoKimTwoZeroOneNineSgdSurHi], stream [\RYFidMnistEcramMoKimTwoZeroOneNineSgdSeqLo,
      \RYFidMnistEcramMoKimTwoZeroOneNineSgdSeqHi]\,pp). The rerun flagged in version 3 was done (seeds 3 and 4 on the desk,
      experiment A2-R): at the main table's five seeds the stream's gap is \RYAtwoRSeqGap\,pp [\RYAtwoRSeqLo, \RYAtwoRSeqHi],
      \RYAtwoRSeqLabel, against \RYAtwoRSurGap\,pp [\RYAtwoRSurLo, \RYAtwoRSurHi], \RYAtwoRSurLabel, with the surrogate; the
      paired change is \RYAtwoRD\,pp [\RYAtwoRDLo, \RYAtwoRDHi] (\RYAtwoRMaterial). The FAIL label holds under either update,
      but the size of the change is not resolved: seed 0 run again on the desk reached \RYAtwoRSeedZeroDesk\,\% against
      \RYAtwoRSeedZeroPod\,\% on the pod, \RYAtwoRSeedZeroDiff\,pp apart from GPU rounding alone (this cell's surrogate gap has
      a seed standard deviation of \RYAtwoRSurSd\,pp), and with the desk's seed 0 the change is \RYAtwoRAltD\,pp
      (\RYAtwoRAltMaterial; label \RYAtwoRAltLabel).
\item One label changes at the same three seeds: \RYFidTransList. Its mean gap moves by only
      \RXFidCifarEcramLiTangTwoZeroOneEightCttvTwoD\,pp, but the stream's interval
      ([\RYFidCifarEcramLiTangTwoZeroOneEightCttvTwoSeqLo, \RYFidCifarEcramLiTangTwoZeroOneEightCttvTwoSeqHi]\,pp) is wider and
      includes the line. This is not a failure, but the label is not preserved, and the difference interval
      ([\RXFidCifarEcramLiTangTwoZeroOneEightCttvTwoLo, \RXFidCifarEcramLiTangTwoZeroOneEightCttvTwoHi]\,pp) does not bound
      the change within $\pm1$\,pp.
\item \RYFidRevN{} pairs of cells reverse their mean order (\RYFidRevList); none was separated by more than 1\,pp under the
      surrogate, so there is no material rank reversal under the registered rule, but the ranking as a whole is not preserved.
      No Tiki-Taka-family cell's mean moves by more than \RXFidTtMaxAbs\,pp (MNIST at most \RXFidMnistMaxAbs\,pp including the
      SGD cell; CIFAR at most \RXFidCifarMaxAbs\,pp, with intervals of several pp at three seeds).
\end{itemize}
Within these bounds (MNIST on every layer, CIFAR on its fully connected layers, the LM at update level only, three seeds), the
registered result is one material mean change, in a failing SGD cell whose FAIL label holds at five seeds under either update; no
material rank reversal; no Tiki-Taka-family mean shift above \RXFidTtMaxAbs\,pp; and one label that loses PASS. This is not a
demonstration that the surrogate and the stream train equivalently, and the per-sample stream is itself an approximation of the
literal one. The surrogate is not validated where clipping removes nearly all of the update (the CIFAR output layer above), for
the convolutional layers, or for the LM's training trajectory, and the main results remain comparisons within this
aggregate-update simulator.

\input{tables/rev3_probe.tex}
\input{tables/rev3_dep.tex}
\input{tables/rev3_fid.tex}
"""
sub("sec_abstract.tex", "Against explicit pulse streams the aggregate\n"
    "update holds on \\RXProbeSurPassN{} of \\RXProbeN{} probes and preserves the ranking of the tested cells (one failing SGD cell moves by more than the pre-set 1\\,pp), but fails where clipping\n"
    "removes nearly all of an update.",
    "Against explicit pulse streams the aggregate\n"
    "update meets preset lines on \\RYProbeSurMeetsN{} of \\RYProbeN{} probes, not where clipping removes nearly all of an\n"
    "update, and ignores shared-line dependence; in training one label and two close rankings change.")
sub("sec_discussion.tex", "Against explicit pulse streams\n"
    "      (Section~\\ref{sec:fidelity}) the surrogate holds on \\RXProbeSurPassN{} of \\RXProbeN{} update probes and in short training\n"
    "      comparisons on MNIST and CIFAR's fully connected layers, but fails on the most clipped layer, and one failing SGD cell moves\n"
    "      by more than 1\\,pp; the convolutional layers and the LM's training are not compared.",
    "Against explicit pulse streams\n"
    "      (Section~\\ref{sec:fidelity}) the surrogate meets the registered lines on \\RYProbeSurMeetsN{} of \\RYProbeN{} update probes\n"
    "      (point estimates), fails on the most clipped layer and does not reproduce the dependence of cells that share a line; in\n"
    "      short training comparisons on MNIST and CIFAR's fully connected layers one label loses PASS, two closely spaced cells swap\n"
    "      order and one failing SGD cell moves by more than 1\\,pp. The convolutional layers and the LM's training are not compared,\n"
    "      and the comparison stream is itself a per-sample approximation of the literal one.")
sub("preamble.tex", "\\input{numbers_rev2}\n", "\\input{numbers_rev2}\n\\input{numbers_rev3}\n")
sub("app_revision.tex", "\\input{tables/rev_d1.tex}",
    "\\input{tables/rev_d1.tex}\n\n"
    "\\paragraph{Version 3's update probes (superseded).} Table~\\ref{tab:v3s_rev2_probe} is version 3's analysis of the update\n"
    "probes (pod sitting r6). Its sampling floor for the per-sample stream added the two methods' variances as if their draws were\n"
    "independent, although the per-sample stream replays the literal stream's line firings, so the floor was too large and every\n"
    "excess of the per-sample stream came out as zero. Version 4 replaces it by the paired analysis of Section~\\ref{sec:fidelity}\n"
    "(Table~\\ref{tab:rev3_probe}). The surrogate's verdicts did not depend on this floor.\n\n"
    "\\input{tables/v3s_rev2_probe.tex}")


def main():
    v3 = T / "v3"
    if not v3.exists():
        v3.mkdir()
        for f in sorted(T.glob("*.tex")):
            shutil.copy2(f, v3 / f.name)
    n = 0
    p = T / "sec_fidelity.tex"
    s = p.read_bytes().decode("utf-8")
    assert s == (v3 / "sec_fidelity.tex").read_bytes().decode("utf-8") and s.count(FID_HEAD) == 1
    p.write_bytes((s[:s.index(FID_HEAD)] + FID_TAIL).encode("utf-8"))
    n += 1
    for f, pairs in E.items():
        p = T / f
        s = p.read_bytes().decode("utf-8")
        for a, b in pairs:
            assert s.count(a) == 1, (f, a[:70], s.count(a))
            s = s.replace(a, b)
            n += 1
        p.write_bytes(s.encode("utf-8"))
    print("edits", n, "files", len(E))


if __name__ == "__main__":
    main()
