"""Version 14 / archive v1.4: record the state in PUBLISHING.md, README.md and STATUS.json (after the clean room, the final check and
sync_deposit.py's local commit; before publishing, which waits for the owner's go).  The counts are read from records/deposit/.
Derived from revision12/record_v13.py.

    python -I -B revision13/record_v14.py <deposit commit> <paper commit> "<now, ET>"
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
steps = rep["steps"]
n_ok, n_all = sum(1 for s in steps if s["ok"]), len(steps)
mut = cr["mutation_tests"]
m_ok = sum(1 for m in mut if m["caught"])
FILES, MB = fc["sizes"]["files"], fc["sizes"]["total_mb"]
assert fc["ok"] is True and fc["scan"]["unjustified"] == 0 and cr["reproduce_all"]["returncode"] == 0 and m_ok == len(mut)
CNT = rep["file_status_counts"]
ROOM = f"REPRODUCE_ALL_OK, {n_ok} of {n_all} steps ({CNT['identical']} files identical, {CNT['normalised']} after the stated normalisation)"


def sub(text, a, b, n=1):
    assert text.count(a) == n, (a[:70], text.count(a))
    return text.replace(a, b)


pub = (P / "PUBLISHING.md").read_bytes().decode("utf-8")
CRLF = "\r\n" in pub                     # the working tree may hold CRLF (core.autocrlf): edit as LF, write back as found
pub = pub.replace("\r\n", "\n")
pub = sub(pub, "record 23848730, zip 106,146,105 bytes). The paper is not yet on arXiv: submit version 13 (not 12).",
          "record 23848730, zip 106,146,105 bytes). Release v1.4, which holds version 14 (the answer to review 11), is built and\n"
          "verified and waits for publishing. The paper is not yet on arXiv: publish v1.4 first, because version 14's availability section\n"
          "names it, then submit version 14 (not 13).")
pub = sub(pub, '"memistor paper - arXiv submission (v13)"', '"memistor paper - arXiv submission (v14)"')
pub = sub(pub, "<!-- deposit-built -->\n",
          "<!-- deposit-built -->\n"
          f"**Release v1.4 ({NOW}): BUILT and verified, committed LOCALLY as {COMMIT} in `C:/Projects/memistor-ecram-training` on top of\n"
          "the published 03474b26b, NOT pushed. It holds version 14 of the paper, the answer to review 11 (text and one new figure; no\n"
          "result changed).**\n\n"
          "- Built on F: (`F:/x1000-deposit/memistor-deposit-v1.4`).\n"
          f"- Clean room: {ROOM}; {m_ok} of {len(mut)} mutation tests caught. `reproduce_all.py` gains two steps: Figure 1\n"
          "  (`revision13/make_fig_arch.py`) and its check against the simulator (`revision13/check_fig_arch.py`).\n"
          "- Scan: 0 unjustified. The archived version 13 joins the mirror-address entry, and the record scripts of versions 13 and 14\n"
          "  join version 10's.\n"
          f"- FINAL_CHECK_OK; {FILES:,} files, {MB} MB (`records/deposit/`; v1.3's records are in `records/deposit/v1.3/`).\n"
          "- Publishing is one push and one release, as for v1.3 (the same two commands with v1.4 and the new commit):\n"
          "  `git -C C:/Projects/memistor-ecram-training push origin main`, then\n"
          f"  `gh release create v1.4 --repo Questeria/memistor-ecram-training --target {COMMIT} --title \"v1.4: code, records and pulse\n"
          "  draws for the memistor paper (version 14)\" --notes-file RELEASE-NOTES.md`, with the tag pinned to the verified commit.\n"
          "  The new version DOI comes from Zenodo; the concept DOI stays.\n\n")
pub = sub(pub, "`pod/build_rev8.sh` for versions 9 to 13", "`pod/build_rev8.sh` for versions 9 to 13 and `pod/build_rev9.sh` for version 14")
pub = sub(pub, "loose copies of the files; `revision12/check_build_v13.py` (version 13) runs",
          "loose copies of the files; `revision13/check_build_v14.py` (version 14) runs `revision6/check_build_v7.py` and reads the version-14\n"
          "   proofs: the word-count text diff `revision13/pdf_text_diff_v14.py` (v13 -> v14, reference numbers as [#], one page more), the\n"
          "   name check in WSL and in Windows, numbers freshness, Figure 1 against the simulator, Figure 4, the reset and the Welch test;\n"
          "   `revision12/check_build_v13.py` (version 13) runs")
pub = sub(pub, 'for version 13: "43 pages, 3 figures; code and data: https://doi.org/10.5281/zenodo.23748861".',
          'for version 14: "44 pages, 4 figures; code and data: https://doi.org/10.5281/zenodo.23748861".')
(P / "PUBLISHING.md").write_bytes((pub.replace("\n", "\r\n") if CRLF else pub).encode("utf-8"))

rd = (P / "README.md").read_bytes().decode("utf-8")
CRLF_RD = "\r\n" in rd
rd = rd.replace("\r\n", "\n").rstrip("\n") + "\n"
rd += f"""
## Revision v14 (2026-10-31, director lane): the answer to review 11 (no experiment; no result changed; $0)

- Review 11 (ChatGPT, `reviews/REVIEW-11-chatgpt-20261031-full.md`, pasted by the owner) read version 13 (43 pages), spot-checked its
  numbers (all agree) and compared related work; it did not rerun anything. Every finding was verified against `tex/v13`, the records,
  the code and primary metadata (`revision13/verify_findings_11.py`, `revision13/cite_check_v14.py`); `RESPONSE-TO-REVIEW-11.md` gives
  each verdict.
