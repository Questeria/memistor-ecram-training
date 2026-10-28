# Lane ME-REVISE: pre-registration of the revision runs (written 2026-10-26, before any revision run)

The paper (commit ef7e0630f) had an independent review (`RESPONSE-TO-REVIEW.md` answers it finding by finding). This plan fixes,
before any run, what the revision runs are, how they are analysed and which wording each outcome allows. Deviations go to
`DEVIATIONS-PAPER.md` as R1, R2, ... with what had been seen when each was made. The old records stay as they are, labelled
"original simulator".

## 0. The repaired simulator (desk-tested before any run)

`sim/memsim_rev.py`, `sim/run_rev.py`, `sim/tasks_rev.py` are copies of the paper's files with the repairs; the old files are
unchanged. `sim/test_rev.py` (8 checks, each shown to fail on the old behaviour or a planted fault) must pass on the desk and
again on every pod before its runs. The repairs:

1. Random streams (`--rng split`, the default of run_rev.py): logical init, data order, each tile's device population and the
   pulse/noise draws use separate generators. Every arm of a seed gets the same logical init and data order (checked by sha256
   recorded in every run). `--rng legacy` replays the old simulator bit for bit.
2. The A reset: `ideal` (the old jump to the symmetry point, charged 2 BL pulses: reported only as "ideal reset"), `pulse`
   (sign-directed pulse trains from the transfer's read toward the read zero, 2 read-correct iterations, at most 62 pulses per
   weight, through the device dynamics, charged as applied), `alt` (31 alternating up/down pairs through the device dynamics),
   `none`. **The repaired default for every reset-based TT run is `pulse`**, or `none` where the validation selection picks it.
3. The aihwkit presets (Li-ECRAM, MO-ECRAM) are mapped one to one onto aihwkit's LinearStepDevice (`bounds_model: aihwkit`,
   `sim/devices_rev.py`, `records/revision/CATALOG-REV.json`): shifted bounds, bound-scaled slopes, slope spread. The old field
   copies stay as `*_papermap`.
4. Clipping of the pulse probabilities is recorded per layer (fraction of updates clipped, lost update fraction).
5. Published-style TTv2 (single-pulse transfer, buffer forgotten after a transfer, no A reset) is available as a variant.
6. `recenter_sp`: the asymmetry sweep with the symmetry point held at mid-range (section 4).

## 1. The device-mapping check (sitting R1, before it is relied on)

On a pod only, aihwkit from PyPI (version recorded) runs its own `get_tile_for_plotting` + `compute_pulse_response` on
EcRamPresetDevice and EcRamMOPresetDevice, 500 devices, from w = 0: Li 1500 up, 3000 down, 3000 up, 2000 alternating; MO
10000 up, 20000 down, 20000 up, 6000 alternating; with and without cycle-to-cycle noise (`revision/aihwkit_curves.py`). The desk
runs our aihwkit-mode tile and the old papermap tile through the same schedules (`revision/compare_curves.py`).

