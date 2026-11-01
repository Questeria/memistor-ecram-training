"""REVISION: every number of the revised results, from records/revision/runs/{e3,e4,e5} (PLAN-REVISION.md section 5).
Writes records/revision/RESULTS-REVISION.json, tex/numbers_rev.tex (macros \\RV...) and tex/tables/rev_*.tex.

    python -B revision/analyze_rev.py
"""
import glob
import json
import math
import os
import re
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "..")
REC = os.path.join(P, "records", "revision")
TEX = os.path.join(P, "tex")
LINE = {"mnist": 2.0, "cifar": 2.0, "lm": 5.0}
# Student t quantiles: one-sided 0.975 and 0.95 for df 1..30 (df > 30: the normal value). REVIEW 12: no longer used by the
# analysis (ci() and width_paired() take t_quantile, as width_verdict() has since review 9); kept for the tests of earlier versions.
T975 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228, 2.201, 2.179, 2.160, 2.145, 2.131, 2.120,
        2.110, 2.101, 2.093, 2.086, 2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042]
T95 = [6.314, 2.920, 2.353, 2.132, 2.015, 1.943, 1.895, 1.860, 1.833, 1.812, 1.796, 1.782, 1.771, 1.761, 1.753, 1.746,
       1.740, 1.734, 1.729, 1.725, 1.721, 1.717, 1.714, 1.711, 1.708, 1.706, 1.703, 1.701, 1.699, 1.697]
DEVS = ["ecram_li_tang2018", "ecram_mo_kim2019", "protonic_onen2022", "wox_ysz_chen2023", "widrow1960_claimed"]
DEVLAB = {"ecram_li_tang2018": "Li-ECRAM", "ecram_mo_kim2019": "MO-ECRAM", "protonic_onen2022": "Protonic-inspired",
          "wox_ysz_chen2023": "W/WO$_x$ ECRAM", "widrow1960_claimed": "Memistor (optimistic)"}
ALGLAB = {"sgd": "SGD", "ttv2": "TTv2", "cttv2": "c-TTv2", "agad": "AGAD"}


def tq(table, df):
    df = int(math.floor(df))
    return table[df - 1] if 1 <= df <= 30 else (1.960 if table is T975 else 1.645)


def _betacf(a, b, x):
    """Continued fraction of the regularized incomplete beta function (modified Lentz)."""
    tiny = 1e-300
    c, d = 1.0, 1.0 - (a + b) * x / (a + 1.0)
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 400):
        for aa in (m * (b - m) * x / ((a + 2 * m - 1) * (a + 2 * m)),
                   -(a + m) * (a + b + m) * x / ((a + 2 * m) * (a + 2 * m + 1))):
            d = 1.0 + aa * d
            d = 1.0 / (d if abs(d) > tiny else tiny)
            c = 1.0 + aa / c
            c = c if abs(c) > tiny else tiny
            h *= d * c
        if abs(d * c - 1.0) < 1e-15:
            return h
    raise ArithmeticError("incomplete beta: no convergence")


def _ibeta(a, b, x):
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_cdf(t, df):
    """Student-t CDF at a real df > 0."""
    tail = 0.5 * _ibeta(df / 2.0, 0.5, df / (df + t * t))
    return 1.0 - tail if t > 0 else tail


def t_quantile(p, df):
    """Student-t quantile (0.5 < p < 1) at a real df > 0, by bisection on t_cdf. REVIEW 9 (DEVIATIONS R9): the Welch interval
    takes it at the Welch-Satterthwaite df itself; tq() reads its table at the df floored, which the plan does not state."""
    lo, hi = 0.0, 2.0
    while t_cdf(hi, df) < p:
        hi *= 2.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if t_cdf(mid, df) < p else (lo, mid)
    return 0.5 * (lo + hi)


def ci(xs):
    n = len(xs)
    m = st.fmean(xs)
    if n < 2:
        return dict(mean=m, n=n, lo=None, hi=None, sd=None, half=None)
    sd = st.stdev(xs)
    h = t_quantile(0.975, n - 1) * sd / math.sqrt(n)   # REVIEW 12: the exact quantile (versions 2-14: tq's three-decimal table)
    return dict(mean=m, n=n, lo=m - h, hi=m + h, sd=sd, half=h)


def label(task, c):
    if c is None or c["lo"] is None:
        return "N/A"
    return "PASS" if c["hi"] <= LINE[task] else ("FAIL" if c["lo"] > LINE[task] else "UNRESOLVED")


def metric(r):
    if r.get("diverged"):
        return None
    m = r["metric"]
    return m["acc"] if "acc" in m else m["bpb"]


def gap(task, ref, dev):
    if ref is None or dev is None:
        return float("inf")
    return 100 * (ref - dev) if task != "lm" else 100 * (dev / ref - 1)


def load(phase):
    out = []
    for p in sorted(glob.glob(os.path.join(REC, "runs", phase, "*.json"))):
        r = json.load(open(p, "rb"))
        r["_extra"] = r["tag"].split("__")[-1] if r["tag"].count("__") >= 6 else ""
        out.append(r)
    return out


def arm_key(r):
    if r["arm"] == "fp_adam":
        return "adam"
    if r["arm"] == "fp_sgd":
        return "fp" if r["algo"] == "sgd" else "digital__" + r["algo"]
    return r["spec"]["name"] + "__" + r["algo"]


def cellstats(task, ref_by_seed, by_seed):
    gs = [gap(task, ref_by_seed[s], by_seed[s]) for s in sorted(by_seed) if s in ref_by_seed]
    gs = [g for g in gs]
    if not gs:
        return None
    c = ci(gs) if all(math.isfinite(g) for g in gs) else dict(mean=float("inf"), n=len(gs), lo=float("inf"),
                                                               hi=float("inf"), sd=None, half=None)
    return dict(gap=c, label=label(task, c), gaps=gs)


