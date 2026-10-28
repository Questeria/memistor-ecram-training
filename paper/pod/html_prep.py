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


body = inline("body")
# resolve \ifdefined\arxivvariant A \else B \fi -> B (the owner's variant)
pat = re.escape(BS + "ifdefined" + BS + "arxivvariant") + r"(.*?)" + re.escape(BS + "else") + r"(.*?)" + re.escape(BS + "fi")
body, n = re.subn(pat, lambda m: m.group(2), body, flags=re.S)
body = body.replace("table*", "table")  # pandoc keeps the labels of plain table environments only
body = re.sub(re.escape(BS) + r"bibliographystyle\{[^}]*\}\s*" + re.escape(BS) + r"bibliography\{[^}]*\}",
              lambda m: "", body)
body = body + "\n" + BS + "section*{References}\n"  # citeproc appends the bibliography at the end of the document
numbers = (D / "numbers.tex").read_text(encoding="utf-8")
head = (BS + "documentclass{article}\n" + BS + "newcommand{" + BS + "fitbox}[1]{#1}\n" + numbers + "\n" + BS + "title{Can memistor-class electrochemical weights train neural "
        "networks? A pre-registered simulation study from Widrow's 1960 memistor to modern ECRAM}\n" + BS +
        "author{Questeria and Claude (Anthropic)}\n" + BS + "date{October 2026}\n" + BS + "begin{document}\n" + BS + "maketitle\n")
(D / "main-html.tex").write_text(head + body + "\n" + BS + "end{document}\n", encoding="utf-8")
print("variant switches resolved:", n)
