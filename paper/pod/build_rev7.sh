#!/bin/bash
# Lane ME-REVISE-7 build (derived by pod/derive_build_rev7.py from build_rev6.sh; run on the desk in WSL Ubuntu). The desk has no TeX, pandoc or matplotlib, so the pod does:
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
$PY "$HERE/make_figures_rev.py" --results "$HERE/records/revision/RESULTS-REVISION.json" --out "$HERE/tex/figs" > "$OUT/figures-rev.txt" 2>&1 || { log "REV FIGURE FAILED"; tail -5 "$OUT/figures-rev.txt"; }
log "rev figure: $(tail -1 "$OUT/figures-rev.txt")"
TV=0.15.0
curl -sS -L --retry 3 -o /tmp/tectonic.tgz "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40$TV/tectonic-$TV-x86_64-unknown-linux-musl.tar.gz" \
  && tar xzf /tmp/tectonic.tgz -C /tmp && log "tectonic $TV fetched ($(sha256sum /tmp/tectonic.tgz | cut -c1-16))" || log "TECTONIC FETCH FAILED"
cd "$HERE/tex"
for M in main main-arxiv; do
  /tmp/tectonic --keep-intermediates --keep-logs "$M.tex" > "$OUT/tectonic-$M.txt" 2>&1 && log "pdf $M ok" || { log "PDF $M FAILED"; tail -20 "$OUT/tectonic-$M.txt"; }
  cp -f "$M.pdf" "$M.log" "$M.bbl" "$M.aux" "$OUT/" 2>/dev/null
done
# REVISION 2: the arXiv source archive from the explicit list (PUBLISHING.md), compiled alone in an empty directory
tar czf "$OUT/arxiv-source.tar.gz" main-arxiv.tex preamble.tex body.tex sec_*.tex app_*.tex numbers.tex numbers_rev.tex numbers_rev2.tex numbers_rev3.tex numbers_rev4.tex tables figs/*.pdf refs.bib main-arxiv.bbl && log "arxiv source archive $(tar tzf "$OUT/arxiv-source.tar.gz" | wc -l) files" || log "ARXIV ARCHIVE FAILED"
rm -rf /tmp/arxivtest && mkdir -p /tmp/arxivtest && tar xzf "$OUT/arxiv-source.tar.gz" -C /tmp/arxivtest && ( cd /tmp/arxivtest && /tmp/tectonic --keep-logs main-arxiv.tex > "$OUT/tectonic-archive.txt" 2>&1 ); [ -f /tmp/arxivtest/main-arxiv.pdf ] && log "archive compiles alone ($(stat -c %s /tmp/arxivtest/main-arxiv.pdf) bytes)" && cp -f /tmp/arxivtest/main-arxiv.log "$OUT/archive-main-arxiv.log" || log "ARCHIVE COMPILE FAILED"
grep -h "Warning\|undefined" "$OUT"/main.log 2>/dev/null | sort | uniq -c | sort -rn | head -40 > "$OUT/latex-warnings.txt"
# HTML: the owner's variant, with the author-variant switch resolved for pandoc
$PY "$HERE/html_prep.py" "$HERE/tex" > "$OUT/html-prep.txt" 2>&1
curl -sS -L --retry 3 -o "$HERE/tex/ieee.csl" https://raw.githubusercontent.com/citation-style-language/styles/master/ieee.csl || log "CSL FETCH FAILED"
PANDOC=$($PY -c "import pypandoc;print(pypandoc.get_pandoc_path())")
$PANDOC main-html.tex -f latex -t html5 -s --citeproc --bibliography=refs.bib --csl=ieee.csl --mathjax --embed-resources \
  --default-image-extension=png --resource-path=.:figs --toc --metadata title="Can memistor-class electrochemical weights train neural networks?" \
  -c "$HERE/html.css" -o "$OUT/main.html" > "$OUT/pandoc.txt" 2>&1 && log "html ok ($(wc -c < "$OUT/main.html") bytes)" || { log "HTML FAILED"; tail -10 "$OUT/pandoc.txt"; }
$PY "$HERE/html_complete.py" "$HERE/tex" "$OUT/main.html" > "$OUT/html-complete.txt" 2>&1 && log "html complete: $(tr '\n' ' ' < "$OUT/html-complete.txt" | cut -c1-200)" || log "HTML INCOMPLETE: $(tr '\n' ' ' < "$OUT/html-complete.txt" | cut -c1-300)"
$PY "$HERE/html_leftover.py" "$OUT/main.html" > "$OUT/html-leftover.txt" 2>&1 && log "html leftover: $(tr '\n' ' ' < "$OUT/html-leftover.txt" | cut -c1-200)" || log "HTML LEFTOVER LATEX: $(tr '\n' ' ' < "$OUT/html-leftover.txt" | cut -c1-300)"
mkdir -p "$OUT/figs" && cp -f figs/* "$OUT/figs/" 2>/dev/null
log "done"
exit 0
