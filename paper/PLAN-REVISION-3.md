# Lane ME-REVISE-3: plan for version 4 after review 3 (written 2026-10-27, committed before any recomputation)

Review 3 (`reviews/REVIEW-3-chatgpt-20261027-full.md`; the reviewer's files copied to `reviews/review-3-support/` with
`SHA256SUMS.txt`) reviewed version 3 (commit bec6f470c). `revision3/verify_findings_3.py` checked every finding against the
records and the code (`records/revision3/VERIFY-FINDINGS-3.json`, its own planted-fault self-checks all pass): findings 1-5 are
CONFIRMED; the minor points are recorded there. What had been seen when this was written: the v3 records and summaries
(`records/revision2/RESULTS-REV2.json`, `records/revision/RESULTS-REVISION.json`) and that verification; no new run.
Deviations go to `DEVIATIONS-PAPER.md` as R7, R8, ... with what had been seen. Cost: $0 (desk only: the P2000 GPU and WSL).
No pod and no cloud money; if a step turns out to need either, it stops and is reported instead.

## 1. Finding 1: the sequential reference, analysed paired (experiment A1-P, desk)

The v3 summaries kept no per-cell moments, so the paired floor cannot be recomputed from them. The three probe runs of
PLAN-REVISION-2.md section 2 (A1) are run again on the desk with a probe that keeps what a paired analysis needs.

