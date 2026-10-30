# Release notes: v1.2

The code, records and pulse draws behind the paper "Can memistor-class electrochemical weights train neural networks?" (version 12, October 29, 2026). Cite the concept DOI 10.5281/zenodo.23748861
(all versions). v1.0 (October 28, 2026) held version 9 of the paper, v1.1 (October 29, 2026) version 11.

v1.2 answers the ninth independent review, a second audit and reproduction from the public archive (v1.1)
(`paper/reviews/REVIEW-9-chatgpt-20261029-full.md`; the response, with each finding verified, is `paper/RESPONSE-TO-REVIEW-9.md`).
No experiment was run.

- Width study (`paper/revision/analyze_rev.py`): the Welch interval now takes the t quantile at the Welch-Satterthwaite degrees of
  freedom; v1.0 and v1.1 rounded them down, which the plan does not state (deviation R9 in `paper/DEVIATIONS-PAPER.md`). One verdict
  changes: CIFAR, protonic-inspired c-TTv2, from inconclusive to grows (Table 11). The other Welch intervals move by at most 0.18 in
  their units, and the paired contrast is unchanged. `paper/revision11/test_welch_df.py` checks the quantile against closed forms,
  the records and the review's independent value, and fails with the df floored.
- Paper version 12: Section 4.4, the abstract, the discussion and the roadmap say that both contrasts detect that growth. Section 4.4
  says only the example order, not the initialisation, is shared across widths. Section 4.3 and Table 8 define the excess correlation
  as an excess in quadrature. Table 16 labels its version-1 values as superseded. The bibliography prints Jacobs-Gedrim with an ASCII
  hyphen.
- `reproduce_all.py`: `--sums` skips a `.venv` folder (the README's install puts one at the root); the Python minimum for the pinned
  environment is stated as 3.12; the Figure 3 check runs its self-test against version 10's code, now bundled
  (`paper/revision10/fixtures/make_figures_v10.py`), so the self-test needs no private history; the Welch test is a new step.
- The simulators' docstrings (`paper/sim/memsim_rev.py`, `paper/sim/memsim.py`, `sim/memsim.py`) no longer call the Poisson draw
  conservative, matching Section 3.2. `CITATION.cff` drops `date-released`, which gave the build date; GitHub and Zenodo record the
  release date. `REDACTIONS.md` says which internal context is kept as provenance.
- Paper: version 12 (sources in `paper/tex/`, PDFs and HTML in `paper/build/`, 43 pages); version 11 is archived (`paper/tex/v11`,
  `paper/build/v11`), with the scripts and check records of version 12 (`paper/revision11/`, `paper/records/revision11/`).
- 3491 files, 132.4 MB; `SHA256SUMS` covers every file. Pod session records (which hold account identifiers) are not included.
