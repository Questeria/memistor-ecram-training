"""Version 15 / archive v1.5: record the state in PUBLISHING.md, README.md and STATUS.json (after the clean room, the final check, the
Python 3.12 run and sync_deposit.py's local commit; before publishing, which waits for the owner's go).  The counts are read from
records/deposit/.  Derived from revision13/record_v14.py.

    python -I -B revision14/record_v15.py <deposit commit> <paper commit> "<now, ET>"
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
assert py["v1.5"]["all_ok"] is True
CNT = rep["file_status_counts"]
ROOM = f"REPRODUCE_ALL_OK, {n_ok} of {n_all} steps ({CNT['identical']} files identical, {CNT['normalised']} after the stated normalisation)"
P5 = py["v1.5"]
PYC = P5["file_status_counts"]
PY312 = (f"REPRODUCE_ALL_OK, {P5['steps_ok']} of {P5['steps']} fast steps ({PYC.get('identical', 0)} identical, "
         f"{PYC.get('normalised', 0)} normalised, {PYC.get('within_policy', 0)} within the numeric policy: AIHWKIT-COMPARE.json, "
         f"{P5['policy_detail_short']})")
P4 = py["v1.4"]
PY312_V14 = (f"release v1.4 itself under the same Python 3.12 setting: {P4['steps_ok']} of {P4['steps']} fast steps passed and "
             f"{P4['file_status_counts'].get('identical', 0) + P4['file_status_counts'].get('normalised', 0)} files matched, "
             f"{P4['file_status_counts'].get('DIFFERS', 0)} differed ({', '.join(P4['differs'])}): {P4['verdict']}")


def sub(text, a, b, n=1):
    assert text.count(a) == n, (a[:70], text.count(a))
    return text.replace(a, b)


pub = (P / "PUBLISHING.md").read_bytes().decode("utf-8")
CRLF = "\r\n" in pub                     # the working tree may hold CRLF (core.autocrlf): edit as LF, write back as found
pub = pub.replace("\r\n", "\n")
pub = sub(pub, "107,820,671 bytes). The paper is not yet on arXiv: submit version 14 (not 13).",
          "107,820,671 bytes). Release v1.5, which holds version 15 (the answer to review 12), is built and verified and waits for\n"
          "publishing. The paper is not yet on arXiv: publish v1.5 first, because version 15's availability section names it, then\n"
          "submit version 15 (not 14).")
pub = sub(pub, '"memistor paper - arXiv submission (v14)"', '"memistor paper - arXiv submission (v15)"')
pub = sub(pub, "<!-- deposit-built -->\n",
          "<!-- deposit-built -->\n"
          f"**Release v1.5 ({NOW}): BUILT and verified, committed LOCALLY as {COMMIT} in `C:/Projects/memistor-ecram-training` on top of\n"
          "the published 39c6ed7fe, NOT pushed. It holds version 15 of the paper, the answer to review 12 (Figure 1's settings, the\n"
          "reproduction's numeric policy, the Agarwal order, the exact t quantile: 16 interval endpoints move by 0.01; no result changed).**\n\n"
          "- Built on F: (`F:/x1000-deposit/memistor-deposit-v1.5`).\n"
          f"- Clean room (reference environment): {ROOM}; {m_ok} of {len(mut)} mutation tests caught (M5 and M6 are new: a flipped\n"
          "  acceptance boolean and a discrepancy past its line in AIHWKIT-COMPARE.json must fail). `reproduce_all.py` gains one step,\n"
          "  the numeric policy's self-test; Figure 1's two steps now run `revision14/`.\n"
          f"- Python 3.12.3 / torch 2.7.1+cpu (WSL) on the finalized v1.5: {PY312}. For comparison, {PY312_V14}\n"
          "  (`records/deposit/PY312-FAST.json`).\n"
          "- Scan: 0 unjustified. The archived version 14 joins the mirror-address entry, and version 15's record script joins those of\n"
          "  versions 10, 13 and 14.\n"
          f"- FINAL_CHECK_OK; {FILES:,} files, {MB} MB (`records/deposit/`; v1.4's records are in `records/deposit/v1.4/`).\n"
          "- Publishing is one push and one release, as for v1.4 (the same two commands with v1.5 and the new commit):\n"
          "  `git -C C:/Projects/memistor-ecram-training push origin main`, then\n"
          f"  `gh release create v1.5 --repo Questeria/memistor-ecram-training --target {COMMIT} --title \"v1.5: code, records and pulse\n"
          "  draws for the memistor paper (version 15)\" --notes-file RELEASE-NOTES.md`, with the tag pinned to the verified commit.\n"
          "  The new version DOI comes from Zenodo; the concept DOI stays.\n\n")
pub = sub(pub, "`pod/build_rev8.sh` for versions 9 to 13 and `pod/build_rev9.sh` for version 14",
          "`pod/build_rev8.sh` for versions 9 to 13 and `pod/build_rev9.sh` for version 14 and `pod/build_rev10.sh` for version 15")
pub = sub(pub, "loose copies of the files; `revision13/check_build_v14.py` (version 14) runs",
          "loose copies of the files; `revision14/check_build_v15.py` (version 15) runs `revision6/check_build_v7.py` and reads the version-15\n"
          "   proofs: the word-count text diff `revision14/pdf_text_diff_v15.py` (v14 -> v15, reference numbers as [#], the same 44 pages),\n"
          "   the name check in WSL and in Windows, numbers freshness, Figure 1 against the selected settings, the records and the\n"
          "   simulator, Figure 4, the reset and the Welch test; `revision13/check_build_v14.py` (version 14) runs")
pub = sub(pub, 'for version 14: "44 pages, 4 figures; code and data: https://doi.org/10.5281/zenodo.23748861".',
          'for version 15: "44 pages, 4 figures; code and data: https://doi.org/10.5281/zenodo.23748861".')
(P / "PUBLISHING.md").write_bytes((pub.replace("\n", "\r\n") if CRLF else pub).encode("utf-8"))

rd = (P / "README.md").read_bytes().decode("utf-8")
CRLF_RD = "\r\n" in rd
rd = rd.replace("\r\n", "\n").rstrip("\n") + "\n"
rd += f"""
## Revision v15 (2026-11-01, director lane): the answer to review 12 (no experiment; no result changed; $0)

