"""Rebuild Tables 6-7 of the paper (the probe tables, tex/tables/rev4_probe_sur.tex, rev4_probe_seq.tex, rev4_dep.tex) from the
12 saved pulse-draw files alone, and compare them byte for byte with the paper's (PLAN-REVISION-4.md section 2).

    H:/x1000/bench/venv/Scripts/python.exe -B revision4/rebuild_draw_tables.py --draws <dir with the 12 .npz>
        [--json records/revision4/DRAW-REBUILD.json] [--selftest]

From each probe record it takes only the draw file's name and SHA-256, the probe's layer, update, shape and clipping figures,
and the bootstrap count; every statistic in the tables (variance ratio, gain difference and its bootstrap interval, raw and
excess mean differences, both floors, per-pair dependence, the version-3 pooled statistic) is recomputed on the CPU from the
arrays with the same functions as the probe (sim/run_rev3.py, sim/run_rev2.py) and the same bootstrap seeds. A file whose
SHA-256 differs from the record is refused. --selftest also shows the comparison failing on a perturbed draw and on a wrong hash.
"""
import argparse
import copy
import glob
import hashlib
import json
import math
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(P, "revision"))
sys.path.insert(0, os.path.join(P, "revision3"))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(P, "sim"))
import numpy as np  # noqa: E402
import torch  # noqa: E402

import analyze_rev3 as A3  # noqa: E402
import analyze_rev4 as A4  # noqa: E402
import run_rev2 as RR  # noqa: E402
import run_rev3 as R3  # noqa: E402

PROBES = os.path.join(P, "records", "revision3", "runs", "fidprobe3-probes")
RUNS = os.path.join(P, "records", "revision3", "runs", "fidprobe3")
TABLES = ["rev4_probe_sur.tex", "rev4_probe_seq.tex", "rev4_dep.tex"]


class HashMismatch(Exception):
    pass


def recompute(p, arrs):
    """The probe record p's statistics, recomputed from the arrays (run_rev3._probe3's order and seeds)."""
    stk = {nm: torch.from_numpy(arrs[nm]).double() for nm in ("surrogate", "seq", "slot")}
    Q, Pexp = torch.from_numpy(arrs["Q"]).double(), torch.from_numpy(arrs["Pexp"]).double()
    sgn = torch.sign(Pexp)
    out = copy.deepcopy(p)
    summ = {nm: RR._summ(list(stk[nm].float().unbind(0)), Q, Pexp) for nm in ("surrogate", "seq", "slot")}
    ref = summ["slot"]
    R = stk["slot"].shape[0]
    assert R == p["draws"], (R, p["draws"])
    for i, nm in enumerate(("surrogate", "seq", "slot")):
        s = summ[nm]
        dm = s["mean"] - ref["mean"]
        rn = float(ref["mean"].norm())
        okv = ref["var"] > 1e-12
        vr = (s["var"][okv] / ref["var"][okv]) if bool(okv.any()) else None
        rec = out[nm]
        rec["vs_slot_rel_mean_err"] = float(dm.norm()) / rn if rn else None
        rec["vs_slot_noise_floor"] = math.sqrt(float((s["var"].sum() + ref["var"].sum()) / R)) / rn if rn else None
        rec["vs_slot_var_ratio_median"] = float(vr.median()) if vr is not None else None
        rec["rho_row"], rec["rho_col"] = s["rho_row"], s["rho_col"]
        if nm != "slot":
            boot = p[nm]["paired"]["boot"]
            rec["paired"] = R3.paired(stk[nm], stk["slot"], Q, boot, R3.CFG3["boot_seed"] + 7919 * p["layer"] + 31 * p["update"] + i)
        rec["dep"] = dict(row=R3.dep(stk[nm], sgn, 2), col=R3.dep(stk[nm], sgn, 1))
    return out


