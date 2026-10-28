"""System-level training energy per weight per row (PLAN-PAPER.md E6), periphery included, against an H100 at its measured
utilisation. Every input carries its source and a label: SPEC (vendor rating), MEASURED (published measurement),
PROJECTION (published projection), SIM (counted in our simulations), ESTIMATE (ours).

Unit: one "row" = one input vector presented to a weight matrix (one sample of an MLP layer, one patch position of a
convolution, one token of the LM).
- The GPU spends 6 FLOP per weight per row (forward, input gradient, weight gradient).
- The analog array spends:
  - two MVM MACs (forward and backward reads, at a measured chip's energy per MAC, periphery included);
  - the update pulses (SIM count x energy per pulse);
  - the pulse-line charging and pulse generation (amortised over the array size N);
  - the Tiki-Taka family's column reads and digital buffer updates.

    python -B energy/energy_system.py --runs records/runs/e3 --out records/ENERGY-SYSTEM.json
"""
import argparse
import glob
import itertools
import json
import math
import os
from collections import defaultdict

INPUTS = {
    # GPU
    "h100_power_w": dict(central=700.0, low=500.0, high=700.0, label="SPEC (range: ESTIMATE of sustained draw)",
                         source="NVIDIA H100 product page: max TDP up to 700 W (SXM) [nvidiah100]; low end ESTIMATE"),
    "h100_bf16_dense_flops": dict(central=989.5e12, label="SPEC",
                                  source="NVIDIA H100 page: BF16 tensor 1,979 TFLOPS with sparsity, i.e. 989.5 dense [nvidiah100]"),
    "h100_mfu": dict(central=0.405, low=0.38, high=0.43, label="MEASURED",
                     source="Llama 3 405B pre-training on 8K-16K H100s: BF16 MFU 38-43 % (380-430 TFLOPs/GPU) [dubey2024]"),
    "gpu_flop_per_weight_row": dict(central=6.0, label="STANDARD",
                                    source="forward 2 + input-gradient 2 + weight-gradient 2 FLOP per weight per row"),
    # analog MVM (forward and backward reads), periphery included
    "mvm_tops_per_w": dict(central=12.4, low=9.76, high=84.0, label="MEASURED (central, low) / PROJECTION (high)",
                           source="12.4 TOPS/W chip-sustained, 14 nm PCM analog-AI chip [ambrogio2023]; 9.76 TOPS/W for 8-bit "
                                  "MVMs, 64-core PCM chip [legallo2023]; 84,000 GOPS/s/W projected RPU system [gokmen2016]"),
    "mvm_mac_per_weight_row": dict(central=2.0, label="STANDARD", source="one forward and one backward (transpose) read"),
    # update: energy per device pulse
    "e_pulse_j": dict(label="per device, see DEVICE_PULSE"),
    # pulse lines and pulse generation
    "line_cap_f_per_cell": dict(central=0.04e-15, low=0.02e-15, high=0.2e-15, label="ESTIMATE",
                                source="about 0.2 fF/um interconnect x 0.2 um cell pitch (ours); high: 1 um pitch"),
    "rng_j_per_slot": dict(central=20e-15, low=5e-15, high=100e-15, label="ESTIMATE",
                           source="one stochastic bit per line per pulse slot (an LFSR plus a comparator; ours)"),
    "array_n": dict(central=1024, low=256, high=4096, label="DESIGN CHOICE", source="array dimension N (N x N tiles)"),
    "adc_j_per_conversion": dict(central=1e-12, low=0.2e-12, high=5e-12, label="ESTIMATE",
                                 source="an 8-bit SAR conversion; the range spans the published survey's energy-efficient "
                                        "designs to conservative ones [murmann_adc]"),
    "sram_add_j": dict(central=1e-12, low=0.2e-12, high=3e-12, label="ESTIMATE",
                       source="one read-add-write of the 16-32 bit buffer H per read weight (ours; cf. [horowitz2014])"),
    "slots_bl": dict(central=31, label="SIM", source="pulse slots per row (the simulator's BL)"),
}
DEVICE_PULSE = {  # energy per device update pulse and the pulse-line voltage
    "ecram_li_tang2018": dict(e_pulse_j=1e-15, v=2.0, label="PROJECTION (pulse) / ESTIMATE (voltage)",
                              source="~1 fJ projected for 100 nm x 100 nm Li-ECRAM [tang2018]; a few volts of gate pulse (ours)"),
    "ecram_mo_kim2019": dict(e_pulse_j=1e-15, v=2.0, label="ESTIMATE", source="the Li-ECRAM projection reused"),
    "protonic_onen2022": dict(e_pulse_j=2.5e-15, v=10.0, label="PARTLY-PUBLISHED",
                              source="~2.5 fJ per 5 ns pulse (gate charging) and 10 V / -8.5 V pulses [onen2022]"),
    "wox_ysz_chen2023": dict(e_pulse_j=1e-15, v=5.0, label="ESTIMATE",
                             source="the Li-ECRAM projection reused; the measured cell used 100 ms pulses at 5 V [chen2023]"),
    "widrow1960_claimed": dict(e_pulse_j=None, v=None, label="CLAIM+ESTIMATE",
                               source="plating energy per level from Widrow's figures (lane ME ENERGY.json widrow_energy_per_level_j)"),
}


