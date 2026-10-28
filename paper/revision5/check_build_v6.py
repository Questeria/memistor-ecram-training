"""ME-REVISE-5: check the version-6 build (PLAN: review 5).  Everything revision4/check_build_v5.py checks (pages' logs, undefined
references and citations, overfull boxes, the HTML numbers and its fault, table sizes, withdrawn phrases, artifacts), plus the
completeness of the HTML (revision5/html_complete.py), which version 5's checks lacked:

  - headings: every \\section and \\subsection of the source is in the HTML, in order;
  - tables: every caption is followed by its own table's header, first and last rows;
  - references: no '??', '[?]', raw [label] or dead internal link;
  - labels: every sec:/app:/tab:/fig: label of the PDF's main.aux is an id in the HTML;
  and the check must FAIL on version 4's HTML and on version 5's HTML (the defect it was written for), and its self-test plants
  eight faults in the good HTML, each of which it must catch.

    H:/x1000/bench/venv/Scripts/python.exe -B revision5/check_build_v6.py <build out dir> [--json records/revision5/ARTIFACT-CHECK-v6.json]
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(P, "revision4"))
import html_complete as HC  # noqa: E402

TEX4 = "H:/x1000/memistor-paper/rev3/build-v4b/tex"   # the exact LaTeX tree version 4's HTML was built from (desk)
V4_HTML = os.path.join(P, "build", "v4", "main.html")
V5_HTML = os.path.join(P, "build", "v5", "main.html")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def v5_tree():
    """version 5's LaTeX tree rebuilt from the repository: tex/v5/*.tex (archived sources) + tex/tables (unchanged in version 6)."""
    d = tempfile.mkdtemp(prefix="v5tree")
    for f in os.listdir(os.path.join(P, "tex", "v5")):
        if f.endswith(".tex"):
            shutil.copy(os.path.join(P, "tex", "v5", f), d)
    shutil.copytree(os.path.join(P, "tex", "tables"), os.path.join(d, "tables"))
    return d


def label_parity(aux_path, html_path):
    aux = open(aux_path, "rb").read().decode("latin-1")
    labels = sorted(set(re.findall(r"\\newlabel\{((?:sec|app|tab|fig):[^}]+)\}", aux)))
    t = HC.html_text_blocks(open(html_path, encoding="utf-8").read())
    ids = set(re.findall(r'\bid="([^"]+)"', t))
    return dict(n_labels_pdf=len(labels), missing_in_html=[l for l in labels if l not in ids], ok=not [l for l in labels if l not in ids])


def main():
    out = sys.argv[1]
    res = {}
    tmp = os.path.join(tempfile.gettempdir(), "check_v5_%d.json" % os.getpid())
    r5 = subprocess.run([sys.executable, "-B", os.path.join(P, "revision4", "check_build_v5.py"), out, "--json", tmp],
                        capture_output=True, text=True)
    c5 = json.load(open(tmp, encoding="utf-8")) if os.path.exists(tmp) else {}
    res["check_build_v5"] = dict(rc=r5.returncode, all_ok=c5.get("all_ok"), tail=r5.stdout.strip()[-300:])
    html = os.path.join(out, "main.html")
    res["html_complete"] = HC.check(os.path.join(P, "tex"), html)
    res["html_selftest"] = HC.selftest(os.path.join(P, "tex"), html)
    aux = os.path.join(out, "main.aux")
    res["label_parity"] = label_parity(aux, html) if os.path.exists(aux) else dict(ok=False, error="no main.aux")
    t5 = v5_tree()
    try:
        res["fault_v5_html"] = HC.check(t5, V5_HTML)
    finally:
        shutil.rmtree(t5, ignore_errors=True)
    res["fault_v4_html"] = HC.check(TEX4, V4_HTML) if os.path.isdir(TEX4) else dict(ok=True, error="v4 source tree not on this machine")
    res["inputs"] = dict(v4_html_sha256=sha(V4_HTML), v5_html_sha256=sha(V5_HTML), v4_tree_body_sha256=sha(os.path.join(TEX4, "body.tex")) if os.path.isdir(TEX4) else None)
    ok = (r5.returncode == 0 and c5.get("all_ok") is True and res["html_complete"]["ok"] and res["html_selftest"]["ok"]
          and res["label_parity"]["ok"] and not res["fault_v5_html"]["ok"] and not res["fault_v4_html"]["ok"])
    res["all_ok"] = ok
    if "--json" in sys.argv:
        jp = sys.argv[sys.argv.index("--json") + 1]
        open(jp if os.path.isabs(jp) else os.path.join(P, jp), "wb").write((json.dumps(res, indent=1) + "\n").encode("utf-8"))
    hcr = res["html_complete"]
    print("v5 checks", res["check_build_v5"]["all_ok"], "| html complete:", hcr["ok"], "headings missing", len(hcr["headings"]["missing"]),
          "table problems", len(hcr["tables"]["problems"]), "refs", hcr["references"]["raw_labels"], "| selftest", res["html_selftest"]["ok"],
          "| labels", res["label_parity"]["ok"], "| fails on v5 html:", not res["fault_v5_html"]["ok"], "fails on v4 html:", not res["fault_v4_html"]["ok"],
          "ALL_OK" if ok else "NOT_OK")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
