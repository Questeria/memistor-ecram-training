# Response to the ninth independent review (ChatGPT in Codex, 2026-10-29), version 12 of the paper

The review (`reviews/REVIEW-9-chatgpt-20261029-full.md`) audited the public archive, release v1.1 (tag v1.1, commit aaee0bed, which
holds version 11), against version 11's PDF (`build/v11/main-arxiv.pdf`, SHA-256 67530090...a2021d), before the arXiv submission.
It worked from a fresh clone and read nothing else. Its checks:
- it ran README.md as written: the install, then 27 of 27 reproduction steps;
- it compared all 68 regenerated outputs with the clone: 55 byte-identical, 7 differing only in the PDF creation date, 6 with
  identical pixels;
- all 2,231 number macros and all 26 tables were equal;
- it recomputed the main, width, sensitivity, probe and energy statistics independently;
- it ran 41 simulator checks and caught 45 planted faults;
- it compiled the arXiv source with TeX Live 2026 and pdfLaTeX: 42 pages, with no unresolved reference or citation;
- it checked that Zenodo's v1.1 ZIP holds the 3,438 tracked files byte for byte.

It reported one major finding (one width-study verdict), eight minor and two cosmetic. Only after its own work did it read review 8
and its response; it found all nine of review 8's findings fixed or disclosed.

Every finding was verified against the files before anything changed, and all eleven are confirmed. Findings 2 and 4 rest on the
review's own counts, so they were recomputed from the records: 6 probes against 5, a maximum of 0.345 against 0.173, and 10 of 10
task/seed groups. No experiment was run. Cost: $0 (desk and WSL; no GPU, no pod).

| # | Finding (severity) | Verification | Change (version 12, archive v1.2) |
|---|---|---|---|
| 1 | The width study's Welch interval floors its degrees of freedom, which changes one verdict (major) | Confirmed. `revision/analyze_rev.py` `tq()` reads the t table at `int(math.floor(df))`. PLAN-REVISION.md (Width) registers a "Welch interval" without rounding, and no deviation or text stated it, so the rounding was an implementation shortcut, not part of the registered method. CIFAR, protonic-inspired c-TTv2: D = 1.762 pp, df = 4.675. With the df-4 value 2.132 the interval is [-0.02, 3.55], INCONCLUSIVE; at the actual df it is [0.05, 3.47], GROWS. | Corrected to the registered method. `t_quantile` (the regularized incomplete beta function, inverted by bisection) gives the quantile at the actual df. Deviation R9 in `DEVIATIONS-PAPER.md` records the departure (versions 2 to 11) and the correction. Table 11 and `numbers_rev.tex` are regenerated, and all eight Welch intervals equal the review's fractional-df values. That arm becomes GROWS; the other seven keep their verdicts and move by at most 0.18 in their units; the paired contrast is unchanged. Section 4.4, the abstract, the discussion and the roadmap now say that both contrasts detect that growth. Its size against the margin stays unresolved, since both intervals include 2 pp. `revision11/test_welch_df.py` checks the quantile against closed forms, the records against the code, and the review's value to 1e-9; it fails with the df floored. |
| 2 | The dependence statistic is an excess in quadrature, not the difference the text implies (minor) | Confirmed. `revision3/analyze_rev3.py` line 85 computes sqrt(max(0, mean_sq_slot - mean_sq_null)). Recomputed from `records/revision3/RESULTS-REV3.json`: the maximum is 0.345 in quadrature, where the plain difference is 0.173, and 6 probes exceed 0.05 in quadrature against 5 as a plain difference. | Section 4.3 and Table 8's caption (`revision4/analyze_rev4.py`) define the statistic: "in quadrature, sqrt(max(0, RMS_slot^2 - RMS_null^2))". No value changed. |
| 3 | Table 16 calls superseded version-1 values "this paper" (minor) | Confirmed. `analyze.py` `laneme()` takes those columns from version 1's results, which come from the original simulator. | The caption says the values are version 1's ("superseded: the original simulator before its repair; the current values are in Tables 4 and 5"), and the columns read "v1". No value changed. |
| 4 | Section 4.4 says the initialisation is shared across widths (minor) | Confirmed from the e4 run records. In 10 of 10 task/seed groups the initialisation hash differs between widths, while the example-order hash is the same at every width; within a width every arm of a seed shares one initialisation. | Section 4.4 says a seed keeps its example order across widths, and within a width every arm also shares the initialisation (the layers differ in shape between widths). `width_paired`'s docstring says the same. The paired analysis is unchanged: it pairs by seed and example order. |
| 5 | Installing `.venv` at the root, as the README says, makes `--sums` fail (minor) | Confirmed. Both walks in `reproduce_all.py` (lines 94 and 152) skip `.git`, `data`, `_repro` and `__pycache__` only. | Both walks also skip `.venv`, and the README's install says so. |
| 6 | The Figure 3 check's self-test needs a private commit (minor) | Confirmed. `V10_COMMIT` 604285ff4 exists only in the author's repository. | Version 10's `make_figures.py` (that commit's file, byte for byte) is bundled as `revision10/fixtures/make_figures_v10.py`, and the self-test reads it. `reproduce_all.py` now runs the check with `--selftest`. On the desk: 60 cells drawn, 0 misdrawn, 0 legend overlaps; the bundled version-10 code fails it, with 2 misdrawn LM means and 11 overlaps. |
| 7 | Internal paths, project names and host names remain in the release (minor) | Confirmed: the strings the review lists are there. None is a credential, and the review's scan found no credential pattern. | Kept as provenance. They are already public in v1.0 and v1.1, both permanent archives, and several sit inside hashed records (training-record host fields, DEPOSIT-PATCHES' old values). `REDACTIONS.md` now says that its zero-hit statement covers only the three kinds of private name it names, and lists the internal context kept. |
| 8 | The stated Python minimum (3.10+) conflicts with the pinned NumPy 2.5.2, which needs 3.12 (minor) | Confirmed: `reproduce_all.py` lines 18 to 20. | `reproduce_all.py` and the README state 3.12 or newer for the pinned environment; the clean rooms used 3.13.15. The training environment (Python 3.10.12 on the pods) stays in `ENVIRONMENT.md`. |
| 9 | The simulators' docstrings still call the Poisson draw conservative (minor) | Confirmed: `sim/memsim_rev.py` lines 38-40 and `sim/memsim.py` lines 23-25. Lane ME's `sim/memsim.py` at the archive root has the same text. | All three match Section 3.2: the mean is exact only while no slot probability clips, per-cell draws ignore shared-line correlations, and the larger variance is not claimed to be conservative. No code changed. |
| 10 | `CITATION.cff` gives the build date as the release date (cosmetic) | Confirmed. The builder wrote the day it ran (2026-10-28); GitHub and Zenodo date v1.1 on 2026-10-29. | `date-released`, which is optional in CFF 1.2.0, is dropped. GitHub and Zenodo record the release date. |
| 11 | Jacobs‐Gedrim prints without its hyphen in the Tectonic PDF (cosmetic) | Confirmed. `tex/refs.bib` lines 260-261 carry U+2010, in that author name and in the title "Li‐Ion", and Tectonic drops it. | Both are now ASCII hyphens, and version 12 prints "Jacobs-Gedrim". The text diff shows it as one of the expected edits. |

