"""ME-REVISE-6: the version-7 edits to the LaTeX sources and PUBLISHING.md, by named anchors (each must occur exactly once).
Review 6 asked for no new experiment: version 7 removes the table-rule commands that version 6's HTML printed as text.

    python -B revision6/edit_6.py
"""
from pathlib import Path

P = Path(__file__).resolve().parent.parent


def edit(path, subs):
    t = path.read_bytes().decode("utf-8")
    for name, a, b in subs:
        assert t.count(a) == 1, (path.name, name, t.count(a))
        t = t.replace(a, b)
    assert "\r\n" not in t
    path.write_bytes(t.encode("utf-8"))


edit(P / "tex" / "app_revision.tex", [
    ("v6-not-this", "Version 6 (October 27, 2026; this paper) answers a fifth review", "Version 6 (October 27, 2026) answers a fifth review"),
    ("v7",
     "two wording corrections are in Section~\\ref{sec:fidelity} and Section~\\ref{sec:availability}.\n",
     "two wording corrections are in Section~\\ref{sec:fidelity} and Section~\\ref{sec:availability}. Version 7 (October 27, 2026;\n"
     "this paper) answers a sixth review (one cosmetic finding; \\texttt{RESPONSE-TO-REVIEW-6.md}; no experiment was run, and no\n"
     "number or sentence of the PDF changed except this history). The HTML edition of version 6 printed the rule arguments\n"
     "as text before ``Seed'' in the header of Table~\\ref{tab:rev4_a2m}. The conversion now removes the table-rule\n"
     "commands, and the HTML check refuses any leftover rule argument or raw command.\n"),
])
edit(P / "tex" / "body.tex", [
    ("reviews", "\\texttt{RESPONSE-TO-REVIEW-4.md}, \\texttt{RESPONSE-TO-REVIEW-5.md});",
     "\\texttt{RESPONSE-TO-REVIEW-4.md}, \\texttt{RESPONSE-TO-REVIEW-5.md}, \\texttt{RESPONSE-TO-REVIEW-6.md});"),
    ("fivelabel", "the responses to the five\n      independent reviews", "the responses to the six\n      independent reviews"),
])
edit(P / "PUBLISHING.md", [
    ("builder", "`pod/build_rev4.sh` for version 5 and `pod/build_rev5.sh` for version 6, on the desk",
     "`pod/build_rev4.sh` for version 5, `pod/build_rev5.sh` for version 6 and `pod/build_rev6.sh` for version 7, on the desk"),
    ("checker", "`revision5/check_build_v6.py` runs `revision4/check_build_v5.py`",
     "`revision6/check_build_v7.py` runs `revision5/check_build_v6.py` and adds `revision6/html_leftover.py` (no `cmidrule`, no `(lr)2-6`-style\n"
     "   rule argument and no raw `\\command` outside the math spans in the HTML text; `pod/html_prep_rev6.py` removes `\\cmidrule` and `\\cline`\n"
     "   before pandoc). `revision5/check_build_v6.py` runs `revision4/check_build_v5.py`"),
])
print("edited")
