# Response to the independent review (lane ME-REVISE, 2026-10-26)

The review: `C:/Users/<user>/.codex/visualizations/2026/10/26/01a17660-270a-7861-bc3d-5e3b794c7ca8/paper-review/Memistor Paper Independent Review.md`
(13 findings, verdict "major revision"). I treated it as data. I checked every claim myself before acting on it.

- My checks on the original code and records: `revision/verify_findings.py` -> `records/revision/VERIFY-FINDINGS.json`.
- The plan for the revision, committed before any revision run: `PLAN-REVISION.md` (commit 46a6e23a5). Its deviations
  R1, R2, ... are in `DEVIATIONS-PAPER.md`.
- Every number below is copied from the record named beside it. The paper's numbers come from `revision/analyze_rev.py` ->
  `tex/numbers_rev.tex`.

Verdicts:

| Finding | Verdict |
|---|---|
| 1 init and data order | CONFIRMED |
| 2 reset | CONFIRMED |
| 3 presets | CONFIRMED |
| 4 surrogate | CONFIRMED |
| 5 spec sheet | CONFIRMED |
| 6 width | CONFIRMED |
| 7 baselines | CONFIRMED |
| 8 energy | CONFIRMED |
| 9 validation | PARTLY CONFIRMED |
| 10 unlogged deviations | CONFIRMED |
| 11 roadmap | PARTLY CONFIRMED |
| 12 related work and release | CONFIRMED |
| 13 presentation | CONFIRMED (editorial) |

No finding is disputed.

## 1. Initialisation and data order are not matched: CONFIRMED

Evidence (`VERIFY-FINDINGS.json` F1). I built the MNIST MLP of the original simulator with seed 0, protonic device:

- For SGD, TTv2, c-TTv2 and AGAD against FP-SGD, the logical initial weights agree only in layer 1 ([true, false, false]).
- The first-epoch permutation differs: 1 position of 50,000 agrees.

Fix:

- `sim/memsim_rev.py` `Streams`: separate generators for the logical init, the data order, each (layer, tile) device
  population and the pulse/noise draws.
- Every run records `init_sha256` and `data_sha256`.
- `test_rev.py c_matched_controls` runs `run_rev.py` itself for 8 MNIST arms (including Adam, the AIHWKIT-mapped device and
  digital TT) and 5 LM arms. It requires equal hashes, and it fails in legacy mode.
- `c_population`: one device has the same tile population whatever the algorithm.
- `c_legacy_replay`: `--rng legacy` replays `run.py` bit for bit.

Effect (diagnostic D1, `records/revision/D1-ANALYSIS.json`):

- The stream repair moved cells by up to 1.68 pp on MNIST and 3.89 pp on the CIFAR slice, within the noise of 3 seeds.
- The paired-gap spread was not reduced in this diagnostic (median 1.78 against 0.76 pp). It is driven by FP-SGD seed
  variability at the edge of stability: the repaired FP-SGD spans 52.0-57.2 % on the CIFAR slice.
- The repaired main table (E3) is paired by seed with matched init and data order.

## 2. The reset is not implemented by the pulses it charges: CONFIRMED

Evidence (F2), nominal protonic parameters, no noise:

- Symmetry point 0.125.
- From u = 0.8, the 62 charged pulses (31 alternating pairs) applied through the device model reach 0.7835 by the batch
  surrogate and 0.7834 by discrete pulses. The implemented reset lands at 0.125.
- Residual: 97.55 % of the displacement.
- A hundredfold reduction needs about 11,513 alternating pulses.
- The selected TTv2 and c-TTv2 configurations used this reset; AGAD did not.

Fix:

- `UpdateCfg.tt_reset` modes `ideal` (old, labelled IDEAL RESET), `pulse` (sign-directed trains from the transfer read, one
  re-read and correction, at most 62 pulses, through the device dynamics), `alt` (31 alternating pairs through the dynamics)
  and `none`.
- `pulse` and `alt` charge exactly what they apply (`c_reset_physical`; it fails on the ideal reset).
- A published-style TTv2 variant: single-pulse transfer, buffer forgotten after firing, no reset of A (`tt_h_forget`,
  `c_h_forget`).
