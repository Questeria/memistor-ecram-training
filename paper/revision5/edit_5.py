"""ME-REVISE-5: the version-6 edits to the LaTeX sources and PUBLISHING.md, by named anchors (each must occur exactly once).
Review 5 asked for no new experiment: version 6 repairs the HTML edition and makes two wording corrections.

    python -B revision5/edit_5.py
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
    ("v5-not-this", "Version 5 (October 27, 2026; this paper) answers a\nfourth review",
     "Version 5 (October 27, 2026) answers a\nfourth review"),
    ("deposit-and-v6",
     "The saved pulse draws joined the deposit with a\ncommand that rebuilds the probe tables from them, the probe table was split in two for legibility, and the abstract\n"
     "states that its probe count is a point-estimate count.\n",
     "The saved pulse draws were added to the deposit inventory with a\ncommand that rebuilds the probe tables from them, the probe table was split in two for legibility, and the abstract\n"
     "states that its probe count is a point-estimate count. Version 6 (October 27, 2026; this paper) answers a fifth review\n"
     "(one finding and two wording corrections; \\texttt{RESPONSE-TO-REVIEW-5.md}; no experiment was run and no number\n"
     "changed). The HTML edition of versions 4 and 5 was incomplete: it lacked Sections~\\ref{sec:energy}--\\ref{sec:availability}, the\n"
     "contribution and acknowledgment statements and two appendices, it printed the rows of the simulator-checks table under the\n"
     "sensitivity table's caption, and nine references were unresolved. The converter had read two adjacent tables with\n"
     "different column-width units as one and dropped everything between them. The conversion now rewrites paragraph-width\n"
     "columns, and a new check refuses any HTML that lacks a heading or a table's own rows or that holds an unresolved reference. The\n"
     "two wording corrections are in Section~\\ref{sec:fidelity} and Section~\\ref{sec:availability}.\n"),
])
edit(P / "tex" / "sec_fidelity.tex", [
    ("alone", "the draws are part of\nthe deposit, and Tables~\\ref{tab:rev4_probe_sur}--\\ref{tab:rev3_dep} can be rebuilt from them alone\n(Section~\\ref{sec:availability}).",
     "the draws are in\nthe deposit inventory, and Tables~\\ref{tab:rev4_probe_sur}--\\ref{tab:rev3_dep} can be rebuilt from them and the probe\nrecords' metadata (Section~\\ref{sec:availability})."),
])
edit(P / "tex" / "body.tex", [
    ("reviews", "\\texttt{RESPONSE-TO-REVIEW-3.md}, \\texttt{RESPONSE-TO-REVIEW-4.md});",
     "\\texttt{RESPONSE-TO-REVIEW-3.md}, \\texttt{RESPONSE-TO-REVIEW-4.md}, \\texttt{RESPONSE-TO-REVIEW-5.md});"),
    ("fourlabel", "the responses to the four\n      independent reviews", "the responses to the five\n      independent reviews"),
    ("metadata", "from which\n      \\texttt{revision4/rebuild\\_draw\\_tables.py} recomputes every statistic of",
     "from which, with the probe records' metadata (layer, clipping figures,\n      bootstrap counts), \\texttt{revision4/rebuild\\_draw\\_tables.py} recomputes every statistic of"),
])
edit(P / "PUBLISHING.md", [
    ("alone", "`rev4_probe_seq.tex`, `rev4_dep.tex`) from the arrays alone, and prints",
     "`rev4_probe_seq.tex`, `rev4_dep.tex`) from the saved arrays and the probe records' metadata (layer, clipping figures, bootstrap\n     counts), and prints"),
    ("builder", "`pod/build_rev3.sh` for version 4 and `pod/build_rev4.sh` for version 5, on the desk",
     "`pod/build_rev3.sh` for version 4, `pod/build_rev4.sh` for version 5 and `pod/build_rev5.sh` for version 6, on the desk"),
    ("checker", "`revision4/check_build_v5.py` checks the logs of all three compilations, the HTML, the revision numbers in the HTML and the\n   printed size of every table.",
     "`revision5/check_build_v6.py` runs `revision4/check_build_v5.py` (the logs of all three compilations, the HTML, the revision numbers in\n"
     "   the HTML, the printed size of every table) and adds `revision5/html_complete.py`: every section and subsection heading of the LaTeX\n"
     "   source is in the HTML in order, every table caption is followed by its own table's header and rows, and no `??`, `[?]`, raw\n"
     "   `[label]` or dead internal link remains. The HTML is made by pandoc 2.19.2 (pypandoc_binary 1.13) from `main-html.tex`, which\n"
     "   `pod/html_prep_rev5.py` writes: it also rewrites every `p{..}` tabular column to `l`, because that pandoc fuses a table with a\n"
     "   `p{..cm}` column and a later table with a `p{..\\linewidth}` column and drops what lies between them (`revision5/pandoc_repro.py`\n"
     "   reproduces it). The pandoc log stays empty in that failure: read the check, not the log."),
    ("abstract", "and `revision4/make_abstract_v5.py` (version 5) from", "and `revision4/make_abstract_v5.py` (versions 5 and 6) from"),
])
print("edited tex/app_revision.tex, sec_fidelity.tex, body.tex and PUBLISHING.md")
