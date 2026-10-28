"""ME-REVISE-3: derive revision3/make_abstract_v4.py from revision2/make_abstract.py by named anchors: it also expands the
RY macros of tex/numbers_rev3.tex and refuses the phrases withdrawn after review 3."""
from pathlib import Path

H = Path(__file__).resolve().parent
s = (H.parent / "revision2" / "make_abstract.py").read_bytes().decode("utf-8")
SUBS = [("files", '("numbers.tex", "numbers_rev.tex", "numbers_rev2.tex")', '("numbers.tex", "numbers_rev.tex", "numbers_rev2.tex", "numbers_rev3.tex")'),
        ("withdrawn", '"no growth of the gap with width"]',
         '"no growth of the gap with width", "sub-margin growth", "preserves the ranking", "valid reference"]'),
        ("doc", "ME-REVISE-2: build/arxiv-abstract.txt", "ME-REVISE-3 (derived by revision3/derive_make_abstract_v4.py): build/arxiv-abstract.txt")]
for n, a, b in SUBS:
    assert s.count(a) == 1, n
    s = s.replace(a, b)
(H / "make_abstract_v4.py").write_bytes(s.encode("utf-8"))
print("wrote make_abstract_v4.py")
