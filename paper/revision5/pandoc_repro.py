"""ME-REVISE-5: minimal reproduction of the HTML conversion defect (review 5, finding 1/2/3), run with the pandoc of the build
(pypandoc_binary 1.13 = pandoc 2.19.2; WSL venv ~/me-rev3-venv). Each case is a tiny LaTeX document with two tables and a sentence
between them; the case "survives" when the sentence is still in the output, and when each table keeps its own caption and rows.

    python -B revision5/pandoc_repro.py [--json records/revision5/PANDOC-REPRO.json]

Findings (see the record): pandoc 2.19.2 loses everything between a tabular whose column spec has an absolute-length
p{..cm} column and a later tabular that has a p{..\\linewidth} column (the first table's rows and the text between are
dropped, and the second table's rows end up under the first table's caption). A tabular whose p columns are rewritten to
l (pod/html_prep_rev5.py) is read correctly.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
BS = chr(92)


def tab(cap, spec, rows, fit=False):
    body = (BS + "begin{tabular}{" + spec + "}" + BS + "toprule H1 & H2" + BS + BS + BS + "midrule " + rows + BS + BS + "\n" + BS +
            "bottomrule" + BS + "end{tabular}")
    if fit:
        body = BS + "fitbox{" + body + "}"
    return BS + "begin{table}[h]" + BS + "caption{" + cap + "}\n" + body + BS + "end{table}\n"


def doc(a, b):
    return (BS + "documentclass{article}\n" + BS + "newcommand{" + BS + "fitbox}[1]{#1}\n" + BS + "begin{document}\n" + a +
            "\nMIDDLE-SENTENCE here.\n\n" + b + "\nAFTER-SENTENCE here.\n" + BS + "end{document}\n")


def to_p_free(t):
    """The repair: every p{...} column of a tabular column specification becomes l."""
    return re.sub(r"p\{[^{}]*\}", "l", t)


CASES = {
    "A cm + B linewidth": (tab("Capt-A", "ll" + "p{8.8cm}", "a1 & a2 & a3"), tab("Capt-B", "p{0.3" + BS + "linewidth}l", "b1 & b2", True)),
    "A cm + B linewidth, no fitbox": (tab("Capt-A", "llp{8.8cm}", "a1 & a2 & a3"), tab("Capt-B", "p{0.3" + BS + "linewidth}l", "b1 & b2")),
    "A linewidth + B linewidth": (tab("Capt-A", "llp{0.5" + BS + "linewidth}", "a1 & a2 & a3"), tab("Capt-B", "p{0.3" + BS + "linewidth}l", "b1 & b2", True)),
    "A cm + B cm": (tab("Capt-A", "llp{8.8cm}", "a1 & a2 & a3"), tab("Capt-B", "p{3cm}l", "b1 & b2", True)),
    "A cm + B textwidth": (tab("Capt-A", "llp{8.8cm}", "a1 & a2 & a3"), tab("Capt-B", "p{0.3" + BS + "textwidth}l", "b1 & b2", True)),
    "A cm + B linewidth, p columns rewritten to l": None,
}


def run_pandoc(tex):
    pandoc = None
    try:
        import pypandoc
        pandoc = pypandoc.get_pandoc_path()
    except Exception:
        pass
    if pandoc is None:
        raise SystemExit("pypandoc not found: run inside the build venv (WSL ~/me-rev3-venv)")
    with tempfile.TemporaryDirectory() as d:
        fp = os.path.join(d, "t.tex")
        open(fp, "wb").write(tex.encode("utf-8"))
        r = subprocess.run([pandoc, fp, "-f", "latex", "-t", "html5"], capture_output=True, text=True)
    return r.stdout


def verdict(h):
    """survived: both sentences and both tables' rows are present, and no row of table B sits in table A."""
    tabs = re.findall(r"<table.*?</table>", h, flags=re.S)
    own = [("Capt-A" in t and "a1" in t and "b1" not in t) for t in tabs[:1]] + [("Capt-B" in t and "b1" in t and "a1" not in t) for t in tabs[1:2]]
    return dict(middle="MIDDLE-SENTENCE" in h, after="AFTER-SENTENCE" in h, tables=len(tabs), own=own,
                ok="MIDDLE-SENTENCE" in h and "AFTER-SENTENCE" in h and len(tabs) == 2 and all(own) and len(own) == 2)


def main():
    out = {}
    cases = dict(CASES)
    a, b = CASES["A cm + B linewidth"]
    cases["A cm + B linewidth, p columns rewritten to l"] = (to_p_free(a), to_p_free(b))
    for k, (x, y) in cases.items():
        out[k] = verdict(run_pandoc(doc(x, y)))
    fails = [k for k, v in out.items() if not v["ok"]]
    res = dict(pandoc=subprocess.run([__import__("pypandoc").get_pandoc_path(), "--version"], capture_output=True, text=True).stdout.splitlines()[0],
               cases=out, failing=fails,
               reproduced=("A cm + B linewidth" in fails and "A cm + B linewidth, p columns rewritten to l" not in fails))
    if "--json" in sys.argv:
        jp = sys.argv[sys.argv.index("--json") + 1]
        open(jp if os.path.isabs(jp) else os.path.join(P, jp), "wb").write((json.dumps(res, indent=1) + "\n").encode("utf-8"))
    for k, v in out.items():
        print(("OK  " if v["ok"] else "LOST"), k, v)
    print("reproduced" if res["reproduced"] else "NOT_REPRODUCED")


if __name__ == "__main__":
    main()
