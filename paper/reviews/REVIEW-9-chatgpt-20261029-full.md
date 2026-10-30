**Independent pre-arXiv audit — paper v11 and public release v1.1**  
Anthony DeMarco, *Can memistor-class electrochemical weights train neural networks?*  
Reviewed 29 October 2026. All scientific results discussed here are simulations.

The deposit reproduces successfully, but I recommend a revision before arXiv. I found **one major statistical reporting issue, eight minor issues and two cosmetic issues**, plus two implementation defects already disclosed and intentionally preserved. The major issue is confined to the width study: the advertised Welch calculation silently floors its degrees of freedom. Using the standard fractional degrees of freedom changes one verdict from **INCONCLUSIVE to GROWS**. It does not establish growth beyond the 2 pp margin and does not change the main training conclusions.

The literal README sequence has one failure: installing `.venv` inside the repository makes its subsequent checksum command reject the environment's files. After continuing through that failure, the fast and full CPU pipelines succeed. **All 27 full-pipeline steps pass; all 26 paper tables, all 3 paper figures and all 2,231 numerical macro definitions regenerate with the deposited values.** This establishes reproduction of the released calculations; the Welch issue illustrates why reproduction alone does not establish that the calculations implement the stated method.

The arXiv source archive compiles with **TeX Live 2026 / pdfLaTeX**, using its bundled bibliography, to **42 pages**, with no remaining undefined references or citations. Every page's numeric tokens match the supplied PDF. One bibliography surname has a visible hyphen difference between pdfLaTeX and the supplied Tectonic PDF.

The four published-device/algorithm pairings that pass all three task margins against same-rate FP-SGD remain supported by the records: Li-ECRAM and protonic-inspired devices, each with c-TTv2 and AGAD. None passes all three against tuned Adam; the best analog LM remains 23.36% worse in bits per byte. I found no additional current training/evaluation leakage or mismatched initialization/data-order pairing in the audited comparisons. These statements concern the simulated models and fixed training budgets, not physical devices or demonstrated system energy savings.

**Scope, provenance and independence**

The original clone is [memistor-ecram-training](../memistor-ecram-training), tag `v1.1`, commit `aaee0bed81a95bc909a8df34ba3c9a5e8f26c16e`. The comparison tag `v1.0` is `076624fbc58b2d50041bf88f2549ff58e37ee52d`. I reviewed the release changes before the computational audit. Source/document changes were read line by line; repeated archived files and bulk numerical/binary changes were additionally checked by byte identity, structured differences and regeneration. The two review-8 documents were withheld from content reads until the independent work was complete. Their deferred diff is [preserved](diff-deferred-now-read.patch).

The supplied [v11 PDF](../memistor-paper-v11.pdf) is byte-identical to `paper/build/main-arxiv.pdf`: SHA-256 `67530090a653ced3af9475323a72e1798d89ecd38e1d06c2c0dbbc6b8a2a021d`. The arXiv archive's SHA-256 is `9e3f631e5ea83a87166dce84c56c5115753c418ae7e9c38d65398d7cce73e17e`.

Research inputs were the fresh public clone, supplied PDF and public release/DOI metadata. I did not read private project folders, prior local audits, memories or anything under `C:\Projects`. References to other drives in this report are literal strings found inside the release; I did not open those paths. Reproduction, fault experiments, caches, temporary files, Python environments and TeX Live were placed under `F:\review9`. Existing system executables/standard-library code were used; no package or TeX installation was made on C:. No push or publication was performed.

The pristine clone was not edited. Generators ran in [reproduction](../reproduction); altered code ran in separate copies. Its final Git status is empty, all **3,437 manifest entries pass**, and the supplied PDF's hash is unchanged: [final integrity](final-integrity.json), [final checksum log](pristine-sums-final.log).

The independent phase was frozen at **2026-10-29 16:58:40 -04:00**, after steps 1–4, with review 8 and its response still unread. The frozen [findings](independent-findings.md) and [evidence hashes](independent-phase-complete.json) already include the Welch finding. Only then did I read the prior review and response. Two supplemental checks afterward reverified learning-rate selection scores and ran the overlapping paper copy of the original simulator test; they are identified in their evidence. The nine-item reconciliation below is separate from the independent findings.

**Execution of README.md and ENVIRONMENT.md**

The documented installation was executed in a fresh PowerShell shell in the reproduction copy, including creating and activating `.venv`, installing `torch==2.7.1` from PyTorch's CPU index, and installing `requirements.txt`. The resulting environment is Python **3.13.15**, torch **2.7.1+cpu**, NumPy **2.5.2**, matplotlib **3.9.2**, Pillow **13.0.0**. Imports and CPU tensor operations succeeded. Smart App Control did not block loading; **WSL was not used**. The audit-only PDF environment is separate from the pinned reproduction environment.

| README action, in its written order | Observed result | Evidence |
|---|---|---|
| Create/activate `.venv`; install CPU torch and requirements | Succeeds | [torch installation](install-torch.log), [requirements installation](install-requirements.log) |
| `python fetch_data.py` | Exit 0; all downloaded dataset digests pass | [download log](quickstart-1-fetch.log) |
| `python fetch_data.py --verify-only` | Exit 0 | [verification](quickstart-2-verify.log) |
| `python -B reproduce_all.py --sums` | **Exit 1: 0 mismatches, 16,928 unlisted `.venv` files** | [failure](quickstart-3-sums.log); finding 5 |
| `cd paper`; `python -B revision4/rebuild_draw_tables.py --draws draws/rev3`; `cd ..` | Exit 0, `ALL_OK`; shell returns to root | [draw reconstruction](quickstart-4-draws.log) |
| `python -B reproduce_all.py --fast` | Exit 0; 22/22 steps pass; 55 identical + 13 normalized outputs | [fast result](REPRODUCE-fast.json), [console](quickstart-5-fast.log) |
| `python -B reproduce_all.py` | Exit 0; 27/27 steps pass, `REPRODUCE_ALL_OK` | [full result](REPRODUCE-full.json), [console](quickstart-6-full.log), [step logs](reproduction-logs/) |

The full run took about **38 minutes 23 seconds**, following the separate fast run. The documented timing is approximate; I do not count host-dependent elapsed time as a defect. The complete exit/time sequence is in [quickstart-status.json](quickstart-status.json). The downloaded and expanded dataset folder occupies **468,306,907 bytes**; README's “about 0.2 GB” is a reasonable compressed-download estimate, not the retained disk footprint.

