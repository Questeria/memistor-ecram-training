"""ME-REVISE-7: derive pod/build_payload_rev7.py, pod/build_rev7.sh and pod/html_prep_rev7.py from the _rev6 versions by named anchors.

    python -B pod/derive_build_rev7.py

html_prep_rev7.py: the HTML title block prints the owner's official name (the _rev6 file hard-coded the old author string).
build_rev7.sh, build_payload_rev7.py: the same steps as version 7, pointing at html_prep_rev7.py.  Version 8 adds no number macro.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = "Quest" + "eria"


def derive(src, dst, subs):
    t = src.read_bytes().decode("utf-8")
    for name, a, b in subs:
        assert t.count(a) == 1, (dst.name, name, t.count(a))
        t = t.replace(a, b)
    dst.write_bytes(t.encode("utf-8"))


derive(HERE / "html_prep_rev6.py", HERE / "html_prep_rev7.py", [
    ("author", '"author{%s and Claude (Anthropic)}\\n"' % OLD, '"author{Anthony DeMarco and Claude (Anthropic)}\\n"'),
])
derive(HERE / "build_rev6.sh", HERE / "build_rev7.sh", [
    ("head", "# Lane ME-REVISE-6 build (derived by pod/derive_build_rev6.py from build_rev5.sh; run on the desk in WSL Ubuntu).",
     "# Lane ME-REVISE-7 build (derived by pod/derive_build_rev7.py from build_rev6.sh; run on the desk in WSL Ubuntu)."),
])
derive(HERE / "build_payload_rev6.py", HERE / "build_payload_rev7.py", [
    ("runsh", '(HERE / "build_rev6.sh").read_bytes()', '(HERE / "build_rev7.sh").read_bytes()'),
    ("htmlprep", '(HERE / "html_prep_rev6.py").read_bytes()', '(HERE / "html_prep_rev7.py").read_bytes()'),
])
print("wrote build_payload_rev7.py, build_rev7.sh, html_prep_rev7.py")
