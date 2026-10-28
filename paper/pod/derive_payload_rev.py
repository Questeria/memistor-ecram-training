"""REVISION: derive pod/make_payload_rev.py from pod/make_payload.py by named anchors (each must match once).

    python -B derive_payload_rev.py
Changes: the payload also holds records/revision/*.json (CATALOG-REV, CHOICES-REVISION when present), revision/aihwkit_curves.py
and pod/run_rev.sh (as run.sh); --with-runs reads records/revision/runs/<phase> when the phase is written rev:<phase>.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
t = (HERE / "make_payload.py").read_bytes().decode("utf-8")
SUBS = [
    ("doc", '"""Build lane ME-PAPER\'s pod payload', '"""REVISION payload (derived by pod/derive_payload_rev.py). Build lane ME-PAPER\'s pod payload'),
    ("records",
     "        if p.exists():\n            files['records/' + n] = p.read_bytes()\n",
     "        if p.exists():\n            files['records/' + n] = p.read_bytes()\n"
     "    for p in sorted((PAPER / 'records' / 'revision').glob('*.json')):\n"
     "        if p.name.startswith(('CATALOG-REV', 'CHOICES-REVISION')):\n"
     "            files['records/revision/' + p.name] = p.read_bytes()\n"
     "    files['revision/aihwkit_curves.py'] = (PAPER / 'revision' / 'aihwkit_curves.py').read_bytes()\n"),
    ("runs_dir",
     "                for f in sorted((PAPER / 'records' / 'runs' / ph).glob('*.json')):\n"
     "                    b = f.read_bytes()\n"
     "                    ti = tarfile.TarInfo('runs/%s/%s' % (ph, f.name))\n",
     "                rev = ph.startswith('rev:')\n"
     "                ph = ph[4:] if rev else ph\n"
     "                src = PAPER / 'records' / ('revision/runs' if rev else 'runs') / ph\n"
     "                for f in sorted(src.glob('*.json')):\n"
     "                    b = f.read_bytes()\n"
     "                    ti = tarfile.TarInfo(('revision/' if rev else '') + 'runs/%s/%s' % (ph, f.name))\n"),
    ("runsh", "    files['run.sh'] = (HERE / 'run.sh').read_bytes()\n", "    files['run.sh'] = (HERE / 'run_rev.sh').read_bytes()\n"),
    ("schema", "schema='x1000.me-paper.payload.v1'", "schema='x1000.me-revision.payload.v1'"),
]
for name, a, b in SUBS:
    assert t.count(a) == 1, name
    t = t.replace(a, b)
(HERE / "make_payload_rev.py").write_bytes(t.encode("utf-8"))
print("wrote make_payload_rev.py")