Because the README runs fast before full, the full pipeline compares against files already regenerated by fast and reports **68 byte-identical** outputs. I therefore independently compared all 68 final outputs to the untouched clone: **55 byte-identical, 7 PDF creation-date-only differences, 6 PNGs with identical RGBA pixels, zero mismatches**. No normalization discards plot geometry or changes pixels. See [independent final comparison](independent-final-68.json).

The untouched clone's checksum check succeeds when invoked with the Python environment outside that clone. This separates the README/environment-directory failure from deposited-file corruption. No other mandatory README/ENVIRONMENT execution instruction failed in the tested Python 3.13 environment. The misleading Python-minimum claim and the optional figure self-test failure are separate findings below. Historical desk-specific build/check scripts are expressly excluded by README; their private-history dependencies are not presented here as failures of the documented CPU pipeline.

**Findings**

Severity: critical would invalidate the central result or expose an immediately consequential secret; major changes a reported inference or materially obstructs review; minor affects a limited calculation, description, diagnostic or instruction; cosmetic affects metadata or presentation only. No critical finding was established. The major finding below changes one width-study inference, not the headline comparison to FP-SGD/Adam.

**1. Major (one width-study verdict; not the headline training conclusion) — Undisclosed integer rounding changes the advertised Welch analysis.**

Locations: paper/revision/analyze_rev.py:31–33,126–153; paper p17 section 4.4 and p20 Table 11; paper/tex/sec_scale.tex:19–21,36–38; paper/tex/tables/rev_width.tex:5.

The code computes Welch-Satterthwaite fractional degrees of freedom, but tq() then floors them to an integer. Neither the paper nor PLAN-REVISION.md:97 describes this conservative approximation. For CIFAR protonic-inspired c-TTv2, D=1.762 pp and df=4.675276586261936. The deposited calculation uses the df=4 table value 2.132 and reports [-0.021101612700745287, 3.5451016127007478], displayed [-0.02, 3.55], INCONCLUSIVE. The standard Welch calculation at the actual df gives [0.050506763611446015, 3.4734932363885567], displayed [0.05, 3.47], GROWS under the paper's own decision order. Thus the statement that the paired analysis detects growth which the Welch test misses depends on an unstated rounding convention. All eight Welch intervals change at displayed precision (one endpoint of the first row remains the same); their expected/actual values are in welch-copy-verification.json. Only this one verdict changes; neither interval establishes growth beyond the 2 pp margin, and the same arm's paired growth finding and headline main-table results survive.

Confirmation: independently inverted the Student-t CDF through the regularized incomplete beta function; verified integer-df critical values against the standard constants; read raw five-seed endpoint records; reproduced every original saved Welch result; then changed only fractional-df quantile evaluation in an isolated copy of analyze_rev.py. The copied function produces the result above. No repository source changed. Evidence: welch-copy-verification.log/json, welch-quantile-check.log/json, welch-copy-change.patch, welch-fault-copy/analyze_rev.py.

Remedy: disclose the conservative integer-df convention and provide the actual-df sensitivity result, or use the standard fractional-df quantile and regenerate Table 11 and the corresponding wording/counts. Preserve the preregistered calculation as such if the rounding was part of it; do not silently rewrite its historical status.

All affected Welch intervals, in the units of Table 11 (CIFAR pp; LM relative bpb %):

| Task / arm | Deposited interval | Standard fractional-df interval | Verdict change |
|---|---|---|---|
| CIFAR / Li-ECRAM c-TTv2 | [-1.34, 0.66] | [-1.34, 0.65] | None |
| CIFAR / Li-ECRAM TTv2 | [-0.37, 4.19] | [-0.34, 4.16] | None |
| CIFAR / Protonic-inspired c-TTv2 | [-0.02, 3.55] | [0.05, 3.47] | INCONCLUSIVE → GROWS |
| CIFAR / Protonic-inspired TTv2 | [-2.53, 0.62] | [-2.51, 0.60] | None |
| LM / Li-ECRAM c-TTv2 | [-15.38, -12.86] | [-15.37, -12.87] | None |
| LM / Li-ECRAM TTv2 | [-14.59, -11.25] | [-14.55, -11.29] | None |
| LM / Protonic-inspired c-TTv2 | [-8.10, -5.70] | [-8.08, -5.72] | None |
| LM / Protonic-inspired TTv2 | [-19.30, -9.57] | [-19.12, -9.75] | None |

All eight original intervals were first reproduced exactly from the raw endpoint records. The changed-copy experiment modifies only fractional-df quantile evaluation; no training was repeated. Separately, replacing the rounded integer-df t constants with full-precision quantiles changes none of 337 checked main/width-cell/sensitivity PASS/FAIL/UNRESOLVED labels ([sensitivity evidence](exact-t-label-sensitivity.json)). The paired-width result is already disclosed by the paper; the issue here is the additional, unstated degree-of-freedom approximation in its Welch column.

**2. Minor — The dependence statistic needs its actual quadrature definition in the paper.**

Locations: paper p15, section 4.3; Table 8 p19; paper/tex/sec_fidelity.tex:41–44; paper/revision3/analyze_rev3.py:85; paper/revision4/analyze_rev4.py probe table caption.

The text says RMS correlation exceeds its null by up to 0.345, exceeding 0.05 on six probes. The code uses sqrt(max(0, RMS_slot^2 - RMS_null^2)), not RMS_slot - RMS_null, and the paper does not state this formula. For the maximum case (MNIST, layer 2, update 3500, row-sharing pairs), slot RMS=0.43100807845246264 and null RMS=0.2582105428201874. Their ordinary difference is 0.17279753563227523; the quadrature excess is 0.34510183898059477. Arithmetic differences exceed 0.05 on five probes, whereas the chosen quadrature statistic exceeds it on six. The stored statistic and Table 8 regenerate correctly; the general finding of detectable line dependence survives. Define the quadrature excess explicitly and describe 0.345 as that statistic. Evidence: rms-definition-check.json, regenerated probe tables/draw checks.

**3. Minor — Table 16 calls superseded v1 numbers 'this paper'.**

