"""Version 11: record the answer to review 8, version 11 and archive release v1.1 (built, not pushed) in PUBLISHING.md, README.md
and STATUS.json (anchors matched once each).  Run before the archive is built, so its copies of PUBLISHING.md and README.md say so.

    python -I -B revision10/record_v11.py
"""
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

P = Path(__file__).resolve().parent.parent
NOW = datetime.now(timezone(timedelta(hours=-4))).strftime("%Y-%m-%d %H:%M ET")
CONCEPT = "10.5281/zenodo.23748861"
LAUNCHER = "Publish the memistor deposit v1.1.cmd"


def edit(path, subs):
    t = path.read_bytes().decode("utf-8")
    for tag, a, b in subs:
        pat = r"\s+".join(re.escape(w) for w in a.split())
        n = len(re.findall(pat, t))
        assert n == 1, (path.name, tag, n)
        t = re.sub(pat, lambda m: b, t)
    path.write_bytes(t.encode("utf-8"))


edit(P / "PUBLISHING.md", [
    ("status", "**Status (2026-10-28, evening ET): PUBLISHED by the owner's command; version 10 of the paper carries the DOI.**",
     "**Status (2026-10-28, late evening ET): version 11 of the paper answers review 8. Release v1.1 of the archive, which holds version 11, is BUILT and\n"
     "verified as one new local commit in `C:/Projects/memistor-ecram-training`, NOT pushed. The owner's one command publishes it:\n"
     "double-click `" + LAUNCHER + "` (on the Desktop; a copy is in this folder). It pushes the commit to `main` and runs\n"
     "`gh release create v1.1`; Zenodo archives the release under the same concept DOI and mints its own version DOI.**\n\n"
     "**Release v1.0 (2026-10-28, evening ET): PUBLISHED by the owner's command; version 10 of the paper carries the DOI.**"),
    ("build list", "and `pod/build_rev8.sh` for versions 9 and 10, on the desk", "and `pod/build_rev8.sh` for versions 9, 10 and 11, on the desk"),
    ("checks", "loose copies of the files; `revision9/check_build_v10.py` (version 10) runs",
     "loose copies of the files; `revision10/check_build_v11.py` (version 11) runs `revision6/check_build_v7.py` and reads the version-11 proofs:\n"
     "   the name check (`revision9/name_check_v10.py`, the same rule), `revision10/pdf_text_diff_v11.py` (v10 -> v11: the expected edits only),\n"
     "   `revision10/check_fig_main.py` (Figure 3 draws every mean and interval of its results; its legend overlaps no label),\n"
     "   `sim/test_ideal_reset_cols.py` and the numbers-freshness record; `revision9/check_build_v10.py` (version 10) runs"),
    ("comments", "Add the comments field; for version 10: \"42 pages, 3 figures; code and data: https://doi.org/" + CONCEPT + "\".",
     "Add the comments field; for version 11: \"42 pages, 3 figures; code and data: https://doi.org/" + CONCEPT + "\"."),
])

