# Lane ME-PAPER: pre-registered plan of the new experiments (written before any of them was run)

Written 2026-10-25 from about 13:15 ET (desk clock), before any run below. It builds on lane ME's finished work in
`ops/x1000-20261023/phase2/memistor/` (PLAN.md, DEVIATIONS.md, VERDICT.md, records/), whose results are DEV and are not
inherited as findings: every number in the paper comes from the runs listed here (or is quoted from lane ME's records and
labelled so). Any change to this plan is written in `DEVIATIONS-PAPER.md` with its reason BEFORE the affected run.

The owner (2026-10-25, about 13:xx ET), verbatim: "For the Memristor modern descendants research, I want you to continue it.
Even though we cannot do it ourselves with our resources I want to make a full research paper like report so that others who
have the resources can attempt it. Also if possible I would like to publish it. Put me and yourself at the authors. Be sure to
correctly cite sources."

## 0. The simulator

`paper/sim/` = lane ME's `sim/` with named additions (`derive_memsim.py`, `edit_tasks_run.py`):

- `gamma_d2d`: a per-device spread of the saturation slopes (the RPU-baseline model needs it).
- `alpha`: a fixed weight scale for every layer (the validation maps the published weight range onto the device).
- `ttv1`: Tiki-Taka v1 (Gokmen and Haensch 2020). W = C + gamma A; every batch reads `tt_cols` columns of A and adds
  lambda x A[:, j] to C[:, j] by a pulsed outer product with the one-hot input e_j; A is never reset.
- `cttv2`: chopped TTv2 (Rasch et al. 2024). The A update sees c ⊙ x with chopper signs c_j in {-1, +1}. The read of column j
  is multiplied by c_j. Each read column's chopper flips with probability `tt_rho`.
- `agad`: AGAD (Rasch et al. 2024). The choppers of c-TTv2, plus a digital leaky average P of the reads,
  p_j <- (1 - beta) p_j + beta w_A[:, j]. The read is z = c_j (w_A[:, j] - pref_j), and pref_j <- p_j when c_j flips.
  The paper's text layer shows the average with a minus sign before beta; we read it as the leaky average its words describe.
- Common to the TT family: lane ME's digital buffer H, with up to 31 C pulses per transfer.

Checks: `sim/test_paper.py` gives 5 checks and 7 planted faults (`records/TESTS-PAPER.json`). The checks include the bit-for-bit
identity of the SGD and TTv2 paths with lane ME's memsim.py. Lane ME's `test_memsim.py` (9 checks, 10 faults) is re-run
against the paper simulator (`records/TESTS-laneME-checks-on-paper-sim.json`). Both were green before this plan was written.
Every pod sitting re-runs both and stops if either fails.

One fix to lane ME's code (named here because it changes the LM selection data):

- Lane ME's LM "validation" was the last 500 kB of the TRAINING slice, so the model had trained on it.
- The paper's selection runs (`--split val`) train on the first 7.5 MB of the slice and evaluate on that held-out last 0.5 MB.
- Test runs train on all 8 MB and evaluate on the separate test slice (enwik8 bytes 60,000,000-60,500,000).

## E1. Simulator validation: reproduce Gokmen and Haensch 2020 (Front. Neurosci. 14:103), FCN on MNIST, RPU-baseline device

Published (their text):

- FP SGD (mini-batch 1, lr 0.01, 50 epochs) reaches 2.0 % test error.
- SGD on the RPU-baseline device gives "about 15%".
- Tiki-Taka gives "close to 2%", indistinguishable from FP.

Model: 784-256-128-10, sigmoid hidden, softmax output; summed cross-entropy; lr 0.01 per sample; 50 epochs on all 60,000
training images; test on the 10,000.

Our device mapping of their RPU-baseline:

- Weight bound 1/1.66 (alpha = 0.60241).
- dw_min0 = 1e-3 at w = 0 (n_states = 2 x 0.60241 / 1e-3 = 1204.8).
- Device-to-device step spread 0.3; gamma_up = gamma_dn = 1 (slope 1.66 in weight units) with gamma_d2d = 0.42 / 1.66 = 0.253.
- Cycle-to-cycle noise 0.3 of the step; no global asymmetry (the two branches share dw_min0, so every device's symmetry point is
  w = 0); ref_err 0; BL 31.

Known differences, stated in the paper:

- We use mini-batches of 16 (their batch is 1). The batch's per-sample pulses are summed and applied as interleaved.
- We do not model their forward/backward read noise (0.06), 7-bit inputs, 9-bit ADC or output bound 12.
- Our biases are digital.
- Our hard bounds are at |u| = 1, so a device whose slope is below the mean saturates at the bound, not at its own 1/slope.

