"""Version 16 / archive v1.6: record the state in PUBLISHING.md, README.md and STATUS.json (after the clean room, the final check, the
Python 3.12 run and sync_deposit.py's local commit; after revision15/edit_docs_v16.py; before publishing, which waits for the owner's go).  The counts are read from
records/deposit/.  Derived from revision14/record_v15.py.

    python -I -B revision15/record_v16.py <deposit commit> <paper commit> "<now, ET>"
"""
import json
import sys
from pathlib import Path

P = Path(__file__).resolve().parent.parent
COMMIT, PAPER_COMMIT, NOW = sys.argv[1], sys.argv[2], sys.argv[3]
D = P / "records" / "deposit"
cr = json.loads((D / "CLEANROOM.json").read_bytes().decode("utf-8"))
fc = json.loads((D / "FINAL-CHECK.json").read_bytes().decode("utf-8"))
rep = json.loads((D / "REPRODUCE.json").read_bytes().decode("utf-8"))
py = json.loads((D / "PY312-FAST.json").read_bytes().decode("utf-8"))
steps = rep["steps"]
n_ok, n_all = sum(1 for s in steps if s["ok"]), len(steps)
mut = cr["mutation_tests"]
m_ok = sum(1 for m in mut if m["caught"])
FILES, MB = fc["sizes"]["files"], fc["sizes"]["total_mb"]
assert fc["ok"] is True and fc["scan"]["unjustified"] == 0 and cr["reproduce_all"]["returncode"] == 0 and m_ok == len(mut)
assert py["v1.6"]["all_ok"] is True
CNT = rep["file_status_counts"]
ROOM = f"REPRODUCE_ALL_OK, {n_ok} of {n_all} steps ({CNT['identical']} files identical, {CNT['normalised']} after the stated normalisation)"
P6 = py["v1.6"]
PYC = P6["file_status_counts"]
PY312 = (f"REPRODUCE_ALL_OK, {P6['steps_ok']} of {P6['steps']} fast steps ({PYC.get('identical', 0)} identical, "
         f"{PYC.get('normalised', 0)} normalised, {PYC.get('within_policy', 0)} within the numeric policy: AIHWKIT-COMPARE.json, "
         f"{P6['policy_detail_short']})")


def sub(text, a, b, n=1):
    assert text.count(a) == n, (a[:70], text.count(a))
    return text.replace(a, b)


pub = (P / "PUBLISHING.md").read_bytes().decode("utf-8")
CRLF = "\r\n" in pub                     # the working tree may hold CRLF (core.autocrlf): edit as LF, write back as found
pub = pub.replace("\r\n", "\n")
pub = sub(pub, "<!-- deposit-built -->\n",
          "<!-- deposit-built -->\n"
          f"**Release v1.6 ({NOW}): BUILT and verified, committed LOCALLY as {COMMIT} in `C:/Projects/memistor-ecram-training` on top of\n"
          "the published b5f86bed2, NOT pushed. It holds version 16 of the paper, the answer to review 13 (the contribution statement counts\n"
          "all thirteen reviews; the policy self-test's negative control no longer depends on the starting value; no result changed).**\n\n"
          "- Built on F: (`F:/x1000-deposit/memistor-deposit-v1.6`).\n"
          f"- Clean room (reference environment): {ROOM}; {m_ok} of {len(mut)} mutation tests caught.\n"
          f"- Python 3.12.3 / torch 2.7.1+cpu (WSL) on the finalized v1.6: {PY312}\n"
          "  (`records/deposit/PY312-FAST.json`; v1.5's records are in `records/deposit/v1.5/`).\n"
          "- Scan: 0 unjustified. The archived version 15 joins the mirror-address entry, and version 16's record script joins those of\n"
          "  versions 10, 13, 14 and 15.\n"
          f"- FINAL_CHECK_OK; {FILES:,} files, {MB} MB (`records/deposit/`).\n"
          "- Publishing is one push and one release, as for v1.5 (the same two commands with v1.6 and the new commit):\n"
          "  `git -C C:/Projects/memistor-ecram-training push origin main`, then\n"
          f"  `gh release create v1.6 --repo Questeria/memistor-ecram-training --target {COMMIT} --title \"v1.6: code, records and pulse\n"
          "  draws for the memistor paper (version 16)\" --notes-file RELEASE-NOTES.md`, with the tag pinned to the verified commit.\n"
          "  The new version DOI comes from Zenodo; the concept DOI stays.\n\n")
(P / "PUBLISHING.md").write_bytes((pub.replace("\n", "\r\n") if CRLF else pub).encode("utf-8"))

