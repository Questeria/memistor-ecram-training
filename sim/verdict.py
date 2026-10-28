"""Lane ME analysis: gaps, the per-axis thresholds, the joint minimum spec rounds, the catalog map and the kill-line verdict.

python -B verdict.py minspec          -> ../records/MINSPEC-CANDIDATES.json (adds the next round when the last one failed)
python -B verdict.py final            -> ../records/RESULTS.json and ../VERDICT.md (numbers only from the records)
Thresholds (PLAN.md): classification gap < 2.0 pp; LM relative bpb excess < 5 %.
"""
import glob
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(HERE, "..", "records")
GAP_CLS, GAP_LM = 2.0, 5.0
ALGOS = ("sgd", "ttv2")
STATES = (64, 256, 1024)
AXES = {  # axis -> (grid prefix, values weakest-last order is computed below, field(s), "larger is weaker")
    "asym": ("B_asym", (0.01, 0.03, 0.1, 0.3), ("asym",), True),
    "gamma": ("C_gamma", (0.1, 0.3, 0.6, 1.0), ("gamma_up", "gamma_dn"), True),
    "c2c": ("D_c2c", (0.3, 1.0, 3.0), ("c2c",), True),
}
TAU = (1e5, 1e4, 1e3, 1e2)  # weaker = smaller


