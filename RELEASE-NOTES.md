# Release notes: v1.4

The code, records and pulse draws behind the paper "Can memistor-class electrochemical weights train neural networks?" (version 14, October 31, 2026). Cite the concept DOI 10.5281/zenodo.23748861
(all versions). v1.0 (October 28, 2026) held version 9 of the paper, v1.1 (October 29, 2026) version 11, v1.2 (October 29, 2026)
version 12, v1.3 (October 31, 2026) version 13.

v1.4 answers the eleventh independent review, a review of version 13 (`paper/reviews/REVIEW-11-chatgpt-20261031-full.md`; the
response, with each finding verified, is `paper/RESPONSE-TO-REVIEW-11.md`). No experiment was run and no result changed.

- Related work: Byun et al., "Device Specifications for Neural Network Training with Analog Resistive Cross-Point Arrays Using
  Tiki-Taka Algorithms" (Advanced Intelligent Systems 7(5), 2400543; doi 10.1002/aisy.202400543), verified against Crossref
  (`paper/revision13/cite_check_v14.py`, `paper/records/revision13/CITE-CHECK-v14.json`; `paper/records/CITE-CHECK.json` 49 of 49).
  Xu et al. (PubMed 42915660), named by the review, is the paper's existing reference xu2026; it now also appears in the roadmap.
- Energy (Section 5): the GPU equation E = 6 P / (F u) with every input range; the low end, 7.05 pJ, is 500 W at 43 %. Which digital
  costs of the Tiki-Taka family are inside the ratio (one ADC conversion and one buffer update per read weight) and which are not;
  the ratio is a per-operation, read-dominated figure, not energy to a quality.
- Wording: "exploratory device sensitivity analysis" (the subtitle, abstract, introduction, Section 4.5); one-at-a-time ranges do
  not bound joint deviations.
- Figure 1 (new): what is simulated as a device and what is digital, for SGD and the Tiki-Taka family
  (`paper/revision13/make_fig_arch.py`); `paper/revision13/check_fig_arch.py` checks it against the simulator. Both are steps of
  `reproduce_all.py`.
- Limitations and roadmap: a control ladder; computational follow-ups (full CIFAR and LM trajectories with correlated pulse streams,
  pulse-length and update-management comparisons, fair tuning of analog SGD).
- Correction history moved from Sections 3, 4.3, 4.4 and 4.5 into Appendix F.
- Paper version 14: 44 pages (version 13: 43); sources in `paper/tex/`, PDFs and HTML in `paper/build/`; version 13 is archived
  (`paper/tex/v13`, `paper/build/v13`), with the scripts and check records of version 14 (`paper/revision13/`,
  `paper/records/revision13/`).
- 3609 files, 138.8 MB; `SHA256SUMS` covers every file. Pod session records (which hold account identifiers) are not included.
