"""REVISION: compare the aihwkit preset pulse responses (pod record AIHWKIT-CURVES.json) with our aihwkit-mode tile and with
the old papermap tile, under the same schedules (PLAN-REVISION.md section 1 pass rule). Desk, CPU, no aihwkit.

    python -B revision/compare_curves.py records/revision/AIHWKIT-CURVES.json records/revision/AIHWKIT-COMPARE.json
"""
import json
import math
import os
import statistics
import sys

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sim"))
import memsim_rev as R  # noqa: E402

CAT = json.load(open(os.path.join(HERE, "..", "records", "revision", "CATALOG-REV.json"), "rb"))["entries"]
KEY = {"EcRamPresetDevice": "ecram_li_tang2018", "EcRamMOPresetDevice": "ecram_mo_kim2019"}
SPREADS = ("asym_d2d", "d2d", "bound_d2d", "gamma_up_dtod", "gamma_dn_dtod", "gamma_d2d")


def ours(spec, sched, n, stride):
    t = R.Tile((n, 1), R.DeviceSpec(**spec), 1.0, torch.Generator().manual_seed(0), torch.device("cpu"),
               ngen=torch.Generator().manual_seed(1))
    # the paper model's state u maps to the weight through g_of (gain and offset per device); read the conductance
    t.u = t.u_of_g(torch.zeros((n, 1))) if t.aihw else torch.zeros((n, 1))
    one, zero = torch.ones((n, 1)), torch.zeros((n, 1))
    tr = []
    for d, cnt in sched:
        seq = ([1, -1] * (cnt // 2)) if d == 0 else [d] * cnt
        for s in seq:
            t.apply_pulses(one, zero) if s > 0 else t.apply_pulses(zero, one)
            tr.append(t.g_of(t.u)[:, 0].clone())
    w = torch.stack(tr)  # (pulses, n)
    idx = list(range(0, w.shape[0], stride))
    return dict(mean=w[idx].mean(1).tolist(), sd=w[idx].std(1).tolist(), dev_max=w.max(0).values.tolist(),
                dev_min=w.min(0).values.tolist())


def judge(a, o, n, dw):
    worst = 0.0
    for ma, sa, mo, so in zip(a["mean"], a["sd"], o["mean"], o["sd"]):
        se = math.sqrt(sa * sa / n + so * so / n)
        worst = max(worst, abs(ma - mo) / max(4 * se, 2 * dw))
    ratios = [so / sa for sa, so in zip(a["sd"], o["sd"]) if sa > 1e-9]
    sd_ratio = statistics.median(ratios) if ratios else None
    ext = {}
    for k in ("dev_max", "dev_min"):
        A, O = a[k], o[k]
        se = math.sqrt(statistics.pvariance(A) / len(A) + statistics.pvariance(O) / len(O))
        ext[k] = dict(aihwkit=statistics.fmean(A), ours=statistics.fmean(O),
                      ok=abs(statistics.fmean(A) - statistics.fmean(O)) <= max(4 * se, 2 * dw))
    ok = worst <= 1.0 and (sd_ratio is None or 0.8 <= sd_ratio <= 1.25) and all(e["ok"] for e in ext.values())
    return dict(ok=ok, worst_mean_diff_in_tolerance_units=worst, median_sd_ratio=sd_ratio, extremes=ext,
                max_abs_mean_diff=max(abs(x - y) for x, y in zip(a["mean"], o["mean"])))


def main():
    src = json.load(open(sys.argv[1], "rb"))
    n = src["n_devices"]
    out = dict(schema="altone.x1000.me-revision.aihwkit-compare.v1", aihwkit=src["aihwkit"], n_devices=n, presets={})
    for cls, rec in src["presets"].items():
        sched = [tuple(x) for x in src["schedules"][cls]]
        stride = rec["noise_free"]["index"][1] - rec["noise_free"]["index"][0]
        dw = rec["fields"]["dw_min"]
        res = {}
        for variant in ("noise_free", "noisy"):
            a = rec[variant]
            nf_has_spread = statistics.fmean(a["sd"]) > 1e-6
            for mapping, key in (("aihwkit_mode", KEY[cls]), ("papermap", KEY[cls] + "_papermap")):
                spec = {k: v for k, v in CAT[key]["spec"].items()}
                spec.pop("name", None)
                spec["ref_err"] = 0.0
                if variant == "noise_free":
                    spec["c2c"] = 0.0
                    if not nf_has_spread:
                        for k in SPREADS:
                            spec[k] = 0.0
                o = ours(spec, sched, n, stride)
                res[f"{variant}__{mapping}"] = judge(a, o, n, dw)
        res["mapping_accepted"] = res["noise_free__aihwkit_mode"]["ok"] and res["noisy__aihwkit_mode"]["ok"]
        out["presets"][cls] = res
        print(cls, {k: (v["ok"], round(v["max_abs_mean_diff"], 4)) for k, v in res.items() if isinstance(v, dict)},
              res["mapping_accepted"])
    with open(sys.argv[2], "wb") as f:
        f.write((json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
