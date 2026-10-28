"""The pre-registered run lists of lane ME (PLAN.md) and a small parallel executor.

python -B sweep.py --phase lrsel --task mnist --workers 2
phases: lrsel (FP lr on val) | ttsel (TTv2 lambda x period on MNIST val) | grid (sweeps A-F + catalog + FP) |
        minspec (joint minimum spec rounds, written by verdict.py into records/MINSPEC-CANDIDATES.json) |
        pod (CIFAR / LM lists)
Records: ../records/runs/<task>/<name>.json; an existing record is never re-run.
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.environ.get("ME_RECORDS") or os.path.join(HERE, "..", "records")  # the pod writes into $OUT/records
PY = sys.executable

LR_GRID = {"mnist": [3e-4, 1e-3, 3e-3], "cifar": [1e-4, 3e-4, 1e-3], "lm": [3e-5, 1e-4, 3e-4]}
TT_GRID = [dict(tt_lambda=l, tt_period=p) for l in (0.3, 1.0, 3.0) for p in (16, 64)]
TT_GRID += [dict(tt_lambda=l, tt_period=p, tt_lr_ratio=1.0 / l) for l in (0.1, 0.3) for p in (16, 64)]  # DEVIATIONS.md D2
MID_DEVICE = dict(n_states=128, asym=0.1, gamma_up=0.3, gamma_dn=0.3, c2c=0.5, ref_err=0.02, name="mid_ttsel")
ALGOS = ("sgd", "ttv2")


def jload(p):
    with open(p, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


def choice(kind, task):
    p = os.path.join(REC, f"{kind}-CHOICE.json")
    if not os.path.exists(p):
        raise SystemExit(f"missing {p}: run the selection phase first")
    d = jload(p)
    return d[task] if task in d else d


def ttcfg():
    c = choice("TT", "mnist")
    d = dict(tt_lambda=c["tt_lambda"], tt_period=c["tt_period"])
    if c.get("tt_lr_ratio"):
        d["tt_lr_ratio"] = c["tt_lr_ratio"]
    return d


def spec_name(s):
    keys = ["n_states", "asym", "gamma_up", "gamma_dn", "c2c", "tau_steps", "ref_err"]
    return "_".join(f"{k.replace('_', '')}{s[k]:g}" for k in keys if k in s) or "ideal"


def runs_lrsel(task):
    return [(f"lrsel_fp_lr{lr:g}", dict(task=task, arm="fp_sgd", lr=lr, split="val", seed=0)) for lr in LR_GRID[task]]


def ttsel_name(g):
    r = g.get("tt_lr_ratio")
    return f"ttsel_lam{g['tt_lambda']:g}_per{g['tt_period']}" + (f"_lrx{r:.4g}" if r else "")


def runs_ttsel():
    lr = choice("LR", "mnist")["lr"]
    out = []
    for g in TT_GRID:
        out.append((ttsel_name(g), dict(
            task="mnist", arm="device", algo="ttv2", spec=MID_DEVICE, ucfg=g, lr=lr, split="val", seed=0)))
    out.append(("ttsel_sgd_ref", dict(task="mnist", arm="device", algo="sgd", spec=MID_DEVICE, lr=lr, split="val", seed=0)))
    return out


def catalog():
    sys.path.insert(0, HERE)
    import devices
    return devices.CATALOG


def dev_runs(task, specs, seeds, lr, tt):
    out = []
    for name, s in specs:
        for algo in ALGOS:
            for seed in seeds:
                u = tt if algo == "ttv2" else {}
                out.append((f"{name}__{algo}__s{seed}", dict(task=task, arm="device", algo=algo, spec=s, ucfg=u,
                                                            lr=lr, split="test", seed=seed)))
    return out


def runs_grid_mnist():
    lr, tt = choice("LR", "mnist")["lr"], ttcfg()
    specs = []
    for n in (16, 32, 64, 128, 256, 1024, 4096):
        specs.append((f"A_states{n}", dict(n_states=n)))
    for a in (0.01, 0.03, 0.1, 0.3):
        for n in (64, 256, 1024):
            specs.append((f"B_asym{a:g}_states{n}", dict(n_states=n, asym=a)))
    for g in (0.1, 0.3, 0.6, 1.0):
        for n in (64, 256, 1024):
            specs.append((f"C_gamma{g:g}_states{n}", dict(n_states=n, gamma_up=g, gamma_dn=g)))
    for c in (0.3, 1.0, 3.0):
        for n in (64, 256, 1024):
            specs.append((f"D_c2c{c:g}_states{n}", dict(n_states=n, c2c=c)))
    for t in (1e2, 1e3, 1e4, 1e5):
        specs.append((f"E_tau{t:g}_states256", dict(n_states=256, tau_steps=t)))
    for r in (0.01, 0.05):
        specs.append((f"F_ref{r:g}_states256", dict(n_states=256, asym=0.1, gamma_up=0.3, gamma_dn=0.3, ref_err=r)))
    out = dev_runs("mnist", specs, [0], lr, tt)
    cat = [(f"CAT_{k}", dict(v["spec"], name=k)) for k, v in catalog().items()]
    out += dev_runs("mnist", cat, [0, 1, 2], lr, tt)
    out += [(f"FP__s{s}", dict(task="mnist", arm="fp_sgd", lr=lr, split="test", seed=s)) for s in (0, 1, 2)]
    return out


def runs_minspec(task):
    p = os.path.join(REC, "MINSPEC-CANDIDATES.json")
    d = jload(p)
    lr, tt = choice("LR", task)["lr"], ttcfg()
    out = []
    for algo, rounds in d["candidates"].items():
        for i, s in enumerate(rounds):
            if task != "mnist" and i != len(rounds) - 1:
                continue  # CIFAR / LM run only the verified (last) round (PLAN.md)
            seeds = [0, 1, 2] if task == "mnist" else [0]
            for seed in seeds:
                u = tt if algo == "ttv2" else {}
                out.append((f"MIN{i}__{algo}__s{seed}", dict(task=task, arm="device", algo=algo, spec=s, ucfg=u, lr=lr,
                                                           split="test", seed=seed)))
    return out


def runs_pod(task):
    lr, tt = choice("LR", task)["lr"], ttcfg()
    specs = [(f"A_states{n}", dict(n_states=n)) for n in (32, 128, 1024)]
    specs += [("B_asym0.1_states1024", dict(n_states=1024, asym=0.1)),
              ("C_gamma0.3_states1024", dict(n_states=1024, gamma_up=0.3, gamma_dn=0.3)),
              ("D_c2c1_states1024", dict(n_states=1024, c2c=1.0))]
    specs += [(f"CAT_{k}", dict(v["spec"], name=k)) for k, v in catalog().items()]
    cat = [s for s in specs if s[0].startswith("CAT_")]
    rest = [s for s in specs if not s[0].startswith("CAT_")]
    out = [(f"FP__s{s}", dict(task=task, arm="fp_sgd", lr=lr, split="test", seed=s)) for s in (0, 1)]
    out += dev_runs(task, cat, [0], lr, tt) + dev_runs(task, rest, [0], lr, tt)
    if task == "lm":
        out += [(f"ADAM__s0", dict(task=task, arm="fp_adam", lr=1e-3, split="test", seed=0))]
    return out


def runs_podall(tasks_avail):
    """The pod's single merged list, by priority: FP of both tasks, the catalog, the MNIST minimum specs, the rest."""
    per = {t: runs_pod(t) for t in tasks_avail}
    have_min = os.path.exists(os.path.join(REC, "MINSPEC-CANDIDATES.json"))
    mins = {t: (runs_minspec(t) if have_min else []) for t in tasks_avail}
    out = []
    for key in (lambda n: n.startswith(("FP__", "ADAM__")), lambda n: n.startswith("CAT_")):
        for t in tasks_avail:
            out += [(n, r) for n, r in per[t] if key(n)]
    for t in tasks_avail:
        out += mins[t]
    for t in tasks_avail:
        out += [(n, r) for n, r in per[t] if not n.startswith(("FP__", "ADAM__", "CAT_"))]
    return out


