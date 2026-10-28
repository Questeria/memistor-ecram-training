"""ME-REVISE-3: verify the findings of review 3 (reviews/REVIEW-3-chatgpt-20261027-full.md) against the records and the code.

    H:/x1000/bench/venv/Scripts/python.exe -B revision3/verify_findings_3.py

Reads only existing records and source (no run). Writes records/revision3/VERIFY-FINDINGS-3.json. Every derived number is
computed here from the records; each check that supports a verdict is also shown to react to a planted fault (`faults`).
"""
import glob
import json
import math
import os
import re
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(P, "revision"))
sys.path.insert(0, os.path.join(P, "sim"))
import analyze_rev as AR  # noqa: E402

OUT = os.path.join(P, "records", "revision3", "VERIFY-FINDINGS-3.json")


def rd(rel):
    return open(os.path.join(P, rel), "rb").read().decode("utf-8")


def floors(ref, cmp_):
    """The A1 floor as implemented (independent: sum var + sum var over R) and the paired floor (var of the differences)."""
    R = len(ref)
    mr, mc = st.fmean(ref), st.fmean(cmp_)
    ind = math.sqrt((st.variance(ref) + st.variance(cmp_)) / R) / abs(mr)
    pai = math.sqrt(st.variance([c - r for c, r in zip(cmp_, ref)]) / R) / abs(mr)
    err = abs(mc - mr) / abs(mr)
    ex = lambda f: math.sqrt(max(0.0, err * err - f * f))
    return dict(rel_mean_err=err, floor_independent=ind, excess_independent=ex(ind), floor_paired=pai, excess_paired=ex(pai))


def f1():
    src = rd("sim/run_rev2.py")
    line = [ln.strip() for ln in src.splitlines() if "vs_slot_noise_floor" in ln and "math.sqrt" in ln]
    shares = ("keep_fire=fire" in src) and ("fire=fire" in src)
    drops = 'if kk not in ("mean", "var")' in src
    seqdoc = rd("sim/pulse_seq_rev2.py")
    noise_once = "added once per sample at the pre-sample state" in seqdoc
    res = json.load(open(os.path.join(P, "records", "revision2", "RESULTS-REV2.json"), "rb"))
    rows = []
    for r in res["probes"]:
        s = r["seq"]
        rows.append(dict(task=r["task"], layer=r["layer"], update=r["update"], draws=r["draws"], rel_mean_err=s["rel_mean_err"],
                         floor_independent=s["noise_floor"], excess_reported=s["excess"], passes=s["passes"]))
    # the reviewer's illustration: 16 reference draws alternating 0 and 2; comparison = reference + 0.2
    ref = [0.0 if i % 2 == 0 else 2.0 for i in range(16)]
    ill = floors(ref, [x + 0.2 for x in ref])
    # fault: an UNPAIRED comparison (same marginal, shuffled pairing) must not lose its excess under the paired floor either
    # (the paired floor equals the independent one in expectation when the pairing carries nothing)
    sh = [x + 0.2 for x in ref[1:] + ref[:1]]
    ill_unpaired = floors(ref, sh)
    lm = [x for x in rows if x["task"] == "lm" and x["layer"] == 9 and x["update"] == 2250][0]
    ok = shares and sum(1 for x in rows if x["excess_reported"] == 0.0) == len(rows) and ill["excess_independent"] == 0.0 < ill["excess_paired"]
    return dict(
        verdict="CONFIRMED" if ok else "REFUTED",
        evidence=dict(
            floor_line_as_implemented=line,
            seq_and_slot_share_line_firings=shares,
            surrogate_draws_its_own_counts=("MR.pulse_counts(xx, d, lr, k, u.BL, g)" in src),
            per_cell_means_and_variances_discarded=drops,
            seq_noise_added_once_per_sample=noise_once,
            probes=rows,
            n_probes=len(rows), n_seq_excess_zero=sum(1 for x in rows if x["excess_reported"] == 0.0),
            n_seq_rel_err_over_0p05=sum(1 for x in rows if x["rel_mean_err"] > 0.05),
            lm_output_2250=lm,
            illustration_paired=ill, illustration_shuffled_pairing=ill_unpaired),
        note=("The floor of run_rev2.py line 121 sums the two methods' variances as if their draws were independent, but seq "
              "replays slot's line firings (keep_fire/fire). Every seq excess is 0, while the raw relative mean difference "
              "exceeds the 0.05 line on several probes, so whether seq meets its line is undetermined from the summaries "
              "(the paired cross-moments were not saved). For the surrogate the independent floor is the right one: its "
              "Poisson counts are drawn separately from the firings. seq adds its write noise once per sample at the "
              "pre-sample state and clips per sample; the paper's text does not say so."))


