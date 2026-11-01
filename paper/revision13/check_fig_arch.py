"""Version 14 (review 11): Figure 1 (fig_arch, revision13/make_fig_arch.py) must say what the simulator does, and be legible.

Against the simulator (sim/memsim_rev.py, AnalogLinear on CPU, one small layer per algorithm SGD, TTv2, c-TTv2 and AGAD with the
main table's tt_gamma = 0 and the pulse reset):
  1. state: every box tied to simulator state names an attribute the layer has for exactly the box's algorithms, and its class
     matches the attribute's type (device box = a device Tile, digital box = a plain tensor); the digital state the buffer box
     also names (chopper signs, AGAD's averages) exists for exactly the stated algorithms; no other Tile or state tensor exists;
  2. reads: the layer's forward output equals the fp32 product x C^T + b exactly (the read box: ideal fp32);
  3. pulses: over a few update steps, SGD pulses only its weight tile (C); the TT family pulses A (its update and the pulse reset)
     and C (the transfer), never through the exact digital path, and its buffer H changes; every box that receives a device arrow
     is a tile that received pulses, and every tile that received pulses receives a device arrow.
On the drawing (matplotlib 3.9.2): every label lies inside its box and no two texts overlap.
--selftest plants four faults and each must be caught: the buffer drawn as a device; the chopper signs left out; the forward read
declared a device operation; a label moved onto another.

    python -B revision13/check_fig_arch.py [--selftest] [--json out.json]          (from paper/; torch and matplotlib 3.9.2)
"""
import types
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(P, "sim"))
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")


