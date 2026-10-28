#!/bin/bash
# Lane ME-PAPER build sitting. The desk has no TeX, pandoc or matplotlib, so the pod does:
#   1. matplotlib figures from records/RESULTS-PAPER.json;
#   2. tectonic PDFs of main.tex (owner's author list) and main-arxiv.tex;
#   3. a self-contained HTML of main.tex via pandoc (citeproc, MathJax).
# Everything under $OUT is pulled before the release.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
OUT=${OUT:-$HERE/out}
mkdir -p "$OUT"
log() { echo "$(date -u +%H:%M:%SZ) $*" | tee -a "$OUT/BUILD-STEPS.txt"; }
( cd "$HERE" && sha256sum -c MANIFEST.sha256 > "$OUT/manifest-check.txt" 2>&1 ) || { log "PAYLOAD MANIFEST MISMATCH"; exit 3; }
PY=$(command -v python3 || command -v python)
$PY -m pip install --no-cache-dir matplotlib==3.9.2 pypandoc_binary==1.13 > "$OUT/pip.log" 2>&1 || { log "PIP FAILED"; tail -5 "$OUT/pip.log"; exit 4; }
$PY -m pip freeze > "$OUT/pip-freeze.txt" 2>&1
log "pip ok"
mkdir -p "$HERE/tex/figs"
$PY "$HERE/make_figures.py" --records "$HERE/records" --out "$HERE/tex/figs" > "$OUT/figures.txt" 2>&1 || { log "FIGURES FAILED"; tail -5 "$OUT/figures.txt"; }
log "figures: $(tr '\n' ' ' < "$OUT/figures.txt" | cut -c1-200)"
TV=0.15.0
curl -sS -L --retry 3 -o /tmp/tectonic.tgz "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40$TV/tectonic-$TV-x86_64-unknown-linux-musl.tar.gz" \
  && tar xzf /tmp/tectonic.tgz -C /tmp && log "tectonic $TV fetched ($(sha256sum /tmp/tectonic.tgz | cut -c1-16))" || log "TECTONIC FETCH FAILED"
cd "$HERE/tex"
for M in main main-arxiv; do
  /tmp/tectonic --keep-intermediates --keep-logs "$M.tex" > "$OUT/tectonic-$M.txt" 2>&1 && log "pdf $M ok" || { log "PDF $M FAILED"; tail -20 "$OUT/tectonic-$M.txt"; }
  cp -f "$M.pdf" "$M.log" "$M.bbl" "$OUT/" 2>/dev/null
done
grep -h "Warning\|undefined" "$OUT"/main.log 2>/dev/null | sort | uniq -c | sort -rn | head -40 > "$OUT/latex-warnings.txt"
# HTML: the owner's variant, with the author-variant switch resolved for pandoc
$PY "$HERE/html_prep.py" "$HERE/tex" > "$OUT/html-prep.txt" 2>&1
curl -sS -L --retry 3 -o "$HERE/tex/ieee.csl" https://raw.githubusercontent.com/citation-style-language/styles/master/ieee.csl || log "CSL FETCH FAILED"
PANDOC=$($PY -c "import pypandoc;print(pypandoc.get_pandoc_path())")
$PANDOC main-html.tex -f latex -t html5 -s --citeproc --bibliography=refs.bib --csl=ieee.csl --mathjax --embed-resources \
  --default-image-extension=png --resource-path=.:figs --toc --metadata title="Can memistor-class electrochemical weights train neural networks?" \
  -c "$HERE/html.css" -o "$OUT/main.html" > "$OUT/pandoc.txt" 2>&1 && log "html ok ($(wc -c < "$OUT/main.html") bytes)" || { log "HTML FAILED"; tail -10 "$OUT/pandoc.txt"; }
mkdir -p "$OUT/figs" && cp -f figs/* "$OUT/figs/" 2>/dev/null
log "done"
exit 0