Arms, 3 seeds each (0, 1, 2), test split:

- FP (ideal float).
- SGD on the device.
- TTv1 as published: eta 0.01 on A, lambda 0.02 on C, gamma 1, ns = 1, i.e. 16 columns per batch of 16.
- Our TTv2: TT-CHOICE settings with tt_cols = 16.

Batch check (seed 0): FP, SGD and TTv1 at batch 64.

Agreement, decided before the runs:

- QUANTITATIVE if all three hold:
  - our FP error is in [1.5, 2.5] %;
  - our SGD error is in [10, 20] %;
  - our TTv1 error is <= our FP error + 0.5 pp.
- QUALITATIVE if SGD >= FP + 5 pp and TTv1 <= FP + 1 pp.
- Otherwise NOT REPRODUCED.

## E1b. Qualitative check of Rasch et al. 2024 (Nat. Commun. 15:7133), Fig. 5: reference offsets

Same FCN and mapping (alpha 0.60241). The device has 20 states (n_states = 20), gamma_up = gamma_dn = 1, c2c 0.3, d2d 0.3,
gamma_d2d 0.253, and ref_err sigma_r in {0, 0.5} (in units of the half-range, i.e. of the weight bound).

- Arms: TTv2, c-TTv2 and AGAD (the E2 settings) and FP.
- Budget: 10 epochs, batch 16, lr 0.01; seeds 0 and 1.
- Published trend: with an uncorrected reference offset, TTv2 degrades strongly; c-TTv2 largely corrects it; AGAD is unaffected.
- REPRODUCED if, at sigma_r = 0.5:
  - error(TTv2) - error(AGAD) >= 2 pp;
  - error(AGAD) is within 1 pp of AGAD at sigma_r = 0;
  - error(c-TTv2) <= error(TTv2).

## E1c. Cross-check against IBM's aihwkit (optional, on a pod only, never on the desk)

- Install `aihwkit` from PyPI on the E1 pod (CPU build). One install attempt, then one pinned older version if the first fails.
  A failure is recorded and ends E1c.
- Cells, with matched device parameters (SoftBoundsDevice; ideal forward/backward; BL 31):
  - the E1 FCN and RPU-baseline device for 3 epochs at batch 16, SGD;
  - the same cell with aihwkit's TTv2 preset or compound;
  - our simulator on the same reduced budget.
- Seeds 0 and 1.
- AGREES if every |error difference| <= max(1.5 pp, 2 x the larger seed spread).

## E2. Selection of the tolerant algorithms' settings (desk, P2000, MNIST validation only)

Lane ME's protocol: MLP 784-256-128-10 tanh, 10 epochs, batch 128, MNIST validation (5,000 held-out training images), with
lane ME's mid device (n_states 128, asym 0.1, gamma 0.3, c2c 0.5, ref_err 0.02), which is not in the catalog.

1. The FP lr grid {3e-4, 1e-3, 3e-3} picked its EDGE (3e-3), so 1e-2 is added. If 1e-2 wins, 3e-2 is added, and so on until the
   best is interior. The MNIST lr is the best FP validation accuracy.
2. If the lr changes, lane ME's TTv2 grid (10 arms, sweep.py TT_GRID) is re-run at the new lr and TTv2 is re-chosen; otherwise
   TT-CHOICE.json stands (lambda 0.1, A lr x 10, period 16).
3. The c-TTv2 grid has 8 arms: lambda {0.1, 0.3} with A lr x 1/lambda, period 16, rho {0.05, 0.2}, reset {no, yes}.
4. The AGAD grid has 8 arms: lambda {0.1, 0.3} with A lr x 1/lambda, period 16, rho {0.05, 0.2}, beta {0.3, 1.0}, no reset.
5. Choosing:
   - Each algorithm's best validation accuracy chooses its setting; a tie goes to the earlier arm.
   - **BEST-CHOPPED** = whichever of c-TTv2 and AGAD has the higher best validation accuracy.
   - **S-ALGO** (the spec-sheet algorithm) = the best of TTv2, c-TTv2 and AGAD.

## E3. The main table (pods)

Tasks:

| task | network and data | budget |
|---|---|---|
| MNIST | as E2 | 10 epochs |
| CIFAR-10 subset | lane ME's 3-conv CNN (c = 32) | 30 epochs, batch 128 |
| char-LM | enwik8 human Wikipedia text of 2006, byte-level transformer d128, 2 layers | 3,000 steps x 32 x 128 bytes |

