"""ME-REVISE-2: the text of experiments A2 and B (after sitting r6 + r7b), anchored edits. Run once."""
import pathlib

T = pathlib.Path(__file__).resolve().parent.parent / "tex"
E = {}


def sub(f, a, b):
    E.setdefault(f, []).append((a, b))


sub("sec_fidelity.tex", "FIDELITY-A2-PLACEHOLDER", r"""\paragraph{Training level (A2).} The same selections, learning rates and seeds as the main table were trained with the
per-sample stream (MNIST: every analog layer, three devices $\times$ SGD, c-TTv2, AGAD; CIFAR: the two fully connected layers,
whose rows are one per image, for Li-ECRAM and protonic-inspired c-TTv2 and MO-ECRAM AGAD; the convolutional layers keep the
surrogate), seeds 0--2, and compared seed by seed with the main table's surrogate runs (Table~\ref{tab:rev2_fid}). The
pre-registered rule calls the change material if any cell's mean gap moves by more than half the line (1\,pp) or two cells
whose gaps differ by more than 1\,pp swap order.
\begin{itemize}
\item By that rule the result is \textbf{material}, through one cell: \RXFidMaterialList, whose gap moves from
      \RXFidMnistEcramMoKimTwoZeroOneNineSgdSur{} to \RXFidMnistEcramMoKimTwoZeroOneNineSgdSeq\,pp
      (difference \RXFidMnistEcramMoKimTwoZeroOneNineSgdD\,pp, 95\,\% interval [\RXFidMnistEcramMoKimTwoZeroOneNineSgdLo,
      \RXFidMnistEcramMoKimTwoZeroOneNineSgdHi]). It is a failing cell, far over the line under either update, and the interval
      includes zero; we report it as not validated against the explicit stream.
\item No pair of cells swaps order (\RXFidSwapsN{} swaps), and no Tiki-Taka-family cell moves by more than
      \RXFidTtMaxAbs\,pp (MNIST at most \RXFidMnistMaxAbs\,pp including the SGD cell; CIFAR at most \RXFidCifarMaxAbs\,pp, with
      intervals of several pp at three seeds).
\end{itemize}
Within these bounds (MNIST on every layer, CIFAR on its fully connected layers, the LM at update level only, three seeds), the
aggregate surrogate preserves the ranking and the pass/fail reading of the tested Tiki-Taka-family cells. It is not validated
where clipping removes nearly all of the update (the CIFAR output layer above), for the convolutional layers, or for the LM's
training trajectory, and the main results remain comparisons within this aggregate-update simulator.

\input{tables/rev2_probe.tex}
\input{tables/rev2_fid.tex}""")
sub("sec_fidelity.tex", r"""\item It fails on the two probes of the most clipped layer: \RXProbeSurFailList. There almost nothing of the requested update
      survives the clipping, and the surrogate's few large counts no longer match the stream's at most one pulse per slot.""",
    r"""\item It fails on the two probes of the most clipped layer: \RXProbeSurFailList. There almost nothing of the requested update
      survives the clipping, and the surrogate's Poisson counts, which can exceed the slot budget that caps the stream, no longer
      match it (review 2's limiting case: Poisson(31) exceeds 31 with probability 0.4524).""")
sub("sec_spec.tex", r"""With the symmetry
point held at mid-range only the base value is established (\RVSpecCttvTwoCifarAsymFixedspThr), but no point fails: up to
$a=0.4$ the mean gap stays at \RVSpecCttvTwoCifarAsymFixedspAtZeroPFourGap\,pp and the intervals merely include the line.""",
    r"""With the symmetry point
held at mid-range, version 2 borrowed the ordinary base (whose range is $[-1.125, +0.875]$) as this sweep's anchor and omitted
its zero point (deviation R5); both are now run with each device's range re-centred (range $[-1, 1]$, pre-registered after the
second review). The recentred base passes (\RVSpecCttvTwoCifarAsymFixedspAtZeroPZeroFiveGap\,pp) and so does $a=0$
(\RVSpecCttvTwoCifarAsymFixedspAtZeroPZeroGap\,pp), so the held-symmetry threshold \RVSpecCttvTwoCifarAsymFixedspThr{} is now
established by its own runs; it differs from the unrecentred base by \RXFixCttvTwoCifarRmu\,pp (95\,\% interval
[\RXFixCttvTwoCifarRmuLo, \RXFixCttvTwoCifarRmuHi]). No point fails: up to $a=0.4$ the mean gap stays at
\RVSpecCttvTwoCifarAsymFixedspAtZeroPFourGap\,pp and the intervals merely include the line.""")
sub("sec_discussion.tex", r"""We did not compare against a sequential pulse-by-pulse
      simulation on training cells.""",
    r"""Against explicit pulse streams
      (Section~\ref{sec:fidelity}) the surrogate holds on \RXProbeSurPassN{} of \RXProbeN{} update probes and in short training
      comparisons on MNIST and CIFAR's fully connected layers, but fails on the most clipped layer, and one failing SGD cell moves
      by more than 1\,pp; the convolutional layers and the LM's training are not compared.""")
sub("sec_abstract.tex", r"""This
version repairs the simulator after an independent review""",
    r"""Against
explicit pulse streams the aggregate update holds on \RXProbeSurPassN{} of \RXProbeN{} probes and preserves the ranking of the tested
cells, but fails where clipping removes nearly all of an update. This
version repairs the simulator after two independent reviews""")
for f, L in E.items():
    p = T / f
    s = p.read_bytes().decode("utf-8")
    for a, b in L:
        assert s.count(a) == 1, (f, a[:70], s.count(a))
        s = s.replace(a, b)
    p.write_bytes(s.encode("utf-8"))
print("ok", sum(len(v) for v in E.values()))
