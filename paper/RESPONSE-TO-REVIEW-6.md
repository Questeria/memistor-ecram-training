# Response to the sixth independent review (ChatGPT, 2026-10-27), version 7 of the paper

The review (`reviews/REVIEW-6-chatgpt-20261027-full.md`) read version 6 (commit 0b632060a, `build/v6/main.pdf` SHA-256 2e42b090...632).
It found no new scientific or numerical error and asked for no experiment; none was run. Its one finding is cosmetic and sits in the HTML
edition only. Lane ME-REVISE-6 checked it against the files first (`revision6/verify_findings_6.py` ->
`records/revision6/VERIFY-FINDINGS-6.json`): CONFIRMED. Cost: $0 (desk, WSL; no GPU, no pod). The numbers below come from
`records/revision6/` (`VERIFY-FINDINGS-6.json`, `ARTIFACT-CHECK-v7.json`, `PDF-TEXT-DIFF-main.json`, `PDF-TEXT-DIFF-main-arxiv.json`,
`FIG-STREAMS.json`, `build-log/`).

| # | Finding | Verdict | Fix |
|---|---|---|---|
| P3 | Table 9's HTML header prints `(lr)2-6(lr)7-8` before "Seed" (main.html line 1990) | CONFIRMED: the cell text is `(lr)<span>2-6</span>(lr)<span>7-8</span> Seed`, from `\cmidrule(lr){2-6}\cmidrule(lr){7-8}` in `tex/tables/rev4_a2m.tex` | The HTML prep removes `\cmidrule` and `\cline` (with their optional width, trim and range) before pandoc; Table 9's cell is `Seed` |
| - | The completeness check compares only selected cells and would not see it | CONFIRMED (a limit of `html_complete.py`, as the review says) | A separate leftover-LaTeX check over every table and all page text (below) |

## Cause and fix

pandoc 2.19.2 (pypandoc_binary 1.13) has no rule drawing in HTML and leaves the arguments of `\cmidrule` as text in the cell that follows.
`pod/html_prep_rev6.py` (derived from `html_prep_rev5.py` by `pod/derive_build_rev6.py`, named anchors) now strips every
`\cmidrule[width](trim){a-b}` and `\cline{a-b}` from the flattened source; it removed 2 here, both in Table 9 (the other
`\cmidrule` table, `rev3_probe.tex`, is not input by the paper). `revision6/test_strip_rules.py` tests eight forms (with and without
trim, with a width, a `\cline`, a `\midrule` and a bare `(lr)` that must stay) and shows a remover that ignores the trim spec fail it.
The review asked for every table to be checked: the new check scans all 26 HTML tables, and the only other source `\cmidrule` table is not in the paper.

## The new check (`revision6/html_leftover.py`, run by `revision6/check_build_v7.py` after `revision5/check_build_v6.py`)

The page text (scripts, styles and images dropped; MathJax math spans dropped, they hold LaTeX by design) must contain no `cmidrule` or
`cline`, no `(lr)`, `(l)` or `(r)` followed by a column range, and no raw `\command`. A bare `(lr)` is legitimate (the scale table's header
"FP metric (lr)" means learning rate) and is not flagged.

| run | result |
|---|---|
| on version 6's HTML (`build/v6/main.html`) | FAIL: 2 hits, both in Table 9 (`(lr) 2-6 (lr) 7-8 Seed`) |
| six planted faults in the repaired HTML (the exact version-6 residue put back into Table 9's cell, `\cmidrule(lr){2-6}`, `(l)3-4`, `cline`, `\toprule`, `\textbf{x}`) | all six caught; each mutation changed the page; a bare `(lr)` and a LaTeX math span are not flagged |
| on the repaired HTML (`build/main.html`) | PASS: 26 tables scanned, 0 hits |
| `check_build_v6.py` (every earlier check: logs, references, table sizes, completeness with its eight planted faults, labels, failure on v4 and v5 HTML) | ALL_OK |

The check also earned its keep on my own text: the first build's history paragraph quoted the residue verbatim, and the check refused it
(`records/revision6/build-log/first-build-html-leftover.txt`). The sentence was reworded and the build repeated.

## The PDF is unchanged except the revision history

`revision6/pdf_text_diff.py` extracts both PDFs' text (page numbers dropped, ligatures folded, a re-broken hyphen joined) and compares them
word by word. Version 6 against version 7, `main.pdf`: 41 pages both, 20,398 -> 20,467 words, 4 hunks and each is an expected edit:
"five" -> "six" (the responses listed in Section 9), `RESPONSE-TO-REVIEW-6.md` added to that list, "; this paper" removed from the version-6 line
and the new version-7 sentence in Appendix F. No other word differs. The same for `main-arxiv.pdf` (20,380 -> 20,449 words, the same 4
hunks). Shown to fail: version 5 against version 7 gives 10 unexpected hunks. The regenerated figure PDFs differ by bytes (a creation
stamp) but their decoded page streams are equal (`FIG-STREAMS.json`, all seven). The arXiv archive differs from version 6's in
`app_revision.tex`, `body.tex` and those figures only; the arXiv abstract is unchanged.

## HTML rendered headless (Microsoft Edge 1280/700/420-480 px; `records/revision6/shots/`)

Top of the page (title, abstract, contents) and the end (references [42]-[45]) render with no defect. Table 9 reads `Seed | FP-SGD | sur. |
seq | gap sur. | gap seq | gap sur. | gap seq` under the group labels `P2200` and `pod (A4000)`, with no leftover text. Remaining cosmetic
points, not defects of this fix: HTML has no rules under the group labels (the `\cmidrule` drawing, which the PDF keeps), and the "gap" columns have uneven
widths because the mean row's cells are wider. At 420 and 480 px the screenshots clip the right edge (text and tables), but headless Edge keeps a minimum
window width, so I did not take that as a page defect; 700 px shows no clipping. The page has `max-width: 52em` and a viewport tag.
Scroll offsets were taken by removing the content before the element (a scrolled headless screenshot came out blank), so the table
and the end are rendered with the page's own CSS.

## Version

Version 7 (October 27, 2026; Appendix F's history names it). v6 files are kept in `build/v6/` and `tex/v6/`. Pandoc stays pinned at 2.19.2.
