"""Run one lane-ME configuration and write one JSON record (bytes, LF).

python -B run.py --task mnist --spec '{"n_states": 100, "asym": 0.1}' --algo sgd --lr 0.01 --seed 0 --out rec.json
--arm fp_sgd   : the same network and update rule with an exact float update (DeviceSpec.ideal_float)
--arm device   : every analog weight update goes through the device model (default)
--arm fp_adam  : torch.nn.Linear twins trained by Adam (context only, never the decisive baseline)
"""
import argparse
import json
import math
import os
import platform
import sys
import time

import torch
import torch.nn.functional as F

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from memsim import DeviceSpec, UpdateCfg, analog_layers, step_update  # noqa: E402
import tasks  # noqa: E402

BUDGET = {  # pre-registered (PLAN.md)
    "mnist": dict(epochs=10, batch=128),
    "cifar": dict(epochs=30, batch=128),
    "lm": dict(steps=3000, batch=32, ctx=128),
}


def build(task, lin, width=128):
    if task == "mnist":
        return tasks.MLP(lin)
    if task == "cifar":
        return tasks.CNN(lin, c=32 if width == 128 else width)  # --width for CIFAR = base channels (DEV scale only)
    return tasks.TinyLM(lin, d=width, ctx=BUDGET["lm"]["ctx"])


@torch.no_grad()
def eval_cls(model, x, y, bs=1000):
    model.eval()
    c, lsum = 0, 0.0
    for i in range(0, len(x), bs):
        o = model(x[i:i + bs])
        c += int((o.argmax(1) == y[i:i + bs]).sum())
        lsum += float(F.cross_entropy(o, y[i:i + bs], reduction="sum"))
    model.train()
    return c / len(x), lsum / len(x)


@torch.no_grad()
def eval_lm(model, va, ctx, bs=64):
    model.eval()
    n = (len(va) - 1) // ctx
    tot, cnt = 0.0, 0
    for i in range(0, n, bs):
        j = torch.arange(i, min(n, i + bs), device=va.device)
        st = j[:, None] * ctx + torch.arange(ctx + 1, device=va.device)[None]
        w = va[st]
        o = model(w[:, :-1])
        tot += float(F.cross_entropy(o.reshape(-1, o.shape[-1]), w[:, 1:].reshape(-1), reduction="sum"))
        cnt += w[:, 1:].numel()
    model.train()
    return tot / cnt / math.log(2)  # bits per byte


def _below_normal():
    if os.name == "nt":
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)


