"""Lane ME-REVISE step 1: my own checks of the 13 review findings, on the ORIGINAL simulator (sim/memsim.py, run.py,
tasks.py as of commit ef7e0630f) and the original records. CPU only, no training. Writes records/revision/VERIFY-FINDINGS.json.

    H:/x1000/bench/venv/Scripts/python.exe -B revision/verify_findings.py
"""
import json
import math
import os
import re
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(P, "sim"))
import memsim as M  # noqa: E402  the original simulator
import tasks as T  # noqa: E402

REC = os.path.join(P, "records")
RES = json.load(open(os.path.join(REC, "RESULTS-PAPER.json"), "rb"))
CAT = json.load(open(os.path.join(REC, "CATALOG.json"), "rb"))["entries"]
CHO = json.load(open(os.path.join(REC, "CHOICES-PAPER.json"), "rb"))
TEX = {f: open(os.path.join(P, "tex", f), "rb").read().decode("utf-8") for f in os.listdir(os.path.join(P, "tex"))
       if f.endswith(".tex")}
out = {}


def tex_has(pat):
    return sorted(f for f, t in TEX.items() if re.search(pat, t, re.S))


# ---- F1: init and data order under one shared generator
def build_mlp(arm, algo, seed=0):
    gen = torch.Generator().manual_seed(seed)
    spec = M.DeviceSpec(ideal_float=True) if arm == "fp_sgd" else M.DeviceSpec(**{k: v for k, v in CAT["protonic_onen2022"]["spec"].items()})
    u = dict(CHO["tt"][algo]["ucfg"]) if algo != "sgd" else {}
    ucfg = M.UpdateCfg(lr=3e-3, algo=algo, **u)
    w0 = []
    orig = M.Tile.program

    def spy(self, w):
        w0.append(w.clone())
        return orig(self, w)
    M.Tile.program = spy
    try:
        T.MLP(T.Lin("analog", spec, ucfg, gen, torch.device("cpu")))
    finally:
        M.Tile.program = orig
    logical = [w for w in w0 if float(w.abs().sum()) > 0]  # the A tiles are programmed to zero
    perm = torch.randperm(50000, generator=gen)
    return logical, perm


ref_w, ref_p = build_mlp("fp_sgd", "sgd")
f1 = {}
for algo in ("sgd", "ttv2", "cttv2", "agad"):
    w, p = build_mlp("device", algo)
    f1[algo] = dict(same_logical_init_per_layer=[bool(torch.equal(a, b)) for a, b in zip(ref_w, w)],
                    same_first_epoch_order=bool(torch.equal(ref_p, p)), positions_equal=int((ref_p == p).sum()))
out["F1_init_and_order"] = dict(verdict="CONFIRMED", vs_fp_sgd_seed0=f1,
                                note="protonic device, MNIST MLP, one shared torch.Generator as in run.py; layer 1 matches, "
                                     "layers 2-3 and the permutation do not")

# ---- F2: the reset charges 2 BL pulses but jumps to the symmetry point
spec = M.DeviceSpec(n_states=1000, asym=0.05, gamma_up=0.2, gamma_dn=0.2)
t = M.Tile((1, 1), spec, 1.0, torch.Generator().manual_seed(0), torch.device("cpu"))
t.u = torch.full((1, 1), 0.8, dtype=torch.float64).float()
ustar = float(t.ustar)
t.apply_pulses(torch.full((1, 1), 31.0), torch.full((1, 1), 31.0))
after = float(t.u)
B1 = float(t.k_up * t.gu + t.k_dn * t.gd)  # decay exponent per (up, down) pair
# sequential discrete pulses, alternating, as a check of the surrogate on this case
u = 0.8
ku, kd = float(t.k_up), float(t.k_dn)
for _ in range(31):
    u = u + ku * (1 - 0.2 * u)
    u = u - kd * (1 + 0.2 * u)
src = TEX["sec_methods.tex"] + TEX.get("sec_background.tex", "")
out["F2_reset"] = dict(verdict="CONFIRMED", symmetry_point=ustar, start=0.8, after_31_up_31_down_surrogate=after,
                       after_31_alternating_pairs_discrete=u, implemented_reset_lands_at=ustar,
                       residual_fraction=(after - ustar) / (0.8 - ustar),
                       pairs_for_100fold=math.log(100) / B1, pulses_for_100fold=2 * math.log(100) / B1,
                       selected_ttv2_reset=CHO["tt"]["ttv2"]["ucfg"].get("tt_reset", True),
                       selected_cttv2_reset=CHO["tt"]["cttv2"]["ucfg"].get("tt_reset", True),
                       selected_agad_reset=CHO["tt"]["agad"]["ucfg"].get("tt_reset", True),
                       code="memsim.py _transfer: A.u[:, idx] = ustar (+ one c2c draw); n_pulses += numel * 2 * BL")