def e3():
    rs = load("e3")
    out = {}
    for task in ("mnist", "cifar", "lm"):
        by = {}
        for r in rs:
            if r["task"] == task:
                by.setdefault(arm_key(r), {})[r["seed"]] = metric(r)
        if "fp" not in by:
            continue
        fp, adam = by["fp"], by.get("adam", {})
        cells = {}
        for k, v in by.items():
            if k == "fp":
                continue
            ms = [x for x in v.values() if x is not None]
            cells[k] = dict(metric=ci(ms) if ms else None, n=len(v), vs_fp=cellstats(task, fp, v),
                            vs_adam=cellstats(task, adam, v) if adam and k != "adam" else None)
        out[task] = dict(fp=ci([x for x in fp.values() if x is not None]), cells=cells)
    # summaries
    summ = {}
    for base in ("vs_fp", "vs_adam"):
        for algo in ("sgd", "ttv2", "cttv2", "agad"):
            for lab in ("PASS", "FAIL", "UNRESOLVED"):
                summ[f"{base}_{algo}_{lab}"] = sum(1 for t in out for k, c in out[t]["cells"].items()
                                                   if k.endswith("__" + algo) and not k.startswith("digital")
                                                   and c.get(base) and c[base]["label"] == lab)
        summ[f"{base}_pass_total"] = sum(1 for t in out for k, c in out[t]["cells"].items() if k.split("__")[0] in DEVS
                                         and c.get(base) and c[base]["label"] == "PASS")
        summ[f"{base}_devices_all_three_same_algo"] = sorted(
            f"{d}__{a}" for d in DEVS for a in ("sgd", "ttv2", "cttv2", "agad")
            if all(out.get(t, {}).get("cells", {}).get(f"{d}__{a}", {}).get(base) and
                   out[t]["cells"][f"{d}__{a}"][base]["label"] == "PASS" for t in ("mnist", "cifar", "lm")))
    return out, summ


def welch(a, b):
    """D = mean(a) - mean(b), its SE and Welch df."""
    ma, mb = st.fmean(a), st.fmean(b)
    va, vb = st.variance(a) / len(a), st.variance(b) / len(b)
    se = math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1)) if se > 0 else 1e9
    return ma - mb, se, df


def width_verdict(task, gl, gh):
    m = LINE[task]
    if any(not math.isfinite(x) for x in gl + gh):
        return dict(verdict="INCONCLUSIVE (a run diverged)")
    D, se, df = welch(gh, gl)
    t90 = t_quantile(0.95, df)        # REVIEW 9 / DEVIATIONS R9: at the Welch df itself, not floored
    lo90, hi90 = D - t90 * se, D + t90 * se
    if -m < lo90 and hi90 < m:
        v = "EQUIVALENT"
    elif lo90 > 0:
        v = "GROWS"
    elif hi90 < 0:
        v = "SHRINKS"
    elif hi90 < m:
        v = "NO EVIDENCE OF GROWTH BEYOND THE MARGIN"
    else:
        v = "INCONCLUSIVE"
    return dict(D=D, se=se, df=df, ci90=[lo90, hi90], margin=m, verdict=v)


def width_paired(task, gl, gh):
    """REVISION 2 (DEVIATIONS R4, added after review 2): the endpoint contrast paired by seed (the arms of one seed share
    the example order across widths, and within a width also the logical initialisation), with the registered decision order."""
    m = LINE[task]
    if any(not math.isfinite(x) for x in gl + gh):
        return dict(verdict="INCONCLUSIVE (a run diverged)")
    dd = [h - l for h, l in zip(gh, gl)]
    n = len(dd)
    D, se = st.fmean(dd), st.stdev(dd) / math.sqrt(n)
    t90 = t_quantile(0.95, n - 1)    # REVIEW 12: the exact quantile, as the Welch interval (versions 2-14: tq's three-decimal table)
    lo90, hi90 = D - t90 * se, D + t90 * se
    if -m < lo90 and hi90 < m:
        v = "EQUIVALENT"
    elif lo90 > 0:
        v = "GROWS"
    elif hi90 < 0:
        v = "SHRINKS"
    elif hi90 < m:
        v = "NO EVIDENCE OF GROWTH BEYOND THE MARGIN"
    else:
        v = "INCONCLUSIVE"
    return dict(D=D, se=se, df=n - 1, ci90=[lo90, hi90], margin=m, verdict=v, diffs=dd)


def e4():
    rs = load("e4")
    out = {}
    for task in ("cifar", "lm"):
        by = {}
        for r in rs:
            if r["task"] == task:
                by.setdefault((arm_key(r), r["width"]), {})[r["seed"]] = metric(r)
        ws = sorted({w for _, w in by})
        if not ws:
            continue
        arms = sorted({k for k, _ in by if k != "fp"})
        res = {}
        for a in arms:
            per = {}
            for w in ws:
                if (a, w) in by and ("fp", w) in by:
                    per[w] = cellstats(task, by[("fp", w)], by[(a, w)])
            if len(per) == len(ws):
                res[a] = dict(widths=per, test=width_verdict(task, per[ws[0]]["gaps"], per[ws[-1]]["gaps"]),
                              paired=width_paired(task, per[ws[0]]["gaps"], per[ws[-1]]["gaps"]))
        out[task] = dict(widths=ws, arms=res, fp={w: ci([x for x in by[("fp", w)].values() if x is not None])
                                                   for w in ws if ("fp", w) in by})
    return out


AX = {"n_states": ("down", 1000), "asym": ("up", 0.05), "asym_fixedsp": ("up", 0.05), "gamma": ("up", 0.2),
      "c2c": ("up", 0.3), "ref_err": ("up", 0.02), "tau_steps": ("down", math.inf)}


