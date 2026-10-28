# Response to the third independent review (ChatGPT, 2026-10-27), version 4 of the paper

The review (`reviews/REVIEW-3-chatgpt-20261027-full.md`; the reviewer's own files are copied into `reviews/review-3-support/`,
with `SHA256SUMS.txt` over the copies as received) read version 3 (commit bec6f470c, `build/v3/main.pdf`, SHA-256
916ff34f...a3bc7, the hash the review quotes). Lane ME-REVISE-3 treated it as findings to verify, not instructions. Every finding
was first checked against the code and the saved records by `revision3/verify_findings_3.py`
(`records/revision3/VERIFY-FINDINGS-3.json`, with planted-fault self-checks). All five findings are CONFIRMED. `PLAN-REVISION-3.md`
was committed (010ec4f2f, pushed about 01:00 ET) before any recomputation, and the paired probe harness with its checks (48419a096)
before the desk runs. Deviation R7 is in `DEVIATIONS-PAPER.md`. The v3 sources are kept in `tex/v3/` and the v3 build in `build/v3/`.
Numbers below are copied from `records/revision3/RESULTS-REV3.json`, `tex/numbers_rev3.tex` or the files named. Cost: $0
(everything ran on the desk: the two Quadro GPUs and WSL; no pod).

| # | Finding | Disposition | Fix |
|---|---|---|---|
| 1 | The seq-vs-literal sampling floor ignores the pairing | CONFIRMED | Probes rerun on the desk with draws kept; paired floor, bootstrap bounds; seq's noise approximation stated |
| 2 | Training does not preserve all labels or the ranking | CONFIRMED | Both arms labelled at n = 3; the transition and both reversals reported; the open A2 rerun done |
| 3 | "Sub-margin growth" misreads the width interval | CONFIRMED | Reworded everywhere: growth detected, size against the margin unresolved, two arms not excluded |
| 4 | The correlation statistic pools signed covariances | CONFIRMED | Per-pair correlations (RMS, sign-aligned, per line) against an empirical null; claim withdrawn |
| 5 | Revision history and directions describe version 2 | CONFIRMED | Appendix F, availability list and PUBLISHING.md updated |

## 1. The pulse-reference comparison: CONFIRMED; reanalysed paired on new probes

Evidence: `sim/run_rev2.py` (line 121) computes the floor of every method against the literal stream as
`sqrt((sum var + sum var_slot) / R) / ||mean slot||`, while `seq` replays the literal stream's line firings (`keep_fire` /
`fire`); every one of the 12 v3 `seq` excesses is 0 although 7 raw relative differences exceed the 0.05 line; the summaries kept
no per-cell moments; the reviewer's 16-draw illustration reproduces exactly (independent floor 0.3651, excess 0; paired floor 0,
excess 0.20). The surrogate draws its Poisson counts separately, so the independent floor is the right one for it. The `seq` noise
approximation (write noise once per sample at the pre-sample state, clipping per sample) was in the code's docstring only.

Fix (experiment A1-P, `PLAN-REVISION-3.md` section 1): `sim/run_rev3.py` imports `run_rev2.py` unchanged and replaces only the
probe; it draws exactly as before and adds the paired floor (variance of the per-draw differences), bootstrap bounds over whole
draws (2000 resamples, same indices for both methods), the dependence statistics of finding 4, and the draws themselves
(`H:/x1000/memistor-paper/rev3/draws/`, 79 MB, SHA-256 in each probe record; not in the repository). `sim/test_rev3.py`: ALL_OK, 4
planted faults caught (literal stream with fresh firings; no planted bias; pooled normalisation; probe sharing the run generator).
The three probe runs were rerun on the desk (16 draws on every probe, R7). Results:

