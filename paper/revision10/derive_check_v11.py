"""Version 11: derive revision10/check_build_v11.py from revision9/check_build_v10.py by named anchors (new docstring; the version-11
records; the Figure 3 check and the ideal-reset check added).

    python -I -B revision10/derive_check_v11.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = '''"""Version 11: check the version-11 build.  Everything revision6/check_build_v7.py checks (which runs revision5/check_build_v6.py, the
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
'''
SUBS = [
    ("name record", 'load("records/revision9/NAME-CHECK-v10.json")', 'load("records/revision10/NAME-CHECK-v11.json")'),
    ("diff records", 'load("records/revision9/" + f)', 'load("records/revision10/" + f)'),
    ("negative", 'load("records/revision9/PDF-TEXT-DIFF-negative-v8-v10.json")', 'load("records/revision10/PDF-TEXT-DIFF-negative-v9-v11.json")'),
    ("numbers record", 'load("records/revision9/NUMBERS-FRESH.json")', 'load("records/revision10/NUMBERS-FRESH.json")'),
    ("new records", '    res["numbers_fresh_live"] = dict(rc=rf.returncode, tail=rf.stdout.strip()[-200:])\n',
     '    res["numbers_fresh_live"] = dict(rc=rf.returncode, tail=rf.stdout.strip()[-200:])\n'
     '    fm = load("records/revision10/FIG-MAIN-CHECK.json")\n'
     '    res["fig_main_recorded"] = dict(all_ok=fm.get("all_ok"), selftest_ok=fm.get("selftest", {}).get("ok"))\n'
     '    tr = load("records/revision10/TESTS-IDEAL-RESET-COLS.json")\n'
     '    caught = bool(tr.get("faults")) and all(f.get("caught") for f in tr.get("faults", {}).values())\n'
     '    res["ideal_reset_cols_recorded"] = dict(all_ok=tr.get("all_ok"), faults_caught=caught)\n'),
    ("ok", 'and nf.get("selftest", {}).get("ok") is True and rf.returncode == 0)',
     'and nf.get("selftest", {}).get("ok") is True and rf.returncode == 0\n'
     '          and fm.get("all_ok") is True and fm.get("selftest", {}).get("ok") is True and tr.get("all_ok") is True and caught)'),
    ("print", '"| v8->v10 diff fails"', '"| v9->v11 diff fails"'),
    ("print new", '"| numbers fresh", nf.get("ok"), "live rc", rf.returncode,',
     '"| numbers fresh", nf.get("ok"), "live rc", rf.returncode, "| fig main", fm.get("all_ok"), "| reset check", tr.get("all_ok"),'),
]
t = (HERE.parent / "revision9" / "check_build_v10.py").read_bytes().decode("utf-8")
code = t[t.index("import json\n"):]
for name, a, b in SUBS:
    assert code.count(a) == 1, (name, code.count(a))
    code = code.replace(a, b)
(HERE / "check_build_v11.py").write_bytes((DOC + code).encode("utf-8"))
print("wrote revision10/check_build_v11.py")
