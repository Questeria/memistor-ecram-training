"""Verify every reference of the paper against Crossref (DOI), the arXiv API (arXiv id) or the live URL (reports, data and
web documents without a DOI), and write tex/refs.bib FROM the fetched metadata plus records/CITE-CHECK.json.

    python -I cite/cite_check.py            (network: api.crossref.org, export.arxiv.org, the listed URLs)

Each entry: key, kind (doi | arxiv | url), id, expect (a few title words that must appear in the fetched title), and for url
entries the bibliographic fields we state (the check records the HTTP status and the fetched page title).
"""
import html
import json
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
UA = "altone-paper-citecheck/1 (research; contact via repository)"

REFS = [
    # history
    ("widrow1960adaline", "url", "https://isl.stanford.edu/~widrow/papers/t1960anadaptive.pdf", "%PDF",
     dict(type="techreport", author="Widrow, Bernard", title="An adaptive ``{ADALINE}'' neuron using chemical ``memistors''",
          institution="Stanford Electronics Laboratories, Stanford University", number="1553-2", year="1960",
          note="Scanned copy at https://isl.stanford.edu/~widrow/papers/t1960anadaptive.pdf (image only; title not machine-checked)")),
    ("widrow1960switching", "doi", "10.21236/ad0241531", "adaptive switching circuits", None),
    ("widrow1990", "doi", "10.1109/5.58323", "30 years of adaptive neural networks", None),
    ("mouttet2010", "arxiv", "1012.5124", "3-terminal devices", None),
    ("chua1971", "doi", "10.1109/TCT.1971.1083337", "memristor", None),
    ("strukov2008", "doi", "10.1038/nature06932", "missing memristor", None),
    ("gaines1967", "doi", "10.1145/1465482.1465505", "stochastic computing", None),
    ("rumelhart1986", "doi", "10.1038/323533a0", "back-propagating errors", None),
    # analog training algorithms and requirements
    ("gokmen2016", "doi", "10.3389/fnins.2016.00333", "resistive cross-point", None),
    ("gokmen2017cnn", "doi", "10.3389/fnins.2017.00538", "convolutional neural networks", None),
    ("agarwal2016", "doi", "10.1109/IJCNN.2016.7727298", "resistive memory device requirements", None),
    ("gokmen2020", "doi", "10.3389/fnins.2020.00103", "resistive device arrays", None),
    ("gokmen2021", "doi", "10.3389/frai.2021.699148", "noisy hardware", None),
    ("rasch2024", "doi", "10.1038/s41467-024-51221-z", "fast and robust analog", None),
    ("rasch2023arxiv", "arxiv", "2303.04721", "offset corrected in-memory training", None),
    ("rasch2021aihwkit", "doi", "10.1109/AICAS51828.2021.9458494", "pytorch toolkit", None),
    ("nandakumar2020", "doi", "10.3389/fnins.2020.00406", "mixed-precision", None),
    ("wu2025", "arxiv", "2502.06309", "non-ideal resistive elements", None),
    ("wu2026scale", "arxiv", "2609.36584", "making analog training scale", None),  # REVISION: the review's related work
    ("haensch2019", "doi", "10.1109/JPROC.2018.2871057", "analog computing", None),
    # devices
    ("tang2018", "doi", "10.1109/IEDM.2018.8614551", "ecram", None),
    ("kim2019", "doi", "10.1109/IEDM19573.2019.8993463", "ecram", None),
    ("onen2022", "doi", "10.1126/science.abp8064", "protonic programmable resistors", None),
    ("chen2023", "doi", "10.1038/s41467-023-41958-4", "electrochemical memory array", None),
    ("xu2026", "doi", "10.1021/acsnano.6c09861", "protonic electrochemical", None),
    ("li2021ecram", "doi", "10.3389/fnins.2021.636127", "electrochemical random-access memory", None),
    ("fuller2017", "doi", "10.1002/adma.201604310", "synaptic transistor", None),
    ("fuller2019", "doi", "10.1126/science.aaw5581", "ionic floating-gate", None),
    ("vandeburgt2017", "doi", "10.1038/nmat4856", "artificial synapse", None),
    ("burr2017", "doi", "10.1080/23746149.2016.1259585", "neuromorphic computing", None),
    ("sebastian2020", "doi", "10.1038/s41565-020-0655-z", "in-memory computing", None),
    ("ielmini2018", "doi", "10.1038/s41928-018-0092-2", "in-memory computing", None),
    ("prezioso2015", "doi", "10.1038/nature14441", "metal-oxide memristors", None),
    ("ambrogio2018", "doi", "10.1038/s41586-018-0180-5", "analogue memory", None),
    ("yao2020", "doi", "10.1038/s41586-020-1942-4", "memristor convolutional", None),
    ("wan2022", "doi", "10.1038/s41586-022-04992-8", "compute-in-memory chip", None),
    ("ambrogio2023", "doi", "10.1038/s41586-023-06337-5", "analog-ai chip", None),
    ("legallo2023", "doi", "10.1038/s41928-023-01010-1", "64-core", None),
    # tasks, models, GPU baseline
    ("lecun1998", "doi", "10.1109/5.726791", "gradient-based learning", None),
    ("krizhevsky2009", "url", "https://www.cs.toronto.edu/~kriz/learning-features-2009-TR.pdf", "",
     dict(type="techreport", author="Krizhevsky, Alex", title="Learning multiple layers of features from tiny images",
          institution="University of Toronto", year="2009")),
    ("mahoney2011", "url", "http://mattmahoney.net/dc/textdata.html", "enwik8",
     dict(type="misc", author="Mahoney, Matt", title="About the test data (enwik8 and enwik9), Large Text Compression Benchmark",
          howpublished="\\url{http://mattmahoney.net/dc/textdata.html}", year="2011", note="accessed 2026-10-25")),
    ("vaswani2017", "arxiv", "1706.03762", "attention is all you need", None),
    ("kingma2014", "arxiv", "1412.6980", "adam", None),
    ("dubey2024", "arxiv", "2407.21783", "llama 3", None),
    ("horowitz2014", "doi", "10.1109/ISSCC.2014.6757323", "energy problem", None),
    ("nvidiah100", "url", "https://www.nvidia.com/en-us/data-center/h100/", "700W",
     dict(type="misc", author="{NVIDIA Corporation}", title="{NVIDIA H100 Tensor Core GPU} datasheet",
          howpublished="\\url{https://www.nvidia.com/en-us/data-center/h100/}",
          year="2023", note="accessed 2026-10-25")),
    ("murmann_adc", "url", "https://github.com/bmurmann/ADC-survey", "ADC Performance Survey",
     dict(type="misc", author="Murmann, Boris", title="{ADC} Performance Survey 1997--2024",
          howpublished="\\url{https://github.com/bmurmann/ADC-survey}", year="2024", note="accessed 2026-10-25")),
    ("arxiv_policy", "url", "https://info.arxiv.org/help/moderation/index.html", "should not be listed as an author",
     dict(type="misc", author="{arXiv}", title="arXiv moderation policies and procedures (including the policy on authors' use of generative AI tools)",
          howpublished="\\url{https://info.arxiv.org/help/moderation/index.html}", year="2026", note="accessed 2026-10-25")),
]


