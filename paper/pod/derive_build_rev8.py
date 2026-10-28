"""ME-DEPOSIT-2: derive pod/build_payload_rev8.py and pod/build_rev8.sh from the _rev7 versions by named anchors.

    python -B pod/derive_build_rev8.py

The same steps as version 8, pointing at build_rev8.sh (html_prep_rev7.py is unchanged).  Version 9 regenerates tex/numbers_rev.tex first.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def derive(src, dst, subs):
    t = src.read_bytes().decode("utf-8")
    for name, a, b in subs:
        assert t.count(a) == 1, (dst.name, name, t.count(a))
        t = t.replace(a, b)
    dst.write_bytes(t.encode("utf-8"))


derive(HERE / "build_rev7.sh", HERE / "build_rev8.sh", [
    ("head", "# Lane ME-REVISE-7 build (derived by pod/derive_build_rev7.py from build_rev6.sh; run on the desk in WSL Ubuntu).",
     "# Lane ME-DEPOSIT-2 build (derived by pod/derive_build_rev8.py from build_rev7.sh; run on the desk in WSL Ubuntu)."),
])
derive(HERE / "build_payload_rev7.py", HERE / "build_payload_rev8.py", [
    ("runsh", '(HERE / "build_rev7.sh").read_bytes()', '(HERE / "build_rev8.sh").read_bytes()'),
])
print("wrote build_payload_rev8.py, build_rev8.sh")
