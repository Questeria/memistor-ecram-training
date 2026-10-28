"""Build the paper's build-sitting payload (devpod --payload DIR) and lint the LaTeX first: every \\R... macro used in tex/ must
be defined in tex/numbers.tex, every \\input file must exist, every \\cite key must be in refs.bib, every \\ref must have a
\\label, braces must balance per file.

    python -I paper/pod/build_payload.py --out H:/x1000/memistor-paper/payload/<name>   (or --lint-only)
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
TEX = PAPER / "tex"
BS = chr(92)


def lint():
    errs = []
    defined = set(re.findall(re.escape(BS) + r"newcommand\{" + re.escape(BS) + r"([A-Za-z]+)\}", (TEX / "numbers.tex").read_text("utf-8") + (TEX / "numbers_rev.tex").read_text("utf-8")))
    keys = set(re.findall(r"@\w+\{([^,]+),", (TEX / "refs.bib").read_text("utf-8")))
    labels, refs = set(), set()
    files = sorted(TEX.glob("*.tex")) + sorted((TEX / "tables").glob("*.tex"))
    for f in files:
        t = re.sub(r"(?m)(?<!\\)%.*$", "", f.read_text("utf-8"))
        for m in re.findall(re.escape(BS) + r"(R[A-Z][A-Za-z]*|RV[A-Za-z]+|nChecks|nFaults)\b", t):
            if m not in defined:
                errs.append(f"{f.name}: undefined macro \\{m}")
        for m in re.findall(re.escape(BS) + r"input\{([^}]+)\}", t):
            p = TEX / (m if m.endswith(".tex") else m + ".tex")
            if not p.exists():
                errs.append(f"{f.name}: missing input {m}")
        for grp in re.findall(re.escape(BS) + r"cite[pt]?\{([^}]+)\}", t):
            for k in grp.split(","):
                if k.strip() not in keys:
                    errs.append(f"{f.name}: unknown cite key {k.strip()}")
        labels |= set(re.findall(re.escape(BS) + r"label\{([^}]+)\}", t))
        refs |= {(f.name, r) for r in re.findall(re.escape(BS) + r"ref\{([^}]+)\}", t)}
        depth = 0
        for ch in t.replace(BS + "{", "").replace(BS + "}", ""):
            depth += (ch == "{") - (ch == "}")
            if depth < 0:
                break
        if depth != 0:
            errs.append(f"{f.name}: unbalanced braces ({depth})")
    for fn, r in refs:
        if r not in labels:
            errs.append(f"{fn}: \\ref to missing label {r}")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    ap.add_argument("--lint-only", action="store_true")
    a = ap.parse_args()
    errs = lint()
    for e in errs:
        print("LINT", e)
    if errs:
        raise SystemExit(f"{len(errs)} lint errors")
    print("lint ok")
    if a.lint_only:
        return
    out = Path(a.out)
    if out.exists():
        raise SystemExit("REFUSED: exists")
    files = {}
    for f in sorted(TEX.glob("*.tex")) + [TEX / "refs.bib"]:
        files["tex/" + f.name] = f.read_bytes()
    for f in sorted((TEX / "tables").glob("*.tex")):
        files["tex/tables/" + f.name] = f.read_bytes()
    for n in ("RESULTS-PAPER.json", "ENERGY-SYSTEM.json"):
        files["records/" + n] = (PAPER / "records" / n).read_bytes()
    files["make_figures.py"] = (PAPER / "make_figures.py").read_bytes()
    files["records/revision/RESULTS-REVISION.json"] = (PAPER / "records" / "revision" / "RESULTS-REVISION.json").read_bytes()
    files["make_figures_rev.py"] = (PAPER / "revision" / "make_figures_rev.py").read_bytes()
    files["run.sh"] = (HERE / "build_rev.sh").read_bytes()
    files["html_prep.py"] = (HERE / "html_prep.py").read_bytes()
    files["html.css"] = (HERE / "html.css").read_bytes()
    for n, b in files.items():
        if b"\r\n" in b:
            raise SystemExit("CRLF in " + n)
    out.mkdir(parents=True)
    lines = []
    for n, b in sorted(files.items()):
        (out / n).parent.mkdir(parents=True, exist_ok=True)
        (out / n).write_bytes(b)
        lines.append("%s  %s" % (hashlib.sha256(b).hexdigest(), n))
    (out / "MANIFEST.sha256").write_bytes(("\n".join(lines) + "\n").encode())
    print(json.dumps(dict(files=len(files), bytes=sum(len(b) for b in files.values()))))


if __name__ == "__main__":
    main()
