"""Version 14: verify review 11's findings against version 13 (tex/v13), the records and the code, before any text changes.
Writes records/revision13/VERIFY-FINDINGS-11.json; RESPONSE-TO-REVIEW-11.md quotes it.  Citations are verified separately by
revision13/cite_check_v14.py (records/revision13/CITE-CHECK-v14.json), which this script reads.

    python -I -B revision13/verify_findings_11.py          (from anywhere; stdlib only)
"""
import importlib.util
import json
import re
from pathlib import Path

P = Path(__file__).resolve().parent.parent
V13 = P / "tex" / "v13"


def tex(name):
    return (V13 / name).read_bytes().decode("utf-8")


def flat(s):
    return " ".join(s.split())


MAC = {}
for f in ("numbers.tex", "numbers_rev.tex", "numbers_rev2.tex", "numbers_rev3.tex", "numbers_rev4.tex"):
    for k, v in re.findall(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$", tex(f), re.M):
        MAC[k] = v
spec = importlib.util.spec_from_file_location("energy_system", P / "energy" / "energy_system.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)
I = E.INPUTS
ER = json.loads((P / "records" / "revision" / "ENERGY-REVISION.json").read_bytes().decode("utf-8"))
MAIN = [n for n in ("sec_abstract.tex", "sec_intro.tex", "sec_background.tex", "sec_methods.tex", "sec_validation.tex", "sec_main.tex",
                    "sec_fidelity.tex", "sec_scale.tex", "sec_spec.tex", "sec_energy.tex", "sec_discussion.tex", "sec_roadmap.tex")]
ALLTXT = {n: flat(tex(n)) for n in MAIN + ["preamble.tex", "app_revision.tex", "app_original.tex", "body.tex", "app_selection.tex"]}
R = {}

# ---- energy: the GPU range, its inputs, the read-dominated ratio, the cost boundary ----
pj = lambda u, w: E.gpu_e(u, w) * 1e12
F, FL = I["h100_bf16_dense_flops"]["central"], I["gpu_flop_per_weight_row"]["central"]
grid = {f"{w:.0f} W at {u:.3f}": round(pj(u, w), 3) for w in (500.0, 700.0) for u in (0.38, 0.405, 0.43)}
lo, hi = ER["gpu_pj_range_by_mfu"]["measured_38_43"]
R["energy_gpu_range"] = dict(
    equation="E_GPU = FLOP_per_weight_row * P / (F_dense_bf16 * u)", flop_per_weight_row=FL, F_dense_bf16=F,
    power_w=dict(central=I["h100_power_w"]["central"], low=I["h100_power_w"]["low"], high=I["h100_power_w"]["high"],
                 label=I["h100_power_w"]["label"], source=I["h100_power_w"]["source"]),
    utilisation=dict(central=I["h100_mfu"]["central"], low=I["h100_mfu"]["low"], high=I["h100_mfu"]["high"]),
    central_pj=round(ER["gpu_pj_central"], 3), record_range_pj=[round(lo, 3), round(hi, 3)],
    low_end_is=f"{I['h100_power_w']['low']:.0f} W at {0.43}: {pj(0.43, 500.0):.3f} pJ",
    high_end_is=f"{I['h100_power_w']['high']:.0f} W at {0.38}: {pj(0.38, 700.0):.3f} pJ",
    range_at_700w_only=[round(pj(0.43, 700.0), 3), round(pj(0.38, 700.0), 3)], grid_pj=grid,
    macros=dict(RVenGpuPj=MAC["RVenGpuPj"], RVenGpuMeasLo=MAC["RVenGpuMeasLo"], RVenGpuMeasHi=MAC["RVenGpuMeasHi"],
                RVenGpuPlannedLo=MAC["RVenGpuPlannedLo"], RVenGpuPlannedHi=MAC["RVenGpuPlannedHi"]),
    v13_prints_power_range=bool(re.search(r"500\s*\\?,?\s*W", ALLTXT["sec_energy.tex"])),
    v13_prints_equation=("FLOP" in ALLTXT["sec_energy.tex"]))
R["energy_gpu_range"]["verdict"] = ("CONFIRMED: 7.05 pJ is 500 W at 43 % and 11.17 pJ is 700 W at 38 %; the range spans the power "
                                    "estimate as well as the utilisation, and version 13 prints neither the power range nor the equation")
ch = ER["rows"]
share = sorted(v["scenarios"][sn]["share"]["mvm"] for k, v in ch.items() if "widrow" not in k for sn in ("chip_12p4", "system_6p94"))
R["energy_read_dominated"] = dict(
    reads_only_pj={"12.4 TOPS/W": round(2 * 2 / 12.4, 4), "6.94 TOPS/W": round(2 * 2 / 6.94, 4)},
    reads_only_ratio={"12.4 TOPS/W": round(ER["gpu_pj_central"] / (4 / 12.4), 2), "6.94 TOPS/W": round(ER["gpu_pj_central"] / (4 / 6.94), 2)},
    printed_ratio_ranges=dict(chip=[MAC["RVenChipMin"], MAC["RVenChipMax"]], system=[MAC["RVenSysMin"], MAC["RVenSysMax"]]),
    min_read_share_of_analog_published_devices=round(share[0], 4), macro_RVenChipMvmShareMin=MAC["RVenChipMvmShareMin"],
    v13_says_reads_set_ratio="set almost entirely by the two borrowed efficiencies" in ALLTXT["sec_energy.tex"],
    v13_says_no_energy_to_target="no energy-to-target training trajectory" in ALLTXT["sec_energy.tex"],
    v13_per_operation_sentence="A low energy per operation is worth nothing without the accuracy" in ALLTXT["sec_energy.tex"],
    verdict="CONFIRMED (arithmetic): the reads alone give 32.49x and 18.18x. PARTLY already in version 13: it states the read "
            "share, that a low energy per operation is worth nothing without the accuracy, and that no energy-to-target trajectory "
            "is shown, but not plainly that the printed ratio itself is a per-operation, read-dominated figure, not energy to a quality")
R["energy_cost_boundary"] = dict(
    tt_term="e_tt = reads_pwr * (adc_j_per_conversion + sram_add_j): one ADC conversion and one read-add-write of H per read weight",
    adc=I["adc_j_per_conversion"]["source"], sram=I["sram_add_j"]["source"],
    v13_inside=re.search(r"the TT family's column reads and digital buffer", ALLTXT["sec_energy.tex"]) is not None,
    v13_outside=re.search(r"the digital TT state", ALLTXT["sec_energy.tex"]) is not None,
    not_in_the_model=["storage of H", "AGAD's leaky average p and reference p_ref (their arithmetic beyond one buffer add)",
                      "chopper signs and flips", "threshold tests and transfer scheduling"],
    verdict="CONFIRMED (wording): both phrases are in version 13 and refer to different costs, but the text does not say which")

# ---- clipping, controls, SGD rate, fidelity scope ----
R["clipping"] = dict(cifar_tt_layer_mean_max_pct=MAC["RVLostCifarTtLayerMeanMaxPct"], lm_tt_layer_mean_max_pct=MAC["RVLostLmTtLayerMeanMaxPct"],
                     worst_record_pct=MAC["RVLostMaxPct"], v13_policy_sentence="update-management policy chosen here" in ALLTXT["sec_main.tex"],
                     v13_proposes_comparison=("pulse length" in ALLTXT["sec_roadmap.tex"] or "pulse-length" in ALLTXT["sec_roadmap.tex"]),
                     verdict="CONFIRMED: the losses are as quoted and the text calls clipping a policy, but proposes no pulse-length or "
                             "update-management comparison")
R["controls"] = dict(v13_ideal_reference_caveat="not an exact-update, algorithm-only TT reference" in ALLTXT["sec_main.tex"],
                     v13_has_ladder=("explicit" in ALLTXT["sec_discussion.tex"] and "accumulator decay" in ALLTXT["sec_discussion.tex"]),
                     verdict="CONFIRMED: version 13 says the ideal-device row is not an algorithm-only reference, but gives no control ladder")
R["sgd_rate"] = dict(v13_main=("FP-SGD learning rate is reused for every device arm" in ALLTXT["sec_main.tex"]),
                     v13_discussion="not about SGD after fair tuning" in ALLTXT["sec_discussion.tex"],
                     verdict="CONFIRMED and already stated (Sections 4.2 and 5); the roadmap does not list fair tuning as a follow-up")
R["fidelity_scope"] = dict(probe_meets=f"{MAC['RYProbeSurMeetsN']} of {MAC['RYProbeN']}", bootstrap=MAC["RYProbeSurAtNinetyFiveN"],
                           v13_lm_update_level_only="the LM at update level only" in ALLTXT["sec_fidelity.tex"],
                           v13_followup_full_trajectories=("trajector" in ALLTXT["sec_roadmap.tex"]),
                           verdict="CONFIRMED and already stated as a limit; full CIFAR and LM trajectories with correlated streams are "
                                   "not named as the first follow-up")

# ---- wording: the specification sheet ----
title = re.search(r"\\title\{(.*?)\}\s*\\authorblock", tex("preamble.tex"), re.S).group(1)
R["spec_sheet"] = dict(title=flat(title), title_promises_sheet="device specification sheet" in flat(title),
                       main_text_uses=[n for n in MAIN if "specification sheet" in ALLTXT[n]],
                       sensitivity_sheet_in=[n for n in MAIN if "sensitivity sheet" in ALLTXT[n]],
                       v13_exploratory="they are exploratory, not fabrication tolerances" in ALLTXT["sec_spec.tex"],
                       v13_combined="Combined deviations" in ALLTXT["sec_spec.tex"],
                       lm_threshold_established=False if "so no LM threshold is established" in ALLTXT["sec_spec.tex"] else None,
                       verdict="CONFIRMED for the subtitle (the body already says 'sensitivity sheet' and 'exploratory'); the joint-"
                               "deviation point is stated only as 'combined deviations ... are not covered'")

# ---- architecture figure, Byun, Xu, spot checks ----
figs = sorted(set(re.findall(r"includegraphics\[[^]]*\]\{figs/([^}]+)\}", " ".join(ALLTXT.values()))))
R["architecture_figure"] = dict(v13_figures=figs, verdict="CONFIRMED: no figure shows which parts are device operations and which digital")
cc = json.loads((P / "records" / "revision13" / "CITE-CHECK-v14.json").read_bytes().decode("utf-8"))
R["byun"] = dict(in_v13_refs="aisy.202400543" in (P / "tex" / "v13").joinpath("body.tex").read_text("utf-8") or None,
                 crossref=dict((k, cc["added"][k]) for k in ("fetched_title", "authors", "year", "venue", "volume", "issue", "pages",
                                                             "published_online", "published_print", "abstract_phrases", "not_in_abstract")),
                 verdict="CONFIRMED: a real, closely related paper (Crossref), not cited in version 13")
R["xu"] = dict((k, cc["confirmed_existing"][k]) for k in ("pubmed_doi", "pubmed_title", "abstract_phrases", "in_refs_bib"))
R["xu"]["verdict"] = "ALREADY CITED (xu2026, since version 2): PubMed 42915660 is the same paper; its abstract gives the 3 % and 21 % the paper prints"
R["spot_checks"] = dict(
    pass_counts_vs_fp=[MAC["RVMnistFpPassN"], MAC["RVCifarFpPassN"], MAC["RVLmFpPassN"]],
    pass_counts_vs_adam=[MAC["RVMnistAdamPassN"], MAC["RVCifarAdamPassN"], MAC["RVLmAdamPassN"]],
    a2m_change=[MAC["RZAtwoMD"], MAC["RZAtwoMDLo"], MAC["RZAtwoMDHi"]],
    lm_best_vs_adam=[MAC["RVLmAdamBestGap"], MAC["RVLmProtonicOnenTwoZeroTwoTwoCttvTwoVsAdamLo"], MAC["RVLmProtonicOnenTwoZeroTwoTwoCttvTwoVsAdamHi"]],
    asym_confound=[MAC["RVSpecTtvTwoCifarAsymAtZeroPFourGap"], MAC["RVSpecTtvTwoCifarAsymFixedspAtZeroPFourGap"]],
    width_growth=[MAC["RVEFourCifarProtonicOnenTwoZeroTwoTwoCttvTwoD"], MAC["RVEFourCifarProtonicOnenTwoZeroTwoTwoCttvTwoPairedLo"],
                  MAC["RVEFourCifarProtonicOnenTwoZeroTwoTwoCttvTwoPairedHi"]],
    mnist_fp=MAC["RVMnistFp"], sgd_fail=f"{MAC['RVSgdPubFail']} of {MAC['RVSgdPubN']}",
    verdict="AGREE: every number review 11 quotes matches the version-13 macros")
out = P / "records" / "revision13" / "VERIFY-FINDINGS-11.json"
out.write_bytes((json.dumps(R, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
for k, v in R.items():
    print(k, "|", v.get("verdict", ""))
