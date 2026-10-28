"""Check a built main.html for leftovers: unexpanded macros, unresolved citations or references, the variant switch.

    python -I html_check.py <main.html>
"""
import html
import re
import sys

t = open(sys.argv[1], encoding="utf-8").read()
body = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
body = re.sub(r"data:image[^\"]+", "IMG", body)
txt = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", body)).split())
BS = re.escape(chr(92))
checks = {"unexpanded R-macro": BS + r"R[A-Z]\w+", "raw cite": BS + r"cite", "raw ref": BS + r"ref\b",
          "pandoc unresolved cite": r"\[@|\?\?\?", "variant switch": r"ifdefined|arxivvariant", "fitbox": "fitbox"}
bad = 0
for k, p in checks.items():
    n = len(re.findall(p, txt))
    bad += n
    print(f"{k}: {n}", (re.findall(".{40}(?:" + p + ").{40}", txt)[:2] if n else ""))
print("images", t.count("<img"), "tables", t.count("<table"), "chars", len(txt))
i = txt.find("Simulator validation")
print(txt[i:i + 500])
sys.exit(1 if bad else 0)
