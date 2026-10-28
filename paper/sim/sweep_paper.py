"""The pre-registered run lists of lane ME-PAPER (PLAN-PAPER.md) and their executor.

python -B sweep_paper.py --phase e2 --workers 2            (desk: MNIST lr edge rule + TT-family selection)
python -B sweep_paper.py --phase e1 --workers 8            (pod: E1 + E1b)
python -B sweep_paper.py --phase fplr --workers 8          (pod: E4 step 1 + LM Adam lr, every width)
python -B sweep_paper.py --phase e3 | e4 | e5 ...          (pod)
Records: $ME_RECORDS/runs/<phase>/<name>.json (default ../records); an existing record is never re-run.
Choices: $ME_RECORDS/CHOICES-PAPER.json (written only from VALIDATION records).
"""
import argparse
import json
import math
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.environ.get("ME_RECORDS") or os.path.join(HERE, "..", "records")
PY = sys.executable
CHO = os.path.join(REC, "CHOICES-PAPER.json")

LR_GRID = {"mnist": [3e-4, 1e-3, 3e-3], "cifar": [1e-4, 3e-4, 1e-3, 3e-3], "lm": [1e-5, 3e-5, 1e-4, 3e-4]}
ADAM_GRID = [3e-4, 1e-3, 3e-3]
BASE_W = {"cifar": 32, "lm": 128, "mnist": 128}
WIDTHS = {"cifar": [16, 32, 64], "lm": [64, 128, 256]}
WIDTH4 = {"cifar": 128, "lm": 512}
MID_DEVICE = dict(n_states=128, asym=0.1, gamma_up=0.3, gamma_dn=0.3, c2c=0.5, ref_err=0.02, name="mid_ttsel")
LANE_ME_TT_GRID = [dict(tt_lambda=l, tt_period=p) for l in (0.3, 1.0, 3.0) for p in (16, 64)]
LANE_ME_TT_GRID += [dict(tt_lambda=l, tt_period=p, tt_lr_ratio=1.0 / l) for l in (0.1, 0.3) for p in (16, 64)]
CTT_GRID = [dict(tt_lambda=l, tt_lr_ratio=1.0 / l, tt_period=16, tt_rho=r, tt_reset=rs)
            for l in (0.1, 0.3) for r in (0.05, 0.2) for rs in (False, True)]
AGAD_GRID = [dict(tt_lambda=l, tt_lr_ratio=1.0 / l, tt_period=16, tt_rho=r, agad_beta=b, tt_reset=False)
             for l in (0.1, 0.3) for r in (0.05, 0.2) for b in (0.3, 1.0)]
MAIN_DEVICES = ["ecram_li_tang2018", "ecram_mo_kim2019", "protonic_onen2022", "wox_ysz_chen2023", "widrow1960_claimed"]
ALGOS = ["sgd", "ttv2", "cttv2", "agad"]
SEEDS5 = [0, 1, 2, 3, 4]
GH_ALPHA = 1.0 / 1.66
GH_DEVICE = dict(n_states=2 * GH_ALPHA / 1e-3, d2d=0.3, gamma_up=1.0, gamma_dn=1.0, gamma_d2d=0.42 / 1.66, c2c=0.3,
                 name="gh2020_rpu_baseline")
RASCH_DEVICE = dict(n_states=20, d2d=0.3, gamma_up=1.0, gamma_dn=1.0, gamma_d2d=0.42 / 1.66, c2c=0.3, name="rasch20")
TTV1_GH = dict(tt_lambda=0.02, tt_gamma=1.0, tt_cols=16, tt_reset=False, tt_lr_ratio=1.0)
# E5
OAT = {"n_states": [100, 200, 500, 1000, 2000, 5000], "asym": [0, 0.05, 0.1, 0.2, 0.4], "gamma": [0, 0.2, 0.5, 1, 2],
       "c2c": [0, 0.3, 1, 2, 4], "tau_steps": [math.inf, 1e5, 1e4, 1e3, 1e2], "ref_err": [0, 0.02, 0.05, 0.1, 0.2, 0.5]}
PAIR_LEVELS = {"n_states": [500, 200], "asym": [0.1, 0.2], "gamma": [0.5, 1], "c2c": [1, 2], "tau_steps": [1e4, 1e3],
               "ref_err": [0.05, 0.1]}
GAP_LINE = {"mnist": 2.0, "cifar": 2.0, "lm": 5.0}


