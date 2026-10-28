"""REVISION checks (lane ME-REVISE 2026-10-26). Each check runs on the repaired code and must PASS, and is shown to FAIL on
the old behaviour or a planted fault (the pattern of test_paper.py). CPU only.

    python -B test_rev.py --out ../records/revision/TESTS-REV.json
  c_legacy_replay     run_rev.py --rng legacy with the ideal reset replays run.py bit for bit (MNIST c-TTv2, AGAD; LM TTv2)
                      [fails: --rng split]
  c_matched_controls  run_rev.py --rng split: every arm of a seed (FP-SGD, device SGD/TTv2/c-TTv2/AGAD, aihwkit-mapped,
                      digital TTv2, Adam) has the same logical-init and data-order sha256 (MNIST and LM) [fails: --rng legacy]
  c_population        one device gets the same tile population whatever the algorithm [fails: legacy streams]
  c_reset_physical    'alt' lands where BL alternating pairs take the device; 'pulse' lands within one step of the read
                      zero; both charge exactly the pulses applied [fails: the ideal reset]
  c_aihwkit_formula   the aihwkit-mode tile follows the LinearStepDevice recurrence over 1500 up and 3000 down pulses
                      (bounds and bound-scaled slopes) [fails: the old field-copy mapping]
  c_clip_stats        pulse_counts reports clipping and the lost update fraction [fails: the old pulse_counts]
  c_h_forget          published-style TTv2 forgets a fired buffer element; the default keeps the remainder [fails: swapped]
  c_recenter_sp       re-centred asymmetric device: symmetry point 0 and the full range reachable [fails: not re-centred]
"""
import argparse
import importlib
import json
import math
import os
import subprocess
import sys
import tempfile

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import memsim as OLD  # noqa: E402
import memsim_rev as R  # noqa: E402
import tasks_rev as TR  # noqa: E402

DEV = torch.device("cpu")
PY = sys.executable
PROTONIC = dict(n_states=1000, asym=0.05, gamma_up=0.2, gamma_dn=0.2, c2c=0.3, d2d=0.1, bound_d2d=0.05, ref_err=0.02)
LI_AIHW = dict(bounds_model="aihwkit", n_states=1000.0, asym=0.0, asym_d2d=0.02, d2d=0.1, u_lo=-0.8276, u_hi=1.1724,
               bound_d2d=0.05, gamma_up=0.1153, gamma_dn=0.5085, gamma_up_dtod=0.05, gamma_dn_dtod=0.05, c2c=0.3,
               ref_err=0.02)