def runs_seed2(tasks_avail):
    """PLAN.md: a second seed wherever a CIFAR / LM catalog gap is within a quarter of its threshold (rule applied to
    records/RESULTS.json), plus one more FP seed per task (DEVIATIONS.md D3: a sensitivity check, reported apart)."""
    res = jload(os.path.join(REC, "RESULTS.json"))
    thr = {"cifar": 2.0, "lm": 5.0}
    out = []
    for t in tasks_avail:
        lr, tt = choice("LR", t)["lr"], ttcfg()
        for k, e in res["catalog"].items():
            for algo in ALGOS:
                g = (e["gaps"].get(t) or {}).get(algo)
                if g and abs(g["gap"] - thr[t]) < thr[t] / 4:
                    u = tt if algo == "ttv2" else {}
                    out.append((f"CAT_{k}__{algo}__s1", dict(task=t, arm="device", algo=algo, spec=dict(e["spec"], name=k),
                                                             ucfg=u, lr=lr, split="test", seed=1)))
        out.append(("FPSENS__s2", dict(task=t, arm="fp_sgd", lr=lr, split="test", seed=2)))
    return out


def runs_scale(tasks_avail):
    """DEV, OUTSIDE THE PRE-REGISTRATION (director's item c): the two ECRAM-class devices under TTv2 and the FP arm at
    other widths. CIFAR: base channels 16 and 64 (pre-registered 32); LM: d 64 and 256 (pre-registered 128)."""
    cat = catalog()
    widths = {"cifar": (16, 64), "lm": (64, 256)}
    out = []
    for t in tasks_avail:
        lr, tt = choice("LR", t)["lr"], ttcfg()
        for w in widths[t]:
            out.append((f"FP_w{w}__s0", dict(task=t, arm="fp_sgd", lr=lr, split="test", seed=0, width=w, sub="-scale-DEV")))
            for k in ("protonic_onen2022", "ecram_li_tang2018"):
                out.append((f"CAT_{k}_w{w}__ttv2__s0", dict(task=t, arm="device", algo="ttv2", spec=dict(cat[k]["spec"], name=k),
                                                            ucfg=tt, lr=lr, split="test", seed=0, width=w, sub="-scale-DEV")))
    return out


