"""ME-REVISE-4: the text of version 5 (PLAN-REVISION-4.md), by named anchors on the v4 sources (kept in tex/v4/). Wording that
depends on experiment A2-M's outcome is chosen here from records/revision4/RESULTS-REV4.json (labels, prediction); every number
is a macro of tex/numbers_rev4.tex (revision4/analyze_rev4.py).

    python -B revision4/edit_tex_4.py      (run once, after analyze_rev4.py; refuses if an anchor is missing)
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parent.parent
TEX = P / "tex"
R = json.loads((P / "records" / "revision4" / "RESULTS-REV4.json").read_bytes())
c = R["p2200"]
both_fail = c["seq_label"] == "FAIL" and c["sur_label"] == "FAIL"
label_sent = ("The FAIL label holds under either update." if both_fail else
              "The labels are \\RZAtwoMSurLabel{} with the surrogate and \\RZAtwoMSeqLabel{} with the stream.")
mech = ("The pod's runs of seeds 0--2 are other random realisations of the same seeds, not a rounding variant of them: the "
        "simulator's generators run on the GPU, and the CUDA random kernels assign draws to threads by the GPU's multiprocessor "
        "count, so another GPU model draws another initialisation and example order (as predicted, the hashes differ from "
        "both the pod's and the earlier desk runs')." if R["prediction_holds"] else
        "The pod's runs of seeds 0--2 are other random realisations of the same seeds (their initialisation and example order "
        "differ), not a rounding variant of them.")

A2M = (
    "The rerun flagged in version 3 was done as matched triples on one GPU (experiment A2-M, Table~\\ref{tab:rev4_a2m};\n"
    "      \\texttt{PLAN-REVISION-4.md}): on the desk's \\RZAtwoMGpu, each of seeds 0--4 trained the FP-SGD control, the\n"
    "      surrogate and the stream from one initialisation and one example order (equal hashes, checked; the analysis refuses\n"
    "      a seed without them). At these \\RZAtwoMN{} matched seeds the stream's gap is \\RZAtwoMSeqGap\\,pp [\\RZAtwoMSeqLo,\n"
    "      \\RZAtwoMSeqHi], \\RZAtwoMSeqLabel, against \\RZAtwoMSurGap\\,pp [\\RZAtwoMSurLo, \\RZAtwoMSurHi], \\RZAtwoMSurLabel,\n"
    "      with the surrogate; the paired change is \\RZAtwoMD\\,pp [\\RZAtwoMDLo, \\RZAtwoMDHi] (\\RZAtwoMMaterial"
    + ("; its interval lies within $\\pm1$\\,pp). " if -1 < c["dgap"]["lo"] and c["dgap"]["hi"] < 1 else "). ")
    + label_sent + "\n      " + mech + "\n"
    "      Per seed the two realisations' gaps differ by up to \\RZRealGapDiffMax\\,pp, and at the pod's three matched seeds the\n"
    "      change was \\RZPodNThreeD\\,pp [\\RZPodNThreeDLo, \\RZPodNThreeDHi]: this cell's gap depends strongly on the\n"
    "      realisation, and the update's effect on it is measured only by the paired comparisons within each matched set.\n"
    "      Version 4's five-seed figures for this cell mixed matched and unmatched pairs and are withdrawn (Appendix~\\ref{app:revision}).")
SUMMARY = ("in a failing SGD cell whose FAIL label holds at five matched seeds on one GPU under either update;" if both_fail else
           "in a failing SGD cell (at five matched seeds on one GPU: \\RZAtwoMSurLabel{} with the surrogate, \\RZAtwoMSeqLabel{} "
           "with the stream);")

EDITS = {
    "preamble.tex": [
        ("fitbox", "\\newcommand{\\fitbox}[1]{\\resizebox{\\ifdim\\width>\\textwidth\\textwidth\\else\\width\\fi}{!}{#1}}",
         "% every \\fitbox logs its table, natural width, text width and font size (revision4/check_build_v5.py reads them)\n"
         "\\newsavebox{\\fitboxbox}\n\\makeatletter\n"
         "\\newcommand{\\fitbox}[1]{\\sbox{\\fitboxbox}{#1}\\typeout{FITBOX table=\\thetable\\space wd=\\the\\wd\\fitboxbox\\space "
         "tw=\\the\\textwidth\\space size=\\f@size}%\n"
         "  \\resizebox{\\ifdim\\wd\\fitboxbox>\\textwidth\\textwidth\\else\\wd\\fitboxbox\\fi}{!}{\\usebox{\\fitboxbox}}}\n"
         "\\makeatother"),
        ("numbers", "\\input{numbers_rev3}", "\\input{numbers_rev3}\n\\input{numbers_rev4}"),
    ],
    "sec_abstract.tex": [
        ("point", "update meets preset lines on \\RYProbeSurMeetsN{} of \\RYProbeN{} probes,",
         "update meets preset point-estimate lines on \\RYProbeSurMeetsN{} of \\RYProbeN{} probes (bootstrap:\n"
         "\\RYProbeSurAtNinetyFiveN),"),
        ("count", "after two independent reviews and reports how much each repair moved",
         "after independent reviews and reports how far each repair moved"),
    ],
    "sec_fidelity.tex": [
        ("tables", "draws (Table~\\ref{tab:rev3_probe}; \\texttt{PLAN-REVISION-3.md}).",
         "draws (Tables~\\ref{tab:rev4_probe_sur} and~\\ref{tab:rev3_probe}; \\texttt{PLAN-REVISION-3.md}); the draws are part of\n"
         "the deposit, and Tables~\\ref{tab:rev4_probe_sur}--\\ref{tab:rev3_dep} can be rebuilt from them alone\n"
         "(Section~\\ref{sec:availability})."),
        ("probe_runs", "on the desk (Quadro P2200) \\RYProbeRunsEqualEThree{} of \\RYProbeRunsN{} do, because rounding differs "
         "between GPU\ngenerations, so the probed states differ slightly from version 3's.",
         "on the desk (Quadro P2200) \\RYProbeRunsEqualEThree{} of \\RYProbeRunsN{} do, and none shares its\n"
         "initialisation with its version-3 run (the MNIST run not its example order either): the simulator's generators run on\n"
         "the GPU, and the CUDA random kernels assign draws to threads by the GPU's multiprocessor count. The desk's probe runs\n"
         "are therefore fresh training realisations, and the probed states are not version 3's; the comparison within each\n"
         "probe is unaffected, since all three updates start from the same saved state."),
        ("a2r", None, A2M),
        ("summary", "in a failing SGD cell whose FAIL label holds at five seeds under either update;", SUMMARY),
        ("inputs", "\\input{tables/rev3_probe.tex}\n\\input{tables/rev3_dep.tex}\n",
         "\\input{tables/rev4_probe_sur.tex}\n\\input{tables/rev4_probe_seq.tex}\n\\input{tables/rev4_dep.tex}\n"
         "\\input{tables/rev4_a2m.tex}\n"),
    ],
    "app_revision.tex": [
        ("v4", "Version 4 (October 27, 2026; this paper) answers a third review",
         "Version 4 (October 27, 2026) answers a third review"),
        ("v5", "includes the width margin is no longer read as growth below it.",
         "includes the width margin is no longer read as growth below it. Version 5 (October 27, 2026; this paper) answers a\n"
         "fourth review (three findings; \\texttt{RESPONSE-TO-REVIEW-4.md}, plan \\texttt{PLAN-REVISION-4.md}, committed before\n"
         "its runs). Version 4's five-seed rerun of the material SGD cell had joined, by seed only, two stream runs whose\n"
         "initialisation and example order differed from their controls' (the random draws depend on the GPU model), and it\n"
         "had put a seed-0 difference down to GPU rounding; its figures (stream gap \\RYAtwoRSeqGap\\,pp, change \\RYAtwoRD\\,pp)\n"
         "are withdrawn as an unmatched, mixed-hardware diagnostic. The cell was rerun as matched triples on one GPU, and the\n"
         "analysis now refuses a seed whose arms do not share both hashes. The saved pulse draws joined the deposit with a\n"
         "command that rebuilds the probe tables from them, the probe table was split in two for legibility, and the abstract\n"
         "states that its probe count is a point-estimate count."),
    ],
    "body.tex": [
        ("plans", "\\texttt{PLAN-REVISION-3.md}), their deviations", "\\texttt{PLAN-REVISION-3.md}, \\texttt{PLAN-REVISION-4.md}), their deviations"),
        ("responses", "the responses to the three\n      independent reviews (\\texttt{RESPONSE-TO-REVIEW.md}, \\texttt{RESPONSE-TO-REVIEW-2.md},\n"
         "      \\texttt{RESPONSE-TO-REVIEW-3.md});",
         "the responses to the four\n      independent reviews (\\texttt{RESPONSE-TO-REVIEW.md}, \\texttt{RESPONSE-TO-REVIEW-2.md},\n"
         "      \\texttt{RESPONSE-TO-REVIEW-3.md}, \\texttt{RESPONSE-TO-REVIEW-4.md});"),
        ("sim", "(\\texttt{sim/*\\_rev2.py}, \\texttt{sim/*\\_rev3.py}), with their checks;",
         "(\\texttt{sim/*\\_rev2.py}, \\texttt{sim/*\\_rev3.py}, \\texttt{sim/sweep\\_rev4.py}), with their checks;"),
        ("scripts", "\\texttt{revision2/analyze\\_rev2.py}, \\texttt{revision3/analyze\\_rev3.py});",
         "\\texttt{revision2/analyze\\_rev2.py}, \\texttt{revision3/analyze\\_rev3.py}, \\texttt{revision4/analyze\\_rev4.py});\n"
         "\\item the saved pulse draws of the update probes: \\RZDrawN{} NumPy archives (\\RZDrawBytes{} bytes, outside the code\n"
         "      repository; each file's SHA-256 is in its probe record and in \\texttt{PUBLISHING.md}), from which\n"
         "      \\texttt{revision4/rebuild\\_draw\\_tables.py} recomputes every statistic of\n"
         "      Tables~\\ref{tab:rev4_probe_sur}--\\ref{tab:rev3_dep} and checks the rebuilt tables against the paper's byte for byte;"),
    ],
}


def main():
    for fn, subs in EDITS.items():
        p = TEX / fn
        t = p.read_bytes().decode("utf-8")
        for name, a, b in subs:
            if name == "a2r":
                i = t.find("The rerun flagged in version 3 was done (seeds 3 and 4 on the desk,")
                j = t.find("(\\RYAtwoRAltMaterial; label \\RYAtwoRAltLabel).")
                assert i > 0 and j > i, (fn, name)
                t = t[:i] + b + t[j + len("(\\RYAtwoRAltMaterial; label \\RYAtwoRAltLabel)."):]
                continue
            assert t.count(a) == 1, (fn, name, t.count(a))
            t = t.replace(a, b)
        p.write_bytes(t.encode("utf-8"))
    print("edited", ", ".join(EDITS), "| both FAIL:", both_fail, "| prediction:", R["prediction_holds"])


if __name__ == "__main__":
    main()
