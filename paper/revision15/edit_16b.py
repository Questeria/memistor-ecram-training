r"""Version 16, second text pass (the owner's "fix anything stale", 2026-11-01), after revision15/edit_16.py:
  1. sec_abstract.tex: "This version repairs the simulator after independent reviews and reports how far each repair moved the
     original results." was stale in every version after the first (the paper is not "this version" of a repair); it now reads "The
     simulator was repaired after independent reviews, and the paper reports how far each repair moved the original results.";
  2. app_revision.tex: the version-16 entry says so.
Same anchor rule as edit_16.py.

    python -I -B revision15/edit_16b.py
"""
import re
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "tex"
EDITS = {
    "sec_abstract.tex": [
        ("abstract", r"This version repairs the simulator after independent reviews and reports how far each repair moved the original results.",
         r"The simulator was repaired after independent reviews, and the paper reports how far each repair moved the original results.", 1),
    ],
    "app_revision.tex": [
        ("v16 abstract", r"instead of versions 1 to 7. The review's one optional finding",
         r"instead of versions 1 to 7, and the abstract no longer says that this version repairs the simulator. The review's one optional finding", 1),
    ],
}
out = []
for name, subs in EDITS.items():
    p = TEX / name
    t = p.read_bytes().decode("utf-8")
    for tag, a, b, want in subs:
        pat = r"\s+".join(re.escape(w) for w in a.split())
        n = len(re.findall(pat, t))
        assert n == want, (name, tag, n, want)
        t = re.sub(pat, lambda m: b, t)
    out.append((p, t))
for p, t in out:
    p.write_bytes(t.encode("utf-8"))
print("edited", ", ".join(p.name for p, _ in out))
