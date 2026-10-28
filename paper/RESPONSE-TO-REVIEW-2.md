# Response to the second independent review (ChatGPT, 2026-10-26), version 3 of the paper

The review (`reviews/REVIEW-2-chatgpt-20261026-full.md`; the owner's pasted summary is `reviews/REVIEW-2-chatgpt-20261026-summary.md`)
read version 2 (commit cd5977206, `build/v2/main.pdf`, SHA-256 d4f9045d...eb45). Lane ME-REVISE-2 treated it as findings to verify,
not instructions. Every finding was first checked against the code and the saved records by `revision2/verify_findings_2.py`
(`records/revision2/VERIFY-FINDINGS-2.json`); numbers below are copied from that file or from the records named. All eight findings
are CONFIRMED. Two bounded experiments were pre-registered in `PLAN-REVISION-2.md` (commit 86e86fe89, pushed 19:38 ET, before any
run) and run in two pod sittings (r6, and r7b for the runs r6's deadline cut, deviation R6). Deviations R4 and R5 are in `DEVIATIONS-PAPER.md`. The v2 sources are kept in `tex/v2/` and the
v2 build in `build/v2/`.

| # | Finding | Disposition | Fix |
|---|---|---|---|
| 1 | Pulse fidelity unvalidated in the training regime | CONFIRMED | Experiment A (A1 update probes, A2 training); Section "Fidelity of the aggregate update" |
| 2 | Width inference ignores the seed pairing | CONFIRMED | Paired contrast beside the registered Welch one (R4); headline reworded |
| 3 | Appendix B lists the v1 settings | CONFIRMED | Table generated from CHOICES-REVISION.json; v1 table moved, marked superseded |
| 4 | Fixed-symmetry sweep uses an unrecentred base | CONFIRMED | Experiment B (recentred base + zero point); anchor substitution removed; R5 |
| 5 | Submission artifacts inconsistent | CONFIRMED | Abstract regenerated from the v3 records; checklist; archive compiled alone |
| 6 | Placeholders and overflowing tables | CONFIRMED | Macros fixed; tables reformatted; lint and LaTeX-log checks |
| 7 | Reset summaries' aggregation units | CONFIRMED | Macro-average, pooled and maximum reported and labelled |
| 8 | Energy labels ("equal quality", 6.94 TOPS/W) | CONFIRMED | Margin wording; FAIL vs not established; projected system figure |

## 1. Pulse fidelity remains the principal scientific uncertainty: CONFIRMED; experiment A run

Evidence (F1): `sim/memsim_rev.py` draws independent per-cell Poisson counts (`pulse_counts`) and applies a batch's up and down
pulses in one ODE step with the write noise at the pre-batch state (`Tile._step`). The worst single layer record loses 96.39 % of
its requested unsigned pulse mass (`e3__cifar_w32__ecram_mo_kim2019__agad__lr0.001__s3`, layer 4); Poisson(31) exceeds 31 with
probability 0.4524 (the review's limiting case, reproduced analytically and by `sim/test_rev2.py` check 3).

Experiment A (pre-registered, `PLAN-REVISION-2.md` section 2; code `sim/pulse_seq_rev2.py`, `sim/run_rev2.py`; checks
`sim/test_rev2.py` ALL_OK with 5 planted faults caught, on the desk and on both pods; records `records/revision/runs/fidprobe*`,
`records/revision/runs/fid`; analysis `revision2/analyze_rev2.py` -> `records/revision2/RESULTS-REV2.json`):

- A1, update fidelity, 12 probes (MNIST Li-ECRAM c-TTv2 layers 0 and 2; CIFAR MO-ECRAM AGAD layers 3 and 4; LM protonic-inspired
  c-TTv2 layers 0 and 9; two training points each). The surrogate passes the pre-registered lines (gain within 10 %, excess mean
  difference <= 0.10, variance ratio in [0.5, 2]) on 10 of 12, including layers losing up to 32.5 % to clipping; its variance
  ratio to the literal stream is 0.71-1.55. It FAILS on both probes of the CIFAR MO-ECRAM AGAD output layer: 92.1 % lost (gain
  +1.8 %, excess mean difference 0.18) and 96.5 % lost (gain +32.7 %, excess 0.37). The per-sample stream passes against the
  literal stream on all 12 (gain within 0.6 %, variance ratio 0.977-1.018), so it is a valid training reference. The cross-cell
  correlation from shared lines is at most 0.011 in absolute value.
- A2, training fidelity, 36 runs (MNIST all layers, 3 devices x SGD, c-TTv2, AGAD; CIFAR fully connected layers, 3 cells; seeds
  0-2), paired with E3's surrogate runs. By the pre-registered kill line the verdict is MATERIAL, through one cell: MNIST MO-ECRAM
  SGD, a failing cell, whose gap moves from 14.10 to 12.68 pp (difference -1.42 pp, 95 % interval [-4.84, 2.00]). No pair of cells
  swaps order; no Tiki-Taka-family cell moves by more than 0.61 pp (CIFAR intervals span several pp at n = 3).
- As registered, the paper names the cell as not validated against the explicit stream, and states the bounds: the conv layers
  and the LM training trajectory are not compared, and the surrogate is not valid where clipping removes nearly all of an update.
  A rerun of the affected comparisons is flagged, not done within this budget; since the one material cell fails by more than
  10 pp under either update, no label of the main table changes.
- The probe runs reproduce their E3 records exactly for MNIST and CIFAR; the LM run differs by 0.13 % because LM training on the
  GPU is not bitwise reproducible (identical E5-base and E3 configurations differ by up to 0.31 % in bits per byte; CIFAR 0.00 %).
  The paper states this.

Fix in the text: the new subsection "Fidelity of the aggregate update" (Tables `tab:rev2_probe`, `tab:rev2_fid`), the methods
paragraph points to it, the clipping item no longer calls clipping "the hardware's pulse budget, not a simulator error" (it is the
chosen update-management policy), the limitations and the abstract carry the result and its bounds, and the main results are
described as comparisons within this aggregate-update simulator.

## 2. Width inference ignores a pairing present in the experiment: CONFIRMED

Evidence (`VERIFY-FINDINGS-2.json` F2): every E4 seed has one data-order hash across widths, so the endpoint samples are paired.
Recomputed from the records, the per-seed differences for protonic-inspired c-TTv2 on CIFAR are 2.82, 3.82, -0.05, 0.11, 2.11 pp;
the registered Welch 90 % interval is [-0.021, 3.545] (INCONCLUSIVE) and the paired one [0.146, 3.378] (GROWS), exactly as the
review states. Li-ECRAM c-TTv2 stays EQUIVALENT paired ([-1.79, 1.106]); all four LM arms shrink by both; protonic-inspired TTv2
stays "no evidence of growth beyond the margin"; Li-ECRAM TTv2 stays INCONCLUSIVE.

Fix: the registered Welch result is kept as the registered result, and the paired contrast is reported beside it as a
sensitivity analysis added after the review (deviation R4; `revision/analyze_rev.py` `width_paired`; Table `tab:rev_width` has
both). The abstract, the width section, the discussion and the conclusion now say: no arm's gap grows detectably beyond the
margin; endpoint equivalence was established for one CIFAR pairing only; a paired analysis detects sub-margin growth for another;
for one arm growth beyond the margin is not excluded; width dependence is unresolved. The text says that an endpoint test does
not cover the middle width, and that a gap moving from more negative to less negative can grow while both cells pass. The
direction of the weight scale is corrected: alpha falls as 1/sqrt(fan-in) when a layer's fan-in grows (layers with fixed fan-in
keep theirs).

## 3. The hyperparameter appendix describes version 1 settings: CONFIRMED

Evidence (F3): `tex/app_selection.tex` input the v1 table `tables/e2.tex` (TTv2 period 16, val 97.86; c-TTv2 rho 0.2; AGAD rho
0.05). `CHOICES-REVISION.json` has TTv2 period 64 with the pulse reset (val 0.976), c-TTv2 period 16, rho 0.05, pulse reset
(0.976), AGAD period 16, rho 0.2, beta 0.3, no reset (0.973). All E3 records agree with the revised choices (0 mismatches).

Fix: `revision2/analyze_rev2.py` generates `tables/rev2_selection.tex` from `CHOICES-REVISION.json` and the simulator's
`UpdateCfg` defaults: each algorithm's setting, its reset mode and budget (pulse reset, at most 62 pulses, 2 read-correct
iterations; BL 31; at most 31 transfer pulses), the validation accuracy, the FP-SGD rates per task and width, the Adam rates and
the E4 arms' rates per width. The v1 table moves to the superseded appendix with the caption prefix "Version 1 (superseded)".
The same prefix is now on every v1 table and figure there (`tables/v1s_*.tex`, made by script from the v1 tables), and the
revised catalog (`tables/rev2_catalog.tex`, from `CATALOG-REV.json`) takes Table 1's position; the original field copy is in the
superseded appendix.

## 4. The fixed-symmetry sweep uses a base point that was not recentred: CONFIRMED; experiment B run

Evidence (F4): all 12 E5 `base` records have `recenter_sp` false; the held-symmetry sweep ran only 0.1, 0.2 and 0.4;
`revision/analyze_rev.py` used the base as the 0.05 anchor (nominal range [-1.125, +0.875] against [-1, 1] when recentred); the plan
listed the zero point. Deviation R5 records the omission and corrects the earlier "miscount" note.

Experiment B (pre-registered, `PLAN-REVISION-2.md` section 3; phase `e5fix`, 24 runs, records `records/revision/runs/e5fix`): the
recentred base (0.05) and the zero point, TTv2 and c-TTv2, CIFAR and LM, seeds 0-2. The analysis no longer substitutes the base
(without its own run the axis is "not established"). Result: on CIFAR with c-TTv2 the recentred base PASSES (gap -0.41 pp) and so
does a = 0 (-1.43 pp), so by the kill line the held-symmetry threshold 0.05 stands, now established by its own runs; the recentred
base differs from the unrecentred one by 0.44 pp (95 % interval [-2.66, 3.54]). 0.1, 0.2 and 0.4 stay UNRESOLVED with mean gaps
below zero. TTv2 (both tasks) and the LM with c-TTv2 have UNRESOLVED recentred bases, so their axes stay "not established". The
signed range of every held-symmetry point is [-1, 1]. The moving-symmetry axis and the reference-error threshold are unchanged.

## 5. Submission artifacts are inconsistent: CONFIRMED

Evidence (F5): `build/arxiv-abstract.txt` (1,736 characters) contained "near-digital", "within five-seed resolution", "does not
grow with width", "few hundred levels suffice", "about 32x", "15-234x" and "We release"; `PUBLISHING.md` did not name
`numbers_rev.tex`, which the preamble inputs.

Fix: the form abstract is now generated by `revision2/analyze_rev2.py` from the v3 numbers (the same claims as the PDF abstract)
and checked against arXiv's 1,920-character limit and against the withdrawn phrases. `PUBLISHING.md` lists `numbers_rev.tex` and
`numbers_rev2.tex`. The build sitting assembles `build/arxiv-source.tar.gz` from exactly the checklist and compiles
`main-arxiv.tex` from that archive alone in an empty directory, so a missing dependency fails the build. The availability section
keeps the deposit in the future tense.

## 6. PDF overflow and literal placeholders: CONFIRMED

Evidence (F6): `tex/sec_methods.tex` line 52 had `RVorderUpDn`, `RVorderDnUp`, `RVorderBatch` without backslashes (they print on
page 5 of `build/v2/main.pdf`, found by `pypdf` text extraction). The v2 LaTeX log (`sessions/b3b-a2-20261026T220941Z/outputs/main.log`)
has overfull boxes of 140.4 pt (the width table, p. 14), 100.8 pt (the D1 table, p. 31), 63.0 pt (the availability list's
typewriter paths), 58.4 pt (the spec table) and 3.6 pt. The old macro check only matched backslash-prefixed names, as the review
says.

Fix: the three macros are restored (values 0.314, 0.334, 0.327 from `VERIFY-FINDINGS.json`). The width table is rebuilt (gap means
per width, both contrasts, abbreviations explained in the caption), the D1 table's headers are abbreviated with a legend, the spec
table's text column is narrowed, the availability list is set `sloppypar`, and `placeins` keeps floats in their section (the
revised figure printed on p. 32 in v2). New checks, each shown to fail on v2: the build lint (`pod/build_payload_rev2.py`) rejects a
bare macro name (3 errors on the v2 `sec_methods.tex`), and `revision2/verify_findings_2.py --artifacts-only` reads the build's
LaTeX logs for overfull boxes above 2 pt (5 on v2) and the PDF text for bare macro names (3 on v2).