def cmd(name, r, outdir):
    c = [PY, "-B", os.path.join(HERE, "run.py"), "--task", r["task"], "--arm", r["arm"], "--lr", repr(r["lr"]),
         "--seed", str(r.get("seed", 0)), "--split", r.get("split", "test"), "--tag", name,
         "--out", os.path.join(outdir, name + ".json")]
    if "algo" in r:
        c += ["--algo", r["algo"]]
    if r.get("spec"):
        c += ["--spec", json.dumps(r["spec"])]
    if r.get("ucfg"):
        c += ["--ucfg", json.dumps(r["ucfg"])]
    if r.get("width"):
        c += ["--width", str(r["width"])]
    if os.environ.get("ME_SCALE"):  # dry rehearsals only: shrink every budget
        c += ["--scale", os.environ["ME_SCALE"]]
    return c


def execute(runs, task, workers, logdir, deadline=None):
    od = lambda r: os.path.join(REC, "runs", r["task"] + r.get("sub", ""))
    for _, r in runs:
        os.makedirs(od(r), exist_ok=True)
    os.makedirs(logdir, exist_ok=True)
    todo = [(n, r) for n, r in runs if not os.path.exists(os.path.join(od(r), n + ".json"))]
    r_of = dict(runs)
    print(f"{len(runs)} runs, {len(todo)} to do", flush=True)
    live, fails = [], []
    est = {}  # seconds of the longest finished run per algo+arm (a run is not started if it cannot finish)
    while todo or live:
        while todo and len(live) < workers:
            if deadline and time.time() + est.get(todo[0][1].get("algo", "sgd") + todo[0][1]["arm"], 0) > deadline:
                print(f"deadline: {len(todo)} runs not started: {[n for n, _ in todo]}", flush=True)
                todo = []
                break
            n, r = todo.pop(0)
            lf = open(os.path.join(logdir, r["task"] + "__" + n + ".log"), "wb")
            flags = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW
            p = subprocess.Popen(cmd(n, r, od(r)), stdout=lf, stderr=subprocess.STDOUT, creationflags=flags)
            live.append((n, p, lf, time.time()))
        time.sleep(1.0)
        for item in list(live):
            n, p, lf, t0 = item
            if p.poll() is not None:
                lf.close(); live.remove(item)
                ok = p.returncode == 0
                key = r_of[n].get("algo", "sgd") + r_of[n]["arm"]
                est[key] = max(est.get(key, 0), time.time() - t0)
                if not ok:
                    fails.append(n)
                print(f"{'done' if ok else 'FAIL'} {n} {time.time() - t0:.0f}s", flush=True)
    print(f"finished; failures: {fails}", flush=True)
    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["lrsel", "ttsel", "grid", "minspec", "pod", "podall", "seed2", "scale"])
    ap.add_argument("--task", default="mnist")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--logdir", default=os.path.join(HERE, "..", "scratch", "logs"))
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--deadline-epoch", type=float, default=None)
    a = ap.parse_args()
    runs = {"lrsel": lambda: runs_lrsel(a.task), "ttsel": runs_ttsel, "grid": runs_grid_mnist,
            "minspec": lambda: runs_minspec(a.task), "pod": lambda: runs_pod(a.task),
            "podall": lambda: runs_podall(a.task.split(",")), "seed2": lambda: runs_seed2(a.task.split(",")),
            "scale": lambda: runs_scale(a.task.split(","))}[a.phase]()
    if a.list:
        for n, r in runs:
            print(n)
        print(len(runs))
        return
    fails = execute(runs, a.task, a.workers, a.logdir, a.deadline_epoch)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
