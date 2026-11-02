r"""Version 16 of the memistor paper: the answer to review 13 (ChatGPT's review of release v1.5 and version 15, 2026-11-01).  No
experiment; no result changes; the review found the version-15 fixes right and the paper ready to submit.  The text edits (the
tables and figures are untouched):

  1. body.tex, the contribution statement of both variants: "reviewed versions 1 to 7 of this paper in turn" was stale; the reviews
     are 1 to 7 of versions 1 to 7, 8 of version 10, 9 of version 11, 10 of version 12, 11 of version 13, 12 of version 14 and
     13 of version 15, so it now reads "versions 1 to 7 and 10 to 15 of this paper in turn, thirteen reviews in all:";
  2. app_revision.tex: version 15 is no longer "this paper"; a version-16 entry is added;
  3. the availability section (body.tex): archive v1.6 holds version 16, release v1.6, the thirteen independent reviews, and the
     thirteenth response in the list of responses.
  The concept DOI is unchanged.

    python -I -B revision15/edit_16.py

Each anchor is matched with any run of whitespace between its words and must occur exactly the stated number of times
(edit_15.py's rule); nothing is written unless every anchor of every file matched.
"""
import re
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "tex"

V16 = (r"Version 16 (November 1, 2026; this paper) answers a thirteenth review, of version 15 and version 1.5 of the archive" "\n"
       r"(\texttt{RESPONSE-TO-REVIEW-13.md}; no experiment was run and no result changed), which found the version-15 changes right" "\n"
       r"and no defect in the paper. The contribution statement now counts all thirteen reviews (versions 1 to 7 and 10 to 15)" "\n"
       r"instead of versions 1 to 7. The review's one optional finding concerned the archive's \texttt{reproduce\_all.py}: the" "\n"
       r"negative control of its numeric-policy self-test shifted a printed value by a fixed amount, which for another starting" "\n"
       r"value the policy permits would not change the printed number; the control now computes the shift from the starting value, as" "\n"
       r"the review suggested, to just across the nearest rounding boundary of the printed number and within the stated tolerance.")

# (tag, anchor, replacement, expected count)
EDITS = {
    "body.tex": [
        ("contribution", r"reviewed versions 1 to 7 of this paper in turn:",
         r"reviewed versions 1 to 7 and 10 to 15 of this paper in turn, thirteen reviews in all:", 2),
        ("archive version",
         r"(this DOI cites all versions; version~1.5 of the archive holds version~15 of this paper, version~1.4 holds version~14,",
         r"(this DOI cites all versions; version~1.6 of the archive holds version~16 of this paper, version~1.5 holds version~15," "\n"
         r"version~1.4 holds version~14,", 1),
        ("release", r"(release v1.5)", r"(release v1.6)", 1),
        ("reviews", r"the twelve independent reviews", r"the thirteen independent reviews", 1),
        ("responses", r"\texttt{RESPONSE-TO-REVIEW-12.md});", r"\texttt{RESPONSE-TO-REVIEW-12.md}, \texttt{RESPONSE-TO-REVIEW-13.md});", 1),
    ],
    "app_revision.tex": [
        ("v15 not current", r"Version 15 (November 1, 2026; this paper) answers", r"Version 15 (November 1, 2026) answers", 1),
        ("v16", r"comparison) under a stated numeric tolerance.", r"comparison) under a stated numeric tolerance." "\n" + V16, 1),
    ],
}


def apply(name, subs):
    p = TEX / name
    t = p.read_bytes().decode("utf-8")
    for tag, a, b, want in subs:
        pat = r"\s+".join(re.escape(w) for w in a.split())
        n = len(re.findall(pat, t))
        assert n == want, (name, tag, n, want)
        t = re.sub(pat, lambda m: b, t)
    return p, t


out = [apply(n, s) for n, s in EDITS.items()]        # every anchor of every file first
for p, t in out:
    p.write_bytes(t.encode("utf-8"))
print("edited", ", ".join(p.name for p, _ in out))