Locations: paper p35, Appendix D, Table 16; paper/tex/tables/laneme.tex:2–3; paper/analyze.py:604–625.
Its 'this paper' columns come from the original RESULTS-PAPER.json, not the current repaired simulator. For example, MNIST Li-ECRAM SGD prints 4.85 pp versus current 6.41 pp; MNIST MO-ECRAM SGD prints 6.96 pp versus current 11.51 pp. The table is reproducible as a historical comparison, but its caption does not identify the paper-v1 lane as superseded as the adjacent Appendix E tables do. Relabel the columns and caption 'paper v1 (superseded)' rather than replacing historical data. All thirty cells and their current counterparts are in table16-current-vs-historical.csv. Main Tables 4–5 and headline conclusions are unaffected.

**4. Minor — The width discussion overstates shared initialization across widths.**

Locations: paper p17, section 4.4; paper/tex/sec_scale.tex:11–14; paper/revision/analyze_rev.py:155–158.

The statement that every arm of a seed shares logical initialization and data order 'across widths' is too strong. Within each width the relevant comparisons are correctly matched. Across the three widths, all ten task/seed groups have different initialization hashes and all ten have the same example-order hash. Different dimensions and fan-in scales also preclude equal initialization matrices. The paired-by-seed sensitivity calculation itself is reproduced; shared example order/seed blocking supports reporting it. Say initialization is matched within each width, and seeds/example order are shared across widths. Evidence: independent-secondary-statistics.json (cross_width_hashes), pairing-audit.json.

**5. Minor — The literal README installation makes the subsequent checksum command fail.**

Locations: README.md:47–58; reproduce_all.py:152–156.

The README creates .venv inside the root and then asks for --sums. The checksum walk excludes .git, data, _repro and __pycache__, but not .venv. Expected: SUMS_OK 3437 files / exit 0. Actual: SUMS_FAILED mismatches=0 unlisted=16928 / exit 1, all unlisted entries in .venv. The untouched clone checks successfully when invoked with the environment outside that clone. No deposited file was corrupt and no numerical result changes. Evidence: quickstart-3-sums.log, pristine-sums.log, quickstart-status.json. Fix the instructions to put the environment outside the checked tree, or exclude the specifically documented environment directory.

**6. Minor — The figure check's advertised fault self-test depends on an unavailable private commit.**

Locations: paper/revision10/check_fig_main.py:7–10,22,95–103.

Expected: the documented --selftest returns a passing positive control and rejects the historical faulty figure. Actual: exit 1 / CalledProcessError because git show 604285ff4:./make_figures.py returns 128 in the public clone. The default check passes. An independent harness using the publicly available v1.0 version as the negative control rejects two misdrawn means and 11 legend overlaps. No current figure changes. Evidence: fig-selftest.log, figure-check-public-history.json, fig-public-history.log. Use a public tag or a bundled fault fixture for this self-test. README's exclusions for historical verify_findings/check_build scripts do not name this new check.

**7. Minor — Internal paths, project names and machine names remain in the release.**

Locations include DEPOSIT-PATCHES.json:22,46,70; VERIFY.json:325,340,355; paper/PLAN-REVISION-2.md:91–93; REDACTIONS.md:19–21 and run-record host fields.

Examples include C:/Projects/Cryptum/tests/corpus/external/enwik8, Helios Evolution B1, HIVE, Helix, kovc, F:/shared/LIVE-HOLDS.jsonl, many H:/<desk folder> paths and host Domain3. These were read as strings in the deposit; none of those external paths was opened. The old-path values in DEPOSIT-PATCHES are provenance, not active dependencies. README explicitly acknowledges old interpreter paths, but the zero-hit redaction statement should not be read as a guarantee that all internal context is absent. No credential pattern was found. Public author/repository names Anthony DeMarco and Questeria are intentional attribution, not secrets. Evidence: privacy-independent.json, privacy-archives.json, privacy-pdf-text.json; a complete occurrence/path inventory accompanies the final report. No result changes.

**8. Minor — The advertised Python minimum conflicts with the pinned reproduction dependencies.**

Locations: reproduce_all.py:18–20; requirements.txt:1.

The script says Python 3.10+, while pinned numpy==2.5.2 declares Requires-Python >=3.12. A Python-3.10-targeted pip resolution exits 1 with no matching distribution. Python 3.13.15, the version actually named by the README's tested installation, works. State the minimum for the pinned environment separately from the older training environment. Evidence: python310-resolution.log and installed distribution metadata. No numerical change in the tested environment.

**9. Minor — The active simulator's documentation retains the withdrawn conservatism claim.**

Locations: paper/sim/memsim_rev.py:38–40; paper/sim/memsim.py:23–25; pulse_counts documentation.

The module describes the aggregate Poisson approximation as conservative and as having the exact mean without the probability-clipping condition. Paper section 3.2 correctly withdraws general conservatism and qualifies the unclipped expected count; the probes demonstrate failure in the highly clipped regime. This is stale code documentation, not a newly discovered implementation error. Update the docstrings to match the paper. No computed value changes.

**10. Cosmetic — CITATION.cff's release date differs from the public release dates.**

Location: CITATION.cff:6.

Actual date-released: 2026-10-28. GitHub v1.1 was published 2026-10-29T17:53:34Z, Zenodo publication_date is 2026-10-29, and DataCite Issued is 2026-10-29. October 28 is the paper/build date. Align the software release date, or distinguish these dates explicitly. Version 1.1 and the concept DOI are otherwise correct. Evidence: github-release-v11.json, zenodo-v11.json, datacite-v11.json. No numerical effect.

**11. Cosmetic — One surname differs visibly between the supplied Tectonic PDF and pdfLaTeX.**

Locations: paper p28 reference [5]; paper/tex/refs.bib:260; bundled main-arxiv.bbl:41.

The source has Jacobs‐Gedrim (U+2010 hyphen). The supplied PDF visibly prints JacobsGedrim; pdfLaTeX prints Jacobs-Gedrim. Numeric tokens, page count and references otherwise agree. High-resolution crops confirm that this is visible, not merely an extraction difference. Use a TeX-safe hyphen if identical bibliography rendering is wanted. Evidence: visual/surname-tectonic.png, visual/surname-pdflatex.png, pdflatex-content-comparison.json. No scientific effect.

**Retained defects already disclosed by the release**