- Code: `sim/run_rev3.py` imports `run_rev2.py` unchanged and replaces only its probe. The draws are made exactly as before
  (same generator seeding, same order: surrogate, `seq`, `slot` replaying `seq`'s firings). New per probe:
  - for `seq` against `slot`, the **paired floor** `sqrt(sum_cells var_r(seq_r - slot_r) / R) / ||mean slot||` and the paired
    excess `sqrt(max(0, err^2 - floor_p^2))` (err as before); the surrogate keeps the independent floor (its Poisson counts are
    drawn separately from the firings, so its draws are independent of `slot`'s);
  - uncertainty: B = 2000 bootstrap resamples of whole draws (the same draw indices for both methods of a pair; generator seed
    fixed), giving the 95th percentile of the excess and the 2.5/97.5 percentiles of the gain ratio `g(m)/g(slot) - 1`;
  - dependence (finding 4): per-pair Pearson correlations of the draws among cells sharing a row and among cells sharing a
    column, summarised without cancellation: the root-mean-square correlation over all pairs (computed exactly through the
    R x R Gram matrix of each row or column of standardised residuals; cells with zero variance excluded), the mean
    sign-aligned correlation `r_jk sgn(P_j) sgn(P_k)` (P the policy-expected update), the per-row (per-column) RMS values'
    median and maximum, and the v3 pooled signed statistic for continuity. The surrogate, whose cells are independent by
    construction, is the empirical null for the RMS at the same R (analytic value for Gaussian draws: 1/(R-1)); the
    **excess RMS** of a method is `sqrt(max(0, ms_method - ms_surrogate))`;
  - the draws themselves (float32, `.npz` per probe) under `H:/x1000/memistor-paper/rev3/draws/`, their SHA-256 in the summary.
- Draws: MNIST and CIFAR 16 as before; **LM 16 instead of 6** (deviation R7: six draws are too few for a bootstrap; cost is
  desk time only). Layers and update numbers as in A1.
- Checks, `sim/test_rev3.py`, each shown to fail on a planted fault: (a) noise-free devices: `seq` equals `slot` draw by
  draw, so the paired floor and the paired excess are 0 while the independent floor is not (fault: `slot` draws fresh
  firings, the paired floor must then be > 0); (b) a planted 10 % bias on `seq` is found by the paired excess (>= 0.08) on a
  case where the independent floor hides it (excess 0); (c) review 3's balanced-sign shared-line example: the RMS correlation
  is 1/3 within 0.01 while the pooled signed statistic is within 0.005 of -1/381 (fault: pooled normalisation in place of
  per-pair, the RMS check must fail); (d) the probe still does not perturb the surrogate run (metric and pulse counts equal
  with and without probes).
- Rules (the registered lines of PLAN-REVISION-2.md, unchanged; only the floor of `seq` changes):
  - `seq` **meets the registered lines** on a probe if |gain ratio - 1| <= 0.05, paired excess <= 0.05 and median variance
    ratio in [0.8, 1.25]. It is **within the lines at 95 %** if, in addition, the bootstrap 95th percentile of the excess is
    <= 0.05 and the gain interval lies within +-0.05. If `seq` does not meet the lines on any probe of a task, that task's A2
    comparison is reported as having no valid reference (the PLAN-REVISION-2.md rule).
  - The surrogate: the registered rule with its independent floor, now with the bootstrap bounds reported beside it.
  - The paper never calls `seq` "a valid reference" without the qualifier: it "meets the registered diagnostic lines" (and
    whether at 95 %), a diagnostic, not a demonstration of equivalence. It states `seq`'s noise approximation (write noise
    added once per sample at the pre-sample state, clipping per sample; the literal stream does both per pulse).
  - Dependence: the paper may call the shared-line correlation small only if the excess RMS correlation of `slot` is at most
    0.05 on every probe; otherwise it reports the numbers without that word. The v3 statistic is renamed "pooled signed
    normalised covariance" wherever it remains.
- The A1 table of v4 reports this run (the r6 summaries stay in the superseded appendix copy and the response). If the
  surrogate's verdict on any probe differs between r6 and this run, both are reported. The probe runs' metrics are compared
  with E3 as before (cross-hardware: the desk P2000 against the pod A4000).
- If the desk cannot finish A1-P (an error that is not a code fault, or a run beyond 6 hours), the claim is narrowed instead:
  "`seq` meets the lines" is withdrawn, A1/A2 stay bounded diagnostics, and the response says so.

## 2. The open A2 rerun: MNIST MO-ECRAM SGD with the explicit stream at five seeds (experiment A2-R, desk)

The v3 rule flagged this cell for a rerun (material: mean change -1.42 pp at n = 3). Run on the desk with the `seq` stream on
every analog layer (as A2), seeds 3 and 4 (the main table has five seeds), plus seed 0 again as a cross-hardware reproduction of
the pod record. Analysis: the cell at n = 5 (seeds 0-2 from the pod, 3-4 from the desk): the `seq` gap's mean, 95 % interval
and label against 2 pp; the paired change against the surrogate (mean, 95 % interval, material if |mean| > 1 pp). The paper
replaces "not validated against the explicit stream" by this result. If desk seed 0 differs from the pod's, the difference is
reported and the cell is marked as mixing hardware. Gated on section 1's rule for MNIST: if `seq` does not meet the lines on an
MNIST probe, A2-R is reported with that qualifier.

## 3. No-run corrections (from existing records)

- Finding 2: the A2 table gets each cell's surrogate and `seq` label at n = 3 (same seeds) with intervals. The text reports the
  one label transition (CIFAR Li-ECRAM c-TTv2 PASS -> UNRESOLVED), all mean-order reversals (two, both below the registered
  1 pp separation) and states "no material rank reversal under the registered rule" instead of preservation of the ranking
  and of the labels; the MO-ECRAM SGD cell is described with its n = 3 labels (UNRESOLVED on both arms) beside its n = 5 main
  label (FAIL). The abstract, results and limitations drop the preservation claim.
- Finding 3: "sub-margin growth" and "growth below or at the margin" are replaced everywhere (abstract, scale, discussion,
  roadmap, submission abstract) by: growth detected for protonic-inspired c-TTv2, its size relative to the 2 pp margin
  unresolved; growth beyond 2 pp not excluded for that arm or for Li-ECRAM TTv2. The verdict list of the analysis is not
  changed (it is correct); only the wording.
- Finding 4: wording as in section 1; if A1-P does not finish, the v3 statistic is renamed and the "small correlation" claim
  is withdrawn.
- Finding 5: Appendix F names version 3 and version 4 with what each answered; the availability list adds the revision 2 and 3
  plans, responses, `*_rev2.py`, `*_rev3.py`, `revision2/analyze_rev2.py`, `revision3/`; PUBLISHING.md names
  `pod/build_rev2.sh` (and the v4 desk build) and `revision2/make_abstract.py` correctly.
- Minor: the reset limitations bullet names its mean (macro-average over runs) and gives the pooled one beside it; the stale
  loose `tex/main-arxiv.bbl` is replaced by the build's.
- Numbers are generated: `revision3/analyze_rev3.py` -> `records/revision3/RESULTS-REV3.json`, `tex/numbers_rev3.tex`
  (macros `\RY...`), tables `tex/tables/rev3_*.tex`; text edits by `revision3/edit_tex_3.py` with named anchors, v3 tex kept
  in `tex/v3/`.

## 4. Build (desk, $0)

The desk has no TeX on Windows; the v3 build ran on a pod. v4 builds in WSL Ubuntu on the desk with the same tools the pod used
(tectonic 0.15.0 linux-musl, matplotlib 3.9.2, pypandoc_binary 1.13 in a venv under `H:/x1000/memistor-paper/rev3/`), by
`pod/build_rev3.sh` derived from `pod/build_rev2.sh`. v3's products are copied to `build/v3/` first. Checks: no undefined
reference or citation, no unexpanded macro or placeholder, no overfull box over 2 pt, the arXiv archive compiles alone, the
submission abstract regenerated by `revision2/make_abstract.py` and within arXiv's limit. Citations are re-verified only where
the text around a citation changed.