- Review 12 (ChatGPT, `reviews/REVIEW-12-chatgpt-20261031-full.md`, pasted by the owner) audited release v1.4 (39c6ed7fe): checksums,
  the 165 main comparisons, the width and sensitivity analyses and the energy output recomputed from the records (all agree; the energy
  byte for byte), and the fast reproduction under Python 3.12.14 / torch 2.7.1+cpu. Minor revision. Every finding was verified
  (`revision14/verify_findings_12.py` -> `records/revision14/VERIFY-FINDINGS-12.json`); `RESPONSE-TO-REVIEW-12.md` gives each verdict.
- A (confirmed): `AIHWKIT-COMPARE.json` re-simulates float32 pulse sequences on the CPU; under Python 3.12.3 / torch 2.7.1+cpu (WSL)
  the same 26 floats differ (largest 4.3e-6 weight units), every boolean and printed value equal
  (`records/revision14/AIHWKIT-COMPARE-py312.json`). `deposit-src/reproduce_all.py` compares that one file under a stated numeric
  policy (exact structure, strings, integers, booleans, unnamed floats and printed values; 5e-5 weight units, 5e-3 tolerance units,
  1e-4 spread ratio) with a `--policy-selftest` step (14 cases); the archive README names the reference environment (Python 3.13.15,
  Windows 11, torch 2.7.1+cu126 on the CPU, NumPy 2.5.2, matplotlib 3.9.2, Pillow 13.0.0); clean-room mutations M5 and M6.
- B (confirmed): Figure 1 shows the selected settings (TTv2, c-TTv2: pulse reset; AGAD: none; TTv2: c = 1) and its caption says so
  (`revision14/make_fig_arch.py`); `revision14/check_fig_arch.py` reads them from `CHOICES-REVISION.json` and all 90 main-experiment
  device records per algorithm and simulates each layer in that configuration (8 of 8 planted faults caught).
- C (confirmed): Section 2.2 cites Agarwal et al. ("for conventional (SGD) training") and the CNN extension before Byun et al.
- D1 (confirmed; labelled, not separated): the reset re-reads' buffer allowance, at most 0.15 % of the analog energy, is called a
  conservative approximation in Section 5; no number changed.
