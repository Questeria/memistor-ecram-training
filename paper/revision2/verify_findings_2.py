"""ME-REVISE-2: check review 2's eight findings against the code and the records (no new runs).

    python -B revision2/verify_findings_2.py [--pdf build/main.pdf] [--out records/revision2/VERIFY-FINDINGS-2.json]
    python -B revision2/verify_findings_2.py --artifacts-only --pdf build/main.pdf --out <file>   (placeholders, overflow)

Writes one JSON with each finding's numbers."""
import argparse
import glob
import json
import math
import os
import re
import statistics as st
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
REC = os.path.join(P, "records", "revision")
sys.path.insert(0, os.path.join(P, "revision"))
import analyze_rev as AR  # noqa: E402  (the paper's own gap, t tables and verdict rule)

DEVS = AR.DEVS


def load(phase):
    return AR.load(phase)


# ---------------------------------------------------------------- F1 pulse fidelity
def f1():
    worst, n = None, 0
    for r in load("e3"):
        if r["arm"] != "device" or r["spec"]["name"] not in DEVS:
            continue
        for i, l in enumerate(r["layers"]):
            v = l.get("update_lost_frac", 0.0)
            n += 1
            if worst is None or v > worst[0]:
                worst = (v, r["tag"], i, l["shape"])
    lam = 31.0
    cdf = sum(math.exp(-lam) * lam ** k / math.factorial(k) for k in range(32))
    return dict(verdict="CONFIRMED", worst_layer_lost_frac=worst[0], worst_tag=worst[1], worst_layer=worst[2],
                worst_shape=worst[3], n_layer_records=n, poisson31_p_gt_31=1 - cdf,
                code=["sim/memsim_rev.py pulse_counts: n_up, n_dn ~ Poisson(lambda) per cell, independent across cells",
                      "sim/memsim_rev.py Tile._step: a batch's up and down pulses in one exact ODE step; the c2c variance is "
                      "evaluated at the pre-step state u0"])


# ---------------------------------------------------------------- F2 width pairing
def paired_verdict(task, diffs):
    m = AR.LINE[task]
    n = len(diffs)
    D = st.fmean(diffs)
    se = st.stdev(diffs) / math.sqrt(n)
    t90 = AR.tq(AR.T95, n - 1)
    lo, hi = D - t90 * se, D + t90 * se
    if -m < lo and hi < m:
        v = "EQUIVALENT"
    elif lo > 0:
        v = "GROWS"
    elif hi < 0:
        v = "SHRINKS"
    elif hi < m:
        v = "NO EVIDENCE OF GROWTH BEYOND THE MARGIN"
    else:
        v = "INCONCLUSIVE"
    return dict(D=D, se=se, df=n - 1, ci90=[lo, hi], t=D / se if se > 0 else float("inf"), verdict=v, diffs=diffs)


def width_contrasts():
    rs = load("e4")
    out = {}
    for task in ("cifar", "lm"):
        by = {}
        for r in rs:
            if r["task"] == task:
                by.setdefault((AR.arm_key(r), r["width"]), {})[r["seed"]] = AR.metric(r)
        ws = sorted({w for _, w in by})
        for a in sorted({k for k, _ in by if k != "fp"}):
            g = {w: {s: AR.gap(task, by[("fp", w)][s], by[(a, w)][s]) for s in by[(a, w)] if s in by[("fp", w)]}
                 for w in ws}
            seeds = sorted(set(g[ws[0]]) & set(g[ws[-1]]))
            gl, gh = [g[ws[0]][s] for s in seeds], [g[ws[-1]][s] for s in seeds]
            w = AR.width_verdict(task, gl, gh)
            hashes = {s: sorted({r["data_sha256"] for r in rs if r["task"] == task and r["seed"] == s})
                      for s in seeds}
            out[f"{task}__{a}"] = dict(task=task, arm=a, widths=ws, seeds=seeds,
                                       welch=dict(D=w.get("D"), ci90=w.get("ci90"), verdict=w["verdict"]),
                                       paired=paired_verdict(task, [h - l for h, l in zip(gh, gl)]),
                                       one_data_hash_per_seed_across_widths=all(len(v) == 1 for v in hashes.values()))
    return out


def f2():
    out = width_contrasts()
    changed = [k for k, v in out.items() if v["welch"]["verdict"] != v["paired"]["verdict"]]
    return dict(verdict="CONFIRMED" if changed else "DISPUTED", arms=out, verdict_changed_by_pairing=changed)


