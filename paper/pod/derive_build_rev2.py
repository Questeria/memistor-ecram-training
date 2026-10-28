"""ME-REVISE-2: derive pod/build_payload_rev2.py and pod/build_rev2.sh from the _rev versions by named anchors.

    python -B pod/derive_build_rev2.py
build_payload_rev2.py: the lint also reads tex/numbers_rev2.tex and checks \\RX... macros, and fails on a bare macro name
(an RV/RX/RE... word without its backslash: review 2 found three in v2 that the lint could not see); it runs build_rev2.sh.
build_rev2.sh: after the PDFs, assembles build/arxiv-source.tar.gz from the explicit PUBLISHING.md list and compiles
main-arxiv.tex from that archive alone in an empty directory (review 2 finding 5).
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
t = (HERE / "build_payload_rev.py").read_bytes().decode("utf-8")
SUBS = [
    ("defined", '(TEX / "numbers_rev.tex").read_text("utf-8")))',
     '(TEX / "numbers_rev.tex").read_text("utf-8") + (TEX / "numbers_rev2.tex").read_text("utf-8")))'),
    ("macro_re", 'r"(R[A-Z][A-Za-z]*|RV[A-Za-z]+|nChecks|nFaults)\\b"', 'r"(R[A-Z][A-Za-z]*|RV[A-Za-z]+|RX[A-Za-z]+|nChecks|nFaults)\\b"'),
    ("bare", '        for m in re.findall(re.escape(BS) + r"input\\{([^}]+)\\}", t):\n',
     '        if not f.name.startswith("numbers"):\n'
     '            for m in re.findall(r"(?<![A-Za-z\\\\])(R(?:V[a-z]|V[A-Z][a-z]|X[A-Z][a-z]|E[A-Z][a-z])[A-Za-z]{2,})", t):\n'
     '                errs.append(f"{f.name}: bare macro name {m} (missing backslash)")\n'
     '        for m in re.findall(re.escape(BS) + r"input\\{([^}]+)\\}", t):\n'),
    ("runsh", '    files["run.sh"] = (HERE / "build_rev.sh").read_bytes()\n', '    files["run.sh"] = (HERE / "build_rev2.sh").read_bytes()\n'),
]
for name, a, b in SUBS:
    assert t.count(a) == 1, name
    t = t.replace(a, b)
(HERE / "build_payload_rev2.py").write_bytes(t.encode("utf-8"))

s = (HERE / "build_rev.sh").read_bytes().decode("utf-8")
a = 'grep -h "Warning\\|undefined" "$OUT"/main.log'
b = ('# REVISION 2: the arXiv source archive from the explicit list (PUBLISHING.md), compiled alone in an empty directory\n'
     'tar czf "$OUT/arxiv-source.tar.gz" main-arxiv.tex preamble.tex body.tex sec_*.tex app_*.tex numbers.tex numbers_rev.tex '
     'numbers_rev2.tex tables figs/*.pdf refs.bib main-arxiv.bbl && log "arxiv source archive $(tar tzf "$OUT/arxiv-source.tar.gz" | wc -l) files" '
     '|| log "ARXIV ARCHIVE FAILED"\n'
     'rm -rf /tmp/arxivtest && mkdir -p /tmp/arxivtest && tar xzf "$OUT/arxiv-source.tar.gz" -C /tmp/arxivtest '
     '&& ( cd /tmp/arxivtest && /tmp/tectonic --keep-logs main-arxiv.tex > "$OUT/tectonic-archive.txt" 2>&1 ); '
     '[ -f /tmp/arxivtest/main-arxiv.pdf ] && log "archive compiles alone ($(stat -c %s /tmp/arxivtest/main-arxiv.pdf) bytes)" '
     '&& cp -f /tmp/arxivtest/main-arxiv.log "$OUT/archive-main-arxiv.log" || log "ARCHIVE COMPILE FAILED"\n' + a)
assert s.count(a) == 1, "warnings anchor"
s = s.replace(a, b).replace("# Lane ME-REVISE build sitting (derived by pod/derive_build_rev.py from build.sh).",
                            "# Lane ME-REVISE-2 build sitting (derived by pod/derive_build_rev2.py from build_rev.sh).")
(HERE / "build_rev2.sh").write_bytes(s.encode("utf-8"))
print("wrote build_payload_rev2.py and build_rev2.sh")
