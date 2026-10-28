"""ME-REVISE-5: derive pod/build_payload_rev5.py, pod/build_rev5.sh and pod/html_prep_rev5.py from the _rev4 versions by named anchors.

    python -B pod/derive_build_rev5.py

html_prep_rev5.py: after the flattening, every tabular's column specification has its p{..} columns rewritten to l.  Reason
(revision5/pandoc_repro.py): pandoc 2.19.2 (pypandoc_binary 1.13) reads a tabular with an absolute-length p{..cm} column followed
later by a tabular with a p{..\\linewidth} column as one table and silently drops the rows, the text and the section headings
between them (version 5's HTML lost Sections 5-9, two appendices, the statements, and put the checks table's rows under the
sensitivity table's caption).  build_rev5.sh: after pandoc it runs html_complete.py (revision5) and logs COMPLETE or INCOMPLETE.
build_payload_rev5.py: packs build_rev5.sh, html_prep_rev5.py and html_complete.py.  Version 6 adds no number macro.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def derive(src, dst, subs):
    t = src.read_bytes().decode("utf-8")
    for name, a, b in subs:
        assert t.count(a) == 1, (dst.name, name, t.count(a))
        t = t.replace(a, b)
    dst.write_bytes(t.encode("utf-8"))


APPX = r'''
def letter_appendices(t):
    """pandoc does not know the appendix command: its references read 'Appendix 15' where the PDF says 'Appendix F'. Every numbered
    section after it becomes 'Appendix X: title' and every ref to an app: label becomes its letter."""
    i = t.find(BS + "appendix")
    if i < 0:
        return t, 0
    head, tail = t[:i], t[i + len(BS + "appendix"):]
    out, pos, n, letters = [], 0, 0, {}
    key = BS + "section{"
    while True:
        j = tail.find(key, pos)
        if j < 0:
            out.append(tail[pos:])
            break
        k = j + len(key) - 1
        d, m = 0, k
        while True:
            c = tail[m]
            if c == BS:
                m += 2
                continue
            d += (c == "{") - (c == "}")
            m += 1
            if d == 0:
                break
        letter = chr(ord("A") + n)
        n += 1
        out.append(tail[pos:j] + key + "Appendix " + letter + ": " + tail[k + 1:m - 1] + "}")
        lab = re.match(r"\s*" + re.escape(BS) + r"label\{(app:[^}]+)\}", tail[m:])
        if lab:
            letters[lab.group(1)] = letter
        pos = m
    allt = head + "".join(out)
    allt = re.sub(re.escape(BS) + r"ref\{(app:[^}]+)\}", lambda mm: letters[mm.group(1)], allt)
    return allt, n


'''

PCOLS = r'''
def rewrite_pcols(t):
    """Every \\begin{tabular}{SPEC}: p{...} columns of SPEC become l (pandoc 2.19.2 fuses a p{..cm} table with a later
    p{..\\linewidth} table and drops what lies between them; see revision5/pandoc_repro.py)."""
    key = BS + "begin{tabular}{"
    out, i, n = [], 0, 0
    while True:
        j = t.find(key, i)
        if j < 0:
            out.append(t[i:])
            break
        k = j + len(key) - 1
        d, m = 0, k
        while True:
            c = t[m]
            if c == BS:
                m += 2
                continue
            d += (c == "{") - (c == "}")
            m += 1
            if d == 0:
                break
        spec = t[k + 1:m - 1]
        new, depth, p = [], 0, 0
        s = 0
        res = ""
        while s < len(spec):
            if spec[s] == "p" and s + 1 < len(spec) and spec[s + 1] == "{":
                e, dd = s + 1, 0
                while True:
                    dd += (spec[e] == "{") - (spec[e] == "}")
                    e += 1
                    if dd == 0:
                        break
                res += "l"
                n += 1
                s = e
            else:
                res += spec[s]
                s += 1
        out.append(t[i:k + 1] + res + "}")
        i = m
    return "".join(out), n


'''

derive(HERE / "html_prep_rev4.py", HERE / "html_prep_rev5.py", [
    ("def", "body = inline(\"body\")\n", PCOLS.lstrip("\n") + APPX.lstrip("\n") + "body = inline(\"body\")\n"),
    ("apply", 'body = body.replace("table*", "table")  # pandoc keeps the labels of plain table environments only\n',
     'body = body.replace("table*", "table")  # pandoc keeps the labels of plain table environments only\n'
     'body, npcols = rewrite_pcols(body)\nprint("p-columns rewritten to l:", npcols)\n'
     'body, napp = letter_appendices(body)\nprint("appendices lettered:", napp)\n'),
])
derive(HERE / "build_rev4.sh", HERE / "build_rev5.sh", [
    ("head", "# Lane ME-REVISE-4 build (derived by pod/derive_build_rev4.py from build_rev3.sh; run on the desk in WSL Ubuntu).",
     "# Lane ME-REVISE-5 build (derived by pod/derive_build_rev5.py from build_rev4.sh; run on the desk in WSL Ubuntu)."),
    ("complete", 'mkdir -p "$OUT/figs" && cp -f figs/* "$OUT/figs/" 2>/dev/null\n',
     '$PY "$HERE/html_complete.py" "$HERE/tex" "$OUT/main.html" > "$OUT/html-complete.txt" 2>&1 && log "html complete: $(tr \'\\n\' \' \' < "$OUT/html-complete.txt" | cut -c1-200)" || log "HTML INCOMPLETE: $(tr \'\\n\' \' \' < "$OUT/html-complete.txt" | cut -c1-300)"\n'
     'mkdir -p "$OUT/figs" && cp -f figs/* "$OUT/figs/" 2>/dev/null\n'),
])
derive(HERE / "build_payload_rev4.py", HERE / "build_payload_rev5.py", [
    ("runsh", '(HERE / "build_rev4.sh").read_bytes()', '(HERE / "build_rev5.sh").read_bytes()'),
    ("htmlprep", '(HERE / "html_prep_rev4.py").read_bytes()', '(HERE / "html_prep_rev5.py").read_bytes()'),
    ("complete", 'files["html.css"] = (HERE / "html.css").read_bytes()\n',
     'files["html.css"] = (HERE / "html.css").read_bytes()\n    files["html_complete.py"] = (PAPER / "revision5" / "html_complete.py").read_bytes()\n'),
])
print("wrote build_payload_rev5.py, build_rev5.sh, html_prep_rev5.py")
