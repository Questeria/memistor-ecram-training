"""ME-REVISE-6: prove a new PDF's text equals the previous version's except for the edits the version meant to make.

Both PDFs' text is extracted page by page (PyMuPDF), joined, lone page numbers dropped, ligatures folded (NFKC), a line-break hyphen
('point- estimate', the same word re-broken because the history grew) joined, whitespace normalised, and compared word by word
(difflib).  Every differing hunk must equal one of the EXPECTED edits (the removed and added strings exactly); anything else fails.
The check fails on a pair of versions that differ more (version 5 against version 7: 12 unexpected hunks).

    python -B revision6/pdf_text_diff.py <old.pdf> <new.pdf> [--json out.json]       (WSL venv with PyMuPDF)
"""
import difflib
import json
import re
import sys
import unicodedata

import fitz  # PyMuPDF

# (removed, added): version 7's edits, each from revision6/edit_6.py (body.tex deposit list, 'five' -> 'six', the history)
EXPECTED = [
    ("five", "six"),
    ("RESPONSE-TO-REVIEW-5.md);", "RESPONSE-TO-REVIEW-5.md, RESPONSE-TO-REVIEW-6.md);"),
    ("2026; this paper)", "2026)"),
    ("", "Version 7 (October 27, 2026; this paper) answers a sixth review (one cosmetic finding; RESPONSE-TO-REVIEW-6.md; no "
         "experiment was run, and no number or sentence of the PDF changed except this history). The HTML edition of version 6 "
         "printed the rule arguments as text before “Seed” in the header of Table 9. The conversion now removes "
         "the table-rule commands, and the HTML check refuses any leftover rule argument or raw command."),
]


def words(path):
    doc = fitz.open(path)
    pages = []
    for p in doc:
        lines = p.get_text().split("\n")
        pages.append(" ".join(l for l in lines if not re.fullmatch(r"\s*\d+\s*", l)))
    t = unicodedata.normalize("NFKC", " ".join(pages))
    t = re.sub(r"(?<=[A-Za-z])- (?=[a-z])", "-", t)
    return t.split(), len(doc)


def diff(old, new):
    a, na = words(old)
    b, nb = words(new)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    hunks = [dict(tag=tag, removed=" ".join(a[i1:i2]), added=" ".join(b[j1:j2]))
             for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]
    return dict(pages_old=na, pages_new=nb, words_old=len(a), words_new=len(b), hunks=hunks)


def judge(r):
    exp = set(EXPECTED)
    r["unexpected_hunks"] = [h for h in r["hunks"] if (h["removed"], h["added"]) not in exp]
    r["expected_not_seen"] = [e for e in EXPECTED if e not in {(h["removed"], h["added"]) for h in r["hunks"]}]
    r["ok"] = not r["unexpected_hunks"] and not r["expected_not_seen"]
    return r


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    r = judge(diff(a[0], a[1]))
    print("pages", r["pages_old"], "->", r["pages_new"], "| words", r["words_old"], "->", r["words_new"], "| hunks", len(r["hunks"]),
          "| unexpected", len(r["unexpected_hunks"]), "| expected not seen", len(r["expected_not_seen"]), "|",
          "TEXT_UNCHANGED_EXCEPT_REVISION_LINE" if r["ok"] else "TEXT_DIFFERS")
    for h in r["hunks"]:
        print("  ", h["tag"], "| -", h["removed"][:90], "| +", h["added"][:140])
    if "--json" in sys.argv:
        open(sys.argv[sys.argv.index("--json") + 1], "wb").write((json.dumps(r, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    sys.exit(0 if r["ok"] else 1)
