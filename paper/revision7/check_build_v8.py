"""ME-REVISE-7: check the version-8 build.  Everything revision6/check_build_v7.py checks (which runs revision5/check_build_v6.py, the
leftover-LaTeX check and their self-tests), plus the two proofs of this version, run beforehand in the WSL venv (PyMuPDF) and read here:

  records/revision7/NAME-CHECK-v8.json      revision7/name_check.py        the old name appears nowhere (shown to fail on v7 and on planted copies)
  records/revision7/PDF-TEXT-DIFF-main.json, PDF-TEXT-DIFF-main-arxiv.json   revision7/pdf_text_diff_v8.py   only the expected hunks

    H:/x1000/bench/venv/Scripts/python.exe -B revision7/check_build_v8.py <build out dir> [--json records/revision7/ARTIFACT-CHECK-v8.json]
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)


def load(rel):
    p = os.path.join(P, rel)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def main():
    out = sys.argv[1]
    res = {}
    tmp = os.path.join(tempfile.gettempdir(), "check_v7_%d.json" % os.getpid())
    r7 = subprocess.run([sys.executable, "-B", os.path.join(P, "revision6", "check_build_v7.py"), out, "--json", tmp],
                        capture_output=True, text=True)
    c7 = json.load(open(tmp, encoding="utf-8")) if os.path.exists(tmp) else {}
    res["check_build_v7"] = dict(rc=r7.returncode, all_ok=c7.get("all_ok"), tail=r7.stdout.strip()[-400:])
    nm = load("records/revision7/NAME-CHECK-v8.json")
    res["name_check"] = dict(all_ok=nm.get("all_ok"), old_name_total_hits=nm.get("old_name_total_hits"),
                             selftest_ok=nm.get("selftest", {}).get("ok"))
    for k, f in (("pdf_diff_main", "PDF-TEXT-DIFF-main.json"), ("pdf_diff_main_arxiv", "PDF-TEXT-DIFF-main-arxiv.json")):
        d = load("records/revision7/" + f)
        res[k] = dict(ok=d.get("ok"), hunks=len(d.get("hunks", [])), unexpected=len(d.get("unexpected_hunks", [])),
                      pages=(d.get("pages_old"), d.get("pages_new")))
    ok = (r7.returncode == 0 and c7.get("all_ok") is True and nm.get("all_ok") is True and res["pdf_diff_main"]["ok"] is True
          and res["pdf_diff_main_arxiv"]["ok"] is True)
    res["all_ok"] = ok
    if "--json" in sys.argv:
        jp = sys.argv[sys.argv.index("--json") + 1]
        open(jp if os.path.isabs(jp) else os.path.join(P, jp), "wb").write((json.dumps(res, indent=1) + "\n").encode("utf-8"))
    print("v7 checks", res["check_build_v7"]["all_ok"], "| name check", res["name_check"]["all_ok"], "(old-name hits",
          res["name_check"]["old_name_total_hits"], ") | pdf diff main", res["pdf_diff_main"]["ok"], "arxiv", res["pdf_diff_main_arxiv"]["ok"],
          "ALL_OK" if ok else "NOT_OK")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
