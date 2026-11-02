# Release notes: v1.6

The code, records and pulse draws behind the paper "Can memistor-class electrochemical weights train neural networks?" (version 16, November 1, 2026). Cite the concept DOI 10.5281/zenodo.23748861
(all versions). v1.0 (October 28, 2026) held version 9 of the paper, v1.1 (October 29, 2026) version 11, v1.2 (October 29, 2026)
version 12, v1.3 (October 31, 2026) version 13, v1.4 (October 31, 2026) version 14, v1.5 (November 1, 2026) version 15.

v1.6 answers the thirteenth independent review, of v1.5 and version 15 (`paper/reviews/REVIEW-13-chatgpt-20261101-full.md`; the
response is `paper/RESPONSE-TO-REVIEW-13.md`). The review found each change of v1.5 implemented correctly, the fast reproduction passing
in the environment that exposed the v1.4 failure and no new substantive defect, and judged the paper ready to submit. No experiment
was run and no result changed.

- Self-test (the review's one optional finding): the negative control of `reproduce_all.py --policy-selftest` named "a change within the
  weight tolerance that changes a printed value" added a fixed 4e-5 to Li-ECRAM's `max_abs_mean_diff` and expected the printed
  four-decimal number to change; for another starting value the policy permits it would not change (the shift crosses no rounding
  boundary), so the self-test would fail although the policy is right. The control now takes its shift from the starting value
  (`printed_flip_value`: just across the nearest rounding boundary of the printed number, never farther than the weight tolerance), and
  `policy_selftest` can take other starting bytes, which the evidence script uses
  (`paper/records/revision14/POLICY-SELFTEST-FIX-R13.json`: over 150 starting values the new control always rejects the mutation, always
  changes the printed value and stays inside the tolerance; the old control left the printed value unchanged for 70 of them). The
  deposited reference value gives the same result as before.
- Paper version 16: the contribution statement counts all thirteen reviews (versions 1 to 7 and 10 to 15) instead of versions 1 to 7,
  the availability section names archive v1.6 and the thirteen reviews, and the abstract's last sentence no longer says that this version
  repairs the simulator; no other text changed (44 pages, as version 15). Version 15
  is archived (`paper/tex/v15`, `paper/build/v15`), with the scripts and check records of version 16 (`paper/revision15/`,
  `paper/records/revision15/`).

- 3731 files, 145.3 MB; `SHA256SUMS` covers every file. Pod session records (which hold account identifiers) are not included.
