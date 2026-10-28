"""DEV scale check, round 2 (OUTSIDE THE PRE-REGISTRATION): at a non-default width the FP arm's lr is re-chosen on
VALIDATION from the task's pre-registered grid, then FP and the two ECRAM-class devices (TTv2) run on test at that lr.
python -B scale_lr.py --task cifar --width 64 [--workers 3]  -> ../records/runs/<task>-scale-DEV/lr*/...
"""
import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from sweep import LR_GRID, REC, catalog, ttcfg  # noqa: E402

PY = sys.executable


def run_all(cmds, workers):
    live = []
    for c in cmds:
        while len(live) >= workers:
            live = [p for p in live if p.poll() is None]
            if len(live) >= workers:
                live[0].wait()
        live.append(subprocess.Popen(c, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    for p in live:
        p.wait()


def base(task, width, seed, split, lr, out, extra=()):
    return [PY, "-B", os.path.join(HERE, "run.py"), "--task", task, "--width", str(width), "--seed", str(seed),
            "--split", split, "--lr", repr(lr), "--out", out, "--tag", os.path.basename(out)[:-5]] + list(extra)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True)
    ap.add_argument("--width", type=int, required=True)
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    d = os.path.join(REC, "runs", a.task + "-scale-DEV", f"lrsel_w{a.width}")
    os.makedirs(d, exist_ok=True)
    cmds = []
    for lr in LR_GRID[a.task]:
        o = os.path.join(d, f"lrsel_fp_w{a.width}_lr{lr:g}.json")
        if not os.path.exists(o):
            cmds.append(base(a.task, a.width, 0, "val", lr, o, ["--arm", "fp_sgd"]))
    run_all(cmds, a.workers)
    best = None
    for lr in LR_GRID[a.task]:
        r = json.load(open(os.path.join(d, f"lrsel_fp_w{a.width}_lr{lr:g}.json")))
        m = r["metric"]
        s = m["acc"] if "acc" in m else -m["bpb"]
        if r.get("diverged") or s != s:
            s = -1e9
        if best is None or s > best[0]:
            best = (s, lr)
    lr = best[1]
    cat, tt = catalog(), ttcfg()
    cmds = [base(a.task, a.width, 0, "test", lr, os.path.join(d, f"FP_w{a.width}__s0.json"), ["--arm", "fp_sgd"])]
    for k in ("protonic_onen2022", "ecram_li_tang2018"):
        cmds.append(base(a.task, a.width, 0, "test", lr, os.path.join(d, f"CAT_{k}_w{a.width}__ttv2__s0.json"),
                         ["--algo", "ttv2", "--spec", json.dumps(dict(cat[k]["spec"], name=k)), "--ucfg", json.dumps(tt)]))
    cmds = [c for c in cmds if not os.path.exists(c[c.index("--out") + 1])]
    run_all(cmds, a.workers)
    with open(os.path.join(d, "LR-CHOICE.json"), "wb") as f:
        f.write((json.dumps(dict(task=a.task, width=a.width, lr=lr), indent=1) + "\n").encode("utf-8"))
    print(json.dumps(dict(task=a.task, width=a.width, lr=lr)))


if __name__ == "__main__":
    main()
