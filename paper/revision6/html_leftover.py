"""ME-REVISE-6: does a built main.html still show LaTeX that the converter should have consumed?  (review 6: version 6's Table 9
header read '(lr)2-6(lr)7-8 Seed' because pandoc 2.19.2 leaves \\cmidrule(lr){2-6} as text, and no check looked for it.)

The visible text of the page (scripts, styles and images dropped; MathJax math spans dropped, they hold LaTeX by design) must contain
  1. no 'cmidrule' or 'cline';
  2. no trim spec '(lr)', '(l)' or '(r)' followed by a column range such as 2-6 (a bare '(lr)' is legitimate: 'FP metric (lr)'
     means learning rate in the scale table);
  3. no raw backslash command, such as \\textbf or \\toprule.
Each hit is reported with the table it lies in (or None outside tables) and the text around it.

    python -B revision6/html_leftover.py <main.html> [--json out.json]        (exit 0 only if nothing is left over)
    python -B revision6/html_leftover.py --selftest <good main.html>           (plants faults in a good HTML)
"""
import html as H
import json
import re
import sys

BS = chr(92)
SCRIPT_STYLE = re.compile(r"<script.*?</script>|<style.*?</style>", re.S)
MATH = re.compile(r'<span class="math (?:inline|display)">.*?</span>', re.S)
PATTERNS = [
    ("cmidrule_or_cline", re.compile(r"cmidrule|cline")),
    ("trim_then_range", re.compile(r"\((?:lr|l|r)\)\s*\{?\s*\d+\s*-\s*\d+")),
    ("raw_command", re.compile(re.escape(BS) + r"[A-Za-z]+")),
]


def page_text_regions(t):
    """(table index or None, text) pieces: tables are cut out so each hit can name its table; tags become spaces."""
    t = SCRIPT_STYLE.sub("", t)
    t = re.sub(r"data:image[^\"')]+", "IMG", t)
    t = MATH.sub(" ", t)
    out, pos, k = [], 0, 0
    for m in re.finditer(r"<table\b.*?</table>", t, flags=re.S):
        out.append((None, t[pos:m.start()]))
        k += 1
        out.append((k, m.group(0)))
        pos = m.end()
    out.append((None, t[pos:]))
    return [(i, " ".join(H.unescape(re.sub(r"<[^>]+>", " ", s)).split())) for i, s in out], k


def find(t):
    regions, ntab = page_text_regions(t)
    hits = []
    for tab, txt in regions:
        for name, rx in PATTERNS:
            for m in rx.finditer(txt):
                hits.append(dict(kind=name, table=tab, text=txt[max(0, m.start() - 40):m.end() + 40]))
    return hits, ntab


def check(html_path):
    hits, ntab = find(open(html_path, encoding="utf-8").read())
    return dict(tables_scanned=ntab, n_hits=len(hits), hits=hits[:20], ok=not hits)


def mutate(t, kind):
    t = t.replace("\r\n", "\n")
    if kind == "table9_header_rule_args":
        # put the exact version-6 residue back into the first cell of Table 9's second header row
        u, n = re.subn(r"(<td[^>]*>)(\s*)Seed(\s*</td>)", lambda m: m.group(1) + "(lr)<span>2-6</span>(lr)<span>7-8</span>\nSeed" + m.group(3), t, count=1)
        assert n == 1, "Table 9's Seed cell not found"
        return u
    i = t.find('<h1 id="sec:intro"')
    j = t.find("<p>", i)
    add = dict(cmidrule_word=BS + "cmidrule(lr){2-6} ", bare_trim_range="(l)3-4 ", cline_word="cline ",
               raw_toprule=BS + "toprule ", raw_textbf=BS + "textbf{x} ")[kind]
    return t[:j + 3] + add + t[j + 3:]


def selftest(good):
    t = open(good, encoding="utf-8").read()
    base = find(t)[0]
    out = dict(good_passes=not base)
    for kind in ["table9_header_rule_args", "cmidrule_word", "bare_trim_range", "cline_word", "raw_toprule", "raw_textbf"]:
        try:
            m = mutate(t, kind)
            changed = m != t
            h, _ = find(m)
            out[kind] = dict(mutation_changed_page=changed, hits=len(h), caught=changed and len(h) > 0, table=[x["table"] for x in h][:1])
        except Exception as e:
            out[kind] = dict(caught=False, error=repr(e))
    # a bare '(lr)' without a range, and LaTeX inside a math span, must NOT be flagged
    i = t.find('<h1 id="sec:intro"')
    j = t.find("<p>", i)
    ok_page = t[:j + 3] + 'learning rate (lr) and <span class="math inline">' + BS + "(" + BS + "mathbf{x}" + BS + ")</span> " + t[j + 3:]
    n_ok = len(find(ok_page)[0])
    out["bare_lr_and_math_not_flagged"] = dict(hits=n_ok, caught=(n_ok == 0 and ok_page != t))
    out["all_faults_caught"] = all(v["caught"] for k, v in out.items() if isinstance(v, dict))
    out["ok"] = out["good_passes"] and out["all_faults_caught"]
    return out


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--json")]
    if a and a[0] == "--selftest":
        r = selftest(a[1])
        print(json.dumps(r, indent=1))
        sys.exit(0 if r["ok"] else 1)
    r = check(a[0])
    if "--json" in sys.argv:
        open(sys.argv[sys.argv.index("--json") + 1], "wb").write((json.dumps(r, indent=1) + "\n").encode("utf-8"))
    print("tables scanned", r["tables_scanned"], "| leftover hits", r["n_hits"], "|", "CLEAN" if r["ok"] else "LEFTOVER LATEX")
    for h in r["hits"][:5]:
        print("  ", h["kind"], "table", h["table"], repr(h["text"]))
    sys.exit(0 if r["ok"] else 1)
