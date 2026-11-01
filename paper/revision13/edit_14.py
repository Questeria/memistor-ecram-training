r"""Version 14 of the memistor paper: the answer to review 11 (ChatGPT's review of version 13, 2026-10-31).  No experiment and no
result changes.  Text and one new figure (fig_arch, revision13/make_fig_arch.py):

  1. related work: Byun et al. (byun2024, verified by revision13/cite_check_v14.py) in the introduction and the background, with what
     this study adds to it; the protonic variability of Xu et al. (xu2026, already cited) in the roadmap's Stage 1;
  2. energy: the GPU equation with every input range (the low end, 7.05 pJ, is 500 W at 43 %); which digital costs of the TT family
     are inside the ratio and which ("the digital TT state") are not; the ratio is a per-operation, read-dominated figure;
  3. wording: "exploratory device sensitivity analysis" in the subtitle (the only place that promised a specification sheet), the
     abstract, the introduction, Section 4.5 (with the joint-deviation sentence), the limitations and Appendix B;
  4. Figure 1 (fig_arch) in Section 3.3: what is simulated as a device and what is digital;
  5. limitations: the control ladder; roadmap: computational follow-ups (full CIFAR and LM trajectories with correlated streams
     first, the pulse-length / update-management comparison, the control ladder, fair tuning of analog SGD);
  6. correction history moved verbatim from Sections 3, 4.3 and 4.5 into Appendix F (where Appendix F already said the same, the
     main-text copy is removed);
  then the availability section (archive v1.4, eleven reviews, the eleventh response) and the history (version 14).

    python -I -B revision13/edit_14.py

Each anchor is matched with any run of whitespace between its words and must occur exactly once (edit_10.py's rule); nothing is
written unless every anchor of every file matched.  A moved passage is one Python string used both as the removed text and inside
the inserted text, so it moves word for word.
"""
import re
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "tex"

# ---- passages moved verbatim from the main text into Appendix F ----
MOVE_PROBES = (r"The probes draw from a generator of their own. On the pod (version 3) the MNIST and CIFAR probe runs reproduced their"
               r" main-table records exactly; on the desk (Quadro P2200) \RYProbeRunsEqualEThree{} of \RYProbeRunsN{} do, and none"
               r" shares its initialisation with its version-3 run (the MNIST run not its example order either): the simulator's"
               r" generators run on the GPU, and the CUDA random kernels assign draws to threads by the GPU's multiprocessor count."
               r" The desk's probe runs are therefore fresh training realisations, and the probed states are not version 3's; the"
               r" comparison within each probe is unaffected, since all three updates start from the same saved state. LM training"
               r" is not bitwise reproducible even on one card type: configurations repeated exactly in the records differ by up to"
               r" \RXReproLmMaxPct\,\% in bits per byte (CIFAR \RXReproCifarMaxPct\,\%).")
MOVE_POD = (r"The pod's runs of seeds 0--2 are other random realisations of the same seeds, not a rounding variant of them: the"
            r" simulator's generators run on the GPU, and the CUDA random kernels assign draws to threads by the GPU's multiprocessor"
            r" count, so another GPU model draws another initialisation and example order (as predicted, the hashes differ from"
            r" both the pod's and the earlier desk runs'). Per seed the two realisations' gaps differ by up to \RZRealGapDiffMax\,pp,"
            r" and at the pod's three matched seeds the change was \RZPodNThreeD\,pp [\RZPodNThreeDLo, \RZPodNThreeDHi]:")
MOVE_V3STAT = (r"The statistic of version 3, a pooled, signed normalised covariance, stays within \RYDepVthreePooledMax{} in absolute"
               r" value on the same draws, because positive and negative terms cancel and unequal cell variances are pooled.")
MOVE_ANCHOR = (r"version 2 borrowed the ordinary base (whose range is $[-1.125, +0.875]$) as this sweep's anchor and omitted its zero"
               r" point (deviation R5);")

