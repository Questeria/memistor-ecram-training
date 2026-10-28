"""ME-REVISE-4 (derived by pod/derive_build_rev4.py from revision3/make_abstract_v4.py): build/arxiv-abstract.txt from tex/sec_abstract.tex (the PDF abstract), with every number macro expanded from
tex/numbers*.tex and the LaTeX reduced to plain text; refuses if it exceeds arXiv's 1,920 characters or contains a phrase
withdrawn after the reviews.

    python -B revision2/make_abstract.py
"""
import re
import sys
from pathlib import Path

P = Path(__file__).resolve().parent.parent
TEX = P / "tex"
WITHDRAWN = ["near-digital", "within five-seed resolution", "does not grow with width", "few hundred levels suffice",
             "about 32x", "15-234x", "We release", "equal quality", "no growth of the gap with width", "sub-margin growth", "preserves the ranking", "valid reference", "rounding alone", "more sensitive to rounding", "two independent reviews"]
mac = {}
for f in ("numbers.tex", "numbers_rev.tex", "numbers_rev2.tex", "numbers_rev3.tex", "numbers_rev4.tex"):
    for k, v in re.findall(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$", (TEX / f).read_text("utf-8"), re.M):
        mac[k] = v
s = (TEX / "sec_abstract.tex").read_text("utf-8")
s = s.replace("\\begin{abstract}", "").replace("\\end{abstract}", "")
s = re.sub(r"\\([A-Za-z]+)(\{\})?", lambda m: mac.get(m.group(1), m.group(0)), s)
s = (s.replace("\\,pp", " pp").replace("\\,\\%", "%").replace("\\%", "%").replace("\\,", "").replace("$\\times$", "x").replace("--", "-")
     .replace("~", " "))
s = re.sub(r"\\emph\{([^}]*)\}", r"\1", s)
s = " ".join(s.split())
left = re.findall(r"\\[A-Za-z]+|[{}$]", s)
bad = [w for w in WITHDRAWN if w.lower() in s.lower()]
if left or bad or len(s) > 1920:
    sys.exit(f"REFUSED: leftover LaTeX {left[:5]}, withdrawn phrases {bad}, {len(s)} characters")
(P / "build" / "arxiv-abstract.txt").write_bytes((s + "\n").encode("utf-8"))
print(len(s), "characters")
