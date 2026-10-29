"""Version 10: prove version 10's PDF text equals version 9's except for the edits version 10 meant to make.

Same extraction as revision6/pdf_text_diff.py (page numbers dropped, ligatures folded, re-broken hyphens joined, word by word).  Every
differing hunk must equal one of the EXPECTED edits exactly: the availability section (the archive, its DOI and its GitHub mirror under the
author's account, the reviews and the draws located in it, the redactions and the dataset download) and the history (version 9 is no
longer "this paper"; version 10's one entry).  The longer availability section moves the first block of appendix B (its heading and its
first paragraphs) to the other side of a float in reading order without changing the page count (42): that is accepted only as a MOVE,
a deleted block whose words equal an inserted block's, listed in MOVES.  Anything else fails; so does version 8 against version 10.

    python -B revision9/pdf_text_diff_v10.py <v9.pdf> <v10.pdf> [--json out.json] [--summary]       (WSL venv with PyMuPDF)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "revision6"))
import pdf_text_diff as D6  # noqa: E402

GH = "https://github.com/" + "Quest" + "eria" + "/ memistor-ecram-training"     # the address breaks after the account in the PDF
A = "’"
# (removed, added)
EXPECTED = [
    ("Nothing has been deposited publicly yet. On deposit, one", "One public"),
    ("will hold", "holds"),
    ("", "Zenodo, doi:10.5281/zenodo.23748861 (this DOI cites all versions; version 1.0 of the archive holds version 9 of this paper). "
         "The same files are on GitHub under the author" + A + "s account, " + GH + " (release v1.0). Code is under the MIT License; "
         "records, pulse draws, text and figures are under CC BY 4.0. The archive keeps the study folder" + A + "s layout, and the paths "
         "below are relative to its paper/ directory. It holds:"),
    ("(DEVIATIONS-PAPER.md)", "(DEVIATIONS-PAPER.md), the seven independent reviews (reviews/)"),
    ("the seven independent reviews", "them"),
    ("out-side the code repository;", "in draws/rev3/;"),
    ("The archive DOI will be added on deposit (Zenodo).", "In the archive" + A + "s copies of the reviews and of one response, local file "
     "paths are shortened for privacy; the archive" + A + "s REDACTIONS.md lists every change."),
    ("digest.", "digest; they are not redistributed, and the archive" + A + "s fetch_data.py downloads them and checks the digests."),
    ("2026; this paper)", "2026)"),
    ("", "Version 10 (October 28, 2026; this paper) gives the public archive, its DOI and its GitHub mirror in Section 9; no number changed."),
]
MOVES = ["B Hyperparameter selection Learning rates and algorithm settings were selected on validation splits only"]   # start of the moved block
D6.EXPECTED = EXPECTED


def run(old_pdf, new_pdf):
    r = D6.judge(D6.diff(old_pdf, new_pdf))
    hunks = r["hunks"]
    moved = []
    for h in hunks:
        if h["tag"] == "delete" and any(h["removed"].startswith(m) for m in MOVES):
            if any(g["tag"] == "insert" and g["added"] == h["removed"] for g in hunks):
                moved.append(h["removed"][:80])
    r["moved_blocks"] = moved
    r["unexpected_hunks"] = [h for h in r["unexpected_hunks"]
                             if not ((h["tag"] == "delete" and h["removed"][:80] in moved)
                                     or (h["tag"] == "insert" and any(h["added"] == g["removed"] for g in hunks if g["removed"][:80] in moved)))]
    r["pages_ok"] = r["pages_new"] == r["pages_old"]
    r["ok"] = not r["unexpected_hunks"] and not r["expected_not_seen"] and r["pages_ok"] and len(moved) == len(MOVES)
    return r


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    r = run(a[0], a[1])
    print("pages", r["pages_old"], "->", r["pages_new"], "| words", r["words_old"], "->", r["words_new"], "| hunks", len(r["hunks"]),
          "| moved", len(r["moved_blocks"]), "| unexpected", len(r["unexpected_hunks"]), "| expected not seen", len(r["expected_not_seen"]),
          "|", "TEXT_UNCHANGED_EXCEPT_EXPECTED" if r["ok"] else "TEXT_DIFFERS")
    if "--summary" in sys.argv:       # keep counts only
        for k in ("hunks", "unexpected_hunks"):
            r[k] = [dict(tag=h["tag"], removed_words=len(h["removed"].split()), added_words=len(h["added"].split())) for h in r[k]]
    if "--json" in sys.argv:
        blob = json.dumps(r, indent=1, ensure_ascii=False).replace("Quest" + "eria", "<account>")
        open(sys.argv[sys.argv.index("--json") + 1], "wb").write((blob + "\n").encode("utf-8"))
    sys.exit(0 if r["ok"] else 1)
