"""Version 10: the old author name may appear in one context only, the GitHub mirror's address github.com/<account>/memistor-ecram-training
(owner, 2026-10-28: "The GitHub is fine with <account>, just make sure it is clear"); everywhere else it must still be absent, and the
owner's official name must be present as in version 8.

The same channels as revision7/name_check.py (current tex sources, both PDFs' raw bytes, Info dict, object text, the HTML's bytes and
visible text, every member of the arXiv archive), counted twice: for the old name and for the allowed address.  The address contains the
name once, so the two counts are equal in a channel exactly when every occurrence of the name lies inside the address.  The PDFs' page text
is read with all whitespace removed, so an address broken across two lines still counts as the address.

The check is shown to fail on a planted name outside the address (HTML, PDF page text, tex source, archive member), on a near-miss address
(another repository of the same account) and on version 7 (the old name as author), and to accept the address broken across two lines.

    python -B revision9/name_check_v10.py <build out dir> <tex dir> [--json out.json]         (WSL venv with PyMuPDF)
"""
import io
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(P, "revision7"))
import name_check as N  # noqa: E402
import fitz  # noqa: E402  PyMuPDF

ALLOWED = "github.com/" + N.OLD + "/memistor-ecram-training"


def pdf_text_nows(data, s):
    with fitz.open(stream=data, filetype="pdf") as doc:
        return re.sub(r"\s+", "", "".join(p.get_text() for p in doc)).lower().count(s.lower())


def channels(out, tex_dir, s):
    """per-channel counts of s as name_check.scan finds them, with the PDFs' page text read without whitespace"""
    r = N.scan(out, tex_dir, s)
    c = {"tex:" + f: n for f, n in r["tex"]["hits"]}
    for k in ("main.pdf", "main-arxiv.pdf"):
        for ch in ("raw", "info_dict", "objects"):
            c[k + ":" + ch] = r[k][ch]
        c[k + ":text"] = pdf_text_nows(open(os.path.join(out, k), "rb").read(), s)
    for ch in ("raw", "visible"):
        c["main.html:" + ch] = r["main.html"][ch]
    c.update({"tar:" + m: n for m, n in r["arxiv-source.tar.gz"]["hits"]})
    if r["arxiv-abstract.txt"]:
        c["arxiv-abstract.txt"] = r["arxiv-abstract.txt"]["raw"]
    return {k: v for k, v in c.items() if v}


def judge(out, tex_dir):
    old, allowed = channels(out, tex_dir, N.OLD), channels(out, tex_dir, ALLOWED)
    outside = {k: old[k] - allowed.get(k, 0) for k in old if old[k] != allowed.get(k, 0)}
    return dict(old=old, allowed=allowed, outside_allowed=outside, ok=not outside)


