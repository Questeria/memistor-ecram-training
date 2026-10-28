"""ME-REVISE-4: derive pod/build_payload_rev4.py, pod/build_rev4.sh and pod/html_prep_rev4.py from the _rev3 versions by named
anchors, and revision4/make_abstract_v5.py from revision3/make_abstract_v4.py.

    python -B pod/derive_build_rev4.py

build_payload_rev4.py: the lint also reads tex/numbers_rev4.tex and checks \\RZ... macros (and bare RZ names); it packs
build_rev4.sh as run.sh and html_prep_rev4.py. build_rev4.sh: the arXiv archive also carries numbers_rev4.tex. html_prep_rev4.py:
the HTML head also defines numbers_rev4.tex (else pandoc drops every \\RZ number silently). make_abstract_v5.py: also expands
numbers_rev4.tex and refuses the phrases withdrawn after review 4. Version 5 is built on the desk in WSL Ubuntu, as version 4.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def derive(src, dst, subs):
    t = src.read_bytes().decode("utf-8")
    for name, a, b in subs:
        assert t.count(a) == 1, (dst.name, name)
        t = t.replace(a, b)
    dst.write_bytes(t.encode("utf-8"))


derive(HERE / "build_payload_rev3.py", HERE / "build_payload_rev4.py", [
    ("defined", '(TEX / "numbers_rev3.tex").read_text("utf-8")))',
     '(TEX / "numbers_rev3.tex").read_text("utf-8") + (TEX / "numbers_rev4.tex").read_text("utf-8")))'),
    ("macro_re", '|RY[A-Za-z]+|nChecks|nFaults)\\b"', '|RY[A-Za-z]+|RZ[A-Za-z]+|nChecks|nFaults)\\b"'),
    ("bare", '|Y[A-Z][a-z]|E[A-Z][a-z])[A-Za-z]{2,})"', '|Y[A-Z][a-z]|Z[A-Z][a-z]|E[A-Z][a-z])[A-Za-z]{2,})"'),
    ("runsh", '(HERE / "build_rev3.sh").read_bytes()', '(HERE / "build_rev4.sh").read_bytes()'),
    ("htmlprep", '(HERE / "html_prep_rev3.py").read_bytes()', '(HERE / "html_prep_rev4.py").read_bytes()'),
])
derive(HERE / "build_rev3.sh", HERE / "build_rev4.sh", [
    ("tar", "numbers_rev2.tex numbers_rev3.tex tables", "numbers_rev2.tex numbers_rev3.tex numbers_rev4.tex tables"),
    ("head", "# Lane ME-REVISE-3 build (derived by pod/derive_build_rev3.py from build_rev2.sh; run on the desk in WSL Ubuntu).",
     "# Lane ME-REVISE-4 build (derived by pod/derive_build_rev4.py from build_rev3.sh; run on the desk in WSL Ubuntu)."),
    ("aux", 'cp -f "$M.pdf" "$M.log" "$M.bbl" "$OUT/"', 'cp -f "$M.pdf" "$M.log" "$M.bbl" "$M.aux" "$OUT/"'),
])
derive(HERE / "html_prep_rev3.py", HERE / "html_prep_rev4.py", [
    ("numbers", '"numbers_rev3.tex"))', '"numbers_rev3.tex", "numbers_rev4.tex"))'),
])
R = HERE.parent / "revision3"
derive(R / "make_abstract_v4.py", HERE.parent / "revision4" / "make_abstract_v5.py", [
    ("files", '"numbers_rev2.tex", "numbers_rev3.tex")', '"numbers_rev2.tex", "numbers_rev3.tex", "numbers_rev4.tex")'),
    ("withdrawn", '"preserves the ranking", "valid reference"]',
     '"preserves the ranking", "valid reference", "rounding alone", "more sensitive to rounding", "two independent reviews"]'),
    ("doc", "ME-REVISE-3 (derived by revision3/derive_make_abstract_v4.py)",
     "ME-REVISE-4 (derived by pod/derive_build_rev4.py from revision3/make_abstract_v4.py)"),
])
print("wrote build_payload_rev4.py, build_rev4.sh, html_prep_rev4.py, revision4/make_abstract_v5.py")