def get(url, accept=None, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **({"Accept": accept} if accept else {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def tex_escape(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    s = " ".join(s.split())
    for a, b in (("&", "\\&"), ("%", "\\%"), ("#", "\\#"), ("_", "\\_")):
        s = s.replace(a, b)
    return s


def crossref(doi):
    st, b = get("https://api.crossref.org/works/" + doi)
    m = json.loads(b.decode("utf-8"))["message"]
    authors = [((a.get("family") or a.get("name") or "").strip(), (a.get("given") or "").strip()) for a in m.get("author", [])]
    year = (m.get("issued") or {}).get("date-parts", [[None]])[0][0]
    return dict(title=(m.get("title") or [""])[0], authors=authors, year=year,
                venue=(m.get("container-title") or [""])[0] if m.get("container-title") else (m.get("publisher") or ""),
                volume=m.get("volume"), issue=m.get("issue"), pages=m.get("page") or m.get("article-number"),
                type=m.get("type"), publisher=m.get("publisher"), doi=m.get("DOI"))


def arxiv(aid):
    st, b = get("https://export.arxiv.org/api/query?id_list=" + aid)
    ns = {"a": "http://www.w3.org/2005/Atom"}
    e = ET.fromstring(b).find("a:entry", ns)
    title = " ".join(e.find("a:title", ns).text.split())
    authors = []
    for a in e.findall("a:author", ns):
        parts = a.find("a:name", ns).text.strip().split()
        authors.append((parts[-1], " ".join(parts[:-1])))
    year = int(e.find("a:published", ns).text[:4])
    return dict(title=title, authors=authors, year=year, venue="arXiv preprint", arxiv=aid)


def bib_from_meta(key, kind, m):
    names = [f"{f}, {g}".strip(", ") for f, g in m["authors"]]
    if len(names) > 10:  # REVISION (review item 13): a long author list is abbreviated to the first author et al.
        names = names[:1] + ["others"]
    au = " and ".join(names) or "{Anonymous}"
    f = dict(author=au, title="{" + tex_escape(m["title"]) + "}", year=str(m["year"]))
    if kind == "arxiv":
        f.update(journal=f"arXiv preprint arXiv:{m['arxiv']}", eprint=m["arxiv"], archivePrefix="arXiv")
        typ = "article"
    else:
        t = m.get("type")
        if t == "proceedings-article":
            typ = "inproceedings"
            f["booktitle"] = tex_escape(m["venue"])
        elif t in ("report", "report-component"):
            typ = "techreport"
            f["institution"] = tex_escape(m.get("publisher") or "")
        else:
            typ = "article"
            f["journal"] = tex_escape(m["venue"])
        for k in ("volume", "issue", "pages"):
            if m.get(k):
                f["number" if k == "issue" else k] = str(m[k]).replace("-", "--")
        f["doi"] = m["doi"]
    body = ",\n".join(f"  {k} = {{{v}}}" if not v.startswith("{") else f"  {k} = {v}" for k, v in f.items())
    return f"@{typ}{{{key},\n{body}\n}}\n"


def bib_manual(key, fields):
    f = dict(fields)
    typ = f.pop("type")
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in f.items())
    return f"@{typ}{{{key},\n{body}\n}}\n"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    out, bib = [], []
    for key, kind, ident, expect, manual in REFS:
        row = dict(key=key, kind=kind, id=ident)
        try:
            if kind == "doi":
                m = crossref(ident)
                row.update(source="api.crossref.org", fetched_title=m["title"], authors=[" ".join(x[::-1]).strip() for x in m["authors"]],
                           year=m["year"], venue=m["venue"], volume=m.get("volume"), pages=m.get("pages"), crossref_type=m.get("type"))
                ok = expect.lower() in m["title"].lower() and bool(m["authors"]) and bool(m["year"])
                bib.append(bib_from_meta(key, kind, m))
            elif kind == "arxiv":
                m = arxiv(ident)
                row.update(source="export.arxiv.org", fetched_title=m["title"], authors=[" ".join(x[::-1]).strip() for x in m["authors"]],
                           year=m["year"])
                ok = expect.lower() in m["title"].lower()
                bib.append(bib_from_meta(key, kind, m))
            else:
                st, b = get(ident)
                t = re.search(rb"<title[^>]*>(.*?)</title>", b[:200000], re.S | re.I)
                row.update(source="HTTP GET", http_status=st, bytes=len(b), content_start=b[:8].decode("latin-1"),
                           page_title=html.unescape(t.group(1).decode("utf-8", "replace")).strip()[:200] if t else None,
                           stated=manual)
                ok = st == 200 and len(b) > 1000 and (not expect or expect.encode() in b)
                row["must_contain"] = expect or None
                bib.append(bib_manual(key, manual))
            row["verified"] = bool(ok)
        except Exception as e:
            row.update(verified=False, error=f"{type(e).__name__}: {e}")
            if manual:
                bib.append(bib_manual(key, dict(manual, note=(manual.get("note", "") + "; NOT VERIFIED").strip("; "))))
        out.append(row)
        print(("OK   " if row["verified"] else "FAIL ") + key + "  " + str(row.get("fetched_title") or row.get("page_title") or row.get("error"))[:90], flush=True)
        time.sleep(0.4)
    (PAPER / "tex").mkdir(exist_ok=True)
    (PAPER / "tex" / "refs.bib").write_bytes(("% generated by cite/cite_check.py from Crossref / arXiv metadata (do not edit by hand)\n\n" + "\n".join(bib)).encode("utf-8"))
    rec = dict(schema="altone.x1000.me-paper.cite-check.v1", checked_at_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
               n=len(out), n_verified=sum(r["verified"] for r in out), refs=out)
    (PAPER / "records" / "CITE-CHECK.json").write_bytes((json.dumps(rec, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"verified {rec['n_verified']} / {rec['n']}")


if __name__ == "__main__":
    main()
