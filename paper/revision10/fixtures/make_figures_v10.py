"""Figures of the paper from records/RESULTS-PAPER.json (and records/ENERGY-SYSTEM.json), matplotlib, our own data only.
Runs where matplotlib exists (the build pod; the desk has none).

    python3 make_figures.py --records records --out tex/figs
"""
import argparse
import json
import math
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DEV = {"ecram_li_tang2018": "Li-ECRAM", "ecram_mo_kim2019": "MO-ECRAM", "protonic_onen2022": "Protonic",
       "wox_ysz_chen2023": "W/YSZ/WOx", "widrow1960_claimed": "Memistor"}
ALG = {"sgd": "SGD", "ttv1": "TTv1", "ttv2": "TTv2", "cttv2": "c-TTv2", "agad": "AGAD"}
COL = {"sgd": "#7f7f7f", "ttv2": "#1f77b4", "cttv2": "#ff7f0e", "agad": "#2ca02c", "ttv1": "#9467bd"}
LINE = {"mnist": 2.0, "cifar": 2.0, "lm": 5.0}
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "legend.fontsize": 7, "figure.dpi": 150})


def save(fig, out, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out, f"{name}.{ext}"), bbox_inches="tight", dpi=200)
    plt.close(fig)


def fin(x):
    return x is not None and isinstance(x, (int, float)) and math.isfinite(x)


def fig_validation(R, out):
    e1, e1b = R.get("e1"), R.get("e1b")
    if not e1:
        return
    fig, ax = plt.subplots(1, 2, figsize=(6.6, 2.4))
    arms = [("fp", "FP"), ("sgd", "SGD"), ("ttv1", "TTv1"), ("ttv2", "TTv2")]
    pub = {"fp": 2.0, "sgd": 15.0, "ttv1": 2.0}
    xs = range(len(arms))
    for i, (k, lab) in enumerate(arms):
        c = e1["arms"].get(k)
        if c and fin(c["mean"]):
            err = [[c["mean"] - c["lo"]], [c["hi"] - c["mean"]]] if fin(c.get("lo")) else None
            ax[0].bar(i - 0.18, c["mean"], 0.36, yerr=err, color="#1f77b4", label="this work" if i == 0 else None)
        if k in pub:
            ax[0].bar(i + 0.18, pub[k], 0.36, color="#cccccc", hatch="//", label="published (text)" if i == 0 else None)
    ax[0].set_xticks(list(xs)); ax[0].set_xticklabels([a[1] for a in arms])
    ax[0].set_ylabel("MNIST test error (%)"); ax[0].set_title("(a) vs Gokmen & Haensch 2020, RPU-baseline device")
    ax[0].legend(frameon=False)
    if e1b:
        for j, a in enumerate(("ttv2", "cttv2", "agad")):
            ys = [e1b["cells"].get(f"{a}|{s}", {}).get("mean") for s in (0.0, 0.5)]
            ax[1].plot([0, 0.5], ys, "o-", color=COL[a], label=ALG[a])
        fp = e1b["cells"].get("fp|None", {}).get("mean")
        if fin(fp):
            ax[1].axhline(fp, ls=":", color="k", lw=0.8, label="FP")
        ax[1].set_xlabel("reference offset $\\sigma_r$"); ax[1].set_ylabel("test error (%)")
        ax[1].set_title("(b) offset robustness (cf. Rasch et al. 2024)"); ax[1].legend(frameon=False)
    save(fig, out, "fig_validation")


def fig_main(R, out):
    e3 = R.get("e3")
    if not e3:
        return
    tasks = [t for t in ("mnist", "cifar", "lm") if t in e3]
    fig, axs = plt.subplots(1, len(tasks), figsize=(6.8, 2.6), sharey=False)
    if len(tasks) == 1:
        axs = [axs]
    for ax, t in zip(axs, tasks):
        devs = list(DEV)
        for di, d in enumerate(devs):
            for ai, a in enumerate(("sgd", "ttv2", "cttv2", "agad")):
                c = e3[t]["cells"].get(f"{d}__{a}")
                if not c or not fin(c["gap"]["mean"]):
                    continue
                g = c["gap"]
                y = di + (ai - 1.5) * 0.18
                xe = [[g["mean"] - g["lo"]], [g["hi"] - g["mean"]]] if fin(g.get("lo")) else None
                ax.errorbar(max(g["mean"], 0.05), y, xerr=xe, fmt="o", ms=3, color=COL[a], label=ALG[a] if di == 0 else None)
        ax.axvline(LINE[t], ls="--", color="r", lw=0.8)
        ax.set_xscale("symlog", linthresh=1.0)
        ticks = [v for v in (-5, -2, 0, 1, 2, 5, 10, 20, 50) if v >= ax.get_xlim()[0] and v <= ax.get_xlim()[1]]
        ax.set_xticks(ticks); ax.set_xticklabels([str(v) for v in ticks])
        ax.set_yticks(range(len(devs))); ax.set_yticklabels([DEV[d] for d in devs] if t == tasks[0] else [])
        ax.set_xlabel("gap (pp)" if t != "lm" else "gap (% bpb)")
        ax.set_title({"mnist": "MNIST", "cifar": "CIFAR-10 subset", "lm": "char-LM (enwik8)"}[t])
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.06))
    save(fig, out, "fig_main")


