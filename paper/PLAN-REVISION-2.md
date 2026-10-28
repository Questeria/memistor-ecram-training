# Lane ME-REVISE-2: pre-registration of the two bounded experiments of review 2 (written 2026-10-26 ~19:35 ET, committed 19:38 ET, before any run)

Review 2 (`reviews/REVIEW-2-chatgpt-20261026-full.md`) asks for two bounded experiments: a pulse-fidelity comparison (its
finding 1) and a corrected fixed-symmetry control (finding 4). This plan fixes the runs, the analysis and the wording each outcome
allows before any run. Deviations go to `DEVIATIONS-PAPER.md` as R4, R5, ... with what had been seen. What had been seen when
this was written: the v2 records (E3, E4, E5) and the checks of `revision2/verify_findings_2.py`
(`records/revision2/VERIFY-FINDINGS-2.json`); no run of this plan. Budget: worst case at most $3 for both, one pod at a time.

## 1. Code (desk-checked before any run)

- `sim/pulse_seq_rev2.py`: the explicit pulse streams beside the surrogate. The line probabilities are those of
  `memsim_rev.pulse_counts` (same update management, same clipping at 1), so all methods share the requested and the
  policy-expected update.
  - `slot` (literal): per sample, per slot, Bernoulli row and column line firings; one pulse per coincident cell through the
    per-pulse step `s_up(u) = k_up (1 - g_up u)`, `s_dn(u) = k_dn (1 + g_dn u)`, write noise per pulse, bounds after every pulse.
  - `seq`: the same line firings give each cell's count per sample (shared lines keep the cross-cell correlation); a sample's
    pulses at one cell all have one sign, so its train is one exact affine map (closed form; its write noise, std
    `c2c sqrt(n) s(u_pre)`, is affine in the pre-sample state and folded in); samples in order, bounds after every sample.
- `sim/run_rev2.py`: `run_rev.py` with `--pulse seq --seq-layers all|i,j` (the named layers update with `seq`; bias, chopper,
  transfer, reset, drift and the other layers unchanged) and update-fidelity probes (`--probe-layers`, `--probe-steps`,
  `--probe-draws`): at a layer's update number the batch's x, d and the target array's state are applied R times from the same
  state by the surrogate, `seq` and `slot` (`slot` replays each `seq` draw's firings), from a probe generator of its own.
- `sim/test_rev2.py` (5 checks, each with a planted fault that must fail): `seq` equals `slot` pulse by pulse on shared firings
  (noise-free, paper and aihwkit devices); the mean count is BL |p_x||p_d|; review 2's limiting case (one sample, p = 1: the
  stream gives exactly 31 pulses, Poisson(31) exceeds 31 with probability 0.4524); `--pulse surrogate` with probes reproduces the
  run without probes (metric and pulse counts); `--pulse seq` is routed. Desk: ALL_OK, 5 faults caught
  (`records/revision2/TESTS-REV2.json`); it runs again on the pod before the phases (a failure stops the sitting).
- `sim/sweep_rev2.py` (phases below), `pod/run_rev2.sh` and `pod/make_payload_rev2.py` (derived by `pod/derive_run_rev2.py`).

## 2. Experiment A: pulse fidelity

**A1, update fidelity (phase `fidprobe`, 3 runs, seed 0, surrogate training identical to E3 plus probes).** Cases chosen to
include clipped and unclipped layers of the operating regime (review 2 finding 1: the worst layer is the MO-ECRAM AGAD CIFAR
output layer, 96.4 % of the requested unsigned pulse mass lost; the LM embedding 27.8 % on average):

| task | device, algorithm | layers probed | at layer updates | draws |
|---|---|---|---|---|
| MNIST | Li-ECRAM c-TTv2 | 0 (256x784), 2 (output 10x128) | 1000, 3500 | 16 |
| CIFAR | MO-ECRAM AGAD | 3 (fc 128x1024), 4 (output 10x128) | 600, 2000 | 16 |
| LM | protonic-inspired c-TTv2 | 0 (embedding 128x256), 9 (output 256x128) | 750, 2250 | 6 |

Per probe and method (in nominal steps): the realised mean update's gain along the requested update
`g_req = <m, Q> / <Q, Q>` (Q = the pre-clip request) and along the policy-expected one, the mean per-cell variance, the mean
off-diagonal correlation of the draws' residuals among cells sharing a row and a column, and against `slot`: the relative mean
difference `||m - m_slot|| / ||m_slot||`, its sampling floor `sqrt((sum var + sum var_slot) / R) / ||m_slot||`, and the median
per-cell variance ratio. The excess mean difference is `sqrt(max(0, diff^2 - floor^2))`.

