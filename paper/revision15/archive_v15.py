"""Version 16: archive the sources of version 15 (tex/v15: the 28 top-level .tex files, as tex/v1..v14 hold them, taken from the
version-15 commit) and version 15's outputs (build/v15, the files of release v1.5 that review 13 read: build/main.pdf, 44 pages;
build/main-arxiv.pdf has the SHA-256 below), before version 16 changes tex/ and build/.  Refuses to overwrite an existing archive
and checks every byte it writes.  Derived from revision14/archive_v14.py (the commit, the hash and the folder names change).

    python -I -B revision15/archive_v15.py
"""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

P = Path(__file__).resolve().parent.parent
REPO = P.parents[4]                                   # the author's repository root
REL = P.relative_to(REPO).as_posix()
V15_COMMIT = "22235e630"                              # "X1000 memistor paper version 15: the answer to review 12"
V15_ARXIV_SHA = "79f2eca47114094855ef822cf22491fe79cf60b3336c6a078fb62e91c1347dcf"   # build/main-arxiv.pdf of version 15


def git_show(commit, rel):
    return subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:{REL}/{rel}"], capture_output=True, check=True).stdout


names = sorted(f.name for f in (P / "tex").glob("*.tex"))
assert len(names) == 28, names
assert sorted(f.name for f in (P / "tex" / "v14").glob("*.tex")) == names
d = P / "tex" / "v15"
assert not d.exists(), d
d.mkdir()
for n in names:
    b = git_show(V15_COMMIT, "tex/" + n)
    (d / n).write_bytes(b)
    assert (d / n).read_bytes() == b
assert hashlib.sha256((P / "build" / "main-arxiv.pdf").read_bytes()).hexdigest() == V15_ARXIV_SHA
b = P / "build" / "v15"
assert not b.exists(), b
b.mkdir()
for n in sorted(os.listdir(P / "build" / "v14")):
    shutil.copyfile(P / "build" / n, b / n)
    assert (b / n).read_bytes() == (P / "build" / n).read_bytes() == git_show(V15_COMMIT, "build/" + n), n
print("archived tex/v15 (%d files) and build/v15 (%d files)" % (len(names), len(os.listdir(b))))