def fig_scale(R, out):
    e4 = R.get("e4")
    if not e4:
        return
    tasks = [t for t in ("cifar", "lm") if t in e4]
    fig, axs = plt.subplots(1, len(tasks), figsize=(6.6, 2.4))
    if len(tasks) == 1:
        axs = [axs]
    for ax, t in zip(axs, tasks):
        for a, d in e4[t]["arms"].items():
            dev, al = a.split("__")
            ws = sorted(int(w) for w in d)
            g = [d[str(w)]["gap"] if str(w) in d else d[w]["gap"] for w in ws]
            m = [x["mean"] for x in g]
            e = [[x["mean"] - x["lo"] for x in g], [x["hi"] - x["mean"] for x in g]] if all(fin(x.get("lo")) for x in g) else None
            ax.errorbar(ws, m, yerr=e, marker="o", ms=3, capsize=2, color=COL[al],
                        ls="-" if dev == "protonic_onen2022" else "--", label=f"{DEV[dev]} {ALG[al]}")
        ax.axhline(LINE[t], ls=":", color="r", lw=0.8)
        ax.set_xscale("log", base=2); ax.set_xlabel("base channels c" if t == "cifar" else "model width d")
        ax.set_ylabel("gap (pp)" if t == "cifar" else "gap (% bpb)")
        ax.set_title("CIFAR-10 subset" if t == "cifar" else "char-LM")
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, loc="lower center", ncol=4, bbox_to_anchor=(0.5, -0.1), fontsize=7)
    fig.tight_layout()
    save(fig, out, "fig_scale")


def fig_oat(R, out):
    e5 = R.get("e5")
    if not e5:
        return
    sa = R["e2"]["s_algo"]
    axes = ["n_states", "asym", "gamma", "c2c", "tau_steps", "ref_err"]
    names = {"n_states": "levels", "asym": "asymmetry a", "gamma": "nonlinearity $\\gamma$", "c2c": "write noise $c_{2c}$",
             "tau_steps": "retention $\\tau$ (steps)", "ref_err": "reference error $\\sigma_r$"}
    for task in ("cifar", "lm"):
        keys = sorted([k for k, x in e5["oat"].items() if x["algo"] == sa and x["task"] == task], key=lambda k: e5["oat"][k]["width"])
        if not keys:
            continue
        fig, axs = plt.subplots(2, 3, figsize=(6.8, 4.0))
        for ax, a in zip(axs.flat, axes):
            for k in keys:
                x = e5["oat"][k]
                pts = sorted((float(v), g) for v, g in x["means"][a].items())
                xv = [(1e6 if not math.isfinite(v) else v) for v, _ in pts]
                yv = [min(g, 60) if fin(g) else 60 for _, g in pts]
                ax.plot(xv, yv, "o-", ms=2.5, label=f"w={x['width']}")
            ax.axhline(LINE[task], ls="--", color="r", lw=0.8)
            if a in ("n_states", "tau_steps"):
                ax.set_xscale("log")
            elif a in ("c2c", "ref_err", "asym", "gamma"):
                pass  # linear axis for the parameters whose grids include 0
            ax.set_yscale("symlog", linthresh=1.0)
            yt = [-2, 0, 2, 5, 10, 20, 50]
            ax.set_yticks(yt); ax.set_yticklabels([str(v) for v in yt]); ax.set_ylim(-3, 70)
            ax.set_xlabel(names[a] + (" (1e6 = none)" if a == "tau_steps" else ""))
            ax.set_ylabel("gap (pp)" if task == "cifar" else "gap (% bpb)")
        axs[0, 0].legend(frameon=False)
        fig.suptitle(f"One-at-a-time sensitivity around the protonic base, {ALG[sa]}, "
                     f"{'CIFAR-10 subset' if task == 'cifar' else 'char-LM'}", fontsize=8)
        fig.tight_layout()
        save(fig, out, f"fig_oat_{task}")


def fig_energy(records, out):
    p = os.path.join(records, "ENERGY-SYSTEM.json")
    if not os.path.exists(p):
        return
    e = json.load(open(p, "rb"))
    rows = [(k, r) for k, r in sorted(e["rows"].items()) if k.startswith("lm__") and k.split("__")[1] in list(DEV)[:4]
            and k.split("__")[2] in ("sgd", "cttv2", "agad")]
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    parts = [("mvm", "forward+backward reads (measured chip)", "#1f77b4", "s"), ("lines", "pulse lines + generation", "#ff7f0e", "^"),
             ("device", "device pulses", "#2ca02c", "o"), ("tt", "TT column reads + buffer", "#9467bd", "v"),
             ("total", "analog total", "k", "x")]
    labels = []
    for i, (k, r) in enumerate(rows):
        for pk, plab, c, mk in parts:
            v = r["analog_pj"]["central"][pk]
            if v > 0:
                ax.plot(v, i, mk, color=c, ms=5, label=plab if i == 0 else None)
        _, dev, al = k.split("__")
        labels.append(f"{DEV[dev]} {ALG[al]}")
    ax.axvline(e["gpu_pj"]["central"], color="#444444", lw=2, label="H100 at measured MFU")
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels)
    ax.set_xscale("log"); ax.set_xlabel("energy per weight per row (pJ), char-LM (central estimates)")
    ax.legend(frameon=False, fontsize=6, loc="center left", bbox_to_anchor=(1.01, 0.5))
    save(fig, out, "fig_energy")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--records", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    R = json.load(open(os.path.join(a.records, "RESULTS-PAPER.json"), "rb"))
    for fn in (fig_validation, fig_main, fig_scale, fig_oat):
        try:
            fn(R, a.out)
            print("ok", fn.__name__)
        except Exception as ex:  # a figure failure is reported, never silent
            print("FIGURE FAILED", fn.__name__, type(ex).__name__, ex)
            raise
    fig_energy(a.records, a.out)
    print("ok fig_energy")


if __name__ == "__main__":
    main()