- **Pass rule (the mapping is accepted)**: on the noise-free and the noisy schedule, at every stored pulse index, the mean
  difference is at most max(4 SE, 2 dw_min) (SE from both sides' sd over 500 devices), and over all stored indices the median
  ratio of across-device sd lies in [0.8, 1.25]; the mean maximum and minimum state reached agree within max(4 SE, 2 dw_min).
- If our aihwkit mode fails: R2 onward runs with the best mapping found by then, and the failure is reported, not hidden.
- The papermap is expected to fail the same rule; the size of its difference is reported.

## 2. The diagnostic, D1 (sitting R1): how much do the repairs move the old conclusions?

Old against repaired simulator, at the OLD selections (`records/CHOICES-PAPER.json`: FP-SGD learning rate, TT configurations),
seeds 0, 1, 2, on MNIST (the full 10-epoch budget) and a CIFAR-subset slice (the paper's subset and network at width 32, 10 of
the 30 epochs), devices protonic and Li-ECRAM (papermap), plus Li-ECRAM aihwkit-mapped. 117 runs per task (`sweep_rev.py
--phase d1`):

- old simulator (`run.py`): FP-SGD; per device SGD, TTv2, c-TTv2, AGAD;
- repaired streams with the ideal reset ("rev"): the same arms;
- repaired streams with the `pulse`, `alt` and `none` resets: TTv2, c-TTv2 per device; published-style TTv2 per device;
- Li-ECRAM aihwkit-mapped: SGD, TTv2 (pulse), c-TTv2 (pulse), AGAD;
- digital (ideal-device) TTv2, c-TTv2, AGAD.

Analysis (`revision/analyze_d1.py`), per cell the gap to the FP-SGD arm of the same simulator, paired by seed, mean and 95 %
t-interval (n = 3), the main-table label (PASS: the whole interval at or under the line; FAIL: the whole interval over it;
UNRESOLVED otherwise; lines 2 pp):

- the RNG effect = rev minus old; the reset effect = rev_pulse (and rev_alt, rev_none) minus rev (ideal); the mapping effect =
  aihwkit minus papermap (both repaired);
- **material** = a change of the mean gap by more than 1 pp (half the line), or a label change;
- the paired-gap sd under old and repaired streams (the variance a matched control should remove).

The diagnostic informs the wording; it does not change the main-run plan below, except that a material effect of the reset
makes "ideal reset" results unusable for any claim about devices (they stay as a labelled variant).

## 3. Selection (sitting R1, validation split, seed 0, repaired simulator)

- FP-SGD learning rate per task and width by the paper's edge rule (MNIST grid + 1e-2; CIFAR widths 16/32/64; LM 64/128/256).
- Adam learning rate per task (MNIST, CIFAR, LM, base widths), grid 3e-4, 1e-3, 3e-3 with the edge rule: Adam becomes a
  reported digital baseline for all three tasks.
- TT family on the mid device (as in E2): TTv2 = lane ME's 10-point grid x reset {pulse, none}; c-TTv2 = the 8-point grid with
  its reset option now {none, pulse}; AGAD the 8-point grid (no reset). Best by validation accuracy; S-ALGO and BEST-CHOPPED
  by the paper's tie rules.

## 4. The main runs (sittings R2..), repaired simulator, selections of section 3

- **E3 main table**: 3 tasks x 5 seeds x {FP-SGD, Adam, digital TTv2, digital c-TTv2, digital AGAD, 5 devices x {SGD, TTv2,
  c-TTv2, AGAD}} = 375 runs. Li-ECRAM and MO-ECRAM aihwkit-mapped; the others as in the paper's catalog.
- **E4 width**: CIFAR c = 16/32/64 and LM d = 64/128/256; arms protonic and Li-ECRAM x {TTv2, BEST-CHOPPED}; each arm's lr by
  the edge rule on validation (as E4); then **5 seeds** (was 3) per width at its own lr, FP-SGD at FP's lr.
- **E5 sensitivity** at the base sizes (CIFAR c = 32, LM d = 128), S-ALGO at FP's lr, protonic base, seeds 0, 1, 2, one axis at
  a time: levels 100/200/500/2000/5000; asymmetry 0/0.1/0.2/0.4 (as before: the symmetry point moves, u* = a/(2 gamma)); **the
  same asymmetries with the symmetry point held at mid-range (recenter_sp)**; gamma 0/0.5/1/2; c2c 0/1/2/4; reference error
  0/0.05/0.1/0.2/0.5; retention tau 1e5/1e4/1e3/1e2. 31 points x 2 tasks x 3 seeds = 186 runs. The FP reference is E3's FP-SGD
  of the same seed (same lr, same init and data order).
- Sittings: cheapest 24 GB card (A4000/A5000/3090, at most $0.30/h), at most two live pods, worst case at most $6 a sitting.

## 5. Pre-registered criteria

- **Main table (absolute lines)**: the gap to FP-SGD, paired by seed, n = 5, 95 % t-interval; PASS if the whole interval is at or
  under the line, FAIL if it is wholly over, else UNRESOLVED. Lines: MNIST and CIFAR 2 pp; LM 5 % in bits per byte. The same
  table is reported **against Adam** with the same lines. "Unresolved" is never reported as adequate.
- **Spec sheet (absolute)**: at each E5 point the same label with n = 3 against the absolute line (never relative to a base).
  A threshold per axis is the weakest grid value that PASSES with every value between it and the best end of the axis also
  passing; if the base point does not pass, the axis threshold is "not established". The signed weight range of each point
  (1 - u*, 1 + u* of the half range, for the paper's device model) is reported beside the asymmetry axes.
- **Width (equivalence)**: per arm, the endpoint contrast D = mean gap(widest) - mean gap(narrowest), Welch interval. Margins:
  CIFAR 2 pp, LM 5 % (the pass lines). EQUIVALENT if the 90 % interval of D lies inside (-margin, +margin) (TOST at 5 %);
  otherwise GROWS if the one-sided 95 % lower bound of D is above 0 (SHRINKS: the upper bound below 0); otherwise NO EVIDENCE
  OF GROWTH BEYOND THE MARGIN if the one-sided 95 % upper bound is under the margin; otherwise INCONCLUSIVE. "FLAT" is no longer used.
- **Energy**: reported as a conditional projection (section 6 of RESPONSE-TO-REVIEW.md); an energy ratio is printed only for
  cells that PASS against the stated baseline (energy to equal quality); cells that fail get "quality not reached". The
  inference-chip read efficiency (12.4 TOPS/W) and the system figure of the same chip (6.94 TOPS/W) are both reported.

## 6. Wording rules fixed now

- "near-digital" is not used. Results are stated against FP-SGD and against Adam in the abstract and the conclusion.
- A device result is stated with its reset (pulse or none); an ideal-reset result is always called "ideal reset".
- The protonic entry is "protonic-inspired"; the Widrow entry "an optimistic historical-device scenario".
