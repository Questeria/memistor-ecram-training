"""REVISION (lane ME-REVISE 2026-10-26): the revised device catalog, records/revision/CATALOG-REV.json.

Every entry of records/CATALOG.json is kept, except the two aihwkit presets, which are now mapped one to one onto the
aihwkit LinearStepDevice model (DeviceSpec.bounds_model "aihwkit", memsim_rev.py) instead of being copied field by field
into the paper's soft-step model with bounds [-1, 1]. Their values are the aihwkit preset values (aihwkit master,
src/aihwkit/simulator/presets/devices.py, EcRamPresetDevice and EcRamMOPresetDevice, read 2026-10-26; the version
installed on the pod is pinned in records/revision/AIHWKIT-CURVES.json), mapped as:
  dw_min -> n_states = 2 / dw_min (the step is k_nom = 2 / n_states = dw_min);  up_down -> asym = 2 up_down;
  up_down_dtod -> asym_d2d = 2 up_down_dtod;  dw_min_dtod -> d2d (additive);  w_max/w_min -> u_hi/u_lo;
  w_max_dtod = w_min_dtod -> bound_d2d (relative);  gamma_up/down -> gamma_up/dn (divided by the mean bounds in the tile);
  gamma_up/down_dtod -> gamma_up/dn_dtod (absolute);  dw_min_std (mult_noise) -> c2c.
ref_err stays the lane's assumption (0.02 of the half range); aihwkit has no reference error in these presets.
The old field-copy entries are kept beside them as *_papermap for the comparison.

    python -B devices_rev.py   (writes ../records/revision/CATALOG-REV.json)
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REC = os.path.join(HERE, "..", "records")

AIHWKIT_PRESETS = {
    "ecram_li_tang2018": dict(cls="EcRamPresetDevice", dw_min=0.002, up_down=0.0, w_max=1.1724, w_min=-0.8276,
                              gamma_up=0.1153, gamma_down=0.5085, dw_min_dtod=0.1, up_down_dtod=0.01, w_max_dtod=0.05,
                              w_min_dtod=0.05, gamma_up_dtod=0.05, gamma_down_dtod=0.05, dw_min_std=0.3,
                              write_noise_std=0.0, mult_noise=True, mean_bound_reference=True),
    "ecram_mo_kim2019": dict(cls="EcRamMOPresetDevice", dw_min=2.8214e-4, up_down=0.0, w_max=1.1714, w_min=-0.8286,
                             gamma_up=0.4152, gamma_down=0.7342, dw_min_dtod=0.1, up_down_dtod=0.01, w_max_dtod=0.05,
                             w_min_dtod=0.05, gamma_up_dtod=0.05, gamma_down_dtod=0.05, dw_min_std=2.0,
                             write_noise_std=0.0, mult_noise=True, mean_bound_reference=True),
}


def spec_of_preset(p, ref_err=0.02):
    return dict(bounds_model="aihwkit", n_states=2.0 / p["dw_min"], asym=2 * p["up_down"], asym_d2d=2 * p["up_down_dtod"],
                d2d=p["dw_min_dtod"], u_lo=p["w_min"], u_hi=p["w_max"], bound_d2d=p["w_max_dtod"],
                gamma_up=p["gamma_up"], gamma_dn=p["gamma_down"], gamma_up_dtod=p["gamma_up_dtod"],
                gamma_dn_dtod=p["gamma_down_dtod"], c2c=p["dw_min_std"], ref_err=ref_err)


def catalog_rev():
    old = json.load(open(os.path.join(REC, "CATALOG.json"), "rb"))["entries"]
    out = {}
    for k, v in old.items():
        if k in AIHWKIT_PRESETS:
            p = AIHWKIT_PRESETS[k]
            assert p["w_max_dtod"] == p["w_min_dtod"]
            out[k] = dict(v, spec=spec_of_preset(p), label="PUBLISHED-FIT (aihwkit LinearStepDevice, one-to-one)",
                          aihwkit_preset=p, revision="REVISED: shifted bounds, bound-scaled slopes and slope spread kept")
            out[k + "_papermap"] = dict(v, revision="the original field copy into the paper model (kept for comparison)")
        else:
            out[k] = dict(v)
    if "protonic_onen2022" in out:
        out["protonic_onen2022"]["revision"] = "unchanged; a protonic-INSPIRED scenario (asym, gamma, c2c are estimates)"
    return out


def main():
    d = dict(schema="altone.x1000.me-revision.catalog.v1", entries=catalog_rev(), presets=AIHWKIT_PRESETS)
    p = os.path.join(REC, "revision", "CATALOG-REV.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write((json.dumps(d, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps({k: v["spec"] for k, v in d["entries"].items() if "ecram" in k})[:800])


if __name__ == "__main__":
    main()