- The selection re-ran on validation with the choice {pulse, none}; validation chose `pulse` for TTv2 and c-TTv2.

Effect:

- D1 (both resets beside the ideal one): a physical reset had an equal or smaller gap in 19 of 24 cells. The ideal reset hid
  no advantage.
- In E3, TTv2 with the pulse reset fails on CIFAR on every published device.
- A residual remains: mean 67 nominal steps on the read columns. Reset pulses are 3.1 % of all pulses in pulse-reset runs.

## 3. The borrowed presets were changed: CONFIRMED

Evidence (F3; the aihwkit master source `presets/devices.py` and `configs/devices.py`, read 2026-10-26):

| | aihwkit EcRamPresetDevice | Our original copy |
|---|---|---|
| Bounds | w_min -0.8276, w_max 1.1724 | [-1, 1] |
| Slopes | divided by the mean bounds | applied directly |
| Slope spread (gamma_*_dtod) | 0.05 | 0 |
| Write noise | multiplicative (mult_noise) | multiplicative |

MO-ECRAM is the same pattern.

Fix:

- `DeviceSpec.bounds_model = "aihwkit"`: the LinearStepDevice parameterisation, one to one.
- `sim/devices_rev.py` -> `records/revision/CATALOG-REV.json`; the old copies are kept as `*_papermap`.
- `c_aihwkit_formula`: our tile follows the LinearStepDevice recurrence over 1500 up and 3000 down pulses within 6.3e-4. It
  fails on the old copy (0.172).

The comparison against aihwkit itself, on a pod:

- `revision/aihwkit_curves.py` (aihwkit from PyPI on the pod, never on the desk) and `revision/compare_curves.py`.
- Done in sitting r4 with aihwkit 1.1.0 on torch 2.10.0+cpu: 500 devices per preset, with and without cycle-to-cycle noise
  (`records/revision/AIHWKIT-CURVES.json`, `AIHWKIT-COMPARE.json`).
- Our aihwkit-mode tile passes the pre-registered rule for both presets. Largest mean difference: 0.0111 (Li), 0.0113 (MO).
  Median sd ratio: 0.94-1.02. Bounds reached: 1.1754 against 1.1765/1.1712, and -0.8264 against -0.8306/-0.8282 (Li).
- The old field copy fails it: mean differences up to 0.17, and it reaches 1.0026 / -1.0014 instead of the shifted bounds.
- Earlier attempts, kept as lessons. Sitting r1d1: aihwkit 1.1.0's plotting needed matplotlib. Sitting r2: pip's torch 2.14.1
  broke aihwkit's tensor binding. Sitting r3: torch 2.9.1 lacks a symbol it needs. `run_rev.sh` now tries torch CPU wheels in
  order until the compiled module imports.

Effect in D1: the mapping moved Li-ECRAM by at most 0.52 pp (MNIST) and 1.08 pp (CIFAR slice).

## 4. The pulse surrogate's fidelity: CONFIRMED (synthetic cases), quantified in the runs

Evidence (F4):

- 20 levels, gamma 1, u = 0.4: up then down gives 0.314, down then up 0.334, the batch solution 0.327.
- x = d = 10, lr 0.1, k 0.002: the requested mean is 5,000 coincidences, the clipped maximum 31.

Fix:

- Per-layer clipping statistics in every revised run.
- The methods now state the exactness condition and the non-commutation. The "conservative noise" claim is withdrawn.

Measured in E3 (`records/revision/runs/e3`; macros `RVLost*`):

- The TT family drives A at 10x the SGD rate and exceeds the BL = 31 pulse budget in the largest layers.
- Mean lost fraction of the requested A update: 57.5 % in the CIFAR output layer, 27.8 % in the LM embedding.
- Plain SGD loses at most 0.7 % in any layer's mean.
- This is reported in Section 4.2 as a property of the pulse budget.

Not done: a comparison against a sequential pulse-by-pulse simulator on training cells. It is listed as a limitation.

## 5. The spec sheet's thresholds are conditional and confounded: CONFIRMED

Evidence (F5):

