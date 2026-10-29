"""Version 10: derive revision9/check_build_v10.py from revision8/check_build_v9.py by named anchors (new docstring; the version-10 records).

    python -I -B revision9/derive_check_v10.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
DOC = '''"""Version 10: check the version-10 build.  Everything revision6/check_build_v7.py checks (which runs revision5/check_build_v6.py, the
leftover-LaTeX check and their self-tests), plus the proofs of version 10, run beforehand and read here:

  records/revision9/NAME-CHECK-v10.json         revision9/name_check_v10.py    the old name appears only inside the GitHub mirror's
                                                address, which the owner allowed on 2026-10-28 (WSL venv, PyMuPDF)
  records/revision9/PDF-TEXT-DIFF-main.json, -main-arxiv.json    revision9/pdf_text_diff_v10.py   v9 -> v10: only the expected hunks
  records/revision9/PDF-TEXT-DIFF-negative-v8-v10.json           the same check on v8 -> v10 must FAIL (it is not the expected edit set)
  records/revision9/NUMBERS-FRESH.json          revision8/check_numbers_fresh.py --selftest     every tex/numbers*.tex equals its
                                                regeneration; the self-test shows it failing on planted faults

It re-runs the numbers check live as well.  Derived from revision8/check_build_v9.py by revision9/derive_check_v10.py.

    H:/x1000/bench/venv/Scripts/python.exe -B revision9/check_build_v10.py <build out dir> [--json records/revision9/ARTIFACT-CHECK-v10.json]
"""
'''
SUBS = [
    ("name record", 'load("records/revision8/NAME-CHECK-v9.json")', 'load("records/revision9/NAME-CHECK-v10.json")'),
    ("name fields", 'old_name_total_hits=nm.get("old_name_total_hits"),', 'outside_address=nm.get("judge", {}).get("outside_allowed"),'),
    ("diff records", 'load("records/revision8/" + f)', 'load("records/revision9/" + f)'),
    ("negative", 'load("records/revision8/PDF-TEXT-DIFF-negative-v7-v9.json")', 'load("records/revision9/PDF-TEXT-DIFF-negative-v8-v10.json")'),
    ("numbers record", 'load("records/revision8/NUMBERS-FRESH.json")', 'load("records/revision9/NUMBERS-FRESH.json")'),
    ("numbers live", 'os.path.join(HERE, "check_numbers_fresh.py")', 'os.path.join(P, "revision8", "check_numbers_fresh.py")'),
    ("print", '"| v7->v9 diff fails"', '"| v8->v10 diff fails"'),
]
t = (HERE.parent / "revision8" / "check_build_v9.py").read_bytes().decode("utf-8")
code = t[t.index("import json\n"):]
for name, a, b in SUBS:
    assert code.count(a) == 1, (name, code.count(a))
    code = code.replace(a, b)
(HERE / "check_build_v10.py").write_bytes((DOC + code).encode("utf-8"))
print("wrote revision9/check_build_v10.py")
