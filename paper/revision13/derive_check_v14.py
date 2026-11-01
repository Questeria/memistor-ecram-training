"""Version 14: derive revision13/check_build_v14.py from revision12/check_build_v13.py by named anchors (new docstring; the version-14
records; the v12 -> v14 negative control; Figure 1's check, revision13/check_fig_arch.py, added).

    python -I -B revision13/derive_check_v14.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = '''"""Version 14: check the version-14 build.  Everything revision6/check_build_v7.py checks (which runs revision5/check_build_v6.py, the
leftover-LaTeX check and their self-tests), plus the proofs of version 14, run beforehand and read here:

  records/revision13/NAME-CHECK-v14.json        revision9/name_check_v10.py    the old name appears only inside the GitHub mirror's
                                                address, which the owner allowed on 2026-10-28 (WSL venv, PyMuPDF)
  records/revision13/NAME-CHECK-v14-windows.json  the same check on Windows
  records/revision13/PDF-TEXT-DIFF-main.json, -main-arxiv.json   revision13/pdf_text_diff_v14.py  v13 -> v14: every word's count
                                                changes exactly as the expected edits change it (reference numbers as [#]); one
                                                page more (43 -> 44)
  records/revision13/PDF-TEXT-DIFF-negative-v12-v14.json         the same check on v12 -> v14 must FAIL
  records/revision13/NUMBERS-FRESH.json         revision8/check_numbers_fresh.py --selftest     every tex/numbers*.tex equals its
                                                regeneration; the self-test shows it failing on planted faults
  records/revision13/FIG-MAIN-CHECK.json        revision10/check_fig_main.py --selftest   Figure 4 (version 1's fig_main) draws every
                                                mean and interval of its results and its legend overlaps no label; version 10's code fails it
  records/revision13/FIG-ARCH-CHECK.json        revision13/check_fig_arch.py --selftest   Figure 1 (fig_arch) matches the simulator's
                                                device and digital state, ideal reads and pulse targets, and no label overlaps; four
                                                planted faults are caught
  records/revision13/TESTS-IDEAL-RESET-COLS.json  sim/test_ideal_reset_cols.py   the ideal reset of a partial column selection
                                                under AIHWKIT bounds works; the old line fails
  records/revision13/TESTS-WELCH-DF.json        revision11/test_welch_df.py   the width study's Welch interval at the Welch-
                                                Satterthwaite df (closed forms, the records, review 9's value); the floored df fails

It re-runs the numbers check live as well.  Derived from revision12/check_build_v13.py by revision13/derive_check_v14.py.

    H:/x1000/bench/venv/Scripts/python.exe -B revision13/check_build_v14.py <build out dir> [--json records/revision13/ARTIFACT-CHECK-v14.json]
"""
'''
SUBS = [
    ("name record", 'load("records/revision12/NAME-CHECK-v13.json")', 'load("records/revision13/NAME-CHECK-v14.json")'),
    ("windows name record", 'load("records/revision12/NAME-CHECK-v13-windows.json")', 'load("records/revision13/NAME-CHECK-v14-windows.json")'),
    ("diff records", 'load("records/revision12/" + f)', 'load("records/revision13/" + f)'),
    ("negative", 'load("records/revision12/PDF-TEXT-DIFF-negative-v11-v13.json")', 'load("records/revision13/PDF-TEXT-DIFF-negative-v12-v14.json")'),
    ("numbers record", 'load("records/revision12/NUMBERS-FRESH.json")', 'load("records/revision13/NUMBERS-FRESH.json")'),
    ("fig record", 'load("records/revision12/FIG-MAIN-CHECK.json")', 'load("records/revision13/FIG-MAIN-CHECK.json")'),
    ("fig arch record",
     '    res["fig_main_recorded"] = dict(all_ok=fm.get("all_ok"), selftest_ok=fm.get("selftest", {}).get("ok"))\n',
     '    res["fig_main_recorded"] = dict(all_ok=fm.get("all_ok"), selftest_ok=fm.get("selftest", {}).get("ok"))\n'
     '    fa = load("records/revision13/FIG-ARCH-CHECK.json")\n'
     '    res["fig_arch_recorded"] = dict(all_ok=fa.get("all_ok"), selftest_ok=fa.get("selftest", {}).get("ok"),\n'
     '                                    faults=fa.get("selftest", {}).get("faults"))\n'),
    ("reset record", 'load("records/revision12/TESTS-IDEAL-RESET-COLS.json")', 'load("records/revision13/TESTS-IDEAL-RESET-COLS.json")'),
    ("welch record", 'load("records/revision12/TESTS-WELCH-DF.json")', 'load("records/revision13/TESTS-WELCH-DF.json")'),
    ("ok", 'and fm.get("all_ok") is True and fm.get("selftest", {}).get("ok") is True',
     'and fm.get("all_ok") is True and fm.get("selftest", {}).get("ok") is True\n'
     '          and fa.get("all_ok") is True and fa.get("selftest", {}).get("ok") is True'),
    ("print", '"| v11->v13 diff fails"', '"| v12->v14 diff fails"'),
    ("print arch", '"| fig main", fm.get("all_ok"),', '"| fig main", fm.get("all_ok"), "| fig arch", fa.get("all_ok"),'),
]
t = (HERE.parent / "revision12" / "check_build_v13.py").read_bytes().decode("utf-8")
code = t[t.index("import json\n"):]
for name, a, b in SUBS:
    assert code.count(a) == 1, (name, code.count(a))
    code = code.replace(a, b)
(HERE / "check_build_v14.py").write_bytes((DOC + code).encode("utf-8"))
print("wrote revision13/check_build_v14.py")
