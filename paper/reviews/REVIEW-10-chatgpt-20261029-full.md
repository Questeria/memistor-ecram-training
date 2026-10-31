# Independent review of paper version 12 and public release v1.2

Review date: 29 October 2026 (America/New_York). Reviewer: ChatGPT / Codex. This follows the v11 audit and uses a fresh public v1.2 clone. It is a revision and regression review, not a claim to have repeated the earlier review without knowing its findings.

## Assessment

The substantive Welch-interval error is repaired. Independently recomputing the eight endpoint comparisons from the raw records agrees with version 12. Protonic-inspired c-TTv2 on CIFAR changes from inconclusive to GROWS: the 90% Welch interval is **[0.050506763611446, 3.473493236388557] percentage points**, at df **4.675276586261936**. Both Welch and paired analyses now detect positive growth, while neither establishes growth beyond the 2 pp margin. The abstract, results, discussion and conclusion describe this correctly.

**No new major or critical scientific discrepancy was found.** All **28/28** full CPU reproduction steps pass. Against the untouched release, all **68** regenerated artifacts match: **55 byte-identical**, **7 differing only in PDF creation timestamps**, and **6 PNGs with identical decoded pixels**. All **26 tables**, **3 included figures** and **2,232 number macros** regenerate. TeX Live/pdfLaTeX builds the arXiv archive to **43 pages** with no remaining undefined reference or citation.

The remaining findings are small: one inaccurate README statement about changed numbers, two editorial inconsistencies, and a Windows cleanup failure in an optional, WSL-documented name-check self-test. None changes an experimental result or scientific conclusion. The last issue is outside the main CPU reproduction recipe.

## Materials, scope and independence

