"""Version 13: archive the sources of version 12 (tex/v12: the 28 top-level .tex files, as tex/v1..v11 hold them, taken from the
version-12 commit) and version 12's outputs (build/v12, the files review 10 read: build/main-arxiv.pdf has the SHA-256 it quotes),
before version 13 changes tex/ and build/.  Refuses to overwrite an existing archive and checks every byte it writes.

    python -I -B revision12/archive_v12.py
"""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

P = Path(__file__).resolve().parent.parent
REPO = P.parents[4]                                   # the author's repository root
REL = P.relative_to(REPO).as_posix()
V12_COMMIT = "b8ab198cf"                              # "X1000 memistor paper version 12: the answer to review 9"
V12_ARXIV_SHA = "264f29c39c779fc07394ebf12a13f0eb3fbb6f7ab7c0483bcef424c42757fb0b"   # build/main-arxiv.pdf of version 12 (review 10)


def git_show(commit, rel):
    return subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:{REL}/{rel}"], capture_output=True, check=True).stdout


names = sorted(f.name for f in (P / "tex").glob("*.tex"))
assert len(names) == 28, names
assert sorted(f.name for f in (P / "tex" / "v11").glob("*.tex")) == names
d = P / "tex" / "v12"
assert not d.exists(), d
d.mkdir()
for n in names:
    b = git_show(V12_COMMIT, "tex/" + n)
    (d / n).write_bytes(b)
    assert (d / n).read_bytes() == b
assert hashlib.sha256((P / "build" / "main-arxiv.pdf").read_bytes()).hexdigest() == V12_ARXIV_SHA
b = P / "build" / "v12"
assert not b.exists(), b
b.mkdir()
for n in sorted(os.listdir(P / "build" / "v11")):
    shutil.copyfile(P / "build" / n, b / n)
    assert (b / n).read_bytes() == (P / "build" / n).read_bytes() == git_show(V12_COMMIT, "build/" + n), n
print("archived tex/v12 (%d files) and build/v12 (%d files)" % (len(names), len(os.listdir(b))))
