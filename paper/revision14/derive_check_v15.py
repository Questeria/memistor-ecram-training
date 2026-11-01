"""Version 15: derive revision14/check_build_v15.py from revision13/check_build_v14.py by named anchors (the docstring's version and
record folder; the version-15 records in records/revision14/; the v13 -> v15 negative control; Figure 1's check is now
revision14/check_fig_arch.py, with eight planted faults).

    python -I -B revision14/derive_check_v15.py
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
t = (HERE.parent / "revision13" / "check_build_v14.py").read_bytes().decode("utf-8")
SUBS = [
    ("doc head", "Version 14: check the version-14 build.", "Version 15: check the version-15 build."),
    ("doc proofs", "plus the proofs of version 14, run beforehand", "plus the proofs of version 15, run beforehand"),
    ("doc diff", "revision13/pdf_text_diff_v14.py  v13 -> v14: every word's count\n"
                 "                                                changes exactly as the expected edits change it (reference numbers as [#]); one\n"
                 "                                                page more (43 -> 44)",
     "revision14/pdf_text_diff_v15.py  v14 -> v15: every word's count\n"
     "                                                changes exactly as the expected edits change it (reference numbers as [#]); the\n"
     "                                                same number of pages (44)"),
    ("doc negative", "PDF-TEXT-DIFF-negative-v12-v14.json         the same check on v12 -> v14 must FAIL",
     "PDF-TEXT-DIFF-negative-v13-v15.json         the same check on v13 -> v15 must FAIL"),
    ("doc arch", "revision13/check_fig_arch.py --selftest   Figure 1 (fig_arch) matches the simulator's\n"
                 "                                                device and digital state, ideal reads and pulse targets, and no label overlaps; four\n"
                 "                                                planted faults are caught",
     "revision14/check_fig_arch.py --selftest   Figure 1 (fig_arch) matches the selected\n"
     "                                                settings, the main-experiment records and the simulator in those configurations (state,\n"
     "                                                ideal reads, pulse targets, reset, chopper), and no label overlaps; eight planted\n"
     "                                                faults are caught (AGAD drawn with the pulse reset among them)"),
    ("doc derived", "Derived from revision12/check_build_v13.py by revision13/derive_check_v14.py.",
     "Derived from revision13/check_build_v14.py by revision14/derive_check_v15.py."),
    ("doc usage", "revision13/check_build_v14.py <build out dir> [--json records/revision13/ARTIFACT-CHECK-v14.json]",
     "revision14/check_build_v15.py <build out dir> [--json records/revision14/ARTIFACT-CHECK-v15.json]"),
    ("name", 'load("records/revision13/NAME-CHECK-v14.json")', 'load("records/revision14/NAME-CHECK-v15.json")'),
    ("name w", 'load("records/revision13/NAME-CHECK-v14-windows.json")', 'load("records/revision14/NAME-CHECK-v15-windows.json")'),
    ("diffs", 'load("records/revision13/" + f)', 'load("records/revision14/" + f)'),
    ("neg", 'load("records/revision13/PDF-TEXT-DIFF-negative-v12-v14.json")', 'load("records/revision14/PDF-TEXT-DIFF-negative-v13-v15.json")'),
    ("nf", 'load("records/revision13/NUMBERS-FRESH.json")', 'load("records/revision14/NUMBERS-FRESH.json")'),
    ("fm", 'load("records/revision13/FIG-MAIN-CHECK.json")', 'load("records/revision14/FIG-MAIN-CHECK.json")'),
    ("fa", 'load("records/revision13/FIG-ARCH-CHECK.json")', 'load("records/revision14/FIG-ARCH-CHECK.json")'),
    ("tr", 'load("records/revision13/TESTS-IDEAL-RESET-COLS.json")', 'load("records/revision14/TESTS-IDEAL-RESET-COLS.json")'),
    ("wd", 'load("records/revision13/TESTS-WELCH-DF.json")', 'load("records/revision14/TESTS-WELCH-DF.json")'),
    ("print", '"| v12->v14 diff fails"', '"| v13->v15 diff fails"'),
]
for name, a, b in SUBS:
    assert t.count(a) == 1, (name, t.count(a))
    t = t.replace(a, b)
head, code = t.split('"""\nimport json', 1)                 # the docstring's record table names the record folder
head = head.replace("  records/revision13/", "  records/revision14/").replace("NAME-CHECK-v14", "NAME-CHECK-v15")
t = head + '"""\nimport json' + code
assert "revision13/" not in t.replace("revision13/check_build_v14.py", ""), "a version-14 record is left"
(HERE / "check_build_v15.py").write_bytes(t.encode("utf-8"))
print("wrote revision14/check_build_v15.py")
