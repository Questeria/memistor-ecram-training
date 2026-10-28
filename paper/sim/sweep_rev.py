"""REVISION run lists (PLAN-REVISION.md), on top of sweep_paper.py's executor and edge-rule lr selection.

Records go to <records>/revision/runs/<phase>/; selections to <records>/revision/CHOICES-REVISION.json; the device catalog is
<records>/revision/CATALOG-REV.json (devices_rev.py). Runs use run_rev.py --rng split unless a run says sim=old (run.py, the
original simulator, for the diagnostic's old arms).

    python -B sweep_rev.py --phase d1|fplr|e2|e3|e4|e5 [--task mnist,cifar,lm] --workers 8
"""
import argparse
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sweep_paper as B  # noqa: E402

REC0 = B.REC
B.REC = os.path.join(REC0, "revision")
B.CHO = os.path.join(B.REC, "CHOICES-REVISION.json")
OLD_CHO = os.path.join(REC0, "CHOICES-PAPER.json")
SEEDS5 = [0, 1, 2, 3, 4]
SEEDS3 = [0, 1, 2]
D1_CIFAR_EPOCHS = 10  # the diagnostic's CIFAR-subset slice: a third of the 30-epoch budget
PUB_TTV2 = dict(tt_reset="none", tt_h_forget=True, tt_max_pulses=1)


def catalog():
    p = os.path.join(B.REC, "CATALOG-REV.json")
    if not os.path.exists(p):
        p = os.path.join(HERE, "..", "records", "revision", "CATALOG-REV.json")
    c = B.jload(p)["entries"]
    return {k: dict(v["spec"], name=k) for k, v in c.items()}


B.catalog = catalog


def cmd(name, r, outdir):
    c = B.__dict__["_cmd_orig"](name, r, outdir)
    if r.get("sim") == "old":
        return c
    c[2] = os.path.join(HERE, "run_rev.py")
    return c + ["--rng", r.get("rng", "split")]


B._cmd_orig = B.cmd
B.cmd = cmd
run, execute, select_lr = B.run, B.execute, B.select_lr


def old_choices():
    return B.jload(OLD_CHO)


def with_reset(u, mode):
    u = dict(u or {})
    u["tt_reset"] = mode
    return u


# ------------------------------------------------------------------ D1: the diagnostic (old against repaired)
def d1_runs(task):
    oc = old_choices()
    lr = oc["lr"][task][str(B.BASE_W[task])]["lr"]
    cat = catalog()
    ep = dict(epochs=D1_CIFAR_EPOCHS) if task == "cifar" else {}
    tt = {a: dict(oc["tt"][a]["ucfg"]) for a in ("ttv2", "cttv2", "agad")}
    devs = {"protonic_onen2022": cat["protonic_onen2022"], "ecram_li_tang2018_papermap": cat["ecram_li_tang2018_papermap"]}
    runs = []
    for s in SEEDS3:
        R = lambda arm, spec=None, algo="sgd", u=None, extra="", **kw: runs.append(
            run("d1", task, arm, lr, s, spec=spec, algo=algo, ucfg=u, extra=extra, **ep, **kw))
        # the original simulator, as run for the paper
        R("fp_sgd", extra="old", sim="old")
        for dn, sp in devs.items():
            R("device", sp, "sgd", None, "old", sim="old")
            for a in ("ttv2", "cttv2", "agad"):
                R("device", sp, a, tt[a], "old", sim="old")
        # repaired streams, the old (ideal) reset: the RNG effect alone
        R("fp_sgd", extra="rev")
        for dn, sp in devs.items():
            R("device", sp, "sgd", None, "rev")
            for a in ("ttv2", "cttv2", "agad"):
                R("device", sp, a, tt[a], "rev")
            for mode in ("pulse", "alt", "none"):  # the reset effect (AGAD has no reset)
                for a in ("ttv2", "cttv2"):
                    R("device", sp, a, with_reset(tt[a], mode), "rev_" + mode)
            R("device", sp, "ttv2", dict(tt["ttv2"], **PUB_TTV2), "rev_pub")
        # the aihwkit-mapped Li-ECRAM (the mapping effect), with the pulse reset
        for a in ("sgd", "ttv2", "cttv2", "agad"):
            u = None if a == "sgd" else (with_reset(tt[a], "pulse") if a != "agad" else tt[a])
            R("device", cat["ecram_li_tang2018"], a, u, "rev_pulse" if a in ("ttv2", "cttv2") else "rev")
        # digital (ideal-device) TT family
        for a in ("ttv2", "cttv2", "agad"):
            R("fp_sgd", None, a, with_reset(tt[a], "pulse") if a != "agad" else tt[a], "rev_digital")
    return runs


