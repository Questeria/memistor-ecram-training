"""ME-REVISE-4 desk runs (PLAN-REVISION-4.md section 1), on top of sweep_rev3.py (same executor, catalog, choices,
learning rates and run definitions). Run on the desk only, with ME_RECORDS pointing at a scratch records tree (never the
repository's records/: the results are copied in by name after the runs) and the free P2200.

    set ME_RECORDS=H:/x1000/memistor-paper/rev4/records
    python -B sweep_rev4.py --phase a2m|list [--workers 2] [--gpu "Quadro P2200"]

a2m   experiment A2-M: MNIST MO-ECRAM SGD as matched triples on ONE GPU: the FP-SGD control, the aggregate surrogate and the
      seq stream on every analog layer, seeds 0-4, exactly the E3 / A2 run definitions. Each seed's three runs must record the
      same init_sha256 and data_sha256 (revision4/analyze_rev4.py refuses a seed otherwise).
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sweep_rev3 as S3  # noqa: E402  (asserts ME_RECORDS is a scratch tree; sets the executor's command builder)

R, B, MO = S3.R, S3.B, S3.MO
A2M_SEEDS = [0, 1, 2, 3, 4]


def runs_a2m():
    cat = R.catalog()
    lr = R.fp_lr("mnist")
    out = []
    for s in A2M_SEEDS:
        out.append(R.run("fidm", "mnist", "fp_sgd", lr, s))
        out.append(R.run("fidm", "mnist", "device", lr, s, spec=cat[MO], algo="sgd", ucfg=R.tt("sgd")))
        out.append(R.run("fidm", "mnist", "device", lr, s, spec=cat[MO], algo="sgd", ucfg=R.tt("sgd"), extra="seq",
                         rev2=["--pulse", "seq", "--seq-layers", "all"]))
    out.sort(key=lambda nr: (not nr[1].get("rev2"), nr[1]["seed"]))  # the slow stream runs first
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["a2m", "list"])
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--gpu", default="Quadro P2200")
    ap.add_argument("--logdir", default=os.path.join(B.REC, "logs"))
    a = ap.parse_args()
    if a.phase == "list":
        for nm, _ in runs_a2m():
            print(nm)
        return
    os.environ.setdefault("OMP_NUM_THREADS", "2")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
    print("gpu", a.gpu, "index", S3.pick_gpu(a.gpu), "records", B.REC, flush=True)
    R.execute(runs_a2m(), a.workers, a.logdir)


if __name__ == "__main__":
    main()