# ---------------------------------------------------------------- F3 appendix settings
def f3():
    ch = json.load(open(os.path.join(REC, "CHOICES-REVISION.json"), "rb"))
    e2tex = open(os.path.join(P, "tex", "tables", "e2.tex"), encoding="utf-8").read()
    app = open(os.path.join(P, "tex", "app_selection.tex"), encoding="utf-8").read()
    mism = []
    for r in load("e3"):
        if r["algo"] in ch["tt"] and r["arm"] == "device":
            for k, v in ch["tt"][r["algo"]]["ucfg"].items():
                if r["ucfg"].get(k) != v:
                    mism.append((r["tag"], k, r["ucfg"].get(k), v))
    return dict(verdict="CONFIRMED", appendix_inputs_v1_table="\\input{tables/e2.tex}" in app,
                printed_ttv2_period16="TTv2 & $\\lambda$ 0.1, $A$ lr $\\times$10, period 16 &" in e2tex,
                choices=ch["tt"], e3_records_vs_choices_mismatches=len(mism))


# ---------------------------------------------------------------- F4 fixed-symmetry base
def f4():
    rs = load("e5")
    base = [r for r in rs if r["spec"]["name"] == "base"]
    fsp = sorted({r["spec"]["name"] for r in rs if r["spec"]["name"].startswith("asym_fixedsp")})
    b = base[0]["spec"]
    a, g = b["asym"], b["gamma_up"]
    us = a / (2 * g) if g else 0.0
    plan = open(os.path.join(P, "PLAN-REVISION.md"), encoding="utf-8").read()
    return dict(verdict="CONFIRMED", base_records=len(base),
                base_recenter_sp_values=sorted({str(r["spec"].get("recenter_sp")) for r in base}),
                fixedsp_points_run=fsp, base_asym=a, base_gamma=g, base_u_star_nominal=us,
                base_signed_range=[-(1 + us), 1 - us], recentered_range=[-1, 1],
                analysis_substitutes_base="revision/analyze_rev.py e5(): vals[basev] = cells.get('base') for asym_fixedsp",
                plan_says_same_asymmetries="the same asymmetries with the symmetry point held at mid-range" in " ".join(plan.split()))


# ---------------------------------------------------------------- F5/F6 artifacts
STALE = ["near-digital", "within five-seed resolution", "does not grow with width", "few hundred levels suffice",
         "about 32x", "15-234x", "We release"]


def placeholders_tex():
    bad = []
    fs = sorted(glob.glob(os.path.join(P, "tex", "*.tex")) + glob.glob(os.path.join(P, "tex", "tables", "*.tex")))
    for f in fs:
        if os.path.basename(f).startswith("numbers"):
            continue
        for i, line in enumerate(open(f, encoding="utf-8"), 1):
            if line.lstrip().startswith("%"):
                continue
            for m in re.finditer(r"(?<![\\A-Za-z])(" + MACRO_WORD + r")", line):
                bad.append(f"{os.path.relpath(f, P)}:{i}:{m.group(1)}")
    return bad


MACRO_WORD = r"R(?:V[a-z]|V[A-Z][a-z]|E[A-Z][a-z])[A-Za-z]{2,}"  # an RV.../RE... number macro name (has lower case)


def pdf_check(pdf):
    """Bare macro names in the PDF text (pypdf)."""
    from pypdf import PdfReader
    rd = PdfReader(pdf)
    bare = []
    for i, pg in enumerate(rd.pages, 1):
        txt = re.sub(r"\bR\s+([VE][A-Za-z])", r"R\1", pg.extract_text() or "")  # pypdf splits "R VorderUpDn"
        for m in re.finditer(r"(?<![A-Za-z\\])(" + MACRO_WORD + r")", txt):
            bare.append(dict(page=i, word=m.group(1)))
    return dict(pages=len(rd.pages), bare_macro_words=bare)


def log_overfull(log, tol=2.0):
    """Overfull hboxes wider than tol pt in a LaTeX log, with the innermost open .tex file (a table that leaves the page)."""
    out, stack = [], []
    for line in open(log, encoding="utf-8", errors="replace"):
        for m in re.finditer(r"\(([./A-Za-z0-9_-]+\.tex)|\(([a-z_]+)(?=[ \n\[])|\)", line):
            if m.group(0) == ")":
                if stack:
                    stack.pop()
            else:
                stack.append(m.group(1) or m.group(2))
        m = re.search(r"Overfull \\hbox \(([\d.]+)pt too wide\) (?:in paragraph|detected) at lines? (\S+)", line)
        if m and float(m.group(1)) > tol:
            out.append(dict(pt=float(m.group(1)), lines=m.group(2), file=stack[-1] if stack else None))
    return out


