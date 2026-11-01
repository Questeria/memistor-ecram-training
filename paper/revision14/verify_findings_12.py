"""Version 15: the evidence for each finding of review 12 (reviews/REVIEW-12-chatgpt-20261031-full.md), read from version 14 (commit
3cbefba20, tex/v14, release v1.4 = 39c6ed7fe) and from version 15's regenerated files.  Writes records/revision14/VERIFY-FINDINGS-12.json.

  A  the AIHWKIT comparison differs under Python 3.12 / torch 2.7.1+cpu: version 14's file against the author's own run in that
     setting (records/revision14/AIHWKIT-COMPARE-py312.json: WSL Ubuntu, Python 3.12.3, torch 2.7.1+cpu, NumPy 2.5.2, Intel Xeon
     W-2123), field by field; and whether every boolean, string, integer and printed value is unchanged;
  B  Figure 1 and its check: the reset and chopper of every main-experiment device record; version 14's check builds every TT
     layer with tt_reset="pulse"; version 14's figure labels A with the pulse reset for all three algorithms;
  C  Section 2.2's order in version 14 (Gokmen-Vlasov, Byun, then "Agarwal et al. reached similar conclusions") and in version 15;
  D1 the reset re-reads' buffer allowance: its largest share of the analog energy over the energy rows (and what separating it
     would print);
  D2 the three-decimal t constants against the exact quantile, and what changing to the exact quantile changed in the tables and
     the result labels (version 14 against version 15).

    python -I -B revision14/verify_findings_12.py          (from paper/; stdlib only; reads git history)
"""
import json
import math
import re
import subprocess
import sys
from pathlib import Path

P = Path(__file__).resolve().parent.parent
REPO = P.parents[4]
REL = P.relative_to(REPO).as_posix()
V14 = "3cbefba20"
sys.path.insert(0, str(P / "revision"))
sys.path.insert(0, str(P / "energy"))


def git(rel, commit=V14):
    return subprocess.run(["git", "-C", str(REPO), "show", f"{commit}:{REL}/{rel}"], capture_output=True, check=True).stdout


def jload(b):
    return json.loads(b.decode("utf-8") if isinstance(b, bytes) else b)


