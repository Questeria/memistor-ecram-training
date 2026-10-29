"""Version 10: record the published deposit and version 10 in PUBLISHING.md, README.md and STATUS.json (anchors matched once each).

    python -I -B revision9/record_v10.py
"""
import glob
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

P = Path(__file__).resolve().parent.parent
NOW = datetime.now(timezone(timedelta(hours=-4))).strftime("%Y-%m-%d %H:%M ET")
CONCEPT, V1 = "10.5281/zenodo.23748861", "10.5281/zenodo.23748862"
GH = "https://github.com/Questeria/memistor-ecram-training"
FIGS = sum(len(re.findall(r"\\includegraphics", Path(f).read_text("utf-8"))) for f in glob.glob(str(P / "tex" / "*.tex")))


def edit(path, subs):
    t = path.read_bytes().decode("utf-8")
    for tag, a, b in subs:
        pat = r"\s+".join(re.escape(w) for w in a.split())
        n = len(re.findall(pat, t))
        assert n == 1, (path.name, tag, n)
        t = re.sub(pat, lambda m: b, t)
    path.write_bytes(t.encode("utf-8"))


edit(P / "PUBLISHING.md", [
    ("status", "**Status (2026-10-28): the deposit is BUILT and verified; the owner's one command publishes it.**",
     "**Status (2026-10-28, evening ET): PUBLISHED by the owner's command; version 10 of the paper carries the DOI.**\n\n"
     "- Cite the concept DOI **" + CONCEPT + "** (all versions; https://doi.org/" + CONCEPT + "). Version 1.0 is " + V1 + "\n"
     "  (https://zenodo.org/records/23748862; Zenodo dates it 2026-10-29; resource type Software; CC BY 4.0 on the record, MIT for the code as its\n"
     "  description states; one file `Questeria/memistor-ecram-training-v1.0.zip`, 100,543,489 bytes, md5 8813e49b550ec91f3b7ee1dca166b074,\n"
     "  which is GitHub's archive of tag v1.0). Version 1.0 holds version 9 of the paper, as version 10's availability section says.\n"
     "- GitHub, under the author's account: " + GH + "; branch `main` and tag `v1.0` are both at\n"
     "  076624fbc58b2d50041bf88f2549ff58e37ee52d, the commit verified before publishing (`git ls-remote`, 2026-10-28).\n"
     "- Zenodo's Files panel says \"Too many files inside the ZIP file.\": its previewer does not list an archive this large (3,338 files).\n"
     "  It is a display limit; the ZIP downloads whole."),
    ("pushed", "NOT pushed.", "pushed by the owner's command (2026-10-28)."),
    ("launcher", "- To publish: double-click", "- Published with (2026-10-28, by the owner): double-click"),
    ("step 3", "3. Put that DOI in the paper's \"Code and data availability\" paragraph (`tex/body.tex`, the `\\availability` text) and rebuild.",
     "3. Put that DOI in the paper's \"Code and data availability\" paragraph (`tex/body.tex`, the `\\availability` text) and rebuild.\n"
     "   Done in version 10 (`revision9/edit_10.py`), with the GitHub mirror under the author's account."),
    ("build list", "and `pod/build_rev8.sh` for version 9, on the desk", "and `pod/build_rev8.sh` for versions 9 and 10, on the desk"),
    ("checks", "loose copies of the files; `revision8/check_build_v9.py` runs",
     "loose copies of the files; `revision9/check_build_v10.py` (version 10) runs `revision6/check_build_v7.py` and reads the version-10 proofs:\n"
     "   `revision9/name_check_v10.py` (the old name appears only inside the GitHub mirror's address, which the owner allowed on 2026-10-28),\n"
     "   `revision9/pdf_text_diff_v10.py` (v9 -> v10: the expected edits only) and the numbers-freshness record; `revision8/check_build_v9.py` runs"),
    ("comments", "Add the comments field, e.g. \"N pages, 6 figures; code and data: <Zenodo DOI>\".",
     "Add the comments field; for version 10: \"42 pages, %d figures; code and data: https://doi.org/%s\"." % (FIGS, CONCEPT)),
])

