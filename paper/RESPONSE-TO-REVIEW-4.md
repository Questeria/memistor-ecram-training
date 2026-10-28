# Response to the fourth independent review (ChatGPT, 2026-10-27), version 5 of the paper

The review (`reviews/REVIEW-4-chatgpt-20261027-full.md`) read version 4 (commit 5afeda818, `build/v4/main.pdf`, SHA-256
824bbc1c...7feaf, the hash the review quotes). Lane ME-REVISE-4 treated it as findings to verify, not instructions. Every finding
was checked against the code and the saved records by `revision4/verify_findings_4.py` (`records/revision4/VERIFY-FINDINGS-4.json`,
six planted faults caught). All three findings are CONFIRMED. `PLAN-REVISION-4.md` was committed (77a73540a, pushed) before any
run. Deviation R8 is in `DEVIATIONS-PAPER.md`. The v4 sources are kept in `tex/v4/` and the v4 build in `build/v4/`. Numbers
below are copied from `records/revision4/RESULTS-REV4.json`, `DRAW-REBUILD.json`, `ARTIFACT-CHECK-v5.json`, `PAGE-FILL-v4-v5.json`
or `tex/numbers_rev4.tex`. Cost: $0 (desk only: the Quadro P2200 and WSL; no pod; the busy P2000 was not used).

| # | Finding | Disposition | Fix |
|---|---|---|---|
| 1 | "GPU rounding alone" is unsupported; the five-seed A2-R join mixes matched and unmatched pairs | CONFIRMED (cause found) | Matched rerun A2-M on one GPU; the analysis refuses unmatched seeds; rounding claim removed; v4's five-seed figures withdrawn |
| 2 | The release recipe omits the 12 pulse-draw files | CONFIRMED | Files, sizes and SHA-256 in PUBLISHING.md and the availability list; a command rebuilds the probe tables from them byte for byte |
| 3 | Presentation: small table type, page-20 blank, unqualified abstract count, "two reviews" | CONFIRMED | Probe table split (9 pt), point-estimate count with bootstrap count, review count removed, blank page removed |

## 1. The cross-machine rerun: CONFIRMED; the cause found, the cell rerun matched

Evidence. The pod's seeds 0-2 of MNIST MO-ECRAM SGD are matched triples (FP-SGD control, surrogate, stream: equal
`init_sha256` and `data_sha256`). The desk's stream runs of seeds 0, 3 and 4 (Quadro P2000) share neither hash with the pod's runs
of the same seed, and `revision3/analyze_rev3.py`'s `a2r()` joined by seed without checking. So v4's five-seed result combined
three matched pairs with two unmatched ones, and the 7.67 pp seed-0 difference was not "GPU rounding alone".

Why the hashes differ (not the code, not the library). Each simulator file has one commit, older than both run sets, and both
sets record torch 2.7.1+cu126. The installed torch's CUDA random kernels size their grid from the GPU's multiprocessor count
(`include/ATen/native/cuda/DistributionTemplates.h`, `calc_execution_policy`, lines 49-59: `multiProcessorCount`,
`maxThreadsPerMultiProcessor`, `counter_offset`), and the Philox subsequence of every drawn element follows the grid. The
simulator's generators live on the GPU (`sim/memsim_rev.py`, `Streams`), so one seed draws another initialisation and another
`torch.randperm` example order on a GPU of another size. Consistent with this, the probe runs' CIFAR and LM example orders are
equal between the A4000 and the P2200, while all initialisations and the MNIST order differ. Prediction, checked by the rerun:
the P2200 (10 multiprocessors, measured) gives hashes equal across its own three arms and different from both the A4000's and the
P2000's for every seed (`prediction_holds: true`).

Fix: experiment A2-M (`sim/sweep_rev4.py`, 15 runs on the P2200). Each of seeds 0-4 trained the control, the surrogate and the
stream with the E3 / A2 definitions. `revision4/analyze_rev4.py` admits a seed only if its three records carry equal
`init_sha256`, equal `data_sha256` and the same GPU. Its self-test refuses v4's join ("seed 3: init_sha256 differs"), a planted
init, data or device mismatch, and a missing control, and accepts the pod's seeds 0-2. Results at five matched seeds on one GPU:

- stream gap 8.73 pp [6.82, 10.65], FAIL; surrogate gap 8.71 pp [7.02, 10.40], FAIL;
- paired change 0.02 pp [-0.47, 0.52], not material; the interval lies within +/-1 pp.

