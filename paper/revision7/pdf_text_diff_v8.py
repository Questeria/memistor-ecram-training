"""ME-REVISE-7: prove version 8's PDF text equals version 7's except for the edits version 8 meant to make.

Same extraction as revision6/pdf_text_diff.py (page numbers dropped, ligatures folded, re-broken hyphens joined, word by word).  The old
author name is first replaced by the new one in version 7's word list (and the number of replacements is recorded and must equal the
number of occurrences of the new name in version 8 minus one, the mention in the new history paragraph), so the name change cannot hide any other difference.  Every other
differing hunk must equal one of the EXPECTED edits exactly: the six -> seven count, the inventory, the history, and the ChatGPT
sentence (once per variant's position, the same string).  Anything else fails.  Fails also on version 6 against version 8.

    python -B revision7/pdf_text_diff_v8.py <v7.pdf> <v8.pdf> [--json out.json]       (WSL venv with PyMuPDF)
"""
import difflib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "revision6"))
import pdf_text_diff as D6  # noqa: E402

OLD = "Quest" + "eria"
NEW = ("Anthony", "DeMarco")

CHATGPT = ("ChatGPT (OpenAI), also an AI system and not an author, reviewed versions 1 to 7 of this paper in turn: it checked the "
           "record hashes, independently recomputed the revised statistics, and reported errors, each of which was verified against "
           "the files and corrected where confirmed (Appendix F).")
# (removed, added)
EXPECTED = [
    ("2026; this paper)", "2026)"),
    ("six", "seven"),
    ("RESPONSE-TO-REVIEW-6.md);", "RESPONSE-TO-REVIEW-6.md, RESPONSE-TO-REVIEW-7.md);"),
    ("", "Version 8 (October 27, 2026; this paper) answers a seventh review, which found no actionable defect "
         "(RESPONSE-TO-REVIEW-7.md; no experiment was run and no number changed). It carries two changes ordered by the author: "
         "his official name, Anthony DeMarco, replaces the name printed in versions 1 to 7, and the contribution statement credits "
         "ChatGPT’s reviews."),
    ("", CHATGPT),
]
EXPECTED_COUNT = {("", CHATGPT): 1}       # each PDF holds one variant, so the sentence is inserted once


def rename(words):
    out, n = [], 0
    for w in words:
        if w.startswith(OLD):
            n += 1
            out += [NEW[0], NEW[1] + w[len(OLD):]]
        else:
            out.append(w)
    return out, n


def run(old_pdf, new_pdf, count_expected=True):
    a, na = D6.words(old_pdf)
    b, nb = D6.words(new_pdf)
    a2, n_old = rename(a)
    n_new = sum(1 for i in range(len(b) - 1) if b[i] == NEW[0] and b[i + 1].startswith(NEW[1]))
    sm = difflib.SequenceMatcher(None, a2, b, autojunk=False)
    hunks = [dict(tag=tag, removed=" ".join(a2[i1:i2]), added=" ".join(b[j1:j2]))
             for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]
    exp = set(EXPECTED)
    r = dict(pages_old=na, pages_new=nb, words_old=len(a), words_new=len(b), old_name_replacements=n_old, new_name_occurrences_in_new=n_new,
             hunks=hunks)
    r["unexpected_hunks"] = [h for h in hunks if (h["removed"], h["added"]) not in exp]
    seen = {(h["removed"], h["added"]) for h in hunks}
    r["expected_not_seen"] = [e for e in EXPECTED if e not in seen]
    cnt = {k: sum(1 for h in hunks if (h["removed"], h["added"]) == k) for k in EXPECTED_COUNT}
    r["count_mismatch"] = [dict(hunk=k[1][:60], want=v, got=cnt[k]) for k, v in EXPECTED_COUNT.items() if cnt[k] != v]
    r["name_count_ok"] = n_new == n_old + 1       # +1: the name in the new history paragraph
    r["ok"] = (not r["unexpected_hunks"] and not r["expected_not_seen"] and not r["count_mismatch"] and r["name_count_ok"])
    return r


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    r = run(a[0], a[1])
    print("pages", r["pages_old"], "->", r["pages_new"], "| words", r["words_old"], "->", r["words_new"], "| old name replaced",
          r["old_name_replacements"], "new name in new", r["new_name_occurrences_in_new"], "| hunks", len(r["hunks"]),
          "| unexpected", len(r["unexpected_hunks"]), "| expected not seen", len(r["expected_not_seen"]),
          "| count mismatch", len(r["count_mismatch"]), "|", "TEXT_UNCHANGED_EXCEPT_EXPECTED" if r["ok"] else "TEXT_DIFFERS")
    for h in r["hunks"]:
        print("  ", h["tag"], "| -", h["removed"][:90], "| +", h["added"][:150])
    if "--json" in sys.argv:
        open(sys.argv[sys.argv.index("--json") + 1], "wb").write((json.dumps(r, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    sys.exit(0 if r["ok"] else 1)
