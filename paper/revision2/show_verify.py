"""Print a short digest of records/revision2/VERIFY-FINDINGS-2.json (or the file given)."""
import json
import os
import sys

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(P, "records", "revision2", "VERIFY-FINDINGS-2.json"), "rb"))
r = lambda x: [round(v, 3) for v in x]
if "F1" in d:
    f = d["F1"]
    print("F1", round(f["worst_layer_lost_frac"], 4), f["worst_tag"], f["worst_layer"], round(f["poisson31_p_gt_31"], 4))
    for k, v in d["F2"]["arms"].items():
        print("F2", k, v["welch"]["verdict"], r(v["welch"]["ci90"]), "|", v["paired"]["verdict"], r(v["paired"]["ci90"]),
              r(v["paired"]["diffs"]), "hash1", v["one_data_hash_per_seed_across_widths"])
    print("F3", {k: v for k, v in d["F3"].items() if k != "choices"})
    print("F4", {k: v for k, v in d["F4"].items() if k not in ("analysis_substitutes_base",)})
    print("F5", d["F5"])
    f = d["F7"]
    print("F7", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in f.items() if k not in ("per_device", "n_reset_from")})
    print("F7dev", {k: {kk: round(vv, 2) for kk, vv in v.items() if vv is not None} for k, v in f["per_device"].items()})
    print("F8", d["F8"])
f = d["F6"]
print("F6", f["tex_bare_placeholders"], f["pdf"], f["overfull_gt_2pt"])
