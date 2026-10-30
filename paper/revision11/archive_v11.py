"""Version 12: archive the sources of version 11 (tex/v11: the 28 top-level .tex files, as tex/v1..v10 hold them, taken from the
version-11 commit, because review 9's regenerated numbers_rev.tex is already in tex/) and version 11's outputs (build/v11), before
version 12 changes tex/ and build/.  Refuses to overwrite an existing archive and checks every byte it writes.

    python -I -B revision11/archive_v11.py
"""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

P = Path(__file__).resolve().parent.parent
REPO = P.parents[4]                                   # the author's repository root
REL = P.relative_to(REPO).as_posix()
V11_COMMIT = "b10ef71b3"                              # "X1000 memistor paper version 11 and archive release v1.1"
V11_ARXIV_SHA = "67530090a653ced3af9475323a72e1798d89ecd38e1d06c2c0dbbc6b8a2a021d"   # build/main-arxiv.pdf of version 11


def git_show(commit, rel):
    return subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:{REL}/{rel}"], capture_output=True, check=True).stdout


names = sorted(f.name for f in (P / "tex").glob("*.tex"))
assert len(names) == 28, names
assert sorted(f.name for f in (P / "tex" / "v10").glob("*.tex")) == names
d = P / "tex" / "v11"
assert not d.exists(), d
d.mkdir()
for n in names:
    b = git_show(V11_COMMIT, "tex/" + n)
    (d / n).write_bytes(b)
    assert (d / n).read_bytes() == b
assert hashlib.sha256((P / "build" / "main-arxiv.pdf").read_bytes()).hexdigest() == V11_ARXIV_SHA
b = P / "build" / "v11"
assert not b.exists(), b
b.mkdir()
for n in sorted(os.listdir(P / "build" / "v10")):
    shutil.copyfile(P / "build" / n, b / n)
    assert (b / n).read_bytes() == (P / "build" / n).read_bytes() == git_show(V11_COMMIT, "build/" + n), n
print("archived tex/v11 (%d files) and build/v11 (%d files)" % (len(names), len(os.listdir(b))))
