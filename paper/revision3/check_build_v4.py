"""ME-REVISE-3: check a v4 build output directory (LaTeX logs of main, main-arxiv and the archive compiled alone, the HTML).

    python -B revision3/check_build_v4.py <out dir> [--json records/revision3/ARTIFACT-CHECK-v4.json]

Fails (exit 1) on: an undefined reference or citation, a multiply defined label, an overfull box wider than 2 pt, a missing
PDF, or an HTML leftover reported by pod/html_check.py. The planted-fault self-test runs the same parser on a log with each
fault inserted and requires it to be caught.
"""
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)


def scan(log):
    pages = re.findall(r"Output written on \S+ \((\d+) pages", log)
    over = [float(x) for x in re.findall(r"Overfull \\[hv]box \(([\d.]+)pt too", log)]
    return dict(pages=int(pages[-1]) if pages else None,
                undefined=len(re.findall(r"(?:Reference|Citation) [`'][^']*' on page \d+ undefined", log))
                + len(re.findall(r"There were undefined references", log)),
                multiply=len(re.findall(r"multiply defined", log)),
                overfull_over_2pt=[x for x in over if x > 2.0], overfull_max=max(over) if over else 0.0)


def bad(s):
    return s["pages"] is None or s["undefined"] or s["multiply"] or s["overfull_over_2pt"]


def selftest():
    base = "Output written on main.xdv (38 pages, 1 bytes).\n"
    faults = {"undefined ref": base + "LaTeX Warning: Reference `tab:x' on page 3 undefined on input line 9.\n",
              "undefined cite": base + "LaTeX Warning: Citation `foo' on page 3 undefined on input line 9.\n",
              "overfull": base + "Overfull \\hbox (12.5pt too wide) in paragraph at lines 1--2\n",
              "no pdf": "nothing\n"}
    return dict(clean_passes=not bad(scan(base)), faults_caught={k: bool(bad(scan(v))) for k, v in faults.items()})


def html_numbers(html_path, abstract_txt):
    """The digits of the HTML abstract must equal those of the generated arXiv abstract (macros expanded): pandoc drops an
    undefined macro silently, which removed every revision number from the v2 and v3 HTML."""
    import html as H
    t = open(html_path, encoding="utf-8").read()
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    x = " ".join(H.unescape(re.sub(r"<[^>]+>", " ", t)).split())
    a = open(abstract_txt, encoding="utf-8").read().strip()
    i = x.find(a[:40])
    j = x.find(a[-40:], i)
    seg = x[i:j + 40] if i >= 0 and j >= 0 else ""
    da, dh = re.findall(r"\d", a), re.findall(r"\d", seg)
    return dict(found=bool(seg), digits_abstract=len(da), digits_html=len(dh), ok=bool(seg) and da == dh)


def main():
    out = sys.argv[1]
    res = dict(selftest=selftest(), logs={})
    ab = os.path.join(P, "build", "arxiv-abstract.txt")
    res["html_numbers"] = html_numbers(os.path.join(out, "main.html"), ab)
    res["html_numbers_fault_v3_html"] = html_numbers(os.path.join(P, "build", "v3", "main.html"),
                                                     os.path.join(P, "build", "v3", "arxiv-abstract.txt"))
    for n in ("main.log", "main-arxiv.log", "archive-main-arxiv.log"):
        p = os.path.join(out, n)
        res["logs"][n] = scan(open(p, "rb").read().decode("latin-1")) if os.path.exists(p) else None
    pdfs = {}
    for n in ("main.pdf", "main-arxiv.pdf", "arxiv-source.tar.gz", "main.html"):
        p = os.path.join(out, n)
        pdfs[n] = dict(bytes=os.path.getsize(p), sha256=hashlib.sha256(open(p, "rb").read()).hexdigest()) if os.path.exists(p) else None
    res["artifacts"] = pdfs
    hc = subprocess.run([sys.executable, "-B", os.path.join(P, "pod", "html_check.py"), os.path.join(out, "main.html")],
                        capture_output=True, text=True)
    res["html_check"] = dict(rc=hc.returncode, out=hc.stdout.strip()[-400:])
    st = res["selftest"]
    ok = (st["clean_passes"] and all(st["faults_caught"].values()) and all(v and not bad(v) for v in res["logs"].values())
          and all(pdfs.values()) and hc.returncode == 0 and res["html_numbers"]["ok"]
          and not res["html_numbers_fault_v3_html"]["ok"])
    res["all_ok"] = ok
    if "--json" in sys.argv:
        jp = sys.argv[sys.argv.index("--json") + 1]
        open(jp, "wb").write((json.dumps(res, indent=1) + "\n").encode("utf-8"))
    print(json.dumps({k: res["logs"][k] for k in res["logs"]}), "html rc", hc.returncode, "html numbers", res["html_numbers"],
          "v3 fault", res["html_numbers_fault_v3_html"], "selftest", st, "ALL_OK" if ok else "NOT_OK")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
