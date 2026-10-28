"""ME-REVISE-7: prove the old author name appears nowhere in version 8, and that the owner's official name does.

Searched, case-insensitively: every .tex/.bib/.md/.py source under tex/ (not the archived tex/v1..v7 folders), both PDFs (extracted text of every
page; the Info dictionary; every PDF object's text, which covers XMP and an object stream; the raw file bytes in UTF-8 and UTF-16),
the HTML (bytes, plus the visible text and <title>/<meta>), and every member of the arXiv archive (bytes, and the text of its PDF members).

The check is shown to fail: the same search on version 7's artifacts (build/v7 and tex/v7) finds the name, and a planted copy of the new
HTML / a new tex file / a new tar member with the name inserted is found.

    python -B revision7/name_check.py <build out dir> <tex dir> [--json out.json]         (WSL venv with PyMuPDF)
"""
import io
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile

import fitz  # PyMuPDF

OLD = "Quest" + "eria"        # in two pieces so that this script is itself clean
NEW = "Anthony DeMarco"
ENCS = ("utf-8", "utf-16-be", "utf-16-le", "latin-1")


def needle_bytes(s):
    return {e: s.encode(e) for e in ENCS}


def bytes_hit(b, s):
    low = b.lower()
    return sum(low.count(s.lower().encode(e)) for e in ("utf-8", "utf-16-be", "utf-16-le"))


def pdf_report(data, s):
    """hits of s in a PDF given as bytes: raw bytes, page text, Info dict, every object's text, XMP"""
    doc = fitz.open(stream=data, filetype="pdf")
    text = "\n".join(p.get_text() for p in doc)
    text_n = len(re.findall(re.escape(s), re.sub(r"\s+", " ", text), flags=re.I))
    meta = json.dumps(doc.metadata, ensure_ascii=False)
    meta_n = meta.lower().count(s.lower())
    obj_n = 0
    for x in range(1, doc.xref_length()):
        try:
            o = doc.xref_object(x, compressed=False)
        except Exception:
            continue
        obj_n += o.lower().count(s.lower())
        try:
            if doc.xref_get_key(x, "Type")[1] == "/Metadata":
                obj_n += doc.xref_stream(x).decode("utf-8", "replace").lower().count(s.lower())
        except Exception:
            pass
    return dict(raw=bytes_hit(data, s), text=text_n, info_dict=meta_n, objects=obj_n, pages=len(doc), metadata=doc.metadata)


def html_report(data, s):
    t = data.decode("utf-8", "replace")
    vis = re.sub(r"<script.*?</script>|<style.*?</style>", " ", t, flags=re.S | re.I)
    vis = re.sub(r"<[^>]+>", " ", vis)
    return dict(raw=bytes_hit(data, s), visible=len(re.findall(re.escape(s), re.sub(r"\s+", " ", vis), flags=re.I)),
                title=re.findall(r"<title>(.*?)</title>", t, flags=re.S | re.I)[:1],
                meta_author=re.findall(r'<meta name="author" content="([^"]*)"', t, flags=re.I))