def selftest(out, tex_dir):
    res = {}
    with tempfile.TemporaryDirectory() as td:
        o2, t2 = os.path.join(td, "out"), os.path.join(td, "tex")
        os.makedirs(o2)
        for f in ("main.pdf", "main-arxiv.pdf", "main.html", "arxiv-source.tar.gz", "arxiv-abstract.txt"):
            if os.path.exists(os.path.join(out, f)):
                shutil.copy(os.path.join(out, f), o2)
        shutil.copytree(tex_dir, t2, ignore=shutil.ignore_patterns("v[0-9]*", "figs"))
        res["clean_copy_passes"] = judge(o2, t2)["ok"]

        def planted(f, data):
            p = os.path.join(o2, f)
            keep = open(p, "rb").read()
            open(p, "wb").write(data)
            r = judge(o2, t2)["ok"]
            open(p, "wb").write(keep)
            return r is False

        html = open(os.path.join(o2, "main.html"), "rb").read()
        res["planted_html_text"] = planted("main.html", html.replace(b"</body>", ("<p>by %s</p></body>" % N.OLD).encode(), 1))
        res["planted_near_miss_address"] = planted("main.html", html.replace(
            b"</body>", ("<p>github.com/%s/another-repository</p></body>" % N.OLD).encode(), 1))
        with fitz.open(os.path.join(o2, "main.pdf")) as d:   # closed before the copy is replaced (Windows locks an open file;
            d[0].insert_text((72, 72), "by %s" % N.OLD)        # review 10, finding 4)
            data = d.tobytes()
        res["planted_pdf_text"] = planted("main.pdf", data)
        tp = os.path.join(o2, "arxiv-source.tar.gz")
        keep = open(tp, "rb").read()
        with tarfile.open(fileobj=io.BytesIO(keep), mode="r:gz") as src, tarfile.open(tp, "w:gz") as dst:
            for m in src.getmembers():
                dst.addfile(m, src.extractfile(m) if m.isfile() else None)
            b = ("%% %s\n" % N.OLD).encode()
            ti = tarfile.TarInfo("planted.tex")
            ti.size = len(b)
            dst.addfile(ti, io.BytesIO(b))
        res["planted_tar_member"] = judge(o2, t2)["ok"] is False
        open(tp, "wb").write(keep)
        open(os.path.join(t2, "planted.tex"), "wb").write(("%% %s\n" % N.OLD).encode())
        res["planted_tex"] = judge(o2, t2)["ok"] is False
        os.remove(os.path.join(t2, "planted.tex"))
        with fitz.open() as b2:
            pg = b2.new_page()
            pg.insert_text((72, 72), "https://github.com/")
            pg.insert_text((72, 90), N.OLD + "/memistor-ecram-training")
            data = b2.tobytes()
        res["broken_address_allowed"] = pdf_text_nows(data, N.OLD) == 1 == pdf_text_nows(data, ALLOWED)
    v7 = judge(os.path.join(P, "build", "v7"), os.path.join(P, "tex", "v7"))
    res["v7_fails"] = v7["ok"] is False
    res["v7_outside_total"] = sum(v7["outside_allowed"].values())
    res["ok"] = all(v for k, v in res.items() if k != "v7_outside_total")
    return res


def main():
    out, tex_dir = sys.argv[1], sys.argv[2]
    j = judge(out, tex_dir)
    new = N.scan(out, tex_dir, N.NEW)
    present = dict(main_pdf_text=new["main.pdf"]["text"], arxiv_pdf_text=new["main-arxiv.pdf"]["text"],
                   html_visible=new["main.html"]["visible"], archive_members=len(new["arxiv-source.tar.gz"]["hits"]),
                   tex_files=len(new["tex"]["hits"]))
    shown = {k: j["allowed"].get(k, 0) for k in ("main.pdf:text", "main-arxiv.pdf:text", "main.html:visible", "tex:body.tex", "tar:body.tex")}
    st = selftest(out, tex_dir)
    res = dict(allowed_context=ALLOWED.replace(N.OLD, "<account>"), judge=j, new_name_present=present, address_shown=shown, selftest=st)
    res["all_ok"] = (j["ok"] and st["ok"] and all(v >= 1 for v in shown.values()) and present["main_pdf_text"] >= 2
                     and present["arxiv_pdf_text"] >= 2 and present["html_visible"] >= 2 and present["archive_members"] >= 1
                     and present["tex_files"] >= 2)
    print("outside the address:", j["outside_allowed"] or 0, "| address shown:", shown, "| new name:", present,
          "| selftest ok", st["ok"], "(v7 outside", st["v7_outside_total"], ")", "|", "NAME_OK" if res["all_ok"] else "NAME_NOT_OK")
    if "--json" in sys.argv:
        blob = json.dumps(res, indent=1, ensure_ascii=False).replace(N.OLD, "<account>")
        open(sys.argv[sys.argv.index("--json") + 1], "wb").write((blob + "\n").encode("utf-8"))
    sys.exit(0 if res["all_ok"] else 1)


if __name__ == "__main__":
    main()
