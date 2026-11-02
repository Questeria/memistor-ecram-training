# Response to the thirteenth independent review (ChatGPT, 2026-11-01), version 16 of the paper and archive v1.6

The review (`reviews/REVIEW-13-chatgpt-20261101-full.md`, pasted by the owner) audits release v1.5 (b5f86bed2) and version 15.
It closes the review round: the paper is **ready to submit**. It finds that each of the six changes of version 15 is implemented
correctly (its section 1), that the fast reproduction now passes in the environment that exposed the v1.4 failure, and no
result-changing error; it asks for no change to the paper. It lists one optional, low-severity problem in its section 5, and says the
release need not be held for it.

The review did not raise the paper's contribution statement; it was found stale while closing the round and is corrected in
version 16 (see "What is and is not changed"). No experiment was run, no pod was used and no result changed. Cost: $0 (desk).

## Finding

| # | Finding | Verdict | Evidence | Change |
|---|---|---|---|---|
| 1 | (optional, low) `policy_selftest()` in `reproduce_all.py`: the negative control "a change within the weight tolerance that changes a printed value" adds a fixed 4e-5 to Li-ECRAM's `max_abs_mean_diff` and expects the printed four-decimal number to change (0.0111 -> 0.0112). For another starting value the policy permits it would not change (deposited - 4e-5, then + 4e-5, still prints 0.0111), giving a false test failure. | **Confirmed** | `records/revision14/POLICY-SELFTEST-FIX-R13.json`. On the deposited value (0.011137, prints 0.0111) the old code passes. For starting values 4e-5 and 3e-5 below it, the full old self-test fails; over a sweep of 150 starting values that still print 0.0111, the old control left the printed value unchanged in 70 (and so wrongly accepted the mutation). | Fixed in `deposit-src/reproduce_all.py`, in archive v1.6: `printed_flip_value` computes the mutation from the starting value, as the nearest rounding boundary of the printed precision plus 1e-8 (never farther than the 5e-5 tolerance), applied to the field that sets the printed maximum. All other cases are unchanged. The new control rejects the mutation, changes the printed value and stays inside the tolerance for all 150 starting values, and the whole self-test passes for every valid starting value tried (shifts of -4e-5 to +1e-5). |

## What is and is not changed

- **No experiment, no pod, no number changed.** Version 16 has the same 44 pages and the same tables and figures as version 15; the
  word-count diff of the PDF text, version 15 to version 16, has eight expected edits and 0 unexplained in both variants
  (`records/revision15/PDF-TEXT-DIFF-main.json`, `-main-arxiv.json`); the control version 14 -> version 16 must fail, and does.
- **Contribution statement (both variants, `tex/body.tex`).** It said ChatGPT "reviewed versions 1 to 7 of this paper in turn", which
  counted only the first seven reviews. The reviews are: 1 to 7 of versions 1 to 7, 8 of version 10, 9 of
  version 11, 10 of version 12, 11 of version 13, 12 of version 14 and 13 of version 15 (each response names its version). It now
  reads "reviewed versions 1 to 7 and 10 to 15 of this paper in turn, thirteen reviews in all:". The availability section counts the
  thirteen independent reviews and lists `RESPONSE-TO-REVIEW-13.md`; it names archive v1.6 as holding version 16.
- **Abstract** (`tex/sec_abstract.tex`, both variants and `build/arxiv-abstract.txt`, 1,914 characters): the last sentence "This version
  repairs the simulator after independent reviews and reports how far each repair moved the original results." read as if each version
  repaired the simulator; it now reads "The simulator was repaired after independent reviews, and the paper reports how far each repair
  moved the original results." (`revision15/edit_16b.py`, the owner's instruction to fix anything stale).
- **Appendix F** (`tex/app_revision.tex`): version 15 is no longer "this paper"; a version-16 entry says what is above.
- **Archive v1.6** holds version 16, the fixed `reproduce_all.py` (the fix for finding 1) and the review and this response. The
  `--policy-selftest` negative control `printed_flip_value` is the only change to the archive's code; all other code, records and
  results are those of v1.5. Published v1.5 (b5f86bed2, Zenodo 10.5281/zenodo.23852922) is not changed.
- The fixed source for finding 1: `deposit-src/reproduce_all.py` (commit 389b1b305).
- Starting values that print a different number than the deposited one (for example +2e-5) make the "another environment's
  output" case fail legitimately, since the printed value then differs from that file's; they are not valid test beds and are listed
  as such in the evidence file.

## Next

Version 16 and archive v1.6 are staged, not published: the owner publishes v1.6 (GitHub release and Zenodo), then submits
version 16 to arXiv from the Desktop folder "memistor paper - arXiv submission (v16)" (step 0 of its `SUBMIT-TO-ARXIV.txt`
is publishing archive v1.6 first); then the identifier is recorded in `PUBLISHING.md` and `STATUS.json`.