def f2():
    e3 = AR.load("e3")
    fp = {(r["task"], r["seed"]): AR.metric(r) for r in e3 if AR.arm_key(r) == "fp"}
    sur = {(r["task"], r["spec"]["name"], r["algo"], r["seed"]): AR.metric(r) for r in e3 if r["arm"] == "device"}
    seq = {}
    for r in AR.load("fid"):
        seq.setdefault((r["task"], r["spec"]["name"], r["algo"]), {})[r["seed"]] = AR.metric(r)
    cells = {}
    for (t, d, a), by in sorted(seq.items()):
        seeds = sorted(s for s in by if (t, s) in fp and (t, d, a, s) in sur)
        gq = [AR.gap(t, fp[(t, s)], by[s]) for s in seeds]
        gs = [AR.gap(t, fp[(t, s)], sur[(t, d, a, s)]) for s in seeds]
        cq, cs = AR.ci(gq), AR.ci(gs)
        cd = AR.ci([x - y for x, y in zip(gq, gs)])
        cells[f"{t}__{d}__{a}"] = dict(task=t, seeds=seeds, sur=dict(mean=cs["mean"], ci95=[cs["lo"], cs["hi"]], label=AR.label(t, cs)),
                                       seq=dict(mean=cq["mean"], ci95=[cq["lo"], cq["hi"]], label=AR.label(t, cq)),
                                       dgap=dict(mean=cd["mean"], ci95=[cd["lo"], cd["hi"]]))
    trans = {k: [c["sur"]["label"], c["seq"]["label"]] for k, c in cells.items() if c["sur"]["label"] != c["seq"]["label"]}
    rev = []
    for t in ("mnist", "cifar"):
        ks = [k for k in cells if cells[k]["task"] == t]
        for i, a in enumerate(ks):
            for b in ks[i + 1:]:
                ds = cells[a]["sur"]["mean"] - cells[b]["sur"]["mean"]
                dq = cells[a]["seq"]["mean"] - cells[b]["seq"]["mean"]
                if ds * dq < 0:
                    rev.append(dict(pair=[a, b], sur_sep=ds, seq_sep=dq, registered=abs(ds) > AR.LINE[t] / 2))
    tt = max(abs(c["dgap"]["mean"]) for k, c in cells.items() if not k.endswith("__sgd"))
    txt = rd("tex/sec_fidelity.tex") + rd("tex/sec_abstract.tex")
    ok = bool(trans) and len(rev) >= 2 and ("preserves the ranking" in txt or "No pair of cells swaps order" in txt)
    return dict(verdict="CONFIRMED" if ok else "REFUTED", evidence=dict(
        cells=cells, label_transitions_same_three_seeds=trans, all_mean_order_reversals=rev,
        n_registered_reversals=sum(1 for x in rev if x["registered"]), tt_family_max_abs_dgap=tt,
        text_claims_preservation=("preserves the ranking" in txt), text_claims_no_swap=("No pair of cells swaps order" in txt),
        text_valid_reference=("valid reference for training" in txt), text_either_update=("under either update" in txt)),
        note="Same seeds 0-2 on both arms: CIFAR Li-ECRAM c-TTv2 PASS (surrogate) -> UNRESOLVED (seq); two mean-order "
             "reversals below the registered 1 pp separation; MNIST MO-ECRAM SGD is UNRESOLVED on both arms at n = 3 "
             "(its n = 5 main-table label is FAIL).")