These are still defects of the recorded implementation/metadata, rather than newly repaired training runs. Their preservation and effect are stated explicitly.

**K1 — Minor, already disclosed — The LM sampler omits the final valid training window.**

Locations: paper/sim/run_rev.py:173; paper/sim/run.py:162; README.md:156–160; paper p7 section 3.5.

For a slice of length N and context c, a window needs c+1 bytes, hence the inclusive last start is N-c-1. torch.randint uses an exclusive upper bound; the current high=N-c-1 yields starts only through N-c-2. Expected corrected high=N-c. The last training byte cannot be a target. It does not touch held-out data. Correcting it changes the random realization of training; the changed accuracies cannot be inferred without rerunning. The disclosure and preservation of the original code are appropriate for tracing the records.

**K2 — Minor, already disclosed; energy consumer repaired — The classification samples fields overcount processed examples.**

Locations: paper/sim/run_rev.py:145–162; paper/sim/run.py:136–152; README.md:161–162; paper/energy/energy_system.py step-count helper.

The loop drops incomplete batches but samples uses the full training-set size per epoch. Among 2,364 inspected records with sufficient budget/layer information, 1,460 classification records have the overcount. Examples (recorded vs actually processed): MNIST 550000 vs 549120; CIFAR full budget 300000 vs 299520; CIFAR shorter budget 100000 vs 99840; MNIST-GH 3000000 vs 2998400. All row-derived step counts agree with the loop. The v1.1 energy code uses those correct counts, not samples. The exact unrounded energy totals changed from v1.0, but all printed values remain unchanged. Evidence: retained-samples-overcounts.csv, step-accounting.json, energy-tag-diff.json, independent-secondary-statistics.json.

**Every table, figure and numerical output**

The reproduction expectation is the pristine v1.1 file; the actual value is the freshly regenerated file. There are **no regeneration mismatches**. Findings 1–4 distinguish errors or ambiguity in statistical interpretation/provenance from byte-for-byte reproduction. In particular, Table 11 reproduces the integer-df convention exactly, and Table 16 reproduces its historical data exactly.

The [macro ledger](numeric-macro-ledger.csv) gives every macro's file, source line, expected value, actual value, equality flag and current-use locations. The [table text inventory](table-text-inventory.json) retains full expected and actual text; the [paper inventory](paper-reproduction-ledger.json) retains page/label/hash mappings; the [68-output comparison](independent-final-68.json) covers every final regenerated result, table, macro, abstract and figure file. Thus an exact-match row is backed by values and hashes, not merely a successful exit code.

| Table | PDF page | File under `paper/tex/tables/` | Reproduction and audit result |
|---|---:|---|---|
| 1 | 7 | [rev2_catalog.tex](../memistor-ecram-training/paper/tex/tables/rev2_catalog.tex) | Exact |
| 2 | 10 | [e1.tex](../memistor-ecram-training/paper/tex/tables/e1.tex) | Exact |
| 3 | 10 | [e1b.tex](../memistor-ecram-training/paper/tex/tables/e1b.tex) | Exact |
| 4 | 14 | [rev_main_vs_fp.tex](../memistor-ecram-training/paper/tex/tables/rev_main_vs_fp.tex) | Exact |
| 5 | 15 | [rev_main_vs_adam.tex](../memistor-ecram-training/paper/tex/tables/rev_main_vs_adam.tex) | Exact |
| 6 | 17 | [rev4_probe_sur.tex](../memistor-ecram-training/paper/tex/tables/rev4_probe_sur.tex) | Exact; also rebuilt from saved pulse draws |
| 7 | 18 | [rev4_probe_seq.tex](../memistor-ecram-training/paper/tex/tables/rev4_probe_seq.tex) | Exact; also rebuilt from saved pulse draws |
| 8 | 19 | [rev4_dep.tex](../memistor-ecram-training/paper/tex/tables/rev4_dep.tex) | Exact; also rebuilt from draws; statistic definition needs clarification (finding 2) |
| 9 | 19 | [rev4_a2m.tex](../memistor-ecram-training/paper/tex/tables/rev4_a2m.tex) | Exact; five matched triples independently recalculated |
| 10 | 20 | [rev3_fid.tex](../memistor-ecram-training/paper/tex/tables/rev3_fid.tex) | Exact |
| 11 | 20 | [rev_width.tex](../memistor-ecram-training/paper/tex/tables/rev_width.tex) | Exact; fractional-df Welch gives different intervals and one verdict (finding 1) |
| 12 | 21 | [rev_spec_p.tex](../memistor-ecram-training/paper/tex/tables/rev_spec_p.tex) | Exact; final `rev_spec_p.tex` is now actually regenerated |
| 13 | 23 | [rev_energy.tex](../memistor-ecram-training/paper/tex/tables/rev_energy.tex) | Exact; corrected accounting independently verified |
| 14 | 33 | [rev2_selection.tex](../memistor-ecram-training/paper/tex/tables/rev2_selection.tex) | Exact; selection grids/scores additionally checked |
| 15 | 34 | [checks.tex](../memistor-ecram-training/paper/tex/tables/checks.tex) | Exact; corresponding simulator checks also pass |
| 16 | 35 | [laneme.tex](../memistor-ecram-training/paper/tex/tables/laneme.tex) | Exact historical values; misleading “this paper” label (finding 3) |
| 17 | 36 | [v1s_catalog.tex](../memistor-ecram-training/paper/tex/tables/v1s_catalog.tex) | Exact; explicitly superseded v1 result |
| 18 | 36 | [v1s_e2.tex](../memistor-ecram-training/paper/tex/tables/v1s_e2.tex) | Exact; explicitly superseded v1 result |
| 19 | 36 | [v1s_main.tex](../memistor-ecram-training/paper/tex/tables/v1s_main.tex) | Exact; explicitly superseded v1 result |
| 20 | 37 | [v1s_scale.tex](../memistor-ecram-training/paper/tex/tables/v1s_scale.tex) | Exact; explicitly superseded v1 result |
| 21 | 37 | [v1s_spec.tex](../memistor-ecram-training/paper/tex/tables/v1s_spec.tex) | Exact; explicitly superseded v1 result |
| 22 | 37 | [v1s_spec_rel.tex](../memistor-ecram-training/paper/tex/tables/v1s_spec_rel.tex) | Exact; explicitly superseded v1 result |
| 23 | 37 | [v1s_pairs.tex](../memistor-ecram-training/paper/tex/tables/v1s_pairs.tex) | Exact; explicitly superseded v1 result |
| 24 | 38 | [v1s_energy.tex](../memistor-ecram-training/paper/tex/tables/v1s_energy.tex) | Exact; explicitly superseded v1 result |
| 25 | 41 | [rev_d1.tex](../memistor-ecram-training/paper/tex/tables/rev_d1.tex) | Exact; reset/reference diagnostic |
| 26 | 42 | [v3s_rev2_probe.tex](../memistor-ecram-training/paper/tex/tables/v3s_rev2_probe.tex) | Exact; explicitly superseded probe analysis |

