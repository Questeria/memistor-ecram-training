# Redactions in this deposit

Privacy defaults, set by the author's team before the first release; the owner may reverse them in a later release.

**The unredacted originals are kept by the author.** They are not part of this deposit. The "original" digests below identify them.

What was redacted: only the deposit's copies of the independent reviews (`paper/reviews/*.md`), of the reviewer's own support files for
review 3 (`paper/reviews/review-3-support/*`) and, for the first rule only, of `paper/RESPONSE-TO-REVIEW.md`. These files quote local file
links and paths of the author's computer. Nothing else was changed for privacy: no run record, no paper source, no archived version of the
paper, no code. The reviews' own words are unchanged; only the path text inside links, quoted paths and JSON keys was shortened.

| Rule | What was shortened or removed | Occurrences |
|---|---|---|
| P0 | the author's computer account name inside local link targets (`C:/Users/<account>/...` became `C:/Users/<user>/...`) | 34 |
| P1 | the author's private project path up to and including the study folder (`C:/Projects/<private repository>/ops/<private folder>/phase2/memistor/`) removed, leaving the study-relative path: `<that prefix>paper/records/X` became `paper/records/X` (in JSON keys and Python strings the same prefix with `\\` separators) | 1085 |
| P2 | the reviewer's local output folder (`C:/Users/<user>/.codex/visualizations/<date>/<id>/paper-review[-vN]/`) shortened to `paper-review[-vN]/` (the folder in which the reviewer saved its check files) | 33 |
| P3 | the author's draws folder on drive H: replaced by this deposit's own `paper/draws/rev3` | 1 |
| P4 | the author's desk folder on drive H: (`H:/<desk folder>`), which review 9 names in its list of internal paths | 2 |
| P5 | the private prefix of the records' machine-readable namespace, which review 10 quotes (`<namespace>.me-revision.results.v1`; the records themselves keep it, as provenance) | 1 |

After the rules, the name of the author's private repository, the author's computer account name and the private folder names appear
nowhere in this deposit (the scan `deposit_scan.py`, category `private_project_name`, reports 0 hits; the build stops if a trace remains
in the redacted files). That statement covers only those three kinds of name. Other internal context is kept as written, as
provenance: desk paths (for example `H:/x1000/...` in older docstrings and build records, and the old values in
`DEPOSIT-PATCHES.json`), the names of the author's other projects and coordination channels in the plans (for example
`paper/PLAN-REVISION-2.md`), and host names in the training records. None is a credential (review 9 scanned for credential
patterns and found none).

## Files changed

| File | Occurrences | SHA-256 of the unredacted original (kept by the author) | SHA-256 of the file in this deposit |
|---|---|---|---|
| `paper/RESPONSE-TO-REVIEW.md` | 1 | `5497b940b67d3ce0a6e03d81506a902bae63b3e8850cbae9d91c763ecdd66122` | `ee74d5fa4eeaa024c7a6baf6208d0cea3bc377aa87a37d93f3c530b4049aceb8` |
| `paper/reviews/REVIEW-1-chatgpt-20261026-full.md` | 39 | `62a22508ba094eeb83bc42f68ed759e741b6943c0d08e9bd2bda281a4ecde676` | `09a3c81e92609b27abd58952b7f8ce4c100f45f3e98a41af9104289b86eaec00` |
| `paper/reviews/REVIEW-10-chatgpt-20261029-full.md` | 1 | `842a4e400579b9266569848490e024ebee2c9ec510fef698feadee2c1a8a2956` | `5e5ad2618a6294681890118d16914de7d071d8aa64f03e75d5ff1de08b4f8297` |
| `paper/reviews/REVIEW-2-chatgpt-20261026-full.md` | 36 | `46a13a2f82998cc213a5c260919fc3a79f0381110d13844e2b2bcd59525252cb` | `6f8af2f92b298d27a0e4f3957285ede19a07666c072164fb9eb20c273ff77074` |
| `paper/reviews/REVIEW-3-chatgpt-20261027-full.md` | 23 | `a5edbdd1c2f7131b153f949782d1fc55f1bea0cb47511ad2327089f09395223a` | `13a993f45e06d8417d7a27a2e4c4453eb0dee2f5a6832a3b46d8a8196df10542` |
| `paper/reviews/REVIEW-4-chatgpt-20261027-full.md` | 14 | `5521412a807bb6d28f94929a9b0781c15c09dccb59e0d38808619924af7458f2` | `b45c1575700df4d00bd3b5fd2888b9705738f8797bd72b46d5bdf79cc49b617f` |
| `paper/reviews/REVIEW-5-chatgpt-20261027-full.md` | 11 | `67f2b7a102651e781540055c2d2fad67bc2bc0fa72a0c2da97236d78d2663611` | `3745646ffbeb3742de2b468e9e7a94fe726640261bf9559bc283437a6bd3cebc` |
| `paper/reviews/REVIEW-6-chatgpt-20261027-full.md` | 9 | `a469c8857ac67dde2d1cc28afa49a6dbceba1e213040c1eaa553c9e422172ce8` | `aeb41f7c12ace5db153aa5d3787b95caa58d8b589d18289eecf4ee90223abe11` |
| `paper/reviews/REVIEW-7-chatgpt-20261027-full.md` | 8 | `d4b35ec2f2232bc7db06684c4f0d8db6aef54d5bca559e3783de8721cf744859` | `1402f05e3b82b7d6ce25137ea73a1cf135dba0a681e89dbb73bcc52ddfafe7d8` |
| `paper/reviews/REVIEW-9-chatgpt-20261029-full.md` | 2 | `e4cd05a10be3ea65e3ddcdead3ed512d93436eec3e56cae24762f37704f8c720` | `7d7c5edaa39c1a3c14097ab7085f624576f73b40ea816d98a4fb8303b9738981` |
| `paper/reviews/review-3-support/SHA256SUMS.txt` | 1 | `5b4f9f70aa3ae7682e4df0217f09ec42f1ea168bb219128f09b100f3006b63ca` | `b58dda9be5cc7fd568521f2c2e7a6d13e02f1286e3030ac3963b09da50b088d7` |
| `paper/reviews/review-3-support/check_v3.py` | 1 | `459e283a2b8158ecfcbac4981592196f66bd8f691ec200b45877e54f4564acfb` | `dc712d419bb84f1c62c9285088b4c63fcc738a522f53b02fff290ad8f2a361e4` |
| `paper/reviews/review-3-support/new-record-manifest.json` | 1011 | `1cd67cd3307d34ca0d80030b6dc1605d4c54a75c12b42e42a89b2a1fd1cfcfd9` | `1280c75a912f08fa5f885433e73b538a5a6a1f696ed614dc957b5a2aa0551982` |

## The digest file of review 3

`paper/reviews/review-3-support/SHA256SUMS.txt` is the reviewer's own list of digests of its support files and covers redacted files.
Its digest lines are left as the reviewer wrote them, so they identify the originals: the lines of `check_v3.py` and `new-record-manifest.json` do not
match this deposit's copies (the lines of `artifact-checks-v3.json`, `record-audit-v3.json` and `review-validation.json` still match). A comment line at the top
of that file says so (a line that starts with `#` is ignored by `sha256sum -c`). The deposit's own `SHA256SUMS` at the root covers the deposit's
bytes, including these redacted copies.
