"""Version 12: prove version 12's PDF text equals version 11's except for the edits version 12 meant to make, counted word by word.

Version 12's longer text adds a page (42 -> 43) and moves a float and two paragraphs across page breaks, which splits a hunk-by-hunk
comparison (revision10/pdf_text_diff_v11.py) into dozens of pieces. This check counts words instead. Both PDFs are read by the same
extraction as revision6/pdf_text_diff.py (page numbers dropped, NFKC, re-broken hyphens joined) and normalised alike: a hyphen between
two lower-case letters is dropped (the line breaker's), and so is a space after "/" or after an en dash before a digit (a URL or a
range broken at the line end). Then the signed change of every word's count from version 11 to version 12 must equal the signed
change that the EXPECTED edits make, word for word. A word the line breaker split around a float in one version ("symme-" ... "try")
and set whole in the other is matched piecewise and listed. Every EXPECTED edit must be seen as a phrase (its old words in version
11, its new words in version 12), and the new version must have exactly one page more. A paragraph or float that only moved changes
no count; anything that appears, disappears or changes does. Version 10 against version 12 must fail (it carries version 11's edits).

EXPECTED holds the 46 hunks of the v11 -> v12 comparison of main-arxiv.pdf that are version 12's edits, verbatim (each checked by hand
against revision11/edit_12.py and the regenerated Tables 8, 11 and 16 and numbers_rev.tex): the abstract's width sentence, Section 4.3's
excess in quadrature, Section 4.4 (the Welch df, the shared example order, the CIFAR verdicts, both contrasts), Table 8's and Table 11's
captions and Table 11's Welch intervals, the discussion and the roadmap, the availability section (archive v1.2, nine reviews, the
ninth response), the bibliography's Jacobs-Gedrim, Table 16's v1 labels, the deviation count R1-R9 and the history.

    python -B revision11/pdf_text_diff_v12.py <v11.pdf> <v12.pdf> [--json out.json]       (WSL venv with PyMuPDF)
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
# (version 11's text, version 12's text), as extracted
EXPECTED = [
    ("an analysis paired by seed detects",
     ""),
    ("",
     "is detected"),
    ("null",
     "null, in quadrature ( \u221a max(0, RMS2 slot \u2212RMS2 null)),"),
    ("independent. They",
     "independent; its interval takes the t quantile at the Welch\u2013Satterthwaite degrees of freedom (versions 2 to 11 rounded them down, which the plan does not state; review 9 found it, deviation R9). The samples"),
    ("not:",
     "not independent: a seed keeps its example order across widths, and within a width"),
    ("",
     "also"),
    ("and",
     "(between widths"),
    ("data order across widths.",
     "layers differ in shape)."),
    ("CIFAR (c = 16, 32, 64). 1 arm is equivalent within \u00b12 pp (Li-ECRAM c-TTv2, D = \u22120.34 pp, 90 % interval [-1.34, 0.66]); for 1 arm there is no evidence of growth beyond the margin (protonic-inspired TTv2); 2 arms are inconclusive (Li-ECRAM TTv2, D = 1.91 pp; protonic-inspired c-TTv2,",
     ""),
    ("",
     "CIFAR (c = 16, 32, 64). 1 arm is equivalent within \u00b12 pp (Li-ECRAM c-TTv2, D = \u22120.34 pp, 90 % interval [-1.34, 0.65]); for 1 arm there is no evidence of growth beyond the margin (protonic-inspired TTv2); 1 arm grows (protonic-inspired c-TTv2,"),
    ("",
     "pp, 90 % interval [0.05, 3.47]), and 1 is inconclusive (Li-ECRAM TTv2, D = 1.91"),
    ("",
     "again"),
    ("3.38]): the",
     "3.38]). Its"),
    ("detected,",
     "detected by both contrasts,"),
    ("the interval includes",
     "both intervals include"),
    ("the paired analysis detects",
     "both contrasts detect"),
    ("which the registered Welch test does not,",
     ""),
    ("",
     "taken in quadrature ( \u221a max(0, RMS2 slot \u2212RMS2 null)),"),
    ("",
     "(the t quantile at the Welch\u2013Satterthwaite degrees of freedom; versions 1\u201311 rounded them down: deviation R9)"),
    ("0.66]",
     "0.65]"),
    ("[-0.37, 4.19]",
     "[-0.34, 4.16]"),
    ("[-0.02, 3.55] INC",
     "[0.05, 3.47] GR"),
    ("[-2.53, 0.62]",
     "[-2.51, 0.60]"),
    ("[-15.38, -12.86]",
     "[-15.37, -12.87]"),
    ("[-14.59, -11.25]",
     "[-14.55, -11.29]"),
    ("[-8.10, -5.70]",
     "[-8.08, -5.72]"),
    ("[-19.30, -9.57]",
     "[-19.12, -9.75]"),
    ("",
     "the registered Welch test and"),
    ("detects",
     "both detect"),
    ("",
     "both the registered Welch test and"),
    ("detects",
     "detect"),
    ("1.1",
     "1.2"),
    ("11",
     "12"),
    ("",
     "version 1.1 holds version 11,"),
    ("v1.1).",
     "v1.2)."),
    ("eight",
     "nine"),
    ("RESPONSE-TO-REVIEW-8.md);",
     "RESPONSE-TO-REVIEW-8.md, RESPONSE-TO-REVIEW-9.md);"),
    ("JacobsGedrim,",
     "Jacobs-Gedrim,"),
    ("this paper\u2019s",
     "the"),
    ("values.",
     "values of version 1 of this paper (v1; superseded: the original simulator before its repair; the current values are in Tables 4 and 5)."),
    ("this paper",
     "v1"),
    ("this paper",
     "v1"),
    ("this paper",
     "v1"),
    ("R1\u2013R8",
     "R1\u2013R9"),
    ("2026; this paper)",
     "2026)"),
    ("",
     "Version 12 (October 29, 2026; this paper) answers a ninth review, a second audit and reproduction from the public archive (RESPONSE-TO-REVIEW-9.md; no experiment was run). The width study\u2019s Welch interval now takes the t quantile at the Welch\u2013Satterthwaite degrees of freedom; versions 2 to 11 rounded them down, which the plan does not state (deviation R9). This changes one verdict, protonic-inspired c-TTv2 on CIFAR, from inconclusive to grows (Sec-tion 4.4), and moves the other Welch intervals by at most 0.18 in their units; the paired contrast is unchanged. The width section now says that across widths a seed shares its example order, not its initialisation; the excess correlation of Table 8 is defined as an excess in quadrature; and Table 16 labels its version-1 values as superseded."),
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
             unexplained_word_changes=left, expected_not_seen=not_seen, rejoined=rejoined, pages_ok=(nb == na + 1))
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
