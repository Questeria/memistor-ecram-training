"""ME-REVISE-3 checks of the paired probe analysis (run_rev3.py), PLAN-REVISION-3.md section 1. Each check is also run against
a planted fault and must FAIL there.

    python -B test_rev3.py [--out ../records/revision3/TESTS-REV3.json]      (CPU; MNIST at 1 % scale for the runner check)
"""
import argparse
import json
import math
import os
import sys
import tempfile

os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # CPU ("" still shows a GPU on this desk)
import torch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pulse_seq_rev2 as PS  # noqa: E402
import run_rev2 as RR  # noqa: E402
import run_rev3 as R3  # noqa: E402
import test_rev2 as T2  # noqa: E402


def _draws(c2c, R=16, M=6, shape=(10, 14), bias=0.0, fresh=False, seed=3):
    over = dict(n_states=40.0) if c2c is None else dict(c2c=c2c, n_states=40.0)
    t = T2.tile(T2.spec("protonic_onen2022", **over), shape=shape)
    P = PS.dev_params(t)
    g = torch.Generator().manual_seed(seed)
    px = ((torch.rand((M, shape[1]), generator=g) - 0.5) * 1.6).clamp(-1, 1)
    pd = ((torch.rand((M, shape[0]), generator=g) - 0.5) * 1.6).clamp(-1, 1)
    Q = -(pd.t() @ px)
    seq, slot = [], []
    for _ in range(R):
        fire = []
        seq.append((PS.seq_apply(t.u, P, px, pd, 31, g, keep_fire=fire, chunk=3) - t.u) / t.k_nom * (1 + bias))
        slot.append((PS.slot_apply(t.u, P, px, pd, 31, g, fire=None if fresh else fire, chunk=3) - t.u) / t.k_nom)
    return torch.stack(seq), torch.stack(slot), Q


def c1_paired_noise_free(fresh=False):
    """Noise-free devices: seq equals slot draw by draw, so the paired floor and excess are ~0 while the independent floor
    is not. Fault: slot draws fresh firings (no pairing): the paired floor must then be large."""
    a, b, Q = _draws(0.0, fresh=fresh)
    p = R3.paired(a, b, Q, 0, 0)
    ok = p["floor_paired"] < 0.01 * p["floor_independent"] and p["excess_paired"] < 0.01 and p["floor_independent"] > 0.02
    return dict(ok=ok, **{k: p[k] for k in ("floor_paired", "floor_independent", "excess_paired", "rel_mean_err")})


def c2_bias_found(bias=0.10):
    """With write noise, a planted 10 % bias of seq is found by the paired excess (>= 0.08) where the independent floor hides
    it (excess 0); the unbiased seq shows paired excess < 0.05 and its bootstrap bound is reported. Fault: bias 0 must not
    pass the 'found' half (so the check measures the bias, not noise)."""
    a, b, Q = _draws(None, R=16, M=2, bias=bias)
    p = R3.paired(a, b, Q, 200, 1)
    a0, b0, Q0 = _draws(None, R=16, M=2, bias=0.0)
    p0 = R3.paired(a0, b0, Q0, 200, 1)
    ok = p["excess_paired"] >= 0.08 and p["excess_independent"] == 0.0 and p0["excess_paired"] < 0.05
    return dict(ok=ok, biased={k: p[k] for k in ("excess_paired", "excess_independent", "excess_paired_p95", "rel_mean_err",
                                                    "floor_paired", "floor_independent")},
                unbiased={k: p0[k] for k in ("excess_paired", "excess_paired_p95", "gain_ratio_minus1_p025",
                                             "gain_ratio_minus1_p975")})


def _shared_line(R=40000, n=128, hetero=False, seed=11):
    g = torch.Generator().manual_seed(seed)
    s = torch.tensor([1.0 if j % 2 == 0 else -1.0 for j in range(n)], dtype=torch.float64)
    row = (torch.rand(R, 1, 1, generator=g, dtype=torch.float64) < 0.5).double()
    col = (torch.rand(R, 1, n, generator=g, dtype=torch.float64) < 0.5).double()
    x = row * col * s.view(1, 1, n)
    if hetero:
        x = x * torch.tensor([10.0] + [0.1] * (n - 1), dtype=torch.float64).view(1, 1, n)
    return x, s.view(1, n)


