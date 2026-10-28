# Response to the fifth independent review (ChatGPT, 2026-10-27), version 6 of the paper

The review (`reviews/REVIEW-5-chatgpt-20261027-full.md`) read version 5 (commit 0c2073426, `build/v5/main.pdf` SHA-256
1d4cfb3c...f3f and `build/v5/main.html` SHA-256 e8718e33...fd9, the hashes the review quotes). It accepted the PDF's science and asked for
no new experiment; none was run. Lane ME-REVISE-5 checked every statement against the files first
(`revision5/verify_findings_5.py` -> `records/revision5/VERIFY-FINDINGS-5.json`): all of them are CONFIRMED. Cost: $0 (desk, WSL; no GPU,
no pod). Numbers below come from `records/revision5/VERIFY-FINDINGS-5.json`, `PANDOC-REPRO.json` and `ARTIFACT-CHECK-v6.json`.

| # | Finding | Verdict | Fix |
|---|---|---|---|
| 1 | The HTML drops Sections 5-9, the two statements and two appendices | CONFIRMED (10 of 34 source headings absent, in v4 and v5) | Root cause removed in the build recipe; the repaired HTML has all 34 headings in order |
| 2 | The checks table's rows sit under the sensitivity table's caption | CONFIRMED | Same cause; every table caption now keeps its own header, first and last rows (26 of 26) |
| 3 | Nine reference labels are unresolved | CONFIRMED (the nine named: app:bench, app:checks, app:selection, sec:availability, sec:discussion, sec:energy, sec:limits, sec:roadmap, tab:rev_selection) | Same cause (their targets were in the lost text); none remain, no dead link |
| 4 | v4's HTML has the same defect; earlier checks missed it | CONFIRMED (same ten headings, same nine labels; `pod/html_check.py` returns 0 on both) | New completeness check fails on v4's and v5's HTML and passes on the repaired one |
| 5a | "joined the deposit" (Appendix F) vs "nothing deposited" (Section 9) | CONFIRMED | "were added to the deposit inventory" |
| 5b | "rebuilt ... from the arrays alone" is too broad | CONFIRMED: `recompute()` deep-copies each probe record and keeps its metadata (e.g. `lost_frac`) | "from them and the probe records' metadata" in Section 4.3, the availability list and PUBLISHING.md |

## Root cause (not a hand edit of main.html)

`revision5/pandoc_repro.py` reproduces it with two tiny tables and one sentence between them, using the build's pandoc (2.19.2,
pypandoc_binary 1.13). When a tabular with an absolute-length paragraph column (`p{8.8cm}`) is followed later by a tabular with a
relative one (`p{0.3\linewidth}`), pandoc reads the two as one table: the first table's rows and everything between the tables are
dropped, and the second table's rows end up under the first caption. Cases with both relative, both absolute, or the second in
`\textwidth` are read correctly. In the paper the sensitivity sheet (`p{8.8cm}`, Section 4.5) and the simulator-checks table
(`p{0.3\linewidth}`, Appendix C) triggered it, which removed Section 4.5's text, Sections 5-9, the statements and Appendices A-B; the
labels they carried were then unresolved. pandoc's log stayed empty and the build said "html ok". The old `html_check.py` greps for
raw macros only, and version 5's checks compared the abstract's digits only.

## Fixes

- `pod/html_prep_rev5.py` (derived by `pod/derive_build_rev5.py`) rewrites every `p{..}` column of a tabular to `l` (6 columns), so
  the two tables are read separately. It also letters the appendices: pandoc has no appendix counter, so the HTML printed
  "Appendix 14/15" where the PDF says "Appendix E/F". Headings and references now read "Appendix F" (an extra repair found while
  checking; the review did not list it). `pod/build_rev5.sh` runs the new check after pandoc and logs COMPLETE or INCOMPLETE.
- `revision5/html_complete.py`, run by `revision5/check_build_v6.py` after everything `check_build_v5.py` does. It passes only if:
  every `\section`/`\subsection` heading of the source (read from `tex/` independently of the converter) is in the HTML in order;
  every table caption is followed by its own table (header, first and last data row inside that table, in order); and no `??`,
  `[?]`, raw `[label]`, dead internal link or numeric "Appendix N" remains. `check_build_v6.py` also requires that every
  `sec:/app:/tab:/fig:` label of the PDF's `main.aux` (56) is an id in the HTML.
- Results (`records/revision5/ARTIFACT-CHECK-v6.json`):

  | HTML | headings missing | table problems | raw labels | dead links | verdict |
  |---|---:|---:|---:|---:|---|
  | v4 (`build/v4/main.html`, its own LaTeX tree) | 10 | 4 | 9 | 9 | FAIL |
  | v5 (`build/v5/main.html`, `tex/v5` + tables) | 10 | 4 | 9 | 9 | FAIL |
  | v6 (`build/main.html`) | 0 | 0 | 0 | 0 | PASS (34 source headings among 76 HTML headings, 26 of 26 tables, 56 of 56 labels) |

  The self-test plants eight faults in the good HTML (a dropped section, two swapped sections, one caption over another table's rows,
  a raw `[sec:energy]`, `??`, `[?]`, a dead link, a numeric appendix) and each is caught.
- Wording (5a, 5b) in `tex/app_revision.tex`, `tex/sec_fidelity.tex`, `tex/body.tex` and `PUBLISHING.md`; the availability list names
  `RESPONSE-TO-REVIEW-5.md` and "five independent reviews". Appendix F records version 6.

## Builds and checks

`build/main.pdf`, `build/main-arxiv.pdf` and the archive compiled alone each give 41 pages, no undefined reference or citation, no
overfull box; the table-size, withdrawn-phrase and revision-number checks pass (HTML abstract 28 of 28 digits; v3's HTML still
fails that check); the arXiv archive has 76 files. No number, table or figure changed; `build/arxiv-abstract.txt` is unchanged.
Version 5 is kept in `build/v5/` and `tex/v5/`, version 4 in `build/v4/`. `build/main.pdf` SHA-256 begins 2e42b090f9b3b8dd.
The build run itself used a first draft of the checker (same result on the HTML); the final `html_complete.py` was run on the
installed `build/main.html` and is what `ARTIFACT-CHECK-v6.json` records.
