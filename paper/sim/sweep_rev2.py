"""ME-REVISE-2 run lists (PLAN-REVISION-2.md), on top of sweep_rev.py (same executor, catalog, choices and learning rates).

    python -B sweep_rev2.py --phase e5fix|fid|fidprobe|list --workers 8

e5fix     experiment B: the recentred fixed-symmetry base (asymmetry 0.05) and the omitted zero point, protonic-inspired base
          device, TTv2 and c-TTv2, CIFAR c = 32 and LM d = 128, seeds 0-2, FP-SGD's learning rate (as E5): 24 runs.
fid       experiment A2: training with the explicit `seq` pulse stream (run_rev2.py --pulse seq), seeds 0-2. MNIST, every
          analog layer: Li-ECRAM, MO-ECRAM, protonic-inspired x SGD, c-TTv2, AGAD (27 runs). CIFAR, the two fully connected
          layers (3, 4; the convolutions keep the surrogate): Li-ECRAM c-TTv2, MO-ECRAM AGAD, protonic-inspired c-TTv2 (9 runs).
fidprobe  experiment A1: surrogate training (identical to E3) with update-fidelity probes, seed 0: MNIST Li-ECRAM c-TTv2
          (layers 0, 2), CIFAR MO-ECRAM AGAD (layers 3, 4), LM protonic-inspired c-TTv2 (layers 0, 9); 3 runs.
Probe files go to <records>/revision/runs/fidprobe-probes/.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sweep_rev as R  # noqa: E402

B = R.B
SEEDS3 = [0, 1, 2]
LI, MO, PR = "ecram_li_tang2018", "ecram_mo_kim2019", "protonic_onen2022"
FID_MNIST = [(d, al) for d in (LI, MO, PR) for al in ("sgd", "cttv2", "agad")]
FID_CIFAR = [(LI, "cttv2"), (MO, "agad"), (PR, "cttv2")]
PROBES = [("mnist", LI, "cttv2", "0,2", "1000,3500", 16), ("cifar", MO, "agad", "3,4", "600,2000", 16),
          ("lm", PR, "cttv2", "0,9", "750,2250", 6)]
FIX_POINTS = [0.05, 0.0]


def cmd2(name, r, outdir):
    c = R.cmd(name, r, outdir)
    if r.get("rev2"):
        c[2] = os.path.join(HERE, "run_rev2.py")
        c += list(r["rev2"])
    return c


B.cmd = cmd2


def phase_e5fix(a):
    base = dict(R.catalog()[PR])
    runs = []
    for t in [x for x in a.task.split(",") if x in ("cifar", "lm")]:
        for s in SEEDS3:
            for al in ("ttv2", "cttv2"):
                for v in FIX_POINTS:
                    nm = f"asym_fixedsp{B.fmt(v)}"
                    sp = dict(base, asym=v, recenter_sp=True, name=nm)
                    runs.append(R.run("e5fix", t, "device", R.fp_lr(t), s, spec=sp, algo=al, ucfg=R.tt(al)))
    runs.sort(key=lambda nr: (nr[1]["seed"], nr[1]["task"]))
    R.execute(runs, a.workers, a.logdir, a.deadline_epoch)


def phase_fid(a):
    cat = R.catalog()
    runs = []
    for s in SEEDS3:
        for t, cells, layers in (("mnist", FID_MNIST, "all"), ("cifar", FID_CIFAR, "3,4")):
            if t not in a.task.split(","):
                continue
            for d, al in cells:
                runs.append(R.run("fid", t, "device", R.fp_lr(t), s, spec=cat[d], algo=al, ucfg=R.tt(al), extra="seq",
                                  rev2=["--pulse", "seq", "--seq-layers", layers]))
    R.execute(runs, a.workers, a.logdir, a.deadline_epoch)


def phase_fidprobe(a):
    cat = R.catalog()
    pdir = os.path.join(B.REC, "runs", "fidprobe-probes")
    os.makedirs(pdir, exist_ok=True)
    runs = []
    for t, d, al, layers, steps, draws in PROBES:
        if t not in a.task.split(","):
            continue
        nm, r = R.run("fidprobe", t, "device", R.fp_lr(t), 0, spec=cat[d], algo=al, ucfg=R.tt(al), extra="probe")
        r["rev2"] = ["--probe-layers", layers, "--probe-steps", steps, "--probe-draws", str(draws),
                     "--probe-out", os.path.join(pdir, nm + ".probes.json")]
        runs.append((nm, r))
    runs.sort(key=lambda nr: nr[1]["task"] != "lm")  # the slowest (LM probes) first
    R.execute(runs, a.workers, a.logdir, a.deadline_epoch)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["e5fix", "fid", "fidprobe", "list"])
    ap.add_argument("--task", default="mnist,cifar,lm")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--logdir", default=os.path.join(B.REC, "logs"))
    ap.add_argument("--deadline-epoch", type=float, default=None)
    a = ap.parse_args()
    if a.phase == "list":
        n = dict(e5fix=2 * 3 * 2 * len(FIX_POINTS), fid=3 * (len(FID_MNIST) + len(FID_CIFAR)), fidprobe=len(PROBES))
        print(n, sum(n.values()))
        return
    {"e5fix": phase_e5fix, "fid": phase_fid, "fidprobe": phase_fidprobe}[a.phase](a)


if __name__ == "__main__":
    main()
