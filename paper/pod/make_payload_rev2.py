"""REVISION payload (derived by pod/derive_payload_rev.py). Build lane ME-PAPER's pod payload (devpod --payload DIR), from lane ME's pod/make_payload.py.

    python -B paper/pod/make_payload.py --out H:/x1000/memistor-paper/payload/<name>

Holds:
- sim/*.py (the paper simulator);
- lane_me/sim/memsim.py and lane_me/records/TT-CHOICE.json (the identity check and the TTv2 choice);
- records/CATALOG.json and records/CHOICES-PAPER.json (when it exists);
- the four pinned MNIST idx files;
- the two pinned enwik8 slices (re-cut from the pinned enwik8 and checked against tasks.SLICE_SHA);
- run.sh, plus MANIFEST.sha256 over every other file.

CIFAR-10 is fetched by the pod (md5 pinned in run.sh). The script refuses an existing --out and any CRLF in code.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAPER = HERE.parent
LANE = PAPER.parent
sys.path.insert(0, str(PAPER / 'sim'))
import tasks  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--with-runs', nargs='*', default=[], help='phases whose run records the sitting needs (e.g. e4 for e5b)')
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        raise SystemExit('REFUSED: %s exists (a payload is built once)' % out)
    files = {}
    for f in sorted((PAPER / 'sim').glob('*.py')):
        files['sim/' + f.name] = f.read_bytes()
    files['lane_me/sim/memsim.py'] = (LANE / 'sim' / 'memsim.py').read_bytes()
    files['lane_me/records/TT-CHOICE.json'] = (LANE / 'records' / 'TT-CHOICE.json').read_bytes()
    for n in ('CATALOG.json', 'CHOICES-PAPER.json'):
        p = PAPER / 'records' / n
        if p.exists():
            files['records/' + n] = p.read_bytes()
    for p in sorted((PAPER / 'records' / 'revision').glob('*.json')):
        if p.name.startswith(('CATALOG-REV', 'CHOICES-REVISION')):
            files['records/revision/' + p.name] = p.read_bytes()
    files['revision/aihwkit_curves.py'] = (PAPER / 'revision' / 'aihwkit_curves.py').read_bytes()
    if a.with_runs:  # one tar (many small files made scp time out in sitting S4's first attempt)
        import io, tarfile
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w', format=tarfile.USTAR_FORMAT) as tf:
            for ph in a.with_runs:
                rev = ph.startswith('rev:')
                ph = ph[4:] if rev else ph
                src = PAPER / 'records' / ('revision/runs' if rev else 'runs') / ph
                for f in sorted(src.glob('*.json')):
                    b = f.read_bytes()
                    ti = tarfile.TarInfo(('revision/' if rev else '') + 'runs/%s/%s' % (ph, f.name))
                    ti.size, ti.mtime, ti.mode = len(b), 0, 0o644
                    tf.addfile(ti, io.BytesIO(b))
        files['records/runs.tar'] = buf.getvalue()
    md = tasks.DATA['mnist_dir']
    for fn, want in tasks.DATA['mnist_sha'].items():
        b = open(os.path.join(md, fn), 'rb').read()
        if hashlib.sha256(b).hexdigest() != want:
            raise SystemExit('MNIST digest mismatch ' + fn)
        files['data/mnist/' + fn] = b
    src = tasks.DATA['enwik8']
    if tasks.sha256(src) != tasks.DATA['enwik8_sha']:
        raise SystemExit('enwik8 digest mismatch')
    with open(src, 'rb') as f:
        for fn, key in (('train', 'lm_train'), ('val', 'lm_val')):
            o, n = tasks.DATA[key]
            f.seek(o)
            b = f.read(n)
            if hashlib.sha256(b).hexdigest() != tasks.SLICE_SHA[fn]:
                raise SystemExit('slice digest mismatch ' + fn)
            files['slices/%s.bin' % fn] = b
    files['run.sh'] = (HERE / 'run_rev2.sh').read_bytes()
    for name, b in files.items():
        if name.endswith(('.py', '.sh', '.json')) and b'\r\n' in b:
            raise SystemExit('REFUSED: %s has CRLF bytes' % name)
    out.mkdir(parents=True)
    lines = []
    for name, b in sorted(files.items()):
        (out / name).parent.mkdir(parents=True, exist_ok=True)
        (out / name).write_bytes(b)
        lines.append('%s  %s' % (hashlib.sha256(b).hexdigest(), name))
    (out / 'MANIFEST.sha256').write_bytes(('\n'.join(lines) + '\n').encode('utf-8'))
    rec = dict(schema='x1000.me-revision.payload.v1', out=str(out).replace('\\', '/'), files=len(files),
               bytes=sum(len(b) for b in files.values()),
               manifest_sha256=hashlib.sha256((out / 'MANIFEST.sha256').read_bytes()).hexdigest())
    (out.parent / (out.name + '.PAYLOAD.json')).write_bytes((json.dumps(rec, indent=1) + '\n').encode('utf-8'))
    print(json.dumps(rec))


if __name__ == '__main__':
    main()
