"""ME-REVISE-3 desk runs (PLAN-REVISION-3.md sections 1 and 2), on top of sweep_rev2.py (same executor, catalog, choices,
learning rates and run definitions). Run on the desk only, with ME_RECORDS pointing at a scratch records tree (never the
repository's records/: the results are copied in by name after the runs) and the desk's spare GPU.

    set ME_RECORDS=H:/x1000/memistor-paper/rev3/records  ME_CIFAR=<cifar-10-batches-py>
    python -B sweep_rev3.py --phase a1p|a2r|list [--workers 2] [--gpu "Quadro P2000"] [--draws-dir DIR]

a1p   experiment A1-P: the three probe runs of A1 (MNIST Li-ECRAM c-TTv2, CIFAR MO-ECRAM AGAD, LM protonic-inspired c-TTv2;
      seed 0, surrogate training identical to E3) with run_rev3.py's paired probe; draws 16 on every task (R7).
a2r   experiment A2-R: MNIST MO-ECRAM SGD with the seq stream on every analog layer, seeds 3 and 4, and seed 0 again as the
      cross-hardware reproduction of the pod record.
"""
import argparse
import ctypes
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
assert os.environ.get("ME_RECORDS"), "set ME_RECORDS to a scratch records tree (never the repository's records/)"
assert os.path.abspath(os.environ["ME_RECORDS"]) != os.path.abspath(os.path.join(HERE, "..", "records"))
import sweep_rev2 as S2  # noqa: E402

R, B = S2.R, S2.B
LI, MO, PR = S2.LI, S2.MO, S2.PR
A1P = [(t, d, al, layers, steps, 16) for (t, d, al, layers, steps, _draws) in S2.PROBES]
A2R_SEEDS = [3, 4, 0]


def cmd3(name, r, outdir):
    c = S2.cmd2(name, r, outdir)
    if r.get("rev3"):
        c[2] = os.path.join(HERE, "run_rev3.py")
        c += list(r["rev3"])
    return c


B.cmd = cmd3


def phase_a1p(a):
    cat = R.catalog()
    pdir = os.path.join(B.REC, "runs", "fidprobe3-probes")
    os.makedirs(pdir, exist_ok=True)
    runs = []
    for t, d, al, layers, steps, draws in A1P:
        nm, r = R.run("fidprobe3", t, "device", R.fp_lr(t), 0, spec=cat[d], algo=al, ucfg=R.tt(al), extra="probe")
        r["rev2"] = ["--probe-layers", layers, "--probe-steps", steps, "--probe-draws", str(draws),
                     "--probe-out", os.path.join(pdir, nm + ".probes.json")]
        r["rev3"] = ["--probe-boot", "2000", "--draws-dir", a.draws_dir]
        runs.append((nm, r))
    runs.sort(key=lambda nr: nr[1]["task"] != "lm")  # the slowest first
    R.execute(runs, a.workers, a.logdir)


def phase_a2r(a):
    cat = R.catalog()
    runs = [R.run("fidr", "mnist", "device", R.fp_lr("mnist"), s, spec=cat[MO], algo="sgd", ucfg=R.tt("sgd"), extra="seq",
                  rev2=["--pulse", "seq", "--seq-layers", "all"]) for s in A2R_SEEDS]
    R.execute(runs, a.workers, a.logdir)


def pick_gpu(name):
    """Expose only the named GPU (PCI order), checked by name, and lower this process tree's priority (BelowNormal)."""
    out = subprocess.run(["nvidia-smi", "--query-gpu=index,name", "--format=csv,noheader"], capture_output=True, text=True,
                         check=True).stdout
    idx = [ln.split(",")[0].strip() for ln in out.splitlines() if ln.split(",")[1].strip() == name]
    assert len(idx) == 1, (name, out)
    os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
    os.environ["CUDA_VISIBLE_DEVICES"] = idx[0]
    chk = subprocess.run([sys.executable, "-c", "import torch;print(torch.cuda.get_device_name(0))"], capture_output=True,
                         text=True, check=True).stdout.strip()
    assert chk == name, (chk, name)
    if os.name == "nt":
        k = ctypes.windll.kernel32
        k.SetPriorityClass(k.GetCurrentProcess(), 0x00004000)  # BELOW_NORMAL_PRIORITY_CLASS, inherited by the runs
    return idx[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["a1p", "a2r", "list"])
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--gpu", default="Quadro P2000")
    ap.add_argument("--draws-dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "draws", "rev3"))
    ap.add_argument("--logdir", default=os.path.join(B.REC, "logs"))
    a = ap.parse_args()
    if a.phase == "list":
        print(dict(a1p=len(A1P), a2r=len(A2R_SEEDS)))
        return
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
    print("gpu", a.gpu, "index", pick_gpu(a.gpu), "records", B.REC, flush=True)
    {"a1p": phase_a1p, "a2r": phase_a2r}[a.phase](a)


if __name__ == "__main__":
    main()
