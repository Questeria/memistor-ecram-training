# Response to the tenth independent review (ChatGPT in Codex, 2026-10-29), version 13 of the paper

The review (`reviews/REVIEW-10-chatgpt-20261029-full.md`) is a revision and regression review of the public archive, release v1.2
(tag v1.2, commit 47da4203, which holds version 12), against version 12's PDF (`build/v12/main-arxiv.pdf`, SHA-256 264f29c3...57fb0b).
It worked from a fresh clone and read the v1.1 -> v1.2 changes before the response to review 9. Its checks:
- it ran README.md as written in a fresh environment (both pip steps, fetch and verify, including a fresh download of all three datasets),
  then `reproduce_all.py --fast` (23 of 23 steps) and the full run (28 of 28 steps);
- it compared all 68 regenerated outputs with the untouched release: 55 byte-identical, 7 differing only in the PDF creation date,
  6 with identical pixels; all 2,232 number macros, all 26 tables and the 3 included figures regenerate;
- it recomputed all eight Welch endpoint contrasts from the raw per-seed records (largest difference 5.33e-15) and checked the
  fractional-df t quantiles against an independent 45-digit reference (largest difference 1.51e-14);
- it recomputed the main, pairing, selection, width, sensitivity, energy, step-accounting and A2-M statistics independently;
- it compiled the arXiv source with TeX Live and pdfLaTeX: 43 pages, with no unresolved reference or citation;
- it checked that Zenodo's v1.2 ZIP holds all 3,491 tracked files byte for byte.

It found the Welch error of version 11 repaired and **no new major or critical issue**. It reported four small findings: two minor and
two cosmetic, none of which changes a result or a conclusion. Every finding was verified against the files before anything changed,
and all four are confirmed. No experiment was run and no number changed. Cost: $0 (desk and WSL; no GPU, no pod).

| # | Finding (severity) | Verification | Change (version 13, archive v1.3) |
|---|---|---|---|
| 1 | The archive README says no other printed number changed in v1.2 (minor) | Confirmed. `make_deposit.py`'s README template, section "Changes since v1.1", said "no other verdict and no other printed number changed". The verdict part is right; the number part is not. All eight Welch intervals changed (by at most 0.18 in their units; for example Li-ECRAM TTv2 on CIFAR [-0.37, 4.19] -> [-0.34, 4.16]). So did the deviation count (R1--R8 -> R1--R9) and the count of inconclusive CIFAR arms (2 -> 1). The paper, Section 4.4 and the history, and `RELEASE-NOTES.md` of v1.2 already described these correctly. | The section now says that all eight Welch intervals were corrected and one verdict changed, which moves the inconclusive count from 2 to 1 and the deviation count to 9. It also says that the paired comparisons and every experimental result outside the width analysis are unchanged, and that review 10 found the old sentence wrong. A new section "Changes since v1.2" describes v1.3. |
| 2 | The archive README counts eight reviews (cosmetic) | Confirmed. The layout table said "the eight independent reviews". v1.2 held nine; with review 10, `paper/reviews/` holds ten (reviews 1 to 10). Section 9 of version 12, `RELEASE-NOTES.md` and `.zenodo.json` said nine, correctly for v1.2. | The layout table says "the ten independent reviews". Section 9 of version 13, `.zenodo.json` and the release notes say ten. |
| 3 | Table 11's caption says versions 1--11 rounded the Welch degrees of freedom (cosmetic) | Confirmed, and the range was checked against the archived versions. Version 1 has no Welch test: `tex/v1/` and the text of `build/v1/main.pdf` never mention one, and its width verdicts came from `sim/stats_paper.py`'s endpoint heuristic. The Welch endpoint test enters with version 2 (`revision/analyze_rev.py`, added at revision 1; `build/v2/main.pdf` names it). Version 12 corrected the df, so versions 2 to 11 are the ones that rounded down. Section 4.4, deviation R9, `revision11/test_welch_df.py` and the history of version 12 already said "2 to 11". | Corrected in the generator (`revision/analyze_rev.py`, the caption string only): "versions 2--11 rounded them down". Table 11 was regenerated (`tex/tables/rev_width.tex`; only its caption line changed). `RESULTS-REVISION.json` and `numbers_rev.tex` are byte-identical, and `revision8/check_numbers_fresh.py` is FRESH. The range stays 2 to 11 in version 13, because version 12 already used the actual df. |
| 4 | The name check's self-test fails during Windows clean-up (minor; an optional tool) | Confirmed on the desk, in Windows (Python 3.13.15, PyMuPDF 1.26.5). The committed `revision9/name_check_v10.py` exits 1 with `PermissionError: [WinError 32]` on the copied `main.pdf` when its `TemporaryDirectory` is removed, and writes no JSON. This happens on both the version-12 and the version-13 build. The cause is `d = fitz.open(...)` at line 83, which is never closed. In WSL, where the script is documented to run, Linux lets the file be removed, so the check had passed there. | Every PDF the script opens is now opened with a context manager. The planted copy is serialised and closed before the file is replaced (and the in-memory PDFs are closed too). The fixed script exits 0 with NAME_OK in Windows and in WSL, and all its positive and negative controls pass. The old script still fails in the same Windows run. Records: `records/revision12/NAME-CHECK-WINDOWS-F4.json`, `NAME-CHECK-v13-windows.json`, `NAME-CHECK-v13.json`. |

