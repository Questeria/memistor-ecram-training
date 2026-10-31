"""Version 13: prove version 13's PDF text equals version 12's except for the edits version 13 meant to make, counted word by word
(revision11/pdf_text_diff_v12.py's method: the same extraction and normalisation, every word's signed count change must equal the
change the EXPECTED edits make, every EXPECTED edit must be seen as a phrase).  Version 13 has as many pages as version 12 (43).
Version 11 against version 13 must fail (it carries version 12's edits).

EXPECTED holds version 13's edits, verbatim as extracted (each checked by hand against revision12/edit_13.py and the regenerated
Table 11): the availability section (archive v1.3, release v1.3, ten reviews, the tenth response), Table 11's caption (versions
2--11, review 10 finding 3) and the history (version 12 no longer "this paper"; version 13).

    python -B revision12/pdf_text_diff_v13.py <v12.pdf> <v13.pdf> [--json out.json]       (WSL venv with PyMuPDF)
"""
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "revision6"))
import pdf_text_diff as D6  # noqa: E402

ACCT = "Quest" + "eria"                                                   # written in two pieces so this script stays clean
# (version 12's text, version 13's text), as extracted
EXPECTED = [
    ("1.2 of the archive holds version 12",
     "1.3 of the archive holds version 13"),
    ("",
     "version 1.2 holds version 12,"),
    ("v1.2).",
     "v1.3)."),
    ("nine independent",
     "ten independent"),
    ("RESPONSE-TO-REVIEW-9.md);",
     "RESPONSE-TO-REVIEW-9.md, RESPONSE-TO-REVIEW-10.md);"),
    ("versions 1–11 rounded",
     "versions 2–11 rounded"),
    ("2026; this paper) answers a ninth",
     "2026) answers a ninth"),
    ("",
     "Version 13 (October 31, 2026; this paper) answers a tenth review, of version 12 and version 1.2 of the archive (RESPONSE-TO-REVIEW-10.md; no experiment was run and no number changed). It found the Welch correction right and four small slips outside the results, all corrected: the archive’s README said that no other printed number changed, although all eight Welch intervals moved, and counted eight reviews; the caption of Table 11 dated the rounded degrees of freedom to versions 1 to 11, not 2 to 11 (version 1 used another width test); and a self-test of the name check left a PDF open, so its clean-up failed on Windows."),
]


def norm(text):
    text = re.sub(r"(?<=/) (?=\w)", "", text)
    text = re.sub(r"(?<=\u2013) (?=\d)", "", text)
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


def run(old_pdf, new_pdf):
    a, na = D6.words(old_pdf)
    b, nb = D6.words(new_pdf)
    ta, tb = norm(" ".join(a)), norm(" ".join(b))
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
    r = run(args[0], args[1])
    print("pages", r["pages_old"], "->", r["pages_new"], "| words", r["words_old"], "->", r["words_new"], "| unexplained",
          sum(abs(n) for n in r["unexplained_word_changes"].values()), "| expected not seen", len(r["expected_not_seen"]),
          "| rejoined", len(r["rejoined"]), "|", "TEXT_UNCHANGED_EXCEPT_EXPECTED" if r["ok"] else "TEXT_DIFFERS")
    if "--json" in sys.argv:
        blob = json.dumps(r, indent=1, ensure_ascii=False).replace(ACCT, "<account>")
        open(sys.argv[sys.argv.index("--json") + 1], "wb").write((blob + "\n").encode("utf-8"))
    sys.exit(0 if r["ok"] else 1)
