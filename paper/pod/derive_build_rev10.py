"""Version 15: derive pod/build_payload_rev10.py and pod/build_rev10.sh from the _rev9 versions by named anchors.

    python -B pod/derive_build_rev10.py

The same steps as version 14; Figure 1 is now drawn by revision14/make_fig_arch.py (the selected reset and chopper settings,
review 12), which the payload carries as make_fig_arch.py.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def derive(src, dst, subs):
    t = src.read_bytes().decode("utf-8")
    for name, a, b in subs:
        assert t.count(a) == 1, (dst.name, name, t.count(a))
        t = t.replace(a, b)
    dst.write_bytes(t.encode("utf-8"))


derive(HERE / "build_rev9.sh", HERE / "build_rev10.sh", [
    ("head", "# Version 14 build (derived by pod/derive_build_rev9.py from build_rev8.sh; run on the desk in WSL Ubuntu).",
     "# Version 15 build (derived by pod/derive_build_rev10.py from build_rev9.sh; run on the desk in WSL Ubuntu)."),
])
derive(HERE / "build_payload_rev9.py", HERE / "build_payload_rev10.py", [
    ("runsh", '(HERE / "build_rev9.sh").read_bytes()', '(HERE / "build_rev10.sh").read_bytes()'),
    ("fig_arch", '(PAPER / "revision13" / "make_fig_arch.py").read_bytes()', '(PAPER / "revision14" / "make_fig_arch.py").read_bytes()'),
])
print("wrote build_payload_rev10.py, build_rev10.sh")
