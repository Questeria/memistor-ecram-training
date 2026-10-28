"""ME-REVISE-3: derive pod/build_payload_rev3.py and pod/build_rev3.sh from the _rev2 versions by named anchors.

    python -B pod/derive_build_rev3.py

build_payload_rev3.py: the lint also reads tex/numbers_rev3.tex and checks \\RY... macros (and bare RY names); it packs
build_rev3.sh as run.sh.
build_rev3.sh: the arXiv archive also carries numbers_rev3.tex. Version 4 is built on the desk, in WSL Ubuntu, with the same
tools the pod used (PLAN-REVISION-3.md section 4); the script itself is unchanged otherwise.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
t = (HERE / "build_payload_rev2.py").read_bytes().decode("utf-8")
SUBS = [
    ("defined", '(TEX / "numbers_rev2.tex").read_text("utf-8")))',
     '(TEX / "numbers_rev2.tex").read_text("utf-8") + (TEX / "numbers_rev3.tex").read_text("utf-8")))'),
    ("macro_re", 'RX[A-Za-z]+|nChecks|nFaults)\\b"', 'RX[A-Za-z]+|RY[A-Za-z]+|nChecks|nFaults)\\b"'),
    ("bare", 'X[A-Z][a-z]|E[A-Z][a-z])[A-Za-z]{2,})"', 'X[A-Z][a-z]|Y[A-Z][a-z]|E[A-Z][a-z])[A-Za-z]{2,})"'),
    ("runsh", '    files["run.sh"] = (HERE / "build_rev2.sh").read_bytes()\n', '    files["run.sh"] = (HERE / "build_rev3.sh").read_bytes()\n'),
    ("htmlprep", '    files["html_prep.py"] = (HERE / "html_prep.py").read_bytes()\n',
     '    files["html_prep.py"] = (HERE / "html_prep_rev3.py").read_bytes()\n'),
]
for name, a, b in SUBS:
    assert t.count(a) == 1, name
    t = t.replace(a, b)
(HERE / "build_payload_rev3.py").write_bytes(t.encode("utf-8"))

s = (HERE / "build_rev2.sh").read_bytes().decode("utf-8")
SUBS2 = [
    ("tar", "numbers_rev.tex numbers_rev2.tex tables", "numbers_rev.tex numbers_rev2.tex numbers_rev3.tex tables"),
    ("head", "# Lane ME-REVISE-2 build sitting (derived by pod/derive_build_rev2.py from build_rev.sh).",
     "# Lane ME-REVISE-3 build (derived by pod/derive_build_rev3.py from build_rev2.sh; run on the desk in WSL Ubuntu)."),
]
for name, a, b in SUBS2:
    assert s.count(a) == 1, name
    s = s.replace(a, b)
(HERE / "build_rev3.sh").write_bytes(s.encode("utf-8"))

# html_prep_rev3.py: the HTML head defined only tex/numbers.tex, so pandoc silently dropped every revision number (\RV, \RX,
# \RY macros) from the HTML text of v2 and v3 (found by ME-REVISE-3; revision3/check_build_v4.py now compares the abstract's
# digits between the HTML and the generated arXiv abstract)
h = (HERE / "html_prep.py").read_bytes().decode("utf-8")
a = 'numbers = (D / "numbers.tex").read_text(encoding="utf-8")'
b = ('numbers = "\\n".join((D / n).read_text(encoding="utf-8") for n in ("numbers.tex", "numbers_rev.tex", "numbers_rev2.tex",\n'
     '                                                                     "numbers_rev3.tex"))')
assert h.count(a) == 1, "html numbers"
(HERE / "html_prep_rev3.py").write_bytes(h.replace(a, b).encode("utf-8"))
print("wrote build_payload_rev3.py, build_rev3.sh and html_prep_rev3.py")
