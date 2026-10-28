"""REVISION: the diagnostic D1 analysis (PLAN-REVISION.md section 2). Reads records/revision/runs/d1/*.json, writes
records/revision/D1-ANALYSIS.json.

    python -B revision/analyze_d1.py
"""
import glob
import json
import math
import os
import statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(HERE, "..", "records", "revision")
T975 = {1: 12.706205, 2: 4.302653, 3: 3.182446, 4: 2.776445, 5: 2.570582, 6: 2.446912, 7: 2.364624, 8: 2.306004}
LINE = 2.0
MATERIAL = 1.0


def ci(xs):
    n = len(xs)
    m = st.fmean(xs)
    if n < 2:
        return dict(mean=m, n=n, lo=None, hi=None, sd=None)
    sd = st.stdev(xs)
    h = T975[n - 1] * sd / math.sqrt(n)
    return dict(mean=m, n=n, lo=m - h, hi=m + h, sd=sd)


def label(c):
    if c["lo"] is None:
        return "N/A"
    return "PASS" if c["hi"] <= LINE else ("FAIL" if c["lo"] > LINE else "UNRESOLVED")


def main():
    runs = {}
    for p in glob.glob(os.path.join(REC, "runs", "d1", "*.json")):
        r = json.load(open(p, "rb"))
        extra = r["tag"].split("__")[-1]
        dev = r["spec"]["name"] if r["arm"] == "device" else "fp_sgd"
        acc = r["metric"]["acc"] if not r.get("diverged") else 0.0
        runs[(r["task"], dev, r["algo"], extra, r["seed"])] = dict(acc=acc, layers=r["layers"], rng=r.get("rng", "old-sim"),
                                                                     init=r.get("init_sha256"), data=r.get("data_sha256"))
    cells = {}
    keys = sorted({k[:4] for k in runs})
    for task, dev, algo, extra in keys:
        if dev == "fp_sgd" and algo == "sgd":
            continue
        ref = "old" if extra == "old" else "rev"
        gaps, seeds = [], []
        for s in (0, 1, 2):
            a, f = runs.get((task, dev, algo, extra, s)), runs.get((task, "fp_sgd", "sgd", ref, s))
            if a and f:
                gaps.append(100 * (f["acc"] - a["acc"])); seeds.append(s)
        if not gaps:
            continue
        c = ci(gaps)
        L = [l for s in seeds for l in runs[(task, dev, algo, extra, s)]["layers"]]
        tot = sum(l["pulses"] for l in L) or 1.0
        diag = dict(reset_pulse_share=sum(l.get("reset_pulses", 0.0) for l in L) / tot,
                    reset_resid_steps=st.fmean([l["reset_resid_steps"] for l in L if l.get("reset_resid_steps") is not None])
                    if any(l.get("reset_resid_steps") is not None for l in L) else None,
                    clip_call_frac_max=max((l.get("clip_call_frac", 0.0) for l in L), default=None),
                    update_lost_frac_max=max((l.get("update_lost_frac", 0.0) for l in L), default=None))
        same_ctrl = None
        if ref == "rev":
            same_ctrl = all(runs[(task, dev, algo, extra, s)]["init"] == runs[(task, "fp_sgd", "sgd", "rev", s)]["init"] and
                            runs[(task, dev, algo, extra, s)]["data"] == runs[(task, "fp_sgd", "sgd", "rev", s)]["data"]
                            for s in seeds)
        cells["|".join((task, dev, algo, extra))] = dict(gap=c, gaps=gaps, seeds=seeds, label=label(c), diag=diag,
                                                         matched_init_and_data=same_ctrl)

    def eff(name, a, b):
        A, B = cells.get(a), cells.get(b)
        if not A or not B:
            return None
        d = A["gap"]["mean"] - B["gap"]["mean"]
        per = [x - y for x, y, s, t in zip(A["gaps"], B["gaps"], A["seeds"], B["seeds"]) if s == t]
        return dict(effect=name, cell=a, against=b, delta_mean=d, delta_ci=ci(per) if len(per) > 1 else None,
                    label_from=B["label"], label_to=A["label"],
                    material=abs(d) > MATERIAL or A["label"] != B["label"])
    effects = []
    for task in ("mnist", "cifar"):
        for dev in ("protonic_onen2022", "ecram_li_tang2018_papermap"):
            for algo in ("sgd", "ttv2", "cttv2", "agad"):
                effects.append(eff("rng", f"{task}|{dev}|{algo}|rev", f"{task}|{dev}|{algo}|old"))
            for algo in ("ttv2", "cttv2"):
                for m in ("pulse", "alt", "none"):
                    effects.append(eff("reset_" + m, f"{task}|{dev}|{algo}|rev_{m}", f"{task}|{dev}|{algo}|rev"))
            effects.append(eff("published_ttv2", f"{task}|{dev}|ttv2|rev_pub", f"{task}|{dev}|ttv2|rev"))
        for algo, v in (("sgd", "rev"), ("ttv2", "rev_pulse"), ("cttv2", "rev_pulse"), ("agad", "rev")):
            effects.append(eff("mapping_aihwkit", f"{task}|ecram_li_tang2018|{algo}|{v}",
                               f"{task}|ecram_li_tang2018_papermap|{algo}|{v}"))
    effects = [e for e in effects if e]
    sd_old = [c["gap"]["sd"] for k, c in cells.items() if k.endswith("|old") and c["gap"]["sd"] is not None]
    sd_rev = [c["gap"]["sd"] for k, c in cells.items() if k.endswith("|rev") and c["gap"]["sd"] is not None]
    out = dict(schema="altone.x1000.me-revision.d1.v1", line_pp=LINE, material_pp=MATERIAL, n_runs=len(runs), cells=cells,
               effects=effects, material_effects=[e for e in effects if e["material"]],
               paired_gap_sd_median=dict(old=st.median(sd_old) if sd_old else None, rev=st.median(sd_rev) if sd_rev else None))
    with open(os.path.join(REC, "D1-ANALYSIS.json"), "wb") as f:
        f.write((json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    for e in effects:
        print(f"{e['effect']:16s} {e['cell']:55s} d={e['delta_mean']:+6.2f} {e['label_from']:>10s}->{e['label_to']:<10s}"
              f"{' MATERIAL' if e['material'] else ''}")
    print("paired-gap sd median old/rev", out["paired_gap_sd_median"], "runs", len(runs))


if __name__ == "__main__":
    main()