| Figure | PDF page | Files under `paper/tex/figs/` | Result |
|---|---:|---|---|
| 1 | 11 | `fig_validation.pdf`, `.png` | Regenerates; same PDF drawing content and PNG pixels |
| 2 | 13 | `fig_rev_main.pdf`, `.png` | Regenerates; same PDF drawing content and PNG pixels |
| 3 | 38 | `fig_main.pdf`, `.png` | Regenerates; negative means/intervals are now plotted correctly; legend clear |

The auxiliary `fig_energy`, `fig_oat_cifar`, `fig_oat_lm` and `fig_scale` PDF/PNG pairs also regenerate. They are repository products, not additional figures in this 42-page paper. All three PNG images embedded in `paper/build/main.html` match the corresponding source PNGs pixel for pixel: [HTML image check](html-embedded-images.json).

| Number file | Macro definitions | Expected versus regenerated |
|---|---:|---|
| `paper/tex/numbers.tex` | 569 | All exact |
| `paper/tex/numbers_rev.tex` | 1346 | All exact |
| `paper/tex/numbers_rev2.tex` | 148 | All exact |
| `paper/tex/numbers_rev3.tex` | 144 | All exact |
| `paper/tex/numbers_rev4.tex` | 24 | All exact |

There are **2,231 definitions**, including unused/historical ones, and **253 distinct macros directly referenced by current arXiv source files**. The generated arXiv abstract also matches. The 44 current numerical-macro/table source files in the submission archive are byte-identical to their repository counterparts: [archive source comparison](arxiv-numeric-source-match.json).

Hard-coded model settings, mathematical constants, cited historical numbers, dates, proposed bench settings and reference numbers are not all empirical outputs. I indexed **2,260 number-bearing extracted PDF lines** as a coverage aid ([index](paper-number-bearing-lines.json)), read all 42 pages, and traced the current experimental settings to their code/records. The [literal-number checks](literal-number-checks.json) verify the 12 draw archives / 81,905,772 bytes, task budgets and the stated Poisson limiting probability: P(Poisson(31)>31)=0.45242821941013667, which rounds to 0.4524. The bench parts script totals $38.50 all-new / $29.00 excluding household items as encoded; these are proposed parts costs, not freshly verified retail quotes. External literature numbers and historical claims were not independently regenerated from the original studies; that limitation is explicit below.

**Code and record audit: checked and found correct**

The line review covered all active computational files in `paper/sim/`: the original/repaired device models and catalogs; `pulse_seq_rev2.py`; original/revised tasks and training loops; `run_rev2.py` and `run_rev3.py` probes; all sweep/selection drivers; `stats_paper.py`; all simulator tests. It also covered the two source-derivation utilities (`derive_memsim.py`, `edit_tasks_run.py`), without executing them on original files. For analyses it covered `paper/analyze.py`, `revision/analyze_rev.py`, `revision/analyze_d1.py`, `revision2/analyze_rev2.py`, `revision3/analyze_rev3.py`, `revision4/analyze_rev4.py`, `revision4/rebuild_draw_tables.py`, the abstract generator, both figure generators and the v1.1 final-Table-12 derivation.

The energy review included `paper/energy/energy_system.py`, `energy_rev.py` and the original root `energy/energy.py`. Original-lane task/runner/model differences, `sim/verdict.py`, selection and scaling scripts were also read. Additional reads covered the reproduction/data-fetch tools, AIHWKIT comparison and curve producer, current numerical/figure/HTML checks, and every changed v1.1 code hunk. Archived copies were deduplicated against their source versions. Historical publishing/orchestration wrappers and all older review-only scripts were not each subjected to the same full line-by-line runtime audit; their exclusion is not a claim that they are portable.

