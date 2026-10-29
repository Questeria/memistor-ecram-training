# Response to the eighth independent review (ChatGPT, 2026-10-28), version 11 of the paper

The review (`reviews/REVIEW-8-chatgpt-20261028-full.md`) audited the public archive, release v1.0 (commit 076624fb, which holds
version 9), against version 10 (`build/v10/main-arxiv.pdf`, SHA-256 8660babf...a717f0). It cloned the release, ran the documented
CPU reproduction (24 of 24 steps; 53 files byte-identical and 14 identical after the stated normalisation; all 2,231 number macros
equal), ran the simulator suites (40 checks passed, 44 planted faults caught), recomputed the revised comparison statistics and the
draw statistics independently, and read the computational source. It reported seven minor and two cosmetic findings and none
that changes a conclusion.

Every finding was verified against the files before anything changed, and all nine are confirmed. No experiment was run, and no
number the paper prints changed. Cost: $0 (desk and WSL; no GPU, no pod).

| # | Finding (severity) | Verification | Change (version 11, archive v1.1) |
|---|---|---|---|
| 1 | Figure 3 draws `max(mean, 0.05)` with the bars of the true mean (minor) | Confirmed: `make_figures.py` line 81. `revision10/check_fig_main.py` re-runs the figure with the plotting call recorded. On version 10's code it finds exactly the review's two cells misdrawn: the LM c-TTv2 means of Li-ECRAM (-1.29 %) and Protonic (-0.84 %), drawn at +0.05 with shifted intervals. Table 19 prints the right values. | The mean itself is plotted (the axis is symmetric-log). Figure 3 is redrawn: all 60 cells are drawn at their mean, with bars ending at their interval. |
| 2 | Classification sample counts include the skipped incomplete batch, so the transfer reads are overstated (minor) | Confirmed: `sim/run_rev.py` line 162 and `sim/run.py` line 152 write `samples = n * len(hist)`, and `energy/energy_system.py` line 102 derived the steps from it. The records' own layer rows show 549,120 trained MNIST examples against 550,000 counted, and 299,520 CIFAR-10 examples against 300,000: +0.16 % steps. | `energy_system.py` counts a run's steps from its smallest layer row count (steps x batch, x ctx for the LM). `records/ENERGY-SYSTEM.json` and `records/revision/ENERGY-REVISION.json` are regenerated. The corrected totals equal the review's independent recomputation to 2.2e-16 relative, in all 60 of its entries. The largest change in a total energy is 4.8e-6 relative in the current projection and 1.4e-5 in version 1's. Every number file and every table regenerates byte-identical (`records/revision10/NUMBERS-FRESH.json`). The runners are not changed: `samples` is a field the runs wrote, and nothing reads it any more. |
| 3 | The optional ideal reset fails with AIHWKIT bounds and a partial column selection (minor) | Confirmed: `sim/memsim_rev.py` line 444 clipped the selected columns against the whole tile's bounds. The new check's planted fault, the old line, raises the review's exact error: `shape mismatch: value tensor of shape [3, 4] cannot be broadcast to indexing result of shape [3, 1]`. No result used this path, because it could not run. | `Tile.clip_cols` clips against the selected columns' own bounds. For a full selection, the only one that ever ran, it is the same operation. `sim/test_ideal_reset_cols.py` checks four transfers of one column each: each resets its own column only, inside that column's bounds and near its symmetry point, and charges 3 x 2 x 31 pulses. The check passes and the old line fails it (`records/revision10/TESTS-IDEAL-RESET-COLS.json`); `reproduce_all.py` runs it. |
| 4 | The LM sampler excludes its last valid window (minor) | Confirmed: `sim/run_rev.py` line 173 and `sim/run.py` line 162 draw `torch.randint(0, len(tr) - ctx - 1)`, whose upper bound is exclusive. The last start, `len(tr) - ctx - 1`, is never drawn, so the training slice's final byte is never a target. No held-out byte is involved. | Disclosed in Section 3 (methods) and in the history. The code is kept as it ran: a corrected bound draws other windows from the same seed, and the records could no longer be traced to the code. The archive's README lists it under "Known defects, kept as run". |
| 5 | The quick start leaves the shell in `paper/` (minor) | Confirmed: README line 47, then line 48. | The quick start has `cd paper`, the draw check and `cd ..` on separate lines, which works in cmd, PowerShell and bash. |
| 6 | "Every table" overstates what is regenerated: Table 12's file `rev_spec_p.tex` is kept as edited (minor) | Confirmed: README lines 48 and 106. The file is `rev_spec.tex` with one comment line and float placement [p]. | Coverage is now complete: `revision10/derive_rev_spec_p.py` derives the file from the regenerated `rev_spec.tex` byte for byte, and `reproduce_all.py` runs it after `revision/analyze_rev.py`. Every table of the paper is now regenerated and compared. |
| 7 | No copyable installation recipe (minor) | Confirmed. | A `requirements.txt` (numpy 2.5.2, matplotlib 3.9.2) and an "Install (CPU)" section, with torch 2.7.1 from PyTorch's CPU index: the set both clean-room runs used, on Python 3.13.15. |
| 8 | The README's size total is stale (cosmetic) | Confirmed: the deposit builder counted the size before it wrote README.md, VERIFY.json and the ENVIRONMENT addendum. | The builder counts it after every file is written, and rewrites README.md, RELEASE-NOTES.md and SHA256SUMS until the printed figures stop changing. |
| 9 | Figure 3's legend overlaps an axis label (cosmetic) | Confirmed: `check_fig_main.py` finds 11 overlaps between the legend and axis or tick labels in version 10's figure. | Space is reserved below the axis labels: 0 overlaps. The tick 10 is dropped, because it overprinted 5 and 20. |

