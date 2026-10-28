"""Energy per weight update: GPU versus electrochemical crossbars (lane ME). Writes ../records/ENERGY.json.

"The same update" = one sample's rank-1 outer-product accumulation into one weight (what a crossbar does per sample).
Every input is cited or labelled ESTIMATE; the activity numbers (device pulses and line-slot occupancy per weight per
sample) are MEASURED in this lane's MNIST catalog runs (records/runs/mnist/CAT_*__s0.json).
python -B energy.py
"""
import glob
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(HERE, "..", "records")

INPUTS = {
    "h100_tdp_w": (700.0, "NVIDIA H100 SXM5 datasheet: max TDP up to 700 W"),
    "h100_bf16_dense_flops": (989.4e12, "NVIDIA H100 SXM5 datasheet: BF16 tensor 1,979 TFLOPS with sparsity = 989.4 dense"),
    "flops_per_update": (2.0, "one multiply-accumulate of x_i d_j into the weight gradient"),
    "hbm_pj_per_bit": (3.9, "O'Connor et al., MICRO 2017 (Fine-Grained DRAM): HBM2 ~3.9 pJ/bit; ESTIMATE for HBM3"),
    "sgd_bytes_per_weight_step": (10.0, "fp32 master weight read + write (8 B) + bf16 gradient read (2 B)"),
    "batch_small": (128.0, "this lane's batch (samples per optimizer step)"),
    "wire_cap_ff_per_cell": (0.04, "ESTIMATE: 0.2 fF/um wire x 0.2 um cell pitch"),
    "slots_BL": (31.0, "pulse slots per sample (sim)"),
    "adc_pj_per_conversion": (1.0, "ESTIMATE: an 8-bit SAR conversion per weight read when TTv2 reads a column of A"),
    "sram_add_pj": (1.0, "ESTIMATE: one read-add-write of the digital buffer H per weight read (TTv2)"),
    # protonic (Onen 2022)
    "protonic_pulse_fj": (2.5, "Onen et al. Science 2022: ~2.5 fJ per pulse transient (gate charging) + ~15 aJ proton transfer"),
    "protonic_v": (10.0, "Onen et al. 2022: +10 V / -8.5 V gate pulses"),
    # Li-ECRAM (Tang 2018)
    "li_ecram_pulse_fj": (1.0, "Tang et al. IEDM 2018: ~1 fJ projected for 100x100 nm devices (PROJECTION)"),
    "li_ecram_v": (2.0, "ESTIMATE: a few volts of gate pulse"),
    # metal-oxide ECRAM and WOx/YSZ: no published energy; use the Li-ECRAM projection (ESTIMATE)
    # Widrow's memistor
    "widrow_current_a": (5e-3, "Widrow et al. 1961: 'several milliamperes of plating current' (5 mA taken)"),
    "widrow_full_range_s": (10.0, "Widrow et al. 1961: '100 ohms to 1 ohm ... in about 10 seconds'"),
    "widrow_levels": (1000.0, "'thousands of possible analog storage levels' (low end)"),
    "cell_voltage_v": (0.3, "ESTIMATE: Cu/Cu2+ plating overpotential + solution IR drop at a few mA"),
    # pencil lead today (ESTIMATE geometry)
    "lead_d_m": (0.5e-3, "0.5 mm lead"),
    "lead_len_m": (0.02, "20 mm immersed (ESTIMATE)"),
    "g_bare_s": (0.2, "5 ohm bare (Hayes 2011)"),
    "g_plated_s": (2.0, "0.5 ohm plated (Hayes 2011)"),
    "cu_sigma_s_per_m": (5.96e7, "copper conductivity"),
    "cu_density_kg_m3": (8960.0, "copper"),
    "cu_molar_kg": (0.063546, "copper"),
    "faraday": (96485.33, "C/mol"),
    "pencil_levels": (100.0, "this lane's estimate (devices.py pencil_lead_today)"),
    # system level, periphery included (DACs, ADCs, drivers, read-out): published figures per operation
    "ambrogio2023_tops_per_w": (12.4, "Ambrogio et al., Nature 620, 768 (2023): 14 nm PCM analog-AI chip, 35M devices, 'analog, "
                                      "low-power peripheral circuitry', up to 12.4 TOPS/W chip-sustained (MEASURED, inference MVM)"),
    "gokmen_vlasov2016_gops_per_w": (84000.0, "Gokmen and Vlasov, Front. Neurosci. 2016: RPU training system incl. periphery, "
                                              "84,000 GigaOps/s/W (PROJECTION)"),
}



def v(k):
    return INPUTS[k][0]


