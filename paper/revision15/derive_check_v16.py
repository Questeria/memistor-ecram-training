"""Version 16: derive revision15/check_build_v16.py from revision14/check_build_v15.py by named anchors (the docstring's version and
record folder; the version-16 records in records/revision15/; the v14 -> v16 negative control; Figure 1's check stays
revision14/check_fig_arch.py).

    python -I -B revision15/derive_check_v16.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
t = (HERE.parent / "revision14" / "check_build_v15.py").read_bytes().decode("utf-8")
SUBS = [
    ("doc head", "Version 15: check the version-15 build.", "Version 16: check the version-16 build."),
    ("doc proofs", "plus the proofs of version 15, run beforehand", "plus the proofs of version 16, run beforehand"),
    ("doc diff", "revision14/pdf_text_diff_v15.py  v14 -> v15: every word's count", "revision15/pdf_text_diff_v16.py  v15 -> v16: every word's count"),
    ("doc negative", "PDF-TEXT-DIFF-negative-v13-v15.json         the same check on v13 -> v15 must FAIL",
     "PDF-TEXT-DIFF-negative-v14-v16.json         the same check on v14 -> v16 must FAIL"),
    ("doc derived", "Derived from revision13/check_build_v14.py by revision14/derive_check_v15.py.",
     "Derived from revision14/check_build_v15.py by revision15/derive_check_v16.py."),
    ("doc usage", "revision14/check_build_v15.py <build out dir> [--json records/revision14/ARTIFACT-CHECK-v15.json]",
     "revision15/check_build_v16.py <build out dir> [--json records/revision15/ARTIFACT-CHECK-v16.json]"),
    ("name", 'load("records/revision14/NAME-CHECK-v15.json")', 'load("records/revision15/NAME-CHECK-v16.json")'),
    ("name w", 'load("records/revision14/NAME-CHECK-v15-windows.json")', 'load("records/revision15/NAME-CHECK-v16-windows.json")'),
    ("diffs", 'load("records/revision14/" + f)', 'load("records/revision15/" + f)'),
    ("neg", 'load("records/revision14/PDF-TEXT-DIFF-negative-v13-v15.json")', 'load("records/revision15/PDF-TEXT-DIFF-negative-v14-v16.json")'),
    ("nf", 'load("records/revision14/NUMBERS-FRESH.json")', 'load("records/revision15/NUMBERS-FRESH.json")'),
    ("fm", 'load("records/revision14/FIG-MAIN-CHECK.json")', 'load("records/revision15/FIG-MAIN-CHECK.json")'),
    ("fa", 'load("records/revision14/FIG-ARCH-CHECK.json")', 'load("records/revision15/FIG-ARCH-CHECK.json")'),
    ("tr", 'load("records/revision14/TESTS-IDEAL-RESET-COLS.json")', 'load("records/revision15/TESTS-IDEAL-RESET-COLS.json")'),
    ("wd", 'load("records/revision14/TESTS-WELCH-DF.json")', 'load("records/revision15/TESTS-WELCH-DF.json")'),
    ("print", '"| v13->v15 diff fails"', '"| v14->v16 diff fails"'),
]
for name, a, b in SUBS:
    assert t.count(a) == 1, (name, t.count(a))
    t = t.replace(a, b)
head, code = t.split('"""\nimport json', 1)                 # the docstring's record table names the record folder
head = head.replace("  records/revision14/", "  records/revision15/").replace("NAME-CHECK-v15", "NAME-CHECK-v16")
head = head.replace("the same\n                                                number of pages (44)", "the same\n                                                number of pages (44)")
t = head + '"""\nimport json' + code
assert "records/revision14/" not in t, "a version-15 record is left"
assert "v15.json" not in t.replace("check_build_v15.py", ""), "a version-15 name is left"
(HERE / "check_build_v16.py").write_bytes(t.encode("utf-8"))
print("wrote revision15/check_build_v16.py")