- **Device/pulse arithmetic.** The implemented update signs, normalization/weight scale, symmetry-point formula, shifted bounds, bound-scaled slopes, device population spread, exponential aggregate update, square-root write-noise scaling, drift target, probability clipping and unsigned lost-mass accounting are consistent with the stated simulator. Chopper modulation/demodulation, transfer sign, residual buffer subtraction and physical reset accounting were traced. The ideal partial-column reset now uses the selected columns' own bounds. Ideal reads, digital biases/layer norms/position table, and the distinction between the aggregate approximation and literal pulses are explicitly disclosed. The stale conservatism docstrings are finding 9, not evidence that the paper still proves conservatism.
- **Random streams and pairing.** Independently checked 960 current device/control comparisons from the main, width, sensitivity and fidelity phases: initialization hash, example-order hash and GPU model match in every checked pair. Evaluation splits are test. Separately checked all five current A2-M triples; all three roles match those hashes/model, and all metrics are on test. See [pairing audit](pairing-audit.json), [A2-M calculation](a2m-independent.json). Cross-width initialization is the wording exception in finding 4; within-width comparison matching is correct.
- **Data separation and evaluation.** MNIST's 55k training / 5k validation / 10k test partition, CIFAR's stated 10k training / next 2k validation / official test partition, and training-only CIFAR normalization agree with the source. LM selection withholds the final 0.5 MB of its 8 MB training slice; final evaluation uses the separate 0.5 MB slice at the documented offset. Evaluation routines use the intended selected split, with cross-entropy converted to bits per byte by division by ln(2). The retained LM last-window defect does not cross a train/evaluation boundary. No additional current leakage was found. Historical overlapping-split and shared-RNG results remain explicitly qualified/superseded.
- **Validation selection.** All 312 inspected selection-phase records use validation. In a supplemental verification after reading review 8, all 34 saved learning-rate choices select the best saved grid score; every grid score matches its raw validation record, including divergent candidates, and none selects a grid endpoint. The three algorithm choices match raw maxima (AGAD 0.973; c-TTv2 0.976; TTv2 0.976). See [split inventory](selection-splits.json), [selection scores](selection-values-verified.json). This check did not launch selection or training runs.
- **Main statistics.** Independently recalculated 144 current main/device/ideal comparison cells against their controls using the released t-quantile convention; means, sample standard deviations, confidence bounds and labels match. Classification gaps have the correct FP-minus-device percentage-point sign; LM gaps use per-seed relative bpb excess. The main-table published-device PASS counts are 11/5/4 versus FP-SGD and 11/4/0 versus Adam for MNIST/CIFAR/LM. Four pairings pass all three against FP-SGD and none against Adam. See [independent main calculation](independent-main-statistics.json).
- **Width and sensitivity.** Independently recalculated 24 per-width cells, eight paired endpoint contrasts and 148 sensitivity points, including their labels, with exact agreement under the released convention. The eight Welch contrasts were subsequently reconstructed from raw records too, exposing finding 1's quantile discrepancy. The current sensitivity table uses absolute task-margin PASS criteria; it does not silently substitute an acceptable-degradation-from-base test. Post-hoc c-TTv2 sensitivity is identified as such. No minimum-state requirement is established when the tested range does not cross a failure boundary. See [secondary calculations](independent-secondary-statistics.json), [Welch copy verification](welch-copy-verification.json).
- **Probe analysis.** The literal and seq streams share line firings where the analysis calls them paired; the surrogate comparison is independent. Whole-draw bootstrap, paired versus independent sampling floors, gain normalization and per-pair correlation aggregation were reviewed. All 12 archived draws and hashes were checked, and Tables 6–8 were rebuilt from them twice plus the fault self-test. The hypothesized zero-sign/diagonal corner case did not occur in these archived dependence calculations. The lower-median convention differs slightly from the average-middle convention but changes none of the printed two-decimal variance ratios. See [draw reconstruction](quickstart-4-draws.log), [dependence check](dependence-sign-audit.json), [median check](median-convention-check.json). The RMS definition issue is finding 2.
- **A2-M.** Independent gaps are 8.710 pp for the surrogate and 8.734 pp for seq, with paired difference 0.024 pp and 95% interval approximately [-0.467, 0.515]. These match the paper. GPU-dependent realizations are reported descriptively; the withdrawn mixed-GPU pairing is not silently reused as a valid matched comparison.
- **Energy.** Independently recomputed 180 scenario/cell entries (60 original and 120 current), tracing pJ units, row-weighted pulse/line activity, two MVMs (four arithmetic operations per training weight-row), TT reads/reset overhead, and the digital power/throughput/utilization expression. Maximum absolute discrepancy is 2.33e-10 pJ, floating-point summation only. All 2,364 applicable row-derived step counts match the actual training-loop budgets. The repaired accounting changes unrounded energies relative to v1.0 but no printed value. The maximum relative change in total energy is 0.000481375% in the current projection and 0.001424732% in the original projection. See [energy calculations](independent-secondary-statistics.json), [changed numerical leaves](energy-tag-diff.json), [step accounting](step-accounting.json).
- **Additional original-lane outputs.** In another copy, root `energy/energy.py` and `sim/verdict.py final` regenerate `records/ENERGY.json`, `records/RESULTS.json` and `VERDICT.md` byte-identically. The current device catalog regenerated semantically identically. See [supplemental regeneration](supplemental-regeneration.json).

The result claims are generally calibrated to these checks: point-estimate probe agreement is distinguished from bootstrap uncertainty; clipped layers that fail are shown; seq is treated as a diagnostic approximation; the fixed-budget Adam comparison is retained; only one CIFAR endpoint-equivalence result is established; the LM width trend is qualified by a worsening FP baseline; and energy is explicitly a conditional projection with excluded operations and different read assumptions. The bibliography/metadata and statistical wording exceptions are itemized above.

**Tests, checks and a physically altered copy**

| Suite executed | Passing checks | Planted faults detected |
|---|---:|---:|
| paper/sim/test_ideal_reset_cols.py | 1 | 1 |
| paper/sim/test_paper.py | 5 | 7 |
| paper/sim/test_rev.py | 8 | 8 |
| paper/sim/test_rev2.py | 5 | 5 |
| paper/sim/test_rev3.py | 4 | 4 |
| sim/test_memsim.py | 9 | 10 |
| paper/sim/test_memsim.py (supplemental) | 9 | 10 |
| **Total executions** | **41** | **45** |

These include overlapping tests of original/paper simulator implementations; they are not 41 independent validations of a physical model. All suite aggregates pass. Full details and fault outputs are in [test inventory](test-inventory.json), [pipeline logs](reproduction-logs/) and the [supplemental log](test-paper-memsim.log).

I also planted a real source fault in a separate copy: replaced `self.A.clip_cols(us, idx)` with `self.A.clip(us)` in `memsim_rev.py`. The unchanged test passes the clean control (exit 0) and fails the altered copy (exit 1), reproducing the 3×4-to-3×1 assignment error. See [fault result](fault-result.json), [control](fault-control.log), [failure](fault-planted.log), and [altered copy](../fault-copy/memsim_rev.py). This is in addition to the repository's built-in mode/parameter fault tests.

Other successful checks include: CPU-only guard; corrupt-dataset detection; wrong-hash and perturbed-draw detection; matched-triple mismatch rejection; bench fitting self-test; numerical-macro freshness and its digit/missing/extra/stale-count faults; HTML section/table/reference completeness faults; leftover-macro detection; and rule-stripping tests. Relevant evidence is [numbers freshness](numbers-fresh-selftest.json), [HTML completeness](html-complete-selftest.log), [HTML leftovers](html-leftover-selftest.log), [rule tests](html-strip-rules.log). The default Figure 3 check passes; its advertised `--selftest` fails because of unavailable history (finding 6). The independent public-v1.0 negative-control harness demonstrates that the figure check can detect the actual historical faults without that private commit.

**Availability, versions, licences and privacy**

Section 9 is on PDF page 27. All **75 explicit path/layout/licence/archive checks** resolve: plans, deviations, original/repaired models, stream/probe code, analyses, records, 12 draw archives, reviews, responses, citation-check record, bench materials and root licence/data-fetch files. The archived `paper/tex/v1`–`v10` and `paper/build/v1`–`v10` directories exist. See [path inventory](availability-paths.json), [archive members](arxiv-members.json), [archived-file comparison](archived-dedup.json).

