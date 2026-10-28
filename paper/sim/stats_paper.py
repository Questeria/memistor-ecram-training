"""Shared statistics of lane ME-PAPER (PLAN-PAPER.md): t-intervals, seed-paired gaps, the E4 growth rule, and the E5
single-axis thresholds and joint spec. Used by sweep_paper.py (phase e5b) and analyze.py. Standard library only."""
import glob
import json
import math
import os

T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306, 9: 2.262, 10: 2.228}
GAP_LINE = {"mnist": 2.0, "cifar": 2.0, "lm": 5.0, "mnist_gh": 2.0}
# E5 axes: values in the PLAN order; "worse" direction per axis
AXES = {
    "n_states": dict(base=1000, worse="down"),
    "asym": dict(base=0.05, worse="up"),
    "gamma": dict(base=0.2, worse="up"),
    "c2c": dict(base=0.3, worse="up"),
    "tau_steps": dict(base=math.inf, worse="down"),
    "ref_err": dict(base=0.02, worse="up"),
}


def jload(p):
    with open(p, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


def load_phase(rec_dir, phase):
    out = []
    for p in sorted(glob.glob(os.path.join(rec_dir, "runs", phase, "*.json"))):
        r = jload(p)
        r["_name"] = os.path.basename(p)[:-5]
        out.append(r)
    return out


def metric(r):
    """Accuracy in percent (classification) or bits per byte (LM); NaN for a diverged LM."""
    m = r["metric"]
    if "acc" in m:
        return 100.0 * m["acc"]
    b = m.get("bpb")
    return b if (b is not None and math.isfinite(b)) else math.nan


def mean_ci(xs):
    xs = [x for x in xs]
    n = len(xs)
    if n == 0:
        return dict(n=0, mean=None, lo=None, hi=None, sd=None)
    if any(not math.isfinite(x) for x in xs):
        return dict(n=n, mean=math.inf, lo=math.inf, hi=math.inf, sd=None, diverged=sum(not math.isfinite(x) for x in xs))
    m = sum(xs) / n
    if n == 1:
        return dict(n=1, mean=m, lo=None, hi=None, sd=None)
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1))
    h = T975[n - 1] * sd / math.sqrt(n)
    return dict(n=n, mean=m, lo=m - h, hi=m + h, sd=sd, half=h)


def gap_value(task, fp, dev):
    """pp for classification (FP acc - device acc), % for the LM (device bpb / FP bpb - 1)."""
    if task == "lm":
        if not math.isfinite(dev):
            return math.inf
        return 100.0 * (dev / fp - 1.0)
    return fp - dev


def label(task, ci):
    line = GAP_LINE[task]
    if ci["n"] == 0 or ci["mean"] is None:
        return "NOT RUN"
    if ci["mean"] == math.inf:
        return "FAIL (diverged)"
    if ci["lo"] is None:
        return "pass (n=1)" if ci["mean"] < line else "fail (n=1)"
    if ci["hi"] < line:
        return "PASS"
    if ci["lo"] > line:
        return "FAIL"
    return "UNRESOLVED"


def paired_gaps(task, fp_by_seed, dev_by_seed):
    seeds = sorted(set(fp_by_seed) & set(dev_by_seed))
    return [gap_value(task, fp_by_seed[s], dev_by_seed[s]) for s in seeds], seeds


def growth(gaps_by_width):
    """E4 rule. gaps_by_width: {width: ci} for >= 3 widths, ascending."""
    ws = sorted(gaps_by_width)
    lo_w, mid_w, hi_w = ws[0], ws[len(ws) // 2], ws[-1]
    a, m, b = gaps_by_width[lo_w], gaps_by_width[mid_w], gaps_by_width[hi_w]
    if any(x["mean"] is None for x in (a, m, b)):
        return "INCOMPLETE"
    hw = max(a.get("half") or 0.0, b.get("half") or 0.0)
    if b["mean"] - a["mean"] > hw and m["mean"] >= a["mean"]:
        return "GROWS"
    if a["mean"] - b["mean"] > hw and m["mean"] <= a["mean"]:
        return "SHRINKS"
    return "FLAT"


def axis_value(spec, axis):
    if axis == "gamma":
        return spec.get("gamma_up")
    if axis == "tau_steps":
        v = spec.get("tau_steps", math.inf)
        return math.inf if v in ("inf", None) else float(v)
    return spec.get(axis)


def oat_point_axis(spec, base):
    """Which single axis this spec moves from the base (None for the base itself)."""
    moved = [ax for ax in AXES if axis_value(spec, ax) != axis_value(base, ax)]
    return moved[0] if len(moved) == 1 else (None if not moved else "multi")


def _interp(v_p, g_p, v_f, g_f, X, axis):
    if not (math.isfinite(v_p) and math.isfinite(v_f)) or g_f == g_p:
        return None
    t = (X - g_p) / (g_f - g_p)
    if v_p > 0 and v_f > 0 and axis in ("n_states", "tau_steps", "gamma", "asym", "c2c", "ref_err"):
        return math.exp(math.log(v_p) + t * (math.log(v_f) - math.log(v_p)))
    return v_p + t * (v_f - v_p)


def thresholds(points, X):
    """points: {axis: {value: mean gap}} including the base value (key AXES[axis]['base']).
    Returns per axis: dict(threshold grid value, interpolated value, status)."""
    out = {}
    for ax, d in points.items():
        base = AXES[ax]["base"]
        vals = sorted(d)
        worse = [v for v in vals if (v < base if AXES[ax]["worse"] == "down" else v > base)]
        better = [v for v in vals if (v > base if AXES[ax]["worse"] == "down" else v < base)]
        # walk outward from the base: in the worse direction for the threshold, the better one if the base fails
        if AXES[ax]["worse"] == "down":
            worse = sorted(worse, reverse=True)
            better = sorted(better)
        else:
            worse = sorted(worse)
            better = sorted(better, reverse=True)
        if base not in d:
            out[ax] = dict(status="base missing")
            continue
        if d[base] < X:
            last, lastg = base, d[base]
            res = dict(status="base passes", threshold=base, interp=None, first_fail=None)
            for v in worse:
                if d[v] < X:
                    last, lastg = v, d[v]
                    res.update(threshold=v)
                else:
                    res.update(first_fail=v, interp=_interp(last, lastg, v, d[v], X, ax))
                    break
            if res["first_fail"] is None:
                res["status"] = "passes over the whole grid"
            out[ax] = res
        else:
            res = dict(status="base fails", threshold=None, interp=None)
            prev, prevg = base, d[base]
            for v in better:
                if d[v] < X:
                    res.update(status="needs improvement", threshold=v, interp=_interp(v, d[v], prev, prevg, X, ax))
                    break
                prev, prevg = v, d[v]
            if res["threshold"] is None:
                res["status"] = "not reachable on this grid"
            out[ax] = res
    return out


def step_toward_base(axis, value, grid):
    """The grid neighbour of value on the side of the base (the base itself stays)."""
    base = AXES[axis]["base"]
    srt = sorted(grid)
    i = srt.index(value)
    if value == base:
        return value
    if (value < base):
        return srt[min(i + 1, len(srt) - 1)]
    return srt[max(i - 1, 0)]