def phase_d1(a):
    runs = []
    for t in a.task.split(","):
        if t in ("mnist", "cifar"):
            runs += d1_runs(t)
    runs.sort(key=lambda nr: (nr[1]["seed"], nr[1]["task"] != "mnist"))
    execute(runs, a.workers, a.logdir, a.deadline_epoch)


# ------------------------------------------------------------------ selection (validation only, seed 0)
def phase_fplr(a):
    for t in ("mnist", "cifar", "lm"):
        for w in ([B.BASE_W[t]] if t == "mnist" else B.WIDTHS[t]):
            grid = B.LR_GRID[t] + ([1e-2] if t == "mnist" else [])
            mk = lambda lr, t=t, w=w: run("fplr", t, "fp_sgd", lr, 0, split="val", width=w)
            lr, tab = select_lr(mk, grid, a.workers, a.logdir, a.deadline_epoch)
            B.set_choice(["lr", t, str(w)], dict(lr=lr, grid=tab))
        mk = lambda lr, t=t: run("fplr", t, "fp_adam", lr, 0, split="val")
        lr, tab = select_lr(mk, B.ADAM_GRID, a.workers, a.logdir, a.deadline_epoch)
        B.set_choice(["adam_lr", t], dict(lr=lr, grid=tab))


TTV2_GRID = [with_reset(u, m) for u in B.LANE_ME_TT_GRID for m in ("pulse", "none")]
CTT_GRID = [with_reset(u, "pulse" if u["tt_reset"] else "none") for u in B.CTT_GRID]
AGAD_GRID = [with_reset(u, "none") for u in B.AGAD_GRID]


def phase_e2(a):
    lr = B.choices()["lr"]["mnist"]["128"]["lr"]
    grids = {"ttv2": TTV2_GRID, "cttv2": CTT_GRID, "agad": AGAD_GRID}
    runs = [run("e2", "mnist", "device", lr, 0, split="val", spec=B.MID_DEVICE, algo=al, ucfg=u, extra=f"g{i}")
            for al, g in grids.items() for i, u in enumerate(g)]
    execute(runs, a.workers, a.logdir, a.deadline_epoch)
    best = {}
    for al, g in grids.items():
        rows = [(B.score(*run("e2", "mnist", "device", lr, 0, split="val", spec=B.MID_DEVICE, algo=al, ucfg=u,
                              extra=f"g{i}")), -i, u) for i, u in enumerate(g)]
        b = max(rows, key=lambda t: (t[0] if t[0] is not None else -math.inf, t[1]))
        best[al] = dict(ucfg=b[2], val_acc=b[0], grid=[dict(u, val_acc=s) for s, _, u in rows])
        B.set_choice(["tt", al], best[al])
    B.set_choice(["best_chopped"], max(("cttv2", "agad"), key=lambda k: (best[k]["val_acc"] or -1, k == "cttv2")))
    B.set_choice(["s_algo"], max(("ttv2", "cttv2", "agad"),
                                 key=lambda k: (best[k]["val_acc"] or -1, {"ttv2": 2, "cttv2": 1, "agad": 0}[k])))


def tt(al):
    return None if al == "sgd" else dict(B.choices()["tt"][al]["ucfg"])


def fp_lr(t, w=None):
    return B.choices()["lr"][t][str(w or B.BASE_W[t])]["lr"]


# ------------------------------------------------------------------ the main table, width, sensitivity
def phase_e3(a):
    cat = catalog()
    runs = []
    for t in a.task.split(","):
        lr = fp_lr(t)
        for s in SEEDS5:
            runs.append(run("e3", t, "fp_sgd", lr, s))
            runs.append(run("e3", t, "fp_adam", B.choices()["adam_lr"][t]["lr"], s))
            for al in ("ttv2", "cttv2", "agad"):
                runs.append(run("e3", t, "fp_sgd", lr, s, algo=al, ucfg=tt(al), extra="digital"))
            for d in B.MAIN_DEVICES:
                for al in B.ALGOS:
                    runs.append(run("e3", t, "device", lr, s, spec=cat[d], algo=al, ucfg=tt(al)))
    runs.sort(key=lambda nr: (nr[1]["seed"], nr[1]["task"] != "mnist"))
    execute(runs, a.workers, a.logdir, a.deadline_epoch)