readme = P / "README.md"
readme.write_bytes(readme.read_bytes() + ("""
## Revision v11 (2026-10-28, director): the answer to review 8 (no experiment; $0)

- Review 8 (ChatGPT in Codex, `reviews/REVIEW-8-chatgpt-20261028-full.md`) audited release v1.0 against version 10: a fresh clone, the
  CPU reproduction (24 of 24 steps), the simulator suites and a line-by-line read of the computational code. It reported seven minor and
  two cosmetic findings and no change to a conclusion. Every finding was verified against the files first; all nine are confirmed.
  `RESPONSE-TO-REVIEW-8.md` gives each one with its verification and change.
- Changes: `make_figures.py` (Figure 3 plots the mean itself; the legend has its own space; the tick 10 is dropped);
  `energy/energy_system.py` (a classification run's steps from its smallest layer row count, not from `samples`, which counts the
  skipped incomplete batch), with `records/ENERGY-SYSTEM.json` and `records/revision/ENERGY-REVISION.json` regenerated and no number
  file or table changed; `sim/memsim_rev.py` (`Tile.clip_cols`: the ideal reset of a partial column selection under AIHWKIT bounds no
  longer fails); the methods disclose the LM sampler's off-by-one, which is kept as run. Every change is checked:
  - `sim/test_ideal_reset_cols.py` checks the reset;
  - `revision10/check_fig_main.py` checks Figure 3 (version 10's code fails it on exactly the review's two cells);
  - `revision10/derive_rev_spec_p.py` re-derives Table 12's file byte for byte, so the archive's `reproduce_all.py` now regenerates
    every table.
- Edits (`revision10/edit_11.py`): Section 9 names archive v1.1, release v1.1, eight reviews and `RESPONSE-TO-REVIEW-8.md`. Section 3 has
  the sampler sentence, and the history gains version 11. `revision10/archive_v9_v10.py` archived `tex/v9`, `tex/v10` and `build/v10`.
- Build: `pod/build_payload_rev8.py --out H:/x1000/memistor-paper/rev10/v11b`, then its `run.sh` in WSL Ubuntu inside `~/me-rev3-venv`
  (the system `python3` refuses pip installs). The result has 42 pages, an arXiv archive that compiles alone, and complete, clean HTML
  (`records/revision10/BUILD-STEPS-v11.txt`).
- Checks: `revision10/check_build_v11.py <out> --json records/revision10/ARTIFACT-CHECK-v11.json` is ALL_OK. It covers:
  - the v7 artifact checks;
  - `NAME-CHECK-v11.json`;
  - `PDF-TEXT-DIFF-main*.json`: v10 -> v11, 14 expected hunks, two reflow hunks and one pure move, pages equal;
  - `PDF-TEXT-DIFF-negative-v9-v11.json`, which fails as it must;
  - `NUMBERS-FRESH.json` and the live numbers check;
  - `FIG-MAIN-CHECK.json` and `TESTS-IDEAL-RESET-COLS.json`.
- Archive v1.1: `make_deposit.py` builds it into a fresh folder, with the README fixes of findings 5 to 8 (a quick start that runs as
  written, `requirements.txt` and an install section, the known defects, a size counted last). `deposit_cleanroom.py` reproduces it in a
  clean room, `sync_deposit.py` lays it over the repository as one commit, and the owner's `""" + LAUNCHER + """` publishes it.
""").encode("utf-8"))

sp = P / "STATUS.json"
d = json.loads(sp.read_bytes().decode("utf-8"))
d["review_8"]["state"] = ("answered 2026-10-28: all nine findings confirmed against the files and fixed (1-3, 5-9) or disclosed (4, kept as run); "
                          "version 11; archive v1.1 built (RESPONSE-TO-REVIEW-8.md)")
d["v11"] = dict(summary="answer to review 8: Figure 3 redrawn (true means; legend clear), energy steps from layer rows (no printed number "
                        "changed), ideal-reset slice fix with a new check, the LM sampler's off-by-one disclosed in the methods, availability "
                        "names archive v1.1 and eight reviews; 42 pages",
                build_dir="H:/x1000/memistor-paper/rev10/v11b",
                checks="records/revision10/ARTIFACT-CHECK-v11.json (ALL_OK) and the records beside it",
                continue_with="read README.md section Revision v11")
d["next"] = ["owner: double-click '" + LAUNCHER + "' (Desktop): it pushes the v1.1 commit and creates release v1.1 (Zenodo archives it "
             "under the concept DOI " + CONCEPT + ")",
             "then owner: submit version 11 to arXiv: build/arxiv-source.tar.gz (main-arxiv), abstract build/arxiv-abstract.txt, comments field "
             "in PUBLISHING.md section 5; arXiv may ask for an endorsement first (section 2). Posting stays his act."]
d["state"] = "done"
d["updated_et"] = NOW
sp.write_bytes((json.dumps(d, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
print("recorded | updated", NOW)