def e5(e3out):
    rs = load("e5") + load("e5fix")  # REVISION 2: e5fix = the recentred base (0.05) and the zero point (PLAN-REVISION-2.md)
    e3r = load("e3")
    out = {}
    for algo, task, w in [(al, t, w) for al in sorted({r["algo"] for r in rs}) for t, w in (("cifar", 32), ("lm", 128))]:
        fp = {r["seed"]: metric(r) for r in e3r if r["task"] == task and arm_key(r) == "fp"}
        pts = {}
        for r in rs:
            if r["task"] == task and r["algo"] == algo:
                pts.setdefault(r["spec"]["name"], {})[r["seed"]] = metric(r)
        if not pts or not fp:
            continue
        cells = {nm: cellstats(task, fp, v) for nm, v in pts.items()}
        axes = {}
        for ax, (worse, basev) in AX.items():
            vals = {}
            for nm, c in cells.items():
                m_ = re.match(r"^(%s)(.+)$" % ax, nm)
                if nm == "base":
                    if ax != "asym_fixedsp":  # REVISION 2: the unrecentred base is not a fixed-symmetry point
                        vals[basev] = c
                elif m_ and not (ax == "asym" and nm.startswith("asym_fixedsp")):
                    v = m_.group(2)
                    vals[math.inf if v == "inf" else float(v)] = c
            # REVISION 2 (review 2 finding 4): the v2 code copied the unrecentred base in as this axis's anchor; the anchor
            # is now the recentred run asym_fixedsp0.05 itself (absent -> the axis is not established)
            order = sorted(vals, reverse=(worse == "down"))  # from the best end to the worst
            thr, ok_run = None, True
            if vals.get(basev) is None:
                status = "not established (no run at the base value)"
            elif vals[basev]["label"] != "PASS":
                status = "not established (the base point does not pass)"
            else:
                for v in order:
                    if vals[v]["label"] == "PASS" and ok_run:
                        thr = v
                    else:
                        ok_run = False
                status = "threshold" if thr is not None else "not established"
            rng = {}
            if ax in ("asym", "asym_fixedsp"):
                for v in vals:
                    us = 0.0 if ax == "asym_fixedsp" else min(1.0, v / (2 * 0.2))
                    rng[v] = dict(u_star=us, positive_range=1 - us, negative_range=1 + us)
            axes[ax] = dict(points={str(v): dict(gap=vals[v]["gap"], label=vals[v]["label"]) for v in order if vals[v]},
                            weakest_passing=thr, status=status, signed_range=rng or None)
        out[f"{algo}__{task}"] = dict(algo=algo, task=task, width=w, axes=axes, base=cells.get("base"))
    return out


def fmt(x, d=2):
    if x is None:
        return "--"
    if isinstance(x, float) and not math.isfinite(x):
        return "div."
    return f"{x:.{d}f}"


def name(s):
    return "RV" + re.sub(r"[^A-Za-z]", "", s.title().replace("0", "Zero").replace("1", "One").replace("2", "Two")
                         .replace("3", "Three").replace("4", "Four").replace("5", "Five").replace("6", "Six")
                         .replace("7", "Seven").replace("8", "Eight").replace("9", "Nine"))


def main():
    E3, summ = e3()
    E4 = e4()
    E5 = e5(E3)
    res = dict(schema="altone.x1000.me-revision.results.v1", e3=E3, e3_summary=summ, e4=E4, e5=E5, lines=LINE)
    with open(os.path.join(REC, "RESULTS-REVISION.json"), "wb") as f:
        f.write((json.dumps(res, indent=1, sort_keys=True, default=str) + "\n").encode("utf-8"))
    macros = {}
    for k, v in summ.items():
        if isinstance(v, int):
            macros[name(k)] = str(v)
    for t, d in E3.items():
        macros[name(f"{t} fp")] = fmt(d["fp"]["mean"] * (100 if t != "lm" else 1), 2 if t != "lm" else 3)
        for k, c in d["cells"].items():
            if c.get("metric"):
                macros[name(f"{t} {k} metric")] = fmt(c["metric"]["mean"] * (100 if t != "lm" else 1), 2 if t != "lm" else 3)
            for base in ("vs_fp", "vs_adam"):
                if c.get(base):
                    g = c[base]["gap"]
                    macros[name(f"{t} {k} {base} gap")] = fmt(g["mean"])
                    macros[name(f"{t} {k} {base} lo")] = fmt(g["lo"])
                    macros[name(f"{t} {k} {base} hi")] = fmt(g["hi"])
                    macros[name(f"{t} {k} {base} label")] = c[base]["label"]
    for t, d in E4.items():
        for w, c in d["fp"].items():
            macros[name(f"e4 {t} fp w{w}")] = fmt(c["mean"] * (100 if t != "lm" else 1), 2 if t != "lm" else 3)
        for a, x in d["arms"].items():
            T = x["test"]
            macros[name(f"e4 {t} {a} verdict")] = T["verdict"].lower()
            if "D" in T:
                macros[name(f"e4 {t} {a} D")] = fmt(T["D"])
                macros[name(f"e4 {t} {a} lo")], macros[name(f"e4 {t} {a} hi")] = fmt(T["ci90"][0]), fmt(T["ci90"][1])
            Pd = x["paired"]
            macros[name(f"e4 {t} {a} paired verdict")] = Pd["verdict"].lower()
            if "D" in Pd:
                macros[name(f"e4 {t} {a} paired lo")], macros[name(f"e4 {t} {a} paired hi")] = fmt(Pd["ci90"][0]), fmt(Pd["ci90"][1])
            for w, c in x["widths"].items():
                macros[name(f"e4 {t} {a} w{w} gap")] = fmt(c["gap"]["mean"])
        vs = [x["test"]["verdict"] for x in d["arms"].values()]
        for v in set(vs):
            macros[name(f"e4 {t} n {v}")] = str(vs.count(v))
        vp = [x["paired"]["verdict"] for x in d["arms"].values()]
        for v in set(vp):
            macros[name(f"e4 {t} n paired {v}")] = str(vp.count(v))
    for t, d in E5.items():
        base = d.get("base")
        if base:
            macros[name(f"spec {t} base gap")] = fmt(base["gap"]["mean"])
            macros[name(f"spec {t} base label")] = base["label"]
        for ax, x in d["axes"].items():
            v = x["weakest_passing"]
            macros[name(f"spec {t} {ax} thr")] = ("not established" if v is None else
                                                  ("$\\infty$" if isinstance(v, float) and math.isinf(v) else f"{v:g}"))
            for k, p in x["points"].items():
                kk = k.replace(".", "p").replace("inf", "Inf")
                macros[name(f"spec {t} {ax} at {kk} gap")] = fmt(p["gap"]["mean"])
                macros[name(f"spec {t} {ax} at {kk} label")] = p["label"]
    macros.update(extra_macros())
    macros.update(e3_macros(E3))
    with open(os.path.join(TEX, "numbers_rev.tex"), "wb") as f:
        f.write(("% generated by revision/analyze_rev.py from records/revision/ (do not edit)\n" +
                 "".join(f"\\newcommand{{\\{k}}}{{{v}}}\n" for k, v in sorted(macros.items()))).encode("utf-8"))
    tables(E3, E4, E5)
    print(json.dumps(summ, indent=0)[:1500])
    for t, d in E4.items():
        for a, x in d["arms"].items():
            print("e4", t, a, x["test"].get("verdict"), fmt(x["test"].get("D")))
    for t, d in E5.items():
        for ax, x in d["axes"].items():
            print("e5", t, ax, x["status"], x["weakest_passing"])


