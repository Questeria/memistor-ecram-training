# Response to the twelfth independent review (ChatGPT, 2026-10-31), version 15 of the paper and archive v1.5

The review (`reviews/REVIEW-12-chatgpt-20261031-full.md`, pasted by the owner) audits release v1.4 (commit 39c6ed7fe) and version 14.
Beyond reading the text, the reviewer checked the release's checksums (3,608 listed files), recomputed the main comparisons (165),
the width study, the sensitivity analysis and the energy output from the records, and ran the fast reproduction path under
Python 3.12.14, PyTorch 2.7.1+cpu, NumPy 2.5.2 and Matplotlib 3.9.2. It did not repeat the training, the five slow simulator test
groups or any physical validation. It recommends minor revision, finds no result-changing error, and asks for three limited
corrections (A, B, C) and two optional numerical cleanups.

Every finding was verified against version 14 (commit 3cbefba20, `tex/v14`), release v1.4, the records and the code before anything
changed: `revision14/verify_findings_12.py` writes `records/revision14/VERIFY-FINDINGS-12.json`. No experiment was run, no pod was
used and no result changed. Cost: $0 (desk, WSL).

## The reviewer's checks

All agree with version 14: the PASS counts against FP-SGD (14, 6, 4 of 20) and Adam (14, 4, 0 of 20); the best LM cell against Adam,
23.36 % [22.15, 24.58]; the width growth of protonic-inspired c-TTv2 on CIFAR, 1.76 pp with paired 90 % interval [0.15, 3.38]
(the reviewer's 1.762 [0.146, 3.378]); the GPU energy 10.48 pJ, 7.05-11.17 pJ and 5.51-14.15 pJ; and the 60-row energy output,
which the reviewer reproduced byte for byte.

## Findings

| # | Finding | Verdict | Evidence | Change (version 15, archive v1.5) |
|---|---|---|---|---|
| A | `reproduce_all.py --fast` ends REPRODUCE_FAILED under Python 3.12.14 / torch 2.7.1+cpu / NumPy 2.5.2: `paper/records/revision/AIHWKIT-COMPARE.json` differs in 26 float fields (largest 5.69e-6 weight units, 4.70e-4 tolerance units); every acceptance boolean and every printed value unchanged | **Confirmed** | Reproduced on the desk under WSL Ubuntu with Python 3.12.3, torch 2.7.1+cpu, NumPy 2.5.2 (Intel Xeon W-2123): `revision/compare_curves.py` of v1.4 on unchanged inputs gives the same 26 differing fields, nothing else different (largest change 4.26e-6 in weight units, 3.85e-4 in tolerance units, 5.2e-6 in the spread ratio); every boolean, string and integer equal; the printed 0.0111, 0.0113, 0.174, 0.173 and "accepted" equal; the largest accepted discrepancy 0.642 of the line 1.0 (`records/revision14/AIHWKIT-COMPARE-py312.json`). The file re-simulates up to 56,000 float32 pulses per device on the CPU, so its rounding depends on the CPU kernels torch dispatches to. The reference environment (`records/deposit/VERIFY.json` of v1.4) is Python 3.13.15 on Windows 11, torch 2.7.1+cu126 with CUDA hidden, NumPy 2.5.2, matplotlib 3.9.2, Pillow 13.0.0. | `reproduce_all.py` compares this one file under a stated numeric policy (`NUMERIC_POLICY`): the same JSON structure, keys and value types; every string, integer and boolean exactly equal; every float not named exactly equal (the AIHWKIT side of the extremes); weight-unit fields within 5e-5, tolerance units within 5e-3 and the spread ratio within 1e-4; the values the paper prints from the file identical. Justification: each tolerance is about ten times the largest change seen in the two Python 3.12 runs and at most a tenth of the margin it could erode (5e-5 is a tenth of the smallest floor of the comparison's own tolerance, 2 dw_min = 5.6e-4 for MO-ECRAM; 5e-3 is half a percent of the line 1.0, which the largest accepted value misses by 0.358; every stored spread ratio is at least 0.067 from the edges of [0.8, 1.25]). Such a file is reported as `within_policy`, with its count of differing floats and the largest change per field. Mutation tests: `reproduce_all.py --policy-selftest` (a new step of the run) shows the 3.12 output and a small in-tolerance change passing, and a flipped acceptance boolean, a flipped `mapping_accepted`, a discrepancy pushed past its line (0.642 -> 1.05 with `ok` left true), a renamed key, a removed key, a change inside the weight tolerance that changes a printed value (0.0111 -> 0.0112), an exact-only float, the AIHWKIT version string, an integer turned float, a spread ratio moved by 1e-3 and a truncated file each failing; the clean room adds two deposit-level mutations (the boolean flipped, the discrepancy past its line, each in the deposit's copy) that `reproduce_all.py` must reject. The archive README gains a section "Reference environment": byte identity of every file is guaranteed only there; elsewhere the policy applies to this file and every other file must still match. |
| B | Figure 1's shared Tiki-Taka panel gives A a pulse reset and the input c (.) x for all three algorithms; AGAD has no reset and TTv2 no chopper; the figure check builds AGAD with `tt_reset="pulse"` | **Confirmed** | All 90 main-experiment device records of each algorithm: TTv2 and c-TTv2 `tt_reset` "pulse", AGAD "none"; `CHOICES-REVISION.json` and Table 14 (`tables/rev2_selection.tex`) agree. Version 14's `revision13/make_fig_arch.py` draws one A box labelled "pulse reset <= 62/weight" and the input c (.) x for TTv2, c-TTv2 and AGAD; its caption says "as run here". `revision13/check_fig_arch.py` builds every TT layer with `tt_reset="pulse"` and reads no selected configuration, so it could not see the difference. | Figure 1 (`revision14/make_fig_arch.py`) takes a per-algorithm table `SETTINGS` (reset, chopper) from which the A box ("pulse reset <= 62/weight (not AGAD)"), the input box ("c = 1 in TTv2") and a key "Selected settings: TTv2: pulse reset of A; c = 1 (no chopper) / c-TTv2: pulse reset of A; chopper signs c / AGAD: no reset of A; chopper signs c" are derived. The caption adds the reviewer's sentence in the paper's words: "In the selected configurations (Table 14) TTv2 and c-TTv2 reset A with pulses and AGAD does not reset it; in the common notation c (.) x, c = 1 for TTv2, and c-TTv2 and AGAD use chopper signs." `revision14/check_fig_arch.py` checks `SETTINGS` against `CHOICES-REVISION.json` and every main-experiment device record (and tt_gamma = 0), checks that the drawn labels are the ones derived from `SETTINGS`, and builds each simulated layer with the update configuration of that algorithm's first main-experiment record (only the learning rate raised, so that a 12 x 6 layer moves in six steps): there TTv2 and c-TTv2 reset A (36 weights, 730 and 711 pulses) and AGAD does not (0), and the chopper signs exist exactly for c-TTv2 and AGAD. Eight planted faults are caught (`records/revision14/FIG-ARCH-CHECK.json`): version 14's four, AGAD drawn with the pulse reset, TTv2 drawn with a chopper, the simulator run in version 14's synthetic configuration, and version 14's A label put back. |
| C | After the Byun insertion, "Agarwal et al. reached similar conclusions" follows the TTv1/TTv2 comparison and could attribute it to a 2016 paper | **Confirmed** | `tex/v14/sec_background.tex`: Gokmen and Vlasov (plain SGD), then Byun et al. (TTv1, TTv2), then "Agarwal et al.~\cite{agarwal2016} reached similar conclusions; the requirements were extended to convolutional networks". Agarwal et al. 2016 (IJCNN, "Resistive memory device requirements for a neural algorithm accelerator") predates Tiki-Taka. | Section 2.2 now reads: Gokmen and Vlasov; "Agarwal et al. [..] reached similar conclusions for conventional (SGD) training, and the requirements were extended to convolutional networks [..]." Then Byun et al.; then "Reviews cover the device landscape". "Similar conclusions" no longer follows any algorithm comparison. |
| D1 | (optional) Reset re-reads are charged an ADC conversion and an H-buffer update but do not update H; at most about 0.15 % | **Confirmed** | `energy/energy_rev.py` adds the pulse reset's extra column reads to `reads_pwr`; `energy/energy_system.py` prices every counted read as `adc + sram_add`. Their buffer allowance is at most 0.1497 % of the analog energy (MNIST, Li-ECRAM c-TTv2, 12.4 TOPS/W). Separating the two read categories would print 31.6 for 31.5 (lowest chip ratio), 97.2 for 97.0 and 98.4 for 98.3 (lowest read shares) and 41.9 for 42.2 (the TOPS/W needed for 100x). | **Labelled, not separated** (judgement call below). Section 5, item 3 adds: "The pulse reset's extra column reads are priced the same way although they do not update H, a conservative approximation: the buffer allowance stands for the arithmetic that turns each re-read into a correction pulse count, and without it the analog energy would be at most 0.15 % lower." No number changes. |
| D2 | (optional) Ordinary and paired intervals use three-decimal t constants; the Welch interval uses `t_quantile`; no classification changes | **Confirmed** | `revision/analyze_rev.py`: `ci()` and `width_paired()` read `tq()`'s three-decimal tables (largest error 4.7e-4 against the exact quantile, df 1-30); `width_verdict()` uses `t_quantile` since version 12. | `ci()` and `width_paired()` take `t_quantile(0.975 or 0.95, n - 1)`; the tables stay for the tests of earlier versions. Regenerated: 16 interval endpoints in Tables 4 and 5 move by 0.01 (listed below); no PASS/FAIL/UNRESOLVED label, mean, verdict or other printed number changes (every string of `RESULTS-REVISION.json`, `RESULTS-REV2/3/4.json` equal; the largest float change 0.013 in an unprinted digit); Section 3 says "the t quantile computed exactly". |

### Every printed number that changed (D2; version 14 -> version 15)

Each endpoint moves by 0.01 because the exact quantile (for df = 4: 2.776445 instead of 2.776) widens or narrows the interval in its
last printed digit; the mean and the label of each cell are unchanged, and no endpoint crosses a line (the lines are 2 pp for MNIST and
CIFAR and 5 % for the LM; the closest moved endpoint is 2.34 for an UNRESOLVED cell whose lower end, 0.87, stays below 2).

| Table | Cell (device, algorithm, task) | v14 | v15 | Label |
|---|---|---|---|---|
| 4 (vs FP-SGD) | Li-ECRAM, SGD, LM | [31.64, 71.63] | [31.63, 71.64] | F |
| 4 | MO-ECRAM, SGD, LM | [7.33, 140.35] | [7.32, 140.36] | F |
| 4 | MO-ECRAM, TTv2, LM | [15.06, 23.57] | [15.05, 23.57] | F |
| 4 | W/WOx ECRAM, TTv2, LM | [18.93, 26.04] | [18.92, 26.04] | F |
| 4 | Memistor (optimistic), SGD, MNIST | [0.87, 2.33] | [0.87, 2.34] | U |
| 4 | Memistor (optimistic), TTv2, CIFAR | [0.26, 2.52] | [0.26, 2.53] | U |
| 5 (vs Adam) | Li-ECRAM, SGD, LM | [60.59, 120.07] | [60.59, 120.08] | F |
| 5 | MO-ECRAM, SGD, MNIST | [4.73, 18.23] | [4.73, 18.24] | F |
| 5 | MO-ECRAM, SGD, LM | [35.42, 199.87] | [35.41, 199.88] | F |
| 5 | MO-ECRAM, c-TTv2, CIFAR | [0.28, 2.53] | [0.27, 2.53] | U |
| 5 | MO-ECRAM, AGAD, LM | [31.48, 39.19] | [31.47, 39.19] | F |
| 5 | Ideal 1000-level, TTv2, CIFAR | [0.66, 10.91] | [0.66, 10.92] | U |
| 5 | Ideal 1000-level, c-TTv2, CIFAR | [10.33, 27.87] | [10.33, 27.88] | F |

Two number macros that the paper does not print (the digital TT arms' upper ends, `\RVCifarDigitalAgadVsAdamHi` 39.28 -> 39.29 and
`\RVLmDigitalTtvTwoVsFpHi` 56.77 -> 56.78) also moved. Nothing else printed changed, other than the text edits above and the date
(November 2026).

## Judgement calls

- **D1: labelled, not separated.** The re-read is followed by digital arithmetic per weight (rounding the read into a signed pulse
  count and limiting it by the remaining budget), which the model does not price otherwise; the buffer allowance is a fair stand-in
  for it, not only an overcharge. The effect is at most 0.15 %, far inside the input ranges of the same term (ADC 0.2-5 pJ, buffer
  0.2-3 pJ) and in the conservative direction (it lowers the ratio). Labelling keeps the energy output that the reviewer reproduced
  byte for byte, and changes no printed number; separating would have moved four (listed above) without changing a conclusion.
- **D2: only the revised analysis.** `revision/analyze_rev.py` (ordinary and paired intervals) now uses the exact quantile everywhere.
  Version 1's superseded analysis (`sim/stats_paper.py`, printed in the appendix as version 1 printed it) and `revision/analyze_d1.py`
  (six-decimal constants, exact to 1e-6) are left as they are. No deviation entry is added: the plans specify a Student-t interval,
  which the exact quantile computes more precisely; the change is recorded in Section 3 and Appendix F.
- **The tolerances of the policy (A)** are absolute and per field, not relative, so a field near zero cannot hide a large relative
  change, and they are set from the two observed environments with tenfold headroom. Any change that could move a conclusion is
  caught by the exact rules (booleans, printed values) regardless of the tolerances.
- **The figure check (B)** uses one record's full update configuration per algorithm; only the learning rate is raised (0.2), as in
  version 14's check, so that the tiny layer moves within six steps. The reset and chopper behaviour do not depend on it.
- **The caption sentence (B)** follows the reviewer's suggestion; the figure also carries a key, so the settings are visible without
  the caption.
- **The date.** `\date` reads November 2026 (version 15 is of November 1); version 14 kept October.
- **Not changed:** the contribution statement still says that ChatGPT reviewed versions 1 to 7 (the owner's wording of version 8);
  reviews 8 to 12 are also by ChatGPT. The concept DOI 10.5281/zenodo.23748861 is unchanged.

## What changed (version 15)

- Text: `revision14/edit_15.py` (every anchor matched exactly once; the Agarwal sentence moves as one string). Version 14 is archived by
  `revision14/archive_v14.py` (`tex/v14`, from commit 3cbefba20; `build/v14`, checked byte for byte).
- Analysis: `revision/analyze_rev.py` (exact t quantile); regenerated `tex/numbers_rev.tex`, `tex/tables/rev_main_vs_fp.tex`,
  `rev_main_vs_adam.tex`, `records/revision/RESULTS-REVISION.json`, `records/revision2..4/RESULTS-REV*.json` and Figure 3
  (`fig_rev_main`, whose interval ends move by at most 0.013).
- Figure 1: `revision14/make_fig_arch.py`, checked by `revision14/check_fig_arch.py`.
- Reproduction: `deposit-src/reproduce_all.py` (numeric policy, `--policy-selftest` step, Figure 1's steps now in `revision14/`, the
  reference environment in the docstring); `make_deposit.py` (v1.5 texts, the README section "Reference environment", the policy's
  status in the derived table); `deposit_cleanroom.py` (mutations M5 and M6; the policy's files in `VERIFY.json`).
- Build: `pod/build_payload_rev10.py` and `pod/build_rev10.sh` (derived by `pod/derive_build_rev10.py`; Figure 1 from `revision14/`),
  run in WSL Ubuntu with tectonic 0.15.0 (`records/revision14/BUILD-STEPS-v15.txt`). Both variants have 44 pages, as version 14; no
  undefined reference or citation; the arXiv archive compiles alone; the HTML is complete and clean.
- Availability: archive v1.5, release v1.5, twelve reviews, `RESPONSE-TO-REVIEW-12.md`, Figure 1's scripts in `revision14/`. History:
  version 14 is no longer "this paper"; version 15 is described.

## Checks

- **Text** (`revision14/pdf_text_diff_v15.py`, version 14 -> 15, the word-count method of versions 13 and 14, reference numbers as [#]):
  30 expected edits (`revision14/expected_v15.py`: the date, the Agarwal sentence, Figure 1's labels, key and caption, the exact
  quantile, the 16 endpoints in 13 entries, the reset-read sentence, the availability section and the history), 0 unexplained word
  changes, 0 edits not seen, in both variants; 44 pages both. The same check on version 13 against version 15 fails, as it must.
- **Name** (`revision9/name_check_v10.py`): NAME_OK in WSL and in Windows.
- **Numbers** (`revision8/check_numbers_fresh.py --selftest`): every `tex/numbers*.tex` is fresh.
- **Figures:** Figure 1 (`revision14/check_fig_arch.py --selftest`, 8 of 8 faults caught) and version 1's Figure 4
  (`check_fig_main.py --selftest`).
- **Reset and Welch** tests pass (`sim/test_ideal_reset_cols.py`, `revision11/test_welch_df.py`).
- **Every earlier check:** `revision14/check_build_v15.py` (derived by `revision14/derive_check_v15.py`) runs `revision6/check_build_v7.py`
  and reads the records above: `records/revision14/ARTIFACT-CHECK-v15.json`, ALL_OK.

## Archive v1.5

Release v1.5 holds version 15 and every change above. `make_deposit.py` builds it and `deposit_cleanroom.py` reproduces it in a clean
room in the reference environment, with the mutation tests (six, two of them new); `reproduce_all.py --fast` of v1.5 was also run under
Python 3.12.3 with torch 2.7.1+cpu, where the policy applies. The results are in `records/deposit/` and in the paper folder's README,
section "Revision v15". The archive README's "Changes since v1.4" and "Reference environment" sections and `RELEASE-NOTES.md` list
the changes.