- `seq` meets its registered lines on **12 of 12** probes with the paired floor. The paired floor is 0.29-0.98 times the
  independent one and accounts for the raw differences (at most 0.224) up to an excess of at most 0.015. So the v3 conclusion
  survives the corrected analysis, but it is now a stated diagnostic: the bootstrap bounds stay within the lines on **6 of 12**
  probes (all MNIST probes, the LM embedding); on the CIFAR layers and the LM output layer 16 draws cannot exclude a mean
  discrepancy up to 0.286. The paper no longer calls `seq` "a valid reference"; it "meets our registered diagnostic thresholds".
- The surrogate meets its lines on 10 of 12 probes (the same two failures as in v3, the most clipped CIFAR output layer), its
  verdicts unchanged from v3 on every probe; its bootstrap bounds are within the lines on 1 of 12.
- The probe runs on the desk do not reproduce the pod's E3 records bit for bit (0 of 3; GPU generations round differently),
  so the probed states differ slightly from v3's. This is stated.
- v3's A1 table is kept, captioned as superseded, in Appendix F (`tables/v3s_rev2_probe.tex`).

## 2. Labels and ranking: CONFIRMED; reported as the registered result, and the open rerun done

Evidence (same seeds 0-2 on both arms): CIFAR Li-ECRAM c-TTv2 is PASS with the surrogate (-1.14 pp, [-3.89, 1.62]) and
UNRESOLVED with the stream (-0.62 pp, [-6.44, 5.20]); its difference interval [-3.26, 4.29] does not bound the change within 1 pp.
Two mean-order reversals exist (CIFAR Li-ECRAM / protonic-inspired c-TTv2, separation -0.29 to 0.84 pp; MNIST MO-ECRAM / protonic-
inspired AGAD, -0.02 to 0.12 pp), none above the registered 1 pp separation. MNIST MO-ECRAM SGD is UNRESOLVED on both arms at
n = 3 ([0.04, 28.15] and [1.27, 24.09] pp).

Fix: the A2 table (`tables/rev3_fid.tex`) gives both arms' gaps, intervals and labels; the text reports the transition, both
reversals ("no material rank reversal under the registered rule; the ranking as a whole is not preserved") and the n = 3 labels of
the SGD cell beside its n = 5 one. Abstract, results and limitations no longer claim preservation.

The open rerun of the material cell (experiment A2-R, `PLAN-REVISION-3.md` section 2) was done on the desk ($0): seeds 3 and 4 with
the stream, and seed 0 again as a reproduction. At five seeds the stream's gap is 11.04 pp [5.98, 16.10], FAIL, against
11.51 pp [4.88, 18.14], FAIL, with the surrogate; the paired change -0.47 pp [-2.86, 1.93] is not material. The FAIL label is
therefore confirmed under either update. The size of the change is not resolved: the desk's seed 0 reached 89.69 % against the
pod's 82.02 % (same configuration and seed; 7.67 pp from GPU rounding alone, against a seed standard deviation of 5.34 pp for
this cell), and with the desk's seed 0 the change is -2.00 pp (material; label still FAIL). The paper says this cell's outcome
is more sensitive to rounding than to the update model.

## 3. "Sub-margin growth": CONFIRMED; reworded

Evidence: protonic-inspired c-TTv2's paired 90 % interval is [0.146, 3.378] pp, which includes 2 pp; Li-ECRAM TTv2's is
[-1.529, 5.349]. Both upper bounds are at or above the margin. Fix (`revision3/edit_tex_3.py`, abstract, Section 4.4, discussion,
roadmap; the submission abstract is regenerated): "a paired analysis detects growth for protonic-inspired c-TTv2 without resolving
its size against the margin; for two arms (that one and Li-ECRAM TTv2) growth beyond the margin is not excluded". The verdict list
of the analysis was correct and is unchanged.

## 4. The correlation statistic: CONFIRMED; replaced, and the claim withdrawn

Evidence: `_offcorr` averages off-diagonal covariances and divides by one pooled variance. On the reviewer's shared-line model
(128 cells, p = 0.5, balanced signs) the code returns -0.0026 (exact -1/381) although every pair's |correlation| is 1/3; with
unequal cell scales it returns 0.0107, inside the quoted 0.011 bound, again with every pair at 1/3.

