# Lane ME (X1000 phase 2): the 1960 pencil-lead memistor and its heirs, electrochemical weights for TRAINING: pre-registered plan

Written 2026-10-24 about 20:35 ET (desk clock), BEFORE any sweep was run. The simulator, its checks and short timing smokes
(scratch/, fractions of an epoch, never used as results) exist already; no result below has been seen. Results are DEV.

## The owner's order (verbatim, 2026-10-24 about 20:1x ET)

"I want you to pursue in parallel the four that have the largest potential. After we rule these out or confirm they work then we
will do the three you recommend."

## The decisive question (the director's brief)

Can memistor-class three-terminal electrochemical weights (Widrow's original or modern ECRAM) train neural networks to
near-digital accuracy? What device specifications would that need, and do such devices meet them, so that in-memory analog
TRAINING could become radically cheaper?

## Kill lines (the director's, applied mechanically by `sim/verdict.py`)

- **RULED OUT** if no realistic electrochemical device spec reaches the gap thresholds even with the device-tolerant algorithm.
- **CONFIRMED AS A DIRECTION** if published modern ECRAM specs meet them AND the energy-per-update estimate gives an advantage of
  100x or more over a GPU for the same update. A CONFIRMED is never written before the director's independent adversary check.
- **UNCLEAR** otherwise.

Thresholds: classification gap = FP accuracy minus device accuracy < 2.0 percentage points (test set); LM: device validation
bits per byte / FP bits per byte - 1 < 5 %. "Realistic electrochemical device spec" = a catalog entry labelled PUBLISHED-FIT or
PARTLY-PUBLISHED (sim/devices.py). "Published modern ECRAM specs meet them" = at least one PUBLISHED-FIT or PARTLY-PUBLISHED
ECRAM/protonic entry passes on ALL THREE tasks with at least one algorithm (3-seed mean on MNIST; 1 seed on CIFAR and LM, a
second seed added wherever the margin is under a quarter of the threshold).

## The device model (`sim/memsim.py`, own code, torch only, no aihwkit, no downloads)

Every analog weight's update goes through the device; forward and backward reads are ideal fp32 (read noise, ADC and DAC
quantisation are OUT OF SCOPE: the question is the update; this is stated beside every result).

- State u in [-1, 1] per device; `n_states` = range / mid-range step (one pulse = 2/n_states).
- Up/down asymmetry `asym` (up = k(1+a/2), down = k(1-a/2)) with device-to-device spread; saturating (soft-bounds) step
  `gamma_up`, `gamma_dn` (up step = k_up(1 - gamma_up u), down = k_dn(1 + gamma_dn u)); cycle-to-cycle write noise `c2c`
  (std per pulse / step, grows as sqrt(pulses)); device-to-device step and bound spreads; drift = relaxation toward the bare
  state u = -1 with time constant `tau_steps` (batches); a reference conductance at each device's symmetry point with
  calibration error `ref_err`.
- Update rule: Gokmen-Vlasov stochastic pulse coincidence, BL = 31 slots per sample, update management (equal x and d stream
  scaling), up and down counts kept separate (asymmetry is never cancelled digitally), counts drawn Poisson with the exact mean,
  the pulses of one batch applied as uniformly interleaved (exact ODE solution). Per-sample semantics: the batch only groups
  samples whose pulses are summed.
- Weight scale: per layer, the init bound (Kaiming-uniform, gain 1 or sqrt 2) maps to 0.4 of the device range.
- Initial programming: closed-loop write-verify, exact to one step. Biases, LayerNorm and the LM's position table are digital
  (plain SGD, same lr).
- Algorithms: (1) plain SGD on the device; (2) **Tiki-Taka v2** (Gokmen 2021): gradient pulses go to array A; columns of A are
  read (ceil(in/period) per batch), H += lambda A_col (digital, in C-pulse units), C fires up to 31 pulses where |H| >= 1, H keeps
  the remainder; read A columns are reset to their symmetry point (aihwkit TransferCompound's reset option; the reset costs two
  pulse trains; its zero is off by `ref_err`). Forward uses C (gamma 0). TTv2 needs A's symmetry point: here it is the
  analytic u* of each device.
- FP baseline ("ideal digital float model"): the SAME network, data order, init and update rule with an exact float update
  (`ideal_float`, no bounds), checked equal to torch.nn.Linear + torch SGD to 7e-7. Context only: Adam on nn.Linear twins (LM).

Checks (`sim/test_memsim.py` -> records/TESTS.json): 8 checks, each shown to fail on a planted fault (9 faults: exact-update
sign, up/down swap, dropped BL, asymmetry ignored, symmetry-point sign, halved step, noise ~n not sqrt n, drift to 0 not bare, TT
transfer sign). Run before any sweep; all must pass and all faults must be caught.

## Tasks and budgets (fixed now)