def main():
    _below_normal()
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=["mnist", "cifar", "lm"])
    ap.add_argument("--arm", default="device", choices=["device", "fp_sgd", "fp_adam"])
    ap.add_argument("--spec", default="{}")
    ap.add_argument("--algo", default="sgd", choices=["sgd", "ttv2"])
    ap.add_argument("--ucfg", default="{}")
    ap.add_argument("--lr", type=float, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--split", default="test", choices=["test", "val"])
    ap.add_argument("--scale", type=float, default=1.0, help="budget multiplier (tests and timing only)")
    ap.add_argument("--tag", default="")
    ap.add_argument("--width", type=int, default=128, help="LM width (default = the pre-registered 128)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(a.seed)
    gen = torch.Generator(device=dev).manual_seed(a.seed)
    spec = DeviceSpec(**json.loads(a.spec))
    if a.arm == "fp_sgd":
        spec = DeviceSpec(ideal_float=True, name="fp_sgd")
    ucfg = UpdateCfg(lr=a.lr, algo=a.algo, **json.loads(a.ucfg))
    lin = tasks.Lin("digital" if a.arm == "fp_adam" else "analog", spec, ucfg, gen, dev)
    model = build(a.task, lin, a.width).to(dev)
    dparams = [p for p in model.parameters()]
    opt = torch.optim.Adam(dparams, lr=a.lr) if a.arm == "fp_adam" else None
    b = BUDGET[a.task]
    t0 = time.time()
    hist = []
    rows = {id(m): 0 for m in analog_layers(model)}

    def train_step(xb, yb, flat):
        o = model(xb)
        if flat:
            o, yb = o.reshape(-1, o.shape[-1]), yb.reshape(-1)
        red = "mean" if opt is not None else "sum"
        loss = F.cross_entropy(o, yb, reduction=red)
        loss.backward()
        for m in analog_layers(model):
            if m._x is not None:
                rows[id(m)] += m._x.shape[0]
        if opt is not None:
            opt.step(); opt.zero_grad(set_to_none=True)
        else:
            step_update(model, dparams, a.lr)
        return float(loss) / (1 if opt is not None else len(yb))

    if a.task in ("mnist", "cifar"):
        D = tasks.load_mnist(dev) if a.task == "mnist" else tasks.load_cifar_subset(dev)
        n = len(D["xtr"])
        epochs = max(1, int(round(b["epochs"] * a.scale))) if a.scale >= 1 else b["epochs"]
        nb_lim = None if a.scale >= 1 else max(1, int(n // b["batch"] * a.scale))
        for ep in range(epochs):
            perm = torch.randperm(n, generator=gen, device=dev)
            ls, nb = 0.0, 0
            for i in range(0, n - b["batch"] + 1, b["batch"]):
                idx = perm[i:i + b["batch"]]
                ls += train_step(D["xtr"][idx], D["ytr"][idx], False); nb += 1
                if nb_lim and nb >= nb_lim:
                    break
            hist.append(dict(epoch=ep + 1, train_loss=ls / max(nb, 1)))
            if nb_lim:
                break
        xs, ys = (D["xte"], D["yte"]) if a.split == "test" else (D["xva"], D["yva"])
        acc, l = eval_cls(model, xs, ys)
        metric = dict(acc=acc, loss=l, split=a.split, n_eval=len(xs))
        samples = n * len(hist) if not nb_lim else nb_lim * b["batch"]
    else:
        D = tasks.load_enwik8_slice(dev)
        ctx, bs = b["ctx"], b["batch"]
        steps = int(b["steps"] * a.scale)
        tr = D["tr"]
        ls = 0.0
        for s in range(steps):
            st = torch.randint(0, len(tr) - ctx - 1, (bs,), generator=gen, device=dev)
            w = tr[st[:, None] + torch.arange(ctx + 1, device=dev)[None]]
            ls += train_step(w[:, :-1], w[:, 1:], True)
            if (s + 1) % 500 == 0:
                hist.append(dict(step=s + 1, train_loss_nats=ls / 500)); ls = 0.0
        va = D["va"] if a.split == "test" else D["tr"][-500_000:]
        metric = dict(bpb=eval_lm(model, va, ctx), split=a.split)
        samples = steps * bs * ctx
    nan = any(not math.isfinite(h.get("train_loss", h.get("train_loss_nats", 0.0))) for h in hist)
    layers = []
    for m in analog_layers(model):
        nw = m.in_f * m.out_f
        layers.append(dict(shape=[m.out_f, m.in_f], pulses=m.n_pulses, rows=rows[id(m)],
                           pulses_per_weight_per_row=m.n_pulses / max(1, nw * rows[id(m)]),
                           mean_px=m.stats.get("px", 0.0) / max(1, rows[id(m)]),
                           mean_pd=m.stats.get("pd", 0.0) / max(1, rows[id(m)])))
    rec = dict(schema="altone.x1000.me.run.v1", task=a.task, arm=a.arm, algo=a.algo, spec=spec.as_dict(),
               ucfg=ucfg.__dict__, lr=a.lr, seed=a.seed, scale=a.scale, tag=a.tag, width=a.width, metric=metric, hist=hist,
               diverged=nan, samples=samples, layers=layers, seconds=round(time.time() - t0, 2),
               torch=torch.__version__, device=torch.cuda.get_device_name(0) if dev.type == "cuda" else "cpu",
               host=platform.node(), results_are="DEV")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "wb") as f:
        f.write((json.dumps(rec, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps(dict(task=a.task, arm=a.arm, algo=a.algo, metric=metric, seconds=rec["seconds"])))


if __name__ == "__main__":
    main()
