"""Version 13 / archive v1.3: record the state in PUBLISHING.md, README.md and STATUS.json (after the clean room, the final check and
sync_deposit.py's local commit; before publishing, which waits for the owner's go).  The counts are read from records/deposit/.

    python -I -B revision12/record_v13.py <deposit commit> <paper commit> "<now, ET>"
"""
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parent.parent
COMMIT, PAPER_COMMIT, NOW = sys.argv[1], sys.argv[2], sys.argv[3]
D = P / "records" / "deposit"
cr = json.loads((D / "CLEANROOM.json").read_bytes().decode("utf-8"))
fc = json.loads((D / "FINAL-CHECK.json").read_bytes().decode("utf-8"))
tail = cr["reproduce_all"]["tail"]
steps = [l for l in json.loads((D / "REPRODUCE.json").read_bytes().decode("utf-8"))["steps"]]
n_ok, n_all = sum(1 for s in steps if s["ok"]), len(steps)
mut = cr["mutation_tests"]
m_ok = sum(1 for m in mut if m["caught"])
counts = [l for l in tail if l.startswith("files rewritten")][0]
FILES, MB = fc["sizes"]["files"], fc["sizes"]["total_mb"]
assert fc["ok"] is True and fc["scan"]["unjustified"] == 0 and cr["reproduce_all"]["returncode"] == 0 and m_ok == len(mut)
CNT = json.loads((D / "REPRODUCE.json").read_bytes().decode("utf-8"))["file_status_counts"]
ROOM = f"REPRODUCE_ALL_OK, {n_ok} of {n_all} steps ({CNT['identical']} files identical, {CNT['normalised']} after the stated normalisation)"


def sub(text, a, b, n=1):
    assert text.count(a) == n, (a[:70], text.count(a))
    return text.replace(a, b)


pub = (P / "PUBLISHING.md").read_bytes().decode("utf-8")
pub = sub(pub, "Release v1.2, which holds\nversion 12 (the answer to review 9), was published on 2026-10-29 at 21:38 ET. The paper is not yet on arXiv.",
          "Release v1.2, which holds\nversion 12 (the answer to review 9), was published on 2026-10-29 at 21:38 ET. Release v1.3, which holds version 13 (the\n"
          "answer to review 10), is built and verified and waits for publishing. The paper is not yet on arXiv: publish v1.3 first, because\n"
          "version 13's availability section names it.")
pub = sub(pub, '"memistor paper - arXiv submission (v12)"', '"memistor paper - arXiv submission (v13)"')
pub = sub(pub, "**Release v1.2 (2026-10-29, 21:38 ET): PUBLISHED.",
          f"**Release v1.3 ({NOW}): BUILT and verified, committed LOCALLY as {COMMIT} in `C:/Projects/memistor-ecram-training` on top of\n"
          "the published 47da42036, NOT pushed. It holds version 13 of the paper, the answer to review 10 (no number changed).**\n\n"
          "- Built on F: (`F:/x1000-deposit/memistor-deposit-v1.3`).\n"
          f"- Clean room: {ROOM}; {m_ok} of {len(mut)} mutation tests caught.\n"
          "- Scan: 0 unjustified. Path rule P5 (`REDACTIONS.md`) masks the records' namespace prefix that review 10 quotes in its prose,\n"
          "  and the archived version 12 joins the mirror-address entry.\n"
          f"- FINAL_CHECK_OK; {FILES:,} files, {MB} MB (`records/deposit/`; v1.2's records are in `records/deposit/v1.2/`).\n"
          "- Publishing is one push and one release, as for v1.2 (the same two commands with v1.3 and the new commit):\n"
          "  `git -C C:/Projects/memistor-ecram-training push origin main`, then\n"
          f"  `gh release create v1.3 --repo Questeria/memistor-ecram-training --target {COMMIT} --title \"v1.3: code, records and pulse\n"
          "  draws for the memistor paper (version 13)\" --notes-file RELEASE-NOTES.md`, with the tag pinned to the verified commit.\n"
          "  The new version DOI comes from Zenodo; the concept DOI stays.\n\n"
          "**Release v1.2 (2026-10-29, 21:38 ET): PUBLISHED.")
pub = sub(pub, "`pod/build_rev8.sh` for versions 9, 10, 11 and 12", "`pod/build_rev8.sh` for versions 9 to 13")
pub = sub(pub, "loose copies of the files; `revision11/check_build_v12.py` (version 12) runs",
          "loose copies of the files; `revision12/check_build_v13.py` (version 13) runs `revision6/check_build_v7.py` and reads the version-13\n"
          "   proofs: the word-count text diff `revision12/pdf_text_diff_v13.py` (v12 -> v13, pages equal), the name check in WSL and in\n"
          "   Windows, numbers freshness, Figure 3, the reset and the Welch test; `revision11/check_build_v12.py` (version 12) runs")
pub = sub(pub, 'for version 12: "43 pages, 3 figures; code and data: https://doi.org/10.5281/zenodo.23748861".',
          'for version 13: "43 pages, 3 figures; code and data: https://doi.org/10.5281/zenodo.23748861".')
