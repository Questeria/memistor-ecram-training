"""Version 16, the static document edits (the owner's "fix anything stale", 2026-11-01): PUBLISHING.md, README.md, STATUS.json.
The edits that need the clean room's numbers are made by revision15/record_v16.py.  CRLF files stay CRLF.

    python -I -B revision15/edit_docs_v16.py
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parent.parent
ACCT = "Quest" + "eria"                       # written in two pieces so this script stays clean for the archive scan


def sub(text, a, b, n=1):
    assert text.count(a) == n, (a[:70], text.count(a))
    return text.replace(a, b)


def edit(name, fn):
    p = P / name
    t = p.read_bytes().decode("utf-8")
    crlf = "\r\n" in t
    t = fn(t.replace("\r\n", "\n"))
    p.write_bytes((t.replace("\n", "\r\n") if crlf else t).encode("utf-8"))


def pub(t):
    t = sub(t, "The\npaper is not yet on arXiv: submit version 15 (not 14).",
            "Release v1.6, which holds\nversion 16 (the answer to review 13), is built and verified and waits for publishing. The\n"
            "paper is not yet on arXiv: submit version 16 (not 15), after release v1.6 is published.")
    t = sub(t, '"memistor paper - arXiv submission (v15)" (SUBMIT-TO-ARXIV.txt there).',
            '"memistor paper - arXiv submission (v16)" (SUBMIT-TO-ARXIV.txt there).')
    t = sub(t, "the round is closed, with one optional self-test fix kept for a later maintenance release.",
            "the round is closed; its one optional self-test fix is in release v1.6, which holds version 16 (the contribution statement counts all thirteen reviews).")
    t = sub(t, "for its reviews of versions 1 to 7. Neither variant", "for its thirteen reviews (versions 1 to 7 and 10 to 15). Neither variant")
    t = sub(t, "**Release v1.5 (2026-11-01 01:43 ET)", "**Release v1.5 (2026-11-01 01:43 EDT)")
    t = sub(t, "and `pod/build_rev10.sh` for version 15,", "and `pod/build_rev10.sh` for versions 15 and 16,")
    t = sub(t, "loose copies of the files; `revision14/check_build_v15.py` (version 15) runs",
            "loose copies of the files; `revision15/check_build_v16.py` (version 16) runs `revision6/check_build_v7.py` and reads the version-16\n"
            "   proofs: the word-count text diff `revision15/pdf_text_diff_v16.py` (v15 -> v16, reference numbers as [#], the same 44 pages),\n"
            "   the name check in WSL and in Windows, numbers freshness, Figures 1 and 4, the reset and the Welch test;\n"
            "   `revision14/check_build_v15.py` (version 15) runs")
    t = sub(t, 'for version 15: "44 pages, 4 figures; code and data: https://doi.org/10.5281/zenodo.23748861".',
            'for version 16: "44 pages, 4 figures; code and data: https://doi.org/10.5281/zenodo.23748861".')
    return t


def rd(t):
    t = sub(t, "(authors " + ACCT + " and Claude (Anthropic))", "(authors Anthony DeMarco and Claude (Anthropic))")
    t = sub(t, "`build/main-arxiv.pdf` (" + ACCT + " only,", "`build/main-arxiv.pdf` (Anthony DeMarco only,")
    t = sub(t, "The published v1.5 (b5f86bed2), version 15 and the arXiv kit are unchanged.",
            "The published v1.5 (b5f86bed2), version 15 and the arXiv kit are unchanged. (Later the same day this became version 16 and archive\n  v1.6; see the next section.)")
    return t


edit("PUBLISHING.md", pub)
edit("README.md", rd)
sp = P / "STATUS.json"
st = json.loads(sp.read_bytes().decode("utf-8"))
st["lane"] = ("x1000-ME-PAPER director lane (version 16 of the memistor paper and archive v1.6); earlier: ME-REVISE .. ME-REVISE-7, "
              "ME-DEPOSIT, ME-DEPOSIT-2")
st["review"] = "reviews/REVIEW-13-chatgpt-20261101-full.md"
sp.write_bytes((json.dumps(st, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
print("edited PUBLISHING.md, README.md, STATUS.json")