## Version 13

- Text (`revision12/edit_13.py`): the availability section names archive version 1.3 (holding version 13), release v1.3, the ten
  independent reviews and `RESPONSE-TO-REVIEW-10.md`. The history marks version 12 as no longer "this paper" and gains version 13.
  The concept DOI 10.5281/zenodo.23748861 that the paper cites is unchanged; it covers every release.
- Table 11's caption: regenerated by `revision/analyze_rev.py` (finding 3).
- Archives: `revision12/archive_v12.py` copied version 12's 28 sources into `tex/v12` (from commit b8ab198cf) and its five outputs into
  `build/v12` (checked byte for byte; `build/v12/main-arxiv.pdf` has the SHA-256 the review quotes).
- Build: `pod/build_payload_rev8.py --out H:/x1000/memistor-paper/rev12/v13`, then its `run.sh` in WSL Ubuntu with the same
  tectonic 0.15.0 (`records/revision12/BUILD-STEPS-v13.txt`). Both variants have 43 pages, as in version 12. The arXiv archive compiles
  alone, and the HTML is complete and clean. The arXiv abstract is unchanged (1,895 characters).

## Checks

- **Text** (`revision12/pdf_text_diff_v13.py`, version 12 -> version 13, word counts by `revision11/pdf_text_diff_v12.py`'s method):
  - 8 expected edits, 0 unexplained word changes and 0 edits not seen, in both variants; pages equal (43 -> 43). The edits are
    the archive version, the release, the review count, the tenth response, Table 11's caption and the two history changes.
    Records: `PDF-TEXT-DIFF-main.json` and `PDF-TEXT-DIFF-main-arxiv.json`.
  - The same check on version 11 against version 13 fails, as it must (`PDF-TEXT-DIFF-negative-v11-v13.json`: 340 unexplained).
- **Name** (`revision9/name_check_v10.py`): the author's account name appears only inside the GitHub mirror's address, in WSL
  (`NAME-CHECK-v13.json`) and in Windows (`NAME-CHECK-v13-windows.json`).
- **Numbers** (`revision8/check_numbers_fresh.py --selftest`, `NUMBERS-FRESH.json`): every `tex/numbers*.tex` equals its regeneration.
- **Figure 3** (`FIG-MAIN-CHECK.json`, with its self-test), **the reset** (`TESTS-IDEAL-RESET-COLS.json`) and **the Welch quantile**
  (`TESTS-WELCH-DF.json`) all pass.
- **Every earlier check:** `revision12/check_build_v13.py` (derived by `revision12/derive_check_v13.py`) runs
  `revision6/check_build_v7.py` and reads the records above (`ARTIFACT-CHECK-v13.json`, ALL_OK).

## Archive v1.3

Release v1.3 holds version 13 and every change above. `make_deposit.py` builds it and `deposit_cleanroom.py` reproduces it in a clean
room; the results are in `records/deposit/`. The README's "Changes since v1.2" section and `RELEASE-NOTES.md` list the changes.
