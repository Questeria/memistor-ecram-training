"""Version 14: archive the sources of version 13 (tex/v13: the 28 top-level .tex files, as tex/v1..v12 hold them, taken from the
version-13 commit) and version 13's outputs (build/v13, the files review 11 read: build/main.pdf, 43 pages; build/main-arxiv.pdf
has the SHA-256 below), before version 14 changes tex/ and build/.  Refuses to overwrite an existing archive and checks every byte
it writes.  Derived from revision12/archive_v12.py (the commit, the hash and the folder names change).

    python -I -B revision13/archive_v13.py
"""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

P = Path(__file__).resolve().parent.parent
REPO = P.parents[4]                                   # the author's repository root
REL = P.relative_to(REPO).as_posix()
V13_COMMIT = "75616d335"                              # "X1000 memistor paper version 13: the answer to review 10"
V13_ARXIV_SHA = "ced8d458200155bca03f06e0893865699579091ce004e6eeb6d65c1ee0be2bb6"   # build/main-arxiv.pdf of version 13


def git_show(commit, rel):
    return subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:{REL}/{rel}"], capture_output=True, check=True).stdout


names = sorted(f.name for f in (P / "tex").glob("*.tex"))
assert len(names) == 28, names
assert sorted(f.name for f in (P / "tex" / "v12").glob("*.tex")) == names
d = P / "tex" / "v13"
assert not d.exists(), d
d.mkdir()
for n in names:
    b = git_show(V13_COMMIT, "tex/" + n)
    (d / n).write_bytes(b)
    assert (d / n).read_bytes() == b
assert hashlib.sha256((P / "build" / "main-arxiv.pdf").read_bytes()).hexdigest() == V13_ARXIV_SHA
b = P / "build" / "v13"
assert not b.exists(), b
b.mkdir()
for n in sorted(os.listdir(P / "build" / "v12")):
    shutil.copyfile(P / "build" / n, b / n)
    assert (b / n).read_bytes() == (P / "build" / n).read_bytes() == git_show(V13_COMMIT, "build/" + n), n
print("archived tex/v13 (%d files) and build/v13 (%d files)" % (len(names), len(os.listdir(b))))