def f5():
    ab = open(os.path.join(P, "build", "arxiv-abstract.txt"), encoding="utf-8").read()
    pub = open(os.path.join(P, "PUBLISHING.md"), encoding="utf-8").read()
    pre = open(os.path.join(P, "tex", "preamble.tex"), encoding="utf-8").read()
    return dict(verdict="CONFIRMED", abstract_chars=len(ab.strip()), stale_phrases=[s for s in STALE if s in ab],
                publishing_names_numbers_rev="numbers_rev" in pub, preamble_inputs_numbers_rev="numbers_rev" in pre)


def f6(pdf, logs):
    return dict(verdict="CONFIRMED", tex_bare_placeholders=placeholders_tex(), pdf=pdf_check(pdf),
                overfull_gt_2pt={os.path.basename(l): log_overfull(l) for l in logs})


# ---------------------------------------------------------------- F7 reset aggregation
def reset_stats():
    resid, share, w_res, n_res, rp, tp = [], [], 0.0, 0.0, 0.0, 0.0
    per_dev, maxl = {}, None
    for r in load("e3"):
        if r["arm"] != "device" or r["spec"]["name"] not in DEVS:
            continue
        iters = (r.get("ucfg") or {}).get("tt_reset_iters", 2)
        pls = [(i, l) for i, l in enumerate(r["layers"]) if l.get("reset") == "pulse"]
        d = per_dev.setdefault(r["spec"]["name"], dict(w=0.0, n=0.0, rp=0.0, tp=0.0, max_layer=0.0))
        for i, l in pls:
            if l.get("reset_resid_steps") is None:
                continue
            n = l["reset_extra_reads"] / max(1, iters - 1)  # each reset weight is re-read iters - 1 times
            resid.append(l["reset_resid_steps"])
            w_res += l["reset_resid_steps"] * n
            n_res += n
            d["w"] += l["reset_resid_steps"] * n
            d["n"] += n
            d["max_layer"] = max(d["max_layer"], l["reset_resid_steps"])
            if maxl is None or l["reset_resid_steps"] > maxl[0]:
                maxl = (l["reset_resid_steps"], r["tag"], i)
        tot = sum(l["pulses"] for l in r["layers"])
        if tot and pls:
            s = sum(l.get("reset_pulses", 0.0) for l in r["layers"])
            share.append(s / tot)
            rp += s
            tp += tot
            d["rp"] += s
            d["tp"] += tot
    return dict(resid_macro_mean=st.fmean(resid), resid_pooled_by_reset_events=w_res / n_res,
                resid_max_layer_mean=maxl[0], resid_max_tag=maxl[1], resid_max_layer=maxl[2],
                share_macro_mean_pct=100 * st.fmean(share), share_pooled_pct=100 * rp / tp,
                per_device={k: dict(resid_pooled=v["w"] / v["n"] if v["n"] else None,
                                    resid_max_layer_mean=v["max_layer"],
                                    share_pooled_pct=100 * v["rp"] / v["tp"] if v["tp"] else None)
                            for k, v in per_dev.items()},
                n_reset_from="reset_extra_reads / (tt_reset_iters - 1): each reset weight is re-read once per extra "
                             "iteration (sim/memsim_rev.py _reset_pulsed), so the event count is logged, not reconstructed")


def f7():
    return dict(verdict="CONFIRMED", **reset_stats())


def f8():
    q = open(os.path.join(P, "records", "revision2", "AMBROGIO2023-QUOTES.txt"), encoding="utf-8").read()
    tex = open(os.path.join(P, "tex", "sec_energy.tex"), encoding="utf-8").read()
    return dict(verdict="CONFIRMED", source="Europe PMC PMC10447234 full text (Ambrogio et al., Nature 620, 2023)",
                source_says_estimated_digital="estimated digital processing" in q,
                source_says_not_integrated="not integrated with digital processing" in q,
                text_uses_equal_quality="equal quality" in tex.lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", default=os.path.join(P, "build", "main.pdf"))
    ap.add_argument("--out", default=os.path.join(P, "records", "revision2", "VERIFY-FINDINGS-2.json"))
    ap.add_argument("--artifacts-only", action="store_true")
    ap.add_argument("--log", action="append", default=None, help="LaTeX logs (default: the v2 build's main.log)")
    a = ap.parse_args()
    logs = a.log or [os.path.join(P, "sessions", "b3b-a2-20261026T220941Z", "outputs", n) for n in ("main.log", "main-arxiv.log")]
    if a.artifacts_only:
        res = dict(F6=f6(a.pdf, logs))
    else:
        res = dict(F1=f1(), F2=f2(), F3=f3(), F4=f4(), F5=f5(), F6=f6(a.pdf, logs), F7=f7(), F8=f8())
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "wb") as f:
        f.write((json.dumps(res, indent=1, default=str) + "\n").encode("utf-8"))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
