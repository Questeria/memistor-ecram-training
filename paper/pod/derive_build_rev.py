"""REVISION: derive pod/build_payload_rev.py and pod/build_rev.sh from build_payload.py and build.sh by named anchors.

    python -B pod/derive_build_rev.py
build_payload_rev.py: the lint also reads tex/numbers_rev.tex and checks \\RV... macros; the payload adds
records/revision/RESULTS-REVISION.json and revision/make_figures_rev.py, and runs build_rev.sh.
build_rev.sh: also makes the revised figure (fig_rev_main).
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = HERE / "build_payload.py"
t = P.read_bytes().decode("utf-8")
SUBS = [
    ("defined",
     '(TEX / "numbers.tex").read_text("utf-8")))',
     '(TEX / "numbers.tex").read_text("utf-8") + (TEX / "numbers_rev.tex").read_text("utf-8")))'),
    ("macro_re", 'r"(R[A-Z][A-Za-z]*|nChecks|nFaults)\\b"', 'r"(R[A-Z][A-Za-z]*|RV[A-Za-z]+|nChecks|nFaults)\\b"'),
    ("records",
     '    files["make_figures.py"] = (PAPER / "make_figures.py").read_bytes()\n',
     '    files["make_figures.py"] = (PAPER / "make_figures.py").read_bytes()\n'
     '    files["records/revision/RESULTS-REVISION.json"] = (PAPER / "records" / "revision" / "RESULTS-REVISION.json").read_bytes()\n'
     '    files["make_figures_rev.py"] = (PAPER / "revision" / "make_figures_rev.py").read_bytes()\n'),
    ("runsh", '    files["run.sh"] = (HERE / "build.sh").read_bytes()\n', '    files["run.sh"] = (HERE / "build_rev.sh").read_bytes()\n'),
]
for name, a, b in SUBS:
    assert t.count(a) == 1, name
    t = t.replace(a, b)
(HERE / "build_payload_rev.py").write_bytes(t.encode("utf-8"))

s = (HERE / "build.sh").read_bytes().decode("utf-8")
a = 'log "figures: $(tr \'\\n\' \' \' < "$OUT/figures.txt" | cut -c1-200)"\n'
b = (a + '$PY "$HERE/make_figures_rev.py" --results "$HERE/records/revision/RESULTS-REVISION.json" --out "$HERE/tex/figs" '
     '> "$OUT/figures-rev.txt" 2>&1 || { log "REV FIGURE FAILED"; tail -5 "$OUT/figures-rev.txt"; }\n'
     'log "rev figure: $(tail -1 "$OUT/figures-rev.txt")"\n')
assert s.count(a) == 1, "build.sh figures anchor"
s = s.replace(a, b).replace("# Lane ME-PAPER build sitting.", "# Lane ME-REVISE build sitting (derived by pod/derive_build_rev.py from build.sh).")
(HERE / "build_rev.sh").write_bytes(s.encode("utf-8"))
print("wrote build_payload_rev.py and build_rev.sh")
