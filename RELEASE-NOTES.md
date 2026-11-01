# Release notes: v1.5

The code, records and pulse draws behind the paper "Can memistor-class electrochemical weights train neural networks?" (version 15, November 1, 2026). Cite the concept DOI 10.5281/zenodo.23748861
(all versions). v1.0 (October 28, 2026) held version 9 of the paper, v1.1 (October 29, 2026) version 11, v1.2 (October 29, 2026)
version 12, v1.3 (October 31, 2026) version 13, v1.4 (October 31, 2026) version 14.

v1.5 answers the twelfth independent review, an audit of v1.4 and version 14 that recomputed the statistics and the energy accounting
from the records and ran the fast reproduction (`paper/reviews/REVIEW-12-chatgpt-20261031-full.md`; the response, with each finding
verified, is `paper/RESPONSE-TO-REVIEW-12.md`). No experiment was run and no result changed.

- Reproduction (finding A): under Python 3.12 with torch 2.7.1+cpu, `reproduce_all.py` ended REPRODUCE_FAILED because
  `paper/records/revision/AIHWKIT-COMPARE.json`, which re-simulates long float32 pulse sequences on the CPU, differed in 26 float
  fields (largest change 5.7e-6 weight units; every boolean and printed value unchanged). The author reproduced it (Python 3.12.3,
  torch 2.7.1+cpu, WSL; the same 26 fields, `paper/records/revision14/AIHWKIT-COMPARE-py312.json`). `reproduce_all.py` now compares
  that one file under a stated numeric policy: the same structure, keys, strings, integers and every acceptance boolean; floats within
  absolute tolerances (5e-5 weight units, 5e-3 tolerance units, 1e-4 for the spread ratio; each about ten times the largest change seen
  and at most a tenth of the margin it could erode); the values the paper prints from it identical. A new step,
  `reproduce_all.py --policy-selftest`, shows another environment's output passing and a flipped boolean, a discrepancy pushed past its
  line, a renamed or removed key, a changed printed value, string, integer type or exact field each failing; the clean room adds two
  mutation tests of the same kind. README section "Reference environment" names the environment in which every file is byte-identical.
- Figure 1 (finding B): it now shows the selected settings (TTv2 and c-TTv2 reset A with pulses, AGAD does not; TTv2 has no chopper,
  c = 1), with a key, and its caption says so (`paper/revision14/make_fig_arch.py`). Its check, `paper/revision14/check_fig_arch.py`,
  reads the settings from `paper/records/revision/CHOICES-REVISION.json` and every main-experiment record (90 device records per
  algorithm) and builds the simulated layers in those configurations, where version 14's check used the pulse reset for all three; it
  catches eight planted faults, AGAD drawn with the pulse reset among them.
- Related work (finding C): Agarwal et al. (2016) now comes before Byun et al. and is said to concern conventional (SGD) training.
- Statistics (optional cleanup 2): the ordinary and paired intervals take the exact t quantile (`paper/revision/analyze_rev.py`), as the
  Welch interval already did. 16 interval endpoints in Tables 4 and 5 move by 0.01; no PASS/FAIL/UNRESOLVED label and no other printed
  number changes (`paper/records/revision14/VERIFY-FINDINGS-12.json` lists each).
- Energy (optional cleanup 1): Section 5 states that the pulse reset's extra reads carry the buffer allowance although they do not
  update H, a conservative approximation worth at most 0.15 % of the analog energy; the model and its output are unchanged.
- Paper version 15: 44 pages (as version 14); sources in `paper/tex/`, PDFs and HTML in `paper/build/`; version 14 is archived
  (`paper/tex/v14`, `paper/build/v14`), with the scripts and check records of version 15 (`paper/revision14/`,
  `paper/records/revision14/`).
- 3671 files, 142.1 MB; `SHA256SUMS` covers every file. Pod session records (which hold account identifiers) are not included.