The [Zenodo v1.1 record](https://zenodo.org/records/23773334) identifies version 1.1, release DOI **10.5281/zenodo.23773334**, and concept DOI **10.5281/zenodo.23748861**. DataCite records the same version and IsVersionOf relationship. The concept DOI in Section 9, README and CITATION.cff is intentional and correct. The [GitHub v1.1 release](https://github.com/Questeria/memistor-ecram-training/releases/tag/v1.1) holds paper v11; public tag v1.0 holds paper v9, as Section 9 states. The CFF release-date discrepancy is finding 10.

The downloaded Zenodo ZIP is **103,313,523 bytes**, and its MD5 **02289e95b2e2fe8bbf358ddc0d748f4d** matches the API record. Removing its enclosing directory for comparison, **all 3,438 tracked files match GitHub byte for byte**, including the checksum manifest. Evidence: [Zenodo metadata](zenodo-v11.json), [GitHub metadata](github-release-v11.json), [DataCite metadata](datacite-v11.json), [per-file comparison](zenodo-file-comparison.json). The repository contains **3,437 files totaling 128,908,754 bytes excluding SHA256SUMS**: README's **128.9 MB** is correct.

The MIT/code and CC BY 4.0/records-draws-text-figures declarations agree across the paper, README, LICENSE, LICENSE-DATA, CFF description and .zenodo.json. Zenodo's aggregate CC BY 4.0 metadata is accompanied by the stated MIT code distinction. Datasets are not tracked in the release and retain their external terms; downloaded copies were placed only in the reproduction workspace. This verifies licence declarations and inventory, not ownership or authority to license every third-party contribution.

ENVIRONMENT.md's **2,691** torch-2.7.1+cu126 training-record count and **2,421 A4000 / 252 P2000 / 18 P2200** counts are correct. The 24 records outside the usual /runs/ trees are under the original lane's superseded records; omitting them would yield an incorrect 2,667 count. See [complete inventory](full-training-inventory.json). Python, NumPy and driver facts attributed to excluded pod logs cannot be checked against those absent logs. make_deposit.py/deposit_scan.py refer to the author's deposit-building process and are not supplied standalone tools. I checked the public output properties directly but could not rerun those builders.

The completed scan covers **3,375 tracked UTF-8 text files**, including the two initially deferred documents. It records **181 Windows-path occurrences / 79 distinct matched strings**, including placeholders and review-evidence links as well as internal paths; these are not 181 independent secrets. Additional checks covered textual members of nine tar archives, metadata of 29 PDFs, and extracted text from all **871 pages** of those PDFs. No credential-pattern hit, secret-key file or credential-assignment context was found. The public Git author uses the intentional GitHub noreply address Questeria@users.noreply.github.com.

| Kind | Examples found inside the release | Location examples |
|---|---|---|
| Internal project/dataset path | C:/Projects/Cryptum/tests/corpus/external/enwik8 | DEPOSIT-PATCHES.json:22,46,70; corresponding old-value entries in VERIFY.json |
| Other project/work context | Helios Evolution B1, HIVE, Helix, kovc | paper/PLAN-REVISION-2.md:91–93 |
| Shared coordination path | F:/shared/LIVE-HOLDS.jsonl | paper/PLAN-REVISION-2.md:93 |
| Author desk/build paths | Numerous H:/<desk folder> interpreter, dataset, draw and build paths | Older docstrings/build records; README acknowledges interpreter paths |
| Review workspace links | H:/review8 paths | Deposited review 8; provenance links, not dependencies used here |
| Host identity | Domain3 plus container host IDs | Training-record host fields |

The complete [occurrence inventory](path-and-name-occurrences.csv), [unique paths](unique-paths.csv) and [scan results](privacy-complete.json) preserve file/line locations. The name-pattern category also contains intentional public author/repository names; it is not a list of secrets. See [archive scan](privacy-archives.json), [PDF text scan](privacy-pdf-text.json), [credential-context scan](credential-context-scan.json). Finding 7 is a privacy/provenance cleanup issue, not evidence of exposed authentication credentials. Pattern scans cannot prove that arbitrary opaque text or binary data contains no secret.

**arXiv-style source compilation and visual comparison**

Portable TeX Live was installed at F:/review9/texlive, with configuration/cache trees also on F:. It used the basic scheme and the needed booktabs/placeins packages. The executable reports **pdfTeX 3.141592653-2.6-1.40.29 (TeX Live 2026)**. No system PATH change or installation on C: was needed. Evidence: [version](pdflatex-version.txt), [successful installation](texlive-install-2.log), [packages](texlive-packages.log). An initial installer attempt failed because of my profile configuration and was corrected; it was not a paper/source defect.

I validated and extracted the **76-member** paper/build/arxiv-source.tar.gz into the initially empty [arxiv-original](../arxiv-original) directory. I compiled main-arxiv.tex directly, using the bundled main-arxiv.bbl. I did not run BibTeX or Tectonic or modify the extracted source. This command ran three times:

```text
F:/review9/texlive/bin/windows/pdflatex.exe -interaction=nonstopmode -halt-on-error -file-line-error -no-shell-escape main-arxiv.tex
```

| Pass | Exit | Undefined reference warnings | Undefined citation warnings | Errors |
|---|---:|---:|---:|---:|
| 1, clean auxiliary state | 0 | 107 | 80 | 0 |
| 2 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 |

The first-pass unresolved labels/citations and rerun requests are normal initialization effects; all resolve on pass two. Final warnings are limited to shell escape being disabled for epstopdf, three h-to-ht float-placement adjustments and eight underfull hboxes. There are **no overfull boxes, missing-character warnings, remaining undefined references/citations or compilation errors**. See [warning inventory](latex-warning-inventory.json), [pass 1](pdflatex-pass1.log), [pass 2](pdflatex-pass2.log), [pass 3](pdflatex-pass3.log).

The resulting [pdfLaTeX PDF](../arxiv-original/main-arxiv.pdf) has **42 pages** and **616,542 bytes**, versus the supplied Tectonic PDF's 42 pages and 305,334 bytes. Whole-file byte equality is not expected across engines/fonts/compression. All 42 pages were rendered and visually inspected side by side, including equations, every table and figure, bibliography and appendices. The fourteen paired contact sheets are in [visual/](visual/). Numeric tokens agree on **42/42 pages**; normalized text agrees on **41/42 pages**. The only text difference is page 28's Jacobs-Gedrim hyphen (finding 11), confirmed in enlarged crops. Minor line spacing/reflow within that bibliography entry accompanies it. I found no changed equation/table value, missing figure, clipping or legend overlap in the final compilation. Evidence: [page comparison](pdflatex-content-comparison.json), [Tectonic crop](visual/surname-tectonic.png), [pdfLaTeX crop](visual/surname-pdflatex.png).

This is a successful local build with TeX Live/pdfLaTeX and the bundled bibliography, not a submission to arXiv or a test of its exact server image. TeX Live 2026 was the installed distribution; I did not claim byte-for-byte replication of arXiv's pinned package set.

**Review 8 and the authors' response — read only after steps 1–4**

I read [the deposited review](../memistor-ecram-training/paper/reviews/REVIEW-8-chatgpt-20261028-full.md) and [the response](../memistor-ecram-training/paper/RESPONSE-TO-REVIEW-8.md) after freezing the independent work. I did not follow their links into H: or other private locations. The assessments below use this review's fresh clone, run logs, calculations and rendered PDFs.

| Review-8 finding | Status in v1.1 / v11 | Confirmation and qualification |
|---|---|---|
| 1. Figure 3 clamps negative means to +0.05 | **Fixed** | Current plotting arguments use all 60 true means and intervals. The public-v1.0 negative control reproduces the two misdrawn LM means; current check passes. Figure 3 was visually checked. |
| 2. Skipped batches inflate transfer energy | **Energy consumer fixed; historical field retained and disclosed** | Step count now comes from layer rows. Independent calculations confirm current energies, including MNIST Li-ECRAM/AGAD chip total 0.32510964862248964 pJ. Printed tables/macros match. The samples field remains wrong as stated; K2 enumerates it. |
| 3. Partial-column ideal reset crashes | **Fixed** | Selected-bound clipping passes. Restoring the old operation in a separate copy causes the exact broadcast mismatch. The test is in the full pipeline. |
| 4. LM omits last valid training window | **Disclosed, intentionally not corrected** | Source retains the exclusive-bound error; PDF p7 section 3.5 and README explain it and why the recorded code is preserved. No held-out byte is involved. See K1. |
| 5. Quick start leaves shell in paper/ | **Fixed** | The written cd paper / draw check / cd .. sequence works. The new .venv/checksum interaction is separate finding 5. |
| 6. Final Table 12 file not regenerated | **Fixed** | derive_rev_spec_p.py runs after analyze_rev.py; rev_spec_p.tex appears in the rewritten-file comparison and matches. All 26 final tables are covered. |
| 7. No copyable installation recipe | **Fixed in tested environment** | CPU torch and requirements commands succeed on Python 3.13.15. The old minimum-version claim remains misleading (finding 8); install/checksum sequencing has finding 5. |
| 8. Stale README size total | **Fixed** | The independent sum is 128,908,754 bytes / 3,437 files excluding SHA256SUMS, correctly displayed as 128.9 MB. |
| 9. Figure 3 legend overlaps axis label | **Fixed** | Current check reports no overlap; public historical negative control detects 11. Regenerated/compiled figure is clear. Private-history dependency of the optional self-test is separate finding 6. |

The response's substantive fixed/disclosed status for all nine findings is supported. Its recorded desk self-test success is not directly portable to this public history; the fresh failure is reported separately from the successful figure repair. Energy records change at unrounded precision between tags; unchanged numerical macros/tables support the statement that printed scientific-result values did not change. Figure 3's misplaced values and layout change visually, as stated. The Welch finding predates my reading of the response and is not addressed by those nine repairs.

**What could not be checked, and why**

- **Every training trajectory from raw data.** The documented reproduction starts from saved records/draws and does not rerun the full GPU experiments. This review did not repeat thousands of training runs. CPU tests exercise small cases, not the complete campaign. Same-seed runs on another GPU model would be different random realizations, as disclosed.
- **A fresh external AIHWKIT reference run.** Deposited curves and the comparison calculation were checked, and mapping formulas audited; AIHWKIT itself was not independently installed and rerun. Agreement with stored reference curves is not an independent device measurement.
- **Original external papers and physical assumptions.** I did not remeasure devices, replicate cited studies, revalidate every historical number, or establish that borrowed inference-chip efficiency applies to ECRAM training. The citation-check record is present and internally consistent, but its author's prior network checks are not a fresh verification of all references. Exact authorship of every byte of the 2006 Wikipedia snapshot was not established; dataset identity and offsets were.
- **Private chronology and completeness beyond the public record.** Public history has two release commits, not the author's full preregistration/run history. It cannot establish every claimed plan-before-experiment date, absence of unreported attempts, or properties supported only by excluded pod logs. Current result cells have their required records; this does not prove an exhaustive history of every attempted run.
- **Private redaction originals and rights provenance.** Those originals and some builder scripts are absent by design. I examined released text, hashes, metadata and licence declarations, but could not reconstruct every private redaction or establish all upstream rights.
- **Every historical desktop wrapper and publishing script.** Many require private Git objects/build trees or account context. I did not use those private paths or launch cloud jobs. Current public reproduction, portable checks and the extracted source build were exercised instead.
- **A fresh full HTML build and browser responsiveness.** Deposited HTML passed structural/fault checks and image equivalence. I did not install/run pandoc to rebuild it or test responsive browser layout. The requested arXiv source build was completed separately.
- **Actual arXiv server acceptance, hardware performance and generalization.** No upload was made. This audit does not establish physical feasibility, measured wall-plug energy, time to a common quality target, convergence on stronger models, or robustness beyond the disclosed seeds/models. The paper generally states these limits appropriately.

**Before submission**

Resolve the Welch convention/result discrepancy in finding 1, explicitly define the dependence statistic in finding 2, and label Table 16's historical lane accurately. The remaining issues are bounded documentation, portability, privacy and bibliography corrections. Preserve original run records and disclosed defects when preparing corrections. This report's altered-code experiments are confined to copies; the original repository and supplied PDF remain unchanged.