Devices:

- the four published electrochemical specs of lane ME's catalog (ecram_li_tang2018, ecram_mo_kim2019, protonic_onen2022,
  wox_ysz_chen2023);
- Widrow's memistor as he described it (widrow1960_claimed).

Arms, 5 seeds (0-4) each, test split:

- FP-SGD (ideal float), the same network and update rule;
- each device x {SGD, TTv2, c-TTv2, AGAD};
- LM only, Adam on digital twins: context, never the baseline; its lr is chosen from {3e-4, 1e-3, 3e-3} on the clean
  validation split, with the edge rule of E2.

Learning rate:

- One per task, all arms: the FP-SGD validation choice. MNIST from E2; CIFAR and LM from E4 step 1 at the base width.
- CIFAR grid {1e-4, 3e-4, 1e-3, 3e-3}; LM grid {1e-5, 3e-5, 1e-4, 3e-4}; edge rule as in E2.

Statistics:

- Each arm gets a mean and a 95 % t-interval over its 5 seeds (df 4).
- The gap is paired by seed: FP_s - device_s for accuracy; for the LM, 100 x (device_s / FP_s - 1) in bits per byte.
- The gap gets a mean and a 95 % t-interval.
- Gap lines (lane ME's): 2 pp (MNIST, CIFAR) and 5 % (LM).
- Each cell is labelled PASS (whole interval below the line), FAIL (whole interval above) or UNRESOLVED (the interval contains
  the line).
- No multiplicity correction; the paper says so.

Supplementary rows: pencil_lead_today and widrow1960_pessimistic, quoted from lane ME's records with their seed counts,
labelled lane ME DEV.

Runs: 3 tasks x (5 FP + 5 devices x 4 algorithms x 5 seeds) + LM Adam (3 selection + 5) = 323.

## E4. Scale (pods): does the gap grow with width when every arm gets its own learning rate?

- Widths: CIFAR base channels c in {16, 32, 64}; LM width d in {64, 128, 256}.
- Fixed training budget at every width.
- Arms: FP-SGD; protonic_onen2022 x {TTv2, BEST-CHOPPED}; ecram_li_tang2018 x {TTv2, BEST-CHOPPED}.

Steps:

1. FP lr per width on validation, seed 0, over the E3 grids, with the edge rule.
2. Each device arm's lr per width on validation, seed 0, over {lr_FP / 3.16, lr_FP, 3.16 x lr_FP}. The 3.16 is half a decade,
   so this is the FP grid's neighbours; edge rule.
3. Three test seeds (0, 1, 2) per arm and width at its own lr. The gap is paired by seed against FP at FP's own lr.

Verdict on "the gap grows with width" (per task, device and algorithm), from the three widths:

- GROWS if the gap at the largest width exceeds the gap at the smallest by more than the half-width of the larger of their two
  95 % intervals, and the middle width is not below the smallest.
- SHRINKS by the mirror rule.
- FLAT otherwise.

Lane ME's DEV observation (gap grows) is CONFIRMED if GROWS holds for both devices with TTv2 on both tasks.

An optional fourth width (CIFAR c = 128, LM d = 512) is run for FP and protonic x S-ALGO only if the funds rule below allows it.
The choice depends on funds, never on results.

## E5. Sensitivity and the device spec sheet (pods)

Base device: protonic_onen2022 (n_states 1000, asym 0.05, gamma 0.2 / 0.2, c2c 0.3, d2d 0.1, bound_d2d 0.05, ref_err 0.02,
no drift).

- Algorithms: S-ALGO at every size; SGD at the base sizes only.
- Learning rate: the FP lr at that size from E4 step 1. This is a deliberate decoupling from E4; the paper states that a device
  arm's own lr could do better.

One-at-a-time grid, one axis moved from the base, the others at the base:

| axis | values (base marked *) |
|---|---|
| levels n_states | {100, 200, 500, 1000*, 2000, 5000} |
| asymmetry asym | {0, 0.05*, 0.1, 0.2, 0.4} |
| nonlinearity gamma_up = gamma_dn | {0, 0.2*, 0.5, 1, 2} |
| write noise c2c | {0, 0.3*, 1, 2, 4} |
| retention tau_steps, in training steps | {inf*, 1e5, 1e4, 1e3, 1e2} |
| reference error ref_err | {0, 0.02*, 0.05, 0.1, 0.2, 0.5} |

- Sizes: CIFAR c in {16, 32, 64} and LM d in {64, 128, 256}.
- Seed 0, then a second seed (1) at every point whose seed-0 gap lies in [0.5 X, 2 X], with X = 2 pp (CIFAR) or 5 % (LM).
- The gap is measured against the mean of E4's 3 FP test seeds at that size.

Single-axis threshold, per size:

- The weakest grid value whose mean gap is < X, such that every grid value between it and the base also passes.
- Reported as that bracket plus a log-linear interpolation to the X crossing. For c2c and ref_err, which include 0, the
  interpolation is linear.
- If even the best grid value fails, the axis reads "not reachable on this grid".

Pairwise, CIFAR c = 32 and LM d = 128, S-ALGO, seed 0:

- All 15 pairs of axes, each axis at two levels, {moderate, severe}:
  - n_states {500, 200}, asym {0.1, 0.2}, gamma {0.5, 1}, c2c {1, 2}, tau {1e4, 1e3}, ref_err {0.05, 0.1};
  - that is 60 runs per task.
- Interaction = gap(a, b) - [gap(a) + gap(b)], with the single-axis gaps taken from the one-at-a-time grid at the same levels.

Joint spec, per size:

- Every axis at its single-axis threshold grid value at once; 3 seeds.
- If its mean gap is >= X, every axis moves one grid step toward the base and is re-verified, once.
- The spec sheet gives, per size, the single-axis minima and the verified joint spec (or "joint spec not verified").

Runs: about 216 one-at-a-time (162 S-ALGO + 54 SGD), up to about 70 second seeds, 120 pairwise, 18-36 joint.

## E6. Energy (desk; an analysis, no runs)

Unit of comparison: one training sample through one weight (forward MAC, backward MAC, weight-gradient MAC and its update).

**GPU.** 6 FLOP per weight per sample at the H100 SXM's energy per FLOP:

- Its 700 W board power (NVIDIA datasheet) over its dense BF16 peak (989 TFLOPS) times the MEASURED model-FLOP utilisation of
  a large published H100 training run: Llama 3, 38-43 % (Dubey et al. 2024).
- Sensitivity: utilisation 30-55 %, power 500-700 W.

**Analog**, per weight per sample:

- (a) forward and backward MVMs at the energy per MAC of a MEASURED analog in-memory chip, periphery included: Ambrogio et al.
  2023, 12.4 TOPS/W; Le Gallo et al. 2023, as published. Sensitivity: up to projected figures, labelled PROJECTION.
- (b) the update: device pulses per weight per sample, MEASURED in our simulations (E3 records), times the published energy per
  pulse of each device class (PROJECTION or ESTIMATE as labelled in CATALOG and ENERGY of lane ME).
- (c) the line drivers and stochastic-pulse generation per active slot, amortised over the array dimension N in {256, 1024, 4096}
  (published or ESTIMATE, labelled).
- (d) the TT family's extra column reads (one ADC conversion per weight per read, at the published ADC energy), the H buffer
  update, and the C writes, all from the simulation counts.

Output:

- `records/ENERGY-SYSTEM.json`, with every input carrying its source and label (MEASURED / PROJECTION / ESTIMATE).
- The ratio GPU / analog per device and algorithm, central and range.
- What would have to improve for 100x.

## E7. Roadmap, spec sheet and bench appendix

From E5 (the spec sheet), E4 (sizes) and lane ME's BENCH.md: device experiments with pass criteria, array sizes, the
hardware-in-the-loop protocol, and the 1960 memistor bench replication with safety notes. No new runs.

## Pods, funds, order

- Pods: devpod.py under GRANT G2, `--name-prefix altone-x1kmp-`, `--program ALT-X1000`, the cheapest card that fits, worst
  <= $6 a sitting, at most 2 pods of this lane at once (4 program-wide).
- Funds: D80 checked before every create. If balance minus every live worst would fall under $15, the lane WAITS and tells the
  director.
- Priority if funds do not allow everything (decided now, never by results):
  1. E1 + E1b;
  2. E3;
  3. E4 (3 widths);
  4. E5 one-at-a-time (S-ALGO);
  5. E5 second seeds and joint spec;
  6. E5 pairwise;
  7. E5 SGD one-at-a-time;
  8. E1c;
  9. E4 fourth width.
  
  Whatever is not run is reported as not run.
- Sittings collect every record before the release; payloads are under 50 MB, so there is no uplink pause.

## Data

- MNIST: lane ME's pinned idx files (sha256 in tasks.py), carried in the payload.
- CIFAR-10: fetched ON THE POD from www.cs.toronto.edu with the md5 pinned (never on the desk).
- enwik8: the two pinned slices (human text, 2006).
- No TinyStories, no AI-written text.
