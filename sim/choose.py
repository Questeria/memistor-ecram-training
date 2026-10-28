"""Write the pre-registered selections from VALIDATION records only.

python -B choose.py lr <task>   -> ../records/LR-CHOICE.json[task] (best FP val metric over LR_GRID)
python -B choose.py tt          -> ../records/TT-CHOICE.json (best TTv2 val acc on MNIST with MID_DEVICE)
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sweep import LR_GRID, REC, TT_GRID, jload, ttsel_name  # noqa: E402


def score(rec):
    m = rec["metric"]
    assert m["split"] == "val", "selection must use validation records"
    if rec.get("diverged"):
        return -math.inf
    return m["acc"] if "acc" in m else -m["bpb"]


def write(name, task, val):
    p = os.path.join(REC, name)
    d = jload(p) if os.path.exists(p) else {}
    if task is None:
        d = val
    else:
        d[task] = val
    with open(p, "wb") as f:
        f.write((json.dumps(d, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    print(name, json.dumps(val))


def main():
    kind = sys.argv[1]
    if kind == "lr":
        task = sys.argv[2]
        rows = []
        for lr in LR_GRID[task]:
            r = jload(os.path.join(REC, "runs", task, f"lrsel_fp_lr{lr:g}.json"))
            rows.append((score(r), lr, r["metric"]))
        best = max(rows)
        write("LR-CHOICE.json", task, dict(lr=best[1], grid=[dict(lr=l, val=m) for _, l, m in rows]))
    elif kind == "tt":
        rows = []
        for i, g in enumerate(TT_GRID):
            r = jload(os.path.join(REC, "runs", "mnist", ttsel_name(g) + ".json"))
            rows.append((score(r), -i, g, r["metric"]["acc"]))  # ties: the earlier (pre-registered) arm
        sgd = jload(os.path.join(REC, "runs", "mnist", "ttsel_sgd_ref.json"))["metric"]["acc"]
        best = max(rows, key=lambda t: (t[0], t[1]))
        write("TT-CHOICE.json", None, dict(best[2], sgd_ref_val_acc=sgd,
                                          grid=[dict(g, val_acc=c) for _, _, g, c in rows]))


if __name__ == "__main__":
    main()
