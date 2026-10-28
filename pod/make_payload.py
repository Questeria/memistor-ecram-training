"""Build lane ME's pod payload (devpod --payload DIR), modelled on bench/pod/make_payload.py.

    python -B pod/make_payload.py --out H:/x1000/memistor/payload/sitting-1

Holds: sim/*.py, the selection and catalog records, the two pinned enwik8 slices (re-cut here from the pinned enwik8 and
checked against tasks.SLICE_SHA), run.sh and MANIFEST.sha256 over every other file. CIFAR-10 is fetched by the pod itself
(md5 pinned in run.sh). Refuses an existing --out and any CRLF in code.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LANE = HERE.parent
sys.path.insert(0, str(LANE / 'sim'))
import tasks  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        raise SystemExit('REFUSED: %s exists (a payload is built once)' % out)
    files = {}
    for f in sorted((LANE / 'sim').glob('*.py')):
        files['sim/' + f.name] = f.read_bytes()
    for n in ('CATALOG.json', 'TT-CHOICE.json', 'LR-CHOICE.json', 'MINSPEC-CANDIDATES.json', 'RESULTS.json'):
        p = LANE / 'records' / n
        if p.exists():
            files['records/' + n] = p.read_bytes()
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
    files['run.sh'] = (HERE / 'run.sh').read_bytes()
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
    rec = dict(schema='x1000.me.payload.v1', out=str(out).replace('\\', '/'), files=len(files),
               bytes=sum(len(b) for b in files.values()),
               manifest_sha256=hashlib.sha256((out / 'MANIFEST.sha256').read_bytes()).hexdigest())
    (out.parent / (out.name + '.PAYLOAD.json')).write_bytes((json.dumps(rec, indent=1) + '\n').encode('utf-8'))
    print(json.dumps(rec))


if __name__ == '__main__':
    main()
