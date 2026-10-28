"""ME-REVISE-5: is a built main.html a complete, faithful edition of the LaTeX source?  (review 5: version 5's HTML silently
lost Sections 5-9 and two appendices, put the checks table's rows under the sensitivity table's caption and left nine reference
labels unresolved, and no check noticed.)  Three checks, each independent of the converter's own pre-processing:

  1. headings: every \\section / \\subsection heading of the source (read from tex/ the same way the PDF reads it, owner variant)
     appears in the HTML as a heading, in the source's order;
  2. tables: every table environment's caption is in the HTML, in order, and the HTML table that carries it also carries
     that table's own header row and its first and last data rows, in that order, and no other source table's caption;
  3. references: the visible text holds no '??', no '[?]', no raw label such as [sec:energy], and every internal link
     (href="#x") has a target id.

    python -B revision5/html_complete.py <tex dir> <main.html> [--json out.json]     (exit 0 only if all three pass)
    python -B revision5/html_complete.py --selftest <tex dir> <good main.html>       (plants faults in a good HTML)
"""
import html as H
import json
import re
import sys

BS = chr(92)
WRAP = r"\\(?:texttt|emph|textbf|textit|textsc|textrm|mathrm|text|ensuremath)\b"


def flatten(texdir):
    """body.tex with every \\input inlined, comments dropped and the author-variant switch resolved to the owner's variant."""
    import os

    def inline(name, depth=0):
        p = os.path.join(texdir, name if name.endswith(".tex") else name + ".tex")
        t = open(p, "rb").read().decode("utf-8")
        t = re.sub(r"(?m)^%.*$", "", t)
        t = re.sub(r"(?m)(?<!\\)%.*$", "", t)
        if depth < 6:
            t = re.sub(r"\\input\{([^}]+)\}", lambda m: inline(m.group(1), depth + 1), t)
        return t

    t = inline("body")
    pat = r"\\ifdefined\\arxivvariant(.*?)\\else(.*?)\\fi"
    return re.sub(pat, lambda m: m.group(2), t, flags=re.S)


def braced(t, i):
    """text of the {...} group whose opening brace is at t[i]; returns (text, index after the closing brace)."""
    assert t[i] == "{"
    d, j = 0, i
    while j < len(t):
        c = t[j]
        if c == "\\":
            j += 2
            continue
        d += (c == "{") - (c == "}")
        j += 1
        if d == 0:
            return t[i + 1:j - 1], j
    return t[i + 1:], len(t)


def norm(s):
    """alphanumeric lower-case signature of LaTeX or HTML text: wrappers and TeX punctuation vanish, math and macro names stay
    the same on both sides (a MathJax span prints \\(\\gamma\\), the source $\\gamma$)."""
    s = re.sub(WRAP, "", s)
    s = H.unescape(s)
    return re.sub(r"[^a-z0-9]", "", s.lower())


def cut_sig(s, minlen=6):
    """signature of the leading plain part of a LaTeX cell/caption: up to the first number macro (\\R...), math or line break,
    whose expansion differs between the source and the HTML.  None if too short to identify anything."""
    s = re.split(r"\\R[A-Za-z]+|\$|\\\\|\\ref|\\cite|\\label", s)[0]
    sg = norm(s)
    return sg if len(sg) >= minlen else None


def source_headings(tex):
    out = []
    app = tex.find("\\appendix")
    for m in re.finditer(r"\\(section|subsection)(\*?)\{", tex):
        title, _ = braced(tex, m.end() - 1)
        plain = norm(title)
        if app >= 0 and m.start() > app and m.group(1) == "section" and not m.group(2):
            # the HTML edition letters the appendices as the PDF does (pandoc has no appendix counter)
            n = sum(1 for x in re.finditer(r"\\section\{", tex[app:m.start()]))
            title = "Appendix " + chr(ord("A") + n) + ": " + title
        out.append(dict(level=m.group(1), starred=bool(m.group(2)), title=re.sub(r"\s+", " ", title).strip(), sig=norm(title), plain=plain))
    return out


def html_text_blocks(t):
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    return re.sub(r"data:image[^\"')]+", "IMG", t)


def html_headings(t):
    t = re.sub(r"<nav .*?</nav>", "", html_text_blocks(t), flags=re.S)
    return [dict(level=int(m.group(1)), text=" ".join(H.unescape(re.sub(r"<[^>]+>", " ", m.group(3))).split()), sig=norm(re.sub(r"<[^>]+>", " ", m.group(3))))
            for m in re.finditer(r"<h([1-6])([^>]*)>(.*?)</h\1>", t, flags=re.S) if 'class="title"' not in m.group(2)]