def e3_macros(E3):
    m = {}
    if not E3:
        return m
    pub = [d for d in DEVS if not d.startswith("widrow")]
    sg = [E3[t]["cells"].get(f"{d}__sgd", {}).get("vs_fp") for t in E3 for d in pub]
    m["RVSgdPubN"] = str(len(sg))
    m["RVSgdPubFail"] = str(sum(1 for c in sg if c and c["label"] == "FAIL"))
    for base, tag in (("vs_fp", "Fp"), ("vs_adam", "Adam")):
        allp = [f"{DEVLAB[d]} {ALGLAB[a]}" for d in DEVS for a in ("sgd", "ttv2", "cttv2", "agad")
                if all(E3.get(t, {}).get("cells", {}).get(f"{d}__{a}", {}).get(base) and
                       E3[t]["cells"][f"{d}__{a}"][base]["label"] == "PASS" for t in ("mnist", "cifar", "lm"))]
        m[f"RVAllThree{tag}N"] = str(len(allp))
        m[f"RVAllThree{tag}List"] = ", ".join(allp) if allp else "none"
        for t in E3:
            cs = {k: c[base] for k, c in E3[t]["cells"].items() if k.split("__")[0] in DEVS and c.get(base)}
            m[f"RV{t.title()}{tag}PassN"] = str(sum(1 for c in cs.values() if c["label"] == "PASS"))
            m[f"RV{t.title()}{tag}CellN"] = str(len(cs))
            k = min(cs, key=lambda x: cs[x]["gap"]["mean"])
            m[f"RV{t.title()}{tag}BestCell"] = f"{DEVLAB[k.split('__')[0]]} {ALGLAB[k.split('__')[1]]}"
            m[f"RV{t.title()}{tag}BestGap"] = fmt(cs[k]["gap"]["mean"])
    if "lm" in E3 and E3["lm"]["cells"].get("adam"):
        m["RVLmFpSgdVsAdamPct"] = fmt(100 * (E3["lm"]["fp"]["mean"] / E3["lm"]["cells"]["adam"]["metric"]["mean"] - 1))
    for t in E3:
        m[f"RV{t.title()}FpSd"] = fmt(E3[t]["fp"]["sd"] * (100 if t != "lm" else 1), 2 if t != "lm" else 3)
    # clipping and reset statistics over the device runs of E3
    clip, lost, resid, share = [], [], [], []
    for r in load("e3"):
        if r["arm"] != "device" or r["spec"]["name"] not in DEVS:
            continue
        for l in r["layers"]:
            clip.append(l.get("clip_call_frac", 0.0))
            lost.append(l.get("update_lost_frac", 0.0))
            if l.get("reset_resid_steps") is not None and l.get("reset") == "pulse":
                resid.append(l["reset_resid_steps"])
        tot = sum(l["pulses"] for l in r["layers"])
        if tot and any(l.get("reset") == "pulse" for l in r["layers"]):
            share.append(sum(l.get("reset_pulses", 0.0) for l in r["layers"]) / tot)
    m["RVClipMaxPct"] = fmt(100 * max(clip), 2)
    m["RVLostMaxPct"] = fmt(100 * max(lost), 1)
    by = {}
    for r in load("e3"):
        if r["arm"] != "device" or r["spec"]["name"] not in DEVS:
            continue
        fam = "sgd" if r["algo"] == "sgd" else "tt"
        for i, l in enumerate(r["layers"]):
            by.setdefault((r["task"], fam, i), []).append(l.get("update_lost_frac", 0.0))
    for task in ("mnist", "cifar", "lm"):
        for fam in ("sgd", "tt"):
            v = [st.fmean(x) for (t, f, i), x in by.items() if t == task and f == fam]
            if v:
                m[f"RVLost{task.title()}{fam.title()}LayerMeanMaxPct"] = fmt(100 * max(v), 1)
    m["RVLostSgdMaxPct"] = fmt(100 * max(max(x) for (t, f, i), x in by.items() if f == "sgd"), 1)
    if resid:
        m["RVResetResidMean"], m["RVResetResidMax"] = fmt(st.fmean(resid)), fmt(max(resid))
        m["RVResetShareMean"] = fmt(100 * st.fmean(share), 1)
    # REVISION 2: pooled over reset events (each reset weight is re-read tt_reset_iters - 1 times, so the event count is
    # reset_extra_reads / (iters - 1)) and over pulses; and per device
    wr = nr = rp = tp = 0.0
    per = {}
    for r in load("e3"):
        if r["arm"] != "device" or r["spec"]["name"] not in DEVS:
            continue
        it = (r.get("ucfg") or {}).get("tt_reset_iters", 2)
        pl = [l for l in r["layers"] if l.get("reset") == "pulse" and l.get("reset_resid_steps") is not None]
        if not pl:
            continue
        q = per.setdefault(r["spec"]["name"], [0.0, 0.0, 0.0])
        for l in pl:
            n = l["reset_extra_reads"] / max(1, it - 1)
            wr += l["reset_resid_steps"] * n
            nr += n
            q[0] += l["reset_resid_steps"] * n
            q[1] += n
            q[2] = max(q[2], l["reset_resid_steps"])
        rp += sum(l.get("reset_pulses", 0.0) for l in r["layers"])
        tp += sum(l["pulses"] for l in r["layers"])
    if nr:
        m["RVResetResidPooled"] = fmt(wr / nr)
        m["RVResetSharePooled"] = fmt(100 * rp / tp, 2)
        for dname, q in per.items():
            m[name(f"reset resid pooled {dname}")] = fmt(q[0] / q[1], 1)
            m[name(f"reset resid max {dname}")] = fmt(q[2], 0)
    lostl = [(l.get("update_lost_frac", 0.0), r["task"], r["spec"]["name"], r["algo"], i) for r in load("e3")
             if r["arm"] == "device" and r["spec"]["name"] in DEVS for i, l in enumerate(r["layers"])]
    w = max(lostl)
    m["RVLostWorstTask"], m["RVLostWorstDev"], m["RVLostWorstAlg"] = w[1].upper(), DEVLAB[w[2]], ALGLAB[w[3]]
    return m