readme = P / "README.md"
readme.write_bytes(readme.read_bytes() + ("""
## Revision v10 (2026-10-28, director): the public archive and its DOI (no experiment; $0)

- The owner published the deposit with his one command on the evening of 2026-10-28 ET: Zenodo concept DOI %s (version 1.0: %s);
  GitHub %s (`main` and tag `v1.0` at 076624fb, the commit verified before publishing).
- Edits (`revision9/edit_10.py`, each anchor matched once): the availability section names the archive, its DOI and its GitHub mirror under the
  author's account (owner, 2026-10-28: "The GitHub is fine with Questeria, just make sure it is clear"), the reviews (`reviews/`) and the draws
  (`draws/rev3/`) inside it, the redactions and `fetch_data.py`; the history gains version 10. No number changed. Every path the section names
  was checked to exist in the deposit.
- Build: `pod/build_payload_rev8.py --out H:/x1000/memistor-paper/rev9/v10`, then its `run.sh` (= `pod/build_rev8.sh`, unchanged) in WSL Ubuntu
  (`wsl -d Ubuntu -e bash -c ...`: without `-e` the default shell expands `$` variables first), tectonic 0.15.0; 42 pages (unchanged); the
  arXiv archive compiles alone; the HTML is complete and clean (`records/revision9/BUILD-STEPS-v10.txt`). Version 9's outputs are in `build/v9`.
- Checks: `revision9/check_build_v10.py <out> --json records/revision9/ARTIFACT-CHECK-v10.json` is ALL_OK: `revision6/check_build_v7.py`;
  `NAME-CHECK-v10.json` (`revision9/name_check_v10.py`: the old name only inside the mirror's address, counted per channel against the address;
  it fails on a planted name in the HTML, a PDF page, a tex file or an archive member, on a near-miss address and on version 7, and accepts
  the address broken across two lines); `PDF-TEXT-DIFF-main*.json` (`revision9/pdf_text_diff_v10.py`: v9 -> v10, 10 expected edits and one pure
  move of appendix B's first block, pages equal); `PDF-TEXT-DIFF-negative-v8-v10.json` (fails as it must); `NUMBERS-FRESH.json` (self-test)
  and the live numbers check.
""" % (CONCEPT, V1, GH)).encode("utf-8"))

sp = P / "STATUS.json"
d = json.loads(sp.read_bytes().decode("utf-8"))
d["v10"] = dict(summary="the public archive in the availability section: Zenodo concept DOI %s (version 1.0 %s, holding paper v9), GitHub "
                        "mirror under the author's account; reviews and draws located in it; redactions; fetch_data.py; history entry; 42 pages; "
                        "no number changed" % (CONCEPT, V1),
                build_dir="H:/x1000/memistor-paper/rev9/v10",
                checks="records/revision9/ARTIFACT-CHECK-v10.json (ALL_OK), NAME-CHECK-v10.json, PDF-TEXT-DIFF-main*.json, "
                       "PDF-TEXT-DIFF-negative-v8-v10.json, NUMBERS-FRESH.json",
                continue_with="read README.md section Revision v10; the owner submits build/arxiv-source.tar.gz (PUBLISHING.md section 5)")
d["deposit"] = dict(concept_doi=CONCEPT, version_1_0_doi=V1, github=GH, tag_v1_0_commit="076624fbc58b2d50041bf88f2549ff58e37ee52d",
                    zenodo_file_bytes=100543489, published_et="2026-10-28 evening")
d["next"] = ["owner: submit version 10 to arXiv: build/arxiv-source.tar.gz (main-arxiv), abstract build/arxiv-abstract.txt, comments field "
             "in PUBLISHING.md section 5; arXiv may ask for an endorsement first (section 2). Posting stays his act."]
d["state"] = "done"
d["updated_et"] = NOW
sp.write_bytes((json.dumps(d, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
print("recorded; figures", FIGS, "| updated", NOW)
