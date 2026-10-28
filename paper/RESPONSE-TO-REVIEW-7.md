# Response to the seventh independent review (ChatGPT, 2026-10-27), version 8 of the paper

The review (`reviews/REVIEW-7-chatgpt-20261027-full.md`) read version 7 (commit c43a544dc, `build/v7/main.pdf` SHA-256 b1a92aa7...3c8).
It found no actionable scientific, numerical or document-content defect and asked for nothing. Its one caveat, that mobile-width HTML
rendering is unverified, stays unclaimed in the paper. No experiment was run. Cost: $0 (desk, WSL; no GPU, no pod).

Version 8 therefore changes only what the owner ordered on 2026-10-27 (about 20:1x ET):

| # | Change | Where |
|---|---|---|
| 1 | The owner's official name, Anthony DeMarco, is printed instead of the name used in versions 1 to 7; the affiliation stays "Independent researcher" | author line of `tex/main.tex` and `tex/main-arxiv.tex`, the contribution statement in `tex/body.tex`, the HTML title block (`pod/html_prep_rev7.py`), `PUBLISHING.md` |
| 2 | ChatGPT is credited, not as an author, in the "Author contributions and use of AI" section of both variants: it reviewed versions 1 to 7 in turn, checked the record hashes, independently recomputed the revised statistics, and reported errors, each verified against the files and corrected where confirmed (pointing to Appendix F) | `tex/body.tex` |

The sentence says "versions 1 to 7" because ChatGPT reviewed each: review 1 of version 1 (31 pages; named in review 2 as "the 31-page
version reviewed previously") and reviews 2 to 7 (`reviews/`). It says "where confirmed" because the responses record a few findings as
qualified or partly confirmed, not all as errors.

The deposit inventory (Section 9) lists `RESPONSE-TO-REVIEW-7.md` and counts seven reviews; the revision history (Appendix F) gains
the version-8 paragraph and version 7 is no longer "this paper".

## Checks (records in `records/revision7/`)

- Name: `revision7/name_check.py` -> `NAME-CHECK-v8.json`. The old name appears nowhere in the current sources, either PDF (page text, Info
  dictionary, every object, raw bytes), the HTML or the arXiv archive; the same search finds it in version 7's artifacts and in planted copies.
- PDF text against version 7: `revision7/pdf_text_diff_v8.py` -> `PDF-TEXT-DIFF-main.json`, `PDF-TEXT-DIFF-main-arxiv.json`. With the name
  replacement accounted for, only the expected hunks differ (history, inventory, ChatGPT sentence). Numbers: see the records.
- Every earlier check: `revision7/check_build_v8.py` runs `revision6/check_build_v7.py` (hence v6, v5, v4 checks) -> `ARTIFACT-CHECK-v8.json`.
- No number macro, table, figure or record changed; the figure PDFs are compared by decoded page stream (`FIG-STREAMS.json`).

## Results (copied from the records)

- `NAME-CHECK-v8.json`: old-name hits 0 across the sources (`tex/`, archived v1-v7 folders excluded), `main.pdf` and `main-arxiv.pdf` (page text,
  Info dictionary, every object, raw bytes; the Author field is empty), `main.html` (bytes, visible text, title, meta) and every member of
  `arxiv-source.tar.gz`. The new name is present: `main.pdf` 5, `main-arxiv.pdf` 3, HTML 5, 3 archive members, 4 source files. The self-test finds
  the old name 27 times in version 7's artifacts and in each planted copy (HTML meta, PDF Info author, PDF text, a tex file, a tar member).
- `PDF-TEXT-DIFF-main.json`: 41 -> 41 pages, 20,467 -> 20,571 words; 4 old-name occurrences replaced by the new name; 5 hunks, all expected
  (six -> seven, the inventory entry, the ChatGPT sentence, "; this paper" removed from version 7, the version-8 paragraph); 0 unexpected.
  `PDF-TEXT-DIFF-main-arxiv.json`: 41 -> 41, 20,449 -> 20,551 words, 2 replacements, the same 5 hunks, 0 unexpected. Version 6 against version 8
  fails (3 unexpected hunks).
- `ARTIFACT-CHECK-v8.json`: ALL_OK (every earlier check, the name proof, both PDF diffs). `FIG-STREAMS.json`: all seven figure streams equal.