def extra_macros():
    """Numbers of the review checks, the catalog, the tests and the diagnostic, quoted in the text."""
    m = {}
    J = lambda n: json.load(open(os.path.join(REC, n), "rb")) if os.path.exists(os.path.join(REC, n)) else None
    v = J("VERIFY-FINDINGS.json")
    if v:
        f2, f4 = v["F2_reset"], v["F4_surrogate"]
        m["RVresetResidPct"] = fmt(100 * f2["residual_fraction"])
        m["RVresetAfter"] = fmt(f2["after_31_up_31_down_surrogate"], 4)
        m["RVresetSp"] = fmt(f2["symmetry_point"], 3)
        m["RVresetPulsesHundredfold"] = f"{f2['pulses_for_100fold']:,.0f}".replace(",", "{,}")
        m["RVorderUpDn"] = fmt(f4["up_then_down"], 3)
        m["RVorderDnUp"] = fmt(f4["down_then_up"], 3)
        m["RVorderBatch"] = fmt(f4["surrogate_batch"], 3)
        f7 = v["F7_baselines"]
        m["RVvOneLiAdamPct"] = fmt(f7["vs_adam_pct_paired"])
        m["RVvOnePerplexityRatio"] = fmt(f7["perplexity_ratio"], 3)
        f5 = v["F5_spec"]
        m["RVvOneCifarBaseGap"] = fmt(f5["cifar_w32_base_gap"])
        m["RVvOneCifarAdmitted"] = fmt(f5["admitted_gap_up_to"])
    c = J("CATALOG-REV.json")
    if c:
        p = c["presets"]["ecram_li_tang2018"]
        m["RVliWmax"], m["RVliWmin"] = f"{p['w_max']:g}", f"{p['w_min']:g}"
        q = c["presets"]["ecram_mo_kim2019"]
        m["RVmoWmax"], m["RVmoWmin"] = f"{q['w_max']:g}", f"{q['w_min']:g}"
        m["RVliGammaDtod"] = f"{p['gamma_up_dtod']:g}"
    a = J("AIHWKIT-COMPARE.json")
    if a:
        P_ = a["presets"]
        ok = all(v["mapping_accepted"] for v in P_.values())
        m["RVaihwVersion"] = a["aihwkit"]
        m["RVaihwVerdict"] = ("matches AIHWKIT's mean responses, device spreads and reached bounds within the pre-registered "
                              "tolerance for both presets" if ok else "does NOT match AIHWKIT within the pre-registered "
                              "tolerance for " + ", ".join(k for k, v in P_.items() if not v["mapping_accepted"]))
        mx = lambda cls, mp: max(P_[cls][f"{nv}__{mp}"]["max_abs_mean_diff"] for nv in ("noise_free", "noisy"))
        m["RVaihwLiMaxDiff"] = fmt(mx("EcRamPresetDevice", "aihwkit_mode"), 4)
        m["RVaihwMoMaxDiff"] = fmt(mx("EcRamMOPresetDevice", "aihwkit_mode"), 4)
        m["RVaihwLiOldMaxDiff"] = fmt(mx("EcRamPresetDevice", "papermap"), 3)
        m["RVaihwMoOldMaxDiff"] = fmt(mx("EcRamMOPresetDevice", "papermap"), 3)
        m["RVaihwAccepted"] = "accepted" if ok else "not accepted"
    en = J("ENERGY-REVISION.json")
    if en:
        rows = {k: r for k, r in en["rows"].items() if k.split("__")[1] in DEVS and not k.split("__")[1].startswith("widrow")}
        for sn, tag in (("chip_12p4", "Chip"), ("system_6p94", "Sys")):
            v = [r["scenarios"][sn]["ratio_per_weight_row"] for r in rows.values()]
            m[f"RVen{tag}Min"], m[f"RVen{tag}Max"] = fmt(min(v), 1), fmt(max(v), 1)
            m[f"RVen{tag}MvmShareMin"] = fmt(100 * min(r["scenarios"][sn]["share"]["mvm"] for r in rows.values()), 1)
        m["RVenGpuPj"] = fmt(en["gpu_pj_central"])
        lo, hi = en["gpu_pj_range_by_mfu"]["planned_30_55"]
        m["RVenGpuPlannedLo"], m["RVenGpuPlannedHi"] = fmt(lo), fmt(hi)
        lo, hi = en["gpu_pj_range_by_mfu"]["measured_38_43"]
        m["RVenGpuMeasLo"], m["RVenGpuMeasHi"] = fmt(lo), fmt(hi)
        for base, tag in (("vs_fp", "Fp"), ("vs_adam", "Adam")):
            for task in ("mnist", "cifar", "lm"):
                m[f"RVenEq{tag}{task.title()}N"] = str(sum(1 for k, r in rows.items() if k.startswith(task + "__")
                                                           and r["equal_quality"][base]["label"] == "PASS"))
                m[f"RVenCells{task.title()}N"] = str(sum(1 for k in rows if k.startswith(task + "__")))
        need = []
        for r in rows.values():
            sc = r["scenarios"]["chip_12p4"]["analog_pj"]
            budget = en["gpu_pj_central"] / 100.0 - (sc["device"] + sc["lines"] + sc["tt"])
            if budget > 0:
                need.append(4.0 / budget)  # TOPS/W: 4 ops (2 MACs) per weight per row, pJ -> TOPS/W
        if need:
            m["RVenNeedTopsMin"], m["RVenNeedTopsMax"] = fmt(min(need), 1), fmt(max(need), 1)
        wr = [r["scenarios"]["chip_12p4"]["ratio_per_weight_row"] for k, r in en["rows"].items() if "widrow" in k]
        if wr:
            mant, ex = f"{max(wr):.1e}".split("e")
            m["RVenWidrowRatioMax"] = f"${mant}\\times10^{{{int(ex)}}}$"
    dv = os.path.join(P, "DEVIATIONS-PAPER.md")
    m["RVnDev"] = str(len(re.findall(r"^## R\d+ ", open(dv, "rb").read().decode("utf-8"), re.M)))
    t = J("TESTS-REV.json")
    if t:
        m["RVnChecks"], m["RVnFaults"] = str(len(t["checks"])), str(len(t["faults"]))
        m["RVtestsAllOk"] = "ALL\\_OK" if t["all_ok"] else "NOT\\_OK"
    d = J("D1-ANALYSIS.json")
    if d:
        m["RVdOneRuns"] = str(d["n_runs"])
        eff = d["effects"]
        for grp, keys in (("Rng", ("rng",)), ("Reset", ("reset_pulse", "reset_alt", "reset_none")),
                          ("Map", ("mapping_aihwkit",)), ("Pub", ("published_ttv2",))):
            for task in ("mnist", "cifar"):
                E = [e for e in eff if e["effect"] in keys and e["cell"].startswith(task)]
                if E:
                    m[f"RVdOne{grp}{task.title()}MaxAbs"] = fmt(max(abs(e["delta_mean"]) for e in E))
                    m[f"RVdOne{grp}{task.title()}NMaterial"] = str(sum(e["material"] for e in E))
                    m[f"RVdOne{grp}{task.title()}N"] = str(len(E))
        sg = [c_["gap"]["mean"] for k, c_ in d["cells"].items() if "|sgd|" in k]
        for task in ("mnist", "cifar"):
            s = [c_["gap"]["mean"] for k, c_ in d["cells"].items() if k.startswith(task) and "|sgd|" in k]
            if s:
                m[f"RVdOneSgd{task.title()}Min"], m[f"RVdOneSgd{task.title()}Max"] = fmt(min(s)), fmt(max(s))
        R_ = [e for e in eff if e["effect"] in ("reset_pulse", "reset_alt", "reset_none")]
        m["RVdOneResetBetterN"] = str(sum(1 for e in R_ if e["delta_mean"] <= 0))
        m["RVdOneResetN"] = str(len(R_))
        m["RVdOneSdOld"] = fmt(d["paired_gap_sd_median"]["old"])
        m["RVdOneSdRev"] = fmt(d["paired_gap_sd_median"]["rev"])
        fp = {}
        for p_ in glob.glob(os.path.join(REC, "runs", "d1", "*__fp_sgd__sgd__*__rev.json")):
            r = json.load(open(p_, "rb"))
            fp.setdefault(r["task"], []).append(r["metric"]["acc"])
        if "cifar" in fp:
            m["RVdOneCifarFpMin"], m["RVdOneCifarFpMax"] = fmt(100 * min(fp["cifar"]), 1), fmt(100 * max(fp["cifar"]), 1)
    return m


