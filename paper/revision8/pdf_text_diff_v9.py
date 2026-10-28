"""ME-DEPOSIT-2: prove version 9's PDF text equals version 8's except for the edits version 9 meant to make.

Same extraction as revision6/pdf_text_diff.py (page numbers dropped, ligatures folded, re-broken hyphens joined, word by word).  Every
differing hunk must equal one of the EXPECTED edits exactly: the deviation count R1--R6 -> R1--R8 (the one regenerated number) and the
history (version 8 is no longer "this paper"; version 9's one entry).  The added history sentence is longer than the slack of the
paragraph's last line, so appendix F's last page is pushed onto a new page (41 -> 42 pages): Table 26's paragraph then follows Table 26's
page.  That is accepted only as a MOVE: a deleted block whose words equal an inserted block's, listed in MOVES, and exactly one more page.
Anything else fails; so does version 7 against version 9.

    python -B revision8/pdf_text_diff_v9.py <old.pdf> <v9.pdf> [--json out.json]       (WSL venv with PyMuPDF)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "revision6"))
import pdf_text_diff as D6  # noqa: E402

# (removed, added)
EXPECTED = [
    ("R1\u2013R6", "R1\u2013R8"),
    ("2026; this paper)", "2026)"),
    ("", "Version 9 (October 28, 2026; this paper) corrects the deviation count R1\u2013R6 to R1\u2013R8, found by the deposit\u2019s "
         "clean-room regeneration."),
]
MOVES = ["Version 3\u2019s update probes (superseded). Table 26 is version 3\u2019s analysis of the update probes"]   # start of the moved block
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
    r["pages_ok"] = r["pages_new"] == r["pages_old"] + (1 if moved else 0)
    r["ok"] = not r["unexpected_hunks"] and not r["expected_not_seen"] and r["pages_ok"] and len(moved) == len(MOVES)
    return r


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    r = run(a[0], a[1])
    print("pages", r["pages_old"], "->", r["pages_new"], "| words", r["words_old"], "->", r["words_new"], "| hunks", len(r["hunks"]),
          "| moved", len(r["moved_blocks"]), "| unexpected", len(r["unexpected_hunks"]), "| expected not seen", len(r["expected_not_seen"]),
          "|", "TEXT_UNCHANGED_EXCEPT_EXPECTED" if r["ok"] else "TEXT_DIFFERS")
    for h in r["hunks"]:
        print("  ", h["tag"], "| -", h["removed"][:60], "| +", h["added"][:130])
    if "--summary" in sys.argv:       # keep counts only (a v7 -> v9 record would otherwise quote the old author name)
        for k in ("hunks", "unexpected_hunks"):
            r[k] = [dict(tag=h["tag"], removed_words=len(h["removed"].split()), added_words=len(h["added"].split())) for h in r[k]]
    if "--json" in sys.argv:
        open(sys.argv[sys.argv.index("--json") + 1], "wb").write((json.dumps(r, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    sys.exit(0 if r["ok"] else 1)