- The CIFAR w32 base gap is 2.39 pp, so the relative band admitted gaps up to 4.39 pp.
- u* = a / (2 gamma): asymmetry 0.4 at gamma 0.2 puts the symmetry point at the upper bound.

Fix (`PLAN-REVISION.md` section 5):

- Absolute lines only.
- 3 seeds paired with FP-SGD of the same seed.
- The asymmetry sweep is repeated with the symmetry point held at mid-range (`recenter_sp`, `c_recenter_sp`).
- The signed weight range is reported beside it.
- The relative "degradation" sheet is withdrawn from the roadmap. The joint mean-only "pass" is not reused.

Result (`records/revision/RESULTS-REVISION.json` e5):

- The pre-registered sheet (S-ALGO = TTv2) has an UNRESOLVED base on both tasks (CIFAR 6.35 pp, LM 5.15 %), so every
  threshold is "not established".
- It does confirm the confound. At a = 0.4 the CIFAR gap is 42.92 pp when the symmetry point moves onto the bound, but 6.20 pp
  when it is held at mid-range (LM: 10.38 against 5.75 %).
- A second sheet with c-TTv2 was added after E3 was seen (deviation R3; sitting r5).
  - CIFAR: the base passes (-0.85 pp). Established: step asymmetry up to 0.2 with the symmetry point moving (0.4: 42.39 pp)
    and reference error up to 0.05.
  - CIFAR, with the symmetry point fixed: only the base value is established, but nothing fails (gap -0.53 pp at a = 0.4,
    UNRESOLVED).
  - Levels, gamma, c2c and finite retention are not established. Their neighbouring values are UNRESOLVED at n = 3.
  - LM: the base is UNRESOLVED at n = 3 (-1.84 %; it passed with 5 seeds in E3), so no LM threshold is established.
- The roadmap therefore says to measure and simulate one's own fitted device, not to read pass lines off the sheet.

## 6. The width "FLAT" label: CONFIRMED

Evidence (F6): Li-ECRAM c-TTv2 LM gaps were -0.55, -0.09 and -13.73 % at widths 64/128/256, and the arm was labelled FLAT.

Fix:

- FLAT is withdrawn.
- 5 seeds per width (was 3).
- TOST equivalence of the endpoint contrast (margins 2 pp, 5 %), else "no evidence of growth beyond the margin", else
  inconclusive.

Result (E4, 5 seeds, `RESULTS-REVISION.json` e4):

| Task | EQUIVALENT | No evidence of growth beyond the margin | INCONCLUSIVE | SHRINKS |
|---|---|---|---|---|
| CIFAR | 1 (Li-ECRAM c-TTv2, D = -0.34 pp, 90 % interval [-1.34, 0.66]) | 1 | 2 | 0 |
| LM | 0 | 0 | 0 | 4 |

- The LM's shrinkage is largely the FP-SGD baseline getting worse at d = 256 under the fixed budget (3.117 against 2.962 bpb at
  d = 128). The paper says so and makes no scaling claim.

## 7. Device study mixed with an optimizer study: CONFIRMED

Evidence (F7):

- Li-ECRAM c-TTv2 LM was 2.8725 bpb against Adam's 2.3611: 21.66 % worse in bpb, a perplexity ratio of 1.425.
- "near-digital" appeared in the abstract and the introduction.

Fix:

- Adam selected on validation for all three tasks.
- Every table and the abstract state results against FP-SGD and against Adam.
- "near-digital" is removed.
- The main table's lr reuse is stated as a restricted question.

Ideal-device TT reference:

- The arm as first defined (exact float, n_states 1e9) had a transfer quantum of 2e-9 and could not move C. That is
  deviation R2; the records are kept and are not tabled.
- It is replaced by every algorithm on an ideal 1000-level symmetric device (sitting r3). Every algorithm passes MNIST on it.
  None passes CIFAR or the LM: SGD 6.32 pp / 12.14 %, c-TTv2 18.04 pp / 14.47 %. With these settings the TT family relies on
  the device's saturation. The "devices must saturate" claim is narrowed accordingly.

Result (E3, `records/revision/RESULTS-REVISION.json`):