CTT = dict(tt_lambda=0.1, tt_lr_ratio=10.0, tt_period=16, tt_rho=0.2)
ENV = dict(os.environ, CUDA_VISIBLE_DEVICES="-1", OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
TMP = tempfile.mkdtemp(prefix="me-rev-tests-")


def runp(script, args, name):
    out = os.path.join(TMP, name + ".json")
    if not os.path.exists(out):
        subprocess.run([PY, "-B", os.path.join(HERE, script)] + args + ["--out", out], check=True, env=ENV,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return json.load(open(out, "rb"))


def _cfg(task, algo, spec, ucfg, arm="device", lr="0.003", seed="1"):
    scale = "0.01" if task == "mnist" else "0.002"
    a = ["--task", task, "--arm", arm, "--algo", algo, "--lr", lr, "--seed", seed, "--scale", scale]
    if spec:
        a += ["--spec", json.dumps(spec)]
    if ucfg:
        a += ["--ucfg", json.dumps(ucfg)]
    return a


REPLAY = [("mnist", "cttv2", dict(CTT, tt_reset=True)), ("mnist", "agad", dict(CTT, tt_reset=False, agad_beta=0.3)),
          ("lm", "ttv2", dict(tt_lambda=0.1, tt_lr_ratio=10.0, tt_period=16))]


def c_legacy_replay(rng="legacy"):
    res = []
    for task, algo, u in REPLAY:
        lr = "0.003" if task == "mnist" else "0.0001"
        a = runp("run.py", _cfg(task, algo, PROTONIC, u, lr=lr), f"old_{task}_{algo}")
        b = runp("run_rev.py", _cfg(task, algo, PROTONIC, u, lr=lr) + ["--rng", rng], f"rev_{rng}_{task}_{algo}")
        same = a["metric"] == b["metric"] and a["hist"] == b["hist"] and \
            [l["pulses"] for l in a["layers"]] == [l["pulses"] for l in b["layers"]]
        res.append(dict(task=task, algo=algo, same=same, old=a["metric"], rev=b["metric"]))
    return all(r["same"] for r in res), res


def _arms(task):
    lr = "0.003" if task == "mnist" else "0.0001"
    P = dict(CTT, tt_reset="pulse")
    arms = [("fp_sgd", "sgd", None, None), ("fp_adam", "sgd", None, None), ("device", "sgd", PROTONIC, None),
            ("device", "ttv2", PROTONIC, dict(tt_lambda=0.1, tt_lr_ratio=10.0, tt_period=16, tt_reset="pulse")),
            ("fp_sgd", "ttv2", None, dict(tt_lambda=0.1, tt_lr_ratio=10.0, tt_period=16, tt_reset="pulse"))]
    if task == "mnist":
        arms += [("device", "cttv2", PROTONIC, P), ("device", "agad", PROTONIC, dict(P, tt_reset=False, agad_beta=0.3)),
                 ("device", "cttv2", LI_AIHW, P)]
    return lr, arms


def c_matched_controls(rng="split"):
    res = {}
    ok = True
    for task in ("mnist", "lm"):
        lr, arms = _arms(task)
        hs = []
        for i, (arm, algo, spec, u) in enumerate(arms):
            r = runp("run_rev.py", _cfg(task, algo, spec, u, arm=arm, lr=lr, seed="3") + ["--rng", rng],
                     f"mc_{rng}_{task}_{i}")
            hs.append((arm, algo, (spec or {}).get("bounds_model", "paper"), r["init_sha256"][:16], r["data_sha256"][:16]))
        same = len({h[3] for h in hs}) == 1 and len({h[4] for h in hs}) == 1
        ok = ok and same
        res[task] = dict(same=same, arms=hs)
    return ok, res


def _mlp(algo, mode, seed=5):
    st = R.Streams(seed, mode, DEV)
    spec = R.DeviceSpec(**PROTONIC)
    uc = R.UpdateCfg(lr=3e-3, algo=algo, **({} if algo == "sgd" else dict(tt_lambda=0.1, tt_lr_ratio=10.0, tt_period=16)))
    return TR.MLP(TR.Lin("analog", spec, uc, st.noise, DEV, streams=st))


def c_population(mode="split"):
    a, b = _mlp("sgd", mode), _mlp("ttv2", mode)
    eq = []
    for la, lb in zip(R.analog_layers(a), R.analog_layers(b)):
        eq.append(all(torch.equal(getattr(la.C, k), getattr(lb.C, k)) for k in ("k_up", "k_dn", "gmax", "gmin", "g_ref")))
    return all(eq), eq


def _layer(reset, spec=None, iters=2, rmax=62):
    st = R.Streams(0, "split", DEV)
    s = R.DeviceSpec(**(spec or dict(n_states=1000, asym=0.05, gamma_up=0.2, gamma_dn=0.2)))
    uc = R.UpdateCfg(lr=1e-3, algo="ttv2", tt_lambda=0.1, tt_period=1, tt_reset=reset, tt_reset_iters=iters, tt_reset_max=rmax)
    return R.AnalogLinear(4, 3, s, uc, st.noise, DEV, streams=st)


def c_reset_physical(alt_mode="alt", pulse_mode="pulse"):
    out = {}
    # alt: BL alternating pairs from u = 0.8
    m = _layer(alt_mode)
    applied = {"n": 0.0}
    orig = m.A.apply_pulses_cols

    def spy(idx, nu, nd):
        applied["n"] += float(nu.sum() + nd.sum())
        return orig(idx, nu, nd)
    m.A.apply_pulses_cols = spy
    m.A.u = torch.full((3, 4), 0.8)
    idx = torch.arange(4)
    m.n_reset_pulses = 0.0
    if m.reset == "ideal":
        m.A.u[:, idx] = m.A.ustar[:, idx]; m.n_reset_pulses += 12 * 2 * m.ucfg.BL  # the ideal reset's own step
    else:
        m._reset_pulsed(idx, m.A.weight()[:, idx])
    us = float(m.A.ustar[0, 0])
    B1 = float(m.A.k_up[0, 0] * m.A.gu + m.A.k_dn[0, 0] * m.A.gd)
    want = us + (0.8 - us) * math.exp(-31 * B1)
    out["alt"] = dict(u=float(m.A.u[0, 0]), want=want, charged=float(m.n_reset_pulses), applied=applied["n"])
    ok_alt = abs(out["alt"]["u"] - want) < 1e-4 and out["alt"]["charged"] == out["alt"]["applied"] == 12 * 62
    # pulse: read-correct to the read zero, ample budget
    m = _layer(pulse_mode, iters=3, rmax=1000)
    applied["n"] = 0.0
    orig = m.A.apply_pulses_cols
    m.A.apply_pulses_cols = spy
    m.A.u = torch.full((3, 4), 0.8)
    m.n_reset_pulses = 0.0
    if m.reset == "ideal":
        m.A.u[:, idx] = m.A.ustar[:, idx]; m.n_reset_pulses += 12 * 2 * m.ucfg.BL
    else:
        m._reset_pulsed(idx, m.A.weight()[:, idx])
    resid = float((m.A.weight() / (m.A.alpha * m.A.k_nom)).abs().max())
    out["pulse"] = dict(resid_steps=resid, charged=float(m.n_reset_pulses), applied=applied["n"])
    ok_p = resid <= 1.0 and out["pulse"]["charged"] == out["pulse"]["applied"] > 0
    return ok_alt and ok_p, out


def _linearstep(n_up, n_dn, wmax, wmin, gu, gd, dw):
    w, tr = 0.0, []
    for i in range(n_up + n_dn):
        if i < n_up:
            w = min(wmax, w + dw * (1 - gu * w / wmax))
        else:
            w = max(wmin, w - dw * (1 + gd * w / -wmin))
        tr.append(w)
    return tr


def c_aihwkit_formula(spec=None):
    s = dict(spec or LI_AIHW)
    for k in ("asym_d2d", "d2d", "bound_d2d", "gamma_up_dtod", "gamma_dn_dtod", "c2c", "ref_err"):
        s[k] = 0.0
    t = R.Tile((1, 1), R.DeviceSpec(**s), 1.0, torch.Generator().manual_seed(0), DEV)
    t.u = torch.zeros((1, 1))
    one, zero = torch.ones((1, 1)), torch.zeros((1, 1))
    ours = []
    for i in range(4500):
        t.apply_pulses(one, zero) if i < 1500 else t.apply_pulses(zero, one)
        ours.append(float(t.u))
    ref = _linearstep(1500, 3000, 1.1724, -0.8276, 0.1153, 0.5085, 0.002)
    err = max(abs(a - b) for a, b in zip(ours, ref))
    return err < 2e-3, dict(max_abs_err=err, ours_max=max(ours), ours_min=min(ours), ref_max=max(ref), ref_min=min(ref))


def c_clip_stats(mod=R):
    st = {"_clip": True}
    x = torch.full((1, 1), 10.0); d = torch.full((1, 1), 10.0)
    mod.pulse_counts(x, d, 0.1, 0.002, 31, torch.Generator().manual_seed(0), st)
    st2 = {"_clip": True}
    mod.pulse_counts(torch.full((1, 1), 0.1), torch.full((1, 1), 0.1), 0.1, 0.002, 31, torch.Generator().manual_seed(0), st2)
    if "want" not in st:
        return False, dict(error="no clipping statistics")
    lost = 1 - float(st["got"]) / float(st["want"])
    lost2 = 1 - float(st2["got"]) / float(st2["want"])
    ok = float(st["clip_calls"]) == 1 and abs(lost - (1 - 31 / 5000)) < 1e-6 and float(st2["clip_calls"]) == 0 and abs(lost2) < 1e-6
    return ok, dict(lost=lost, lost_unclipped=lost2)


def c_h_forget(swap=False):
    res = {}
    for forget in (False, True):
        st = R.Streams(0, "split", DEV)
        uc = R.UpdateCfg(lr=1e-3, algo="ttv2", tt_lambda=0.0, tt_period=1, tt_reset="none", tt_h_forget=forget != swap)
        m = R.AnalogLinear(4, 3, R.DeviceSpec(ideal_float=True), uc, st.noise, DEV, streams=st)
        m.H.fill_(2.5)
        m._transfer()
        res[str(forget)] = float(m.H[0, 0])
    return res["False"] == 0.5 and res["True"] == 0.0, res


def c_recenter_sp(recenter=True):
    s = R.DeviceSpec(n_states=1000, asym=0.4, gamma_up=0.2, gamma_dn=0.2, recenter_sp=recenter)
    t = R.Tile((1, 1), s, 1.0, torch.Generator().manual_seed(0), DEV)
    sp = float(t.ustar)
    t.u = torch.full((1, 1), 0.9)
    for _ in range(100):
        t.apply_pulses(torch.full((1, 1), 200.0), torch.full((1, 1), 200.0))
    eq = float(t.u)
    t.u = torch.zeros((1, 1))
    t.apply_pulses(torch.full((1, 1), 5000.0), torch.zeros((1, 1)))
    top = float(t.u)
    return abs(sp) < 1e-6 and abs(eq) < 0.01 and top > 0.9, dict(symmetry_point=sp, alternating_equilibrium=eq, up_reach=top)


CHECKS = {"c_legacy_replay": c_legacy_replay, "c_matched_controls": c_matched_controls, "c_population": c_population,
          "c_reset_physical": c_reset_physical, "c_aihwkit_formula": c_aihwkit_formula, "c_clip_stats": c_clip_stats,
          "c_h_forget": c_h_forget, "c_recenter_sp": c_recenter_sp}
OLD_LI = dict(n_states=1000, asym=0.0, gamma_up=0.1153, gamma_dn=0.5085)
FAULTS = {
    "f_split_vs_old": ("c_legacy_replay", lambda: c_legacy_replay(rng="split")),
    "f_legacy_controls": ("c_matched_controls", lambda: c_matched_controls(rng="legacy")),
    "f_legacy_population": ("c_population", lambda: c_population(mode="legacy")),
    "f_ideal_reset": ("c_reset_physical", lambda: c_reset_physical(alt_mode="ideal", pulse_mode="ideal")),
    "f_old_li_mapping": ("c_aihwkit_formula", lambda: c_aihwkit_formula(spec=OLD_LI)),
    "f_old_pulse_counts": ("c_clip_stats", lambda: c_clip_stats(mod=OLD)),
    "f_forget_swapped": ("c_h_forget", lambda: c_h_forget(swap=True)),
    "f_not_recentred": ("c_recenter_sp", lambda: c_recenter_sp(recenter=False)),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    torch.set_num_threads(2)
    out = dict(schema="altone.x1000.me-revision.tests.v1", torch=torch.__version__, checks={}, faults={})
    for n, f in CHECKS.items():
        ok, det = f()
        out["checks"][n] = dict(ok=bool(ok), detail=det)
        print(n, "OK" if ok else "FAIL", flush=True)
    for n, (cn, f) in FAULTS.items():
        try:
            ok, det = f()
            caught = not ok
        except Exception as e:  # a crash on the planted fault also counts as caught
            caught, det = True, dict(exception=repr(e)[:300])
        out["faults"][n] = dict(check=cn, caught=bool(caught), detail=det)
        print(n, "CAUGHT" if caught else "MISSED", flush=True)
    out["all_ok"] = all(c["ok"] for c in out["checks"].values()) and all(f["caught"] for f in out["faults"].values())
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "wb") as f:
        f.write((json.dumps(out, indent=1, sort_keys=True, default=str) + "\n").encode("utf-8"))
    print("ALL_OK" if out["all_ok"] else "NOT_OK")
    sys.exit(0 if out["all_ok"] else 1)


if __name__ == "__main__":
    main()