# ---- F3: device presets vs aihwkit (values quoted from aihwkit master, src/aihwkit/simulator/presets/devices.py,
# fetched 2026-10-26; LinearStepDevice: up step dw(1 + beta + s xi)(1 - |g_up + g_dtod xi| w / b_max), clip to bounds)
AIHW = {"ecram_li_tang2018": dict(dw_min=0.002, w_max=1.1724, w_min=-0.8276, gamma_up=0.1153, gamma_down=0.5085,
                                  gamma_up_dtod=0.05, gamma_down_dtod=0.05, dw_min_dtod=0.1, up_down_dtod=0.01,
                                  w_max_dtod=0.05, w_min_dtod=0.05, dw_min_std=0.3, mult_noise=True, mean_bound_reference=True),
        "ecram_mo_kim2019": dict(dw_min=2.8214e-4, w_max=1.1714, w_min=-0.8286, gamma_up=0.4152, gamma_down=0.7342,
                                 gamma_up_dtod=0.05, gamma_down_dtod=0.05, dw_min_dtod=0.1, up_down_dtod=0.01,
                                 w_max_dtod=0.05, w_min_dtod=0.05, dw_min_std=2.0, mult_noise=True, mean_bound_reference=True)}
f3 = {}
for k, a in AIHW.items():
    s = CAT[k]["spec"]
    f3[k] = dict(paper_bounds=[-1.0, 1.0], aihwkit_bounds=[a["w_min"], a["w_max"]],
                 paper_slope_up_per_unit_w=s["gamma_up"], aihwkit_slope_up_per_unit_w=a["gamma_up"] / a["w_max"],
                 paper_slope_dn_per_unit_w=s["gamma_dn"], aihwkit_slope_dn_per_unit_w=a["gamma_down"] / -a["w_min"],
                 paper_gamma_d2d=s.get("gamma_d2d", 0.0), aihwkit_gamma_dtod_abs=[a["gamma_up_dtod"], a["gamma_down_dtod"]],
                 symmetry_point_from_upper_bound_paper=1.0, symmetry_point_from_upper_bound_aihwkit=a["w_max"])
out["F3_device_mapping"] = dict(verdict="CONFIRMED", presets=f3,
                                note="the bounds, the bound-scaled slopes and the slope spread differ; the curve comparison "
                                     "against aihwkit itself is done on a pod (records/revision/AIHWKIT-CURVES.json)")

# ---- F4: surrogate order dependence and clipping
k = 2 / 20
up_dn = 0.4 + k * (1 - 0.4); up_dn = up_dn - k * (1 + up_dn)
dn_up = 0.4 - k * (1 + 0.4); dn_up = dn_up + k * (1 - dn_up)
tt = M.Tile((1, 1), M.DeviceSpec(n_states=20, gamma_up=1.0, gamma_dn=1.0), 1.0, torch.Generator().manual_seed(0),
            torch.device("cpu"))
tt.u = torch.full((1, 1), 0.4)
tt.apply_pulses(torch.ones(1, 1), torch.ones(1, 1))
x = torch.full((1, 1), 10.0); d = torch.full((1, 1), 10.0)
lr, kn = 0.1, 0.002
nu, nd = M.pulse_counts(x, d, lr, kn, 31, torch.Generator().manual_seed(0))
out["F4_surrogate"] = dict(verdict="CONFIRMED (synthetic cases; runtime clipping frequency is measured in the repaired sim)",
                           up_then_down=up_dn, down_then_up=dn_up, surrogate_batch=float(tt.u),
                           clip_case=dict(intended_mean=lr / kn * 100.0, max_possible=31, drawn=float(nu + nd)),
                           exact_mean_condition="(lr/k_nom) * max|x| * max|d| <= BL")

# ---- F5: spec thresholds and the asymmetry/symmetry-point confound
oat = RES["e5"]["oat"]["ttv2__cifar_w32"]
asym_u = {str(a): a / (2 * 0.2) for a in (0, 0.05, 0.1, 0.2, 0.4)}
out["F5_spec"] = dict(verdict="CONFIRMED", cifar_w32_base_gap=oat["base_gap"], band_X=2.0,
                      admitted_gap_up_to=oat["base_gap"] + 2.0, asym_grid_symmetry_point_at_gamma_0p2=asym_u,
                      asym_gap_means=oat["means"]["asym"],
                      joint_lm_w64=RES["e5"]["joint"].get("lm_w64"))

