"""ME-REVISE-4: page fill and smallest printed text size per page of a PDF (review 4's presentation points: the blank area on
v4's page 20, the probe tables' print size). Runs in the WSL build venv (PyMuPDF).

    python3 page_fill.py <pdf> [<pdf> ...] > out.json
Per page: the fraction of the page height covered by text or images (union of block extents, top margin to bottom margin),
the largest vertical gap between consecutive blocks, and the smallest font size of any text span.
"""
import json
import sys

import fitz  # PyMuPDF

res = {}
for fn in sys.argv[1:]:
    doc = fitz.open(fn)
    pages = []
    for i, pg in enumerate(doc):
        h = pg.rect.height
        blocks = sorted((b[1], b[3]) for b in pg.get_text("blocks"))
        body = [b for b in blocks if b[0] > 0.06 * h and b[1] < 0.94 * h]  # drop running heads and page numbers
        sizes = [s["size"] for b in pg.get_text("dict")["blocks"] for ln in b.get("lines", []) for s in ln["spans"]
                 if s["text"].strip()]
        cov, gap, last = 0.0, 0.0, None
        for y0, y1 in body:
            if last is None:
                cov += y1 - y0
            else:
                gap = max(gap, y0 - last)
                cov += max(0.0, y1 - max(y0, last))
            last = y1 if last is None else max(last, y1)
        bottom_gap = (0.94 * h - last) if last is not None else 0.94 * h
        pages.append(dict(page=i + 1, cover=round(cov / (0.88 * h), 3), max_gap_frac=round(gap / h, 3),
                          bottom_blank_frac=round(bottom_gap / h, 3), min_font=round(min(sizes), 2) if sizes else None))
    res[fn] = pages
print(json.dumps(res))
