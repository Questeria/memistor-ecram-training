"""Version 13: derive revision12/check_build_v13.py from revision11/check_build_v12.py by named anchors (new docstring; the version-13
records; the v11 -> v13 negative control; the Windows run of the name check, review 10 finding 4, added).

    python -I -B revision12/derive_check_v13.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = '''"""Version 13: check the version-13 build.  Everything revision6/check_build_v7.py checks (which runs revision5/check_build_v6.py, the
leftover-LaTeX check and their self-tests), plus the proofs of version 13, run beforehand and read here:

  records/revision12/NAME-CHECK-v13.json        revision9/name_check_v10.py    the old name appears only inside the GitHub mirror's
                                                address, which the owner allowed on 2026-10-28 (WSL venv, PyMuPDF)
  records/revision12/NAME-CHECK-v13-windows.json  the same check on Windows (review 10, finding 4: it now closes the copied PDF
                                                before its temporary folder is removed; NAME-CHECK-WINDOWS-F4.json has the old run)
  records/revision12/PDF-TEXT-DIFF-main.json, -main-arxiv.json   revision12/pdf_text_diff_v13.py  v12 -> v13: every word's count
                                                changes exactly as the expected edits change it; pages equal
  records/revision12/PDF-TEXT-DIFF-negative-v11-v13.json         the same check on v11 -> v13 must FAIL
  records/revision12/NUMBERS-FRESH.json         revision8/check_numbers_fresh.py --selftest     every tex/numbers*.tex equals its
                                                regeneration; the self-test shows it failing on planted faults
  records/revision12/FIG-MAIN-CHECK.json        revision10/check_fig_main.py --selftest   Figure 3 draws every mean and interval of
                                                its results and its legend overlaps no label; version 10's code (bundled) fails it
  records/revision12/TESTS-IDEAL-RESET-COLS.json  sim/test_ideal_reset_cols.py   the ideal reset of a partial column selection
                                                under AIHWKIT bounds works; the old line fails
  records/revision12/TESTS-WELCH-DF.json        revision11/test_welch_df.py   the width study's Welch interval at the Welch-
                                                Satterthwaite df (closed forms, the records, review 9's value); the floored df fails

It re-runs the numbers check live as well.  Derived from revision11/check_build_v12.py by revision12/derive_check_v13.py.

    H:/x1000/bench/venv/Scripts/python.exe -B revision12/check_build_v13.py <build out dir> [--json records/revision12/ARTIFACT-CHECK-v13.json]
"""
'''
SUBS = [
    ("name record", 'load("records/revision11/NAME-CHECK-v12.json")', 'load("records/revision12/NAME-CHECK-v13.json")'),
    ("windows name record",
     '                             selftest_ok=nm.get("selftest", {}).get("ok"))\n',
     '                             selftest_ok=nm.get("selftest", {}).get("ok"))\n'
     '    nw = load("records/revision12/NAME-CHECK-v13-windows.json")\n'
     '    res["name_check_windows"] = dict(all_ok=nw.get("all_ok"), selftest_ok=nw.get("selftest", {}).get("ok"))\n'),
    ("diff records", 'load("records/revision11/" + f)', 'load("records/revision12/" + f)'),
    ("negative", 'load("records/revision11/PDF-TEXT-DIFF-negative-v10-v12.json")', 'load("records/revision12/PDF-TEXT-DIFF-negative-v11-v13.json")'),
    ("numbers record", 'load("records/revision11/NUMBERS-FRESH.json")', 'load("records/revision12/NUMBERS-FRESH.json")'),
    ("fig record", 'load("records/revision11/FIG-MAIN-CHECK.json")', 'load("records/revision12/FIG-MAIN-CHECK.json")'),
    ("reset record", 'load("records/revision11/TESTS-IDEAL-RESET-COLS.json")', 'load("records/revision12/TESTS-IDEAL-RESET-COLS.json")'),
    ("welch record", 'load("records/revision11/TESTS-WELCH-DF.json")', 'load("records/revision12/TESTS-WELCH-DF.json")'),
    ("ok", 'and c7.get("all_ok") is True and nm.get("all_ok") is True\n',
     'and c7.get("all_ok") is True and nm.get("all_ok") is True and nw.get("all_ok") is True\n'),
    ("print", '"| v10->v12 diff fails"', '"| v11->v13 diff fails"'),
    ("print windows", '"| name check", res["name_check"]["all_ok"],', '"| name check", res["name_check"]["all_ok"], "windows", nw.get("all_ok"),'),
]
t = (HERE.parent / "revision11" / "check_build_v12.py").read_bytes().decode("utf-8")
code = t[t.index("import json\n"):]
for name, a, b in SUBS:
    assert code.count(a) == 1, (name, code.count(a))
    code = code.replace(a, b)
(HERE / "check_build_v13.py").write_bytes((DOC + code).encode("utf-8"))
print("wrote revision12/check_build_v13.py")
