#!/usr/bin/env python3
"""Regenerate the paper's number files, tables and figures from the saved records and compare each regenerated file
byte for byte with the one in this deposit, then run the simulators' CPU checks.

    python -B reproduce_all.py                  everything (the slow CPU checks take about half an hour)
    python -B reproduce_all.py --fast           regeneration + the quick checks only
    python -B reproduce_all.py --list           print the steps
    python -B reproduce_all.py --only analyze   run the steps whose id contains this text (repeatable)
    python -B reproduce_all.py --json out.json  where to write the result (default _repro/REPRODUCE.json)

How it works. The script keeps the starting bytes of every number file, table, figure and result record, runs each step in
order (generators overwrite files in place), and at the end compares every file a step rewrote with its starting bytes. A
"regen" step must exit 0 (and print its token, if one is required); a "check" step is a self-test that writes only under
_repro/. A regenerated file must be byte-identical, with two narrow, explicit exceptions (figure PDFs: the /CreationDate
stamp; figure PNGs: compressed bytes when the decoded pixels are identical), a table KNOWN_DIFFERENCES (empty since version 9)
and, since v1.5, one numeric comparison policy for one file (NUMERIC_POLICY below: the AIHWKIT comparison, which re-simulates
long float32 pulse sequences on the CPU). Nothing is trained: the long runs of the paper are NOT repeated here; their records are the
inputs. Run it from a COPY of the deposit if you want the original bytes kept.

Reference environment (byte identity of every file is guaranteed only here): Python 3.13.15 on Windows 11 (x86-64, Intel Xeon
W-2123), torch 2.7.1+cu126 with CUDA hidden (CPU execution), NumPy 2.5.2, matplotlib 3.9.2, Pillow 13.0.0. Elsewhere (Python 3.12+;
numpy 2.5.2 requires it) the same rules apply, and AIHWKIT-COMPARE.json is compared under NUMERIC_POLICY. The training ran in the
pods' own environment, see ENVIRONMENT.md. numpy and torch (CPU is enough; the checks run with CUDA hidden
(CUDA_VISIBLE_DEVICES=-1)) and matplotlib 3.9.2 for the figure steps (the paper's figures were drawn with matplotlib 3.9.2);
README.md, sections "Install (CPU)" and "Reference environment", and requirements.txt give the commands and the versions.
The MNIST/CIFAR/enwik8 files from fetch_data.py are needed by the checks that load data (python fetch_data.py).

    python -B reproduce_all.py --policy-selftest    the numeric policy's self-test: another environment's output passes; a flipped
                                                    boolean, a discrepancy pushed past its line, a renamed key, a changed printed
                                                    value, string or exact field each fail (prints POLICY_SELFTEST_OK)
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

# (id, cwd relative to ROOT, argv after python, kind, required output token, slow)
STEPS = [
    # ---- guard: nothing below may touch a GPU (the runners pick CUDA when it is visible) ----
    ("cpu_only_guard", ".", ["-B", "-c", "import torch,sys;print('CPU_ONLY' if not torch.cuda.is_available() else 'GPU_VISIBLE');sys.exit(1 if torch.cuda.is_available() else 0)"], "check", "CPU_ONLY", False),
    # ---- numbers, tables, figures (regenerated from the records; compared byte for byte) ----
    ("energy_system", "paper", ["-B", "energy/energy_system.py", "--runs", "records/runs/e3", "--out", "records/ENERGY-SYSTEM.json"], "regen", None, False),
    ("analyze", "paper", ["-I", "analyze.py"], "regen", None, False),
    ("make_figures", "paper", ["-B", "make_figures.py", "--records", "records", "--out", "tex/figs"], "regen", None, False),
    ("compare_curves", "paper", ["-B", "revision/compare_curves.py", "records/revision/AIHWKIT-CURVES.json", "records/revision/AIHWKIT-COMPARE.json"], "regen", None, False),
    ("analyze_d1", "paper", ["-B", "revision/analyze_d1.py"], "regen", None, False),
    ("energy_rev", "paper", ["-B", "energy/energy_rev.py", "--runs", "records/revision/runs/e3", "--out", "records/revision/ENERGY-REVISION.json"], "regen", None, False),
    ("analyze_rev", "paper", ["-B", "revision/analyze_rev.py"], "regen", None, False),
    ("derive_rev_spec_p", "paper", ["-B", "revision10/derive_rev_spec_p.py"], "regen", None, False),   # Table 12's file (v1.1)
    ("make_figures_rev", "paper", ["-B", "revision/make_figures_rev.py", "--results", "records/revision/RESULTS-REVISION.json", "--out", "tex/figs"], "regen", None, False),
    ("make_fig_arch", "paper", ["-B", "revision14/make_fig_arch.py", "--out", "tex/figs"], "regen", None, False),   # Figure 1 (v1.4; v1.5: the selected settings)
    ("analyze_rev2", "paper", ["-B", "revision2/analyze_rev2.py"], "regen", None, False),
    ("analyze_rev3", "paper", ["-B", "revision3/analyze_rev3.py"], "regen", None, False),
    ("analyze_rev4", "paper", ["-B", "revision4/analyze_rev4.py"], "regen", None, False),
    ("make_abstract_v5", "paper", ["-B", "revision4/make_abstract_v5.py"], "regen", None, False),
    ("rebuild_draw_tables", "paper", ["-B", "revision4/rebuild_draw_tables.py", "--draws", "draws/rev3"], "regen", "ALL_OK", False),
    # ---- self-tests (each must be shown to fail on broken code; they write only under _repro/) ----
    ("selftest_analyze_rev4", "paper", ["-B", "revision4/analyze_rev4.py", "--selftest"], "check", None, False),
    ("selftest_rebuild_draw_tables", "paper", ["-B", "revision4/rebuild_draw_tables.py", "--draws", "draws/rev3", "--selftest"], "check", "ALL_OK", False),
    ("fetch_data_selftest", ".", ["-B", "fetch_data.py", "--selftest"], "check", "SELFTEST_OK", False),
    ("bench_parts", "bench", ["-B", "analyze_bench.py", "--parts"], "check", None, False),
    ("bench_selftest", "bench", ["-B", "analyze_bench.py", "--selftest"], "check", None, False),
    # ---- v1.1 (review 8): Figure 3 draws every mean and interval of its results; the ideal reset of a partial column selection ----
    ("check_fig_main", "paper", ["-B", "revision10/check_fig_main.py", "--selftest"], "check", "FIG_MAIN_OK", False),
    ("test_ideal_reset_cols", "paper/sim", ["-B", "test_ideal_reset_cols.py", "--out", "../../_repro/TESTS-IDEAL-RESET-COLS.json"], "check", "ALL_OK", False),
    # ---- v1.2 (review 9): the width study's Welch interval at the Welch-Satterthwaite df itself ----
    ("test_welch_df", "paper", ["-B", "revision11/test_welch_df.py", "--out", "../_repro/TESTS-WELCH-DF.json"], "check", "ALL_OK", False),
    # ---- v1.4 (review 11): Figure 1 says what the simulator does (device and digital state, ideal reads, pulse targets) ----
    ("check_fig_arch", "paper", ["-B", "revision14/check_fig_arch.py", "--selftest"], "check", "FIG_ARCH_OK", False),
    # ---- v1.5 (review 12): the numeric comparison policy of AIHWKIT-COMPARE.json must reject meaningful perturbations ----
    ("policy_selftest", ".", ["-B", "reproduce_all.py", "--policy-selftest"], "check", "POLICY_SELFTEST_OK", False),
    # ---- the simulators' checks (CPU; CUDA hidden) ----
    ("test_memsim_laneME", "sim", ["-B", "test_memsim.py", "--out", "../_repro/TESTS.json"], "check", "ALL_OK", True),
    ("test_paper", "paper/sim", ["-B", "test_paper.py", "--out", "../../_repro/TESTS-PAPER.json"], "check", "ALL_OK", True),
    ("test_rev", "paper/sim", ["-B", "test_rev.py", "--out", "../../_repro/TESTS-REV.json"], "check", "ALL_OK", True),
    ("test_rev2", "paper/sim", ["-B", "test_rev2.py", "--out", "../../_repro/TESTS-REV2.json"], "check", "ALL_OK", True),
    ("test_rev3", "paper/sim", ["-B", "test_rev3.py", "--out", "../../_repro/TESTS-REV3.json"], "check", "ALL_OK", True),
]



# A regenerated file must be byte-identical to the deposit's copy, with three explicit, narrow exceptions:
#   * a figure PDF may differ ONLY in matplotlib's /CreationDate stamp (the paper's figures carry the date they were drawn);
#   * a figure PNG may differ in its compressed bytes (zlib build) when the decoded RGBA pixels are identical;
#   * KNOWN_DIFFERENCES: files whose regenerated text is known to differ from the paper's by exactly the listed lines.
KNOWN_DIFFERENCES = {
    # None since version 9 (the version-8 numbers_rev.tex said \\RVnDev = 6 while the generator writes 8; fixed, and
    # paper/revision8/check_numbers_fresh.py now fails on any stale numbers*.tex).
}
PDF_DATE = None

# ---- v1.5 (review 12, finding A): one numeric comparison policy, for one file ----
# paper/revision/compare_curves.py re-simulates the two AIHWKIT presets' pulse schedules (9,500 and 56,000 float32 pulses on 500
# devices) on the CPU and summarises them. The float32 rounding of those long sequences depends on the CPU kernels torch dispatches
# to: under Python 3.12 with torch 2.7.1+cpu, review 12 found 26 float fields different (largest change 5.69e-6 in weight units,
# 4.70e-4 in tolerance units) and the author's WSL run (Python 3.12.3, torch 2.7.1+cpu, NumPy 2.5.2) the same 26 fields (largest
# 4.26e-6 and 3.85e-4); every boolean, string and integer and every printed value were unchanged. This file alone is therefore
# compared field by field:
#   * the same JSON structure: the same keys at every level, the same list lengths and the same value types;
#   * every string (schema, AIHWKIT version), integer (device count), boolean (each `ok`, each `mapping_accepted`) exactly equal;
#   * floats by field, within the absolute tolerances below; any float not named here (the AIHWKIT side of `extremes`, computed
#     from the stored AIHWKIT record alone) exactly equal;
#   * the values the manuscript prints from this file (revision/analyze_rev.py: the largest mean differences to 4 and 3 decimals,
#     the verdict and "accepted") identical when computed from either file.
# Why these tolerances: each is about ten times the largest change seen in another environment and at most a tenth of the margin
# it could erode. Weight units: 5e-5 is a tenth of the smallest floor of the comparison's own tolerance, 2 dw_min = 5.6e-4 (MO-ECRAM).
# Tolerance units: 5e-3 is half a percent of the acceptance line 1.0; the largest accepted value, 0.642, is 0.358 below it. The
# spread ratio: 1e-4, against at least 0.067 between any stored ratio and the edges of its acceptance band [0.8, 1.25].
NUMERIC_POLICY_FILE = "paper/records/revision/AIHWKIT-COMPARE.json"
NUMERIC_TOL = {"ours": 5e-5, "max_abs_mean_diff": 5e-5, "worst_mean_diff_in_tolerance_units": 5e-3, "median_sd_ratio": 1e-4}
POLICY_REFERENCE_OTHER_ENV = "paper/records/revision14/AIHWKIT-COMPARE-py312.json"   # the author's Python 3.12.3 output (positive control)


def aihwkit_printed(d):
    """What the manuscript prints from AIHWKIT-COMPARE.json, formatted as revision/analyze_rev.py formats it."""
    P_ = d["presets"]
    mx = lambda cls, mp: max(P_[cls][f"{nv}__{mp}"]["max_abs_mean_diff"] for nv in ("noise_free", "noisy"))
    return dict(RVaihwVersion=d["aihwkit"], RVaihwAccepted=all(v["mapping_accepted"] for v in P_.values()),
                RVaihwLiMaxDiff=f"{mx('EcRamPresetDevice', 'aihwkit_mode'):.4f}",
                RVaihwMoMaxDiff=f"{mx('EcRamMOPresetDevice', 'aihwkit_mode'):.4f}",
                RVaihwLiOldMaxDiff=f"{mx('EcRamPresetDevice', 'papermap'):.3f}",
                RVaihwMoOldMaxDiff=f"{mx('EcRamMOPresetDevice', 'papermap'):.3f}",
                not_accepted=sorted(k for k, v in P_.items() if not v["mapping_accepted"]))


def numeric_policy(old_bytes, new_bytes):
    """(ok, detail) for AIHWKIT-COMPARE.json under NUMERIC_POLICY (see above)."""
    try:
        a, b = json.loads(old_bytes.decode("utf-8")), json.loads(new_bytes.decode("utf-8"))
    except Exception as e:
        return False, f"not JSON: {e}"
    bad, nf, worst = [], [0], {}

    def walk(x, y, path):
        if type(x) is not type(y):
            bad.append(f"{path}: type {type(x).__name__} -> {type(y).__name__}")
        elif isinstance(x, dict):
            if set(x) != set(y):
                bad.append(f"{path}: keys differ ({sorted(set(x) ^ set(y))})")
            for k in sorted(set(x) & set(y)):
                walk(x[k], y[k], f"{path}/{k}")
        elif isinstance(x, list):
            if len(x) != len(y):
                bad.append(f"{path}: list length {len(x)} -> {len(y)}")
            for i, (u, v) in enumerate(zip(x, y)):
                walk(u, v, f"{path}[{i}]")
        elif isinstance(x, float):
            if x != y:
                key = path.rsplit("/", 1)[-1]
                tol = NUMERIC_TOL.get(key)
                d = abs(x - y)
                if tol is None or not d <= tol:
                    bad.append(f"{path}: {x!r} -> {y!r} (|diff| {d:.3g}, allowed {tol if tol is not None else 'none: exact field'})")
                else:
                    nf[0] += 1
                    worst[key] = max(worst.get(key, 0.0), d)
        elif x != y:
            bad.append(f"{path}: {x!r} -> {y!r} (must be equal)")

    walk(a, b, "")
    if not bad:
        try:
            pa, pb = aihwkit_printed(a), aihwkit_printed(b)
            bad += [f"printed {k}: {pa[k]!r} -> {pb[k]!r}" for k in pa if pa[k] != pb[k]]
        except Exception as e:
            bad.append(f"printed values not computable: {e}")
    if bad:
        return False, "outside the numeric policy: " + "; ".join(bad[:6]) + (f" (+{len(bad) - 6} more)" if len(bad) > 6 else "")
    return True, (f"{nf[0]} float fields differ within the numeric policy (largest |diff|: "
                  + ", ".join(f"{k} {v:.3g}" for k, v in sorted(worst.items()))
                  + "); structure, strings, integers, every boolean and every printed value equal")


def printed_flip_value(d):
    """(key, new value) that moves the Li-ECRAM printed 4-decimal value (the maximum over the noise-free and noisy fields, `.4f`)
    to the other side of its nearest rounding boundary while changing the stored float by at most the weight tolerance. It is
    computed from d, so it holds for any starting value the policy permits (review 13: a fixed +4e-5 does not)."""
    P_ = d["presets"]["EcRamPresetDevice"]
    key = max(("noise_free__aihwkit_mode", "noisy__aihwkit_mode"), key=lambda k: P_[k]["max_abs_mean_diff"])
    x = P_[key]["max_abs_mean_diff"]
    n = round(x * 1e4)                                   # printed integer, in units of 1e-4
    cands = [(n + 0.5) * 1e-4 + 1e-8, (n - 0.5) * 1e-4 - 1e-8]    # just past either neighbouring boundary
    new = min(cands, key=lambda c: abs(c - x))
    assert abs(new - x) <= NUMERIC_TOL["max_abs_mean_diff"] and f"{new:.4f}" != f"{x:.4f}", (x, new)
    return key, new


def policy_selftest(ref_b=None, quiet=False):
    """The policy passes the reference and another environment's output, and fails every meaningful perturbation.
    ref_b: optional starting file (bytes) in place of the deposited one, for testing other starting values."""
    import copy
    if ref_b is None:
        ref_b = open(os.path.join(ROOT, NUMERIC_POLICY_FILE), "rb").read()
    ref = json.loads(ref_b.decode("utf-8"))
    enc = lambda d: (json.dumps(d, indent=1, sort_keys=True) + "\n").encode("utf-8")

    def mutated(f):
        d = copy.deepcopy(ref)
        f(d)
        return enc(d)
    li = lambda d: d["presets"]["EcRamPresetDevice"]["noisy__aihwkit_mode"]
    cases = [("reference itself", ref_b, True),
             ("another environment's output (Python 3.12.3, torch 2.7.1+cpu; 26 floats differ)",
              open(os.path.join(ROOT, POLICY_REFERENCE_OTHER_ENV), "rb").read(), True),
             ("a float inside its tolerance that does not change a printed value",
              mutated(lambda d: li(d).__setitem__("worst_mean_diff_in_tolerance_units", li(d)["worst_mean_diff_in_tolerance_units"] + 1e-3)), True),
             ("an acceptance boolean flipped (Li-ECRAM noisy ok)", mutated(lambda d: li(d).__setitem__("ok", False)), False),
             ("mapping_accepted flipped (MO-ECRAM)",
              mutated(lambda d: d["presets"]["EcRamMOPresetDevice"].__setitem__("mapping_accepted", False)), False),
             ("a discrepancy pushed past its line (Li-ECRAM noisy: 0.642 -> 1.05 tolerance units, ok left true)",
              mutated(lambda d: li(d).__setitem__("worst_mean_diff_in_tolerance_units", 1.05)), False),
             ("a key renamed (median_sd_ratio)", mutated(lambda d: li(d).__setitem__("median_sd_ratio_", li(d).pop("median_sd_ratio"))), False),
             ("a key removed (extremes/dev_min)", mutated(lambda d: li(d)["extremes"].pop("dev_min")), False),
             ("a change within the weight tolerance that changes a printed value (Li-ECRAM, across the nearest rounding boundary)",
              mutated(lambda d: d["presets"]["EcRamPresetDevice"][printed_flip_value(d)[0]].__setitem__("max_abs_mean_diff", printed_flip_value(d)[1])), False),
             ("an exact-only float changed (the AIHWKIT side of an extreme)",
              mutated(lambda d: li(d)["extremes"]["dev_max"].__setitem__("aihwkit", li(d)["extremes"]["dev_max"]["aihwkit"] + 1e-12)), False),
             ("a metadata string changed (AIHWKIT version)", mutated(lambda d: d.__setitem__("aihwkit", "1.1.1")), False),
             ("an integer turned into a float (n_devices)", mutated(lambda d: d.__setitem__("n_devices", float(d["n_devices"]))), False),
             ("a spread ratio moved by 1e-3", mutated(lambda d: li(d).__setitem__("median_sd_ratio", li(d)["median_sd_ratio"] + 1e-3)), False),
             ("not JSON", ref_b[:-40], False)]
    ok_all = True
    for name, new, want in cases:
        ok, detail = numeric_policy(ref_b, new)
        good = ok == want
        ok_all &= good
        if not quiet:
            print(f"{'ok  ' if good else 'BAD '} {'passes' if ok else 'fails '} (want {'pass' if want else 'fail'}) {name}: {detail[:160]}")
    if not quiet:
        print("POLICY_SELFTEST_OK" if ok_all else "POLICY_SELFTEST_FAILED")
    return 0 if ok_all else 1


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def snapshot():
    snap = {}
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in (".git", "data", "_repro", "__pycache__", ".venv")]
        for n in fn:
            p = os.path.join(dp, n)
            st = os.stat(p)
            snap[os.path.relpath(p, ROOT).replace(os.sep, "/")] = (st.st_mtime_ns, st.st_size)
    return snap


def pdf_norm(b):
    import re
    return re.sub(rb"/CreationDate \(D:[0-9]{14}Z\)", b"/CreationDate (D:NORMALISED)", b)


def png_pixels(b):
    from PIL import Image
    import io
    im = Image.open(io.BytesIO(b)).convert("RGBA")
    return im.size, im.tobytes()


def compare(rel, old_bytes, new_bytes):
    """Returns (status, detail). status in identical | normalised | known_difference | within_policy | DIFFERS."""
    if old_bytes == new_bytes:
        return "identical", ""
    if rel == NUMERIC_POLICY_FILE:
        ok, detail = numeric_policy(old_bytes, new_bytes)
        return ("within_policy" if ok else "DIFFERS"), detail
    if rel in KNOWN_DIFFERENCES:
        a = [l for l in old_bytes.split(b"\n")]
        b = [l for l in new_bytes.split(b"\n")]
        if len(a) == len(b):
            ch = [(x, y) for x, y in zip(a, b) if x != y]
            want_old, want_new = KNOWN_DIFFERENCES[rel]
            if [x for x, _ in ch] == want_old and [y for _, y in ch] == want_new:
                return "known_difference", f"only {want_old[0].decode()} -> {want_new[0].decode()}"
        return "DIFFERS", "differs beyond the documented difference"
    if rel.endswith(".pdf") and pdf_norm(old_bytes) == pdf_norm(new_bytes):
        return "normalised", "figure PDF identical except the /CreationDate stamp"
    if rel.endswith(".png"):
        try:
            if png_pixels(old_bytes) == png_pixels(new_bytes):
                return "normalised", "figure PNG: same decoded RGBA pixels; compressed bytes differ"
        except Exception as e:  # PIL missing
            return "DIFFERS", f"png pixel comparison unavailable: {e}"
    return "DIFFERS", ""


def check_sums():
    bad, n = [], 0
    with open(os.path.join(ROOT, "SHA256SUMS"), "rb") as f:
        for line in f.read().decode("utf-8").splitlines():
            h, name = line.split("  ", 1)
            n += 1
            p = os.path.join(ROOT, name)
            if not os.path.isfile(p) or sha256(p) != h:
                bad.append(name)
    extra = []
    listed = set()
    with open(os.path.join(ROOT, "SHA256SUMS"), "rb") as f:
        listed = {l.split("  ", 1)[1] for l in f.read().decode("utf-8").splitlines()}
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in (".git", "data", "_repro", "__pycache__", ".venv")]
        for x in fn:
            r = os.path.relpath(os.path.join(dp, x), ROOT).replace(os.sep, "/")
            if r not in listed and r != "SHA256SUMS":
                extra.append(r)
    for b in bad:
        print("MISMATCH", b)
    for e in extra:
        print("NOT LISTED", e)
    print(f"SUMS_OK {n} files" if not bad and not extra else f"SUMS_FAILED mismatches={len(bad)} unlisted={len(extra)}")
    return 0 if not bad and not extra else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--sums", action="store_true", help="only check SHA256SUMS against the files (run this before the generators)")
    ap.add_argument("--only", action="append")
    ap.add_argument("--json", default=os.path.join(ROOT, "_repro", "REPRODUCE.json"))
    ap.add_argument("--policy-selftest", action="store_true", help="only run the numeric policy's self-test")
    a = ap.parse_args()
    if a.sums:
        return check_sums()
    if a.policy_selftest:
        return policy_selftest()
    steps = [s for s in STEPS if (not a.only or any(t in s[0] for t in a.only)) and not (a.fast and s[5])]
    if a.list:
        for s in steps:
            print(f"{s[0]:32s} cwd={s[1]:10s} python {' '.join(s[2])}  [{s[3]}{', slow' if s[5] else ''}]")
        return 0
    os.makedirs(os.path.join(ROOT, "_repro"), exist_ok=True)
    start = snapshot()
    # keep the starting bytes of every file the generators may rewrite (all text and figure outputs are small)
    orig = {}
    for rel in start:
        if rel.startswith(("paper/tex/", "paper/records/", "records/", "paper/build/arxiv-abstract.txt")) and start[rel][1] < 20_000_000:
            with open(os.path.join(ROOT, rel), "rb") as f:
                orig[rel] = f.read()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", CUDA_VISIBLE_DEVICES="-1", OPENBLAS_NUM_THREADS="2",
               OMP_NUM_THREADS="2", MKL_NUM_THREADS="2",
               SOURCE_DATE_EPOCH="0")  # makes matplotlib write the UTC form of /CreationDate, as the paper's figures have
    results = []
    written_by = {}
    ok_all = True
    for sid, cwd, argv, kind, token, slow in steps:
        before = snapshot()
        t0 = time.time()
        p = subprocess.run([PY] + argv, cwd=os.path.join(ROOT, cwd), env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        dt = time.time() - t0
        out = (p.stdout or "") + (p.stderr or "")
        with open(os.path.join(ROOT, "_repro", sid + ".log"), "wb") as f:
            f.write(out.encode("utf-8"))
        after = snapshot()
        wrote = sorted(r for r in after if r not in before or after[r] != before[r])
        for r in wrote:
            written_by[r] = sid
        ok = p.returncode == 0 and (token is None or token in out) and (kind == "regen" or not wrote)
        ok_all &= ok
        results.append(dict(id=sid, cwd=cwd, argv=argv, kind=kind, returncode=p.returncode, token=token,
                            token_found=(token in out) if token else None, seconds=round(dt, 1), ok=ok,
                            rewrote=wrote, log=f"_repro/{sid}.log"))
        print(f"{'OK  ' if ok else 'FAIL'} {sid:32s} rc={p.returncode} {dt:7.1f}s rewrote={len(wrote)}", flush=True)
    # end-state comparison of every file any step rewrote with its starting bytes
    files = {}
    for rel, sid in sorted(written_by.items()):
        if rel not in orig:
            files[rel] = dict(status="DIFFERS", detail="new file not in the deposit", last_step=sid)
            continue
        with open(os.path.join(ROOT, rel), "rb") as f:
            new = f.read()
        st, detail = compare(rel, orig[rel], new)
        files[rel] = dict(status=st, detail=detail, last_step=sid)
    bad = [r for r, v in files.items() if v["status"] == "DIFFERS"]
    ok_all = ok_all and not bad
    counts = {}
    for v in files.values():
        counts[v["status"]] = counts.get(v["status"], 0) + 1
    rec = dict(python=sys.version, platform=sys.platform, all_ok=ok_all, file_status_counts=counts, files=files, steps=results,
               numeric_policy=dict(file=NUMERIC_POLICY_FILE, absolute_tolerances=NUMERIC_TOL,
                                   exact="structure, strings, integers, booleans, every other float, the printed values"))
    os.makedirs(os.path.dirname(a.json), exist_ok=True)
    with open(a.json, "wb") as f:
        f.write((json.dumps(rec, indent=1) + "\n").encode("utf-8"))
    print("files rewritten:", counts, "| not matching:", bad)
    print("REPRODUCE_ALL_OK" if ok_all else "REPRODUCE_FAILED")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
