# Release notes: v1.1

The code, records and pulse draws behind the paper "Can memistor-class electrochemical weights train neural networks?" (version 11, October 28, 2026). Cite the concept DOI 10.5281/zenodo.23748861
(all versions). v1.0 (October 28, 2026) held version 9 of the paper.

v1.1 answers the eighth independent review, a code audit and reproduction of v1.0 (`paper/reviews/REVIEW-8-chatgpt-20261028-full.md`;
the response, with each finding verified, is `paper/RESPONSE-TO-REVIEW-8.md`). No experiment was run and no number the paper prints changed.

- Figure 3 (`paper/make_figures.py`, `fig_main`): two negative LM means were drawn at +0.05 with shifted intervals, and the legend
  overlapped an axis label; both are corrected, and `paper/revision10/check_fig_main.py` checks every drawn mean and interval.
- Energy (`paper/energy/energy_system.py`): a classification run's optimizer steps are counted from the rows its layers trained (the
  records' `samples` field includes each epoch's skipped incomplete batch, +0.16 % steps); `ENERGY-SYSTEM.json` and
  `ENERGY-REVISION.json` are regenerated (largest change in a total energy 0.0014 %).
- Simulator (`paper/sim/memsim_rev.py`): the ideal reset of a partial column selection under AIHWKIT bounds no longer fails (no run used
  it); `paper/sim/test_ideal_reset_cols.py` covers it.
- `reproduce_all.py` now also regenerates Table 12's file (`paper/tex/tables/rev_spec_p.tex`, by `paper/revision10/derive_rev_spec_p.py`)
  and runs the two new checks, so every number file, table and figure of the paper is regenerated and compared.
- README: a quick start that runs as written, an installation recipe (`requirements.txt`), the known defects kept as run (the LM
  sampler's off-by-one), and a size computed after every file is written.
- Paper: version 11 (sources in `paper/tex/`, PDFs and HTML in `paper/build/`); versions 9 and 10 are archived (`paper/tex/v9`, `v10`;
  `paper/build/v9`, `v10`), with the scripts and check records of versions 10 and 11 (`paper/revision9/`, `paper/revision10/`,
  `paper/records/revision9/`, `paper/records/revision10/`).
- 3438 files, 129.4 MB; `SHA256SUMS` covers every file. Pod session records (which hold account identifiers) are not included.
