"""ME-REVISE-6: verify review 6's one finding against version 6's own files before changing anything.

  P3: Table 9's HTML header carries '(lr)2-6(lr)7-8' before 'Seed'; the source is \\cmidrule(lr){2-6}\\cmidrule(lr){7-8}.
Also: which tables of the source use \\cmidrule or \\cline, which of those are in the version-6 body, and how many leftover
rule arguments the version-6 HTML shows in all.

    python -B revision6/verify_findings_6.py [--json records/revision6/VERIFY-FINDINGS-6.json]
"""
import json
import re
import sys
from pathlib import Path

P = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(P / "revision6"))
import html_leftover as HL  # noqa: E402

BS = chr(92)
html = (P / "build" / "v6" / "main.html").read_bytes().decode("utf-8")
lines = html.split("\n")
res = {}
res["html_line"] = next((i + 1 for i, l in enumerate(lines) if "(lr)<span>2-6</span>(lr)<span>7-8</span>" in l), None)
res["html_text"] = lines[res["html_line"] - 1] + " | " + lines[res["html_line"]] if res["html_line"] else None
src = {}
for f in sorted((P / "tex" / "tables").glob("*.tex")):
    t = f.read_bytes().decode("utf-8")
    n = len(re.findall(re.escape(BS) + r"(?:cmidrule|cline)\b", t))
    if n:
        src[f.name] = n
res["source_tables_with_rules"] = src
body = "".join((P / "tex" / n).read_bytes().decode("utf-8") for n in sorted(p.name for p in (P / "tex").glob("*.tex") if p.name.startswith(("body", "sec_", "app_"))))
res["inputted_in_v6_body"] = {k[:-4]: (BS + "input{tables/" + k in body) for k in src}
hits, ntab = HL.find(html)
res["v6_html_tables"] = ntab
res["v6_html_leftover_hits"] = [dict(kind=h["kind"], table=h["table"]) for h in hits]
res["finding_confirmed"] = bool(res["html_line"]) and len(hits) > 0
print(json.dumps(res, indent=1))
if "--json" in sys.argv:
    out = Path(sys.argv[sys.argv.index("--json") + 1])
    out = out if out.is_absolute() else P / out
    out.write_bytes((json.dumps(res, indent=1) + "\n").encode("utf-8"))