## 7. Reset summaries need their aggregation units: CONFIRMED

Evidence (F7): the 67.00 nominal steps are the unweighted mean of per-layer residual means (66.996); pooled over reset events it is
26.966 (the event count is logged: each reset weight is re-read once per extra iteration, so events = reset_extra_reads / 1, not
reconstructed). The reset pulse share is 3.074 % as a mean of per-run fractions and 0.492 % pooled. The largest layer-mean residual
is 2,081.42 nominal steps (MO-ECRAM c-TTv2 CIFAR, seed 4, layer 4). Per device, pooled: Li-ECRAM 3.74, protonic-inspired 5.46, W/WOx
3.86, memistor 8.43, MO-ECRAM 113.35. The worst single layer record loses 96.39 % of its requested unsigned pulse mass (MO-ECRAM
AGAD, CIFAR output layer, seed 3).

Fix: the main text gives the macro-average, the pooled value, the per-device pooled values and the maximum, and says which
question each answers; the clipping item says that the per-layer figures are means over runs, names the worst single layer, and
that the logged fraction is the discarded unsigned expected pulse mass, not the lost signed gradient after cancellation.

## 8. Keep the energy analysis at its stated evidentiary level: CONFIRMED

Evidence (F8): the primary source (Ambrogio et al., Nature 620, 2023; Europe PMC full text PMC10447234, quotes in
`records/revision2/AMBROGIO2023-QUOTES.txt`) says the five-chip RNNT implementation "is not integrated with digital processing" and
that the energy-efficiency figure is at the "full system level including estimated digital processing energy"; the system total
gives 6.94 TOPS/W, and "some external components used in real systems, such as system buses and voltage regulators" are not
included. 12.4 TOPS/W is the measured chip-sustained figure.