def tar_report(path, s):
    hits, members, pdf_members = [], 0, 0
    with tarfile.open(path, "r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            members += 1
            b = tf.extractfile(m).read()
            n = bytes_hit(b, s)
            if m.name.lower().endswith(".pdf"):
                pdf_members += 1
                r = pdf_report(b, s)
                n += r["text"] + r["info_dict"] + r["objects"]
            if n:
                hits.append((m.name, n))
    # the names inside the archive are searched too
    return dict(members=members, pdf_members=pdf_members, hits=hits)


def tex_report(tex_dir, s):
    hits, files = [], 0
    for root, dirs, fs in os.walk(tex_dir):
        dirs[:] = [d for d in dirs if not re.fullmatch(r"v\d+", d)]
        for f in fs:
            if f.endswith((".tex", ".bib", ".bbl", ".md", ".txt", ".sty", ".cls")):
                files += 1
                b = open(os.path.join(root, f), "rb").read()
                n = bytes_hit(b, s)
                if n:
                    hits.append((os.path.relpath(os.path.join(root, f), tex_dir), n))
    return dict(files=files, hits=hits)


def scan(out, tex_dir, s):
    r = {}
    r["tex"] = tex_report(tex_dir, s)
    for pdf in ("main.pdf", "main-arxiv.pdf"):
        r[pdf] = pdf_report(open(os.path.join(out, pdf), "rb").read(), s)
    r["main.html"] = html_report(open(os.path.join(out, "main.html"), "rb").read(), s)
    r["arxiv-source.tar.gz"] = tar_report(os.path.join(out, "arxiv-source.tar.gz"), s)
    ab = os.path.join(out, "arxiv-abstract.txt")
    r["arxiv-abstract.txt"] = dict(raw=bytes_hit(open(ab, "rb").read(), s)) if os.path.exists(ab) else None
    return r


def total(r):
    n = len(r["tex"]["hits"]) and sum(h[1] for h in r["tex"]["hits"]) or 0
    for k in ("main.pdf", "main-arxiv.pdf"):
        n += r[k]["raw"] + r[k]["text"] + r[k]["info_dict"] + r[k]["objects"]
    n += r["main.html"]["raw"] + r["main.html"]["visible"]
    n += sum(h[1] for h in r["arxiv-source.tar.gz"]["hits"])
    if r["arxiv-abstract.txt"]:
        n += r["arxiv-abstract.txt"]["raw"]
    return n


def selftest(out, tex_dir, v7_out, v7_tex):
    """the search finds the name where it is: in version 7's artifacts, and in planted copies of version 8's"""
    res = {}
    r7 = scan(v7_out, v7_tex, OLD)
    res["v7_total_hits"] = total(r7)
    res["v7_found_in"] = dict(tex=len(r7["tex"]["hits"]), main_pdf=r7["main.pdf"]["text"], arxiv_pdf=r7["main-arxiv.pdf"]["text"],
                              html=r7["main.html"]["visible"], archive=len(r7["arxiv-source.tar.gz"]["hits"]))
    tmp = tempfile.mkdtemp()
    try:
        # planted: HTML with the name in the author meta, a tex file, a tar member, a PDF whose Info author is the name
        h = open(os.path.join(out, "main.html"), "rb").read().replace(b"</head>", ("<meta name=\"author\" content=\"%s\"></head>" % OLD).encode(), 1)
        res["planted_html"] = html_report(h, OLD)["raw"] > 0
        d = fitz.open(os.path.join(out, "main.pdf"))
        md = d.metadata
        md["author"] = OLD
        d.set_metadata(md)
        b = d.tobytes()
        pr = pdf_report(b, OLD)
        res["planted_pdf_info"] = pr["info_dict"] > 0 or pr["objects"] > 0
        d2 = fitz.open()
        pg = d2.new_page()
        pg.insert_text((72, 72), "by %s" % OLD)
        res["planted_pdf_text"] = pdf_report(d2.tobytes(), OLD)["text"] > 0
        td = os.path.join(tmp, "tex")
        shutil.copytree(tex_dir, td, ignore=shutil.ignore_patterns("v[0-9]*", "figs"))
        open(os.path.join(td, "planted.tex"), "wb").write(("\\author{%s}\n" % OLD).encode())
        res["planted_tex"] = len(tex_report(td, OLD)["hits"]) > 0
        tp = os.path.join(tmp, "a.tar.gz")
        with tarfile.open(os.path.join(out, "arxiv-source.tar.gz"), "r:gz") as src, tarfile.open(tp, "w:gz") as dst:
            for m in src.getmembers():
                f = src.extractfile(m) if m.isfile() else None
                dst.addfile(m, f)
            data = ("%% %s\n" % OLD).encode()
            ti = tarfile.TarInfo("planted.tex")
            ti.size = len(data)
            dst.addfile(ti, io.BytesIO(data))
        res["planted_tar"] = len(tar_report(tp, OLD)["hits"]) > 0
        # the check is case-insensitive
        res["planted_case"] = bytes_hit(OLD.upper().encode(), OLD) > 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    res["ok"] = (res["v7_total_hits"] > 0 and all(v > 0 for v in res["v7_found_in"].values())
                 and all(res[k] for k in ("planted_html", "planted_pdf_info", "planted_pdf_text", "planted_tex", "planted_tar", "planted_case")))
    return res


def main():
    out, tex_dir = sys.argv[1], sys.argv[2]
    P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    old = scan(out, tex_dir, OLD)
    new = scan(out, tex_dir, NEW)
    st = selftest(out, tex_dir, os.path.join(P, "build", "v7"), os.path.join(P, "tex", "v7"))
    res = dict(searched_for="old name (written as two pieces in this script)", old_name_total_hits=total(old), old_name_detail=old,
               new_name_present=dict(main_pdf_text=new["main.pdf"]["text"], arxiv_pdf_text=new["main-arxiv.pdf"]["text"],
                                     html_visible=new["main.html"]["visible"], archive_members=len(new["arxiv-source.tar.gz"]["hits"]),
                                     tex_files=len(new["tex"]["hits"])),
               pdf_metadata={k: old[k]["metadata"] for k in ("main.pdf", "main-arxiv.pdf")},
               html_head={k: old["main.html"][k] for k in ("title", "meta_author")}, selftest=st)
    res["all_ok"] = (res["old_name_total_hits"] == 0 and st["ok"] and res["new_name_present"]["main_pdf_text"] >= 2
                     and res["new_name_present"]["arxiv_pdf_text"] >= 2 and res["new_name_present"]["html_visible"] >= 2
                     and res["new_name_present"]["archive_members"] >= 1 and res["new_name_present"]["tex_files"] >= 2)
    print("old name hits:", res["old_name_total_hits"], "| new name: main.pdf", res["new_name_present"]["main_pdf_text"], "arxiv.pdf",
          res["new_name_present"]["arxiv_pdf_text"], "html", res["new_name_present"]["html_visible"], "archive members",
          res["new_name_present"]["archive_members"], "tex files", res["new_name_present"]["tex_files"],
          "| selftest: v7 hits", st["v7_total_hits"], "ok", st["ok"], "|", "NAME_OK" if res["all_ok"] else "NAME_NOT_OK")
    print("pdf metadata:", json.dumps(res["pdf_metadata"], ensure_ascii=False)[:400])
    if "--json" in sys.argv:
        open(sys.argv[sys.argv.index("--json") + 1], "wb").write((json.dumps(res, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    sys.exit(0 if res["all_ok"] else 1)


if __name__ == "__main__":
    main()
