"""Version 11 (review 8, findings 1 and 9): Figure 3 (fig_main) must draw every cell at its mean with the interval [lo, hi] of its
result, and its legend must not overlap any axis label or tick label.

The check runs make_figures.fig_main on records/RESULTS-PAPER.json with Axes.errorbar wrapped and the figure kept: every drawn
point must have x = mean, x - left bar = lo and x + right bar = hi (to 1e-9), every finite cell must be drawn once, and the
legend's box must not intersect the box of any x-axis label or x tick label.  It is shown to FAIL on version 10's make_figures.py
(git HEAD before version 11), which drew max(mean, 0.05) with the bars of the true mean and put the legend over an axis label.

    python -B revision10/check_fig_main.py [--json out.json]           (from paper/; matplotlib 3.9.2)
    python -B revision10/check_fig_main.py --selftest [--json out.json]
"""
import importlib.util
import json
import math
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
V10_COMMIT = "604285ff4"                                  # version 10 of the paper


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def check(mf_path):
    MF = load_module(mf_path, "mf_under_test")
    plt = MF.plt
    from matplotlib.axes import Axes
    R = json.load(open(os.path.join(P, "records", "RESULTS-PAPER.json"), "rb"))
    drawn, kept = [], {}
    orig_eb = Axes.errorbar

    def eb(self, x, y, xerr=None, **kw):
        drawn.append(dict(ax=self, x=float(x), y=float(y),
                          left=None if xerr is None else float(xerr[0][0]), right=None if xerr is None else float(xerr[1][0])))
        return orig_eb(self, x, y, xerr=xerr, **kw)

    def keep(fig, out, name):
        kept["fig"] = fig
    Axes.errorbar, MF.save = eb, keep
    try:
        with tempfile.TemporaryDirectory() as td:
            MF.fig_main(R, td)
    finally:
        Axes.errorbar = orig_eb
    fig = kept["fig"]
    tasks = [t for t in ("mnist", "cifar", "lm") if t in R["e3"]]
    task_of = {id(ax): t for ax, t in zip(fig.axes, tasks)}    # the panels in fig_main's order (titles are set after drawing)
    for d in drawn:
        d["ax"] = task_of.get(id(d["ax"]))
    want = []
    for t in ("mnist", "cifar", "lm"):
        for di, d in enumerate(MF.DEV):
            for ai, a in enumerate(("sgd", "ttv2", "cttv2", "agad")):
                c = R["e3"][t]["cells"].get(f"{d}__{a}")
                if c and MF.fin(c["gap"]["mean"]):
                    want.append(dict(task=t, cell=f"{d}__{a}", ax=t, y=di + (ai - 1.5) * 0.18, **{k: c["gap"].get(k) for k in ("mean", "lo", "hi")}))
    bad = []
    for w in want:
        m = [d for d in drawn if d["ax"] == w["ax"] and abs(d["y"] - w["y"]) < 1e-9]
        if len(m) != 1:
            bad.append(dict(cell=w["cell"], task=w["task"], problem="drawn %d times" % len(m)))
            continue
        d = m[0]
        errs = [abs(d["x"] - w["mean"])]
        if MF.fin(w["lo"]):
            errs += [abs(d["x"] - d["left"] - w["lo"]), abs(d["x"] + d["right"] - w["hi"])]
        if max(errs) > 1e-9:
            bad.append(dict(cell=w["cell"], task=w["task"], mean=w["mean"], drawn_x=d["x"], lo=w["lo"], hi=w["hi"],
                            drawn_lo=d["x"] - d["left"] if d["left"] is not None else None,
                            drawn_hi=d["x"] + d["right"] if d["right"] is not None else None))
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    lg = fig.legends[0].get_window_extent(r)
    hits = []
    for ax in fig.axes:
        for tx in [ax.xaxis.label] + [t for t in ax.get_xticklabels() if t.get_text()]:
            bb = tx.get_window_extent(r)
            if bb.overlaps(lg):
                hits.append(dict(ax=ax.get_title(), text=tx.get_text()))
    plt.close(fig)
    return dict(cells_expected=len(want), points_drawn=len(drawn), misdrawn=bad, legend_overlaps=hits,
                ok=not bad and not hits and len(drawn) == len(want))


def main():
    res = dict(current=check(os.path.join(P, "make_figures.py")))
    if "--selftest" in sys.argv:
        old = subprocess.run(["git", "-C", P, "show", V10_COMMIT + ":./make_figures.py"], capture_output=True, check=True).stdout
        with tempfile.TemporaryDirectory() as td:
            p = os.path.join(td, "make_figures_v10.py")
            open(p, "wb").write(old)
            v10 = check(p)
        res["selftest"] = dict(v10_fails=v10["ok"] is False, v10_misdrawn=[(b["task"], b["cell"]) for b in v10["misdrawn"]],
                               v10_legend_overlaps=len(v10["legend_overlaps"]))
        res["selftest"]["ok"] = res["selftest"]["v10_fails"] and len(v10["misdrawn"]) >= 1 and v10["legend_overlaps"] != []
    res["all_ok"] = res["current"]["ok"] and res.get("selftest", {"ok": True})["ok"]
    print("cells", res["current"]["cells_expected"], "| drawn", res["current"]["points_drawn"], "| misdrawn", len(res["current"]["misdrawn"]),
          "| legend overlaps", len(res["current"]["legend_overlaps"]),
          ("| v10 fails: %s %s, %d legend overlaps" % (res["selftest"]["v10_fails"], res["selftest"]["v10_misdrawn"],
                                                     res["selftest"]["v10_legend_overlaps"])) if "selftest" in res else "",
          "|", "FIG_MAIN_OK" if res["all_ok"] else "FIG_MAIN_NOT_OK")
    if "--json" in sys.argv:
        jp = sys.argv[sys.argv.index("--json") + 1]
        os.makedirs(os.path.dirname(os.path.abspath(jp)), exist_ok=True)
        open(jp, "wb").write((json.dumps(res, indent=1) + "\n").encode("utf-8"))
    sys.exit(0 if res["all_ok"] else 1)


if __name__ == "__main__":
    main()