def cellfmt(c):
    if not c:
        return "--"
    g = c["gap"]
    if not math.isfinite(g["mean"]):
        return "div."
    return f"{fmt(g['mean'])} [{fmt(g['lo'])}, {fmt(g['hi'])}] {c['label'][0]}"


def d1_table():
    p = os.path.join(REC, "D1-ANALYSIS.json")
    if not os.path.exists(p):
        return
    cells = json.load(open(p, "rb"))["cells"]
    V = [("old", "orig."), ("rev", "ideal"), ("rev_pulse", "pulse"), ("rev_alt", "alt."),
         ("rev_none", "none"), ("rev_pub", "publ.")]
    rows = []
    for task in ("mnist", "cifar"):
        for dev, dl in (("protonic_onen2022", "Protonic-insp."), ("ecram_li_tang2018_papermap", "Li (old map)"),
                        ("ecram_li_tang2018", "Li (AIHWKIT)")):
            for a in ("sgd", "ttv2", "cttv2", "agad"):
                vals = []
                for v, _ in V:
                    k = f"{task}|{dev}|{a}|{v}"
                    if dev == "ecram_li_tang2018" and v == "rev" and a in ("ttv2", "cttv2"):
                        k = None
                    c = cells.get(k) if k else None
                    vals.append(f"{fmt(c['gap']['mean'])}{c['label'][0]}" if c else "")
                if any(vals):
                    rows.append(f"{'MNIST' if task == 'mnist' else 'CIFAR-10ep'} & {dl} & {ALGLAB[a]} & " + " & ".join(vals) + r"\\")
            for a in ("ttv2", "cttv2", "agad"):
                pass
        for a in ():  # DEVIATIONS R2: the rev_digital arms were defined wrongly (transfer quantum 2e-9); not tabled
            c = cells.get(f"{task}|fp_sgd|{a}|rev_digital")
            if c:
                rows.append(f"{'MNIST' if task == 'mnist' else 'CIFAR-10ep'} & ideal device & {ALGLAB[a]} & & & "
                            f"{fmt(c['gap']['mean'])}{c['label'][0]} & & & \\\\")
    open(os.path.join(TEX, "tables", "rev_d1.tex"), "wb").write((
        "\\begin{table*}[t]\\centering\\scriptsize\\caption{Diagnostic D1: mean gap to FP-SGD of the same simulator (pp, 3 seeds; "
        "P/F/U against 2 pp) at the original selections. Columns: orig. = the original simulator; ideal = the repaired "
        "random streams with the original ideal reset; then the reset replaced by the pulse reset (pulse), 31 alternating pulse "
        "pairs (alt.), or none; publ. = the published-style TTv2. The AIHWKIT-mapped Li-ECRAM row uses the pulse reset for TTv2 and c-TTv2. CIFAR here is a "
        "10-epoch slice.}\\label{tab:rev_d1}\n\\begin{tabular}{lllcccccc}\\toprule Task & Device & Alg. & "
        + " & ".join(l for _, l in V) + "\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\\end{table*}\n"
    ).encode("utf-8"))