def gpu_e(mfu, power):
    return INPUTS["gpu_flop_per_weight_row"]["central"] * power / (INPUTS["h100_bf16_dense_flops"]["central"] * mfu)


def analog_e(counts, dev, tops, ccell, erng, n, eadc, esram, widrow_level_j=None):
    bl = INPUTS["slots_bl"]["central"]
    e_mvm = INPUTS["mvm_mac_per_weight_row"]["central"] * 2.0 / (tops * 1e12)  # 2 ops per MAC
    dp = DEVICE_PULSE[dev]
    e_pulse = dp["e_pulse_j"] if dp["e_pulse_j"] is not None else widrow_level_j
    e_dev = counts["ppwr"] * e_pulse
    v = dp["v"] or 0.0
    # half-select: each line carries V/2; a line spans N cells
    e_lines = bl * (counts["px"] + counts["pd"]) * ccell * (v / 2) ** 2 + 2 * bl * erng / n
    e_tt = counts["reads_pwr"] * (eadc + esram)
    return dict(mvm=e_mvm, device=e_dev, lines=e_lines, tt=e_tt, total=e_mvm + e_dev + e_lines + e_tt)


def counts_from_records(paths):
    """Mean over seeds of the row-weighted per-weight pulse count, slot occupancies and TT column reads."""
    acc = defaultdict(list)
    for p in paths:
        r = json.load(open(p, "rb"))
        if r["arm"] != "device" or r.get("diverged"):
            continue
        dev = r["spec"]["name"]
        W = sum(l["shape"][0] * l["shape"][1] * l["rows"] for l in r["layers"])
        if W == 0:
            continue
        ppwr = sum(l["pulses"] for l in r["layers"]) / W
        px = sum(l["mean_px"] * l["shape"][0] * l["shape"][1] * l["rows"] for l in r["layers"]) / W
        pd = sum(l["mean_pd"] * l["shape"][0] * l["shape"][1] * l["rows"] for l in r["layers"]) / W
        reads = 0.0
        if r["algo"] != "sgd":
            u = r["ucfg"]
            batch = r["budget"]["batch"] if r.get("budget") else 128
            steps = r["samples"] / (batch * (r["budget"].get("ctx", 1) if r.get("budget") else 1))
            for l in r["layers"]:
                ncols = u.get("tt_cols") or math.ceil(l["shape"][1] / u["tt_period"])
                reads += steps * min(ncols, l["shape"][1]) * l["shape"][0]  # weights read over the run
            reads /= W
        acc[(r["task"], dev, r["algo"])].append(dict(ppwr=ppwr, px=px, pd=pd, reads_pwr=reads, file=os.path.basename(p)))
    out = {}
    for k, v in acc.items():
        out[k] = {f: sum(x[f] for x in v) / len(v) for f in ("ppwr", "px", "pd", "reads_pwr")}
        out[k]["n"] = len(v)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True, help="a directory of run records (E3)")
    ap.add_argument("--widrow", default=os.path.join(os.path.dirname(__file__), "..", "..", "records", "ENERGY.json"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    wl = json.load(open(a.widrow, "rb")).get("widrow_energy_per_level_j")
    counts = counts_from_records(sorted(glob.glob(os.path.join(a.runs, "*.json"))))
    I = INPUTS
    g_c = gpu_e(I["h100_mfu"]["central"], I["h100_power_w"]["central"])
    g_lo = gpu_e(I["h100_mfu"]["high"], I["h100_power_w"]["low"])  # the GPU's best case
    g_hi = gpu_e(I["h100_mfu"]["low"], I["h100_power_w"]["high"])
    rows = {}
    for (task, dev, algo), c in sorted(counts.items()):
        if dev not in DEVICE_PULSE:
            continue
        cen = analog_e(c, dev, I["mvm_tops_per_w"]["central"], I["line_cap_f_per_cell"]["central"], I["rng_j_per_slot"]["central"],
                       I["array_n"]["central"], I["adc_j_per_conversion"]["central"], I["sram_add_j"]["central"], wl)
        worst = analog_e(c, dev, I["mvm_tops_per_w"]["low"], I["line_cap_f_per_cell"]["high"], I["rng_j_per_slot"]["high"],
                         I["array_n"]["low"], I["adc_j_per_conversion"]["high"], I["sram_add_j"]["high"], wl)
        best = analog_e(c, dev, I["mvm_tops_per_w"]["high"], I["line_cap_f_per_cell"]["low"], I["rng_j_per_slot"]["low"],
                        I["array_n"]["high"], I["adc_j_per_conversion"]["low"], I["sram_add_j"]["low"], wl)
        meas = analog_e(c, dev, I["mvm_tops_per_w"]["central"], I["line_cap_f_per_cell"]["central"], I["rng_j_per_slot"]["central"],
                        I["array_n"]["central"], I["adc_j_per_conversion"]["central"], I["sram_add_j"]["central"], wl)
        rows[f"{task}__{dev}__{algo}"] = dict(
            counts=c, analog_pj=dict(central={k: v * 1e12 for k, v in cen.items()}, pessimistic={k: v * 1e12 for k, v in worst.items()},
                                     optimistic={k: v * 1e12 for k, v in best.items()}),
            ratio_gpu_over_analog=dict(central=g_c / cen["total"], range_low=g_lo / worst["total"], range_high=g_hi / best["total"],
                                       measured_mvm_only=g_c / meas["total"]),
            share_of_total_central={k: cen[k] / cen["total"] for k in ("mvm", "device", "lines", "tt")},
            device_pulse=DEVICE_PULSE[dev])
    # what the MVM periphery must reach for 100x at the central GPU figure, with the device terms of the best device
    need = {}
    for k, r in rows.items():
        rest = sum(r["analog_pj"]["central"][x] for x in ("device", "lines", "tt")) * 1e-12
        budget = g_c / 100.0 - rest
        need[k] = (I["mvm_mac_per_weight_row"]["central"] * 2.0 / budget / 1e12) if budget > 0 else None
    out = dict(schema="altone.x1000.me-paper.energy-system.v1", unit="J per weight per row (reported in pJ)", inputs=INPUTS,
               device_pulse=DEVICE_PULSE, gpu_pj=dict(central=g_c * 1e12, best_case=g_lo * 1e12, worst_case=g_hi * 1e12),
               rows=rows, mvm_tops_per_w_needed_for_100x=need, widrow_energy_per_level_j=wl,
               note="central: measured PCM-chip MVM efficiency + central estimates; range: every input at its low/high end "
                    "(the analog pessimistic total against the GPU's best case, and the reverse)")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "wb").write((json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    for k, r in rows.items():
        q = r["ratio_gpu_over_analog"]
        print(f"{k}: central {q['central']:.3g}x  range {q['range_low']:.3g}-{q['range_high']:.3g}x  "
              f"mvm share {r['share_of_total_central']['mvm']:.2f}")


if __name__ == "__main__":
    main()
