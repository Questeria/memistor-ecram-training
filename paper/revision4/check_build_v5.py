"""ME-REVISE-4: check the version-5 build (PLAN-REVISION-4.md sections 3-4). Everything revision3/check_build_v4.py checks
(pages, undefined references and citations, multiply defined labels, overfull boxes in main, main-arxiv and the archive compiled
alone; the HTML check; the revision-number check: the HTML abstract's digits equal the generated arXiv abstract's, and v3's HTML
must fail it), plus:
  - table sizes: every table set through \\fitbox logs its number, natural width, text width and font size (tex/preamble.tex);
    its printed size is font size x min(1, text width / natural width), and every one must be at least MIN_PT;
  - withdrawn phrases: none of revision4/make_abstract_v5.py's withdrawn phrases appears in tex/*.tex (v5 sources) or the
    generated abstract.

    H:/x1000/bench/venv/Scripts/python.exe -B revision4/check_build_v5.py <build out dir> [--json records/revision4/ARTIFACT-CHECK-v5.json]
"""
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(P, "revision3"))
import check_build_v4 as C4  # noqa: E402

MIN_PT = 7.5
WITHDRAWN = ["rounding alone", "more sensitive to rounding", "two independent reviews", "sub-margin growth",
             "preserves the ranking", "valid reference"]


def pt(s):
    return float(s.replace("pt", ""))


def appendix_tables(aux):
    """Table numbers printed on or after the first appendix page (deviation R8: MIN_PT binds the body's tables; the appendix
    tables, chiefly version 1's record reproduced unchanged, are reported)."""
    tabs = {n: int(pg) for n, pg in re.findall(r"newlabel\{tab:[^}]*\}\{\{(\d+)\}\{(\d+)\}", aux)}
    apps = [int(pg) for pg in re.findall(r"newlabel\{app:[^}]*\}\{\{[A-Z]\}\{(\d+)\}", aux)]
    start = min(apps) if apps else None
    return {n for n, pg in tabs.items() if start is not None and pg >= start}


def table_sizes(log, appendix=frozenset()):
    rows, seen = [], set()
    for m in re.finditer(r"FITBOX table=(\S+) wd=([\d.]+pt) tw=([\d.]+pt) size=([\d.]+)", log):
        k = m.groups()
        if k in seen:
            continue
        seen.add(k)
        wd, tw, size = pt(k[1]), pt(k[2]), float(k[3])
        rows.append(dict(table=k[0], natural_pt=wd, text_pt=tw, font_pt=size, printed_pt=round(size * min(1.0, tw / wd), 3),
                         appendix=k[0] in appendix))
    return dict(n=len(rows), min_printed_pt=min((r["printed_pt"] for r in rows), default=None),
                below=[r for r in rows if r["printed_pt"] < MIN_PT and not r["appendix"]],
                appendix_below=[r for r in rows if r["printed_pt"] < MIN_PT and r["appendix"]], rows=rows)


def withdrawn_in(texts):
    return sorted({w for t in texts for w in WITHDRAWN if w.lower() in re.sub(r"\s+", " ", t).lower()})


def selftest5():
    good = "FITBOX table=6 wd=300.0pt tw=345.0pt size=8\n"
    shrunk = "FITBOX table=7 wd=400.0pt tw=345.0pt size=8\n"  # 8 x 345/400 = 6.9 pt
    aux = "\\newlabel{tab:a}{{6}{17}}\\newlabel{tab:b}{{7}{40}}\\newlabel{app:x}{{A}{32}}"
    return dict(clean_passes=not table_sizes(good)["below"] and table_sizes(good)["n"] == 1,
                shrunk_caught=bool(table_sizes(shrunk)["below"]), no_log_caught=table_sizes("")["n"] == 0,
                appendix_split=appendix_tables(aux) == {"7"} and not table_sizes(shrunk, {"7"})["below"],
                phrase_caught=withdrawn_in(["from GPU rounding\n alone"]) == ["rounding alone"])


def main():
    out = sys.argv[1]
    res = dict(selftest=C4.selftest(), selftest5=selftest5(), logs={})
    ab = os.path.join(P, "build", "arxiv-abstract.txt")
    res["html_numbers"] = C4.html_numbers(os.path.join(out, "main.html"), ab)
    res["html_numbers_fault_v3_html"] = C4.html_numbers(os.path.join(P, "build", "v3", "main.html"),
                                                        os.path.join(P, "build", "v3", "arxiv-abstract.txt"))
    for n in ("main.log", "main-arxiv.log", "archive-main-arxiv.log"):
        p = os.path.join(out, n)
        res["logs"][n] = C4.scan(open(p, "rb").read().decode("latin-1")) if os.path.exists(p) else None
    res["tables"] = {}
    for n in ("main.log", "main-arxiv.log"):
        aux = os.path.join(out, n.replace(".log", ".aux"))
        if os.path.exists(os.path.join(out, n)) and os.path.exists(aux):
            res["tables"][n] = table_sizes(open(os.path.join(out, n), "rb").read().decode("latin-1"),
                                           appendix_tables(open(aux, "rb").read().decode("latin-1")))
    srcs = [open(f, "rb").read().decode("utf-8") for f in glob.glob(os.path.join(P, "tex", "*.tex"))]
    srcs += [open(f, "rb").read().decode("utf-8") for f in glob.glob(os.path.join(P, "tex", "tables", "*.tex"))]
    res["withdrawn_in_sources"] = withdrawn_in(srcs)
    res["withdrawn_in_abstract"] = withdrawn_in([open(ab, "rb").read().decode("utf-8")])
    import hashlib
    import subprocess
    arts = {}
    for n in ("main.pdf", "main-arxiv.pdf", "arxiv-source.tar.gz", "main.html"):
        p = os.path.join(out, n)
        arts[n] = dict(bytes=os.path.getsize(p), sha256=hashlib.sha256(open(p, "rb").read()).hexdigest()) if os.path.exists(p) else None
    res["artifacts"] = arts
    hc = subprocess.run([sys.executable, "-B", os.path.join(P, "pod", "html_check.py"), os.path.join(out, "main.html")],
                        capture_output=True, text=True)
    res["html_check"] = dict(rc=hc.returncode, out=hc.stdout.strip()[-400:])
    st, s5 = res["selftest"], res["selftest5"]
    ok = (st["clean_passes"] and all(st["faults_caught"].values()) and all(s5.values())
          and all(v and not C4.bad(v) for v in res["logs"].values()) and all(arts.values()) and hc.returncode == 0
          and res["html_numbers"]["ok"] and not res["html_numbers_fault_v3_html"]["ok"]
          and all(t["n"] > 0 and not t["below"] for t in res["tables"].values()) and len(res["tables"]) == 2
          and not res["withdrawn_in_sources"] and not res["withdrawn_in_abstract"])
    res["all_ok"] = ok
    if "--json" in sys.argv:
        jp = sys.argv[sys.argv.index("--json") + 1]
        open(jp if os.path.isabs(jp) else os.path.join(P, jp), "wb").write((json.dumps(res, indent=1) + "\n").encode("utf-8"))
    print(json.dumps(res["logs"]), "html", hc.returncode, res["html_numbers"], "tables min",
          {k: (v["n"], v["min_printed_pt"], [r["table"] for r in v["below"]]) for k, v in res["tables"].items()},
          "withdrawn", res["withdrawn_in_sources"], res["withdrawn_in_abstract"], "ALL_OK" if ok else "NOT_OK")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