def energy_table():
    p = os.path.join(REC, "ENERGY-REVISION.json")
    if not os.path.exists(p):
        return
    rows_ = json.load(open(p, "rb"))["rows"]
    rows = []
    for d in DEVS:
        if d.startswith("widrow"):
            continue
        for a in ("sgd", "ttv2", "cttv2", "agad"):
            cells = []
            for t in ("mnist", "cifar", "lm"):
                r = rows_.get(f"{t}__{d}__{a}")
                for base in ("vs_fp", "vs_adam"):
                    if not r:
                        cells.append("--")
                        continue
                    q = r["equal_quality"][base]
                    v = q["ratio_at_equal_quality"]
                    cells.append(f"{v['chip_12p4']:.0f} / {v['system_6p94']:.0f}" if q["label"] == "PASS" else
                                 ("fail" if q["label"] == "FAIL" else "n.e."))
            rows.append(f"{DEVLAB[d]} & {ALGLAB[a]} & " + " & ".join(cells) + r"\\")
    open(os.path.join(TEX, "tables", "rev_energy.tex"), "wb").write((
        "\\begin{table*}[t]\\centering\\scriptsize\\caption{Conditional energy ratios for cells that pass the stated "
        "non-inferiority margin under ideal reads: the GPU-to-analog energy ratio per weight per row (12.4 TOPS/W measured "
        "chip figure / 6.94 TOPS/W projected system figure of the same inference chip, which includes estimated digital "
        "processing), printed only where the cell PASSES against the baseline; fail = the cell FAILS the margin; n.e. = the "
        "criterion is not established (UNRESOLVED). No finite-read operating point is demonstrated.}"
        "\\label{tab:rev_energy}\n\\begin{tabular}{llcccccc}\\toprule & & \\multicolumn{2}{c}{MNIST} & "
        "\\multicolumn{2}{c}{CIFAR} & \\multicolumn{2}{c}{LM}\\\\ Device & Alg. & FP-SGD & Adam & FP-SGD & Adam & FP-SGD & Adam"
        "\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\\end{table*}\n").encode("utf-8"))