The FAIL label therefore holds under either update at five matched seeds. The pod's matched three seeds (change -1.42 pp
[-4.84, 2.00], both arms UNRESOLVED at n = 3) stay as the secondary result. The two GPUs' realisations of one seed differ in gap
by up to 9.97 pp, so the paper now says that this cell's gap depends strongly on the realisation, and that the update's effect
is measured only by paired comparisons within a matched set. "GPU rounding alone" and "more sensitive to rounding than to the
update model" are gone from the paper. The abstract generator and the build check refuse them. v4's five-seed figures (11.04 pp;
change -0.47 pp) are named in Appendix F as withdrawn, an unmatched mixed-hardware diagnostic. The desk probe runs of A1-P are now
described as fresh training realisations, with a different initialisation from E3's (and, on MNIST, a different order). The
comparison within each probe is unaffected, since all three updates start from one saved state.

## 2. The draw files: CONFIRMED; listed, hashed and made usable

Evidence: all 12 `.npz` exist under `H:/x1000/memistor-paper/rev3/draws/` (81,905,772 bytes) and match the SHA-256 in their
probe records. Neither PUBLISHING.md nor the availability paragraph named them.

Fix: PUBLISHING.md (`revision4/edit_publishing_4.py`) lists each file with its size and SHA-256 (read from the re-hash, not
typed), under the portable deposit path `draws/rev3/<name>`, and gives the command
`python -B revision4/rebuild_draw_tables.py --draws draws/rev3`. That script uses only the arrays, plus each probe record's
file name, hash, layer, update and bootstrap count. It recomputes every statistic of the three probe tables with the probe's own
functions and bootstrap seeds, on the CPU. It regenerates the tables and compares them with `tex/tables/` byte for byte: all
three are identical, and the largest relative difference from the recorded values is 7.7e-12. Its self-test fails on a
perturbed draw and on a wrong hash. The availability section lists the draws and this command; the arXiv archive does not need them.

## 3. Presentation: CONFIRMED; changed

- Table 6 (8 pt type shrunk to 6.82 pt) is split into Table 6 (surrogate) and Table 7 (stream), both footnotesize. The
  dependence table (now 8) is footnotesize too. Measured on the PDF (`revision4/page_fill.py`), v4's pages 17-18 had a smallest
  type of 6.82 and 7.18 pt, as the review says; v5's are 8.97 pt. Every `\fitbox` now logs its scale, and
  `revision4/check_build_v5.py` requires every body table to print at 7.5 pt or more. Two appendix tables of version 1's
  record print smaller and are reported, not changed (R8).
- The "(95)" mark is now defined in both captions as covering the excess's 95th percentile and the gain interval only, "not a
  joint 95 % guarantee for every line".
- Abstract: "meets preset point-estimate lines on 10 of 12 probes (bootstrap: 1)"; "after independent reviews" (no count).
  1,918 characters.
- The blank area (v4 page 20, text cover 0.07) was the sensitivity sheet, input after Section 4.5's last paragraph and held to a
  page of its own by the section barrier. It is now input at the start of the subsection from a `[p]` copy (R8). v5 has 41 pages
  and no body page under 0.45 text cover.

## The build

Built on the desk in WSL as v4 (tectonic 0.15.0): `pod/build_payload_rev4.py` (lint with `\RZ` macros) and `pod/build_rev4.sh`,
derived by `pod/derive_build_rev4.py`. `revision4/check_build_v5.py` -> `records/revision4/ARTIFACT-CHECK-v5.json`: main,
main-arxiv and the archive compiled alone each give 41 pages, with no undefined reference or citation and no overfull box. The
HTML check passes. The revision-number check passes: the HTML abstract has 28 of 28 digits, and v3's HTML still fails it. The
table-size and withdrawn-phrase checks pass, and the self-tests catch each planted fault. No citation changed. `build/main.pdf`
SHA-256 begins 1d4cfb3c6d8d8fa0.

## What stays open

- Stream-level training for the convolutional layers and the LM; `seq` at 95 % on the CIFAR layers and the LM output layer.
- Cross-machine replay: the generators stay on the GPU, so a seed is reproducible only on a GPU of the same size. Portable
  initial tensors and orders would need a simulator change (not made: it would change every earlier record's stream).
