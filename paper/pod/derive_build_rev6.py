"""ME-REVISE-6: derive pod/build_payload_rev6.py, pod/build_rev6.sh and pod/html_prep_rev6.py from the _rev5 versions by named anchors.

    python -B pod/derive_build_rev6.py

html_prep_rev6.py: after the flattening, every \\cmidrule (with its optional [width], its optional (trim) and its {range}) and every
\\cline{range} is removed.  Reason (review 6): pandoc 2.19.2 leaves them as text, so Table 9's header printed '(lr)2-6(lr)7-8 Seed'.
build_rev6.sh: after pandoc it runs revision6/html_leftover.py as well as html_complete.py.
build_payload_rev6.py: packs build_rev6.sh, html_prep_rev6.py, html_complete.py and html_leftover.py.  Version 7 adds no number macro.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def derive(src, dst, subs):
    t = src.read_bytes().decode("utf-8")
    for name, a, b in subs:
        assert t.count(a) == 1, (dst.name, name, t.count(a))
        t = t.replace(a, b)
    dst.write_bytes(t.encode("utf-8"))


STRIP = r'''
RULE_RE = re.compile(re.escape(BS) + r"(?:cmidrule\s*(?:\[[^\]]*\])?\s*(?:\([^)]*\))?|cline)\s*\{[^}]*\}")


def strip_rules(t):
    """pandoc 2.19.2 leaves \\cmidrule[wd](trim){a-b} and \\cline{a-b} in the text of the cell that follows (review 6: Table 9's
    header read '(lr)2-6(lr)7-8 Seed').  Remove the whole command; the rules are drawing, not content."""
    return RULE_RE.subn("", t)


'''

derive(HERE / "html_prep_rev5.py", HERE / "html_prep_rev6.py", [
    ("def", "body = inline(\"body\")\n", STRIP.lstrip("\n") + "body = inline(\"body\")\n"),
    ("apply", 'body, napp = letter_appendices(body)\nprint("appendices lettered:", napp)\n',
     'body, napp = letter_appendices(body)\nprint("appendices lettered:", napp)\n'
     'body, nrules = strip_rules(body)\nprint("table rules (cmidrule/cline) removed:", nrules)\n'),
])
derive(HERE / "build_rev5.sh", HERE / "build_rev6.sh", [
    ("head", "# Lane ME-REVISE-5 build (derived by pod/derive_build_rev5.py from build_rev4.sh; run on the desk in WSL Ubuntu).",
     "# Lane ME-REVISE-6 build (derived by pod/derive_build_rev6.py from build_rev5.sh; run on the desk in WSL Ubuntu)."),
    ("leftover", 'mkdir -p "$OUT/figs" && cp -f figs/* "$OUT/figs/" 2>/dev/null\n',
     '$PY "$HERE/html_leftover.py" "$OUT/main.html" > "$OUT/html-leftover.txt" 2>&1 && log "html leftover: $(tr \'\\n\' \' \' < "$OUT/html-leftover.txt" | cut -c1-200)" || log "HTML LEFTOVER LATEX: $(tr \'\\n\' \' \' < "$OUT/html-leftover.txt" | cut -c1-300)"\n'
     'mkdir -p "$OUT/figs" && cp -f figs/* "$OUT/figs/" 2>/dev/null\n'),
])
derive(HERE / "build_payload_rev5.py", HERE / "build_payload_rev6.py", [
    ("runsh", '(HERE / "build_rev5.sh").read_bytes()', '(HERE / "build_rev6.sh").read_bytes()'),
    ("htmlprep", '(HERE / "html_prep_rev5.py").read_bytes()', '(HERE / "html_prep_rev6.py").read_bytes()'),
    ("leftover", 'files["html_complete.py"] = (PAPER / "revision5" / "html_complete.py").read_bytes()\n',
     'files["html_complete.py"] = (PAPER / "revision5" / "html_complete.py").read_bytes()\n    files["html_leftover.py"] = (PAPER / "revision6" / "html_leftover.py").read_bytes()\n'),
])
print("wrote build_payload_rev6.py, build_rev6.sh, html_prep_rev6.py")