- D2 (confirmed): `revision/analyze_rev.py` takes the exact t quantile for the ordinary and paired intervals; 16 endpoints in Tables
  4 and 5 move by 0.01 (each listed in `RESPONSE-TO-REVIEW-12.md`); no label or other printed number changed.
- Text: `revision14/edit_15.py`; availability (archive v1.5, twelve reviews, the twelfth response) and the history (version 15); date
  November 2026. `revision14/archive_v14.py` archived `tex/v14` and `build/v14`.
- Build: `pod/build_payload_rev10.py --out H:/x1000/memistor-paper/rev14/v15`, `run.sh` in WSL. Both variants have 44 pages (as v14).
- Checks: `revision14/check_build_v15.py <out> --json records/revision14/ARTIFACT-CHECK-v15.json` is ALL_OK. The word-count diff
  v14 -> v15 has 30 expected edits and 0 unexplained in both variants; the v13 control fails. Paper commit {PAPER_COMMIT}.
- Archive v1.5 (`F:/x1000-deposit/memistor-deposit-v1.5`): clean room {ROOM}; mutation {m_ok} of {len(mut)}; Python 3.12 fast path
  {PY312}; scan 0 unjustified; FINAL_CHECK_OK; {FILES:,} files, {MB} MB. Committed locally as {COMMIT}, NOT pushed.
- Left:
  - the owner's go to publish v1.5 (push + release, as for v1.4; Zenodo mints its version DOI);
  - then the owner's arXiv submission of version 15, from the Desktop folder "memistor paper - arXiv submission (v15)".
"""
(P / "README.md").write_bytes((rd.replace("\n", "\r\n") if CRLF_RD else rd).encode("utf-8"))

sp = P / "STATUS.json"
st = json.loads(sp.read_bytes().decode("utf-8"))
st["updated_et"] = NOW
st["done"].append(f"review 12 (ChatGPT, audit of v1.4 / v14) answered (RESPONSE-TO-REVIEW-12.md: reproduction numeric policy for "
                  f"AIHWKIT-COMPARE.json + reference environment, Figure 1 selected settings + check from the records, Agarwal before "
                  f"Byun, exact t quantile (16 endpoints by 0.01, no label changed), reset-read allowance labelled); paper version 15 "
                  f"(44 pages; check_build_v15 ALL_OK; commit {PAPER_COMMIT}); archive v1.5 built on F:, clean room {n_ok}/{n_all}, "
                  f"mutation {m_ok}/{len(mut)}, Python 3.12 fast path REPRODUCE_ALL_OK, scan 0 unjustified, FINAL_CHECK_OK, {FILES} files, "
                  f"{MB} MB, committed locally {COMMIT} (NOT pushed)")
st["next"] = ["the owner's go: publish archive v1.5 (git push origin main + gh release create v1.5, tag pinned to " + COMMIT
              + "; the same commands as v1.4); then record its Zenodo version DOI in PUBLISHING.md and STATUS.json",
              "then the owner submits version 15 to arXiv from the Desktop folder \"memistor paper - arXiv submission (v15)\" (44 pages); "
              "account, endorsement and terms are his",
              "then: record the arXiv identifier in PUBLISHING.md and STATUS.json"]
st["waiting_on"] = ["the owner: a go to publish v1.5, then the arXiv submission of version 15"]
st["v15"] = dict(summary="review 12 (ChatGPT, audit of v1.4 / v14): reproduction numeric policy for AIHWKIT-COMPARE.json with a "
                         "self-test and the reference environment stated; Figure 1 shows the selected reset/chopper settings and its check "
                         "reads them from the records; Agarwal before Byun; exact t quantile (16 endpoints in Tables 4 and 5 by 0.01, no "
                         "label changed); reset-read buffer allowance labelled conservative; availability names v1.5; 44 pages; no "
                         "experiment, no result changed",
                 build_dir="H:/x1000/memistor-paper/rev14/v15",
                 checks="records/revision14/ARTIFACT-CHECK-v15.json (ALL_OK) and the records beside it",
                 deposit=dict(build="F:/x1000-deposit/memistor-deposit-v1.5", local_commit=COMMIT, parent="39c6ed7fe", pushed=False,
                              files=FILES, mb=MB),
                 continue_with="read README.md section Revision v15")
sp.write_bytes((json.dumps(st, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
print("recorded v15 / v1.5 in PUBLISHING.md, README.md, STATUS.json")