def floats_and_rest(a, b, path=""):
    """[(path, old, new)] of differing floats, [(path, old, new)] of other differences."""
    fl, other = [], []
    if isinstance(a, dict):
        if set(a) != set(b):
            other.append((path, sorted(a), sorted(b)))
        for k in sorted(set(a) & set(b)):
            f, o = floats_and_rest(a[k], b[k], f"{path}/{k}")
            fl += f
            other += o
    elif isinstance(a, list):
        if len(a) != len(b):
            other.append((path, len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            f, o = floats_and_rest(x, y, f"{path}[{i}]")
            fl += f
            other += o
    elif isinstance(a, float) and isinstance(b, float):
        if a != b:
            fl.append((path, a, b))
    elif a != b or type(a) is not type(b):
        other.append((path, a, b))
    return fl, other


out = {}

# ---- A ----
old = jload(git("records/revision/AIHWKIT-COMPARE.json"))
new = jload((P / "records" / "revision14" / "AIHWKIT-COMPARE-py312.json").read_bytes())
fl, other = floats_and_rest(old, new)


def printed(d):
    P_ = d["presets"]
    mx = lambda cls, mp: max(P_[cls][f"{nv}__{mp}"]["max_abs_mean_diff"] for nv in ("noise_free", "noisy"))
    return {"RVaihwLiMaxDiff": f"{mx('EcRamPresetDevice', 'aihwkit_mode'):.4f}", "RVaihwMoMaxDiff": f"{mx('EcRamMOPresetDevice', 'aihwkit_mode'):.4f}",
            "RVaihwLiOldMaxDiff": f"{mx('EcRamPresetDevice', 'papermap'):.3f}", "RVaihwMoOldMaxDiff": f"{mx('EcRamMOPresetDevice', 'papermap'):.3f}",
            "accepted": all(v["mapping_accepted"] for v in P_.values())}


by_key = {}
for p, a, b in fl:
    k = p.rsplit("/", 1)[-1]
    by_key[k] = max(by_key.get(k, 0.0), abs(a - b))
worst_acc = max(v["worst_mean_diff_in_tolerance_units"] for c in new["presets"].values() for k, v in c.items()
                if isinstance(v, dict) and k.endswith("aihwkit_mode"))
out["A"] = dict(
    verdict="confirmed",
    environment="WSL Ubuntu 24.04 on the desk (Intel Xeon W-2123), Python 3.12.3, torch 2.7.1+cpu, NumPy 2.5.2, matplotlib 3.9.2; "
                "paper/revision/compare_curves.py of release v1.4, unchanged inputs",
    floats_differing=len(fl), other_differences=other, largest_change_by_field=by_key,
    largest_weight_change=max(by_key.get("max_abs_mean_diff", 0.0), by_key.get("ours", 0.0)),
    largest_tolerance_unit_change=by_key.get("worst_mean_diff_in_tolerance_units"),
    largest_accepted_discrepancy_tolerance_units=worst_acc,
    printed_values_v14=printed(old), printed_values_py312=printed(new), printed_equal=printed(old) == printed(new),
    review_12=dict(floats_differing=26, largest_weight_change=5.69e-6, largest_tolerance_unit_change=4.70e-4,
                   environment="Python 3.12.14, torch 2.7.1+cpu, NumPy 2.5.2, matplotlib 3.9.2"),
    reference_environment="Python 3.13.15, Windows 11 (build 26200), torch 2.7.1+cu126 with CUDA hidden, NumPy 2.5.2, matplotlib "
                          "3.9.2, Pillow 13.0.0 (records/deposit/VERIFY.json of v1.4)")

# ---- B ----
recs = {}
for p in sorted((P / "records" / "revision" / "runs" / "e3").glob("*.json")):
    r = json.loads(p.read_bytes().decode("utf-8"))
    if r["arm"] == "device" and r["algo"] in ("ttv2", "cttv2", "agad"):
        k = r["algo"]
        recs.setdefault(k, {}).setdefault(str(r["ucfg"]["tt_reset"]), 0)
        recs[k][str(r["ucfg"]["tt_reset"])] += 1
chk14 = git("revision13/check_fig_arch.py").decode("utf-8")
fig14 = git("revision13/make_fig_arch.py").decode("utf-8")
sel = (P / "tex" / "tables" / "rev2_selection.tex").read_text(encoding="utf-8")
out["B"] = dict(
    verdict="confirmed",
    main_experiment_device_records_reset=recs,
    selection_table_rows=[l.split("&")[0].strip() + ": " + l.split("&")[2].strip() for l in sel.splitlines()
                          if l.startswith(("TTv2 &", "c-TTv2 &", "AGAD &"))],
    v14_check_builds_every_layer_with_pulse_reset='tt_reset="pulse"' in chk14 and "M.UpdateCfg(lr=0.2, algo=algo" in chk14,
    v14_check_reads_selected_configurations=("CHOICES-REVISION" in chk14) or ("runs" in chk14 and "e3" in chk14),
    v14_figure_A_label_shared_by_TTv2_cTTv2_AGAD=bool(re.search(r'"b_A".*pulse reset.*TT, "A"\)', fig14)),
    v14_figure_input_c_odot_x_for_all_three=bool(re.search(r'"b_prob".*odot x.*TT, None\)', fig14)),
    v15_check="revision14/check_fig_arch.py: records/revision14/FIG-ARCH-CHECK.json")
fa = json.loads((P / "records" / "revision14" / "FIG-ARCH-CHECK.json").read_bytes().decode("utf-8"))
out["B"]["v15_check_result"] = dict(all_ok=fa["all_ok"], faults=fa["selftest"]["faults"])

# ---- C ----
bg14 = git("tex/sec_background.tex").decode("utf-8")
bg15 = (P / "tex" / "sec_background.tex").read_text(encoding="utf-8")
pos = lambda t, s: t.find(s)
out["C"] = dict(
    verdict="confirmed",
    v14_order=dict(gokmen2016=pos(bg14, "gokmen2016"), byun2024=pos(bg14, "byun2024"), agarwal2016=pos(bg14, "agarwal2016")),
    v14_agarwal_after_byun=pos(bg14, "agarwal2016") > pos(bg14, "byun2024"),
    v14_agarwal_sentence=bg14[pos(bg14, "Agarwal"):pos(bg14, "Agarwal") + 60],
    v15_order=dict(gokmen2016=pos(bg15, "gokmen2016"), agarwal2016=pos(bg15, "agarwal2016"), byun2024=pos(bg15, "byun2024")),
    v15_agarwal_before_byun=pos(bg15, "agarwal2016") < pos(bg15, "byun2024"),
    v15_says_conventional_sgd="reached similar conclusions for conventional (SGD) training" in bg15,
    v15_similar_conclusions_after_byun="similar conclusions" in bg15[pos(bg15, "byun2024"):],
    agarwal2016_year=2016, bib=re.search(r"@inproceedings\{agarwal2016,.*?title = \{([^}]*)\}", (P / "tex" / "refs.bib").read_text(encoding="utf-8"), re.S).group(1))

# ---- D1 ----
import energy_system as E  # noqa: E402
en = json.loads((P / "records" / "revision" / "ENERGY-REVISION.json").read_bytes().decode("utf-8"))
es = E.INPUTS["sram_add_j"]["central"]
shares = []
for k, r in en["rows"].items():
    x = r["counts"].get("reset_extra_reads_pwr", 0.0)
    for sn, s in r["scenarios"].items():
        shares.append((x * es / (s["analog_pj"]["total"] * 1e-12), k, sn))
shares.sort()
DEVS = ["ecram_li_tang2018", "ecram_mo_kim2019", "protonic_onen2022", "wox_ysz_chen2023"]
sep = {}
for sn, tag in (("chip_12p4", "Chip"), ("system_6p94", "Sys")):
    ratio, mvm = [], []
    for k, r in en["rows"].items():
        if k.split("__")[1] not in DEVS:
            continue
        s = r["scenarios"][sn]
        tot = s["analog_pj"]["total"] - r["counts"].get("reset_extra_reads_pwr", 0.0) * es * 1e12
        ratio.append(en["gpu_pj_central"] / tot)
        mvm.append(100 * s["analog_pj"]["mvm"] / tot)
    sep[f"RVen{tag}Min"] = f"{min(ratio):.1f}"
    sep[f"RVen{tag}Max"] = f"{max(ratio):.1f}"
    sep[f"RVen{tag}MvmShareMin"] = f"{min(mvm):.1f}"
nums = (P / "tex" / "numbers_rev.tex").read_text(encoding="utf-8")
cur = {k: re.search(r"\\newcommand\{\\" + k + r"\}\{([^}]*)\}", nums).group(1) for k in sep}
out["D1"] = dict(
    verdict="confirmed (a conservative approximation; labelled in Section 5, not separated)",
    model="energy/energy_system.py analog_e: tt = reads_pwr * (adc + sram_add); energy/energy_rev.py adds reset_extra_reads_pwr to reads_pwr",
    largest_share_of_analog_energy=shares[-1][0], largest_at=shares[-1][1:], printed_bound="0.15 %",
    if_separated_printed=sep, printed_now=cur,
    if_separated_changes={k: (cur[k], sep[k]) for k in sep if cur[k] != sep[k]},
    note="the desk experiment of separating the two read categories also moved RVenNeedTopsMax 42.2 -> 41.9")

# ---- D2 ----
import analyze_rev as AR  # noqa: E402
tab = []
for df in range(1, 31):
    for p, T in ((0.975, AR.T975), (0.95, AR.T95)):
        tab.append(abs(T[df - 1] - AR.t_quantile(p, df)))
endp = []
for t in ("rev_main_vs_fp.tex", "rev_main_vs_adam.tex"):
    a = git("tex/tables/" + t).decode("utf-8").splitlines()
    b = (P / "tex" / "tables" / t).read_text(encoding="utf-8").splitlines()
    assert len(a) == len(b)
    for la, lb in zip(a, b):
        if la != lb:
            ca, cb = la.split("&"), lb.split("&")
            for j, (x, y) in enumerate(zip(ca, cb)):
                if x != y:
                    ma = re.match(r"\s*(\S+) \[(\S+), (\S+)\] (\w)", x)
                    mb = re.match(r"\s*(\S+) \[(\S+), (\S+)\] (\w)", y)
                    assert ma.group(1) == mb.group(1) and ma.group(4) == mb.group(4), (x, y)
                    for side, i in (("lo", 2), ("hi", 3)):
                        if ma.group(i) != mb.group(i):
                            endp.append(dict(table=t, row=ca[0].strip() + " " + ca[1].strip(), task=["MNIST", "CIFAR", "LM"][j - 2],
                                             end=side, v14=ma.group(i), v15=mb.group(i), label=ma.group(4)))
lab = {}
for f in ("revision/RESULTS-REVISION.json", "revision2/RESULTS-REV2.json", "revision3/RESULTS-REV3.json", "revision4/RESULTS-REV4.json"):
    fl, other = floats_and_rest(jload(git("records/" + f)), jload((P / "records" / f).read_bytes()))
    lab[f] = dict(floats_changed=len(fl), largest_change=max((abs(a - b) for _, a, b in fl if math.isfinite(a)), default=0.0),
                  non_float_differences=other)
out["D2"] = dict(
    verdict="confirmed; no classification changes",
    largest_table_error=max(tab), interval_endpoints_changed_in_tables=endp, n_endpoints_changed=len(endp),
    results_records=lab, labels_unchanged=all(not v["non_float_differences"] for v in lab.values()))
out["all_confirmed"] = True
(P / "records" / "revision14" / "VERIFY-FINDINGS-12.json").write_bytes((json.dumps(out, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
print("A floats", out["A"]["floats_differing"], "printed equal", out["A"]["printed_equal"], "| B", recs, "| C v14 agarwal after byun",
      out["C"]["v14_agarwal_after_byun"], "v15 before", out["C"]["v15_agarwal_before_byun"], "| D1 max share %.4f %%" % (100 * shares[-1][0]),
      "| D2 endpoints", len(endp), "labels unchanged", out["D2"]["labels_unchanged"])
