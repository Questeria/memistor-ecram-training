"""ME-REVISE-2 checks of the explicit pulse streams (pulse_seq_rev2.py) and the runner (run_rev2.py). Each check is also run
against a planted fault and must FAIL there (PLAN-REVISION-2.md section 1).

    python -B test_rev2.py [--out TESTS-REV2.json]       (CPU; MNIST at 1 % scale for the runner checks)
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
import memsim_rev as MR  # noqa: E402
import pulse_seq_rev2 as PS  # noqa: E402
import run_rev2 as RR  # noqa: E402

KEEP_AC = PS._ac
CAT = os.path.join(HERE, "..", "records", "revision", "CATALOG-REV.json")


def spec(name, **over):
    s = dict(json.load(open(CAT, "rb"))["entries"][name]["spec"])
    s.update(over)
    return MR.DeviceSpec(**{k: v for k, v in s.items() if k in MR.DeviceSpec.__dataclass_fields__})


def tile(sp, shape=(6, 9), seed=1):
    g = torch.Generator().manual_seed(seed)
    t = MR.Tile(shape, sp, 0.5, g, torch.device("cpu"), ngen=torch.Generator().manual_seed(seed + 1))
    t.program((torch.rand(shape, generator=g) - 0.5) * 0.3)
    return t


# --------------------------------------------------------------------------- checks
def c1_closed_form():
    """seq (closed-form same-sign trains) == slot (pulse by pulse) on the same line firings, noise-free, several samples of
    mixed signs, a saturating paper device and an aihwkit-mapped device."""
    worst = 0.0
    for nm in ("protonic_onen2022", "ecram_mo_kim2019"):
        t = tile(spec(nm, c2c=0.0, n_states=40.0))
        P = PS.dev_params(t)
        g = torch.Generator().manual_seed(5)
        px = (torch.rand((7, 9), generator=g) - 0.5) * 1.6
        pd = (torch.rand((7, 6), generator=g) - 0.5) * 1.6
        px, pd = px.clamp(-1, 1), pd.clamp(-1, 1)
        fire = []
        a = PS.seq_apply(t.u, P, px, pd, 31, g, keep_fire=fire, chunk=3)
        b = PS.slot_apply(t.u, P, px, pd, 31, g, fire=fire, chunk=3)
        worst = max(worst, float((a - b).abs().max()) / t.k_nom)
    return dict(ok=worst < 1e-3, max_diff_nominal_steps=worst)


def c2_counts():
    """The mean coincidence count of a cell is BL |p_x,i| |p_d,j| (the surrogate's Poisson mean), within 4 SE."""
    g = torch.Generator().manual_seed(7)
    px = torch.tensor([[0.9, -0.3, 0.05]]).repeat(4000, 1)
    pd = torch.tensor([[-0.6, 0.2]]).repeat(4000, 1)
    n, _, _ = PS.counts(px, pd, 31, g)
    mean, sd = n.mean(0), n.std(0)
    exp = 31 * pd[0].abs()[:, None] * px[0].abs()[None, :]
    z = ((mean - exp) / (sd / math.sqrt(4000)).clamp_min(1e-9)).abs()
    return dict(ok=bool((z < 4).all()), max_z=float(z.max()))


def c3_boundary():
    """Review 2's limiting case: one sample, p_x = p_d = 1, BL 31. The stream delivers exactly 31 pulses (variance 0);
    the surrogate's Poisson(31) exceeds 31 with probability 0.4524."""
    g = torch.Generator().manual_seed(9)
    px, pd = torch.ones((1, 1)), torch.ones((1, 1))
    ns = torch.stack([PS.counts(px, pd, 31, g)[0][0, 0, 0] for _ in range(400)])
    lam = torch.full((4000,), 31.0)
    pois = torch.poisson(lam, generator=g)
    frac = float((pois > 31).float().mean())
    return dict(ok=float(ns.var()) == 0.0 and float(ns.mean()) == 31.0 and abs(frac - 0.4524) < 0.03,
                seq_mean=float(ns.mean()), seq_var=float(ns.var()), surrogate_p_gt_31=frac)


def _run(args, out):
    RR.main(args + ["--task", "mnist", "--algo", "cttv2", "--lr", "0.003", "--seed", "0", "--scale", "0.01",
                    "--spec", json.dumps(dict(json.load(open(CAT, "rb"))["entries"]["ecram_li_tang2018"]["spec"],
                                              name="ecram_li_tang2018")),
                    "--ucfg", json.dumps(dict(tt_lambda=0.1, tt_lr_ratio=10.0, tt_period=16, tt_reset="pulse",
                                              tt_rho=0.05)), "--out", out])
    return json.load(open(out, "rb"))


def c4_transparent(tmp):
    """run_rev2 --pulse surrogate with probes on reproduces run_rev2 without probes (the probes draw from their own
    generator), and its pulse counts; it also writes its probes."""
    a = _run(["--probe-steps", "2", "--probe-layers", "0,2", "--probe-draws", "2",
              "--probe-out", os.path.join(tmp, "p.json")], os.path.join(tmp, "a.json"))
    b = _run([], os.path.join(tmp, "b.json"))
    same = a["metric"] == b["metric"] and [l["pulses"] for l in a["layers"]] == [l["pulses"] for l in b["layers"]]
    pr = json.load(open(os.path.join(tmp, "p.json"), "rb"))["probes"]
    return dict(ok=same and len(pr) == 2 and a["pulse_mode"] == "surrogate", same=same, probes=len(pr),
                probe0={k: pr[0][k] for k in ("layer", "update", "shape", "lost_frac")} if pr else None)


def c5_seq_routes(tmp):
    """--pulse seq changes the run (the explicit stream is used) and still trains (finite metric, pulses counted)."""
    a = _run(["--pulse", "seq"], os.path.join(tmp, "s.json"))
    b = json.load(open(os.path.join(tmp, "b.json"), "rb"))
    differs = [l["pulses"] for l in a["layers"]] != [l["pulses"] for l in b["layers"]]
    return dict(ok=differs and math.isfinite(a["metric"]["acc"]) and all(l["pulses"] > 0 for l in a["layers"])
                and a["pulse_mode"] == "seq", differs=differs, acc=a["metric"]["acc"])


# --------------------------------------------------------------------------- planted faults
def _bad_ac(n, sg, P, xi=None):
    a, c, up, dn = KEEP_AC(n, sg, P, xi)
    return a, c.abs(), up, dn  # FAULT: down trains move up


def _bad_counts(px_b, pd_b, BL, gen):
    S, nin = px_b.shape
    nout = pd_b.shape[1]
    fx = (torch.rand((S, BL, nin), generator=gen) < px_b.abs()[:, None, :] ** 2).float()  # FAULT: p^2
    fd = (torch.rand((S, BL, nout), generator=gen) < pd_b.abs()[:, None, :]).float()
    return torch.bmm(fd.transpose(1, 2), fx), fx, fd


def _poisson_counts(px_b, pd_b, BL, gen):
    lam = BL * pd_b.abs()[:, :, None] * px_b.abs()[:, None, :]  # FAULT: the stream replaced by Poisson draws
    S, nin = px_b.shape
    return torch.poisson(lam, generator=gen), torch.ones((S, BL, nin)), torch.ones((S, BL, pd_b.shape[1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "..", "records", "revision2", "TESTS-REV2.json"))
    a = ap.parse_args()
    torch.set_num_threads(2)
    res, faults = {}, {}
    with tempfile.TemporaryDirectory() as tmp:
        res["c1_closed_form"] = c1_closed_form()
        res["c2_counts"] = c2_counts()
        res["c3_boundary"] = c3_boundary()
        res["c4_transparent"] = c4_transparent(tmp)
        res["c5_seq_routes"] = c5_seq_routes(tmp)
        keep_t, keep_c = PS._ac, PS.counts
        PS._ac = _bad_ac
        faults["c1_down_trains_move_up"] = c1_closed_form()
        PS._ac = keep_t
        PS.counts = _bad_counts
        faults["c2_line_probability_squared"] = c2_counts()
        PS.counts = _poisson_counts
        faults["c3_poisson_instead_of_stream"] = c3_boundary()
        PS.counts = keep_c
        RR.CFG["fault_probe_shared_gen"] = True
        try:
            faults["c4_probe_shares_the_run_generator"] = c4_transparent(tmp)
        finally:
            RR.CFG["fault_probe_shared_gen"] = False
        keep_u = RR.CFG
        orig = RR.MR.AnalogLinear.update
        RR.MR.AnalogLinear.update = RR._orig_update  # FAULT: the seq flag is ignored
        faults["c5_seq_flag_ignored"] = c5_seq_routes(tmp)
        RR.MR.AnalogLinear.update = orig
    all_ok = all(v["ok"] for v in res.values())
    caught = all(not v["ok"] for v in faults.values())
    out = dict(schema="altone.x1000.me-revision2.tests.v1", checks=res, faults=faults, all_ok=all_ok,
               all_faults_caught=caught, torch=torch.__version__)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "wb") as f:
        f.write((json.dumps(out, indent=1, default=str) + "\n").encode("utf-8"))
    for k, v in list(res.items()) + list(faults.items()):
        print(k, "ok" if v["ok"] else "FAIL")
    print("ALL_OK" if all_ok and caught else "NOT_OK", "checks", all_ok, "faults caught", caught)
    sys.exit(0 if all_ok and caught else 1)


if __name__ == "__main__":
    main()
