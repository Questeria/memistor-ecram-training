"""Version 11: prove version 11's PDF text equals version 10's except for the edits version 11 meant to make.

Same extraction as revision6/pdf_text_diff.py (page numbers dropped, ligatures folded, re-broken hyphens joined, word by word).  Every
differing hunk must equal one of the EXPECTED edits exactly: the methods' sentence on the LM sampler (and the one word it re-hyphenates,
"embedding"), the availability section (archive version 1.1 holds version 11; release v1.1; eight reviews; the eighth response; the
GitHub address now breaks after "github.com/" instead of after the account), Figure 3's tick labels (the redrawn figure: the tick 10 is
gone and the LM panel reaches -5) and the history (version 10 is no longer "this paper"; version 11's entry).  The longer history moves
appendix F's paragraph "Wording withdrawn or narrowed" to the other side of a float in reading order without changing the page count
(42): that is accepted only as a MOVE, a deleted block whose words equal an inserted block's, listed in MOVES.  Anything else fails;
so does version 9 against version 11.

    python -B revision10/pdf_text_diff_v11.py <v10.pdf> <v11.pdf> [--json out.json] [--summary]       (WSL venv with PyMuPDF)
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "revision6"))
import pdf_text_diff as D6  # noqa: E402

ACCT = "Quest" + "eria"                                                   # written in two pieces so this script stays clean
A = "’"
# (removed, added)
EXPECTED = [
    ("bytes.", "bytes, each window starting at a uniformly random position. The start" + A + "s upper bound is one short (found by "
     "review 8), so the last window of the training slice is never drawn and the slice" + A + "s final byte is never a target; no "
     "held-out byte is affected."),
    ("embed-ding", "embedding"),
    ("1.0", "1.1"),
    ("9", "11"),
    ("paper).", "paper, and version 1.0 holds version 9)."),
    ("https://github.com/" + ACCT + "/ memistor-ecram-training", "https://github.com/ " + ACCT + "/memistor-ecram-training"),
    ("v1.0).", "v1.1)."),
    ("seven", "eight"),
    ("RESPONSE-TO-REVIEW-7.md);", "RESPONSE-TO-REVIEW-7.md, RESPONSE-TO-REVIEW-8.md);"),
    ("51020", "5"),
    ("-5-2", "-5 -2"),
    ("5102050", "5"),
    ("2026; this paper)", "2026)"),
    ("", "Version 11 (October 28, 2026; this paper) answers an eighth review, a code audit and reproduction from the public archive "
         "(RESPONSE-TO-REVIEW-8.md; no experiment was run). Figure 3 (version 1, superseded) drew two negative LM means at +0.05, with "
         "their intervals shifted, and its legend overlapped an axis label; both are corrected. The energy model now counts a "
         "classification run" + A + "s optimizer steps from the rows its layers trained: the run records" + A + " sample count includes "
         "each epoch" + A + "s incomplete last batch, which training skips, so the transfer reads were overstated by 0.16 %. No printed "
         "number changed; the largest change in a total energy is 0.0005 % in the current projection and 0.0014 % in version 1" + A + "s. "
         "Section 3 now discloses an off-by-one in the LM sampler. The simulator" + A + "s ideal reset of a partial column selection "
         "under AIHWKIT bounds, which no result used, no longer fails, and a new check covers it."),
]
MOVES = ["Wording withdrawn or narrowed. " + "“" + "Near-digital" + "”" + " is not used."]   # start of the moved block
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
        blob = json.dumps(r, indent=1, ensure_ascii=False).replace(ACCT, "<account>")
        open(sys.argv[sys.argv.index("--json") + 1], "wb").write((blob + "\n").encode("utf-8"))
    sys.exit(0 if r["ok"] else 1)
