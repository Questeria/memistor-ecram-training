r"""Version 15 of the memistor paper: the answer to review 12 (ChatGPT's audit of release v1.4 and version 14, 2026-10-31).  No
experiment; no result changes.  The text edits (the regenerated tables and figures come from their generators, not from here):

  B. Figure 1's caption states the selected settings: TTv2 and c-TTv2 reset A with pulses, AGAD does not reset it; in the common
     notation c (.) x, c = 1 for TTv2, and c-TTv2 and AGAD use chopper signs (the figure itself: revision14/make_fig_arch.py);
  C. Section 2.2: Agarwal et al. (2016) and the extension to convolutional networks (2017) now come right after Gokmen and Vlasov
     and before Byun et al., with "for conventional (SGD) training", so no later algorithm comparison is attributed to them;
  D1. Section 5, item 3: the pulse reset's extra reads are priced like the transfer's reads (one ADC conversion and one buffer
     allowance), although they do not update H: stated as a conservative approximation, with its bound (at most 0.15 %);
  D2. Section 3 (Statistics): the t quantile is computed exactly (revision/analyze_rev.py now takes t_quantile for the ordinary
     and paired intervals, as the Welch interval has since version 12);
  then the date (November 2026), the availability section (archive v1.5, twelve reviews, the twelfth response, Figure 1's scripts
  in revision14/) and the history (version 15).  The concept DOI is unchanged; the contribution statement is not touched.

    python -I -B revision14/edit_15.py

Each anchor is matched with any run of whitespace between its words and must occur exactly once (edit_10.py's rule); nothing is
written unless every anchor of every file matched.  The Agarwal sentence moves as one Python string (removed and inserted), so its
words move unchanged; only "for conventional (SGD) training" is added to it.
"""
import re
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "tex"

GOKMEN_END = r"tolerance to large cycle-to-cycle and device-to-device variation."
AGARWAL = r"Agarwal et al.~\cite{agarwal2016} reached similar conclusions"
CNN = r"the requirements were extended to convolutional networks~\cite{gokmen2017cnn}"
BYUN_END = r"in their simulations TTv2 permits more lenient specifications than TTv1, and plain SGD needs the most stringent."

EDITS = {
    "preamble.tex": [
        ("date", r"\date{October 2026}", r"\date{November 2026}"),
    ],
    "sec_background.tex": [
        ("agarwal before byun", GOKMEN_END + r" Byun et al.~\cite{byun2024}",
         GOKMEN_END + " " + AGARWAL + r" for conventional (SGD) training, and " + CNN + r"." "\n"
         r"Byun et al.~\cite{byun2024}"),
        ("agarwal removed after byun", BYUN_END + " " + AGARWAL + r"; " + CNN + r", and reviews cover the device",
         BYUN_END + "\n" + r"Reviews cover the device"),
    ],
    "sec_methods.tex": [
        ("caption settings",
         r"here, with forward weight $C$ (TTv1, used only in Section~\ref{sec:validation}, has no buffer and no reset). Pulse probabilities",
         r"here, with forward weight $C$ (TTv1, used only in Section~\ref{sec:validation}, has no buffer and no reset). In the selected" "\n"
         r"configurations (Table~\ref{tab:rev_selection}) TTv2 and c-TTv2 reset $A$ with pulses and AGAD does not reset it; in the" "\n"
         r"common notation $c\odot x$, $c=\mathbf{1}$ for TTv2, and c-TTv2 and AGAD use chopper signs. Pulse probabilities"),
        ("exact t", r"we report the mean and a 95\% Student-$t$ interval.",
         r"we report the mean and a 95\% Student-$t$ interval (the $t$ quantile computed exactly)."),
    ],
    "sec_energy.tex": [
        ("reset reads",
         r"as one ADC conversion and one read-add-write of the digital buffer $H$ per read weight).",
         r"as one ADC conversion and one read-add-write of the digital buffer $H$ per read weight). The pulse reset's extra" "\n"
         r"      column reads are priced the same way although they do not update $H$, a conservative approximation: the buffer" "\n"
         r"      allowance stands for the arithmetic that turns each re-read into a correction pulse count, and without it the analog" "\n"
         r"      energy would be at most 0.15\,\% lower."),
    ],
    "body.tex": [
        ("archive version",
         r"(this DOI cites all versions; version~1.4 of the archive holds version~14 of this paper, version~1.3 holds version~13,",
         r"(this DOI cites all versions; version~1.5 of the archive holds version~15 of this paper, version~1.4 holds version~14," "\n"
         r"version~1.3 holds version~13,"),
        ("release", r"(release v1.4)", r"(release v1.5)"),
        ("reviews", r"the eleven independent reviews", r"the twelve independent reviews"),
        ("responses", r"\texttt{RESPONSE-TO-REVIEW-11.md});", r"\texttt{RESPONSE-TO-REVIEW-11.md}, \texttt{RESPONSE-TO-REVIEW-12.md});"),
        ("fig scripts", r"Figure~\ref{fig:arch} is drawn by \texttt{revision13/make\_fig\_arch.py} and",
         r"Figure~\ref{fig:arch} is drawn by \texttt{revision14/make\_fig\_arch.py} and"),
        ("fig check", r"checked against the simulator by \texttt{revision13/check\_fig\_arch.py};",
         r"checked against the selected settings, the records and the simulator by \texttt{revision14/check\_fig\_arch.py};"),
    ],
    "app_revision.tex": [
        ("v14 not current", r"Version 14 (October 31, 2026; this paper) answers", r"Version 14 (October 31, 2026) answers"),
        ("v15",
         r"Sections~\ref{sec:methods}, \ref{sec:fidelity}, \ref{sec:scale} and~\ref{sec:spec} to this appendix.",
         r"Sections~\ref{sec:methods}, \ref{sec:fidelity}, \ref{sec:scale} and~\ref{sec:spec} to this appendix." "\n"
         r"Version 15 (November 1, 2026; this paper) answers a twelfth review, of version 14 and version 1.4 of the archive" "\n"
         r"(\texttt{RESPONSE-TO-REVIEW-12.md}; no experiment was run and no result changed), which recomputed the statistics and the" "\n"
         r"energy accounting from the records and ran the archive's fast reproduction. Figure~\ref{fig:arch} and its caption now" "\n"
         r"show the selected settings (TTv2 and c-TTv2 reset $A$ with pulses, AGAD does not; TTv2 has no chopper), and its check takes" "\n"
         r"them from the main experiment's settings and records; Section~\ref{sec:background} cites Agarwal et al.\ before the" "\n"
         r"Tiki-Taka studies; the ordinary and paired intervals take the exact $t$ quantile, as the Welch interval already did, which" "\n"
         r"moves 16 endpoints in Tables~\ref{tab:rev_vs_fp} and~\ref{tab:rev_vs_adam} by 0.01 and changes no classification;" "\n"
         r"Section~\ref{sec:energy} states that the reset's extra reads carry a buffer allowance; and outside its reference" "\n"
         r"environment the archive's reproduction compares its one CPU re-simulation of float32 pulse sequences (the AIHWKIT" "\n"
         r"comparison) under a stated numeric tolerance."),
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