def jload(p):
    with open(p, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


def jsave(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write((json.dumps(d, indent=1, sort_keys=True) + "\n").encode("utf-8"))


def choices():
    return jload(CHO) if os.path.exists(CHO) else {}


def set_choice(path, val):
    d = choices()
    cur = d
    for k in path[:-1]:
        cur = cur.setdefault(k, {})
    cur[path[-1]] = val
    jsave(CHO, d)
    print("choice", "/".join(path), json.dumps(val), flush=True)


def catalog():
    c = jload(os.path.join(HERE, "..", "records", "CATALOG.json"))["entries"]
    return {k: dict(v["spec"], name=k) for k, v in c.items()}


def fmt(v):
    return "inf" if isinstance(v, float) and math.isinf(v) else f"{v:g}"


def rname(phase, task, width, dev, algo, lr, seed, extra=""):
    return f"{phase}__{task}_w{width}__{dev}__{algo}__lr{lr:g}__s{seed}" + (f"__{extra}" if extra else "")


def run(phase, task, arm, lr, seed, split="test", width=None, spec=None, algo="sgd", ucfg=None, extra="", **kw):
    width = width or BASE_W.get(task, 128)
    dev = (spec or {}).get("name", arm)
    r = dict(phase=phase, task=task, arm=arm, lr=lr, seed=seed, split=split, width=width, algo=algo)
    if spec:
        r["spec"] = dict(spec)
    if ucfg:
        r["ucfg"] = ucfg
    r.update(kw)
    return rname(phase, task, width, dev, algo, lr, seed, extra), r


def cmd(name, r, outdir):
    c = [PY, "-B", os.path.join(HERE, "run.py"), "--task", r["task"], "--arm", r["arm"], "--lr", repr(r["lr"]),
         "--seed", str(r["seed"]), "--split", r["split"], "--tag", name, "--algo", r["algo"],
         "--out", os.path.join(outdir, name + ".json")]
    if r.get("spec"):
        c += ["--spec", json.dumps(r["spec"])]  # tau_steps inf is written as Infinity, which json.loads reads back
    if r.get("ucfg"):
        c += ["--ucfg", json.dumps(r["ucfg"])]
    if r["task"] in ("cifar", "lm"):
        c += ["--width", str(r["width"])]
    for k in ("alpha", "epochs", "batch"):
        if r.get(k) is not None:
            c += ["--" + k, str(r[k])]
    if os.environ.get("ME_SCALE"):  # dry rehearsals only
        c += ["--scale", os.environ["ME_SCALE"]]
    return c


def outdir(r):
    return os.path.join(REC, "runs", r["phase"])


def recpath(name, r):
    return os.path.join(outdir(r), name + ".json")


def execute(runs, workers, logdir, deadline=None):
    runs = list(dict(runs).items())
    for _, r in runs:
        os.makedirs(outdir(r), exist_ok=True)
    os.makedirs(logdir, exist_ok=True)
    todo = [(n, r) for n, r in runs if not os.path.exists(recpath(n, r))]
    print(f"{len(runs)} runs, {len(todo)} to do", flush=True)
    live, fails, est = [], [], {}
    key = lambda r: (r["task"], r.get("width"), r["algo"], r["arm"], r.get("epochs"))
    while todo or live:
        while todo and len(live) < workers:
            if deadline and time.time() + 1.15 * est.get(key(todo[0][1]), 0) > deadline:
                print(f"deadline: {len(todo)} runs not started", flush=True)
                jsave(os.path.join(REC, "NOT-STARTED-" + str(int(time.time())) + ".json"), [n for n, _ in todo])
                todo = []
                break
            n, r = todo.pop(0)
            lf = open(os.path.join(logdir, n + ".log"), "wb")
            flags = 0x08000000 if os.name == "nt" else 0  # CREATE_NO_WINDOW
            p = subprocess.Popen(cmd(n, r, outdir(r)), stdout=lf, stderr=subprocess.STDOUT, creationflags=flags)
            live.append((n, r, p, lf, time.time()))
        time.sleep(1.0)
        for item in list(live):
            n, r, p, lf, t0 = item
            if p.poll() is not None:
                lf.close(); live.remove(item)
                est[key(r)] = max(est.get(key(r), 0), time.time() - t0)
                if p.returncode != 0:
                    fails.append(n)
                print(f"{'done' if p.returncode == 0 else 'FAIL'} {n} {time.time() - t0:.0f}s", flush=True)
    print(f"finished; failures: {fails}", flush=True)
    return fails


def score(name, r):
    p = recpath(name, r)
    if not os.path.exists(p):
        return None
    rec = jload(p)
    assert rec["metric"]["split"] == "val", "selection must use validation records"
    m = rec["metric"]
    v = m["acc"] if "acc" in m else -m.get("bpb", math.nan)
    if rec.get("diverged") or not math.isfinite(v):
        return -math.inf
    return v


def lr_up(v):
    m = round(v / 10 ** math.floor(math.log10(v)))
    return float(f"{v * (3 if m == 1 else 10 / 3):.1g}")


def lr_down(v):
    m = round(v / 10 ** math.floor(math.log10(v)))
    return float(f"{v / (10 / 3 if m == 1 else 3):.1g}")


def select_lr(mk, grid, workers, logdir, deadline, max_ext=3):
    """Edge rule (PLAN-PAPER.md E2/E3): run the grid on validation; while the best is at an edge, add the next half-decade
    point beyond it (at most max_ext times). mk(lr) -> (name, run). Returns (lr, table)."""
    grid = sorted(grid)
    for _ in range(max_ext + 1):
        execute([mk(lr) for lr in grid], workers, logdir, deadline)
        sc = [(score(*mk(lr)), lr) for lr in grid]
        if any(s is None for s, _ in sc):
            return None, sc
        best = max(sc, key=lambda t: (t[0], -t[1]))  # ties: the smaller lr
        i = grid.index(best[1])
        if i == len(grid) - 1 and best[0] > -math.inf:
            grid.append(lr_up(grid[-1]))
        elif i == 0 and len(grid) > 1:
            grid.insert(0, lr_down(grid[0]))
        else:
            return best[1], sc
    return best[1], sc


# ------------------------------------------------------------------ phases
def phase_e2(a):
    """Desk: MNIST FP lr edge rule (lane ME's grid + extensions), then the TT family on the mid device."""
    mk = lambda lr: run("e2", "mnist", "fp_sgd", lr, 0, split="val")
    lr, tab = select_lr(mk, LR_GRID["mnist"] + [1e-2], a.workers, a.logdir, a.deadline_epoch)
    set_choice(["lr", "mnist", "128"], dict(lr=lr, grid=tab))
    lane_me_lr = 3e-3
    grids = {"cttv2": CTT_GRID, "agad": AGAD_GRID}
    if lr != lane_me_lr:
        grids["ttv2"] = LANE_ME_TT_GRID
    runs = []
    for algo, g in grids.items():
        for i, u in enumerate(g):
            runs.append(run("e2", "mnist", "device", lr, 0, split="val", spec=MID_DEVICE, algo=algo, ucfg=u, extra=f"g{i}"))
    runs.append(run("e2", "mnist", "device", lr, 0, split="val", spec=MID_DEVICE, algo="sgd", extra="ref"))
    execute(runs, a.workers, a.logdir, a.deadline_epoch)
    best = {}
    for algo, g in grids.items():
        rows = []
        for i, u in enumerate(g):
            s = score(*run("e2", "mnist", "device", lr, 0, split="val", spec=MID_DEVICE, algo=algo, ucfg=u, extra=f"g{i}"))
            rows.append((s, -i, u))
        b = max(rows, key=lambda t: (t[0], t[1]))
        best[algo] = dict(ucfg=b[2], val_acc=b[0], grid=[dict(u, val_acc=s) for s, _, u in rows])
    if "ttv2" not in best:
        tt = jload(os.path.join(os.environ.get("ME_LANE_ME") or os.path.join(HERE, "..", ".."), "records", "TT-CHOICE.json"))
        u = {k: tt[k] for k in ("tt_lambda", "tt_period", "tt_lr_ratio") if k in tt}
        acc = max(g["val_acc"] for g in tt["grid"] if all(g.get(k) == v for k, v in u.items()))
        best["ttv2"] = dict(ucfg=u, val_acc=acc, source="lane ME records/TT-CHOICE.json (same lr 3e-3, same desk GPU)")
    for algo in best:
        set_choice(["tt", algo], best[algo])
    bc = max(("cttv2", "agad"), key=lambda k: (best[k]["val_acc"], k == "cttv2"))
    sa = max(("ttv2", "cttv2", "agad"), key=lambda k: (best[k]["val_acc"], {"ttv2": 2, "cttv2": 1, "agad": 0}[k]))
    set_choice(["best_chopped"], bc)
    set_choice(["s_algo"], sa)


def tt(algo):
    if algo == "sgd":
        return None
    return dict(choices()["tt"][algo]["ucfg"])


def phase_e1(a):
    runs = []
    for s in (0, 1, 2):
        kw = dict(alpha=GH_ALPHA)
        runs.append(run("e1", "mnist_gh", "fp_sgd", 0.01, s, **kw))
        runs.append(run("e1", "mnist_gh", "device", 0.01, s, spec=GH_DEVICE, **kw))
        runs.append(run("e1", "mnist_gh", "device", 0.01, s, spec=GH_DEVICE, algo="ttv1", ucfg=TTV1_GH, **kw))
        runs.append(run("e1", "mnist_gh", "device", 0.01, s, spec=GH_DEVICE, algo="ttv2", ucfg=dict(tt("ttv2"), tt_cols=16),
                        **kw))
    for arm, algo, u in (("fp_sgd", "sgd", None), ("device", "sgd", None), ("device", "ttv1", dict(TTV1_GH, tt_cols=64))):
        runs.append(run("e1", "mnist_gh", arm, 0.01, 0, spec=GH_DEVICE if arm == "device" else None, algo=algo, ucfg=u,
                        alpha=GH_ALPHA, batch=64, extra="b64"))
    for sr in (0.0, 0.5):
        spec = dict(RASCH_DEVICE, ref_err=sr, name=f"rasch20_sr{sr:g}")
        for s in (0, 1):
            for algo in ("ttv2", "cttv2", "agad"):
                runs.append(run("e1b", "mnist_gh", "device", 0.01, s, spec=spec, algo=algo, ucfg=tt(algo), alpha=GH_ALPHA,
                                epochs=10))
    for s in (0, 1):
        runs.append(run("e1b", "mnist_gh", "fp_sgd", 0.01, s, alpha=GH_ALPHA, epochs=10))
    execute(runs, a.workers, a.logdir, a.deadline_epoch)


def phase_fplr(a):
    widths = {t: list(WIDTHS[t]) + ([WIDTH4[t]] if a.width4 else []) for t in ("cifar", "lm")}
    for t in ("cifar", "lm"):
        for w in widths[t]:
            mk = lambda lr, t=t, w=w: run("fplr", t, "fp_sgd", lr, 0, split="val", width=w)
            lr, tab = select_lr(mk, LR_GRID[t], a.workers, a.logdir, a.deadline_epoch)
            set_choice(["lr", t, str(w)], dict(lr=lr, grid=tab))
    mk = lambda lr: run("fplr", "lm", "fp_adam", lr, 0, split="val")
    lr, tab = select_lr(mk, ADAM_GRID, a.workers, a.logdir, a.deadline_epoch)
    set_choice(["adam_lr"], dict(lr=lr, grid=tab))


def fp_lr(task, width=None):
    return choices()["lr"][task][str(width or BASE_W[task])]["lr"]


def phase_e3(a):
    cat = catalog()
    runs = []
    for t in a.task.split(","):
        lr = fp_lr(t)
        for s in SEEDS5:
            runs.append(run("e3", t, "fp_sgd", lr, s))
            for d in MAIN_DEVICES:
                for algo in ALGOS:
                    runs.append(run("e3", t, "device", lr, s, spec=cat[d], algo=algo, ucfg=tt(algo)))
        if t == "lm":
            for s in SEEDS5:
                runs.append(run("e3", t, "fp_adam", choices()["adam_lr"]["lr"], s))
    # interleave tasks so a deadline cut leaves every task partly done, seeds in order
    runs.sort(key=lambda nr: (nr[1]["seed"], nr[1]["task"] != "mnist"))
    execute(runs, a.workers, a.logdir, a.deadline_epoch)


def e4_arms():
    bc = choices()["best_chopped"]
    return [(d, al) for d in ("protonic_onen2022", "ecram_li_tang2018") for al in ("ttv2", bc)]


def phase_e4(a):
    cat = catalog()
    for t in [x for x in a.task.split(",") if x in WIDTHS]:
        ws = list(WIDTHS[t])
        for w in ws:
            lf = fp_lr(t, w)
            for d, al in e4_arms():
                grid = [lr_down(lf), lf, lr_up(lf)]
                mk = lambda lr, d=d, al=al, w=w: run("e4sel", t, "device", lr, 0, split="val", width=w, spec=cat[d], algo=al,
                                                    ucfg=tt(al))
                lr, tab = select_lr(mk, grid, a.workers, a.logdir, a.deadline_epoch, max_ext=2)
                set_choice(["devlr", t, str(w), f"{d}__{al}"], dict(lr=lr, grid=tab))
        runs = []
        for s in (0, 1, 2):
            for w in ws:
                runs.append(run("e4", t, "fp_sgd", fp_lr(t, w), s, width=w))
                for d, al in e4_arms():
                    lr = choices()["devlr"][t][str(w)][f"{d}__{al}"]["lr"]
                    runs.append(run("e4", t, "device", lr, s, width=w, spec=cat[d], algo=al, ucfg=tt(al)))
        execute(runs, a.workers, a.logdir, a.deadline_epoch)


def oat_specs():
    base = dict(catalog()["protonic_onen2022"])
    out = [("base", dict(base, name="base"))]
    for ax, vals in OAT.items():
        for v in vals:
            s = dict(base)
            if ax == "gamma":
                if v == base["gamma_up"]:
                    continue
                s["gamma_up"] = s["gamma_dn"] = v
            else:
                if s.get(ax, math.inf if ax == "tau_steps" else None) == v:
                    continue
                s[ax] = v
            nm = f"{ax}{fmt(v)}"
            out.append((nm, dict(s, name=nm)))
    return out


def phase_e5(a):
    sa = choices()["s_algo"]
    runs = []
    sizes = [(t, w) for t in ("cifar", "lm") for w in WIDTHS[t]]
    for t, w in sizes:
        for nm, s in oat_specs():
            runs.append(run("e5", t, "device", fp_lr(t, w), 0, width=w, spec=s, algo=sa, ucfg=tt(sa)))
    if a.sgd:
        for t in ("cifar", "lm"):
            for nm, s in oat_specs():
                runs.append(run("e5", t, "device", fp_lr(t), 0, spec=s, algo="sgd"))
    runs.sort(key=lambda nr: (nr[1]["width"] / BASE_W[nr[1]["task"]], nr[1]["task"]))
    execute(runs, a.workers, a.logdir, a.deadline_epoch)


def pair_specs():
    base = dict(catalog()["protonic_onen2022"])
    axes = list(PAIR_LEVELS)
    out = []
    for i in range(len(axes)):
        for j in range(i + 1, len(axes)):
            for vi in PAIR_LEVELS[axes[i]]:
                for vj in PAIR_LEVELS[axes[j]]:
                    s = dict(base)
                    for ax, v in ((axes[i], vi), (axes[j], vj)):
                        if ax == "gamma":
                            s["gamma_up"] = s["gamma_dn"] = v
                        else:
                            s[ax] = v
                    nm = f"{axes[i]}{fmt(vi)}+{axes[j]}{fmt(vj)}"
                    out.append((nm, dict(s, name=nm)))
    return out


def phase_e5pair(a):
    sa = choices()["s_algo"]
    runs = [run("e5pair", t, "device", fp_lr(t), 0, spec=s, algo=sa, ucfg=tt(sa))
            for t in ("cifar", "lm") for _, s in pair_specs()]
    execute(runs, a.workers, a.logdir, a.deadline_epoch)


def e5_points(task, width, algo):
    """{axis: {value: [gaps by seed]}} of the one-at-a-time grid against E4's FP test mean at that size."""
    import stats_paper as S
    fp = [S.metric(r) for r in S.load_phase(REC, "e4") if r["task"] == task and r["width"] == width and r["arm"] == "fp_sgd"]
    if not fp:
        raise SystemExit(f"e5b: no E4 FP records for {task} w{width}")
    fpm = sum(fp) / len(fp)
    base = dict(catalog()["protonic_onen2022"])
    pts = {ax: {} for ax in S.AXES}
    names = {}
    for r in S.load_phase(REC, "e5"):
        if r["task"] != task or r["width"] != width or r["algo"] != algo:
            continue
        g = S.gap_value(task, fpm, S.metric(r))
        ax = S.oat_point_axis(r["spec"], base)
        axes = list(S.AXES) if ax is None else [ax]
        for a_ in axes:
            v = S.axis_value(r["spec"], a_)
            pts[a_].setdefault(v, []).append(g)
            names[(a_, v)] = r["spec"]["name"]
    return pts, fpm


def spec_from_axes(vals, name):
    s = dict(catalog()["protonic_onen2022"])
    for ax, v in vals.items():
        if ax == "gamma":
            s["gamma_up"] = s["gamma_dn"] = v
        else:
            s[ax] = v
    s["name"] = name
    return s


def phase_e5b(a):
    """E5 second seeds (seed-0 gap in [0.5 X, 2 X]), then the joint spec per size (3 seeds), tightened once if it fails."""
    import stats_paper as S
    sa = choices()["s_algo"]
    sizes = [(t, w) for t in ("cifar", "lm") for w in WIDTHS[t]]
    specs = dict(oat_specs())
    runs = []
    for t, w in sizes:
        X = S.GAP_LINE[t]
        for nm, s in specs.items():
            p0 = recpath(*run("e5", t, "device", fp_lr(t, w), 0, width=w, spec=s, algo=sa, ucfg=tt(sa)))
            if not os.path.exists(p0):
                continue
            pts, fpm = e5_points(t, w, sa)
            r0 = S.jload(p0)
            g0 = S.gap_value(t, fpm, S.metric(r0))
            if 0.5 * X <= g0 <= 2 * X:
                runs.append(run("e5", t, "device", fp_lr(t, w), 1, width=w, spec=s, algo=sa, ucfg=tt(sa)))
    execute(runs, a.workers, a.logdir, a.deadline_epoch)
    out = {}
    for rnd in (1, 2):
        jr = []
        for t, w in sizes:
            key = f"{t}_w{w}"
            X = S.GAP_LINE[t]
            if rnd == 1:
                pts, fpm = e5_points(t, w, sa)
                th = S.thresholds({ax: {v: sum(g) / len(g) for v, g in d.items()} for ax, d in pts.items()}, X)
                vals = {ax: r["threshold"] for ax, r in th.items()}
                out[key] = dict(fp_mean=fpm, thresholds=th, joint_r1=vals)
            else:
                if out[key].get("joint_r1_pass") is not False:
                    continue
                vals = {ax: S.step_toward_base(ax, v, OAT[ax]) for ax, v in out[key]["joint_r1"].items()}
                out[key]["joint_r2"] = vals
            if any(v is None for v in vals.values()):
                out[key][f"joint_r{rnd}_status"] = "not defined (an axis is not reachable on the grid)"
                continue
            s = spec_from_axes(vals, f"joint_r{rnd}")
            for seed in (0, 1, 2):
                jr.append(run("e5joint", t, "device", fp_lr(t, w), seed, width=w, spec=s, algo=sa, ucfg=tt(sa)))
        if not jr:
            break
        execute(jr, a.workers, a.logdir, a.deadline_epoch)
        for t, w in sizes:
            key = f"{t}_w{w}"
            gs = [S.gap_value(t, out[key]["fp_mean"], S.metric(r)) for r in S.load_phase(REC, "e5joint")
                  if r["task"] == t and r["width"] == w and r["spec"]["name"] == f"joint_r{rnd}"]
            if gs:
                ci = S.mean_ci(gs)
                out[key][f"joint_r{rnd}_gap"] = ci
                out[key][f"joint_r{rnd}_pass"] = bool(ci["mean"] < S.GAP_LINE[t])
        jsave(os.path.join(REC, "E5-JOINT.json"), out)
    jsave(os.path.join(REC, "E5-JOINT.json"), out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["e2", "e1", "fplr", "e3", "e4", "e5", "e5b", "e5pair"])
    ap.add_argument("--task", default="mnist,cifar,lm")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--logdir", default=os.path.join(HERE, "..", "scratch", "logs"))
    ap.add_argument("--deadline-epoch", type=float, default=None)
    ap.add_argument("--width4", action="store_true")
    ap.add_argument("--sgd", action="store_true", help="E5: add the SGD one-at-a-time at the base sizes")
    a = ap.parse_args()
    {"e2": phase_e2, "e1": phase_e1, "fplr": phase_fplr, "e3": phase_e3, "e4": phase_e4, "e5": phase_e5,
     "e5b": phase_e5b, "e5pair": phase_e5pair}[a.phase](a)


if __name__ == "__main__":
    main()
