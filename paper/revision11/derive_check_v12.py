"""Version 12: derive revision11/check_build_v12.py from revision10/check_build_v11.py by named anchors (new docstring; the version-12
records; the word-count text diff's fields; the Welch df test added).

    python -I -B revision11/derive_check_v12.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = '''"""Version 12: check the version-12 build.  Everything revision6/check_build_v7.py checks (which runs revision5/check_build_v6.py, the
leftover-LaTeX check and their self-tests), plus the proofs of version 12, run beforehand and read here:

  records/revision11/NAME-CHECK-v12.json        revision9/name_check_v10.py    the old name appears only inside the GitHub mirror's
                                                address, which the owner allowed on 2026-10-28 (WSL venv, PyMuPDF)
  records/revision11/PDF-TEXT-DIFF-main.json, -main-arxiv.json   revision11/pdf_text_diff_v12.py  v11 -> v12: every word's count
                                                changes exactly as the 46 expected edits change it; one page more
  records/revision11/PDF-TEXT-DIFF-negative-v10-v12.json         the same check on v10 -> v12 must FAIL
  records/revision11/NUMBERS-FRESH.json         revision8/check_numbers_fresh.py --selftest     every tex/numbers*.tex equals its
                                                regeneration; the self-test shows it failing on planted faults
  records/revision11/FIG-MAIN-CHECK.json        revision10/check_fig_main.py --selftest   Figure 3 draws every mean and interval of
                                                its results and its legend overlaps no label; version 10's code (bundled) fails it
  records/revision11/TESTS-IDEAL-RESET-COLS.json  sim/test_ideal_reset_cols.py   the ideal reset of a partial column selection
                                                under AIHWKIT bounds works; the old line fails
  records/revision11/TESTS-WELCH-DF.json        revision11/test_welch_df.py   the width study's Welch interval at the Welch-
                                                Satterthwaite df (closed forms, the records, review 9's value); the floored df fails

It re-runs the numbers check live as well.  Derived from revision10/check_build_v11.py by revision11/derive_check_v12.py.

    H:/x1000/bench/venv/Scripts/python.exe -B revision11/check_build_v12.py <build out dir> [--json records/revision11/ARTIFACT-CHECK-v12.json]
"""
'''
SUBS = [
    ("name record", 'load("records/revision10/NAME-CHECK-v11.json")', 'load("records/revision11/NAME-CHECK-v12.json")'),
    ("diff records", 'load("records/revision10/" + f)', 'load("records/revision11/" + f)'),
    ("diff fields", 'res[k] = dict(ok=d.get("ok"), hunks=len(d.get("hunks", [])), unexpected=len(d.get("unexpected_hunks", [])),\n'
                    '                      moved=len(d.get("moved_blocks", [])), pages=(d.get("pages_old"), d.get("pages_new")))',
     'res[k] = dict(ok=d.get("ok"), unexplained=len(d.get("unexplained_word_changes", {})),\n'
     '                      expected_not_seen=len(d.get("expected_not_seen", [])), rejoined=len(d.get("rejoined", [])),\n'
     '                      pages=(d.get("pages_old"), d.get("pages_new")))'),
    ("negative", 'load("records/revision10/PDF-TEXT-DIFF-negative-v9-v11.json")', 'load("records/revision11/PDF-TEXT-DIFF-negative-v10-v12.json")'),
    ("negative fields", 'unexpected_hunks=len(neg.get("unexpected_hunks", [])))', 'unexplained=len(neg.get("unexplained_word_changes", {})))'),
    ("numbers record", 'load("records/revision10/NUMBERS-FRESH.json")', 'load("records/revision11/NUMBERS-FRESH.json")'),
    ("fig record", 'load("records/revision10/FIG-MAIN-CHECK.json")', 'load("records/revision11/FIG-MAIN-CHECK.json")'),
    ("reset record", 'load("records/revision10/TESTS-IDEAL-RESET-COLS.json")', 'load("records/revision11/TESTS-IDEAL-RESET-COLS.json")'),
    ("welch record", '    res["ideal_reset_cols_recorded"] = dict(all_ok=tr.get("all_ok"), faults_caught=caught)\n',
     '    res["ideal_reset_cols_recorded"] = dict(all_ok=tr.get("all_ok"), faults_caught=caught)\n'
     '    wd = load("records/revision11/TESTS-WELCH-DF.json")\n'
     '    wf = wd.get("4_fault_floored_df", {}).get("detected") is True\n'
     '    res["welch_df_recorded"] = dict(all_ok=wd.get("all_ok"), floored_fault_detected=wf)\n'),
    ("ok", 'and tr.get("all_ok") is True and caught)', 'and tr.get("all_ok") is True and caught\n'
                                                       '          and wd.get("all_ok") is True and wf)'),
    ("print", '"| v9->v11 diff fails"', '"| v10->v12 diff fails"'),
    ("print new", '"| reset check", tr.get("all_ok"),', '"| reset check", tr.get("all_ok"), "| welch df", wd.get("all_ok"),'),
]
t = (HERE.parent / "revision10" / "check_build_v11.py").read_bytes().decode("utf-8")
code = t[t.index("import json\n"):]
for name, a, b in SUBS:
    assert code.count(a) == 1, (name, code.count(a))
    code = code.replace(a, b)
(HERE / "check_build_v12.py").write_bytes((DOC + code).encode("utf-8"))
print("wrote revision11/check_build_v12.py")