- **The surrogate is update-faithful on a probe** if |g_req(surrogate) / g_req(slot) - 1| <= 0.10, the excess mean difference
  <= 0.10, and the median variance ratio lies in [0.5, 2]. Otherwise it is **not faithful on that probe** (reported with which
  part fails).
- `seq` is a valid training reference if it meets the same lines against `slot` with 0.05 and [0.8, 1.25]; if it does not on a
  task, that task's A2 comparison is reported as having no valid reference.
- Covariance is descriptive (no line): the Poisson surrogate has independent cells, the stream does not.

**A2, training fidelity (phase `fid`, 36 runs, seeds 0, 1, 2).** The same selections and learning rates as E3, with the `seq`
stream: MNIST on every analog layer, Li-ECRAM, MO-ECRAM, protonic-inspired x SGD, c-TTv2, AGAD (27 runs); CIFAR on the two fully
connected layers (3, 4; the convolutional layers, whose rows per batch are 128 x 1024 patches, keep the surrogate within this
budget): Li-ECRAM c-TTv2, MO-ECRAM AGAD, protonic-inspired c-TTv2 (9 runs). No LM training run (4096 rows per batch at 10 layers is
beyond this budget); the LM is covered by A1 only.

- Per cell: `dgap(s) = gap_seq(s) - gap_surrogate(s)`, the surrogate gap being E3's record of the same seed (same init and data
  order), both against E3's FP-SGD of that seed; the mean over seeds and its 95 % t-interval (n = 3).
- **Material** (kill line for "the main-table conclusions are robust to the aggregate update in this regime"): for any cell
  |mean dgap| > 1 pp (half the line), or within a task two cells whose surrogate mean gaps differ by more than 1 pp swap order
  under `seq`. **Not material**: neither occurs. Either verdict is stated with its bound (MNIST all layers; CIFAR fc layers only;
  LM update level only; n = 3).
- If material: the paper says the affected results are not validated against the explicit stream and names the cells; the
  affected comparisons are flagged for a rerun (not done within this budget). If not material: the paper publishes the evidence
  with its bounds and keeps the fidelity gap for the conv layers and the LM.
- The E3 label (n = 5) of a cell is not re-derived from n = 3.

## 3. Experiment B: the fixed-symmetry control (phase `e5fix`, 24 runs)

The protonic-inspired base with `recenter_sp = true` at asymmetry 0.05 (the recentred base; nominal range [-1, 1], against
[-1.125, +0.875] for the E5 base) and at asymmetry 0 (the zero point the plan listed and the code omitted), TTv2 and c-TTv2,
CIFAR c = 32 and LM d = 128, seeds 0, 1, 2, FP-SGD's learning rate, the FP reference E3's FP-SGD of the same seed (as E5).

- Each point gets the E5 label against the absolute line (n = 3). The fixed-symmetry axis is re-derived with these runs as its
  anchor (0.05) and best end (0), plus the existing 0.1, 0.2, 0.4 points: the pre-registered E5 rule (the anchor must PASS; the
  threshold is the weakest value passing with every value between it and the best end passing). The signed range of every
  fixed-symmetry point is [-1, 1].
- **Kill line for the v2 claim** "with the symmetry point held at mid-range only the base value (0.05) is established": it
  stands only if the recentred base PASSES on CIFAR with c-TTv2; otherwise it is withdrawn and replaced by what the recentred
  points show. The unrecentred and the recentred base are also compared paired by seed (mean difference, 95 % interval).
- The moving-symmetry axis and the reference-error threshold are not changed by this experiment.

## 4. Where and how

One pod (`altone-x1kmr-`, grant G2, `pod/guarded_create_rev.sh`, cheapest 24 GB card at most $0.30/h, cap $1.5), phases in
the order `fidprobe fid e5fix`, 8 workers, run 100 minutes. The start rule: balance minus every live pod's worst case at least $15,
else wait. Announced to MFU, "Helios Evolution B1 sub conversation", "HIVE engine: every model type and size, multi-GPU" and
"Helix language + kovc: make it the best for us". Outputs are pulled before the release; the release is confirmed in the pod
listing and in `F:/shared/LIVE-HOLDS.jsonl`. The analysis is `revision2/analyze_rev2.py` (written before the records are read;
its numbers go to `records/revision2/RESULTS-REV2.json` and `tex/numbers_rev2.tex`).