rd = (P / "README.md").read_bytes().decode("utf-8")
CRLF_RD = "\r\n" in rd
rd = rd.replace("\r\n", "\n").rstrip("\n") + "\n"
rd = sub(rd, 'from the Desktop folder "memistor paper - arXiv submission (v15)".\n', 'from the Desktop folder "memistor paper - arXiv submission (v15)" (superseded by version 16, see "Revision v16" below).\n')
rd += f"""
## Revision v16 (2026-11-01, director lane): the answer to review 13 (no experiment; no result changed; $0)

- Review 13 (ChatGPT, `reviews/REVIEW-13-chatgpt-20261101-full.md`, of release v1.5 and version 15) found the version-15 changes right
  and the paper ready to submit; its one optional finding (the `--policy-selftest` negative control added a fixed 4e-5, so it could
  fail for another valid starting value) was confirmed and fixed in `deposit-src/reproduce_all.py` (`printed_flip_value`, commit
  389b1b305; evidence `records/revision14/POLICY-SELFTEST-FIX-R13.json`). `RESPONSE-TO-REVIEW-13.md`.
- Text (`revision15/edit_16.py`): the contribution statement of both variants counts all thirteen reviews ("versions 1 to 7 and 10 to
  15 of this paper in turn, thirteen reviews in all"; it said versions 1 to 7); the availability section (archive v1.6, release v1.6,
  thirteen reviews, the thirteenth response); Appendix F (version 15 no longer "this paper", a version-16 entry); and, in a second pass
  (`revision15/edit_16b.py`, the owner's "fix anything stale"), the abstract's last sentence ("This version repairs the simulator after
  independent reviews ..." -> "The simulator was repaired after independent reviews, and the paper reports how far each repair moved the
  original results."). Nothing else.
  `revision15/archive_v15.py` archived `tex/v15` and `build/v15`.
- Build: `pod/build_payload_rev10.py --out H:/x1000/memistor-paper/rev15/v16`, `pod/build_rev10.sh` as `run.sh` in WSL. Both variants
  have 44 pages (as v15). BUILD-STEPS: `records/revision15/BUILD-STEPS-v16.txt`.
- Checks: `revision15/check_build_v16.py <out> --json records/revision15/ARTIFACT-CHECK-v16.json` is ALL_OK. The word-count diff
  v15 -> v16 has 8 expected edits and 0 unexplained in both variants; the v14 -> v16 control fails. Paper commit {PAPER_COMMIT}.
- Archive v1.6 (`F:/x1000-deposit/memistor-deposit-v1.6`): clean room {ROOM}; mutation {m_ok} of {len(mut)}; Python 3.12 fast path
  {PY312}; scan 0 unjustified; FINAL_CHECK_OK; {FILES:,} files, {MB} MB. Committed locally as {COMMIT}, NOT pushed.
- arXiv kit: Desktop folder "memistor paper - arXiv submission (v16)" (step 0: publish archive v1.6 first).
- Left: publish archive v1.6, then the owner's arXiv submission of version 16, from the Desktop folder "memistor paper - arXiv submission (v16)".
"""
(P / "README.md").write_bytes((rd.replace("\n", "\r\n") if CRLF_RD else rd).encode("utf-8"))

sp = P / "STATUS.json"
st = json.loads(sp.read_bytes().decode("utf-8"))
st["updated_et"] = NOW
st["done"].append(f"version 16 / archive v1.6 STAGED, NOT published: the contribution statement counts all thirteen reviews (versions 1 to 7 "
                  f"and 10 to 15); availability names v1.6; Appendix F version-16 entry; review 13's optional fix (printed_flip_value, "
                  f"389b1b305) is in v1.6's reproduce_all.py; RESPONSE-TO-REVIEW-13.md; 44 pages; check_build_v16 ALL_OK; paper commit "
                  f"{PAPER_COMMIT}; archive v1.6 built on F:, clean room {n_ok}/{n_all}, mutation {m_ok}/{len(mut)}, Python 3.12 fast "
                  f"path REPRODUCE_ALL_OK, scan 0 unjustified, FINAL_CHECK_OK, {FILES} files, {MB} MB, committed locally {COMMIT} "
                  f"(NOT pushed)")
st["next"] = ["the owner's go: publish archive v1.6 (git push origin main + gh release create v1.6, tag pinned to " + COMMIT
              + "; the same commands as v1.5); then record its Zenodo version DOI in PUBLISHING.md and STATUS.json",
              "then the owner submits version 16 to arXiv from the Desktop folder \"memistor paper - arXiv submission (v16)\" (44 pages); "
              "account, endorsement and terms are his",
              "then: record the arXiv identifier in PUBLISHING.md and STATUS.json"]
st["waiting_on"] = ["the owner: a go to publish v1.6, then the arXiv submission of version 16"]
st["v16"] = dict(summary="review 13 (ChatGPT, of v1.5 / v15): ready to submit; contribution statement counts all thirteen reviews; "
                         "the policy self-test's negative control computes its shift from the starting value (printed_flip_value); "
                         "availability names v1.6; 44 pages; no experiment, no result changed",
                 build_dir="H:/x1000/memistor-paper/rev15/v16",
                 checks="records/revision15/ARTIFACT-CHECK-v16.json (ALL_OK) and the records beside it",
                 kit="the owner's Desktop folder \"memistor paper - arXiv submission (v16)\"",
                 deposit=dict(build="F:/x1000-deposit/memistor-deposit-v1.6", local_commit=COMMIT, parent="b5f86bed2", pushed=False,
                              files=FILES, mb=MB),
                 continue_with="read README.md section Revision v16")
st["review_13"]["status"] = "confirmed; fixed in deposit-src and shipped in archive v1.6 (version 16); v1.5 unchanged"
sp.write_bytes((json.dumps(st, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
print("recorded v16 / v1.6 in PUBLISHING.md, README.md, STATUS.json")