def numeric_diff(a, b, path=""):
    """Largest relative difference between two nested records (numbers only)."""
    if isinstance(a, dict):
        return max([numeric_diff(a[k], b.get(k), path + "/" + k) for k in a if k in b] or [0.0])
    if isinstance(a, bool) or a is None or b is None or isinstance(a, (str, list)):
        return 0.0
    if isinstance(a, (int, float)):
        if not (math.isfinite(a) and math.isfinite(b)):
            return 0.0 if a == b else float("inf")
        return abs(a - b) / max(1e-12, abs(a), abs(b))
    return 0.0


def rebuild(draws, outdir, perturb=None, wrong_hash=None):
    tmp = tempfile.mkdtemp(prefix="drawrebuild_")
    try:
        r3 = os.path.join(tmp, "revision3")
        os.makedirs(os.path.join(r3, "runs", "fidprobe3-probes"))
        shutil.copytree(RUNS, os.path.join(r3, "runs", "fidprobe3"))
        worst, files = 0.0, []
        for f in sorted(glob.glob(os.path.join(PROBES, "*.probes.json"))):
            d = json.load(open(f, "rb"))
            new = []
            for p in d["probes"]:
                fn = os.path.join(draws, p["draws_file"])
                h = hashlib.sha256(open(fn, "rb").read()).hexdigest()
                want = p["draws_sha256"] if wrong_hash != p["draws_file"] else "0" * 64
                if h != want:
                    raise HashMismatch(p["draws_file"])
                with np.load(fn) as z:
                    arrs = {k: z[k].copy() for k in z.files}
                if perturb == p["draws_file"]:
                    arrs["seq"][0] += 0.05 * np.abs(arrs["seq"]).max()
                q = recompute(p, arrs)
                worst = max(worst, numeric_diff({k: p[k] for k in ("surrogate", "seq", "slot")},
                                                {k: q[k] for k in ("surrogate", "seq", "slot")}))
                new.append(q)
                files.append(dict(file=p["draws_file"], sha256=h, bytes=os.path.getsize(fn)))
            open(os.path.join(r3, "runs", "fidprobe3-probes", os.path.basename(f)), "wb").write(
                json.dumps(dict(d, probes=new)).encode("utf-8"))
        keep = A3.R3
        A3.R3 = r3
        try:
            PR, _ = A3.probes3()
        finally:
            A3.R3 = keep
        A4.write_probe_tables(PR, outdir)
        same = {t: open(os.path.join(outdir, t), "rb").read() == open(os.path.join(A4.TEX, "tables", t), "rb").read()
                for t in TABLES}
        return dict(files=files, max_rel_diff_vs_records=worst, tables_identical=same, all_identical=all(same.values()))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--draws", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "draws", "rev3"))
    ap.add_argument("--json", default="")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    out = tempfile.mkdtemp(prefix="drawtables_")
    res = rebuild(a.draws, out)
    print("tables identical:", res["tables_identical"], "max rel diff vs records:", f"{res['max_rel_diff_vs_records']:.2e}")
    if a.selftest:
        first = res["files"][0]["file"]
        seq_files = [f["file"] for f in res["files"]]
        pert = rebuild(a.draws, tempfile.mkdtemp(prefix="drawtables_f_"), perturb=seq_files[3])
        try:
            rebuild(a.draws, tempfile.mkdtemp(prefix="drawtables_h_"), wrong_hash=first)
            hash_caught = False
        except HashMismatch:
            hash_caught = True
        res["selftest"] = dict(perturbed_draw_caught=not pert["all_identical"], perturbed_file=seq_files[3],
                               wrong_hash_caught=hash_caught)
        print("selftest", res["selftest"])
    if a.json:
        open(os.path.join(P, a.json) if not os.path.isabs(a.json) else a.json, "wb").write(
            (json.dumps(res, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    ok = res["all_identical"] and (not a.selftest or all(v for k, v in res["selftest"].items() if k != "perturbed_file"))
    print("ALL_OK" if ok else "NOT_OK")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
