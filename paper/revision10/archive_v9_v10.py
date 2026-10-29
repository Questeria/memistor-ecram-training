"""Version 11: archive the sources of versions 9 and 10 (tex/v9, tex/v10: the 28 top-level .tex files, as tex/v1..v8 hold them)
and version 10's outputs (build/v10), before version 11 changes tex/ and build/.  Version 10 left tex/v9 out; it is taken from
the version-9 commit.  Refuses to overwrite an existing archive and checks every byte it writes.

    python -I -B revision10/archive_v9_v10.py
"""
import hashlib
import os
import shutil
import subprocess
from pathlib import Path

P = Path(__file__).resolve().parent.parent
REPO = P.parents[4]                                   # the author's repository root
REL = P.relative_to(REPO).as_posix()
V9_COMMIT = "b2b002ea7"                               # "version 9 of the memistor paper"
V10_ARXIV_SHA = "8660babf8321459d1f716e2527a72e25da0f1d14a932a54f4e5db75243a717f0"   # build/main-arxiv.pdf of version 10


def git_show(commit, rel):
    return subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:{REL}/{rel}"], capture_output=True, check=True).stdout


names = sorted(f.name for f in (P / "tex").glob("*.tex"))
assert len(names) == 28, names
assert sorted(f.name for f in (P / "tex" / "v8").glob("*.tex")) == names
for v, get in (("v9", lambda n: git_show(V9_COMMIT, "tex/" + n)), ("v10", lambda n: git_show("HEAD", "tex/" + n))):
    d = P / "tex" / v
    assert not d.exists(), d
    d.mkdir()
    for n in names:
        (d / n).write_bytes(get(n))
        assert (d / n).read_bytes() == get(n)
for n in names:                                       # tex/ is still version 10's when this runs
    assert (P / "tex" / n).read_bytes() == (P / "tex" / "v10" / n).read_bytes(), n
assert hashlib.sha256((P / "build" / "main-arxiv.pdf").read_bytes()).hexdigest() == V10_ARXIV_SHA
b = P / "build" / "v10"
assert not b.exists(), b
b.mkdir()
for n in sorted(os.listdir(P / "build" / "v9")):
    shutil.copyfile(P / "build" / n, b / n)
    assert (b / n).read_bytes() == (P / "build" / n).read_bytes()
print("archived tex/v9, tex/v10 (%d files each) and build/v10 (%d files)" % (len(names), len(os.listdir(b))))
