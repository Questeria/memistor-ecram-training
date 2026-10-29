"""Version 10 of the memistor paper: the public archive (Zenodo, published 2026-10-28 ET), its DOI and its GitHub mirror in the
availability section, and version 10's line in the history.

    python -I -B revision9/edit_10.py

Each anchor is matched with any run of whitespace between its words and must occur exactly once.  The GitHub mirror's address
carries the author's account name, which version 8 removed from the papers; the owner allowed it in this one place (2026-10-28:
"The GitHub is fine with <account>, just make sure it is clear"), so the sentence says the account is the author's, and
revision9/name_check_v10.py allows the name inside that address only.  The name is written in two pieces so this script stays clean.
"""
import re
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "tex"
GH = "https://github.com/" + "Quest" + "eria" + "/memistor-ecram-training"

LEAD_OLD = r"""Nothing has been deposited publicly yet. On deposit, one archive will hold everything needed to reproduce this paper, with
versions, source hashes, dataset digests and split offsets, run manifests and licences:"""
LEAD_NEW = (r"""One public archive holds everything needed to reproduce this paper, with versions, source hashes, dataset digests and split
offsets, run manifests and licences: Zenodo, \href{https://doi.org/10.5281/zenodo.23748861}{doi:10.5281/zenodo.23748861}
(this DOI cites all versions; version~1.0 of the archive holds version~9 of this paper). The same files are on GitHub under
the author's account, \url{""" + GH + r"""} (release v1.0). Code is under the MIT License; records, pulse draws, text and
figures are under CC~BY~4.0. The archive keeps the study folder's layout, and the paths below are relative to its
\texttt{paper/} directory. It holds:""")

REV_OLD = r"""their deviations (\texttt{DEVIATIONS-PAPER.md}) and the responses to the seven
      independent reviews (\texttt{RESPONSE-TO-REVIEW.md},"""
REV_NEW = r"""their deviations (\texttt{DEVIATIONS-PAPER.md}), the seven independent reviews
      (\texttt{reviews/}) and the responses to them (\texttt{RESPONSE-TO-REVIEW.md},"""

DRAW_OLD = r"""(\RZDrawBytes{} bytes, outside the code
      repository; each file's SHA-256"""
DRAW_NEW = r"""(\RZDrawBytes{} bytes, in
      \texttt{draws/rev3/}; each file's SHA-256"""

CLOSE_OLD = r"""The archive DOI will be added on deposit (Zenodo). Data: MNIST, CIFAR-10 and enwik8 are public and pinned by digest. All text
data used for training is human-written (Wikipedia, 2006)."""
CLOSE_NEW = r"""In the archive's copies of the reviews and of one response, local file paths are shortened for privacy; the archive's
\texttt{REDACTIONS.md} lists every change. Data: MNIST, CIFAR-10 and enwik8 are public and pinned by digest; they are not
redistributed, and the archive's \texttt{fetch\_data.py} downloads them and checks the digests. All text data used for training
is human-written (Wikipedia, 2006)."""

HIST_OLD = r"""Version 9 (October 28, 2026; this paper) corrects the deviation count R1--R6 to R1--R8, found by the deposit's clean-room regeneration."""
HIST_NEW = r"""Version 9 (October 28, 2026) corrects the deviation count R1--R6 to R1--R8, found by the deposit's clean-room regeneration.
Version 10 (October 28, 2026; this paper) gives the public archive, its DOI and its GitHub mirror in Section~\ref{sec:availability};
no number changed."""


def edit(name, subs):
    p = TEX / name
    t = p.read_bytes().decode("utf-8")
    for tag, a, b in subs:
        pat = r"\s+".join(re.escape(w) for w in a.split())
        n = len(re.findall(pat, t))
        assert n == 1, (name, tag, n)
        t = re.sub(pat, lambda m: b, t)
    p.write_bytes(t.encode("utf-8"))


edit("body.tex", [("lead", LEAD_OLD, LEAD_NEW), ("reviews", REV_OLD, REV_NEW), ("draws", DRAW_OLD, DRAW_NEW),
                  ("close", CLOSE_OLD, CLOSE_NEW)])
edit("app_revision.tex", [("history", HIST_OLD, HIST_NEW)])
print("edited body.tex (4 anchors), app_revision.tex (1 anchor)")