def c3_dependence():
    """Review 3's example (one shared line, p = 0.5, balanced signs): per-pair |r| = 1/3. The RMS and the sign-aligned mean are
    1/3 within 0.01 on balanced AND heterogeneous-scale cells, while the v3 pooled signed statistic is -1/381 (balanced) and
    the plain signed mean is near -1/381. Also the exact Gram computation equals brute-force corrcoef on a small case.
    Fault: pooled normalisation instead of per-pair (CFG3 fault_pooled_corr) must fail."""
    x, s = _shared_line()
    d = R3.dep(x, s, 2)
    xh, _ = _shared_line(hetero=True)
    dh = R3.dep(xh, s, 2)
    off = RR._offcorr(x - x.mean(0), 2)
    g = torch.Generator().manual_seed(5)
    small = torch.randn(9, 3, 7, generator=g, dtype=torch.float64) + torch.randn(9, 3, 1, generator=g, dtype=torch.float64)
    sg = torch.sign(torch.randn(3, 7, generator=g, dtype=torch.float64))
    ds = R3.dep(small, sg, 2)
    bf_sq, bf_al, npairs = 0.0, 0.0, 0
    for i in range(3):
        C = torch.corrcoef(small[:, i, :].t())
        for j in range(7):
            for k in range(7):
                if j != k:
                    bf_sq += float(C[j, k]) ** 2
                    bf_al += float(C[j, k] * sg[i, j] * sg[i, k])
                    npairs += 1
    exact = abs(ds["mean_sq"] - bf_sq / npairs) < 1e-9 and abs(ds["mean_aligned"] - bf_al / npairs) < 1e-9
    ok = (abs(d["rms"] - 1 / 3) < 0.01 and abs(dh["rms"] - 1 / 3) < 0.01 and abs(d["mean_aligned"] - 1 / 3) < 0.01
          and abs(off + 1 / 381) < 0.005 and abs(d["mean_signed"] + 1 / 381) < 0.005 and exact)
    return dict(ok=ok, rms=d["rms"], rms_hetero=dh["rms"], aligned=d["mean_aligned"], signed=d["mean_signed"],
                v3_pooled_signed=off, gram_equals_bruteforce=exact)


def c4_runner(tmp):
    """run_rev3 with probes reproduces run_rev2 without probes (metric, pulse counts) and writes the paired and dependence
    fields and the draws. Fault: the probe draws from the run's generator (run_rev2's planted fault)."""
    out_a = os.path.join(tmp, "a3.json")
    args = ["--probe-steps", "2", "--probe-layers", "0,2", "--probe-draws", "3", "--probe-out", os.path.join(tmp, "p3.json"),
            "--probe-boot", "20", "--draws-dir", os.path.join(tmp, "draws"), "--tag", "t3",
            "--task", "mnist", "--algo", "cttv2", "--lr", "0.003", "--seed", "0", "--scale", "0.01",
            "--spec", json.dumps(dict(json.load(open(T2.CAT, "rb"))["entries"]["ecram_li_tang2018"]["spec"],
                                      name="ecram_li_tang2018")),
            "--ucfg", json.dumps(dict(tt_lambda=0.1, tt_lr_ratio=10.0, tt_period=16, tt_reset="pulse", tt_rho=0.05)),
            "--out", out_a]
    R3.main(args)
    a = json.load(open(out_a, "rb"))
    b = T2._run([], os.path.join(tmp, "b3.json"))
    same = a["metric"] == b["metric"] and [l["pulses"] for l in a["layers"]] == [l["pulses"] for l in b["layers"]]
    pr = json.load(open(os.path.join(tmp, "p3.json"), "rb"))["probes"]
    has = bool(pr) and all("paired" in p["seq"] and "dep" in p["slot"] and "draws_sha256" in p for p in pr)
    return dict(ok=same and len(pr) == 2 and has and a.get("schema_revision3") is not None, same=same, probes=len(pr),
                fields=has, seq0=({k: pr[0]["seq"]["paired"][k] for k in ("floor_paired", "floor_independent",
                                                                           "excess_paired_p95")} if has else None))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "records", "revision3", "TESTS-REV3.json"))
    a = ap.parse_args()
    torch.set_num_threads(2)
    res, faults = {}, {}
    with tempfile.TemporaryDirectory() as tmp:
        res["c1_paired_noise_free"] = c1_paired_noise_free()
        res["c2_bias_found"] = c2_bias_found()
        res["c3_dependence"] = c3_dependence()
        res["c4_runner"] = c4_runner(tmp)
        faults["c1_slot_fresh_firings"] = c1_paired_noise_free(fresh=True)
        faults["c2_no_bias_planted"] = c2_bias_found(bias=0.0)
        R3.CFG3["fault_pooled_corr"] = True
        try:
            faults["c3_pooled_normalisation"] = c3_dependence()
        finally:
            R3.CFG3["fault_pooled_corr"] = False
        RR.CFG["fault_probe_shared_gen"] = True
        try:
            faults["c4_probe_shares_the_run_generator"] = c4_runner(tmp)
        finally:
            RR.CFG["fault_probe_shared_gen"] = False
    all_ok = all(v["ok"] for v in res.values())
    caught = all(not v["ok"] for v in faults.values())
    out = dict(schema="altone.x1000.me-revision3.tests.v1", checks=res, faults=faults, all_ok=all_ok,
               all_faults_caught=caught, torch=torch.__version__)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "wb") as f:
        f.write((json.dumps(out, indent=1, default=str) + "\n").encode("utf-8"))
    for k, v in list(res.items()) + list(faults.items()):
        print(k, "ok" if v["ok"] else "FAIL", {kk: vv for kk, vv in v.items() if kk != "ok"})
    print("ALL_OK" if all_ok and caught else "NOT_OK", "checks", all_ok, "faults caught", caught)


if __name__ == "__main__":
    main()
