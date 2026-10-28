"""ME-REVISE-6: check the version-7 build.  Everything revision5/check_build_v6.py checks (which runs revision4/check_build_v5.py:
logs, references, overfull boxes, table sizes, the HTML numbers; and revision5/html_complete.py: headings, tables, references,
labels, its eight planted faults, and failure on the version-4 and version-5 HTML), plus the leftover-LaTeX check
(revision6/html_leftover.py): no 'cmidrule'/'cline', no '(lr)2-6'-style rule argument, no raw \\command outside math spans.  The
leftover check must FAIL on version 6's HTML (build/v6/main.html, the defect it was written for), PASS on the new HTML, and
catch each of six planted faults (including the exact version-6 residue put back into Table 9's header).

    H:/x1000/bench/venv/Scripts/python.exe -B revision6/check_build_v7.py <build out dir> [--json records/revision6/ARTIFACT-CHECK-v7.json]
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import html_leftover as HL  # noqa: E402

V6_HTML = os.path.join(P, "build", "v6", "main.html")


def main():
    out = sys.argv[1]
    res = {}
    tmp = os.path.join(tempfile.gettempdir(), "check_v6_%d.json" % os.getpid())
    r6 = subprocess.run([sys.executable, "-B", os.path.join(P, "revision5", "check_build_v6.py"), out, "--json", tmp],
                        capture_output=True, text=True)
    c6 = json.load(open(tmp, encoding="utf-8")) if os.path.exists(tmp) else {}
    res["check_build_v6"] = dict(rc=r6.returncode, all_ok=c6.get("all_ok"), tail=r6.stdout.strip()[-400:])
    html = os.path.join(out, "main.html")
    res["leftover_new_html"] = HL.check(html)
    res["leftover_selftest"] = HL.selftest(html)
    res["leftover_on_v6_html"] = HL.check(V6_HTML)
    ok = (r6.returncode == 0 and c6.get("all_ok") is True and res["leftover_new_html"]["ok"] and res["leftover_selftest"]["ok"]
          and not res["leftover_on_v6_html"]["ok"])
    res["all_ok"] = ok
    if "--json" in sys.argv:
        jp = sys.argv[sys.argv.index("--json") + 1]
        open(jp if os.path.isabs(jp) else os.path.join(P, jp), "wb").write((json.dumps(res, indent=1) + "\n").encode("utf-8"))
    print("v6 checks", res["check_build_v6"]["all_ok"], "| leftover on new html: hits", res["leftover_new_html"]["n_hits"],
          "tables", res["leftover_new_html"]["tables_scanned"], "| selftest", res["leftover_selftest"]["ok"],
          "| fails on v6 html:", not res["leftover_on_v6_html"]["ok"], "(hits %d)" % res["leftover_on_v6_html"]["n_hits"],
          "ALL_OK" if ok else "NOT_OK")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
