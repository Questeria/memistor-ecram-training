"""REVISION: every \\RV... macro used in tex/*.tex is defined in tex/numbers_rev.tex (and no \\R... v1 macro is missing from
tex/numbers.tex). Prints the missing names; exit 1 if any.

    python -B revision/check_macros.py
"""
import os
import re
import sys

T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tex")
defs = set()
for f in ("numbers.tex", "numbers_rev.tex"):
    p = os.path.join(T, f)
    if os.path.exists(p):
        defs |= set(re.findall(r"\\newcommand\{\\([A-Za-z]+)\}", open(p, "rb").read().decode("utf-8")))
used = {}
for f in sorted(os.listdir(T)) + ["tables/" + x for x in sorted(os.listdir(os.path.join(T, "tables")))]:
    if not f.endswith(".tex") or f.startswith("numbers"):
        continue
    for m in re.findall(r"\\(R[A-Z][A-Za-z]*|RV[A-Za-z]+|nChecks|nFaults)\b", open(os.path.join(T, f), "rb").read().decode("utf-8")):
        used.setdefault(m, set()).add(f)
missing = {m: sorted(fs) for m, fs in used.items() if m not in defs}
for m, fs in sorted(missing.items()):
    print("MISSING", m, fs)
print(f"{len(used)} macros used, {len(missing)} missing")
sys.exit(1 if missing else 0)