| task | data (local, sha256-pinned) | model | budget |
|---|---|---|---|
| MNIST | H:/x1000/ep/raw/mnist (the canonical idx gz, digests in tasks.py); train 55k, val 5k (selection only), test 10k | MLP 784-256-128-10, tanh | 10 epochs, batch 128 (summed loss) |
| CIFAR-10 subset | cifar-10-python.tar.gz fetched ON THE POD from www.cs.toronto.edu (md5 c58f30108f718f92721af3b95e74349a checked; never on the desk); train = first 10,000 of batches 1-2, val next 2,000, test 10k | CNN 3 conv (32-64-64, 3x3, as crossbar matmuls over unfolded patches) + FC 1024-128-10 | 30 epochs, batch 128 |
| LM (human text) | enwik8 (Wikipedia 2006, sha256 2b49720e...; read-only from Cryptum's test corpus): train bytes 40,000,000-48,000,000, val 60,000,000-60,500,000 | byte-level transformer d128, 2 layers, 4 heads, ctx 128, all matrices incl. embedding and head analog | 3,000 steps x 32 x 128 bytes |

Learning rate: per task, the FP arm picks the lr with the best VALIDATION metric from a 3-point grid (MNIST {3e-4, 1e-3,
3e-3}; CIFAR {1e-4, 3e-4, 1e-3}; LM {3e-5, 1e-4, 3e-4}; per-sample, summed loss); every device run uses that lr. TTv2
hyperparameters (lambda in {0.3, 1, 3} x period in {16, 64}) are chosen ONCE on MNIST validation with a mid device that is
not in the catalog (n_states 128, asym 0.1, gamma 0.3, c2c 0.5, ref_err 0.02) and frozen for every task. No result on a test
split is ever used to choose anything.

## Sweeps (fixed now; SGD and TTv2 each)

MNIST (desk P2000, BelowNormal, 1 seed unless stated):
- A. states {16, 32, 64, 128, 256, 1024, 4096}, all else ideal.
- B. asym {0.01, 0.03, 0.1, 0.3} x states {64, 256, 1024}.
- C. gamma (up = down) {0.1, 0.3, 0.6, 1.0} x states {64, 256, 1024}.
- D. c2c {0.3, 1, 3} x states {64, 256, 1024}.
- E. drift tau {1e2, 1e3, 1e4, 1e5} batches at states 256.
- F. ref_err {0.01, 0.05} at states 256, asym 0.1, gamma 0.3.
- Catalog: the 7 entries x 3 seeds. FP: 3 seeds.

CIFAR and LM (one pod sitting): FP at the chosen lr (2 seeds) + Adam context (LM, 1); states {32, 128, 1024}; at states 1024:
asym 0.1, gamma 0.3, c2c 1 (one at a time); the 7 catalog entries; the MNIST joint minimum spec (below).

**The minimum spec** (per algorithm): from MNIST grids A-E take, per axis, the weakest grid value whose gap is < 2 pp at the
state count that passes; join them into one spec; verify it with 3 seeds; if it fails, tighten the axis whose single-axis gap was
largest by one grid step and re-verify (at most 3 rounds). The verified joint spec is run on CIFAR and LM; if it fails there, the
min spec is reported per task. The map: catalog points placed on the axes, each with its gap.

## Energy per update (`energy/energy.py` -> records/ENERGY.json; every input cited or labelled ESTIMATE)

"The same update" = one sample's rank-1 outer-product accumulation into one weight. GPU: the weight-gradient MAC (2 FLOP) at the
H100 SXM's energy per FLOP (700 W / 989 dense BF16 TFLOPS at 100 % and at 50 % utilisation) plus the optimizer's weight
read-modify-write amortised over the batch. Analog: device pulses per weight per sample (measured in the sims) x energy per
pulse, plus half-select line charging per active slot (slot occupancy measured in the sims) at the published gate voltage and
capacitance. Widrow's and the pencil-lead cells: plating charge per level x cell voltage. The advantage = GPU / analog.

## The pencil lead built today (an ESTIMATE, labelled as such everywhere)

0.5 mm HB lead, 20 mm immersed, bare ~5 ohm, plated ~0.5 ohm: a copper shell of ~0.39 um carries the extra 1.8 S, i.e. 0.33 C of
plating for the full range (Faraday). Central estimate: 100 usable levels, asym 0.1, gamma 0.3, c2c 0.5, d2d 0.2, drift: full
range lost in ~10 h in an aerated bath (tau 940 batches at 0.3 s per sample). The bench test (BENCH.md) measures these.

## Pod use

One sitting, at most 120 min, worst <= $2, the cheapest of A4000 / A5000 / 3090 in stock, through
ops/x1000-20261023/bench/devpod/devpod.py under grant G1 (--name-prefix altone-x1kme-, --program ALT-X1000); D80 checked from
F:/shared/LIVE-HOLDS.jsonl and List-Pods before the create; one line to each of the four sessions; F:/shared/UPLINK-PAUSE while
the payload uploads; collect, release, confirm by the listing.

## What would change the plan

A check that fails or a fault that is not caught stops the sweeps. A divergent FP run at the chosen lr stops that task. Any
deviation from this plan is written in DEVIATIONS.md with its reason before the affected run.