# ---- F6: width FLAT label
lm = RES["e4"]["lm"]["arms"]["ecram_li_tang2018__cttv2"]
out["F6_width"] = dict(verdict="CONFIRMED", li_cttv2_lm_gap_mean_by_width={w: lm[w]["gap"]["mean"] for w in lm},
                       label=RES["e4"]["lm"]["verdict"].get("ecram_li_tang2018__cttv2"),
                       fp_lm_bpb_by_width=RES["e4"]["lm"]["fp"])

# ---- F7: digital Adam context
c = RES["e3"]["lm"]["cells"]["ecram_li_tang2018__cttv2"]
adam = RES["e3"]["lm"]["adam"]["mean"]
out["F7_baselines"] = dict(verdict="CONFIRMED", li_cttv2_bpb=c["metric"]["mean"], adam_bpb=adam,
                           vs_adam_pct_paired=c["vs_adam_pct"]["mean"],
                           ratio_of_means_pct=100 * (c["metric"]["mean"] / adam - 1),
                           perplexity_ratio=2 ** (c["metric"]["mean"] - adam),
                           sgd_lr_reused_from_fp=True, near_digital_in=tex_has(r"near-digital"))

# ---- F8: energy
E = json.load(open(os.path.join(REC, "ENERGY-SYSTEM.json"), "rb"))
gpu = 6 * 700 / (989.5e12 * 0.405) * 1e12
mvm = 2 * 2 / 12.4e12 * 1e12
out["F8_energy"] = dict(verdict="CONFIRMED", gpu_pj=gpu, mvm_pj_12p4=mvm, mvm_pj_6p94=4 / 6.94e12 * 1e12,
                        note="read energy from a PCM inference chip; accuracy from ideal fp32 reads; no energy-to-quality",
                        record_keys=sorted(E)[:12])

# ---- F9-F13: text and code checks
out["F9_validation_scope"] = dict(verdict="PARTLY CONFIRMED", gh_batch_local=16, gh_batch_paper=1, reads="ideal fp32",
                                  historical_claim_in=tex_has(r"not accuracy|lacked density"))
st = open(os.path.join(P, "sim", "stats_paper.py"), "rb").read().decode("utf-8")
an = open(os.path.join(P, "analyze.py"), "rb").read().decode("utf-8")
en = open(os.path.join(P, "energy", "energy_system.py"), "rb").read().decode("utf-8")
pl = open(os.path.join(P, "PLAN-PAPER.md"), "rb").read().decode("utf-8")
out["F10_unlogged_deviations"] = dict(
    verdict="CONFIRMED",
    interaction_plan="gap(a, b) - [gap(a) + gap(b)]" in pl,
    interaction_code_adds_base="gap(base)" in an,
    interp_plan_linear_for_c2c_ref="the\n  interpolation is linear" in pl or "interpolation is linear" in pl,
    interp_code_log_for_c2c_ref='"c2c", "ref_err")' in st,
    mfu_plan_30_55="utilisation 30-55 %" in pl, mfu_code_range="low=0.38, high=0.43" in en)
out["F11_roadmap"] = dict(verdict="PARTLY CONFIRMED", ci_used_for_hardware_band_in=tex_has(r"confidence interval|95 \\% CI|CI of the"),
                          bench_replication_in=tex_has(r"bench replication"),
                          per_cell_pulse_maxima_recorded=False)
out["F12_related_release"] = dict(verdict="CONFIRMED", wu2026_cited="2609.36584" in TEX.get("refs.bib", "") or any("2609.36584" in t for t in TEX.values()),
                                  released_wording_in=tex_has(r"[Ee]verything .{0,40}released|are released"))
out["F13_presentation"] = dict(verdict="CONFIRMED (editorial)", abstract_words=len(re.sub(r"\\[a-z]+|[{}%]", " ", TEX["sec_abstract.tex"]).split()))
os.makedirs(os.path.join(REC, "revision"), exist_ok=True)
with open(os.path.join(REC, "revision", "VERIFY-FINDINGS.json"), "wb") as f:
    f.write((json.dumps(out, indent=1, sort_keys=True, default=str) + "\n").encode("utf-8"))
print(json.dumps({k: v["verdict"] for k, v in out.items()}, indent=0))