- Fresh clone: [v1.2 repository](F:/review9/memistor-ecram-training-v1.2), commit `47da4203630b179779a3433861ca5ecc937e05c4`.
- Reviewed PDF: [paper/build/main-arxiv.pdf](F:/review9/memistor-ecram-training-v1.2/paper/build/main-arxiv.pdf), **43 pages**, SHA-256 `264f29c39c779fc07394ebf12a13f0eb3fbb6f7ab7c0483bcef424c42757fb0b`. No new standalone PDF was present beside the clone; the updated public release supplied the paper.
- Public archive: [Zenodo v1.2, DOI 10.5281/zenodo.23788075](https://doi.org/10.5281/zenodo.23788075), reached through the [concept DOI](https://doi.org/10.5281/zenodo.23748861). The downloaded ZIP is 104,736,531 bytes; its MD5 `60185c563156ab2b2f6a60a14546329e` matches Zenodo. All **3,491** archived files match the Git clone byte for byte, with no extras or omissions. See [remote-release-check.json](F:/review9/audit-v12/remote-release-check.json).
- GitHub published v1.2 at `2026-10-30T01:38:36Z`, October 29 locally; Zenodo's UTC publication date is October 30. CFF now omits the previously misleading build-date release field. These dates are consistent, not a new discrepancy.
- Reproduction ran in [a separate copy](F:/review9/reproduction-v1.2). New environment, package cache, temporary files, TeX output and experiments stayed under `F:\review9`. The original v1.1/v11 materials and the fresh v1.2 reference clone were preserved. No push or publication was performed.
- I read the v1.1-to-v1.2 computational and manuscript changes before consulting the new author response. The two deferred review/response documents were excluded from the initial diff and privacy scan. The independent findings were frozen before the response comparison; the later reconciliation is reported separately below.

The change inventory contains **3,401 byte-identical files, 37 modified files and 53 additions**. All 2,677 raw JSON files under run directories and all 12 pulse-draw archives are byte-identical to v1.1; no new training or draw record was added. All 33 archived v11 source/build files equal their v1.1 originals. The three changed simulator files have identical executable ASTs after removing docstrings. The new Figure 3 fault fixture equals the public v1.0 figure source exactly. See [revision-change-summary.json](F:/review9/audit-v12/revision-change-summary.json), [release-inventory.json](F:/review9/audit-v12/release-inventory.json) and [code-change-checks.json](F:/review9/audit-v12/code-change-checks.json).

## Findings

### F1 — Minor: README understates which printed numbers changed

**Location:** [README.md:171](F:/review9/memistor-ecram-training-v1.2/README.md:171), “Changes since v1.1.”

**Problem:** After identifying the changed CIFAR verdict, the README says “no other verdict and no other printed number changed.” The verdict part is correct; the number part is not. Every Welch interval changes. For example, Li-ECRAM TTv2 on CIFAR changes from **[-0.37, 4.19]** to **[-0.34, 4.16]**, and protonic-inspired TTv2 on the LM changes from **[-19.30, -9.57]** to **[-19.12, -9.75]**. The deviation count also changes from 8 to 9, and the CIFAR inconclusive count from 2 to 1.

**Effect:** Misdescribes the numerical scope of the release. The new values are correct; it does not introduce another scientific error or verdict change.

**Confirmation:** Independent raw-record Welch calculation; exact v1.1/v1.2 JSON and macro comparison. There are 17 changed leaves in `RESULTS-REVISION.json` (16 interval endpoints and one verdict) and 19 changed/added macros, including the deviation count. The paper and RELEASE-NOTES already explain the other interval changes correctly. [Evidence](F:/review9/audit-v12/revision-change-summary.json).

**Suggested correction:** Say that all eight Welch intervals were corrected, one verdict changed, the paired comparisons are unchanged, and experimental results outside the width analysis are unchanged.

### F2 — Cosmetic: README still counts eight reviews

**Location:** [README.md:15](F:/review9/memistor-ecram-training-v1.2/README.md:15), layout table.

**Problem:** `paper/reviews/` is described as containing “the eight independent reviews.” There are **nine** numbered review reports. Section 9, the current release notes and `.zenodo.json` correctly say nine.

**Effect:** Repository-description inconsistency only; no result or conclusion changes.

**Confirmation:** Tracked-file inventory and Section 9, pp. 27–28. Replace “eight” with “nine.”

### F3 — Cosmetic: Table 11 gives the wrong start version for the Welch error

**Location:** Paper p. 21, Table 11 caption; [paper/tex/tables/rev_width.tex:1](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev_width.tex:1); generator [paper/revision/analyze_rev.py:718](F:/review9/memistor-ecram-training-v1.2/paper/revision/analyze_rev.py:718).

**Problem:** The caption says “versions 1–11” rounded down Welch degrees of freedom. Section 4.4, deviation R9, the new test and revision history correctly identify **versions 2–11**. Version 1 used the earlier GROWS/SHRINKS/FLAT heuristic, not this Welch endpoint test.

**Effect:** Historical description only; the current calculations and labels are correct.

**Confirmation:** Version-1 width source and [stats_paper.py:88](F:/review9/memistor-ecram-training-v1.2/paper/sim/stats_paper.py:88), which compares endpoint differences with the maximum endpoint interval half-width and applies a middle-width direction condition. Change the generator's caption to “versions 2–11” and regenerate the table.

### F4 — Minor, optional-tool portability: name-check self-test fails during Windows cleanup

**Location:** [paper/revision9/name_check_v10.py:83](F:/review9/memistor-ecram-training-v1.2/paper/revision9/name_check_v10.py:83), PDF fault case inside the temporary-directory context opened at line 62.

**Problem:** `d = fitz.open(...)` leaves the copied `main.pdf` open after the fault case. On this Windows environment, leaving `TemporaryDirectory` raises `PermissionError: [WinError 32]` when deleting that PDF. The command exits 1 before writing its requested JSON report.

**Effect:** An auxiliary checker fails on Windows. No paper number, training record or conclusion changes. This is **not** a failing README quick-start instruction: the script documents WSL with PyMuPDF, and README explicitly excludes desk/review-time build checks from the normal pipeline. It is also not a v1.2 regression; these lines are unchanged from v1.1.

**Confirmation:** Ran the unmodified checker against v12; retained [the traceback](F:/review9/audit-v12/name-check.log). Closing that handle before replacing the copied PDF makes the same check exit **0**, print `NAME_OK`, and pass all its positive/negative controls. [Corrected-copy result](F:/review9/audit-v12/name-check-copy.json), [exit status](F:/review9/audit-v12/name-check-copy-exit.json). This was tested with PyMuPDF 2.0 / MuPDF 1.28.5 on Windows. The isolated [copy-only patch](F:/review9/audit-v12/name-check-copy.patch) serializes the modified PDF, closes `d`, then runs the planted-content check. The reference clone was not changed.

**Suggested correction:** Close the PDF explicitly or use a context manager before replacing/deleting its backing file.


## Reproduction and numerical coverage

A fresh PowerShell session created `.venv` inside the reproduction copy and executed the README CPU install commands in order. Both pip commands exited 0. The resulting environment is Python **3.13.15**, torch **2.7.1+cpu**, NumPy **2.5.2**, matplotlib **3.9.2**, Pillow **13.0.0**, with CUDA unavailable. No Smart App Control failure occurred, so WSL was not needed for reproduction. The underlying Python installation and the already installed portable TeX Live were reused; packages for this reproduction were newly installed in the F-drive virtual environment.

The ordered quick-start used dataset copies from the earlier F-drive audit, and both fetch and verify-only passed. I then separately ran the **unchanged** `fetch_data.py` in an initially empty data directory: all three datasets downloaded from the network and the subsequent verify-only command also exited **0**. Thus both the existing-data and fresh-download branches were tested. CIFAR-10 transferred slowly in this session; this was a throughput delay, not a failed digest or instruction. [Fresh-download log](F:/review9/audit-v12/fresh-data-fetch.log), [verification](F:/review9/audit-v12/fresh-data-verify.log), [exit status](F:/review9/audit-v12/fresh-data-status.json). All 14 freshly downloaded/expanded files (468,306,907 bytes) match the reproduction cache byte for byte. [Data comparison](F:/review9/audit-v12/fresh-data-comparison.json). The pipeline also exercised corrupted-data negative controls. The commands themselves were unchanged. Environment variables confined temporary files, package caches and matplotlib configuration to F and hid CUDA; CPU libraries were limited to two threads.

[Install status](F:/review9/audit-v12/install-status.json), [torch log](F:/review9/audit-v12/install-torch.log), [requirements log](F:/review9/audit-v12/install-requirements.log), [environment](F:/review9/audit-v12/environment.json), and [ordered quick-start command results](F:/review9/audit-v12/quickstart-status.json) record the execution.

| README operation | Result |
|---|---|
| Create and activate `.venv`; install CPU torch; install requirements | Passed |
| `python fetch_data.py` | Passed against the copied, pinned dataset cache |
| `python fetch_data.py --verify-only` | Passed |
| `python -B reproduce_all.py --sums`, with `.venv` present | Passed: 3,490 files checked; the previous unlisted-venv failure is fixed |
| From `paper`, rebuild draw tables | `ALL_OK`; all three tables identical; largest relative difference from stored probe statistics 7.66e-12 |
| `python -B reproduce_all.py --fast` | 23/23 steps passed; 758.69 seconds |
| `python -B reproduce_all.py` | 28/28 steps passed; 1894.21 seconds (31 minutes 34 seconds) |

No README install/quick-start instruction failed in this tested environment. Documentation discrepancies are F1–F3. The optional, explicitly WSL-documented checker failure is F4. ENVIRONMENT's training Python, NumPy and driver claims rely partly on omitted pod logs; I did not convert those into independently verified facts. All 2,691 training records report torch 2.7.1+cu126; GPU counts are 2,421 A4000, 252 P2000 and 18 P2200, matching the document. This includes 24 superseded records outside `/runs/`. [Complete record environment check](F:/review9/audit-v12/all-record-environment.json).

The fast run regenerated **68 artifacts: 55 byte-identical, 13 matching under the stated normalizations**. The latter are seven figure PDFs after removing only `/CreationDate` and six PNG files with equal decoded pixels. No scientific-value exception was needed. Because the README runs fast before full, the full pass reports **68 byte-identical** files relative to the already regenerated fast-pass outputs. I separately compared its final outputs with the untouched release and again obtained **55 identical + 7 PDF-date-only + 6 PNG-pixel-identical**, with no mismatch. [Full pipeline](F:/review9/audit-v12/reproduce-full.json), [independent comparison](F:/review9/audit-v12/independent-artifact-comparison.json).

- All **2,232** generated number macros match, including **256** used directly in the arXiv source. [Complete expected/actual macro ledger](F:/review9/audit-v12/numeric-macro-ledger.csv).
- All **26 tables** used in the PDF match their regenerated source bytes; all **three included figures** match after the documented PDF timestamp normalization. The individual table/figure inventory appears below and in [the machine-readable ledger](F:/review9/audit-v12/paper-reproduction-ledger.json).
- The four other figure pairs kept in the release also pass regeneration; they are not four additional figures in the current paper.
- All five `numbers*.tex` files pass the separate freshness check. It rejects a changed digit, a missing file, a stray file and v8's stale macro file. [Results](F:/review9/audit-v12/numbers-fresh.json).
- The three HTML embedded figures have identical pixels to the corresponding released PNGs. HTML completeness, section/table/reference checks and all 14 completeness/leftover-LaTeX fault cases pass. [Image evidence](F:/review9/audit-v12/html-embedded-images.json), [HTML validation](F:/review9/audit-v12/html-validation.json).

A regenerated number is not necessarily a newly validated physical fact. Literature measurements, assumed budgets/thresholds and proposed bench specifications are inputs, not results that this simulation can regenerate. The unchanged hardware/reference claims were not remeasured or re-fetched from all 45 references in this revision review. The following independent checks go beyond byte agreement.

### Independent calculations from records

| Check | Fresh result |
|---|---|
| Main result cells, against FP-SGD and Adam | 144 cells; means, sample SDs and stored interval arithmetic reproduce exactly |
| Seed/control matching | 960 comparisons; matching initialization hash, data-order hash and GPU model; no mismatches |
| Selection split | All 312 inspected learning-rate/algorithm-selection records use validation |
| Selected settings | All 34 learning-rate choices reproduce the validation-grid maximum; none lies on the final grid edge; all three selected TT-family settings reproduce their validation maxima |
| Width-study cells and paired contrasts | 24 cells plus 8 paired contrasts reproduce exactly |
| Across-width initialization/data order | All 10 task-seed groups share data order; zero share identical initialization hashes across differently shaped widths, agreeing with the corrected text |
| Welch endpoint contrasts | All 8 independently recomputed from raw per-seed records; maximum interval discrepancy 5.33e-15 |
| Fractional-df t quantiles | 132 points: df 4 through 8 in 1/8 steps, probabilities .9, .95, .975 and .995; maximum discrepancy against 45-digit mpmath incomplete-beta inversion 1.51e-14 |
| Sensitivity grid | 148 points; means, SDs, intervals and labels reproduce; no mismatched labels |
| Energy components | 180 original/revised scenario rows recomputed from raw pulse/row counts and explicit pJ units; maximum component discrepancy 2.33e-10 pJ, floating-point rounding in the high-energy historical device |
| Recorded training steps | 2,364 records with layer/budget information agree with executed-loop step counts |
| Matched A2-M triples | Five seeds on one GPU; surrogate and stream gaps reproduce 8.710 and 8.734 pp; difference 0.024 pp, 95% interval approximately [-0.467, 0.515] |
| Literal quantities | 12 draw archives, 81,905,772 bytes; task budgets and Poisson(31) tail 0.4524 reproduce |

Evidence: [main statistics](F:/review9/audit-v12/independent-main-statistics.json), [pairing](F:/review9/audit-v12/pairing-audit.json), [selection splits](F:/review9/audit-v12/selection-splits.json), [selected values](F:/review9/audit-v12/selection-values-verified.json), [width/sensitivity/energy](F:/review9/audit-v12/independent-secondary-statistics.json), [step accounting](F:/review9/audit-v12/step-accounting.json), [Welch audit](F:/review9/audit-v12/welch-independent.json), [A2-M calculation log](F:/review9/audit-v12/a2m-independent.log), [literal checks](F:/review9/audit-v12/literal-number-checks.json).

### All changed Welch intervals

These are **successful corrections from v11 to v12**, not new reproduction mismatches. Units are percentage points for CIFAR and relative percentage for the LM. The table lists printed two-decimal values; full precision and raw per-seed gaps are in the Welch evidence file.

| Task / arm | v11 interval | Independent expected v12 | Released v12 | Verdict v11 -> v12 |
|---|---|---|---|---|
| CIFAR / Li-ECRAM / c-TTv2 | [-1.34, 0.66] | [-1.34, 0.65] | [-1.34, 0.65] | EQUIVALENT -> EQUIVALENT |
| CIFAR / Li-ECRAM / TTv2 | [-0.37, 4.19] | [-0.34, 4.16] | [-0.34, 4.16] | INCONCLUSIVE -> INCONCLUSIVE |
| CIFAR / protonic-inspired / c-TTv2 | [-0.02, 3.55] | [0.05, 3.47] | [0.05, 3.47] | INCONCLUSIVE -> GROWS |
| CIFAR / protonic-inspired / TTv2 | [-2.53, 0.62] | [-2.51, 0.60] | [-2.51, 0.60] | NO EVIDENCE OF GROWTH BEYOND THE MARGIN -> NO EVIDENCE OF GROWTH BEYOND THE MARGIN |
| LM / Li-ECRAM / c-TTv2 | [-15.38, -12.86] | [-15.37, -12.87] | [-15.37, -12.87] | SHRINKS -> SHRINKS |
| LM / Li-ECRAM / TTv2 | [-14.59, -11.25] | [-14.55, -11.29] | [-14.55, -11.29] | SHRINKS -> SHRINKS |
| LM / protonic-inspired / c-TTv2 | [-8.10, -5.70] | [-8.08, -5.72] | [-8.08, -5.72] | SHRINKS -> SHRINKS |
| LM / protonic-inspired / TTv2 | [-19.30, -9.57] | [-19.12, -9.75] | [-19.12, -9.75] | SHRINKS -> SHRINKS |

The corrected code retains the actual Welch–Satterthwaite df, evaluates the Student-t CDF through the regularized incomplete beta function, and inverts it by bisection. I reviewed the continued fraction, complement branch, tail conversion and endpoint interval arithmetic. The numerical reference above is independent of the repository's implementation and of its hardcoded prior-review target. The unchanged analyses retain their three-decimal integer-df t tables; replacing those constants with full-precision quantiles changes none of 337 checked decision labels (largest endpoint shift 0.0132 in its units). [Precision check](F:/review9/audit-v12/exact-t-labels.log). Restoring the old `tq(T95, df)` line **in a copy** produces the old inconclusive interval and makes `test_welch_df.py` exit **1**; the clean copy exits **0**. [Fault status](F:/review9/audit-v12/welch-fault-status.json), [clean result](F:/review9/audit-v12/welch-copy-clean.json), [fault result](F:/review9/audit-v12/welch-copy-floored.json).

### Computational code coverage

I read every changed computational hunk and every new revision-11 script. The rest of the scientific implementation is unchanged from the earlier full v11 code audit, confirmed by file hashes rather than assumed from release notes.

| Area | Review and result |
|---|---|
| Device models and pulse updates | Changed simulator text now qualifies the exact mean by the no-clipping condition and withdraws the unsupported conservatism claim. Executable ASTs are unchanged. The repaired models, reset implementation, pulse streams and probes retain the audited v11 implementation; their CPU tests were rerun. |
| Training and data sampling | No executable change. Fresh record pairing/split/step checks agree with the original audit. Two intentional historical defects remain disclosed below. No new leakage, split swap or mismatched-arm evidence was found. |
| Energy | No code or energy-record change. Independent row-based step/pulse/read accounting and unit conversions agree with the released scenarios; the obsolete `samples` field is not consumed. |
| Statistics | Only the Welch calculation changes numerically. Other changed analysis lines are the Table 8/11/16 captions and the cross-width initialization description. Main, sensitivity, width, paired and A2-M calculations were independently rerun. |
| Figures | Current figure generators are unchanged from v1.1. The Figure 3 self-test now uses a bundled public fixture; it no longer needs the author's private commit. The current figure passes and the old mean-clamping/legend-overlap fixture is rejected. |
| Revision scripts | `edit_12.py` applied to copied v11 sources reproduces all seven edited v12 text files exactly. `derive_check_v12.py` reproduces its generated checker exactly. All 33 archived v11 files match the previous public release. [Evidence](F:/review9/audit-v12/revision-script-checks.json). |

Across the simulator suites, including the supplemental `paper/sim/test_memsim.py`, **41 check executions pass and all 45 planted-fault instances are detected**. These counts include overlapping original/paper implementation tests; they are not 41 independent validations of the physical model. The new Welch test adds three successful check groups and its floored-df negative control. CPU-only, dataset-corruption, draw/hash-fault, bench, Figure 3 and reset-column checks also pass. [Test inventory](F:/review9/audit-v12/test-inventory.json), [full run log](F:/review9/audit-v12/quickstart-full.log), [supplemental simulator log](F:/review9/audit-v12/tests-paper-memsim.log).

The PDF text checker accepts v11 to v12 with 46 expected edits, zero unexplained word-count changes and one reconstructed split word; its v10-to-v12 negative control fails as required. This checker compares word counts and expected phrases, so I did not treat it as proof of all ordering/layout properties. I also inspected the ordered source edits and all 43 rendered pages. [Positive](F:/review9/audit-v12/pdf-diff-positive.json), [negative](F:/review9/audit-v12/pdf-diff-negative.json).


## Referee assessment of the revised argument

I read the current paper, including its appendices, and inspected every rendered page beside the independent pdfLaTeX build. The revised conclusions are supported within the stated simulation scope:

- Four device/algorithm pairings pass all three tasks against the same-rate FP-SGD comparator: Li-ECRAM and the protonic-inspired scenario with c-TTv2 or AGAD. The manuscript continues to distinguish that comparator from a separately tuned digital Adam baseline. No analog LM cell passes against Adam; the best remaining gap is 23.36% in bits per byte. These are not claims of hardware parity with the strongest digital training method.
- Section 4.4 no longer says different-width layers share an identical initialization. The registered Welch contrast and the later paired sensitivity analysis are both retained and distinguished. Positive endpoint growth and growth beyond the practical margin are correctly separated. The text still warns that the LM's apparent gap shrinkage accompanies a weaker large-width FP-SGD baseline at a fixed budget.
- The quadratic excess-RMS definition in Section 4.3 and Table 8 now matches the implemented statistic. The paper still states that independent surrogate draws do not reproduce shared-line dependence, that two strongly clipped update probes fail, that one short-training label reverses, and that the probe/training coverage is incomplete. These limitations have not been erased by the improved wording.
- Table 16 now clearly identifies its v1 values as superseded and directs readers to Tables 4 and 5 for current values. The original results and version-3 probe analysis remain marked as historical in the appendices.
- The 17.9–32.4 energy ratios remain conditional weight-matrix accounting results under borrowed read efficiencies and ideal-read accuracy. Section 5 explicitly excludes peripherals, nonlinear operations, movement and other system work, and does not claim an integrated device at the required accuracy or energy-to-target advantage. Independent accounting reproduced the stated scenarios.
- Simulation-only status, unmeasured/estimated device parameters, the protonic-inspired scenario, ideal reads, limited widths and training budgets, small seed counts, lack of multiplicity correction, fixed-budget baseline limitations, and internal rather than externally registered plans remain explicit.

The important remaining research limitations need new experiments or modeling; they are not unresolved bookkeeping errors introduced by v12. This review does not establish physical device feasibility, read/write circuit energy, hardware endurance, converged scaling, or generalization beyond the tested models.

## arXiv source and presentation

I extracted the released [arxiv-source.tar.gz](F:/review9/memistor-ecram-training-v1.2/paper/build/arxiv-source.tar.gz) into the empty folder [arxiv-v12](F:/review9/arxiv-v12), checked member paths for traversal/link entries, and used the existing **F-drive TeX Live 2026** installation. The archive has 76 members. All 44 released number/table source files match the archive copies. No BibTeX run was substituted for the bundled `main-arxiv.bbl`.

Three passes ran:

```text
pdflatex -no-shell-escape -interaction=nonstopmode -halt-on-error -file-line-error main-arxiv.tex
```

All exited 0. The first pass naturally reported 114 undefined-reference occurrences and 80 citation-warning occurrences. Both resolve on pass two; pass three has **zero errors, zero undefined references/citations, zero overfull boxes and zero missing-character warnings**. Eight underfull-box notices, three `h`-to-`ht` float notices and the unused epstopdf shell-escape warning remain. They do not prevent compilation.

The [independently compiled PDF](F:/review9/arxiv-v12/main-arxiv.pdf) is **43 pages, 622,242 bytes**, with the same page count and no visible content discrepancy from the released 43-page Tectonic PDF. All numeric token sequences match on each of the 43 pages. Whitespace/ligature-normalized text matches on 41 pages; the only differences on the other two, pp. 15 and 19, are a PDF text-extraction variation selector (`U+FE02`) after the radical in the new RMS equation. This is not a changed mathematical symbol. The formerly missing Jacobs-Gedrim hyphen now appears in both builds.

The large whitespace around the Table 11 float on p. 21 is present in both builds; it is a layout choice, not omitted content. The total page increase from 42 to 43 is documented by the release. I found no cropped table, broken legend, missing figure, unresolved citation or missing appendix. The HTML structure and embedded figure pixels also pass the checks described above; browser/mobile interaction was not tested.

Evidence: [compile status](F:/review9/audit-v12/pdflatex-status.json), [final compile log](F:/review9/audit-v12/pdflatex-pass3.log), [warning inventory](F:/review9/audit-v12/latex-warning-inventory.json), [per-page numeric/text comparison](F:/review9/audit-v12/pdflatex-content-comparison.json), [exact extraction differences](F:/review9/audit-v12/pdf-text-differences.json), [rendered page comparisons](F:/review9/audit-v12/visual).

This demonstrates a local TeX Live/pdfLaTeX build using the supplied bibliography. It does not demonstrate a submission to, or acceptance by, arXiv's production service; nothing was uploaded.

## Availability, licensing and exposed context

All **78** explicit availability/archive/layout path checks pass, including archived versions 1–11, the plans, current analyses, pulse streams/probes, draw archives, checks, catalogue and licences. Generated table/figure paths are additionally covered by the reproduction ledger. [Path evidence](F:/review9/audit-v12/availability-paths.json).

Section 9, `CITATION.cff`, `.zenodo.json` and the live Zenodo metadata agree on paper v12/release v1.2, the concept DOI and the MIT-code/CC-BY-4.0-data-and-text split. Zenodo labels the deposit as CC BY 4.0 and explicitly preserves the separate MIT code terms in its description. `LICENSE` and `LICENSE-DATA` are present. The named datasets are absent from tracked release files and retain their own terms. This is a check of the deposited licence declarations and consistency, not a determination of rights in every cited third-party work.

The README size statement is correct: **3,490 files excluding SHA256SUMS, 131,937,854 bytes (131.9 decimal MB)**. Adding the manifest gives the release-note count of 3,491 files. The only current repository-description errors found are F1/F2; the paper's archive-version explanation is accurate.

Privacy is now disclosed more accurately, rather than all internal context having been removed. `REDACTIONS.md:21–26` expressly retains desk paths, other-project/channel names and host identifiers as provenance. The initial scan, excluding the two deferred review/response files, found 193 Windows-style path occurrences (including examples/placeholders) and one Unix-style personal-path occurrence. Surviving internal labels include **Cryptum, Helios, HIVE, Helix, kovc and Domain3**, as well as pod host identifiers. Machine-readable namespaces such as `<namespace>.me-revision.results.v1` also remain (for example `paper/records/revision/RESULTS-REVISION.json:6871`). The public GitHub handle and author name are intentional public identities, not credentials. See the per-file/line [path/name ledger](F:/review9/audit-v12/privacy-independent.json) and [internal-context ledger](F:/review9/audit-v12/internal-context.json).

No tested credential pattern, credential-like context or secret-file name was found. Ten source archives contain no hits in the tested path/name/secret patterns; 31 PDFs, totalling 957 pages including historical versions and figures, and their metadata contain no hits in the tested internal-path/credential patterns. After reading the response and prior review, the completed text scan covers **3,425 files**, **202 Windows-style path occurrences**, one Unix-style personal path and one intentional GitHub noreply email mention; still no credential-pattern hit. All 12 deposited-file hashes listed in REDACTIONS match. [Complete scan](F:/review9/audit-v12/privacy-complete.json), [redaction output hashes](F:/review9/audit-v12/redaction-output-hashes.json). These checks cannot rule out arbitrary undocumented secrets or prove what the author's unavailable unredacted originals contained. [Archive scan](F:/review9/audit-v12/privacy-archives.json), [PDF text scan](F:/review9/audit-v12/privacy-pdf-text.json), [credential-context scan](F:/review9/audit-v12/credential-context-scan.json).

## Intentional defects retained in the historical implementation

These are carried-forward disclosures, not fresh v12 regressions:

1. **LM final training window excluded.** `torch.randint(0, len(tr) - ctx - 1)` has an exclusive upper bound and omits the final valid window. It involves no held-out bytes. Section 3.5 and README explain it. The code/records are kept as run; the effect of correcting the bound on training outcomes cannot be determined without new training realizations.
2. **`samples` overcounts skipped incomplete batches.** The record field still counts the nominal epoch size while the loop omits incomplete batches. README explains it; the energy consumer has already been changed to derive steps from layer row counts. The fresh 2,364-record step audit and 180 energy-scenario checks confirm that the present published energy calculations no longer use that field.

## What could not be checked in this review

- No training runs were repeated, and no physical hardware experiment was performed. Reproduction starts from saved records/draws, as the README specifies. It does not independently authenticate the original execution environment or prove the records were produced by the deposited source.
- A fresh network download and pinned-digest verification succeeded, in addition to the cached-data reproduction. Installation succeeded on the tested Windows/Python 3.13 environment; other Python versions and operating systems were not exhaustively tested.
- Omitted pod session logs, private Git history, the unredacted original reviews and build orchestration outside the deposit were unavailable. Claims derived only from them remain unverified. The archived v11 output bytes, however, were independently matched to public v1.1.
- I did not rerun the network citation audit or repeat literature/device-parameter extraction for unchanged references. All scientific data and non-Welch computations were compared with the prior audit and subjected to the fresh regression/record checks above.
- Some author-side archival/build wrappers deliberately depend on private history or desk layout. They were inspected as provenance rather than presented as portable commands. The new edit/check derivation scripts were tested in copies; the arXiv archive was actually compiled independently.
- Privacy scans cover declared patterns and readable PDF/source content, not arbitrary steganography or unknown credential formats. Licence-file consistency is verified; upstream rights ownership is not.
- The official arXiv service, mobile HTML layout and live device/circuit behavior were not exercised.


## Prior review and author response: checked after the independent phase

The main independent phase completed at **2026-10-30 02:47:38 UTC** (October 29 locally), with the four findings above already recorded and the review/response still unread. I then read the full deposited review 9 and [the response](F:/review9/memistor-ecram-training-v1.2/paper/RESPONSE-TO-REVIEW-9.md). The additional fresh network-download check was still running; it does not supply or alter the scientific findings. [Independent freeze](F:/review9/audit-v12/independent-phase-complete.json), [response-check record](F:/review9/audit-v12/response-cross-check.json).

| Prior finding | v1.2 / v12 status | Independent confirmation |
|---|---|---|
| 1. Floored Welch df changes a verdict | **Fixed** | Raw-record reconstruction, independent high-precision t quantiles, all eight interval rows, the new test and a physically changed faulty copy. The corresponding prose now agrees. |
| 2. Excess-RMS statistic undefined | **Fixed by definition** | Section 4.3 p. 15 and Table 8 p. 19 explicitly give the quadrature formula used by the analysis. Draw-derived values are unchanged and regenerate. |
| 3. Table 16's “this paper” label | **Fixed** | P. 36 identifies v1/superseded values and points to current Tables 4/5; the generator reproduces that caption and all three “v1” column labels. |
| 4. Initialization claimed shared across widths | **Fixed** | Ten task/seed groups share example order but not initialization hashes; both Section 4.4 and `width_paired` now state the correct distinction. |
| 5. `.venv` breaks checksums | **Fixed** | README's in-root fresh environment is present; `--sums` exits 0 with all 3,490 manifest entries. Both directory walks exclude `.venv`. |
| 6. Figure self-test requires private history | **Fixed** | Bundled fixture equals public v1.0 bytes. Both fast and full pipelines run `--selftest` successfully and reject the faulty plotting code. |
| 7. Internal paths/names remain | **Disclosed and intentionally retained** | Strings remain; REDACTIONS explicitly scopes its zero-hit claim and identifies retained provenance. This is disclosure, not erasure. Complete privacy results are supplied. |
| 8. Wrong Python minimum | **Fixed** | README and reproducer now state 3.12 minimum for pinned NumPy; installation on 3.13.15 succeeds. Training-environment history is kept separate. |
| 9. “Conservative” Poisson docstrings | **Fixed** | All three module docstrings qualify the mean by clipping and withdraw conservatism; executable ASTs are unchanged. |
| 10. CFF build date used as release date | **Fixed** | Optional `date-released` is omitted; live GitHub/Zenodo release metadata is coherent. |
| 11. Tectonic drops surname hyphen | **Fixed** | ASCII hyphens in both relevant bibliography strings; rendered reference [5] agrees between engines. |
| K1. Omitted final LM training window | **Still disclosed, preserved as run** | Source bound unchanged; Section 3.5 and README explain it. No held-out byte is implicated. |
| K2. Overcounted `samples` | **Still disclosed; energy consumer remains repaired** | Recorded field unchanged; published energy derives steps from layer row counts and reproduces independently. |

The response's substantive fixed/disclosed classifications are supported. F1–F3 above are small residual wording inconsistencies; F4 is an additional Windows-only observation about a WSL-documented auxiliary check, not a contradiction of the author's WSL result. The response's author-side `make_deposit.py`, `deposit_cleanroom.py` and `records/deposit/` references are not public reproduction tools/paths in this release; I verified the supplied `VERIFY.json` claims against actual public outputs rather than attempting to invoke absent author-side builders.

## Final integrity and evidence

The final reference-clone Git status is empty and all **3,490 SHA256SUMS entries** match. The released PDF retains its original SHA-256. [Final integrity](F:/review9/audit-v12/final-integrity.json). The prior [v11 report](F:/review9/audit/REVIEW.md) is preserved. This report and all new scripts, logs, comparisons, altered test copies and rendered evidence are under [audit-v12](F:/review9/audit-v12).

The tested release has no remaining major or critical discrepancy identified by this review. Correct the small text issues before packaging another version, and close the auxiliary PDF handle if Windows support for that checker is desired. These corrections require no new training experiment. The paper should retain its explicit simulation, comparator, surrogate, energy and small-sample limits.


## Complete table and figure regeneration inventory

Expected bytes are the v1.2 release; actual bytes are the fresh regeneration. Table cells and captions match exactly. Figure comparisons remove only the PDF creation timestamp. The macro CSV gives each generated number and its actual value separately.

| Table | PDF page | Released/generated source | Comparison |
|---|---|---|---|
| 1 | 7 | [tables/rev2_catalog.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev2_catalog.tex) | Byte-identical |
| 2 | 10 | [tables/e1.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/e1.tex) | Byte-identical |
| 3 | 10 | [tables/e1b.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/e1b.tex) | Byte-identical |
| 4 | 14 | [tables/rev_main_vs_fp.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev_main_vs_fp.tex) | Byte-identical |
| 5 | 15 | [tables/rev_main_vs_adam.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev_main_vs_adam.tex) | Byte-identical |
| 6 | 17 | [tables/rev4_probe_sur.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev4_probe_sur.tex) | Byte-identical |
| 7 | 18 | [tables/rev4_probe_seq.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev4_probe_seq.tex) | Byte-identical |
| 8 | 19 | [tables/rev4_dep.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev4_dep.tex) | Byte-identical |
| 9 | 20 | [tables/rev4_a2m.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev4_a2m.tex) | Byte-identical |
| 10 | 20 | [tables/rev3_fid.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev3_fid.tex) | Byte-identical |
| 11 | 21 | [tables/rev_width.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev_width.tex) | Byte-identical |
| 12 | 22 | [tables/rev_spec_p.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev_spec_p.tex) | Byte-identical |
| 13 | 24 | [tables/rev_energy.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev_energy.tex) | Byte-identical |
| 14 | 34 | [tables/rev2_selection.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev2_selection.tex) | Byte-identical |
| 15 | 35 | [tables/checks.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/checks.tex) | Byte-identical |
| 16 | 36 | [tables/laneme.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/laneme.tex) | Byte-identical |
| 17 | 37 | [tables/v1s_catalog.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/v1s_catalog.tex) | Byte-identical |
| 18 | 37 | [tables/v1s_e2.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/v1s_e2.tex) | Byte-identical |
| 19 | 37 | [tables/v1s_main.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/v1s_main.tex) | Byte-identical |
| 20 | 38 | [tables/v1s_scale.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/v1s_scale.tex) | Byte-identical |
| 21 | 38 | [tables/v1s_spec.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/v1s_spec.tex) | Byte-identical |
| 22 | 38 | [tables/v1s_spec_rel.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/v1s_spec_rel.tex) | Byte-identical |
| 23 | 38 | [tables/v1s_pairs.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/v1s_pairs.tex) | Byte-identical |
| 24 | 39 | [tables/v1s_energy.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/v1s_energy.tex) | Byte-identical |
| 25 | 42 | [tables/rev_d1.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/rev_d1.tex) | Byte-identical |
| 26 | 43 | [tables/v3s_rev2_probe.tex](F:/review9/memistor-ecram-training-v1.2/paper/tex/tables/v3s_rev2_probe.tex) | Byte-identical |

| Figure | PDF page | Released/generated file | Comparison |
|---|---|---|---|
| 1 | 11 | [figs/fig_validation.pdf](F:/review9/memistor-ecram-training-v1.2/paper/tex/figs/fig_validation.pdf) | Identical except creation timestamp |
| 2 | 13 | [figs/fig_rev_main.pdf](F:/review9/memistor-ecram-training-v1.2/paper/tex/figs/fig_rev_main.pdf) | Identical except creation timestamp |
| 3 | 39 | [figs/fig_main.pdf](F:/review9/memistor-ecram-training-v1.2/paper/tex/figs/fig_main.pdf) | Identical except creation timestamp |

Tables 16–24 and 26, and Figure 3, are historical/superseded material as identified in the paper. Matching their records does not turn them into current repaired-simulator results. The other four regenerated figure pairs (`fig_energy`, `fig_oat_cifar`, `fig_oat_lm`, `fig_scale`) are retained release outputs and do not appear in the current 43-page PDF.