The two defects the release already disclosed stay as they are, unchanged and kept as run: K1, the LM sampler's last window, and K2,
the classification `samples` field, which nothing reads any more.

On the review's limits:

- **The arXiv compile.** The review compiled version 11's source with pdfLaTeX. Version 12 is built with Tectonic, as before; its source
  adds only text, a standard amsmath formula in Table 8's caption and an ASCII hyphen, which removes the one difference between engines
  the review saw. arXiv compiles the source again and shows a preview before anything is posted.
- **Length.** Version 12 has 43 pages, one more than version 11, because Section 4.4 and the history are longer. The arXiv comments field
  changes to "43 pages, 3 figures".
- **Training trajectories, AIHWKIT, the cited studies and private history** are outside a CPU reproduction, as the review says. Nothing
  here changes that.

## Checks (records in `records/revision11/`)

- **Build:** version 12 built with `pod/build_payload_rev8.py` and its `run.sh` (tectonic 0.15.0, in WSL Ubuntu). It has 43 pages; the
  arXiv archive compiles alone, and the HTML is complete and clean (`BUILD-STEPS-v12.txt`). `revision11/archive_v11.py` archived
  version 11 first (`tex/v11` from the version-11 commit, `build/v11`).
- **Text against version 11** (`revision11/pdf_text_diff_v12.py`, giving `PDF-TEXT-DIFF-main.json` and `PDF-TEXT-DIFF-main-arxiv.json`):
  - Why a new method: the extra page moves a float and two paragraphs across page breaks, and that splits a hunk-by-hunk comparison into
    69 pieces.
  - What it checks instead: word counts. Every word's count must change exactly as the 46 expected edits change it, after one
    normalisation applied to both versions (line-break hyphens, and a URL or range broken at a line end).
  - Result: every expected edit is seen, 0 word changes are unexplained, and one word split around a float is rejoined
    ("symme-" + "try"). The new version has exactly one page more.
  - The same check on version 10 against version 12 fails, as it must (`PDF-TEXT-DIFF-negative-v10-v12.json`: 217 unexplained).
- **Name** (`revision9/name_check_v10.py`, giving `NAME-CHECK-v12.json`): the author's account name appears only inside the GitHub mirror's
  address.
- **Numbers** (`revision8/check_numbers_fresh.py --selftest`, giving `NUMBERS-FRESH.json`): every `tex/numbers*.tex` equals its regeneration.
- **Figure 3** (`FIG-MAIN-CHECK.json`, with the bundled self-test), **the reset** (`TESTS-IDEAL-RESET-COLS.json`) and **the Welch
  quantile** (`TESTS-WELCH-DF.json`) all pass.
- **Every earlier check:** `revision11/check_build_v12.py` runs `revision6/check_build_v7.py` and reads the records above
  (`ARTIFACT-CHECK-v12.json`, ALL_OK).

## Archive v1.2

Release v1.2 holds version 12 and every change above. It is built by `make_deposit.py` and reproduced in a clean room
(`deposit_cleanroom.py`), whose results are in `records/deposit/`. The README's "Changes since v1.1" section and `RELEASE-NOTES.md`
list the changes.