Fix: per-pair Pearson correlations over all pairs of cells sharing a row or a column, computed exactly through each line's R x R
Gram matrix: root-mean-square correlation, mean correlation aligned with the expected update's signs, per-line RMS, and the
surrogate (independent cells) as the empirical null at the same R (0.255-0.260; the Gaussian value is 0.258). On the new probes
the literal stream's RMS correlation exceeds that null by up to **0.345**, by more than 0.05 on 6 of 12 probes (all MNIST probes
and the LM output layer; sign-aligned mean up to 0.208), while the v3 statistic on the same draws stays within 0.020. The
"small correlation" claim is withdrawn: the paper now says the dependence is not small everywhere, that the surrogate does not
reproduce it, that the per-cell lines do not test it, and that A2 is the test of whether it matters for training. It remains
descriptive (no pass line), so no registered count depends on it.

## 5. History and directions: CONFIRMED; updated

Appendix F names versions 3 and 4 and what each answered; the availability list adds the revision 2 and 3 plans and responses,
`sim/*_rev2.py`, `sim/*_rev3.py`, `revision2/analyze_rev2.py` and `revision3/analyze_rev3.py`. `PUBLISHING.md`
(`revision3/edit_publishing_3.py`) now names `pod/build_rev2.sh` (v3) and `pod/build_rev3.sh` (v4) as the archive builders and
`revision2/make_abstract.py` / `revision3/make_abstract_v4.py` as the abstract generators, and adds `numbers_rev3.tex` to the list.
The stale loose `tex/main-arxiv.bbl` and `tex/main.bbl` are replaced by the v4 build's.

## Minor points

- The limitations bullet on the reset now names its mean (over runs, 67.00 steps) beside the pooled one (26.97).
- Length, Table 9's density and Figure 2's rotated labels: noted, not changed (presentation, not error); the new tables are fitted
  to the text width.

## Found while revising (not in the review)

- **The HTML of versions 2 and 3 dropped every revision number.** `pod/html_prep.py` gave pandoc only `numbers.tex`, so every
  `\RV`, `\RX` macro was silently removed (v3's HTML abstract carries 13 of the PDF abstract's 28 digits; `pod/html_check.py`
  saw only the 9 left inside math). `pod/html_prep_rev3.py` (derived by `pod/derive_build_rev3.py`) defines all four number files;
  `revision3/check_build_v4.py` now compares the abstract's digits between the HTML and the generated arXiv abstract and fails on
  the v3 HTML (planted fault). The v4 HTML passes (27 of 27).

## The build

Version 4 was built on the desk in WSL Ubuntu with the tools the pod used (tectonic 0.15.0 linux-musl, matplotlib 3.9.2,
pypandoc_binary 1.13): `pod/build_payload_rev3.py` (lint, including the `\RY` macros) and `pod/build_rev3.sh`. A trial build of the
unchanged v3 sources gave the same 37 pages first. `revision3/check_build_v4.py` -> `records/revision3/ARTIFACT-CHECK-v4.json`:
main, main-arxiv and the archive compiled alone each give 41 pages, no undefined reference or citation, no overfull box (0 pt), and the
HTML check passes; its own self-test catches each planted log fault. No citation key changed and `refs.bib` is unchanged, so the
citation check was not rerun. The submission abstract (`build/arxiv-abstract.txt`, 1,893 characters) is regenerated by
`revision3/make_abstract_v4.py`, which also refuses "sub-margin growth", "preserves the ranking" and "valid reference".

## What stays open

- Stream-level training for the convolutional layers and the LM (the LM is covered at update level only).
- `seq` against the literal stream at 95 % on the CIFAR layers and the LM output layer (more draws would narrow the bounds).
- Whether the shared-line dependence matters for training beyond the A2 cells.