def main():
    out = dict(schema="altone.x1000.me.energy.v1", inputs={k: dict(value=a, source=b) for k, (a, b) in INPUTS.items()},
               results_are="DEV")
    e_flop_peak = v("h100_tdp_w") / v("h100_bf16_dense_flops")
    gpu = {
        "e_flop_peak_pj": e_flop_peak * 1e12,
        "update_pj_peak_floor": v("flops_per_update") * e_flop_peak * 1e12,
        "update_pj_50pct": v("flops_per_update") * e_flop_peak * 2 * 1e12,
        "optimizer_rmw_pj_per_weight_step": v("sgd_bytes_per_weight_step") * 8 * v("hbm_pj_per_bit"),
    }
    gpu["update_pj_50pct_batch128"] = gpu["update_pj_50pct"] + gpu["optimizer_rmw_pj_per_weight_step"] / v("batch_small")
    out["gpu"] = gpu
    bar = gpu["update_pj_peak_floor"]  # the GPU's best case is the bar

    # pencil-lead geometry -> plating charge for the full range
    d, L = v("lead_d_m"), v("lead_len_m")
    dg = v("g_plated_s") - v("g_bare_s")
    t_cu = dg * L / (v("cu_sigma_s_per_m") * math.pi * d)
    vol = math.pi * d * L * t_cu
    q_full = vol * v("cu_density_kg_m3") / v("cu_molar_kg") * 2 * v("faraday")
    out["pencil_geometry"] = dict(cu_thickness_m=t_cu, cu_volume_m3=vol, plating_charge_full_range_c=q_full)

    e_widrow_level = v("widrow_current_a") * v("widrow_full_range_s") / v("widrow_levels") * v("cell_voltage_v")
    e_pencil_level = q_full / v("pencil_levels") * v("cell_voltage_v")
    wire = v("wire_cap_ff_per_cell") * 1e-15
    per_dev = {
        "protonic_onen2022": (v("protonic_pulse_fj") * 1e-15,
                              v("protonic_pulse_fj") * 1e-15 / 4 + wire * (v("protonic_v") / 2) ** 2, "PARTLY-PUBLISHED"),
        "ecram_li_tang2018": (v("li_ecram_pulse_fj") * 1e-15,
                              v("li_ecram_pulse_fj") * 1e-15 / 4 + wire * (v("li_ecram_v") / 2) ** 2, "PROJECTION"),
        "ecram_mo_kim2019": (v("li_ecram_pulse_fj") * 1e-15,
                             v("li_ecram_pulse_fj") * 1e-15 / 4 + wire * (v("li_ecram_v") / 2) ** 2,
                             "ESTIMATE (Li-ECRAM projection reused)"),
        "wox_ysz_chen2023": (v("li_ecram_pulse_fj") * 1e-15,
                             v("li_ecram_pulse_fj") * 1e-15 / 4 + wire * (v("li_ecram_v") / 2) ** 2,
                             "ESTIMATE (Li-ECRAM projection reused; the measured cell used 100 ms pulses at 5 V)"),
        "widrow1960_claimed": (e_widrow_level, 0.0, "CLAIM+ESTIMATE (macroscopic, individually wired cells)"),
        "widrow1960_pessimistic": (e_widrow_level, 0.0, "CLAIM+ESTIMATE"),
        "pencil_lead_today": (e_pencil_level, 0.0, "ESTIMATE"),
    }
    out["devices_by_task"] = {}
    for task in ("mnist", "cifar", "lm"):
      rows = {}
      for f in sorted(glob.glob(os.path.join(REC, "runs", task, "CAT_*__s0.json"))):
          with open(f, "rb") as fh:
              r = json.loads(fh.read().decode("utf-8"))
          name = r["spec"]["name"]
          if name not in per_dev:
              continue
          e_pulse, e_half, lab = per_dev[name]
          nw = sum(l["shape"][0] * l["shape"][1] for l in r["layers"])
          # weight-averaged activity per weight per sample
          pul = sum(l["pulses_per_weight_per_row"] * l["shape"][0] * l["shape"][1] for l in r["layers"]) / nw
          occ = sum((l["mean_px"] + l["mean_pd"]) * l["shape"][0] * l["shape"][1] for l in r["layers"]) / nw
          e = pul * e_pulse + v("slots_BL") * occ * e_half
          if r["algo"] == "ttv2":  # each A weight is read (ADC) and its H entry updated once per tt_period batches
              e += (v("adc_pj_per_conversion") + v("sram_add_pj")) * 1e-12 / (r["ucfg"]["tt_period"] * v("batch_small"))
          rows[f"{name}__{r['algo']}"] = dict(device_pulses_per_weight_per_sample=pul, line_slot_occupancy=occ,
                                              e_pulse_j=e_pulse, e_halfselect_j=e_half, energy_label=lab,
                                              update_energy_pj=e * 1e12, advantage_vs_gpu_peak=bar / (e * 1e12),
                                              advantage_vs_gpu_50pct=gpu["update_pj_50pct"] / (e * 1e12),
                                              record=os.path.relpath(f, REC).replace("\\", "/"))
      out["devices_by_task"][task] = rows
    rows = out["devices_by_task"]["mnist"]  # the pre-registered activity source
    out["devices"] = rows
    h100_tops_w = v("h100_bf16_dense_flops") / v("h100_tdp_w") / 1e12
    out["system_level_with_periphery"] = dict(
        h100_tops_per_w_peak=h100_tops_w,
        measured_chip_ambrogio2023_x=v("ambrogio2023_tops_per_w") / h100_tops_w,
        projected_rpu_gokmen_vlasov2016_x=v("gokmen_vlasov2016_gops_per_w") / 1000 / h100_tops_w,
        note="per operation, periphery included; the measured chip is PCM inference (not ECRAM training); the projection is "
             "an RPU training system. Both are below the 100x line; the device-plus-line figures above exclude periphery.")
    out["widrow_energy_per_level_j"] = e_widrow_level
    out["pencil_energy_per_level_j"] = e_pencil_level
    p = os.path.join(REC, "ENERGY.json")
    with open(p, "wb") as fh:
        fh.write((json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    for k, r in rows.items():
        print(f"{k:40s} {r['update_energy_pj']:.3e} pJ  adv(peak) {r['advantage_vs_gpu_peak']:.3g}")
    print(json.dumps(gpu))


if __name__ == "__main__":
    main()
