"""Version 14: derive pod/build_payload_rev9.py and pod/build_rev9.sh from the _rev8 versions by named anchors.

    python -B pod/derive_build_rev9.py

The same steps as versions 9 to 13, plus Figure 1 (fig_arch): the payload carries revision13/make_fig_arch.py as make_fig_arch.py,
and the build draws it beside the other figures (it reads no record; it draws the tables in the script).
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def derive(src, dst, subs):
    t = src.read_bytes().decode("utf-8")
    for name, a, b in subs:
        assert t.count(a) == 1, (dst.name, name, t.count(a))
        t = t.replace(a, b)
    dst.write_bytes(t.encode("utf-8"))


derive(HERE / "build_rev8.sh", HERE / "build_rev9.sh", [
    ("head", "# Lane ME-DEPOSIT-2 build (derived by pod/derive_build_rev8.py from build_rev7.sh; run on the desk in WSL Ubuntu).",
     "# Version 14 build (derived by pod/derive_build_rev9.py from build_rev8.sh; run on the desk in WSL Ubuntu)."),
    ("fig_arch", 'log "rev figure: $(tail -1 "$OUT/figures-rev.txt")"\n',
     'log "rev figure: $(tail -1 "$OUT/figures-rev.txt")"\n'
     '$PY "$HERE/make_fig_arch.py" --out "$HERE/tex/figs" > "$OUT/figures-arch.txt" 2>&1 || { log "ARCH FIGURE FAILED"; tail -5 "$OUT/figures-arch.txt"; }\n'
     'log "arch figure: $(tail -1 "$OUT/figures-arch.txt")"\n'),
])
derive(HERE / "build_payload_rev8.py", HERE / "build_payload_rev9.py", [
    ("runsh", '(HERE / "build_rev8.sh").read_bytes()', '(HERE / "build_rev9.sh").read_bytes()'),
    ("fig_arch", '    files["make_figures_rev.py"] = (PAPER / "revision" / "make_figures_rev.py").read_bytes()\n',
     '    files["make_figures_rev.py"] = (PAPER / "revision" / "make_figures_rev.py").read_bytes()\n'
     '    files["make_fig_arch.py"] = (PAPER / "revision13" / "make_fig_arch.py").read_bytes()\n'),
])
print("wrote build_payload_rev9.py, build_rev9.sh")