def check_headings(tex, t):
    src, got = source_headings(tex), html_headings(t)
    pos, missing, k = [], [], 0
    for s in src:
        j = next((i for i in range(k, len(got)) if got[i]["sig"] in (s["sig"], s["plain"])), None)
        if j is None:
            missing.append(s["title"])
        else:
            pos.append(j)
            k = j + 1
    # a heading found only out of order is reported as out of order
    ooo = [s["title"] for s in src if s["title"] in missing and any(g["sig"] in (s["sig"], s["plain"]) for g in got)]
    return dict(n_source=len(src), n_html=len(got), missing=[m for m in missing if m not in ooo], out_of_order=ooo,
                ok=not missing)


def source_tables(tex):
    out = []
    for m in re.finditer(r"\\begin\{table\*?\}", tex):
        e = re.compile(r"\\end\{table\*?\}").search(tex, m.end())
        env = tex[m.end():e.start()]
        c = env.find("\\caption{")
        cap, _ = braced(env, c + len("\\caption")) if c >= 0 else ("", 0)
        rest = env.replace(cap, "", 1)
        # drop the column spec (first braced group) and trailing \end{tabular}
        body = rest[rest.find("\\begin{tabular}") + len("\\begin{tabular}"):] if "\\begin{tabular}" in rest else rest
        if body.startswith("{"):
            _, j = braced(body, 0)
            body = body[j:]
        body = re.sub(r"\\end\{tabular\}.*", "", body, flags=re.S)
        body = re.sub(r"\\(?:toprule|midrule|bottomrule|hline)\b", "\n", body)
        rows = [r.strip() for r in re.split(r"\\\\(?:\[[^\]]*\])?", body) if r.strip()]
        out.append(dict(caption=re.sub(r"\s+", " ", cap).strip(), csig=cut_sig(cap, 10), rows=rows))
    return out


def first_sig(row):
    """signature of the first identifiable cell of a source row (multicolumn cells count as their text; rules are dropped)."""
    row = re.sub(r"\\(?:cmidrule|cline)(?:\([^)]*\))?\{[^}]*\}", "", row)
    row = re.sub(r"\\(?:addlinespace|noalign)(?:\[[^\]]*\])?", "", row)
    row = re.sub(r"\\multicolumn\{[^}]*\}\{[^}]*\}\{", "{", row)
    for cell in row.split("&"):
        s = cut_sig(cell, 4)
        if s:
            return s
    return None


def html_tables(t):
    t = html_text_blocks(t)
    out = []
    for m in re.finditer(r"<table\b.*?</table>", t, flags=re.S):
        tb = m.group(0)
        cap = re.search(r"<caption>(.*?)</caption>", tb, flags=re.S)
        out.append(dict(pos=m.start(), caption=norm(re.sub(r"<[^>]+>", " ", cap.group(1))) if cap else "",
                        text=norm(re.sub(r"<[^>]+>", " ", tb[cap.end():] if cap else tb)),
                        rows=[norm(re.sub(r"<[^>]+>", " ", r)) for r in re.findall(r"<tr\b.*?</tr>", tb, flags=re.S)]))
    return out


def check_tables(tex, t):
    src, got = source_tables(tex), html_tables(t)
    res, last, bad = [], -1, []
    for i, s in enumerate(src):
        cand = [j for j, g in enumerate(got) if s["csig"] and s["csig"] in g["caption"]]
        r = dict(i=i, caption=s["caption"][:60], found=bool(cand))
        if not cand:
            bad.append(dict(table=s["caption"][:80], why="caption not in the HTML"))
            res.append(r)
            continue
        g = got[cand[0]]
        r["in_order"] = cand[0] > last
        if not r["in_order"]:
            bad.append(dict(table=s["caption"][:80], why="out of order"))
        last = max(last, cand[0])
        # the table's own rows: header row first cell, first and last data row, in order inside this HTML table
        hdr, first, lastrow = (first_sig(s["rows"][0]), first_sig(s["rows"][1]) if len(s["rows"]) > 1 else None,
                               first_sig(s["rows"][-1]) if len(s["rows"]) > 2 else None)
        at, ok = 0, True
        for name, sg in (("header", hdr), ("first row", first), ("last row", lastrow)):
            if sg is None:
                continue
            j = g["text"].find(sg, at)
            if j < 0:
                ok = False
                bad.append(dict(table=s["caption"][:80], why=name + " of the source table is not under its caption"))
                break
            at = j
        r["own_rows"] = ok
        # the HTML table must not carry another source table's caption signature
        r["n_rows_html"], r["n_rows_src"] = len(g["rows"]), len(s["rows"])
        res.append(r)
    return dict(n_source=len(src), n_html=len(got), problems=bad, ok=not bad)


