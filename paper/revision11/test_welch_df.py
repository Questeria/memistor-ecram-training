#!/usr/bin/env python3
"""Review 9 (2026-10-29; DEVIATIONS R9): the width study's Welch interval takes the t quantile at the Welch-Satterthwaite degrees
of freedom itself; versions 2 to 11 read a t table at the df rounded down.

Checks:
  1. revision/analyze_rev.t_cdf against the closed-form Student-t CDFs for df 1 to 4, and t_quantile against the closed-form
     quantiles for df 1, 2 and 4 (to 1e-12), and against the three-decimal tables T95 and T975 that the other analyses read
     (df 1 to 30, to 6e-4);
  2. every Welch row of records/revision/RESULTS-REVISION.json (e4), recomputed from its per-seed gaps by width_verdict, gives
     the stored D, df, interval and verdict;
  3. CIFAR, protonic-inspired c-TTv2 equals review 9's independent calculation: df 4.675276586261936, 90 % interval
     [0.050506763611446015, 3.4734932363885567], GROWS (to 1e-9);
  4. fault: with the df floored (as in versions 2 to 11), check 3 must fail.

    python -B revision11/test_welch_df.py [--out file.json]          (from paper/)
"""
import importlib.util
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
REVIEW9 = dict(df=4.675276586261936, ci90=[0.050506763611446015, 3.4734932363885567], verdict="GROWS")

CDF = {1: lambda t: 0.5 + math.atan(t) / math.pi,
       2: lambda t: 0.5 + t / (2.0 * math.sqrt(2.0 + t * t)),
       3: lambda t: 0.5 + (t / (math.sqrt(3.0) * (1.0 + t * t / 3.0)) + math.atan(t / math.sqrt(3.0))) / math.pi,
       4: lambda t: 0.5 + 0.375 * t / math.sqrt(1.0 + t * t / 4.0) * (1.0 - t * t / (12.0 * (1.0 + t * t / 4.0)))}


def q4(p):
    a = 4.0 * p * (1.0 - p)
    q = math.cos(math.acos(math.sqrt(a)) / 3.0) / math.sqrt(a)
    return 2.0 * math.sqrt(q - 1.0)


QUANT = {1: lambda p: math.tan(math.pi * (p - 0.5)),
         2: lambda p: (2.0 * p - 1.0) / math.sqrt(2.0 * p * (1.0 - p)),
         4: q4}


def load():
    spec = importlib.util.spec_from_file_location("analyze_rev", os.path.join(P, "revision", "analyze_rev.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def close(a, b, tol):
    return a is not None and b is not None and abs(a - b) <= tol


def main():
    m = load()
    res = {}
    cdf_err = max(abs(m.t_cdf(t, df) - f(t)) for df, f in CDF.items() for t in (-3.0, -0.7, 0.0, 0.4, 1.3, 2.1, 5.0, 40.0))
    q_err = max(abs(m.t_quantile(p, df) - f(p)) for df, f in QUANT.items() for p in (0.9, 0.95, 0.975, 0.995))
    tab_err = max(abs(m.t_quantile(p, df) - tab[df - 1]) for p, tab in ((0.95, m.T95), (0.975, m.T975)) for df in range(1, 31))
    res["1_quantile"] = dict(cdf_max_err=cdf_err, quantile_max_err=q_err, table_max_err=tab_err,
                             ok=cdf_err < 1e-12 and q_err < 1e-12 and tab_err < 6e-4)

    e4 = json.load(open(os.path.join(P, "records", "revision", "RESULTS-REVISION.json"), encoding="utf-8"))["e4"]
    rows, bad = 0, []
    for task, d in e4.items():
        for arm, x in d["arms"].items():
            ws = sorted(x["widths"], key=float)
            got = m.width_verdict(task, x["widths"][ws[0]]["gaps"], x["widths"][ws[-1]]["gaps"])
            want = x["test"]
            rows += 1
            if not (close(got["D"], want["D"], 1e-12) and close(got["df"], want["df"], 1e-9) and got["verdict"] == want["verdict"]
                    and all(close(g, w, 1e-12) for g, w in zip(got["ci90"], want["ci90"]))):
                bad.append(f"{task}/{arm}")
    res["2_records"] = dict(rows=rows, mismatches=bad, ok=rows == 8 and not bad)

    def case(mod):
        x = e4["cifar"]["arms"]["protonic_onen2022__cttv2"]
        ws = sorted(x["widths"], key=float)
        return mod.width_verdict("cifar", x["widths"][ws[0]]["gaps"], x["widths"][ws[-1]]["gaps"])

    def matches(v):
        return (close(v["df"], REVIEW9["df"], 1e-9) and v["verdict"] == REVIEW9["verdict"]
                and all(close(g, w, 1e-9) for g, w in zip(v["ci90"], REVIEW9["ci90"])))

    v = case(m)
    res["3_review9_case"] = dict(ci90=v["ci90"], df=v["df"], verdict=v["verdict"], ok=matches(v))
    m.t_quantile = lambda p, df: m.tq(m.T95 if p == 0.95 else m.T975, df)        # the fault: the floored table of versions 2-11
    f = case(m)
    res["4_fault_floored_df"] = dict(ci90=f["ci90"], verdict=f["verdict"], detected=not matches(f))
    res["all_ok"] = all(res[k]["ok"] for k in ("1_quantile", "2_records", "3_review9_case")) and res["4_fault_floored_df"]["detected"]
    print(f"quantile: cdf err {cdf_err:.1e}, quantile err {q_err:.1e}, table err {tab_err:.1e} | records {rows} rows, "
          f"{len(bad)} mismatches | review-9 case {v['verdict']} [{v['ci90'][0]:.6f}, {v['ci90'][1]:.6f}] | floored fault "
          f"{f['verdict']} [{f['ci90'][0]:.4f}, {f['ci90'][1]:.4f}] detected={res['4_fault_floored_df']['detected']} | "
          + ("ALL_OK" if res["all_ok"] else "NOT_OK"))
    if "--out" in sys.argv:
        o = sys.argv[sys.argv.index("--out") + 1]
        os.makedirs(os.path.dirname(os.path.abspath(o)), exist_ok=True)
        open(o, "wb").write((json.dumps(res, indent=1) + "\n").encode("utf-8"))
    sys.exit(0 if res["all_ok"] else 1)


if __name__ == "__main__":
    main()