# DEVIATIONS R2: the "digital" TT arms of e3 (ideal_float, n_states 1e9) make the transfer quantum alpha * 2e-9, so C never
# moves; the algorithm-only reference is instead every algorithm on an ideal device: symmetric, constant step, 1000 levels,
# no noise, no spread, no reference error (pulses still stochastic, bounds still [-1, 1]).
IDEAL_DEV = dict(n_states=1000, name="ideal1000")


def phase_e3ideal(a):
    runs = []
    for t in a.task.split(","):
        lr = fp_lr(t)
        for s in SEEDS5:
            for al in B.ALGOS:
                runs.append(run("e3", t, "device", lr, s, spec=IDEAL_DEV, algo=al, ucfg=tt(al)))
    runs.sort(key=lambda nr: (nr[1]["seed"], nr[1]["task"] != "mnist"))
    execute(runs, a.workers, a.logdir, a.deadline_epoch)


def e4_arms():
    bc = B.choices()["best_chopped"]
    return [(d, al) for d in ("protonic_onen2022", "ecram_li_tang2018") for al in ("ttv2", bc)]


def phase_e4(a):
    cat = catalog()
    for t in [x for x in a.task.split(",") if x in B.WIDTHS]:
        ws = list(B.WIDTHS[t])
        for w in ws:
            lf = fp_lr(t, w)
            for d, al in e4_arms():
                mk = lambda lr, d=d, al=al, w=w: run("e4sel", t, "device", lr, 0, split="val", width=w, spec=cat[d],
                                                    algo=al, ucfg=tt(al))
                lr, tab = select_lr(mk, [B.lr_down(lf), lf, B.lr_up(lf)], a.workers, a.logdir, a.deadline_epoch, max_ext=2)
                B.set_choice(["devlr", t, str(w), f"{d}__{al}"], dict(lr=lr, grid=tab))
        runs = []
        for s in SEEDS5:
            for w in ws:
                runs.append(run("e4", t, "fp_sgd", fp_lr(t, w), s, width=w))
                for d, al in e4_arms():
                    lr = B.choices()["devlr"][t][str(w)][f"{d}__{al}"]["lr"]
                    runs.append(run("e4", t, "device", lr, s, width=w, spec=cat[d], algo=al, ucfg=tt(al)))
        execute(runs, a.workers, a.logdir, a.deadline_epoch)


OAT_REV = {"n_states": [100, 200, 500, 2000, 5000], "asym": [0, 0.1, 0.2, 0.4], "asym_fixedsp": [0.1, 0.2, 0.4],
           "gamma": [0, 0.5, 1, 2], "c2c": [0, 1, 2, 4], "ref_err": [0, 0.05, 0.1, 0.2, 0.5],
           "tau_steps": [1e5, 1e4, 1e3, 1e2]}


def oat_rev():
    base = dict(catalog()["protonic_onen2022"])
    out = [("base", dict(base, name="base"))]
    for ax, vals in OAT_REV.items():
        for v in vals:
            s = dict(base)
            if ax == "gamma":
                s["gamma_up"] = s["gamma_dn"] = v
            elif ax == "asym_fixedsp":
                s["asym"], s["recenter_sp"] = v, True
            else:
                s[ax] = v
            nm = f"{ax}{B.fmt(v)}"
            out.append((nm, dict(s, name=nm)))
    return out


def phase_e5(a):
    sa = os.environ.get("ME_E5_ALGO") or B.choices()["s_algo"]  # DEVIATIONS R3: a second sheet with c-TTv2
    runs = []
    for t in [x for x in a.task.split(",") if x in ("cifar", "lm")]:
        for s in SEEDS3:
            for nm, sp in oat_rev():
                runs.append(run("e5", t, "device", fp_lr(t), s, spec=sp, algo=sa, ucfg=tt(sa)))
    runs.sort(key=lambda nr: (nr[1]["seed"], nr[1]["task"]))
    execute(runs, a.workers, a.logdir, a.deadline_epoch)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["d1", "fplr", "e2", "e3", "e3ideal", "e4", "e5", "list"])
    ap.add_argument("--task", default="mnist,cifar,lm")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--logdir", default=os.path.join(HERE, "..", "scratch", "logs-rev"))
    ap.add_argument("--deadline-epoch", type=float, default=None)
    a = ap.parse_args()
    if a.phase == "list":  # count the runs of every phase without executing (no choices needed for d1)
        print(json.dumps({t: len(d1_runs(t)) for t in ("mnist", "cifar")}))
        return
    {"d1": phase_d1, "fplr": phase_fplr, "e2": phase_e2, "e3": phase_e3, "e3ideal": phase_e3ideal, "e4": phase_e4, "e5": phase_e5}[a.phase](a)


if __name__ == "__main__":
    main()
