"""Version 11 check (review 8, finding 3): the ideal reset of a PARTIAL column selection on an aihwkit-bounds tile. It must PASS
on the repaired code and is shown to FAIL on the old behaviour (the pattern of test_rev.py). CPU only.

    python -B test_ideal_reset_cols.py --out ../records/revision10/TESTS-IDEAL-RESET-COLS.json
  c_ideal_reset_cols  AnalogLinear(4, 3), bounds_model 'aihwkit', tt_reset 'ideal', one column per transfer: four transfers reset
                      columns 0, 1, 2, 3 in turn, each to its symmetry point plus one pulse of write noise clipped to that column's
                      own bounds, leave the other columns alone and charge 2 BL pulses per reset weight
                      [fails: the old line, which clipped the selected columns against the whole tile's bounds and crashed]

No deposited result used this combination (it could not have run); the check guards the simulator's supported configuration.
"""
import argparse
import json
import os
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import memsim_rev as R  # noqa: E402
from test_rev import DEV, LI_AIHW  # noqa: E402


def c_ideal_reset_cols(whole_tile_bounds=False):
    st = R.Streams(0, "split", DEV)
    uc = R.UpdateCfg(lr=1e-3, algo="ttv2", tt_lambda=0.1, tt_period=1, tt_cols=1, tt_reset="ideal")
    m = R.AnalogLinear(4, 3, R.DeviceSpec(**LI_AIHW), uc, st.noise, DEV, streams=st)
    if whole_tile_bounds:  # the planted fault: the old line's bounds
        m.A.clip_cols = lambda u, idx: m.A.clip(u)
    rows = []
    for col in range(4):
        n0 = float(m.n_reset_pulses)
        m.A.u.fill_(0.5)  # off the symmetry point, so a reset shows
        u0 = m.A.u.clone()
        m._transfer()
        changed = sorted({int(j) for j in torch.nonzero(m.A.u != u0)[:, 1]})
        lo, hi = m.A.lo[:, col], m.A.hi[:, col]
        inside = bool(((m.A.u[:, col] >= lo) & (m.A.u[:, col] <= hi)).all())
        near = float((m.A.u[:, col] - m.A.ustar[:, col]).abs().max()) <= 6 * m.A.spec.c2c * m.A.k_nom + 1e-12  # one pulse of noise
        charged = float(m.n_reset_pulses) - n0
        rows.append(dict(col=col, changed_cols=changed, inside_bounds=inside, near_symmetry_point=near, charged=charged))
    ok = all(r["changed_cols"] == [r["col"]] and r["inside_bounds"] and r["near_symmetry_point"]
             and r["charged"] == 3 * 2 * uc.BL for r in rows)
    return ok, rows


CHECKS = {"c_ideal_reset_cols": c_ideal_reset_cols}
FAULTS = {"f_whole_tile_bounds": ("c_ideal_reset_cols", lambda: c_ideal_reset_cols(whole_tile_bounds=True))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    torch.set_num_threads(2)
    out = dict(schema="altone.x1000.me-paper.v11.tests.v1", torch=torch.__version__, checks={}, faults={})
    for n, f in CHECKS.items():
        ok, det = f()
        out["checks"][n] = dict(ok=bool(ok), detail=det)
        print(n, "OK" if ok else "FAIL", flush=True)
    for n, (cn, f) in FAULTS.items():
        try:
            ok, det = f()
            caught = not ok
        except Exception as e:  # a crash on the planted fault also counts as caught
            caught, det = True, dict(exception=repr(e)[:300])
        out["faults"][n] = dict(check=cn, caught=bool(caught), detail=det)
        print(n, "CAUGHT" if caught else "MISSED", flush=True)
    out["all_ok"] = all(c["ok"] for c in out["checks"].values()) and all(f["caught"] for f in out["faults"].values())
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "wb") as f:
        f.write((json.dumps(out, indent=1, sort_keys=True, default=str) + "\n").encode("utf-8"))
    print("ALL_OK" if out["all_ok"] else "NOT_OK")
    sys.exit(0 if out["all_ok"] else 1)


if __name__ == "__main__":
    main()
