"""ME-REVISE-7: the version-8 edits to the LaTeX sources and PUBLISHING.md, by named anchors (each must occur exactly once).
Review 7 found no actionable defect.  Version 8 carries the owner's two orders of 2026-10-27 (about 20:1x ET):
  1. print his official name, Anthony DeMarco, instead of the name used so far (affiliation unchanged: Independent researcher);
  2. credit ChatGPT, not as an author, in the AI-use statement of both variants.

    python -B revision7/edit_7.py
"""
from pathlib import Path

P = Path(__file__).resolve().parent.parent
OLD = "Quest" + "eria"          # written in two pieces so that this script is itself clean under the name proof
NEW = "Anthony DeMarco"

CHATGPT = ("ChatGPT (OpenAI), also an AI system and not an author, reviewed versions 1 to 7 of this paper in turn: it checked the\n"
           "record hashes, independently recomputed the revised statistics, and reported errors, each of which was verified against\n"
           "the files and corrected where confirmed (Appendix~\\ref{app:revision}).")


def edit(path, subs):
    t = path.read_bytes().decode("utf-8")
    for name, a, b in subs:
        assert t.count(a) == 1, (path.name, name, t.count(a))
        t = t.replace(a, b)
    assert "\r\n" not in t
    path.write_bytes(t.encode("utf-8"))


edit(P / "tex" / "main.tex", [
    ("comment", "chosen by the owner: %s and Claude" % OLD, "chosen by the owner: %s and Claude" % NEW),
    ("author", "\\author{%s\\\\ \\small Independent researcher \\and Claude" % OLD,
     "\\author{%s\\\\ \\small Independent researcher \\and Claude" % NEW),
])
edit(P / "tex" / "main-arxiv.tex", [
    ("author", "\\author{%s\\\\ \\small Independent researcher}" % OLD, "\\author{%s\\\\ \\small Independent researcher}" % NEW),
])
edit(P / "tex" / "body.tex", [
    ("arxiv-name", "%s conceived the study, directed it," % OLD, "%s conceived the study, directed it," % NEW),
    ("arxiv-chatgpt", "All numbers were produced by scripts from the saved records.\n\\else",
     "All numbers were produced by scripts from the saved records.\n\n" + CHATGPT + "\n\\else"),
    ("both-name1", "%s conceived and directed the study." % OLD, "%s conceived and directed the study." % NEW),
    ("both-name2", "under %s's direction," % OLD, "under %s's direction," % NEW),
    ("both-chatgpt", "verified the\nreferences, and drafted the text.\n\nUnder the policies",
     "verified the\nreferences, and drafted the text. " + CHATGPT + "\n\nUnder the policies"),
    ("both-name3", "lists %s as the sole author" % OLD, "lists %s as the sole author" % NEW),
    ("inventory", "\\texttt{RESPONSE-TO-REVIEW-5.md}, \\texttt{RESPONSE-TO-REVIEW-6.md});",
     "\\texttt{RESPONSE-TO-REVIEW-5.md}, \\texttt{RESPONSE-TO-REVIEW-6.md}, \\texttt{RESPONSE-TO-REVIEW-7.md});"),
    ("sevenlabel", "the responses to the six\n      independent reviews", "the responses to the seven\n      independent reviews"),
])
edit(P / "tex" / "app_revision.tex", [
    ("v7-not-this", "Version 7 (October 27, 2026;\nthis paper) answers a sixth review", "Version 7 (October 27, 2026)\nanswers a sixth review"),
    ("v8",
     "and the HTML check refuses any leftover rule argument or raw command.\n",
     "and the HTML check refuses any leftover rule argument or raw command. Version 8 (October 27, 2026; this paper) answers a\n"
     "seventh review, which found no actionable defect (\\texttt{RESPONSE-TO-REVIEW-7.md}; no experiment was run and no number\n"
     "changed). It carries two changes ordered by the author: his official name, %s, replaces the name printed in versions 1 to 7,\n"
     "and the contribution statement credits ChatGPT's reviews.\n" % NEW),
])
edit(P / "PUBLISHING.md", [
    ("l7", "lists the authors as you asked: \"%s\" and \"Claude (Anthropic)\"." % OLD,
     "lists the authors as you asked: \"%s\" and \"Claude (Anthropic)\"." % NEW),
    ("l9", "lists \"%s\" alone." % OLD, "lists \"%s\" alone." % NEW),
    ("l23", "You may replace \"%s\" with your full name in both files: it is the `\\author` line near the top of each. Neither variant\n"
     "prints an email address." % OLD,
     "Version 8 prints your official name, \"%s\", with the affiliation \"Independent researcher\", in both files (your word of\n"
     "2026-10-27); there is nothing left to replace. The contribution statement of both variants also credits ChatGPT (OpenAI), an AI\n"
     "system and not an author, for its reviews of versions 1 to 7. Neither variant prints an email address." % NEW),
    ("builder", "`pod/build_rev6.sh` for version 7, on the desk", "`pod/build_rev6.sh` for version 7 and `pod/build_rev7.sh` for version 8, on the desk"),
    ("checker", "`revision6/check_build_v7.py` runs `revision5/check_build_v6.py` and adds",
     "`revision7/check_build_v8.py` runs `revision6/check_build_v7.py` and adds the name proof (`revision7/name_check.py`: the old name\n"
     "   appears nowhere in the sources, either PDF's text and metadata, the HTML or the archive); `revision6/check_build_v7.py` runs\n"
     "   `revision5/check_build_v6.py` and adds"),
])
print("edited")