def jl(p):
    with open(p, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


def jw(p, o):
    with open(p, "wb") as f:
        f.write((json.dumps(o, indent=1, sort_keys=True) + "\n").encode("utf-8"))


def load(task):
    out = {}
    for f in glob.glob(os.path.join(REC, "runs", task, "*.json")):
        r = jl(f)
        out[r["tag"]] = r
    return out


def metric(r):
    m = r["metric"]
    return m["acc"] * 100 if "acc" in m else m["bpb"]


def fp_ref(R):
    v = [metric(r) for n, r in R.items() if n.startswith("FP__")]
    return (st.mean(v), st.pstdev(v), len(v)) if v else (None, None, 0)


def gap(task, R, prefix, algo):
    """Mean gap over the seeds of <prefix>__<algo>__s*. cls: pp below FP; lm: % bpb above FP."""
    fp = fp_ref(R)[0]
    v = [metric(r) for n, r in R.items() if n.startswith(prefix + "__" + algo + "__s")]
    if fp is None or not v:
        return None
    m = st.mean(v)
    g = (fp - m) if task != "lm" else (m / fp - 1) * 100
    if any(r.get("diverged") for n, r in R.items() if n.startswith(prefix + "__" + algo + "__s")):
        g = math.inf
    return dict(gap=g, n=len(v), mean=m, fp=fp, passes=g < (GAP_LM if task == "lm" else GAP_CLS))


def per_axis(R, algo):
    """Per-axis thresholds on MNIST (PLAN.md 'The minimum spec')."""
    A = {n: gap("mnist", R, f"A_states{n}", algo) for n in (16, 32, 64, 128, 256, 1024, 4096)}
    s_min = next((n for n in sorted(A) if A[n] and A[n]["passes"]), None)
    res = dict(states_alone=A, s_min=s_min)
    for s_star in [s for s in STATES if s_min is not None and s >= s_min] + [None]:
        if s_star is None:
            break
        ax = {}
        for name, (pre, vals, _, _) in AXES.items():
            g = {v: gap("mnist", R, f"{pre}{v:g}_states{s_star}", algo) for v in vals}
            ok = [v for v in vals if g[v] and g[v]["passes"]]
            ax[name] = dict(weakest_passing=max(ok) if ok else 0.0, gaps={str(k): x for k, x in g.items()})
        gt = {t: gap("mnist", R, f"E_tau{t:g}_states256", algo) for t in TAU}
        okt = [t for t in TAU if gt[t] and gt[t]["passes"]]
        ax["tau"] = dict(weakest_passing=min(okt) if okt else math.inf, gaps={str(k): x for k, x in gt.items()})
        gr = {r: gap("mnist", R, f"F_ref{r:g}_states256", algo) for r in (0.01, 0.05)}
        okr = [r for r in (0.01, 0.05) if gr[r] and gr[r]["passes"]]
        ax["ref_err"] = dict(weakest_passing=max(okr) if okr else 0.0, gaps={str(k): x for k, x in gr.items()},
                             note="grid F holds asym 0.1 and gamma 0.3 fixed")
        res.update(s_star=s_star, axes=ax)
        if all(ax[k]["weakest_passing"] > 0 for k in AXES):
            break
    return res


def spec_of(s_star, ax):
    sp = dict(n_states=s_star, asym=ax["asym"]["weakest_passing"], gamma_up=ax["gamma"]["weakest_passing"],
              gamma_dn=ax["gamma"]["weakest_passing"], c2c=ax["c2c"]["weakest_passing"],
              ref_err=ax["ref_err"]["weakest_passing"], name="minspec")
    if math.isfinite(ax["tau"]["weakest_passing"]):
        sp["tau_steps"] = ax["tau"]["weakest_passing"]
    return sp


def tighten(sp, ax):
    """One grid step toward ideal on the axis whose single-axis gap at its chosen value was largest."""
    worst, wg = None, -math.inf
    for k, (pre, vals, flds, _) in AXES.items():
        v = sp[flds[0]]
        if v == 0:
            continue
        g = ax[k]["gaps"].get(str(v)) or {}
        if g.get("gap", -math.inf) > wg:
            worst, wg = k, g["gap"]
    if worst is None:
        sp = dict(sp, n_states=sp["n_states"] * 4)
        return sp, "n_states x4"
    pre, vals, flds, _ = AXES[worst]
    v = sp[flds[0]]
    lower = [x for x in vals if x < v]
    nv = max(lower) if lower else 0.0
    sp = dict(sp)
    for f in flds:
        sp[f] = nv
    return sp, f"{worst} {v:g} -> {nv:g}"


def minspec():
    R = load("mnist")
    p = os.path.join(REC, "MINSPEC-CANDIDATES.json")
    cur = jl(p) if os.path.exists(p) else dict(candidates={}, log=[])
    for algo in ALGOS:
        pa = per_axis(R, algo)
        rounds = cur["candidates"].setdefault(algo, [])
        if pa["s_min"] is None:
            cur["log"].append(f"{algo}: no state count passes alone; no candidate")
            continue
        if not rounds:
            rounds.append(spec_of(pa["s_star"], pa["axes"]))
            cur["log"].append(f"{algo}: round 0 = per-axis join at states {pa['s_star']}")
            continue
        i = len(rounds) - 1
        g = gap("mnist", R, f"MIN{i}", algo)
        if g is None:
            cur["log"].append(f"{algo}: round {i} not run yet")
            continue
        if g["passes"] or len(rounds) >= 4:
            cur["log"].append(f"{algo}: round {i} {'PASSES' if g['passes'] else 'fails (3 rounds used)'} gap {g['gap']:.3f}")
            continue
        sp, what = tighten(rounds[-1], pa["axes"])
        rounds.append(sp)
        cur["log"].append(f"{algo}: round {i} fails (gap {g['gap']:.3f}); round {i + 1}: {what}")
    jw(p, cur)
    print("\n".join(cur["log"][-4:]))


def final():
    out = dict(schema="altone.x1000.me.results.v1", results_are="DEV", thresholds=dict(cls_pp=GAP_CLS, lm_pct=GAP_LM))
    tasks = [t for t in ("mnist", "cifar", "lm") if os.path.isdir(os.path.join(REC, "runs", t))]
    cat = jl(os.path.join(REC, "CATALOG.json"))["entries"]
    R = {t: load(t) for t in tasks}
    out["fp"] = {t: dict(zip(("mean", "sd", "n"), fp_ref(R[t]))) for t in tasks}
    if "lm" in R and "ADAM__s0" in R["lm"]:
        out["lm_adam_context_bpb"] = adam = metric(R["lm"]["ADAM__s0"])
        out["lm_vs_adam_pct"] = {}  # director's item a: every LM result also against the best digital optimizer here
        for n_, r in R["lm"].items():
            if n_.startswith(("CAT_", "FP__", "MIN")):
                out["lm_vs_adam_pct"][n_] = (metric(r) / adam - 1) * 100
    out["per_axis_mnist"] = {a: per_axis(R["mnist"], a) for a in ALGOS}
    mc = os.path.join(REC, "MINSPEC-CANDIDATES.json")
    if os.path.exists(mc):
        M = jl(mc)
        out["minspec"] = {}
        for a, rounds in M["candidates"].items():
            out["minspec"][a] = [dict(spec=sp, gaps={t: gap(t, R[t], f"MIN{i}", a) for t in tasks})
                                 for i, sp in enumerate(rounds)]
    m = {}
    for k, e in cat.items():
        m[k] = dict(label=e["label"], spec=e["spec"],
                    gaps={t: {a: gap(t, R[t], f"CAT_{k}", a) for a in ALGOS} for t in tasks})
    out["catalog"] = m
    out["grids_pod"] = {t: {n: {a: gap(t, R[t], n, a) for a in ALGOS}
                            for n in ("A_states32", "A_states128", "A_states1024", "B_asym0.1_states1024",
                                      "C_gamma0.3_states1024", "D_c2c1_states1024")} for t in tasks if t != "mnist"}
    # kill lines
    realistic = [k for k, e in cat.items() if e["label"] in ("PUBLISHED-FIT", "PARTLY-PUBLISHED")]
    ecram = [k for k in realistic if k.startswith(("ecram", "protonic", "wox"))]
    def passes_all(k):
        res = {}
        for a in ALGOS:
            gs = [m[k]["gaps"][t][a] for t in ("mnist", "cifar", "lm")]
            res[a] = all(g is not None and g["passes"] for g in gs)
        return res
    pa = {k: passes_all(k) for k in realistic}
    any_task_any_algo = {k: {t: any((m[k]["gaps"].get(t) or {}).get(a) and m[k]["gaps"][t][a]["passes"] for a in ALGOS)
                             for t in tasks} for k in realistic}
    en = jl(os.path.join(REC, "ENERGY.json")) if os.path.exists(os.path.join(REC, "ENERGY.json")) else None
    out["kill"] = dict(realistic=realistic, ecram=ecram, passes_all_three=pa, passes_by_task=any_task_any_algo,
                       all_three_tasks_present=all(t in R for t in ("mnist", "cifar", "lm")))
    ecram_ok = [k for k in ecram if any(pa[k].values())]
    adv = None
    if en:
        adv = {k: max([v["advantage_vs_gpu_peak"] for kk, v in en["devices"].items() if kk.startswith(k + "__")] or [0])
               for k in ecram_ok}
    out["kill"]["ecram_passing_all_three"] = ecram_ok
    out["kill"]["energy_advantage_of_passing"] = adv
    none_reach = not any(any(v.values()) for v in any_task_any_algo.values())
    if not out["kill"]["all_three_tasks_present"]:
        verdict = "INCOMPLETE (a task is missing)"
    elif none_reach:
        verdict = "RULED OUT"
    elif ecram_ok and adv and max(adv.values()) >= 100:
        verdict = "CONFIRMED-CANDIDATE (needs the director's independent adversary check before CONFIRMED)"
    else:
        verdict = "UNCLEAR"
    out["verdict"] = verdict
    sens = {}  # DEVIATIONS.md D3: gaps against the FP mean that includes FPSENS__s2 (reported apart; never the verdict)
    for t in ("cifar", "lm"):
        if t not in R or "FPSENS__s2" not in R[t]:
            continue
        v = [metric(r) for n, r in R[t].items() if n.startswith(("FP__", "FPSENS__"))]
        fp3 = st.mean(v)
        sens[t] = dict(fp_mean=fp3, fp_sd=st.pstdev(v), n=len(v), gaps={})
        for k in realistic:
            for a in ALGOS:
                vv = [metric(r) for n, r in R[t].items() if n.startswith(f"CAT_{k}__{a}__s")]
                if vv:
                    m_ = st.mean(vv)
                    g = (fp3 - m_) if t != "lm" else (m_ / fp3 - 1) * 100
                    sens[t]["gaps"][f"{k}__{a}"] = dict(gap=g, n=len(vv), passes=g < (GAP_LM if t == "lm" else GAP_CLS))
    out["fp_sensitivity_D3"] = sens
    jw(os.path.join(REC, "RESULTS.json"), out)
    write_md(out, en)
    print(verdict)


def fmt(g, task):
    if not g:
        return "-"
    if not math.isfinite(g["gap"]):
        return "diverged"
    u = "%" if task == "lm" else " pp"
    return f"{g['gap']:.2f}{u}{' (n=%d)' % g['n'] if g['n'] > 1 else ''}{' PASS' if g['passes'] else ''}"


def write_md(o, en):
    """VERDICT.md: every number is copied from RESULTS.json / ENERGY.json by this function."""
    T = [t for t in ("mnist", "cifar", "lm") if t in o["fp"]]
    L = ["# Lane ME verdict (generated by sim/verdict.py final from records/RESULTS.json; results are DEV)", "",
         f"**Verdict: {o['verdict']}**", "",
         "Gap = FP accuracy minus device accuracy (pp, test) for MNIST and CIFAR; LM = device bits per byte / FP - 1 (%).",
         "Thresholds: < 2 pp; < 5 %. Forward and backward reads are ideal (the update is what is tested).", "",
         "FP baselines: " + "; ".join(f"{t} {o['fp'][t]['mean']:.4g} (sd {o['fp'][t]['sd']:.2g}, n {o['fp'][t]['n']})" for t in T)
         + (f"; LM Adam context {o['lm_adam_context_bpb']:.4g} bpb" if "lm_adam_context_bpb" in o else ""), "",
         "## The catalog on the map", "",
         "| device | label | " + " | ".join(f"{t} SGD | {t} TTv2" for t in T) + " |",
         "|---|---|" + "---|---|" * len(T)]
    for k, e in o["catalog"].items():
        L.append(f"| {k} | {e['label']} | " + " | ".join(f"{fmt(e['gaps'][t]['sgd'], t)} | {fmt(e['gaps'][t]['ttv2'], t)}" for t in T) + " |")
    L += ["", "## Minimum specs (MNIST per-axis thresholds, then the joint rounds)", ""]
    for a, pa in o["per_axis_mnist"].items():
        ax = pa.get("axes", {})
        L.append(f"- {a}: fewest states passing alone {pa['s_min']}; at states {pa.get('s_star')}: "
                 + ", ".join(f"{k} <= {v['weakest_passing']:g}" if k != "tau" else f"tau >= {v['weakest_passing']:g} batches"
                             for k, v in ax.items()))
    for a, rounds in (o.get("minspec") or {}).items():
        for i, r in enumerate(rounds):
            sp = {k: v for k, v in r["spec"].items() if k != "name"}
            L.append(f"- {a} round {i}: {json.dumps(sp)} -> " + "; ".join(f"{t} {fmt(r['gaps'].get(t), t)}" for t in T))
    if o.get("grids_pod"):
        L += ["", "## CIFAR and LM single-axis points", ""]
        for t, d in o["grids_pod"].items():
            L.append(f"- {t}: " + "; ".join(f"{n} SGD {fmt(v['sgd'], t)} / TTv2 {fmt(v['ttv2'], t)}" for n, v in d.items()))
    if en:
        L += ["", "## Energy per update (records/ENERGY.json)", "",
              f"GPU (H100, weight-gradient MAC, best case): {en['gpu']['update_pj_peak_floor']:.3g} pJ; at 50 % utilisation "
              f"{en['gpu']['update_pj_50pct']:.3g} pJ.", ""]
        for k, r in en["devices"].items():
            L.append(f"- {k}: {r['update_energy_pj']:.3g} pJ per weight per sample ({r['energy_label']}); "
                     f"advantage over the GPU's best case {r['advantage_vs_gpu_peak']:.3g}x")
    if o.get("lm_vs_adam_pct"):
        L += ["", "## LM against Adam (the best digital optimizer run here; context, not the pre-registered baseline)", ""]
        L.append("- " + "; ".join(f"{k} {v:+.1f}%" for k, v in sorted(o["lm_vs_adam_pct"].items())
                                  if k.startswith("FP__") or "protonic" in k or "ecram_li" in k))
    if o.get("fp_sensitivity_D3"):
        L += ["", "## FP sensitivity (DEVIATIONS.md D3: 3-seed FP mean; not the verdict)", ""]
        for t, d in o["fp_sensitivity_D3"].items():
            L.append(f"- {t}: FP {d['fp_mean']:.4g} (sd {d['fp_sd']:.2g}, n {d['n']}): " + "; ".join(
                f"{k} {fmt(g, t)}" for k, g in d["gaps"].items() if g["gap"] < 3 * (GAP_LM if t == "lm" else GAP_CLS)))
    sp = os.path.join(REC, "SCALE-DEV.json")
    if os.path.exists(sp):
        S = jl(sp)
        L += ["", "## Scale check (DEV, OUTSIDE THE PRE-REGISTRATION; seed 0; records/SCALE-DEV.json)", "",
              "Gap of TTv2 on protonic / Li-ECRAM at each width; 'fixed lr' = the pre-registered lr, 're-tuned' = the FP lr "
              "re-chosen on validation at that width (sittings 4 and 5)."]
        for t in ("cifar", "lm"):
            for w, r in S.get(t, {}).items():
                g = lambda q, k: f"{q[k]['gap']:.2f}" if k in q else "-"
                line = f"- {t} width {w}: fixed lr FP {r['fp']:.4g}, gaps {g(r, 'protonic_onen2022')} / {g(r, 'ecram_li_tang2018')}"
                if "retuned" in r:
                    q = r["retuned"]
                    line += f"; re-tuned lr {q['lr']:g} FP {q['fp']:.4g}, gaps {g(q, 'protonic_onen2022')} / {g(q, 'ecram_li_tang2018')}"
                L.append(line)
        a = jl(os.path.join(REC, "runs", "lm-scale-DEV", "FP_w64__s0.json"))
        b = jl(os.path.join(REC, "runs", "lm-scale-DEV", "lrsel_w64", "FP_w64__s0.json"))
        L.append(f"- The same FP LM run (width 64, lr {a['lr']:g}, seed 0) gave {a['metric']['bpb']:.4g} bpb on the {a['device']} "
                 f"and {b['metric']['bpb']:.4g} on the {b['device']}: a {abs(b['metric']['bpb'] / a['metric']['bpb'] - 1) * 100:.1f} % "
                 "cross-GPU spread, the same size as the LM threshold (every pre-registered CIFAR / LM run used A4000s).")
    L += ["", "## Kill lines", "", "```", json.dumps(o["kill"], indent=1, sort_keys=True, default=str)[:4000], "```", ""]
    with open(os.path.join(HERE, "..", "VERDICT.md"), "wb") as f:
        f.write((chr(10).join(L) + chr(10)).encode("utf-8"))


if __name__ == "__main__":
    {"minspec": minspec, "final": final}[sys.argv[1]]()