def f3():
    e4 = json.load(open(os.path.join(P, "records", "revision", "RESULTS-REVISION.json"), "rb"))["e4"]["cifar"]["arms"]
    arms = {k: dict(paired=dict(D=v["paired"]["D"], ci90=v["paired"]["ci90"], verdict=v["paired"]["verdict"]),
                    welch=dict(D=v["test"]["D"], ci90=v["test"]["ci90"], verdict=v["test"]["verdict"])) for k, v in e4.items()}
    not_excl = sorted(k for k, v in e4.items() if v["paired"]["ci90"][1] >= v["paired"]["margin"])
    txt = rd("tex/sec_scale.tex")
    ok = "protonic_onen2022__cttv2" in not_excl and "growth below or at the margin" in txt
    return dict(verdict="CONFIRMED" if ok else "REFUTED", evidence=dict(
        arms=arms, paired_upper_at_or_above_margin=not_excl,
        text_says_below_or_at_margin=("growth below or at the margin, since the interval includes 2" in txt),
        files_with_sub_margin=sorted(os.path.basename(f) for f in glob.glob(os.path.join(P, "tex", "*.tex"))
                                     if "sub-margin" in open(f, "rb").read().decode("utf-8"))),
        note="An interval containing 2 pp leaves the size of the growth unresolved against the margin; growth beyond 2 pp is "
             "not excluded for protonic c-TTv2 (paired) and Li-ECRAM TTv2 (paired and Welch).")


def f4():
    import torch
    import run_rev2 as RR
    # the reviewer's model: one shared row line (p = 0.5), 128 column lines (p = 0.5), balanced signs
    n = 128
    s = torch.tensor([1.0 if j % 2 == 0 else -1.0 for j in range(n)], dtype=torch.float64)
    cov_same, var = 0.125 - 0.0625, 0.25 - 0.0625
    exact_pair = cov_same / var
    exact_signed_mean = exact_pair * (float(s.sum()) ** 2 - n) / (n * (n - 1))
    g = torch.Generator().manual_seed(7)
    R = 200000
    row = (torch.rand(R, 1, 1, generator=g, dtype=torch.float64) < 0.5).double()
    col = (torch.rand(R, 1, n, generator=g, dtype=torch.float64) < 0.5).double()
    x = row * col * s.view(1, 1, n)
    res = x - x.mean(0)
    sim_offcorr = RR._offcorr(res, 2)
    z = res / res.std(0, unbiased=False)
    C = torch.einsum("rj,rk->jk", z[:, 0, :], z[:, 0, :]) / R
    off = ~torch.eye(n, dtype=torch.bool)
    sim_abs = float(C[off].abs().mean())
    sim_rms = float(C[off].pow(2).mean().sqrt())
    # fault: with all signs equal the same code must report the full 1/3 (the statistic is not insensitive in general)
    x1 = row * col
    same_sign_offcorr = RR._offcorr(x1 - x1.mean(0), 2)
    # heterogeneous variances: cell j scaled by w_j; pooled normalisation shrinks the statistic below the per-pair value
    w = torch.tensor([10.0] + [0.1] * (n - 1), dtype=torch.float64).view(1, 1, n)
    xh = x1 * w
    het_offcorr = RR._offcorr(xh - xh.mean(0), 2)
    ok = abs(sim_offcorr) < 0.011 and sim_abs > 0.3 and het_offcorr < 0.05
    return dict(verdict="CONFIRMED" if ok else "REFUTED", evidence=dict(
        offcorr_source=[ln.strip() for ln in open(os.path.join(P, "sim", "run_rev2.py"), "rb").read().decode().splitlines()
                        if "off = " in ln or "v = (res" in ln or "return float(off" in ln],
        exact_pair_correlation=exact_pair, exact_signed_mean_balanced=exact_signed_mean,
        simulated_offcorr_balanced=sim_offcorr, simulated_mean_abs_pearson=sim_abs, simulated_rms_pearson=sim_rms,
        simulated_offcorr_all_same_sign=same_sign_offcorr, simulated_offcorr_heterogeneous_scale=het_offcorr, draws=R),
        note="The statistic is a pooled, signed, normalised covariance: balanced signs cancel it to -1/381 although every pair "
             "has |correlation| 1/3, and unequal cell variances shrink it. It cannot show that dependence is weak. It was "
             "descriptive (no pass line), so the A1 pass count does not depend on it.")