On the review's limits:

- **Archive identity.** Before publishing, `git ls-remote` showed the GitHub tag v1.0 and `main` both at 076624fb (`PUBLISHING.md`). Zenodo's
  single file is GitHub's archive of that tag: 100,543,489 bytes, md5 8813e49b550ec91f3b7ee1dca166b074.
- **Version 10's sources.** Release v1.0 does not hold them. Release v1.1 does (`tex/v10`, `build/v10`), together with version 11's sources and
  outputs.

## Checks (records in `records/revision10/`)

- **Build:** version 11 built with `pod/build_payload_rev8.py` and its `run.sh` (tectonic 0.15.0, in WSL Ubuntu): 42 pages. The arXiv
  archive compiles alone, and the HTML is complete and clean (`BUILD-STEPS-v11.txt`).
- **Text against version 10** (`revision10/pdf_text_diff_v11.py`, giving `PDF-TEXT-DIFF-main.json` and `PDF-TEXT-DIFF-main-arxiv.json`):
  - Every differing hunk is an expected edit: the methods sentence, the availability section, Figure 3's tick labels and the history.
  - Two hunks are reflow: "embedding", which is no longer hyphenated, and the GitHub address, which now breaks after "github.com/".
  - One block is a pure move: appendix F's paragraph "Wording withdrawn or narrowed".
  - The page count is unchanged. The same check on version 9 against version 11 fails, as it must (`PDF-TEXT-DIFF-negative-v9-v11.json`).
- **Name** (`revision9/name_check_v10.py`, giving `NAME-CHECK-v11.json`): the author's account name appears only inside the GitHub mirror's
  address, as the owner allowed on 2026-10-28.
- **Numbers** (`revision8/check_numbers_fresh.py --selftest`, giving `NUMBERS-FRESH.json`): every `tex/numbers*.tex` equals its regeneration
  with the corrected energy model.
- **Figure 3** (`revision10/check_fig_main.py --selftest`, giving `FIG-MAIN-CHECK.json`) and **the reset** (`sim/test_ideal_reset_cols.py`,
  giving `TESTS-IDEAL-RESET-COLS.json`): see findings 1, 3 and 9.
- **Every earlier check:** `revision10/check_build_v11.py` runs `revision6/check_build_v7.py` and reads the records above
  (`ARTIFACT-CHECK-v11.json`).
- **Archive v1.1:** built by `make_deposit.py`; its clean-room reproduction and secret scan are recorded in the archive's `VERIFY.json`.
