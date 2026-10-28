# Plan of revision 4 (version 5 of the paper), answering review 4: pre-registered before any recomputation

Lane ME-REVISE-4, 2026-10-27 (ET). Review: `reviews/REVIEW-4-chatgpt-20261027-full.md` (it read version 4, commit 5afeda818).
Its findings were checked against the records and the code first: `revision4/verify_findings_4.py` ->
`records/revision4/VERIFY-FINDINGS-4.json` (F1, F2, F3 CONFIRMED; six planted faults caught). This plan is committed before any
run or table of version 5. Deviations go to `DEVIATIONS-PAPER.md` as R8, R9, ... Cost: $0 (desk only: the free Quadro P2200 and
WSL; the P2000 is busy with another lane and is not used).

## 1. Finding 1: the A2-R comparison was not matched (experiment A2-M, desk P2200)

What the records show (VERIFY-FINDINGS-4.json F1): the pod's seeds 0-2 of MNIST MO-ECRAM SGD are matched triples (FP-SGD control,
surrogate, stream: equal `init_sha256` and `data_sha256`); the desk's stream runs (P2000) for seeds 0, 3 and 4 share neither
hash with the pod's runs of the same seed; `analyze_rev3.a2r()` joins by seed without checking. Same code (one commit of each
simulator file, older than both run sets) and the same torch build (2.7.1+cu126) on both. Cause: the installed torch's CUDA
random kernels size their grid from the GPU's multiprocessor count, and every drawn element's Philox subsequence follows the
grid, while the simulator's generators live on the GPU: one seed gives a different initialisation and MNIST example order on a
GPU of another size. So the 7.67 pp seed-0 difference is a different random realisation, not rounding, and v4's five-seed
numbers combine three matched and two unmatched pairs.

Experiment A2-M (`sim/sweep_rev4.py --phase a2m`, ME_RECORDS = `H:/x1000/memistor-paper/rev4/records`): on the P2200 alone,
seeds 0-4, each seed's three runs with exactly the E3 / A2 definitions (FP-SGD control, surrogate, `seq` on every analog layer;
learning rate 0.003, the same catalog and choices files, byte-equal to the repository's). 15 runs.

Analysis (`revision4/analyze_rev4.py`, written before the runs finish, checked on planted mismatches):
- A seed enters a matched comparison only if its three records carry equal `init_sha256` and equal `data_sha256` and the same
  GPU name; otherwise the analysis stops with an error naming the seed (no result is labelled matched). The check is shown to
  fail on v4's A2-R join.
- Primary: the P2200 cell at n = 5 matched: gaps of `seq` and of the surrogate against the same seed's FP-SGD control (mean,
  95 % t interval, label against the 2 pp line as everywhere), the paired change `seq` minus surrogate (mean, 95 % interval,
  material if |mean| > 1 pp). Secondary, unchanged: the pod's matched n = 3 result (Table rev3_fid).
- Descriptive: per seed, the pod's and the P2200's gaps side by side (seeds 0-2), as the spread between two random
  realisations of one seed, with no attribution.
- Prediction of the cause, checked: the P2200's hashes (multiprocessor count 10) equal across its own three arms per seed and
  differ from the A4000's (seeds 0-4) and the P2000's (seeds 0, 3, 4). If a P2200 hash equals the A4000's or the P2000's, the
  mechanism is withdrawn from the text and only "different random realisations" is stated.
- If A2-M cannot finish on the desk (an error that is not a code fault, or beyond 4 hours), the claim is narrowed instead:
  the five-seed result is removed, the matched n = 3 result stays with its UNRESOLVED labels.

Text: "GPU rounding alone" and "more sensitive to rounding than to the update model" are removed everywhere; v4's five-seed
numbers are named in Appendix F as an unmatched, mixed-hardware diagnostic superseded by A2-M; the desk probe runs of A1-P are
described as fresh training realisations (their probed states are not those of v3), not as "slightly different by rounding".

## 2. Finding 2: the draw files in the deposit

`PUBLISHING.md` and the availability paragraph list the 12 `.npz` draw files (portable path `draws/rev3/<name>` in the data
deposit, outside git) with their SHA-256 (from the probe records, re-hashed). `revision4/rebuild_draw_tables.py --draws DIR`
recomputes every probe statistic of Tables 6 and 7 from the arrays alone (the probe records supply only the names, hashes and
seeds), regenerates both tables and compares them byte for byte with `tex/tables/`; it is shown to fail on a perturbed draw and on
a wrong hash.

## 3. Finding 3: presentation

- Abstract: the 10-of-12 count is called a point-estimate count and the bootstrap counts are given; the review count is removed.
- Table 6 is split into a surrogate table and a `seq` table at footnotesize; Table 7 is set at footnotesize; the build logs each
  shrunk table's scale, and `revision4/check_build_v5.py` requires every logged table's printed size to be at least 7.5 pt.
- The "(95)" mark is stated to cover the excess and the gain interval only, not a joint 95 % guarantee for every line.
- Page 20's blank area: float placement checked on the v5 render.

## 4. Build and checks (desk, $0)

As v4: WSL Ubuntu, tectonic 0.15.0, `pod/build_rev3.sh` derivative for v5, v4 kept in `build/v4/` and `tex/v4/`. Checks: lint
(every macro defined), the revision-number check (HTML abstract digits equal the arXiv abstract's), no undefined reference or
citation, no overfull box, the archive compiles alone, the table-size check; the abstract generator refuses "rounding alone".
