# Lane ME-PAPER: deviations from PLAN-PAPER.md

## D1 (2026-10-25 about 21:05 ET): an added, descriptive "degradation" spec sheet beside the pre-registered one

What I had seen when I wrote this:

- E5's one-at-a-time records, seed 0, from sitting S3.
- Sitting S4 (second seeds, joint spec, pairwise) was running; none of its results had been seen.

What the data show:

- With S-ALGO = TTv2 at the FP learning rate, the protonic base device's own gap is already at or above the line at several sizes.
  On CIFAR it is 4.0, 2.2 and 7.3 pp at c = 16, 32 and 64. On the LM at d = 256 it is 16 %.
- The pre-registered rule then reads "base fails". It looks for improvements that pass, and most axes come out "not reachable
  on this grid".
- At the base size the CIFAR gap of the base device sits within one seed's noise of the line: the FP seed standard deviation
  is about 1.4 pp.

The pre-registered table is reported unchanged. Beside it, I add one descriptive analysis, labelled as added after the
one-at-a-time data were seen:

- **The degradation threshold.** Per size and axis, it is the weakest grid value whose gap exceeds the base device's own gap by
  less than X (2 pp CIFAR, 5 % LM), with every value between it and the base also inside that band.
- It uses the same function as the pre-registered rule, applied to the gaps minus the base gap.
- It answers the question a device maker asks: how far can each parameter move from a protonic-like device before training
  degrades.

No runs are added, removed or changed by D1.

## R1 (2026-10-26 about 01:15 ET, revision): the selection (PLAN-REVISION.md section 3) runs on the desk P2000, not a pod

What I had seen: no revision result (the diagnostic sitting r1d1 was still waiting for a card).

Why: the director's pod-slot rule of 01:10 ET (X1000 at most 3 live pods; two RECIPES pods and r1d1 hold them), so the
second pod (r1sel) was stopped before any create (no stock had been quoted; nothing was rented). The desk P2000 was idle.
The selection runs (sweep_rev.py fplr, then e2) are the same runs on a different GPU (each record names its device); the
rule, the grids and the seed are unchanged.
- Addendum (01:14 ET): CIFAR-10 is not on the desk (it is fetched md5-pinned by each pod), so the CIFAR FP-SGD and Adam
  selections failed on the desk without a record; they run on the next pod (sweep_rev.py fplr again: the MNIST and LM
  selection records travel in the payload and are not re-run).

## R2 (2026-10-26 about 06:40 ET, revision): the "digital TT" arms are replaced by TT on an ideal 1000-level device

What I had seen: the E3 records of sitting r2 (all 375 runs), including the three "digital" TT arms (FP arm, exact float
update, TT algorithm), which reach chance-like accuracy (MNIST about 45 %, CIFAR about 23 %, LM about 4.5 bits per byte).

Why: with the exact-update spec the nominal step is 2 / 1e9, so a TTv2 transfer of at most 31 nominal steps moves C by about
6e-8 per weight: C never leaves its initialisation (a 0.1-scale desk check: 11.1 % against 73.4 % on an ideal device). The arm
was defined wrongly, not run wrongly. Its algorithm-only purpose is served instead by every algorithm (SGD, TTv2, c-TTv2,
AGAD) on an ideal device: symmetric, constant step, 1000 levels, no noise, no spread, no reference error (sweep_rev.py
e3ideal, 60 runs, sitting r3). The digital arms' records are kept and reported as an invalid arm definition; they enter no
table. The D1 "rev_digital" cells have the same defect and are dropped from the D1 table.

## R3 (2026-10-26 about 12:00 ET, revision): a second sensitivity sheet with c-TTv2, beside the pre-registered S-ALGO sheet

What I had seen: the E3 main table and E4, not any E5 result (16 of the 186 E5 runs exist on the desk; I have not opened them).
In E3, S-ALGO (TTv2, chosen on MNIST validation by the pre-registered rule) FAILS on CIFAR on every published device with the
pulse reset, and the protonic-inspired base with TTv2 is UNRESOLVED on the LM. Under the absolute rule a sheet whose base point
does not pass yields "not established" on every axis, which says nothing about the algorithm that does pass.

Change: the pre-registered E5 (S-ALGO = TTv2) runs and is reported unchanged. Beside it, the same grid, seeds and rule run with
c-TTv2 (the pre-registered BEST-CHOPPED), via ME_E5_ALGO=cttv2 (sweep_rev.py e5, records named ...__cttv2__...). It is labelled
as added after E3 was seen.

## Note (2026-10-26 about 14:50 ET, revision): PLAN-REVISION.md section 4 miscounts E5

The plan lists the E5 grid exactly as run but counts it as "31 points ... 186 runs". The listed grid has 30 points (the base,
5 + 4 + 3 + 4 + 4 + 5 + 4 values), so 180 runs per sheet. No run was added or dropped; only the plan's arithmetic was wrong.

## R4 (2026-10-26 about 19:50 ET, revision 2): the width contrast is also reported paired by seed