Fix: the energy section, the energy table caption and `energy/energy_rev.py` call 6.94 TOPS/W the authors' projected full-system
figure (digital processing estimated, not integrated; buses and regulators excluded) and 12.4 TOPS/W the measured chip figure. "Energy
to equal quality" is replaced by "conditional ratios for cells that pass the stated margin under ideal reads"; FAIL cells are
marked as missing the margin and UNRESOLVED cells as "criterion not established" (the table distinguishes them); the text says that
no joint finite-read operating point or energy-to-target trajectory is demonstrated. The energy numbers are unchanged
(`ENERGY-REVISION.json` regenerated; identical apart from the notes, checked).

## The additional points

- Alpha direction (p. 12): corrected (finding 2 above).
- "Without establishing equivalence": now "endpoint equivalence was established for one CIFAR pairing only", with the paired
  qualification, in the abstract and the conclusion.
- AGAD (p. 9): the unqualified "AGAD is unaffected" item is replaced by the two-seed reading.
- Table 1: the revised catalog takes the main position; the field copy is in the superseded appendix.
- Superseded captions: every v1 table there starts "Version 1 (superseded)".
- "Released records" (author contributions): now "saved records".
- "The remaining questions are experimental": the conclusion now names the computational and methodological questions too.
- The ideal 1000-level reference: the text says it keeps stochastic counts, bounds, thresholds and the update management, is not an
  exact-update algorithm-only reference, and that its MNIST success does not make every other failure an unavoidable device limit.