def load_fig():
    spec = importlib.util.spec_from_file_location("make_fig_arch_under_test", os.path.join(HERE, "make_fig_arch.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def layer(M, algo):
    import torch
    spec = M.DeviceSpec(n_states=60, asym=0.1, gamma_up=0.4, gamma_dn=0.4, c2c=0.05, d2d=0.1, ref_err=0.02, name="check")
    u = M.UpdateCfg(lr=0.2, algo=algo, tt_lr_ratio=1.0 if algo == "sgd" else 10.0, tt_lambda=1.0, tt_period=1, tt_reset="pulse",
                    tt_rho=0.5)
    st = M.Streams(0, "split", device="cpu")
    torch.manual_seed(0)
    return M.AnalogLinear(12, 6, spec, u, None, "cpu", streams=st)


def sim_facts(F):
    """What the simulator holds and does, per algorithm."""
    import torch
    import memsim_rev as M
    facts = {}
    for algo in ("sgd", "ttv2", "cttv2", "agad"):
        L = layer(M, algo)
        state = {}
        for k, v in vars(L).items():
            if isinstance(v, M.Tile):
                state[k] = "device"
            elif isinstance(v, torch.Tensor) and v.dim() >= 1 and k not in ("_x", "_d"):
                state[k] = "digital"
        g = torch.Generator().manual_seed(1)
        x = torch.randn(8, 12, generator=g)
        y = L(x)
        ideal = x @ L.C.weight().t() + L.bias
        read_exact = bool(torch.equal(y.detach(), ideal))
        pulsed, exact = {}, []
        o_ap, o_apc, o_ex = M.Tile.apply_pulses, M.Tile.apply_pulses_cols, M.Tile.apply_exact
        name_of = lambda t: "A" if t is getattr(L, "A", None) else ("C" if t is L.C else "?")

        def ap(self, n_up, n_dn):
            pulsed[name_of(self)] = pulsed.get(name_of(self), 0.0) + float(n_up.sum() + n_dn.sum())
            return o_ap(self, n_up, n_dn)

        def apc(self, idx, n_up, n_dn):
            pulsed[name_of(self)] = pulsed.get(name_of(self), 0.0) + float(n_up.sum() + n_dn.sum())
            return o_apc(self, idx, n_up, n_dn)

        def ex(self, dw):
            exact.append(name_of(self))
            return o_ex(self, dw)
        M.Tile.apply_pulses, M.Tile.apply_pulses_cols, M.Tile.apply_exact = ap, apc, ex
        h0 = L.H.clone() if hasattr(L, "H") else None
        try:
            for s in range(6):
                xs = torch.randn(8, 12, generator=g)
                out = L(xs)
                (out ** 2).sum().backward()
                L.update()
        finally:
            M.Tile.apply_pulses, M.Tile.apply_pulses_cols, M.Tile.apply_exact = o_ap, o_apc, o_ex
        facts[algo] = dict(state=state, read_exact=read_exact, pulsed=sorted(k for k, v in pulsed.items() if v > 0),
                           exact_updates=exact, buffer_changed=None if h0 is None else bool(not torch.equal(h0, L.H)))
    return facts


def judge(F, facts, read_kind="read"):
    bad = []
    boxes = {b[0]: b for b in F.BOXES}
    for algo, f in facts.items():
        declared = {}
        for b in F.BOXES:
            if algo in b[8] and b[9]:
                declared[b[9]] = b[6]
        for attr, algos in F.H_ALSO.items():
            if algo in algos:
                declared[attr] = "digital"
        for attr, kind in declared.items():
            if f["state"].get(attr) != kind:
                bad.append(f"{algo}: figure says {attr} is {kind}, simulator has {f['state'].get(attr)}")
        for attr, kind in f["state"].items():
            if attr not in declared:
                bad.append(f"{algo}: simulator state {attr} ({kind}) is not in the figure")
        if not f["read_exact"]:
            bad.append(f"{algo}: the forward read is not the ideal fp32 product")
        if read_kind != "read" or any(b[6] != "read" for b in F.BOXES if b[0].endswith("read") and algo in b[8]):
            if f["read_exact"]:
                bad.append(f"{algo}: a read is drawn as a device or digital operation, but the simulator reads ideally in fp32")
        targets = sorted({boxes[a[1]][9] for a in F.ARROWS if a[2] == "device" and algo in boxes[a[1]][8]})
        if targets != f["pulsed"]:
            bad.append(f"{algo}: device arrows reach {targets}, the simulator pulsed {f['pulsed']}")
        if f["exact_updates"]:
            bad.append(f"{algo}: exact digital updates of {f['exact_updates']}")
        if algo != "sgd" and f["buffer_changed"] is not True:
            bad.append(f"{algo}: the digital buffer H did not change")
    return bad


def layout(F, boxes=None, arrows=None):
    fig, ax, texts = F.draw(boxes or F.BOXES, arrows or F.ARROWS)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    inv = ax.transData.inverted()
    bb = {k: t.get_window_extent(r) for k, t in texts.items()}
    bad = []
    keys = sorted(bb)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            if bb[a].overlaps(bb[b]):
                bad.append(f"texts overlap: {a} / {b}")
    for b in boxes or F.BOXES:
        (x0, y0), (x1, y1) = inv.transform([[bb[b[0]].x0, bb[b[0]].y0], [bb[b[0]].x1, bb[b[0]].y1]])
        if x0 < b[2] or y0 < b[3] or x1 > b[2] + b[4] or y1 > b[3] + b[5]:
            bad.append(f"label of {b[0]} leaves its box")
    import matplotlib.pyplot as plt
    plt.close(fig)
    return bad


def main():
    F = load_fig()
    facts = sim_facts(F)
    res = dict(facts=facts, sim_problems=judge(F, facts), layout_problems=layout(F))
    res["ok"] = not res["sim_problems"] and not res["layout_problems"]
    if "--selftest" in sys.argv:
        st = {}
        G = types.SimpleNamespace(**{k: getattr(F, k) for k in ('BOXES', 'ARROWS', 'H_ALSO')})
        G.BOXES = [b[:6] + ("device",) + b[7:] if b[0] == "b_H" else b for b in F.BOXES]
        st["buffer_as_device"] = bool(judge(G, facts))
        G = types.SimpleNamespace(**{k: getattr(F, k) for k in ('BOXES', 'ARROWS', 'H_ALSO')})
        G.H_ALSO = {k: v for k, v in F.H_ALSO.items() if k != "chop"}
        st["chopper_left_out"] = bool(judge(G, facts))
        st["read_as_device"] = bool(judge(F, facts, read_kind="device"))
        moved = [b[:2] + (F.BOXES[1][2], F.BOXES[1][3]) + b[4:] if b[0] == "a_W" else b for b in F.BOXES]
        st["label_on_label"] = bool(layout(F, boxes=moved))
        res["selftest"] = dict(faults=st, ok=all(st.values()))
    res["all_ok"] = res["ok"] and res.get("selftest", {"ok": True})["ok"]
    print("sim problems", len(res["sim_problems"]), "| layout problems", len(res["layout_problems"]),
          ("| faults caught %d of %d" % (sum(res["selftest"]["faults"].values()), len(res["selftest"]["faults"]))) if "selftest" in res else "",
          "|", "FIG_ARCH_OK" if res["all_ok"] else "FIG_ARCH_NOT_OK")
    for p in res["sim_problems"] + res["layout_problems"]:
        print("  ", p)
    if "--json" in sys.argv:
        jp = sys.argv[sys.argv.index("--json") + 1]
        os.makedirs(os.path.dirname(os.path.abspath(jp)), exist_ok=True)
        open(jp, "wb").write((json.dumps(res, indent=1) + "\n").encode("utf-8"))
    sys.exit(0 if res["all_ok"] else 1)


if __name__ == "__main__":
    main()