| | Against FP-SGD | Against Adam |
|---|---|---|
| Pairings passing all three tasks | 4: Li-ECRAM and protonic-inspired x {c-TTv2, AGAD} | none |
| Best LM cell | | protonic-inspired c-TTv2, +23.36 % bpb |
| LM cells passing | 4 of 20 | 0 of 20 |

On the LM, FP-SGD itself is 25.35 % worse in bpb than Adam.

## 8. The energy figure is a conditional projection: CONFIRMED

Evidence (F8): our recomputation gives 10.48 pJ for the GPU and 0.3226 pJ for the reads, a ratio of about 32. At 6.94 TOPS/W it
is about 18.

Fix (`energy/energy_rev.py` -> `records/revision/ENERGY-REVISION.json`):

- Section 5 is renamed and starts from its assumptions: ideal-read accuracy against finite-read energy, the inference-chip
  source, the boundary, and the GPU side.
- Both read figures of the same chip are given: 31.5-32.4x (12.4 TOPS/W) and 17.9-18.1x (6.94 TOPS/W, verified in the PMC full
  text).
- The planned 30-55 % GPU utilisation range is shown beside the measured 38-43 %.
- A ratio is printed only for PASS cells (energy to equal quality). On the LM no cell reaches Adam's quality, so no ratio
  exists against it.

Not done: a joint read-precision and energy model.

## 9. Validation and historical claims: PARTLY CONFIRMED

Confirmed:

- The Gokmen-Haensch check uses batch 16 against their batch 1, and ideal reads.
- The Rasch check uses 2 seeds and an ordering.
- The historical sentence was categorical.

Qualified: the paper did list batch 16 and ideal reads as known differences.

Fix:

- The wording is "agreement with selected published outcomes under a simplified read model".
- The Rasch result is an ordering, not equivalence.
- The memistor claim became "an optimistic historical-device scenario attained useful accuracy in this simulator".
- Prior art (Rasch 2024 on reference correction and requirements; Chen 2023 on in-situ ECRAM training) is now credited in the
  introduction.

## 10. Unlogged plan differences: CONFIRMED

Evidence (F10):

- The interaction formula adds the base gap back.
- c2c and reference-error interpolation is log where the plan said linear.
- The GPU utilisation range is 38-43 % against the planned 30-55 %.

Fix:

- These are recorded in the revision appendix and here.
- The revision withdraws the pairwise table and the relative sheet from the conclusions. They remain in the
  original-results appendix.
- Section 5 shows the planned utilisation range.
- The plans are described as internal, repository-timestamped plans, not an external registry.

## 11. Roadmap: PARTLY CONFIRMED

Confirmed:

- A hardware band from a simulator CI shrinks with seeds.
- Per-cell pulse maxima are not recorded.
- "A bench replication" read as done.

Qualified: the appendix already labelled the bench protocol unbuilt.

Fix:

- Stage 3 asks for a prediction interval (device population, fit uncertainty, seeds, measurement noise) and a number of
  independent chips.
- The reset and reference calibration are stated as physical processes with a pulse budget.
- The endurance figure is an average with its caveats.
- Retention needs a schedule.
- "a proposed, unbuilt bench replication protocol".

## 12. Related work and release: CONFIRMED

Fix:

- Wu et al. 2026 ("Making Analog Training Scale", arXiv 2609.36584v1, published 2026-09-29, verified on the arXiv API; authors
  Wu, Gokmen, Fagbohungbe, Xiao, Chen) is cited in the introduction and in a new background paragraph. It contrasts their
  digital weight-gradient path with our fully in-memory update.
- The contribution is narrowed to a reproducible seed-matched comparison.
- The availability section is in the future tense ("nothing has been deposited publicly yet").
- The citation check covers 48 of 48 references (`records/CITE-CHECK.json`).

Not done: the ACS Nano 2026 values could not be checked against the full text; that is stated as a limitation.

## 13. Presentation: CONFIRMED (editorial)

Fix:

- A shorter abstract stating ideal reads, both baselines and the conditional energy.
- Author lists over ten names are abbreviated to "et al." in the bibliography.
- The old dense tables move to the original-results appendix.
- The TTv1 learning-rate exception and the n = 2 interval wording are corrected.