FIG = r"""
\begin{figure}[t]\centering
\includegraphics[width=\linewidth]{figs/fig_arch}
\caption{Device operations and digital ones, for one learned weight matrix: (a) plain SGD; (b) TTv2, c-TTv2 and AGAD as run
here, with forward weight $C$ (TTv1, used only in Section~\ref{sec:validation}, has no buffer and no reset). Pulse probabilities
are computed digitally; the pulses go through the device model; the forward and backward reads are ideal fp32 products of the
device state; biases, layer norms, nonlinearities, attention products and the LM's position table are digital. The energy
projection (Section~\ref{sec:energy}) prices the reads as finite-precision analog reads, the pulses at device energies and, for
the TT family, one ADC conversion and one buffer update per read weight.}\label{fig:arch}
\end{figure}"""

EDITS = {
    "preamble.tex": [
        ("subtitle", r"with a device specification sheet and an experimental roadmap",
         "with an exploratory device\nsensitivity analysis and an experimental roadmap"),
    ],
    "sec_abstract.tex": [
        ("abstract", r"A sensitivity sheet with three seeds establishes", r"An exploratory sensitivity analysis with three seeds establishes"),
    ],
    "sec_intro.tex": [
        ("byun", r"keeping the weight-gradient path digital. Our",
         r"keeping the weight-gradient path digital. Byun et al.~\cite{byun2024} derived device specifications for TTv1 and TTv2 by"
         "\n" r"simulation; relative to that analysis, this study covers the chopped algorithms c-TTv2 and AGAD and a catalog of published"
         "\n" r"electrochemical devices, and reports seed-paired intervals against absolute margins, a language model beside the image"
         "\n" r"tasks and a test of the aggregate update against explicit pulse streams; its own sensitivity analysis is narrower. Our"),
        ("fig ref", r"Reads are ideal (fp32); only the update is analog.", r"Reads are ideal (fp32); only the update is analog (Fig.~\ref{fig:arch})."),
        ("item 4", r"\item \textbf{A sensitivity sheet} against absolute accuracy lines,",
         r"\item \textbf{An exploratory device sensitivity analysis} against absolute accuracy lines, one property at a time with three" "\n"
         r"      seeds (not fabrication tolerances),"),
    ],
    "sec_background.tex": [
        ("byun", r"tolerance to large cycle-to-cycle and device-to-device variation.",
         r"tolerance to large cycle-to-cycle and device-to-device variation. Byun et al.~\cite{byun2024} derived such specifications for" "\n"
         r"TTv1 and TTv2 by multiparameter simulation of asymmetry, retention, pulse count and cycle-to-cycle variation: in their" "\n"
         r"simulations TTv2 permits more lenient specifications than TTv1, and plain SGD needs the most stringent."),
    ],
    "sec_methods.tex": [
        ("aihwkit history",
         r"with multiplicative write noise. The original version of this paper copied the preset fields into the model above with bounds"
         r" $[-1,1]$ and no slope spread; that mapping is kept only for comparison (Appendix~\ref{app:revision}).",
         r"with multiplicative write noise."),
        ("reset history",
         r"\item[The reset of $A$ (revision).] The original simulator moved the read column of $A$ straight to its symmetry point and"
         r" charged $2BL=62$ pulses it never applied (the \emph{ideal reset}). Applied through the device model, those 62 alternating"
         r" pulses leave \RVresetResidPct\,\% of the displacement on the protonic-inspired device. The repaired \emph{pulse reset} uses the",
         r"\item[The reset of $A$.] The repaired \emph{pulse reset} uses the"),
        ("review 8", r"one short (found by review~8), so", r"one short, so"),
        ("ideal reset", r"The ideal reset is reported only as a labelled variant.",
         r"The original simulator's \emph{ideal reset} (Appendix~\ref{app:revision}) is reported only as a labelled variant."),
        ("figure", r"We implemented the algorithms from the papers' text; we did not use the authors' code.",
         r"We implemented the algorithms from the papers' text; we did not use the authors' code. Figure~\ref{fig:arch} shows which"
         "\n" r"parts are simulated as device operations and which are digital." + FIG),
    ],
    "sec_fidelity.tex": [
        ("second review", r"After the second review we compared the two,", r"We compared the two,"),
        ("v3 floor",
         r"Version 3 compared seq with the literal stream as if their draws were independent, although they share the line firings, so"
         r" its sampling floor could hide a real difference (Table~\ref{tab:v3s_rev2_probe}, Appendix~\ref{app:revision}). The probes"
         r" were therefore run again with the draws kept, 16 per probe, and seq is now compared paired by draw, with bootstrap bounds"
         r" over whole draws",
         r"Because seq replays the literal stream's line firings, the two are compared paired by draw, with the draws kept (16 per" "\n"
         r"probe) and bootstrap bounds over whole draws"),
        ("superseded", r"records' metadata (Section~\ref{sec:availability}).",
         r"records' metadata (Section~\ref{sec:availability}); an earlier, unpaired analysis is superseded" "\n"
         r"(Appendix~\ref{app:revision})."),
        ("v3 statistic", MOVE_V3STAT + r" The cross-cell dependence", r"The cross-cell dependence"),
        ("probe realisations", MOVE_PROBES,
         r"The probed states are fresh training realisations on the desk's GPU (Appendix~\ref{app:revision}); the comparison within each" "\n"
         r"probe is unaffected, since all three updates start from the same saved state."),
        ("rerun", r"The rerun flagged in version 3 was done as matched triples on one GPU", r"It was rerun as matched triples on one GPU"),
        ("pod realisations", MOVE_POD + r" this cell's gap depends strongly on the realisation,",
         r"This cell's gap depends strongly on the random realisation (Appendix~\ref{app:revision}),"),
        ("v4 withdrawn",
         r"Version 4's five-seed figures for this cell mixed matched and unmatched pairs and are withdrawn (Appendix~\ref{app:revision}).", ""),
    ],
    "sec_spec.tex": [
        ("heading", r"\subsection{Sensitivity against absolute lines}", r"\subsection{Exploratory device sensitivity against absolute lines}"),
        ("anchor history", r"held at mid-range, " + MOVE_ANCHOR + r" both are now run with each device's range re-centred (range $[-1, 1]$,"
         r" pre-registered after the second review).",
         r"held at mid-range, the base and $a=0$ are run with each device's range re-centred (range $[-1, 1]$; pre-registered after the" "\n"
         r"second review, deviation R5, Appendix~\ref{app:revision})."),
        ("how to read",
         r"\paragraph{How to read the sheet.} These are one-at-a-time ranges around one base device, for one algorithm setting, at FP-SGD's"
         r" learning rate, with three seeds; they are exploratory, not fabrication tolerances. Combined deviations, other algorithm"
         r" settings and independent device populations are not covered.",
         r"\paragraph{How to read this analysis.} It is an exploratory device sensitivity analysis, not a specification sheet:" "\n"
         r"one-at-a-time ranges around one base device, for one algorithm setting, at FP-SGD's learning rate, with three seeds, and" "\n"
         r"not fabrication tolerances. A range established for one property does not bound joint deviations: passing with a step" "\n"
         r"asymmetry alone and with a reference error alone does not show passing with both. Other algorithm settings and independent" "\n"
         r"device populations are not covered either."),
    ],
    "sec_energy.tex": [
        ("tt inside",
         r"and the update (device pulses, pulse lines and pulse generation, and the TT family's column reads and digital buffer).",
         r"and the update (device pulses, pulse lines and pulse generation, and, for the TT family, the transfer's column reads, priced" "\n"
         r"      as one ADC conversion and one read-add-write of the digital buffer $H$ per read weight)."),
        ("tt outside", r"and the digital exclusions do not cancel the analog ones.",
         r"and the digital exclusions do not cancel the analog ones. The rest of the TT family's digital work, called the" "\n"
         r"      digital TT state below (the storage of $H$, AGAD's averages $p$ and $p^{\mathrm{ref}}$ and their arithmetic, the chopper" "\n"
         r"      signs, the threshold tests and the transfer scheduling), is outside the ratio."),
        ("gpu",
         r"\item \textbf{The GPU side} is H100 board power over its dense BF16 peak~\cite{nvidiah100} at the utilisation of a very large"
         r" training run, 38--43\,\%~\cite{dubey2024}: \RVenGpuPj\,pJ per weight per row (\RVenGpuMeasLo--\RVenGpuMeasHi\,pJ over that"
         r" range; \RVenGpuPlannedLo--\RVenGpuPlannedHi\,pJ over the 30--55\,\% range of our original plan).",
         r"\item \textbf{The GPU side} is H100 board power $P$ over its dense BF16 peak $F$~\cite{nvidiah100} at the utilisation $u$ of" "\n"
         r"      a very large training run~\cite{dubey2024}, with 6 FLOP per weight per row (2 each for the forward pass, the input" "\n"
         r"      gradient and the weight gradient): $E_{\mathrm{GPU}}=6P/(Fu)$, with $F=989.5$\,TFLOP/s (half the 1979\,TFLOP/s" "\n"
         r"      sparsity figure), $P$ from 500\,W (our estimate of a sustained draw) to 700\,W (the rated maximum) and $u$ from 38 to" "\n"
         r"      43\,\%. At 700\,W and $u=40.5\,\%$ this is \RVenGpuPj\,pJ per weight per row; over both ranges it is" "\n"
         r"      \RVenGpuMeasLo\,pJ (500\,W, 43\,\%) to \RVenGpuMeasHi\,pJ (700\,W, 38\,\%), and with $u$ over the 30--55\,\% range of our" "\n"
         r"      original plan \RVenGpuPlannedLo--\RVenGpuPlannedHi\,pJ."),
        ("per operation", r"and changes in the simulated pulse counts barely move it.",
         r"and changes in the simulated pulse counts barely move it. It is therefore a conditional, read-dominated figure per" "\n"
         r"operation (one forward read, one backward read and one update of each weight per row), not the energy to train a model to a" "\n"
         r"given quality."),
    ],
    "sec_discussion.tex": [
        ("controls", r"The settings were selected once, on MNIST, with a mid device.",
         r"The settings were selected once, on MNIST, with a mid device." "\n"
         r"\item \textbf{Controls.} The ideal-device reference keeps stochastic pulses, bounds and the selected update management, so it" "\n"
         r"      does not separate the optimiser from the device. A full ladder would run exact digital SGD, a digital TT with an" "\n"
         r"      explicit accumulator decay, finite pulses and levels on ideal devices, the device imperfections and shared-line pulse" "\n"
         r"      streams; we ran the first, the ideal 1000-level device, the catalog and, on MNIST and CIFAR's dense layers, the" "\n"
         r"      per-sample stream."),
        ("statistics", r"three in the sensitivity sheet and the diagnostic", r"three in the sensitivity analysis and the diagnostic"),
    ],
    "sec_roadmap.tex": [
        ("computational",
         r"in Section~\ref{sec:main}." "\n\n" r"\paragraph{Stage 1: single-device characterisation}",
         r"in Section~\ref{sec:main}." "\n\n"
         r"\paragraph{Computational follow-ups (no hardware).} In order of value: (1) train the passing configurations over full CIFAR and" "\n"
         r"LM trajectories with correlated, shared-line pulse streams on every analog layer (so far compared in training only on MNIST" "\n"
         r"and CIFAR's dense layers, Section~\ref{sec:fidelity}); (2) compare pulse lengths and update-management policies where the" "\n"
         r"update clips (mean lost fraction up to \RVLostCifarTtLayerMeanMaxPct\,\%, worst layer record \RVLostMaxPct\,\%); (3) run the" "\n"
         r"control ladder of Section~\ref{sec:limits}; (4) tune each analog arm, plain SGD included, with a search budget comparable to" "\n"
         r"the digital baselines' (the main table reuses the FP-SGD learning rate)." "\n\n"
         r"\paragraph{Stage 1: single-device characterisation}"),
        ("xu", r"Combined deviations are not covered.",
         r"Combined deviations are not covered. Published variability of BEOL-compatible protonic ECRAM~\cite{xu2026}" "\n"
         r"      (3\,\% cycle-to-cycle, 21\,\% device-to-device) is a starting point for such a fit, once its definitions are reconciled" "\n"
         r"      with this model's $c_{2c}$ and $\sigma_{\mathrm{d2d}}$."),
    ],
    "sec_scale.tex": [
        ("flat", r"The original paper's ``FLAT'' label is withdrawn: it did not test equivalence and covered large non-monotonic changes. ",
         ""),
        ("welch df", r"(versions 2 to 11 rounded them down, which the plan does not state; review~9 found it, deviation R9).",
         r"(deviation R9; Appendix~\ref{app:revision})."),
    ],
    "app_original.tex": [
        ("float", r"\begin{figure}[t]\centering \includegraphics[width=\linewidth]{figs/fig_main}",
         "\\begin{figure}[!htb]\\centering\n\\includegraphics[width=\\linewidth]{figs/fig_main}"),
    ],
    "app_selection.tex": [
        ("sheet", r"in the specification sheet.", r"in the sensitivity analysis."),
    ],
    "body.tex": [
        ("archive version",
         r"(this DOI cites all versions; version~1.3 of the archive holds version~13 of this paper, version~1.2 holds version~12,"
         r" version~1.1 holds version~11, and version~1.0 holds version~9)",
         r"(this DOI cites all versions; version~1.4 of the archive holds version~14 of this paper, version~1.3 holds version~13," "\n"
         r"version~1.2 holds version~12, version~1.1 holds version~11, and version~1.0 holds version~9)"),
        ("release", r"(release v1.3)", r"(release v1.4)"),
        ("reviews", r"the ten independent reviews", r"the eleven independent reviews"),
        ("responses", r"\texttt{RESPONSE-TO-REVIEW-10.md});", r"\texttt{RESPONSE-TO-REVIEW-10.md}, \texttt{RESPONSE-TO-REVIEW-11.md});"),
        ("fig script", r"\texttt{revision4/analyze\_rev4.py});",
         r"\texttt{revision4/analyze\_rev4.py}); Figure~\ref{fig:arch} is drawn by \texttt{revision13/make\_fig\_arch.py} and" "\n"
         r"      checked against the simulator by \texttt{revision13/check\_fig\_arch.py};"),
    ],
    "app_revision.tex": [
        ("v13 not current", r"Version 13 (October 31, 2026; this paper) answers", r"Version 13 (October 31, 2026) answers"),
        ("v14", r"name check left a PDF open, so its clean-up failed on Windows.",
         r"name check left a PDF open, so its clean-up failed on Windows." "\n"
         r"Version 14 (October 31, 2026; this paper) answers an eleventh review, of version 13 (\texttt{RESPONSE-TO-REVIEW-11.md}; no" "\n"
         r"experiment was run and no result changed). It cites Byun et al.~\cite{byun2024} and states what this study adds to it;" "\n"
         r"prints the GPU energy equation with both input ranges (the low end, \RVenGpuMeasLo\,pJ, is 500\,W at 43\,\%; version 13" "\n"
         r"named only the utilisation range); says which digital costs of the TT family are inside the energy ratio and that the ratio" "\n"
         r"is a per-operation, read-dominated figure; calls the sensitivity sheet an exploratory device sensitivity analysis, in the" "\n"
         r"subtitle too, and states that one-at-a-time ranges do not bound joint deviations; adds Figure~\ref{fig:arch}; adds a" "\n"
         r"control ladder to the limitations and computational follow-ups to the roadmap; and moves correction history from" "\n"
         r"Sections~\ref{sec:methods}, \ref{sec:fidelity}, \ref{sec:scale} and~\ref{sec:spec} to this appendix."),
        ("moved",
         r"(Table~\ref{tab:rev3_probe}). The surrogate's verdicts did not depend on this floor.",
         r"(Table~\ref{tab:rev3_probe}). The surrogate's verdicts did not depend on this floor." "\n" + MOVE_V3STAT + "\n\n"
         r"\paragraph{Random realisations of the probe and rerun states.} " + MOVE_PROBES + "\n"
         r"The material SGD cell of Section~\ref{sec:fidelity} was rerun as matched triples on the desk. " + MOVE_POD + r" its gap depends strongly on the realisation." "\n\n"
         r"\paragraph{The held-symmetry anchor.} With the symmetry point held at mid-range, " + MOVE_ANCHOR + "\n"
         r"version 3 ran both with each device's range re-centred (Section~\ref{sec:spec})."),
    ],
}


def apply(name, subs):
    p = TEX / name
    t = p.read_bytes().decode("utf-8")
    for tag, a, b in subs:
        pat = r"\s+".join(re.escape(w) for w in a.split())
        n = len(re.findall(pat, t))
        assert n == 1, (name, tag, n)
        t = re.sub(pat, lambda m: b, t)
    return p, t


out = [apply(n, s) for n, s in EDITS.items()]        # every anchor of every file first
for p, t in out:
    p.write_bytes(t.encode("utf-8"))
print("edited", ", ".join(p.name for p, _ in out))
