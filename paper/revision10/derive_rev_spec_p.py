"""Version 11 (review 8, finding 6): derive tables/rev_spec_p.tex, the paper's Table 12, from the generated tables/rev_spec.tex
exactly as revision4/edit_tex_4b.py did (one comment line; float placement [p] instead of [t]), so that reproduce_all.py
regenerates and byte-compares every table the paper prints.

    python -B revision10/derive_rev_spec_p.py         (from paper/, after revision/analyze_rev.py)
"""
from pathlib import Path

T = Path(__file__).resolve().parent.parent / "tex" / "tables"
HEAD = "\\begin{table*}[t]"
src = (T / "rev_spec.tex").read_bytes().decode("utf-8")
assert src.startswith(HEAD) and src.count(HEAD) == 1, "rev_spec.tex does not start with its one table* [t]"
out = ("% derived by revision4/edit_tex_4b.py from tables/rev_spec.tex: placement [p] instead of [t]\n"
       + "\\begin{table*}[p]" + src[len(HEAD):])
(T / "rev_spec_p.tex").write_bytes(out.encode("utf-8"))
print("wrote tables/rev_spec_p.tex from tables/rev_spec.tex")