- The stringent sheet rule: the text says that "not established" does not mean no grid value passed (c-TTv2 CIFAR passes at 500,
  1000 and 2000 levels; 5000 is UNRESOLVED) and does not show that more levels harm training.
- Absolute digital baselines: printed beside the gap tables (FP-SGD and Adam means per task).

## The previous thirteen findings

The review's disposition table is accepted. Items 4, 5, 6, 8, 10 and 13 are those it left open; they are answered above (findings
1, 4, 2, 8, 4 and 6 respectively).

## The version 3 build

Build sitting b5 (session `sessions/b5-a1-20261027T031257Z`, released and confirmed absent): `build/main.pdf` (authors Questeria
and Claude (Anthropic)), `build/main-arxiv.pdf` (author Questeria; Claude acknowledged in "Author contributions and use of AI"),
`build/main.html`, 37 pages, and `build/arxiv-source.tar.gz` (65 files from the PUBLISHING.md list; it compiles alone in an empty
directory). Checks (`records/revision2/ARTIFACT-CHECK-v3.json`): no overfull box above 2 pt in the main, arXiv and archive logs (the
first build of this round, b4b, still had four, which led to the table restructuring of `revision2/edit_fit_tables.py`); no bare
macro name in the PDF text or the sources; no undefined reference or citation in either log; the build lint passes. The form
abstract (1,867 characters) is generated from the PDF abstract. The citation check was re-run (`records/revision2/CITE-CHECK-rerun-v3.*`):
44 of 48 verified; the other four (mouttet2010, rasch2023arxiv, wu2025, wu2026scale) failed on HTTP 429 rate limits or a read
timeout, not on content; no reference changed since the 48/48 check of version 2, so `tex/refs.bib` and `records/CITE-CHECK.json` are
kept as verified then.

Spend of this round: about $0.85 (sittings r6 and r7b on an RTX A4000 at $0.25/h, two short build sittings); balance $36.02 before,
$35.17 after.
