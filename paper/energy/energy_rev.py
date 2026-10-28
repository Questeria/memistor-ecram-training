"""REVISION: the conditional matrix-training energy projection on the repaired E3 records (PLAN-REVISION.md section 5).

The model and its inputs are those of energy_system.py (imported, unchanged), with four changes:
  1. pulse counts from the repaired simulator, the reset pulses applied (not charged), and the pulse reset's extra column
     reads added to the TT read count;
  2. two read-efficiency scenarios of the same PCM inference chip [ambrogio2023]: 12.4 TOPS/W (one chip, sustained) and
     6.94 TOPS/W (the authors' PROJECTED full-system figure for five chips: digital processing estimated, not integrated);
  3. the GPU utilisation range as pre-registered in PLAN-PAPER.md (30-55 %) beside the measured 38-43 %;
  4. conditional ratios for cells passing the margin (ideal reads): a ratio is reported only for a cell that PASSES against the stated baseline (FP-SGD or Adam,
     records/revision/RESULTS-REVISION.json); a FAIL cell reports "fails the margin", an UNRESOLVED one "criterion not established".

    python -B energy/energy_rev.py --runs records/revision/runs/e3 --out records/revision/ENERGY-REVISION.json
"""
import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import energy_system as E  # noqa: E402

READ_SCENARIOS = {"chip_12p4": dict(tops=12.4, source="[ambrogio2023]: up to 12.4 TOPS/W chip-sustained (chip 4)"),
                  "system_6p94": dict(tops=6.94, source="[ambrogio2023]: 6.94 TOPS/W, the PROJECTED full-system figure for the "
                                                         "five-chip system (measured analog chips, digital processing estimated: not "
                                                         "integrated; system buses and voltage regulators excluded)")}

MFU = {"measured_38_43": (0.38, 0.43), "planned_30_55": (0.30, 0.55)}

def counts(paths):
    c = E.counts_from_records(paths)
    extra = {}
    for p in paths:
        r = json.load(open(p, "rb"))
        if r["arm"] != "device" or r.get("diverged"):
            continue
        W = sum(l["shape"][0] * l["shape"][1] * l["rows"] for l in r["layers"])
        x = sum(l.get("reset_extra_reads", 0.0) for l in r["layers"]) / max(1, W)
        extra.setdefault((r["task"], r["spec"]["name"], r["algo"]), []).append(x)
    for k, v in extra.items():
        if k in c:
            c[k]["reads_pwr"] += sum(v) / len(v)
            c[k]["reset_extra_reads_pwr"] = sum(v) / len(v)
    return c

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--results", default=os.path.join(HERE, "..", "records", "revision", "RESULTS-REVISION.json"))
    ap.add_argument("--widrow", default=os.path.join(HERE, "..", "..", "records", "ENERGY.json"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    wl = json.load(open(a.widrow, "rb")).get("widrow_energy_per_level_j")
    res = json.load(open(a.results, "rb"))["e3"]
    I = E.INPUTS
    C = counts(sorted(glob.glob(os.path.join(a.runs, "*.json"))))
    g = E.gpu_e(I["h100_mfu"]["central"], I["h100_power_w"]["central"])
    gpu_range = {k: [E.gpu_e(hi, I["h100_power_w"]["low"]) * 1e12, E.gpu_e(lo, I["h100_power_w"]["high"]) * 1e12]
                 for k, (lo, hi) in MFU.items()}
    rows = {}
    for (task, dev, algo), c in sorted(C.items()):
        if dev not in E.DEVICE_PULSE:
            continue
        cell = res.get(task, {}).get("cells", {}).get(f"{dev}__{algo}", {})
        sc = {}
        for sn, s in READ_SCENARIOS.items():
            an = E.analog_e(c, dev, s["tops"], I["line_cap_f_per_cell"]["central"], I["rng_j_per_slot"]["central"],
                            I["array_n"]["central"], I["adc_j_per_conversion"]["central"], I["sram_add_j"]["central"], wl)
            sc[sn] = dict(analog_pj={k: v * 1e12 for k, v in an.items()}, ratio_per_weight_row=g / an["total"],
                          share={k: an[k] / an["total"] for k in ("mvm", "device", "lines", "tt")})
        q = {}
        for base in ("vs_fp", "vs_adam"):
            lab = (cell.get(base) or {}).get("label")
            q[base] = dict(label=lab, ratio_at_equal_quality={sn: (sc[sn]["ratio_per_weight_row"] if lab == "PASS" else None)
                                                              for sn in sc},
                           note=None if lab == "PASS" else ("the cell FAILS the margin" if lab == "FAIL" else "criterion not established (UNRESOLVED)"))
        rows[f"{task}__{dev}__{algo}"] = dict(counts=c, scenarios=sc, equal_quality=q)
    out = dict(schema="altone.x1000.me-revision.energy.v1", kind="CONDITIONAL PROJECTION (not a measurement)",
               assumptions=["accuracy is simulated with ideal fp32 reads; the read energy is borrowed from a PCM inference chip",
                            "per weight per training row: forward + backward reads and the update; attention products, "
                            "nonlinearities, normalisation, activation storage, data movement, control and static power "
                            "are not modelled on either side", "the GPU side is H100 board power at large-run MFU"],
               read_scenarios=READ_SCENARIOS, gpu_pj_central=g * 1e12, gpu_pj_range_by_mfu=gpu_range, rows=rows)
    with open(a.out, "wb") as f:
        f.write((json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    for k, r in rows.items():
        print(k, {sn: round(v["ratio_per_weight_row"], 1) for sn, v in r["scenarios"].items()},
              r["equal_quality"]["vs_fp"]["label"], r["equal_quality"]["vs_adam"]["label"])

if __name__ == "__main__":
    main()