def check_refs(t):
    t = html_text_blocks(t)
    txt = " ".join(H.unescape(re.sub(r"<[^>]+>", " ", t)).split())
    raw = sorted(set(re.findall(r"\[(?:[A-Za-z]+[:_][A-Za-z0-9_:\-]+)\]", txt)))
    qq = len(re.findall(r"\?\?", txt))
    qb = len(re.findall(r"\[\?\]", txt))
    ids = set(re.findall(r'\bid="([^"]+)"', t))
    dead = sorted({h for h in re.findall(r'href="#([^"]+)"', t) if h not in ids})
    numeric_app = sorted(set(re.findall(r"Appendix\s+\d+", txt)))   # the PDF letters its appendices; a number is pandoc's own counter
    return dict(raw_labels=raw, double_question=qq, bracket_question=qb, dead_internal_links=dead, numeric_appendix_refs=numeric_app,
                ok=not raw and not qq and not qb and not dead and not numeric_app)


def check(texdir, html_path):
    tex = flatten(texdir)
    t = open(html_path, encoding="utf-8").read()
    res = dict(headings=check_headings(tex, t), tables=check_tables(tex, t), references=check_refs(t))
    res["ok"] = all(v["ok"] for v in res.values())
    return res


def mutate(t, kind, tex):
    """Plant one fault in a good HTML."""
    t = t.replace("\r\n", "\n")
    if kind == "drop_section":
        i = t.find('<h1 id="sec:energy"')
        j = t.find("<h1", i + 5)
        return t[:i] + t[j:]
    if kind == "swap_sections":
        return swap(t, '<h1 id="sec:discussion"', '<h1 id="sec:roadmap"')
    if kind == "rows_under_wrong_caption":
        tabs = list(re.finditer(r"<table\b.*?</table>", t, flags=re.S))
        a, b = tabs[3], tabs[4]
        ca = re.search(r"<caption>.*?</caption>", a.group(0), flags=re.S)
        cb = re.search(r"<caption>.*?</caption>", b.group(0), flags=re.S)
        na = a.group(0).replace(ca.group(0), "\0A\0").replace("\0A\0", cb.group(0))
        return t[:a.start()] + na + t[a.end():]
    if kind == "raw_label":
        return inject(t, "[sec:energy] ")
    if kind == "double_question":
        return inject(t, "?? ")
    if kind == "bracket_question":
        return inject(t, "[?] ")
    if kind == "numeric_appendix":
        return inject(t, "Appendix 15 ")
    if kind == "dead_link":
        return t.replace("<a href=\"#sec:intro\"", "<a href=\"#sec:nowhere\"", 1)
    raise KeyError(kind)


def inject(t, s):
    """put s at the start of the first paragraph of the Introduction (the MathJax script embedded in the page holds <p> too)."""
    i = t.find('<h1 id="sec:intro"')
    j = t.find("<p>", i)
    return t[:j + 3] + s + t[j + 3:]


def swap(t, a, b):
    ia, ib = t.find(a), t.find(b)
    # move the block starting at b (one h1 block) in front of a
    jb = t.find("<h1", ib + 5)
    return t[:ia] + t[ib:jb] + t[ia:ib] + t[jb:]


def selftest(texdir, good):
    tex = flatten(texdir)
    t = open(good, encoding="utf-8").read()
    base = dict(headings=check_headings(tex, t), tables=check_tables(tex, t), references=check_refs(t))
    out = dict(good_passes=all(v["ok"] for v in base.values()))
    plan = [("drop_section", "headings"), ("swap_sections", "headings"), ("rows_under_wrong_caption", "tables"),
            ("raw_label", "references"), ("double_question", "references"), ("bracket_question", "references"),
            ("dead_link", "references"), ("numeric_appendix", "references")]
    for kind, part in plan:
        try:
            m = mutate(t, kind, tex)
            r = dict(headings=check_headings(tex, m), tables=check_tables(tex, m), references=check_refs(m))
            out[kind] = dict(caught_by=part, caught=not r[part]["ok"], others_ok=[k for k, v in r.items() if v["ok"]])
        except Exception as e:  # a planted fault that cannot be planted is a failed selftest
            out[kind] = dict(caught=False, error=repr(e))
    out["all_faults_caught"] = all(v["caught"] for k, v in out.items() if isinstance(v, dict))
    out["ok"] = out["good_passes"] and out["all_faults_caught"]
    return out


if __name__ == "__main__":
    a = [x for x in sys.argv[1:] if not x.startswith("--json")]
    if a and a[0] == "--selftest":
        r = selftest(a[1], a[2])
        print(json.dumps(r, indent=1))
        sys.exit(0 if r["ok"] else 1)
    r = check(a[0], a[1])
    if "--json" in sys.argv:
        jp = sys.argv[sys.argv.index("--json") + 1]
        open(jp, "wb").write((json.dumps(r, indent=1) + "\n").encode("utf-8"))
    print("headings", r["headings"]["ok"], "missing", len(r["headings"]["missing"]), "| tables", r["tables"]["ok"], "problems",
          len(r["tables"]["problems"]), "| references", r["references"]["ok"], "raw", r["references"]["raw_labels"], "dead",
          len(r["references"]["dead_internal_links"]), "|", "COMPLETE" if r["ok"] else "INCOMPLETE")
    sys.exit(0 if r["ok"] else 1)
