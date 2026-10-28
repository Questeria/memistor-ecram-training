"""Prepare tex/main-html.tex for pandoc. Pandoc does not evaluate \\ifdefined, so the author-variant switch is resolved to the
owner's variant, and the files are flattened (inputs inlined) so that every macro and table is seen.

    python3 html_prep.py <tex dir>
"""
import re
import sys
from pathlib import Path

D = Path(sys.argv[1])
BS = chr(92)


def inline(name, depth=0):
    p = D / (name if name.endswith(".tex") else name + ".tex")
    t = p.read_text(encoding="utf-8")
    t = re.sub(r"(?m)^%.*$", "", t)
    if depth < 6:
        t = re.sub(re.escape(BS) + r"input\{([^}]+)\}", lambda m: inline(m.group(1), depth + 1), t)
    return t


def rewrite_pcols(t):
    """Every \\begin{tabular}{SPEC}: p{...} columns of SPEC become l (pandoc 2.19.2 fuses a p{..cm} table with a later
    p{..\\linewidth} table and drops what lies between them; see revision5/pandoc_repro.py)."""
    key = BS + "begin{tabular}{"
    out, i, n = [], 0, 0
    while True:
        j = t.find(key, i)
        if j < 0:
            out.append(t[i:])
            break
        k = j + len(key) - 1
        d, m = 0, k
        while True:
            c = t[m]
            if c == BS:
                m += 2
                continue
            d += (c == "{") - (c == "}")
            m += 1
            if d == 0:
                break
        spec = t[k + 1:m - 1]
        new, depth, p = [], 0, 0
        s = 0
        res = ""
        while s < len(spec):
            if spec[s] == "p" and s + 1 < len(spec) and spec[s + 1] == "{":
                e, dd = s + 1, 0
                while True:
                    dd += (spec[e] == "{") - (spec[e] == "}")
                    e += 1
                    if dd == 0:
                        break
                res += "l"
                n += 1
                s = e
            else:
                res += spec[s]
                s += 1
        out.append(t[i:k + 1] + res + "}")
        i = m
    return "".join(out), n


def letter_appendices(t):
    """pandoc does not know the appendix command: its references read 'Appendix 15' where the PDF says 'Appendix F'. Every numbered
    section after it becomes 'Appendix X: title' and every ref to an app: label becomes its letter."""
    i = t.find(BS + "appendix")
    if i < 0:
        return t, 0
    head, tail = t[:i], t[i + len(BS + "appendix"):]
    out, pos, n, letters = [], 0, 0, {}
    key = BS + "section{"
    while True:
        j = tail.find(key, pos)
        if j < 0:
            out.append(tail[pos:])
            break
        k = j + len(key) - 1
        d, m = 0, k
        while True:
            c = tail[m]
            if c == BS:
                m += 2
                continue
            d += (c == "{") - (c == "}")
            m += 1
            if d == 0:
                break
        letter = chr(ord("A") + n)
        n += 1
        out.append(tail[pos:j] + key + "Appendix " + letter + ": " + tail[k + 1:m - 1] + "}")
        lab = re.match(r"\s*" + re.escape(BS) + r"label\{(app:[^}]+)\}", tail[m:])
        if lab:
            letters[lab.group(1)] = letter
        pos = m
    allt = head + "".join(out)
    allt = re.sub(re.escape(BS) + r"ref\{(app:[^}]+)\}", lambda mm: letters[mm.group(1)], allt)
    return allt, n


body = inline("body")
# resolve \ifdefined\arxivvariant A \else B \fi -> B (the owner's variant)
pat = re.escape(BS + "ifdefined" + BS + "arxivvariant") + r"(.*?)" + re.escape(BS + "else") + r"(.*?)" + re.escape(BS + "fi")
body, n = re.subn(pat, lambda m: m.group(2), body, flags=re.S)
body = body.replace("table*", "table")  # pandoc keeps the labels of plain table environments only
body, npcols = rewrite_pcols(body)
print("p-columns rewritten to l:", npcols)
body, napp = letter_appendices(body)
print("appendices lettered:", napp)
body = re.sub(re.escape(BS) + r"bibliographystyle\{[^}]*\}\s*" + re.escape(BS) + r"bibliography\{[^}]*\}",
              lambda m: "", body)
body = body + "\n" + BS + "section*{References}\n"  # citeproc appends the bibliography at the end of the document
numbers = "\n".join((D / n).read_text(encoding="utf-8") for n in ("numbers.tex", "numbers_rev.tex", "numbers_rev2.tex",
                                                                     "numbers_rev3.tex", "numbers_rev4.tex"))
head = (BS + "documentclass{article}\n" + BS + "newcommand{" + BS + "fitbox}[1]{#1}\n" + numbers + "\n" + BS + "title{Can memistor-class electrochemical weights train neural "
        "networks? A pre-registered simulation study from Widrow's 1960 memistor to modern ECRAM}\n" + BS +
        "author{Questeria and Claude (Anthropic)}\n" + BS + "date{October 2026}\n" + BS + "begin{document}\n" + BS + "maketitle\n")
(D / "main-html.tex").write_text(head + body + "\n" + BS + "end{document}\n", encoding="utf-8")
print("variant switches resolved:", n)
