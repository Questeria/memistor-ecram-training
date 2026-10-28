"""REVISION: pulse-response curves of the aihwkit presets themselves (run ON A POD, in a venv with aihwkit from PyPI; never
on the desk). Writes $OUT/AIHWKIT-CURVES.json: the installed version, every field of each preset, and for each schedule the
per-pulse mean, sd and 5/50/95 % quantiles across n devices (with and without cycle-to-cycle noise), and each device's
maximum and minimum state reached.

    python aihwkit_curves.py OUT.json
"""
import dataclasses
import inspect
import json
import sys
import time

import numpy as np
import torch

import aihwkit
from aihwkit.simulator.configs import SingleRPUConfig
from aihwkit.simulator.presets.devices import EcRamMOPresetDevice, EcRamPresetDevice
from aihwkit.utils import visualization as V

N = 500
SCHED = {  # (direction, count) segments; +1 = the direction aihwkit's own plots start with
    "EcRamPresetDevice": [(+1, 1500), (-1, 3000), (+1, 3000), (0, 2000)],
    "EcRamMOPresetDevice": [(+1, 10000), (-1, 20000), (+1, 20000), (0, 6000)],
}
STRIDE = {"EcRamPresetDevice": 10, "EcRamMOPresetDevice": 50}


def direction(segs):
    out = []
    for d, n in segs:
        out += ([+1, -1] * (n // 2)) if d == 0 else [d] * n
    return np.array(out, dtype=float)


def make_tile(dev, noise_free):
    cfg = SingleRPUConfig(device=dev)
    sig = inspect.signature(V.get_tile_for_plotting).parameters
    kw = {}
    if "use_cuda" in sig:
        kw["use_cuda"] = False
    if "noise_free" in sig:
        kw["noise_free"] = noise_free
    if "w_init" in sig:  # start every device at w = 0 (aihwkit's own default is w_min)
        kw["w_init"] = 0.0
    t = V.get_tile_for_plotting(cfg, N, **kw)
    if "w_init" not in sig:
        w0 = torch.zeros((N, 1))
        try:
            t.set_weights(w0)
        except TypeError:
            t.set_weights(w0, None)
    return t


def summarise(tr, stride):
    w = tr[:, :, 0]  # (pulses, N)
    idx = np.arange(0, w.shape[0], stride)
    q = np.quantile(w[idx], [0.05, 0.5, 0.95], axis=1)
    return dict(index=idx.tolist(), mean=w[idx].mean(1).tolist(), sd=w[idx].std(1, ddof=1).tolist(),
                q05=q[0].tolist(), q50=q[1].tolist(), q95=q[2].tolist(),
                dev_max=w.max(0).tolist(), dev_min=w.min(0).tolist(), final=w[-1].tolist(),
                first100_mean=float(w[99].mean()))


def main():
    out = dict(schema="altone.x1000.me-revision.aihwkit-curves.v1", aihwkit=aihwkit.__version__, torch=torch.__version__,
               n_devices=N, schedules={k: v for k, v in SCHED.items()}, presets={})
    for cls in (EcRamPresetDevice, EcRamMOPresetDevice):
        dev = cls()
        name = cls.__name__
        fields = {f.name: (getattr(dev, f.name) if isinstance(getattr(dev, f.name), (int, float, bool, str)) else
                           str(getattr(dev, f.name))) for f in dataclasses.fields(dev)}
        rec = dict(fields=fields)
        dirs = direction(SCHED[name])
        for nf in (True, False):
            torch.manual_seed(0)
            t0 = time.time()
            tile = make_tile(cls(), nf)
            tr = V.compute_pulse_response(tile, dirs, False)
            rec["noise_free" if nf else "noisy"] = dict(summarise(np.asarray(tr), STRIDE[name]), seconds=time.time() - t0)
        out["presets"][name] = rec
        print(name, rec["noise_free"]["first100_mean"], rec["noisy"]["first100_mean"], flush=True)
    with open(sys.argv[1], "wb") as f:
        f.write((json.dumps(out, sort_keys=True) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
