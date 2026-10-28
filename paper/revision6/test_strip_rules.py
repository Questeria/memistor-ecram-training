"""ME-REVISE-6: the HTML prep's strip_rules removes every \\cmidrule / \\cline form and nothing else, and the test fails on a
broken remover (one that ignores the optional trim spec, as a naive pattern would).

    python -B revision6/test_strip_rules.py          -> prints each case and ALL_OK
"""
import ast
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BS = chr(92)
src = (HERE.parent / "pod" / "html_prep_rev6.py").read_text(encoding="utf-8")
tree = ast.parse(src)
ns = {"re": re, "BS": BS}
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name == "strip_rules":
        exec(compile(ast.Module([node], []), "strip_rules", "exec"), ns)
    if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "RULE_RE" for t in node.targets):
        exec(compile(ast.Module([node], []), "RULE_RE", "exec"), ns)
good = ns["strip_rules"]


def broken(t):
    """a remover that forgets the optional (trim) argument"""
    return re.subn(re.escape(BS) + r"cmidrule\s*\{[^}]*\}", "", t)


CASES = [
    (BS + r"cmidrule(lr){2-6}" + BS + r"cmidrule(lr){7-8} Seed & FP", " Seed & FP", 2),
    (BS + r"cmidrule{1-2} A", " A", 1),
    (BS + r"cmidrule[0.5pt](l){3-4} B", " B", 1),
    (BS + r"cmidrule(r){3-4}" + BS + r"cline{2-3} C", " C", 2),
    (BS + r"cline{2-3} D", " D", 1),
    (BS + r"multicolumn{2}{c}{x} " + BS + r"midrule E", BS + r"multicolumn{2}{c}{x} " + BS + r"midrule E", 0),
    ("FP metric (lr) & Li", "FP metric (lr) & Li", 0),
    (BS + r"toprule \multicolumn{5}{c}{P2200}\\" + BS + r"cmidrule(lr){2-6} Seed", BS + r"toprule \multicolumn{5}{c}{P2200}\\ Seed", 1),
]
ok = True
for inp, want, n in CASES:
    got, k = good(inp)
    good_ok = (got == want and k == n)
    b, _ = broken(inp)
    broken_fails = (b != want)
    print("case", "OK " if good_ok else "BAD", "| broken remover differs from expected:", broken_fails, "|", repr(inp[:50]))
    ok &= good_ok
# the broken remover must fail at least on the trim-spec cases (otherwise the test proves nothing)
trim_cases = [c for c in CASES if "(" in c[0] and "cmidrule(" in c[0]]
assert trim_cases and all(broken(c[0])[0] != c[1] for c in trim_cases), "test does not fail on the broken remover"
print("ALL_OK" if ok else "NOT_OK")
sys.exit(0 if ok else 1)