- Related work: Byun et al. (Adv. Intell. Syst. 7(5) 2400543, doi 10.1002/aisy.202400543) confirmed on Crossref and cited, with what
  this study adds; `records/CITE-CHECK.json` 49 of 49. Xu et al. (PubMed 42915660) is the existing `xu2026`, now also in Stage 1.
- Energy (Section 5): the GPU equation 6P/(Fu) with every input range (the low end 7.05 pJ is 500 W at 43 %); the TT family's
  digital-cost boundary; the ratio is a per-operation, read-dominated figure, not energy to a quality.
- Wording: the subtitle's "device specification sheet" is now "exploratory device sensitivity analysis" (judgement call; the title is
  otherwise unchanged), as are the abstract, introduction, Section 4.5 (one-at-a-time ranges do not bound joint deviations),
  limitations and Appendix B.
- New Figure 1 (`revision13/make_fig_arch.py`): device vs digital, for SGD and the TT family; `revision13/check_fig_arch.py` checks it
  against `sim/memsim_rev.py` (`records/revision13/FIG-ARCH-CHECK.json`, 4 of 4 faults caught).
- Limitations: the control ladder; roadmap: computational follow-ups (full CIFAR and LM trajectories with correlated streams first,
  pulse-length and update-management comparisons, the ladder, fair tuning of analog SGD).
- Correction history moved word for word from Sections 3, 4.3, 4.4 and 4.5 into Appendix F, or removed where E or F already held it.
- Text: `revision13/edit_14.py`; availability (archive v1.4, eleven reviews, the eleventh response) and the history (version 14).
  `revision13/archive_v13.py` archived `tex/v13` and `build/v13`.
- Build: `pod/build_payload_rev9.py --out H:/x1000/memistor-paper/rev13/v14e`, `run.sh` in WSL. Both variants have 44 pages
  (version 13: 43).
- Checks: `revision13/check_build_v14.py <out> --json records/revision13/ARTIFACT-CHECK-v14.json` is ALL_OK. The word-count diff
  v13 -> v14 has 58 expected edits and 0 unexplained in both variants (reference numbers as [#]), one page more; the v12 control
  fails. Paper commit {PAPER_COMMIT}.
- Archive v1.4 (`F:/x1000-deposit/memistor-deposit-v1.4`): clean room {ROOM}; mutation {m_ok} of {len(mut)}; scan 0 unjustified;
  FINAL_CHECK_OK; {FILES:,} files, {MB} MB. Committed locally as {COMMIT}, NOT pushed.
- Left:
  - the owner's go to publish v1.4 (push + release, as for v1.3; Zenodo mints its version DOI);
  - then the owner's arXiv submission of version 14, from the Desktop folder "memistor paper - arXiv submission (v14)".
"""
(P / "README.md").write_bytes((rd.replace("\n", "\r\n") if CRLF_RD else rd).encode("utf-8"))

sp = P / "STATUS.json"
st = json.loads(sp.read_bytes().decode("utf-8"))
st["updated_et"] = NOW
st["done"].append(f"review 11 (ChatGPT, of v13) answered (RESPONSE-TO-REVIEW-11.md: Byun et al. cited, GPU equation and inputs, energy "
                  f"boundary, exploratory sensitivity wording incl. subtitle, Figure 1, control ladder, follow-ups, history moved to "
                  f"Appendix F); paper version 14 (44 pages; check_build_v14 ALL_OK; commit {PAPER_COMMIT}); archive v1.4 built on F:, "
                  f"clean room {n_ok}/{n_all}, mutation {m_ok}/{len(mut)}, scan 0 unjustified, FINAL_CHECK_OK, {FILES} files, {MB} MB, "
                  f"committed locally {COMMIT} (NOT pushed)")
st["next"] = ["the owner's go: publish archive v1.4 (git push origin main + gh release create v1.4, tag pinned to " + COMMIT
              + "; the same commands as v1.3); then record its Zenodo version DOI in PUBLISHING.md and STATUS.json",
              "then the owner submits version 14 to arXiv from the Desktop folder \"memistor paper - arXiv submission (v14)\" (44 pages); "
              "account, endorsement and terms are his",
              "then: record the arXiv identifier in PUBLISHING.md and STATUS.json"]
st["waiting_on"] = ["the owner: a go to publish v1.4, then the arXiv submission of version 14"]
st["v14"] = dict(summary="review 11 (ChatGPT, of v13): Byun et al. cited; GPU energy equation with every input range; TT digital-cost "
                         "boundary; per-operation read-dominated ratio; 'exploratory device sensitivity analysis' (subtitle too); new "
                         "Figure 1 (device vs digital) checked against the simulator; control ladder; computational follow-ups; correction "
                         "history moved to Appendix F; availability names v1.4; 44 pages; no experiment, no result changed",
                 build_dir="H:/x1000/memistor-paper/rev13/v14e",
                 checks="records/revision13/ARTIFACT-CHECK-v14.json (ALL_OK) and the records beside it",
                 deposit=dict(build="F:/x1000-deposit/memistor-deposit-v1.4", local_commit=COMMIT, parent="03474b26b", pushed=False,
                              files=FILES, mb=MB),
                 continue_with="read README.md section Revision v14")
sp.write_bytes((json.dumps(st, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
print("recorded v14 / v1.4 in PUBLISHING.md, README.md, STATUS.json")