def f5():
    pub = rd("PUBLISHING.md")
    app = rd("tex/app_revision.tex")
    body = rd("tex/body.tex")
    ok = ("Version 2 (this paper)" in app) or ("make_arxiv_source.py" in pub)
    return dict(verdict="CONFIRMED" if ok else "REFUTED", evidence=dict(
        app_revision_says_version2_this_paper=("Version 2 (this paper)" in app),
        app_revision_mentions_review_2=("second review" in app or "review 2" in app.lower()),
        availability_lists=dict((k, k.replace("_", "\\_") in body or k in body) for k in (
            "PLAN-REVISION-2.md", "RESPONSE-TO-REVIEW-2.md", "pulse_seq_rev2.py", "run_rev2.py", "analyze_rev2.py")),
        publishing_names_make_arxiv_source=("make_arxiv_source.py" in pub),
        make_arxiv_source_exists=os.path.exists(os.path.join(P, "revision2", "make_arxiv_source.py")),
        build_rev2_exists=os.path.exists(os.path.join(P, "pod", "build_rev2.sh")),
        publishing_attributes_abstract_to_analyze_rev2=bool(re.search(r"generated by `revision2/analyze_rev2.py`", pub)),
        make_abstract_exists=os.path.exists(os.path.join(P, "revision2", "make_abstract.py"))),
        note="Documentation only; the delivered archive is not shown broken.")


def minor():
    disc = rd("tex/sec_discussion.tex")
    return dict(
        reset_limitations_bullet=dict(verdict="CONFIRMED (minor)", evidence=dict(
            bullet_names_which_mean=("macro" in disc.split("The reset.")[1][:400] if "The reset." in disc else None)),
            note="The limitations bullet quotes one mean residual without saying it is the macro-average over runs."),
        mo_sgd_either_update=dict(verdict="CONFIRMED (part of finding 2)",
                                  note="'far over the line under either update' mixes the n = 5 FAIL with the n = 3 cells, "
                                       "which are UNRESOLVED on both arms."),
        editorial=dict(verdict="NOTED (no error)", note="Length (37 pages of which much is superseded history), dense Table 9 "
                       "and rotated labels of Figure 2: presentation suggestions, not findings of error."),
        loose_main_arxiv_bbl=dict(verdict="CONFIRMED (minor)", evidence=dict(
            loose_bbl_exists=os.path.exists(os.path.join(P, "tex", "main-arxiv.bbl"))),
            note="The loose tex/main-arxiv.bbl is older than the one inside the archive; the archive is the deliverable."))


def main():
    out = dict(schema="verify-findings-3/v1", review="reviews/REVIEW-3-chatgpt-20261027-full.md",
               support="reviews/review-3-support/ (copies of the reviewer's files, SHA256SUMS.txt)",
               F1_paired_floor=f1(), F2_labels_and_ranking=f2(), F3_sub_margin_growth=f3(), F4_correlation_statistic=f4(),
               F5_history_and_directions=f5(), minor=minor())
    # self-checks with planted faults: each verdict's key evidence must flip on the fault
    E1, E4 = out["F1_paired_floor"]["evidence"], out["F4_correlation_statistic"]["evidence"]
    faults = dict(
        f1_paired_floor_keeps_excess=E1["illustration_paired"]["excess_paired"] > 0.19 and E1["illustration_paired"]["excess_independent"] == 0.0,
        f1_shuffled_pairing_floor_not_zero=E1["illustration_shuffled_pairing"]["floor_paired"] > 0.3,
        f4_same_sign_shows_full_correlation=abs(E4["simulated_offcorr_all_same_sign"] - 1 / 3) < 0.01,
        f4_balanced_cancels=abs(E4["simulated_offcorr_balanced"] - E4["exact_signed_mean_balanced"]) < 0.005,
        f4_abs_does_not_cancel=abs(E4["simulated_mean_abs_pearson"] - 1 / 3) < 0.01)
    out["self_checks"] = faults
    out["self_checks_all_ok"] = all(faults.values())
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "wb").write((json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    print("self_checks_all_ok", out["self_checks_all_ok"], faults)
    for k in ("F1_paired_floor", "F2_labels_and_ranking", "F3_sub_margin_growth", "F4_correlation_statistic", "F5_history_and_directions"):
        print(k, out[k]["verdict"])


if __name__ == "__main__":
    main()
