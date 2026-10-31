"""Version 12 / archive v1.2: record the state in PUBLISHING.md, README.md and STATUS.json (after the clean room, the final check and
sync_deposit.py's local commit; before publishing, which waits for the owner's go).

    python -I -B revision11/record_v12.py
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parent.parent
NOW = "2026-10-29 21:15 ET"
COMMIT = "47da42036"


def sub(text, a, b, n=1):
    assert text.count(a) == n, (a[:70], text.count(a))
    return text.replace(a, b)


pub = (P / "PUBLISHING.md").read_bytes().decode("utf-8")
pub = sub(pub, "The code and data archive is published (release v1.0 on 2026-10-28 and v1.1 on 2026-10-29; section 4). The paper is not yet on arXiv.",
          "The code and data archive is published (release v1.0 on 2026-10-28 and v1.1 on 2026-10-29; section 4). Release v1.2, which holds\n"
          "version 12 (the answer to review 9), is built and verified and waits for publishing. The paper is not yet on arXiv: publish v1.2\n"
          "first, because version 12's availability section names it.")
pub = sub(pub, '"memistor paper - arXiv submission (v11)"', '"memistor paper - arXiv submission (v12)"')
pub = sub(pub, "**Release v1.1 (2026-10-29, 13:53 ET): PUBLISHED.",
          f"**Release v1.2 ({NOW}): BUILT and verified, committed LOCALLY as {COMMIT} in `C:/Projects/memistor-ecram-training` on top of\n"
          "the published aaee0bed8, NOT pushed. It holds version 12 of the paper, the answer to review 9.**\n\n"
          "- Built on F: (`F:/x1000-deposit/memistor-deposit-v1.2`; H: is kept for the drive-G backup).\n"
          "- Clean room: REPRODUCE_ALL_OK, 28 of 28 steps (55 files identical, 13 after the stated normalisation); 4 of 4 mutation tests\n"
          "  caught.\n"
          "- Scan: 0 unjustified, after two additions. The archived version 11 joins the mirror-address entry, and an email hit is now masked\n"
          "  to its domain, because review 9 quotes the account's no-reply address.\n"
          "- FINAL_CHECK_OK; 3,491 files, 132.4 MB (`records/deposit/`; v1.1's records are in `records/deposit/v1.1/`).\n"
          "- Publishing is one push and one release, as for v1.1. The new version DOI comes from Zenodo; the concept DOI stays.\n\n"
          "**Release v1.1 (2026-10-29, 13:53 ET): PUBLISHED.")
pub = sub(pub, "`pod/build_rev8.sh` for versions 9, 10 and 11", "`pod/build_rev8.sh` for versions 9, 10, 11 and 12")
pub = sub(pub, "loose copies of the files; `revision10/check_build_v11.py` (version 11) runs",
          "loose copies of the files; `revision11/check_build_v12.py` (version 12) runs `revision6/check_build_v7.py` and reads the version-12\n"
          "   proofs: the word-count text diff `revision11/pdf_text_diff_v12.py` (v11 -> v12; the extra page reflows floats), the name check,\n"
          "   numbers freshness, Figure 3 (its self-test on bundled version-10 code), the reset and `revision11/test_welch_df.py`;\n"
          "   `revision10/check_build_v11.py` (version 11) runs")
pub = sub(pub, 'for version 11: "42 pages, 3 figures; code and data: https://doi.org/10.5281/zenodo.23748861".',
          'for version 12: "43 pages, 3 figures; code and data: https://doi.org/10.5281/zenodo.23748861".')
(P / "PUBLISHING.md").write_bytes(pub.encode("utf-8"))

rd = (P / "README.md").read_bytes().decode("utf-8").rstrip("\n") + "\n"
rd += f"""
## Revision v12 (2026-10-29, director): the answer to review 9 (no experiment; $0)

- Review 9 (ChatGPT in Codex, `reviews/REVIEW-9-chatgpt-20261029-full.md`) audited release v1.1 against version 11 before arXiv.
  - It worked from a fresh clone and ran the README as written, then 27 of 27 steps.
  - It compared all 68 outputs, recomputed the statistics independently and compiled the arXiv source with pdfLaTeX (42 pages, clean).
  - It found 1 major, 8 minor and 2 cosmetic issues, and all of review 8's findings fixed or disclosed.
  - All eleven were verified and confirmed. `RESPONSE-TO-REVIEW-9.md` gives each, with its verification and change.
- Major: the width study's Welch interval read its t table at the floored df (`revision/analyze_rev.py` `tq()`); the plan registers a
  Welch interval. Now `t_quantile` at the actual df (DEVIATIONS R9). CIFAR protonic-inspired c-TTv2 becomes GROWS [0.05, 3.47]; no other
  verdict changes. `revision11/test_welch_df.py` checks it, and the floored df fails it.
- Text (`revision11/edit_12.py`):
  - the width section, the abstract, the discussion and the roadmap;
  - only the example order is shared across widths;
  - the excess correlation is defined in quadrature (Section 4.3, Table 8);
  - Table 16's v1 labels; Jacobs-Gedrim; the availability section (v1.2, nine reviews); the history.
  The paper now has 43 pages. `revision11/archive_v11.py` archived `tex/v11` and `build/v11`.
- Checks: `revision11/check_build_v12.py <out> --json records/revision11/ARTIFACT-CHECK-v12.json` is ALL_OK. The text diff now counts
  words (`revision11/pdf_text_diff_v12.py`): 46 expected edits, 0 unexplained; the v10 control fails.
- Archive v1.2:
  - The figure self-test needs no private history (`revision10/fixtures/`); `--sums` skips `.venv`; Python 3.12+ is stated.
  - Docstrings, CITATION.cff and REDACTIONS.md fixed; rule P4.
  - Clean room 28 of 28 (55 + 13), mutation 4 of 4, scan 0 unjustified, FINAL_CHECK_OK. Committed locally as {COMMIT}, NOT pushed.
- Left:
  - the owner's go to publish v1.2 (push + release; Zenodo mints its version DOI);
  - then the owner's arXiv submission of version 12, from the Desktop folder "memistor paper - arXiv submission (v12)".
"""
(P / "README.md").write_bytes(rd.encode("utf-8"))

sp = P / "STATUS.json"
st = json.loads(sp.read_bytes().decode("utf-8"))
st["updated_et"] = NOW
st["done"].append(f"review 9 answered (all 11 findings confirmed); paper version 12 (43 pages; check_build_v12 ALL_OK; commit b8ab198cf); "
                  f"archive v1.2 built on F:, clean room 28/28, mutation 4/4, scan 0 unjustified, FINAL_CHECK_OK, committed locally {COMMIT} (NOT pushed)")
st["next"] = ["the owner's go: publish archive v1.2 (git push origin main + gh release create v1.2, tag pinned to " + COMMIT
              + "); then record its Zenodo version DOI in PUBLISHING.md and STATUS.json",
              "then the owner submits version 12 to arXiv from the Desktop folder \"memistor paper - arXiv submission (v12)\" (43 pages); "
              "account, endorsement and terms are his",
              "then: record the arXiv identifier in PUBLISHING.md and STATUS.json"]
st["waiting_on"] = ["the owner: a go to publish v1.2, then the arXiv submission of version 12"]
sp.write_bytes((json.dumps(st, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
print("recorded v12 / v1.2 in PUBLISHING.md, README.md, STATUS.json")
