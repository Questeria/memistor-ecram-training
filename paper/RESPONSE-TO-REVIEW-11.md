# Response to the eleventh independent review (ChatGPT, 2026-10-31), version 14 of the paper

The review (`reviews/REVIEW-11-chatgpt-20261031-full.md`, pasted by the owner) is a reader's review of version 13 (`build/v13/main.pdf`,
43 pages, the owner's author variant). The reviewer read the manuscript, checked selected calculations and compared related work; it
did not rerun the experiments or audit the archive. It calls the paper "a technically serious, transparent simulation study" whose
novelty is incremental, and recommends developing it as a focused simulation and methodology paper.

Every finding was verified against the version-13 sources (`tex/v13/`), the records and the code, and the two citations against
their primary metadata, before anything changed. The verification is `revision13/verify_findings_11.py`
(`records/revision13/VERIFY-FINDINGS-11.json`) and `revision13/cite_check_v14.py` (`records/revision13/CITE-CHECK-v14.json`).
No experiment was run, no pod was used and no result changed. Cost: $0 (desk and WSL).

## The reviewer's spot checks

All agree with the version-13 macros: PASS counts against FP-SGD 14, 6, 4 and against Adam 14, 4, 0; Table 9's paired change 0.02 pp
[-0.47, 0.52] (the reviewer's 0.024 [-0.467, 0.515] rounds to it); the best LM cell against Adam 23.36 % [22.15, 24.58]; the asymmetry
confound 42.92 -> 6.20 pp; the width growth 1.76 pp [0.15, 3.38]; MNIST FP-SGD 97.77 %; plain SGD fails 12 of 12.

## Findings

| # | Finding | Verdict | Evidence | Change (version 14, archive v1.4) |
|---|---|---|---|---|
| 1 | Byun et al. (Adv. Intell. Syst., doi 10.1002/aisy.202400543) is a close predecessor missing from the bibliography (Section 6 of the review) | **Confirmed** | Crossref: Byun, Kim, Kim, Lee, Ji, Kim, "Device Specifications for Neural Network Training with Analog Resistive Cross-Point Arrays Using Tiki-Taka Algorithms", Advanced Intelligent Systems 7(5), article 2400543; online 2024-09-24, issue May 2025. Its abstract (Crossref's copy; the Wiley page answered 403) analyses device prerequisites for TTv1 and TTv2 with plain SGD as the reference, by multiparameter simulation of asymmetry, retention, number of pulses and cycle-to-cycle variation, with pattern-recognition accuracy as the metric; TTv2 permits more lenient specifications than TTv1. The abstract names neither chopped TTv2 nor AGAD nor ECRAM. Version 13 did not cite it. The full text was not read, so the reviewer's "device-requirements table" is not confirmed or denied. | Cited in Section 1 (with what this study adds: c-TTv2 and AGAD, a catalog of published electrochemical devices, seed-paired intervals against absolute margins, a language model beside the image tasks, the test against explicit pulse streams; its own sensitivity analysis is narrower) and in Section 2.2 (what Byun et al. found). Added to `cite/cite_check.py`; `records/CITE-CHECK.json` 49 of 49. Only claims the abstract supports are made about it. |
| 2 | Xu et al. protonic variability (PubMed 42915660) as a basis for a better-grounded model (Section 7) | **Partly**: already cited | PubMed esummary and efetch: the record's DOI is 10.1021/acsnano.6c09861, which is the paper's existing reference `xu2026` (ACS Nano 20(39), 26566-26579, cited since version 2 in Sections 2.4 and 6.1). Its abstract gives the 3 % cycle-to-cycle and 21 % device-to-device variability the paper prints. | Stage 1 of the roadmap now names it as a starting point for a fit, once its definitions are reconciled with this model's c2c and sigma_d2d. The confirmation is in `CITE-CHECK-v14.json`. |
| 3 | The GPU range 7.05-11.17 pJ "over 38-43 % utilisation" cannot be reproduced from 989 TFLOP/s and 700 W; 7.05 pJ matches 500 W at 43 % (Section 5) | **Confirmed** | `energy/energy_system.py`: E = 6 P / (F u), F = 989.5e12 FLOP/s (dense BF16), P = 700 W central with a 500-700 W range (labelled an estimate of sustained draw), u = 40.5 % central, 38-43 %. `energy/energy_rev.py` takes the low end at 500 W and 43 % (7.051 pJ) and the high end at 700 W and 38 % (11.170 pJ); at 700 W alone the range would be 9.871-11.170 pJ. Version 13 printed neither the power range nor the equation. The calculation is right; the prose omitted an input. | Section 5, item 4 prints the equation and every input with its range and source: 6 FLOP per weight per row, F = 989.5 TFLOP/s (half the 1979 sparsity figure), P from 500 W (our estimate) to 700 W (rated maximum), u from 38 to 43 %; the central 10.48 pJ (700 W, 40.5 %), the range 7.05 pJ (500 W, 43 %) to 11.17 pJ (700 W, 38 %), and the planned 30-55 % range 5.51-14.15 pJ. No number changed. |
| 4 | "Digital buffer" (inside the ratio) and "digital TT state" (outside) need an explicit boundary (Section 5) | **Confirmed** (wording) | The model's TT term is `reads_pwr * (adc_j_per_conversion + sram_add_j)`: one ADC conversion and one read-add-write of H per read weight. The storage of H, AGAD's averages p and p_ref and their arithmetic, the chopper signs, the threshold tests and the transfer scheduling are not in the model. Version 13 used both phrases without saying which is which. | Section 5, item 3 says what the TT family's update cost includes and names everything else "the digital TT state", outside the ratio; the closing sentence of the section uses the term so defined. |
| 5 | The ratio is set by the borrowed read efficiency (reads alone give 32.5x and 18.2x); energy per operation is not energy to a quality (Section 5) | **Confirmed** (arithmetic); **partly** already stated | Reads alone: 4 operations per weight per row at 12.4 or 6.94 TOPS/W are 0.3226 or 0.5764 pJ, i.e. 32.49x or 18.18x against 10.48 pJ, against the printed 31.5-32.4x and 17.9-18.1x. The read share is at least 97.0 % of the analog energy for every published device (minimum 0.9702 in the records). Version 13 already said the ratio is "set almost entirely by the two borrowed efficiencies", "a low energy per operation is worth nothing without the accuracy" and that no energy-to-target trajectory is shown, but not plainly what the ratio itself is. | One sentence after the read share: the ratio is a conditional, read-dominated figure per operation (one forward read, one backward read and one update per weight per row), not the energy to train a model to a given quality. |
| 6 | The "device specification sheet" is exploratory; one-variable ranges do not bound joint deviations; three seeds (Section 4.4 of the review) | **Confirmed** for the subtitle; the body was already mostly right | The subtitle promised "a device specification sheet". The body already said "sensitivity sheet" (abstract, introduction, limitations), "exploratory, not fabrication tolerances" and "combined deviations ... are not covered"; the TTv2 sheet establishes no threshold and the LM none. | Subtitle: "with an exploratory device sensitivity analysis and an experimental roadmap" (only that phrase changed; judgement call below). The abstract, the introduction's item 4, Section 4.5's heading and its "How to read" paragraph, the limitations and Appendix B say "exploratory (device) sensitivity analysis". Section 4.5 adds: a range established for one property does not bound joint deviations; passing with asymmetry alone and with reference error alone does not show passing with both. |
| 7 | An analog/digital architecture diagram (Section 7, item 5) | **Confirmed** | Version 13 had three figures, none of this kind. | New Figure 1 (Section 3.3, `revision13/make_fig_arch.py`): for SGD and for TTv2, c-TTv2 and AGAD, which arrays are device tiles, which reads are ideal fp32, which state is digital (biases and other network operations, the pulse probabilities, H, the chopper signs, AGAD's p and p_ref) and which arrays receive pulses. `revision13/check_fig_arch.py` checks the figure against the simulator itself (`sim/memsim_rev.py`): the device/digital class of every state, that the forward output equals the ideal fp32 product, and which tiles are pulsed; four planted faults are caught (`records/revision13/FIG-ARCH-CHECK.json`). It is a step of the archive's `reproduce_all.py`, beside the figure itself. |
| 8 | Algorithm and device effects are not separated; a control ladder (Section 4.3 of the review) | **Confirmed** | Version 13 said the ideal-device row "is not an exact-update, algorithm-only TT reference", but gave no ladder. | Limitations, new item "Controls": the ladder (exact digital SGD; a digital TT with an explicit accumulator decay; finite pulses and levels on ideal devices; the device imperfections; shared-line streams) and which rungs were run. The roadmap lists it as follow-up 3. |
| 9 | Clipping removes up to 57.5 % (layer mean) and 96.4 % (worst record) of the requested update; compare pulse lengths and update management (Section 4.2) | **Confirmed** | `\RVLostCifarTtLayerMeanMaxPct` = 57.5, `\RVLostMaxPct` = 96.4. Version 13 calls clipping the chosen update-management policy (Section 4.2) but proposed no comparison. | Roadmap follow-up 2: compare pulse lengths and update-management policies where the update clips. |
| 10 | The aggregate update is validated only partly; full CIFAR and LM trajectories with correlated streams are the highest-value next experiment (Section 4.1) | **Confirmed**; the limits were already stated | 10 of 12 probes meet the lines (point estimates), 1 with bootstrap bounds; A2 covers MNIST and CIFAR's dense layers; the LM only at update level (Section 4.3 and the limitations already say so). The roadmap did not name the follow-up. | New roadmap paragraph "Computational follow-ups (no hardware)", item 1: train the passing configurations over full CIFAR and LM trajectories with correlated, shared-line streams on every analog layer. |
| 11 | Analog SGD reuses the digital SGD rate and is not separately tuned (Section 2C) | **Confirmed**; already stated | Section 4.2 ("a restricted question ... not a fair-tuning comparison") and Section 6 ("not about SGD after fair tuning"). | Roadmap follow-up 4: tune each analog arm, plain SGD included, with a search budget comparable to the digital baselines'. |
| 12 | Shorten the main narrative: the correction history competes with the scientific story (Section 7, item 4) | **Partly** | Correction history in the main text of version 13: Section 3.1 (the original preset copy), 3.3 (the original reset), 3.5 ("found by review 8"), 4.3 (version 3's unpaired floor and pooled statistic, the probe runs' realisations, the pod's realisations, version 4's withdrawn figures), 4.4 (the withdrawn FLAT label, the rounded Welch df), 4.5 (version 2's anchor). Most of it was already in Appendix F or E. Results were not rewritten. | Moved to Appendix F word for word, where Appendix F did not already hold it (version 3's pooled statistic; the probe runs' realisations; the pod's realisations; version 2's anchor), and removed from the main text where Appendix E or F already held it (the preset copy, the original reset, version 3's floor, version 4's withdrawn figures, FLAT, the rounded df, "found by review 8"), each with a pointer to Appendix F. The text diff proves each moved passage moved unchanged. |
| 13 | Scaling is not established; more seeds would help; the energy claim is conditional (Sections 4.5, 4.6, 5) | **Confirmed**; already stated | Version 13 says width dependence is unresolved, makes no multiplicity correction, and calls the energy a conditional projection reported only for passing cells. | None beyond rows 3-5 and 10. |
| 14 | The title could emphasise the distinctive contribution (Section 7) | Judgement | | Only the subtitle's "device specification sheet" changed (row 6); the title is otherwise unchanged, as instructed. |

## Judgement calls

- **The subtitle.** "with a device specification sheet and an experimental roadmap" became "with an exploratory device sensitivity
  analysis and an experimental roadmap". It was the only place that promised a specification sheet. The main title is unchanged.
- **What moved.** Only correction history moved; every result, table and number stayed where it was. Where Appendix E or F already
  told the history, the main-text copy was removed rather than duplicated; where it did not, the passage moved word for word. The
  pointers left in the main text are short ("Appendix F").
- **Byun et al.** Only what Crossref's metadata and abstract support is said about it. The introduction lists what this study covers
  without claiming that Byun et al. lack anything beyond what their abstract shows (it names TTv1 and TTv2 only).
- **Pages.** Version 14 has 44 pages against 43 (both variants): the new figure and the added text outweigh the moved history. To keep
  that to one page the figure was drawn compact, its caption kept short, and version 1's superseded Figure 4 may now float to the foot
  of a page (`[!htb]`), which removed a float page.
- **Not changed:** the contribution statement still says ChatGPT reviewed versions 1 to 7 (reviews 8 to 11 are by ChatGPT, in Codex for
  8 to 10); that sentence was ordered by the owner in version 8 and the review did not raise it. Flagged for the owner.

## What changed (version 14)

- Text: `revision13/edit_14.py` (every anchor matched exactly once; moved passages are one string removed and inserted). Version 13
  is archived by `revision13/archive_v13.py` (`tex/v13`, from commit 75616d335; `build/v13`, checked byte for byte).
- Citation: `revision13/cite_check_v14.py` writes Byun et al.'s entry into `tex/refs.bib` from Crossref (with `cite_check.py`'s own
  functions; Unicode hyphens folded to ASCII) and appends its row to `records/CITE-CHECK.json`.
- Figure 1: `revision13/make_fig_arch.py`, checked by `revision13/check_fig_arch.py`. Figures 1-3 of version 13 are now 2-4.
- Build: `pod/build_payload_rev9.py` and `pod/build_rev9.sh` (derived by `pod/derive_build_rev9.py`; they add Figure 1), run in WSL
  Ubuntu with tectonic 0.15.0 (`records/revision13/BUILD-STEPS-v14.txt`). Both variants have 44 pages, no undefined reference or
  citation, no overfull box over 2 pt; the arXiv archive compiles alone; the HTML is complete and clean. The arXiv abstract has
  1,911 characters (limit 1,920).
- Availability: archive v1.4, release v1.4, eleven reviews, `RESPONSE-TO-REVIEW-11.md`, Figure 1's scripts. The concept DOI
  10.5281/zenodo.23748861 is unchanged. History: version 13 is no longer "this paper"; version 14 is described.

## Checks

- **Text** (`revision13/pdf_text_diff_v14.py`, version 13 -> 14, word counts by `revision12/pdf_text_diff_v13.py`'s method): 58 expected
  edits (55 edits and 3 line-break or glyph-spacing artefacts of unchanged text, listed in `revision13/expected_v14.py`), 0 unexplained
  word changes, 0 edits not seen, in both variants; one page more (43 -> 44). Reference numbers are compared as "[#]" because the new
  citation renumbers every later reference. The same check on version 12 against version 14 fails, as it must.
- **Name** (`revision9/name_check_v10.py`): NAME_OK in WSL and in Windows.
- **Numbers** (`revision8/check_numbers_fresh.py --selftest`): every `tex/numbers*.tex` is fresh.
- **Figures:** Figure 1 (`check_fig_arch.py --selftest`, 4 of 4 faults caught) and version 1's Figure 4 (`check_fig_main.py --selftest`).
- **Reset and Welch** tests pass.
- **Every earlier check:** `revision13/check_build_v14.py` (derived by `revision13/derive_check_v14.py`) runs `revision6/check_build_v7.py`
  and reads the records above: `records/revision13/ARTIFACT-CHECK-v14.json`, ALL_OK.

## Archive v1.4

Release v1.4 holds version 14 and every change above. `make_deposit.py` builds it (with `reproduce_all.py` gaining two steps: Figure 1
and its check) and `deposit_cleanroom.py` reproduces it in a clean room; the results are in `records/deposit/`. The README's "Changes
since v1.3" section and `RELEASE-NOTES.md` list the changes.