What I had seen: all E4 records and the registered Welch verdicts (v2), and review 2's paired recalculation (finding 2), which
`revision2/verify_findings_2.py` reproduces from the records (`records/revision2/VERIFY-FINDINGS-2.json`, F2).

Why: PLAN-REVISION.md section 5 registered a Welch interval for D = mean gap(widest) - mean gap(narrowest), which treats the two
widths' seed samples as independent. They are not: every arm of a seed shares the logical initialisation and the data order
across widths (one data hash per seed, checked). Change: the registered Welch result is reported unchanged as the registered
result; beside it, the contrast of the per-seed differences (paired t, n = 5, 90 % interval, the same decision order) is
reported as a sensitivity analysis added after the review (`revision/analyze_rev.py` width_paired; the width table carries both).
It changes one verdict: protonic-inspired c-TTv2 on CIFAR, INCONCLUSIVE (Welch) to GROWS (paired, an interval that still
includes the 2 pp margin). No run is added or changed.

## R5 (2026-10-26 about 19:50 ET, revision 2): the fixed-symmetry sweep omitted its zero point and borrowed an unrecentred anchor

What I had seen: the E5 records (v2) and review 2's finding 4.

- PLAN-REVISION.md section 4 lists the asymmetries 0/0.1/0.2/0.4 and asks for "the same asymmetries with the symmetry point held
  at mid-range". `sim/sweep_rev.py` ran the held-symmetry sweep at 0.1, 0.2 and 0.4 only: the zero point was omitted. The Note of
  14:50 ET above therefore misdescribed the difference between the plan's 31 points and the 30 executed as a miscount; one
  planned point (asym_fixedsp 0) was not run. Zero global asymmetry does not make the two sweeps identical, because each device's
  own asymmetry spread remains and only the held-symmetry sweep re-centres each device.
- `revision/analyze_rev.py` used the ordinary `base` runs (recenter_sp false; nominal range [-1.125, +0.875]) as the held-symmetry
  anchor at 0.05 and printed the held-symmetry threshold 0.05 from them. That anchor was the wrong intervention.
- Change (pre-registered in PLAN-REVISION-2.md section 3 before any run): the recentred base (0.05) and the zero point are run as
  phase `e5fix` (24 runs); the analysis no longer substitutes the base (the axis is "not established" without its own anchor
  run), and the v2 claim stands or falls by the kill line of PLAN-REVISION-2.md.

## R6 (2026-10-26 about 21:20 ET, revision 2): experiments A2 and B finish in a second sitting

What I had seen: sitting r6's step log and the run counts only (no metric of a fid or e5fix run had been opened). The CIFAR fetch
took 13 minutes and the seq-stream runs ran slower than estimated, so the sweep's deadline left 17 of the 36 `fid` runs and 12 of
the 24 `e5fix` runs unstarted (all three `fidprobe` runs finished). Change: sitting r7 runs the same phases with the finished
records in its payload (the executor skips them), on the same card class with the same code and seeds. No run, rule or line of
PLAN-REVISION-2.md changes.

## R7 (2026-10-27 about 01:00 ET, revision 3): the update probes are rerun on the desk with 16 LM draws, analysed paired

What I had seen: review 3 and `records/revision3/VERIFY-FINDINGS-3.json` (the v3 probe summaries, which kept no per-cell
moments); no result of the rerun. The A1 probes of PLAN-REVISION-2.md are run again (experiment A1-P of PLAN-REVISION-3.md,
committed before the run) on the desk's Quadro P2000 instead of a pod, with the same runs, layers, update numbers and probe
seed, and with 16 draws on the LM probes instead of 6 (six draws are too few for the bootstrap over draws that review 3 asks
for). The registered lines do not change; the floor of the per-sample stream becomes the paired one, and bootstrap bounds are
reported beside every point estimate. The v3 (r6) probe summaries remain in the records and are compared in the response.

## R8 (2026-10-27 ET, revision 4): the table-size check binds the body's tables; the spec sheet is placed [p]

What I had seen: the A2-M result and the first v5 build. PLAN-REVISION-4.md section 3 said every table set through `\fitbox`
must print at 7.5 pt or more. In the first v5 build every body table does (the split probe tables print at 9 pt), but two
appendix tables reproduced unchanged from version 1's record (Appendix E, Tables 20 and 24) print at 6.37 and 7.12 pt; review 4
did not raise them, and re-laying out the original record is out of this revision's scope. `revision4/check_build_v5.py`
therefore enforces the 7.5 pt line on tables printed before the first appendix page (read from the build's .aux) and reports the
appendix tables (`appendix_below` in `records/revision4/ARTIFACT-CHECK-v5.json`). Also, the plan named only a check of page 20's
blank area; the fix needed is in `revision4/edit_tex_4b.py`: the sensitivity sheet is input at the start of Section 4.5 from
a derived copy placed `[p]` (`tex/tables/rev_spec_p.tex`); two intermediate builds that only moved it, or only changed the
placement, left the blank page (`revision4/page_fill.py`; final: no body page below 0.45 text cover).
