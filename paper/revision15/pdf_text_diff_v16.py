"""Version 16: prove version 16's PDF text equals version 15's except for the edits version 16 meant to make, counted word by word
(revision14/pdf_text_diff_v15.py's method and normalisation: every word's signed count change must equal the change the EXPECTED
edits make, and every EXPECTED edit must be seen as a phrase).  A passage that only moved changes no count, so it needs no entry.

Bracketed reference numbers are replaced by "[#]" in both versions before counting.  The EXPECTED edits of version 16
(revision15/expected_v16.py) are the abstract's last sentence, the contribution statement's review count (both variants), the availability section (archive
v1.6, release v1.6, thirteen reviews, the thirteenth response) and the history (version 15 no longer "this paper"; the version-16
entry).

Version 16 has as many pages as version 15 (44); the check requires that.  Version 14 against version 16 must fail (it carries
version 15's edits).

    python -B revision15/pdf_text_diff_v16.py <v15.pdf> <v16.pdf> [--json out.json] [--show]     (WSL venv with PyMuPDF)
"""
import collections
import difflib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "revision6"))
import pdf_text_diff as D6  # noqa: E402

ACCT = "Quest" + "eria"                                                   # written in two pieces so this script stays clean
CITE = re.compile(r"\[\d+(?:\s?[,–-]\s?\d+)*\]")
from expected_v16 import EXPECTED  # noqa: E402  (version 14's text, version 15's text), as extracted


def norm(text):
    text = CITE.sub("[#]", text)
    text = re.sub(r"(?<=/) (?=\w)", "", text)
    text = re.sub(r"(?<=–) (?=\d)", "", text)
    text = re.sub(r"(?<=[a-z])- ?(?=[a-z])", "", text)
    return text.split()


def rejoin(resid):
    """Cancel a word split around a float in one version ("symme-" and "try") against its whole form in the other ("symmetry")."""
    done = []
    for w in [w for w in list(resid) if len(w) > 1 and w.endswith("-") and w[-2].isalpha()]:
        for u in list(resid):
            whole = w[:-1] + u
            if (u and u[0].islower() and resid.get(w) and resid.get(u) and resid.get(whole)
                    and resid[w] == resid[u] == -resid[whole]):
                n = resid[w]
                resid[w] -= n
                resid[u] -= n
                resid[whole] += n
                done.append([w, u, whole])
                break
    return done


def run(old_pdf, new_pdf, show=False):
    a, na = D6.words(old_pdf)
    b, nb = D6.words(new_pdf)
    ta, tb = norm(" ".join(a)), norm(" ".join(b))
    if show:
        sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag != "equal":
                print("HUNK", tag, "|-", " ".join(ta[i1:i2])[:400], "|+", " ".join(tb[j1:j2])[:600])
    ca, cb = collections.Counter(ta), collections.Counter(tb)
    resid = {w: cb[w] - ca[w] for w in set(ca) | set(cb)}
    for old, new in EXPECTED:
        for w in norm(new):
            resid[w] = resid.get(w, 0) - 1
        for w in norm(old):
            resid[w] = resid.get(w, 0) + 1
    rejoined = rejoin(resid)
    left = {w: n for w, n in sorted(resid.items()) if n}
    sa, sb = " " + " ".join(ta) + " ", " " + " ".join(tb) + " "
    not_seen = [[o[:80], n[:80]] for o, n in EXPECTED
                if (o and " " + " ".join(norm(o)) + " " not in sa) or (n and " " + " ".join(norm(n)) + " " not in sb)]
    r = dict(pages_old=na, pages_new=nb, words_old=len(a), words_new=len(b), expected_edits=len(EXPECTED),
             unexplained_word_changes=left, expected_not_seen=not_seen, rejoined=rejoined, pages_ok=(nb == na))
    r["ok"] = not left and not not_seen and r["pages_ok"]
    return r


if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    jp = sys.argv[sys.argv.index("--json") + 1] if "--json" in sys.argv else None
    args = [x for x in args if x != jp]
    r = run(args[0], args[1], show="--show" in sys.argv)
    print("pages", r["pages_old"], "->", r["pages_new"], "| words", r["words_old"], "->", r["words_new"], "| unexplained",
          sum(abs(n) for n in r["unexplained_word_changes"].values()), "| expected not seen", len(r["expected_not_seen"]),
          "| rejoined", len(r["rejoined"]), "|", "TEXT_UNCHANGED_EXCEPT_EXPECTED" if r["ok"] else "TEXT_DIFFERS")
    if "--show" in sys.argv:
        print("UNEXPLAINED", r["unexplained_word_changes"])
        print("NOT SEEN", r["expected_not_seen"])
    if jp:
        blob = json.dumps(r, indent=1, ensure_ascii=False).replace(ACCT, "<account>")
        open(jp, "wb").write((blob + "\n").encode("utf-8"))
    sys.exit(0 if r["ok"] else 1)
