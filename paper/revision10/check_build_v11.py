"""Version 11: check the version-11 build.  Everything revision6/check_build_v7.py checks (which runs revision5/check_build_v6.py, the
leftover-LaTeX check and their self-tests), plus the proofs of version 11, run beforehand and read here:

  records/revision10/NAME-CHECK-v11.json        revision9/name_check_v10.py    the old name appears only inside the GitHub mirror's
                                                address, which the owner allowed on 2026-10-28 (WSL venv, PyMuPDF)
  records/revision10/PDF-TEXT-DIFF-main.json, -main-arxiv.json   revision10/pdf_text_diff_v11.py  v10 -> v11: only the expected hunks
  records/revision10/PDF-TEXT-DIFF-negative-v9-v11.json          the same check on v9 -> v11 must FAIL (it is not the expected edit set)
  records/revision10/NUMBERS-FRESH.json         revision8/check_numbers_fresh.py --selftest     every tex/numbers*.tex equals its
                                                regeneration; the self-test shows it failing on planted faults
  records/revision10/FIG-MAIN-CHECK.json        revision10/check_fig_main.py --selftest   Figure 3 draws every mean and interval of
                                                its results and its legend overlaps no label; version 10's code fails it
  records/revision10/TESTS-IDEAL-RESET-COLS.json  sim/test_ideal_reset_cols.py   the ideal reset of a partial column selection
                                                under AIHWKIT bounds works; the old line fails

It re-runs the numbers check live as well.  Derived from revision9/check_build_v10.py by revision10/derive_check_v11.py.

    H:/x1000/bench/venv/Scripts/python.exe -B revision10/check_build_v11.py <build out dir> [--json records/revision10/ARTIFACT-CHECK-v11.json]
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
    nm = load("records/revision10/NAME-CHECK-v11.json")
    res["name_check"] = dict(all_ok=nm.get("all_ok"), outside_address=nm.get("judge", {}).get("outside_allowed"),
                             selftest_ok=nm.get("selftest", {}).get("ok"))
    for k, f in (("pdf_diff_main", "PDF-TEXT-DIFF-main.json"), ("pdf_diff_main_arxiv", "PDF-TEXT-DIFF-main-arxiv.json")):
        d = load("records/revision10/" + f)
        res[k] = dict(ok=d.get("ok"), hunks=len(d.get("hunks", [])), unexpected=len(d.get("unexpected_hunks", [])),
                      moved=len(d.get("moved_blocks", [])), pages=(d.get("pages_old"), d.get("pages_new")))
    neg = load("records/revision10/PDF-TEXT-DIFF-negative-v9-v11.json")
    res["pdf_diff_negative_control"] = dict(fails_as_it_must=(neg.get("ok") is False), unexpected_hunks=len(neg.get("unexpected_hunks", [])))
    nf = load("records/revision10/NUMBERS-FRESH.json")
    res["numbers_fresh_recorded"] = dict(ok=nf.get("ok"), files=nf.get("numbers_files"), selftest_ok=nf.get("selftest", {}).get("ok"))
    rf = subprocess.run([sys.executable, "-B", os.path.join(P, "revision8", "check_numbers_fresh.py")], capture_output=True, text=True)
    res["numbers_fresh_live"] = dict(rc=rf.returncode, tail=rf.stdout.strip()[-200:])
    fm = load("records/revision10/FIG-MAIN-CHECK.json")
    res["fig_main_recorded"] = dict(all_ok=fm.get("all_ok"), selftest_ok=fm.get("selftest", {}).get("ok"))
    tr = load("records/revision10/TESTS-IDEAL-RESET-COLS.json")
    caught = bool(tr.get("faults")) and all(f.get("caught") for f in tr.get("faults", {}).values())
    res["ideal_reset_cols_recorded"] = dict(all_ok=tr.get("all_ok"), faults_caught=caught)
    ok = (r7.returncode == 0 and c7.get("all_ok") is True and nm.get("all_ok") is True
          and res["pdf_diff_main"]["ok"] is True and res["pdf_diff_main_arxiv"]["ok"] is True
          and res["pdf_diff_negative_control"]["fails_as_it_must"] and nf.get("ok") is True
          and nf.get("selftest", {}).get("ok") is True and rf.returncode == 0
          and fm.get("all_ok") is True and fm.get("selftest", {}).get("ok") is True and tr.get("all_ok") is True and caught)
    res["all_ok"] = ok
    if "--json" in sys.argv:
        jp = sys.argv[sys.argv.index("--json") + 1]
        jp = jp if os.path.isabs(jp) else os.path.join(P, jp)
        os.makedirs(os.path.dirname(jp), exist_ok=True)
        open(jp, "wb").write((json.dumps(res, indent=1) + "\n").encode("utf-8"))
    print("v7 checks", res["check_build_v7"]["all_ok"], "| name check", res["name_check"]["all_ok"], "| pdf diff main",
          res["pdf_diff_main"]["ok"], "arxiv", res["pdf_diff_main_arxiv"]["ok"], "| v9->v11 diff fails", res["pdf_diff_negative_control"]["fails_as_it_must"],
          "| numbers fresh", nf.get("ok"), "live rc", rf.returncode, "| fig main", fm.get("all_ok"), "| reset check", tr.get("all_ok"), "ALL_OK" if ok else "NOT_OK")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