(P / "PUBLISHING.md").write_bytes(pub.encode("utf-8"))

rd = (P / "README.md").read_bytes().decode("utf-8").rstrip("\n") + "\n"
rd += f"""
## Revision v13 (2026-10-31, director lane): the answer to review 10 (no experiment; no number changed; $0)

- Review 10 (ChatGPT in Codex, `reviews/REVIEW-10-chatgpt-20261029-full.md`) re-audited release v1.2 against version 12: a fresh clone, the
  README as written, 28 of 28 steps, 68 outputs and 2,232 macros, the eight Welch intervals recomputed from the records, pdfLaTeX 43
  pages. It found the Welch fix right, no new major or critical issue, and four small findings. All four are verified and confirmed
  (`RESPONSE-TO-REVIEW-10.md`).
- F1: the archive README ("Changes since v1.1", in `make_deposit.py`) said no other printed number changed; all eight Welch intervals
  did. Corrected, with a new "Changes since v1.2".
- F2: the archive README's layout table said eight reviews; it says ten.
- F3: Table 11's caption said versions 1--11; it says 2--11 (version 1 had no Welch test). Fixed in `revision/analyze_rev.py`, table
  regenerated; nothing else changed (numbers FRESH).
- F4: `revision9/name_check_v10.py` closes every PDF (context managers), so its self-test cleans up on Windows. Old: exit 1
  (WinError 32); new: NAME_OK (`records/revision12/NAME-CHECK-WINDOWS-F4.json`).
- Text (`revision12/edit_13.py`): availability (archive v1.3, release v1.3, ten reviews, the tenth response) and the history
  (version 13). The concept DOI is unchanged. `revision12/archive_v12.py` archived `tex/v12` and `build/v12`.
- Build: `pod/build_payload_rev8.py --out H:/x1000/memistor-paper/rev12/v13`, `run.sh` in WSL. Both variants have 43 pages.
- Checks: `revision12/check_build_v13.py <out> --json records/revision12/ARTIFACT-CHECK-v13.json` is ALL_OK. The word-count diff
  v12 -> v13 has 8 expected edits and 0 unexplained, pages equal; the v11 control fails. Paper commit {PAPER_COMMIT}.
- Archive v1.3 (`F:/x1000-deposit/memistor-deposit-v1.3`): clean room {ROOM}; mutation {m_ok} of {len(mut)}; scan 0 unjustified;
  FINAL_CHECK_OK; {FILES:,} files, {MB} MB. Committed locally as {COMMIT}, NOT pushed.
- Left:
  - the owner's go to publish v1.3 (push + release, as for v1.2; Zenodo mints its version DOI);
  - then the owner's arXiv submission of version 13, from the Desktop folder "memistor paper - arXiv submission (v13)".
"""
(P / "README.md").write_bytes(rd.encode("utf-8"))

sp = P / "STATUS.json"
st = json.loads(sp.read_bytes().decode("utf-8"))
st["updated_et"] = NOW
st["done"].append(f"review 10 answered (all 4 findings confirmed and fixed; RESPONSE-TO-REVIEW-10.md); paper version 13 (43 pages; "
                  f"check_build_v13 ALL_OK; commit {PAPER_COMMIT}); archive v1.3 built on F:, clean room {n_ok}/{n_all}, mutation "
                  f"{m_ok}/{len(mut)}, scan 0 unjustified, FINAL_CHECK_OK, {FILES} files, {MB} MB, committed locally {COMMIT} (NOT pushed)")
st["next"] = ["the owner's go: publish archive v1.3 (git push origin main + gh release create v1.3, tag pinned to " + COMMIT
              + "; the same commands as v1.2); then record its Zenodo version DOI in PUBLISHING.md and STATUS.json",
              "then the owner submits version 13 to arXiv from the Desktop folder \"memistor paper - arXiv submission (v13)\" (43 pages); "
              "account, endorsement and terms are his",
              "then: record the arXiv identifier in PUBLISHING.md and STATUS.json"]
st["waiting_on"] = ["the owner: a go to publish v1.3, then the arXiv submission of version 13"]
st["v13"] = dict(summary="review 10: four small findings, all fixed (archive README wording and review count, Table 11's caption "
                         "versions 2--11, the name check's open PDF on Windows); availability names v1.3; 43 pages; no experiment, no number changed",
                 build_dir="H:/x1000/memistor-paper/rev12/v13",
                 checks="records/revision12/ARTIFACT-CHECK-v13.json (ALL_OK) and the records beside it",
                 deposit=dict(build="F:/x1000-deposit/memistor-deposit-v1.3", local_commit=COMMIT, parent="47da42036", pushed=False,
                              files=FILES, mb=MB),
                 continue_with="read README.md section Revision v13")
sp.write_bytes((json.dumps(st, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
print("recorded v13 / v1.3 in PUBLISHING.md, README.md, STATUS.json")
