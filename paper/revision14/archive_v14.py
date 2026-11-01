"""Version 15: archive the sources of version 14 (tex/v14: the 28 top-level .tex files, as tex/v1..v13 hold them, taken from the
version-14 commit) and version 14's outputs (build/v14, the files of release v1.4 that review 12 read: build/main.pdf, 44 pages;
build/main-arxiv.pdf has the SHA-256 below), before version 15 changes tex/ and build/.  Refuses to overwrite an existing archive
and checks every byte it writes.  Derived from revision13/archive_v13.py (the commit, the hash and the folder names change).

    python -I -B revision14/archive_v14.py
"""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

P = Path(__file__).resolve().parent.parent
REPO = P.parents[4]                                   # the author's repository root
REL = P.relative_to(REPO).as_posix()
V14_COMMIT = "3cbefba20"                              # "X1000 memistor paper version 14: the answer to review 11"
V14_ARXIV_SHA = "b9d785ea913c1d7e4e89ac88942f3c6122ea525f403173734e987a643352d5af"   # build/main-arxiv.pdf of version 14


def git_show(commit, rel):
    return subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:{REL}/{rel}"], capture_output=True, check=True).stdout


names = sorted(f.name for f in (P / "tex").glob("*.tex"))
assert len(names) == 28, names
assert sorted(f.name for f in (P / "tex" / "v13").glob("*.tex")) == names
d = P / "tex" / "v14"
assert not d.exists(), d
d.mkdir()
for n in names:
    b = git_show(V14_COMMIT, "tex/" + n)
    (d / n).write_bytes(b)
    assert (d / n).read_bytes() == b
assert hashlib.sha256((P / "build" / "main-arxiv.pdf").read_bytes()).hexdigest() == V14_ARXIV_SHA
b = P / "build" / "v14"
assert not b.exists(), b
b.mkdir()
for n in sorted(os.listdir(P / "build" / "v13")):
    shutil.copyfile(P / "build" / n, b / n)
    assert (b / n).read_bytes() == (P / "build" / n).read_bytes() == git_show(V14_COMMIT, "build/" + n), n
print("archived tex/v14 (%d files) and build/v14 (%d files)" % (len(names), len(os.listdir(b))))
