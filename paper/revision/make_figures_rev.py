"""REVISION figure (build pod; matplotlib): fig_rev_main = gap to FP-SGD and to Adam per device-algorithm cell and task, mean and
95 % interval over 5 seeds, from records/revision/RESULTS-REVISION.json.

    python make_figures_rev.py --results RESULTS-REVISION.json --out tex/figs
"""
import argparse
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

DEVS = [("ecram_li_tang2018", "Li"), ("ecram_mo_kim2019", "MO"), ("protonic_onen2022", "Prot."),
        ("wox_ysz_chen2023", "WOx"), ("widrow1960_claimed", "Mem."), ("ideal1000", "Ideal")]
ALGS = [("sgd", "SGD"), ("ttv2", "TTv2"), ("cttv2", "cTT"), ("agad", "AGAD")]
LINE = {"mnist": 2.0, "cifar": 2.0, "lm": 5.0}
TITLE = {"mnist": "MNIST (pp)", "cifar": "CIFAR-10 subset (pp)", "lm": "Byte LM (% bits/byte)"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    E3 = json.load(open(a.results, "rb"))["e3"]
    fig, axs = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    keys = [(d, al) for d, _ in DEVS for al, _ in ALGS]
    for ax, t in zip(axs, ("mnist", "cifar", "lm")):
        for off, base, col in ((-0.15, "vs_fp", "tab:blue"), (0.15, "vs_adam", "tab:orange")):
            xs, ms, lo, hi = [], [], [], []
            for i, (d, al) in enumerate(keys):
                c = E3.get(t, {}).get("cells", {}).get(f"{d}__{al}", {}).get(base)
                if not c or c["gap"]["lo"] is None:
                    continue
                g = c["gap"]
                xs.append(i + off); ms.append(g["mean"]); lo.append(g["mean"] - g["lo"]); hi.append(g["hi"] - g["mean"])
            ax.errorbar(xs, ms, yerr=[lo, hi], fmt="o", ms=3, color=col, label="vs FP-SGD" if base == "vs_fp" else "vs Adam")
        ax.axhline(LINE[t], ls="--", color="k", lw=0.8)
        ax.axhline(0, color="gray", lw=0.5)
        ax.set_yscale("symlog", linthresh=2.0)
        ax.set_title(TITLE[t], fontsize=9)
    axs[0].legend(fontsize=8, loc="upper right")
    axs[-1].set_xticks(range(len(keys)))
    axs[-1].set_xticklabels([f"{dn} {an}" for d, dn in DEVS for al, an in ALGS], rotation=90, fontsize=7)
    fig.tight_layout()
    os.makedirs(a.out, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(a.out, f"fig_rev_main.{ext}"), dpi=150)
    print("fig_rev_main written")


if __name__ == "__main__":
    main()