def tables(E3, E4, E5):
    os.makedirs(os.path.join(TEX, "tables"), exist_ok=True)
    d1_table()
    energy_table()
    # review item 13: the E1b caption's interval wording (the table itself is generated by analyze.py from the v1 records)
    p = os.path.join(TEX, "tables", "e1b.tex")
    t = open(p, "rb").read().decode("utf-8")
    t2 = t.replace("mean and range over 2 seeds as a t-interval", "mean and 95 \\% $t$ interval, $n=2$")
    if t2 != t:
        open(p, "wb").write(t2.encode("utf-8"))
    for base, cap in (("vs_fp", "FP-SGD at the same learning rate"), ("vs_adam", "digital Adam (its own selected learning rate)")):
        rows = []
        for d in DEVS:
            for a in ("sgd", "ttv2", "cttv2", "agad"):
                k = f"{d}__{a}"
                rows.append(f"{DEVLAB[d]} & {ALGLAB[a]} & " + " & ".join(
                    cellfmt(E3.get(t, {}).get("cells", {}).get(k, {}).get(base)) for t in ("mnist", "cifar", "lm")) + r"\\")
        for a in ("sgd", "ttv2", "cttv2", "agad"):  # DEVIATIONS R2: the ideal 1000-level device replaces the digital arms
            k = f"ideal1000__{a}"
            rows.append(f"Ideal 1000-level & {ALGLAB[a]} & " + " & ".join(
                cellfmt(E3.get(t, {}).get("cells", {}).get(k, {}).get(base)) for t in ("mnist", "cifar", "lm")) + r"\\")
        if base == "vs_fp":
            rows.append("Digital & Adam & " + " & ".join(cellfmt(E3.get(t, {}).get("cells", {}).get("adam", {}).get("vs_fp"))
                                                       for t in ("mnist", "cifar", "lm")) + r"\\")
        body = ("\\begin{table*}[t]\\centering\\footnotesize\\caption{Revised main table (repaired simulator): gap to "
                + cap + ", mean [95 \\% $t$-interval] over 5 seeds paired by seed (same initialisation and data order); MNIST "
                "and CIFAR in accuracy points, LM in \\% of bits per byte; P/F/U = PASS/FAIL/UNRESOLVED against the absolute "
                "lines 2 pp, 2 pp, 5 \\%.}\\label{tab:rev_" + base + "}\n\\begin{tabular}{llccc}\\toprule Device & Alg. & MNIST & "
                "CIFAR & LM\\\\\\midrule\n" + "\n".join(rows).replace("_", "\\_").replace("\\_{x}", "_x").replace("$\\_x$", "$_x$")
                + "\n\\bottomrule\\end{tabular}\\end{table*}\n")
        open(os.path.join(TEX, "tables", f"rev_main_{base}.tex"), "wb").write(body.encode("utf-8"))
    rows = []
    VA = {"EQUIVALENT": "EQ", "GROWS": "GR", "SHRINKS": "SH", "NO EVIDENCE OF GROWTH BEYOND THE MARGIN": "NG",
          "INCONCLUSIVE": "INC"}
    SH = {"ecram_li_tang2018": "Li", "ecram_mo_kim2019": "MO", "protonic_onen2022": "Prot."}
    for t, d in E4.items():
        for a, x in d["arms"].items():
            dv, al = a.rsplit("__", 1)
            gs = " / ".join(fmt(x["widths"][w]["gap"]["mean"]) for w in d["widths"])
            iv = lambda T: (f"{fmt(T.get('D'))} [{fmt((T.get('ci90') or [None])[0])}, "
                            f"{fmt((T.get('ci90') or [None, None])[1])}] {VA.get(T['verdict'], T['verdict'])}")
            rows.append(f"{'CIFAR' if t == 'cifar' else 'LM'} & {SH.get(dv, dv)} {ALGLAB.get(al, al)} & {gs} & "
                        f"{iv(x['test'])} & {iv(x['paired'])}\\\\")
    open(os.path.join(TEX, "tables", "rev_width.tex"), "wb").write((
        "\\begin{table*}[t]\\centering\\scriptsize\\caption{Revised width study (Li = Li-ECRAM, Prot. = protonic-inspired): mean gap at the narrow / mid / wide "
        "width (5 seeds, each arm at its own selected learning rate; CIFAR $c=16/32/64$ in pp, LM $d=64/128/256$ in \\%), and "
        "the endpoint contrast $D$ (widest minus narrowest) with its 90 \\% interval and verdict, by the pre-registered Welch "
        "test (the $t$ quantile at the Welch--Satterthwaite degrees of freedom; versions 2--11 rounded them down: deviation R9) and, added after review 2 (deviation R4), paired by seed. Verdicts (margins 2 pp, 5 \\%): EQ = equivalent at the "
        "endpoints, GR = grows, SH = shrinks, NG = no evidence of growth beyond the margin, INC = inconclusive. An endpoint test says nothing about the "
        "middle width.}\\label{tab:rev_width}\n\\begin{tabular}{llccc}"
        "\\toprule Task & Arm & gap narrow / mid / wide & Welch $D$ [90 \\%] & paired $D$ [90 \\%]\\\\\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\\end{table*}\n").encode("utf-8"))
    rows = []
    AXL = {"n_states": "levels", "asym": "asym.\\ $a$ (SP moves)", "asym_fixedsp": "asym.\\ $a$ (SP fixed)",
           "gamma": "nonlin.\\ $\\gamma$", "c2c": "noise $c_{2c}$", "ref_err": "ref.\\ err.\\ $\\sigma_r$",
           "tau_steps": "retention $\\tau$"}
    for t, d in E5.items():
        for ax, x in d["axes"].items():
            pts = "; ".join(f"{k}: {fmt(v['gap']['mean'])}{v['label'][0]}" for k, v in x["points"].items())
            rows.append(f"{ALGLAB[d['algo']]}, {'CIFAR' if d['task'] == 'cifar' else 'LM'} & {AXL[ax]} & {pts} & "
                        f"{x['weakest_passing'] if x['weakest_passing'] is not None else '--'}\\\\")
    open(os.path.join(TEX, "tables", "rev_spec.tex"), "wb").write((
        "\\begin{table*}[t]\\centering\\scriptsize\\caption{Revised sensitivity sheet (protonic-inspired base; TTv2 = the "
        "pre-registered S-ALGO, c-TTv2 added after the main table was seen, deviation R3; 3 seeds paired with FP-SGD): mean gap per grid value with its label against the ABSOLUTE line (P/F/U), and the weakest value "
        "that passes with every value toward the best end also passing (-- = not established).}\\label{tab:rev_spec}\n"
        "\\begin{tabular}{llp{8.8cm}l}\\toprule Alg., task & Axis & mean gap per value & threshold\\\\\\midrule\n" +
        "\n".join(rows) + "\n\\bottomrule\\end{tabular}\\end{table*}\n").encode("utf-8"))


if __name__ == "__main__":
    main()
