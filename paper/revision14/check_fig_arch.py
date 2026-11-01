"""Version 15 (review 12, finding B; derived from revision13/check_fig_arch.py of version 14): Figure 1 (fig_arch,
revision14/make_fig_arch.py) must say what the simulator does in the configurations the main experiment ran, and be legible.

Version 14's check built all three TT-family layers with tt_reset = "pulse", AGAD included, so it could not see that the figure's
shared panel gave AGAD a pulse reset it never had.  This check takes the configurations from the experiment itself:
  0. settings: the figure's SETTINGS (reset of A, chopper) for TTv2, c-TTv2 and AGAD equal the selected configurations
     (records/revision/CHOICES-REVISION.json, tt.<algo>.ucfg) and every main-experiment device record of that algorithm
     (records/revision/runs/e3, arm "device": 90 per algorithm); every such record has tt_gamma = 0 (forward weight C); the labels
     drawn (the A box, the pulse-probability box, the key) are the ones make_fig_arch.labels() derives from SETTINGS.
Against the simulator (sim/memsim_rev.py, AnalogLinear on CPU, one small layer per algorithm SGD, TTv2, c-TTv2 and AGAD, built with
the update configuration of that algorithm's first main-experiment device record; only the learning rate is raised to 0.2, so that
a few steps move pulses in a 12 x 6 layer):
  1. state: every box tied to simulator state names an attribute the layer has for exactly the box's algorithms, and its class
     matches the attribute's type (device box = a device Tile, digital box = a plain tensor); the digital state the buffer box
     also names (chopper signs, AGAD's averages) exists for exactly the stated algorithms; no other Tile or state tensor exists;
  2. reads: the layer's forward output equals the fp32 product x C^T + b exactly (the read box: ideal fp32);
  3. pulses: over a few update steps, SGD pulses only its weight tile (C); the TT family pulses A and C, never through the exact
     digital path, and its buffer H changes; every box that receives a device arrow is a tile that received pulses, and every
     tile that received pulses receives a device arrow;
  4. reset and chopper: A is reset (reset pulses applied) exactly for the algorithms SETTINGS gives the pulse reset, and the layer
     carries chopper signs exactly for the algorithms SETTINGS gives a chopper.
On the drawing (matplotlib 3.9.2): every label lies inside its box and no two texts overlap (the key included).
--selftest plants eight faults and each must be caught: the buffer drawn as a device; the chopper signs left out; the forward
read declared a device operation; a label moved onto another (version 14's four); AGAD drawn with the pulse reset (review 12);
TTv2 drawn with a chopper; the simulator run with version 14's synthetic configuration (the pulse reset for all three); version
14's A-box label (a pulse reset for all) put back.

    python -B revision14/check_fig_arch.py [--selftest] [--json out.json]          (from paper/; torch and matplotlib 3.9.2)
"""
import glob
import importlib.util
import json
import os
import sys
import types

HERE = os.path.dirname(os.path.abspath(__file__))
P = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(P, "sim"))
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
CHOICES = os.path.join(P, "records", "revision", "CHOICES-REVISION.json")
E3 = os.path.join(P, "records", "revision", "runs", "e3")
TT = ("ttv2", "cttv2", "agad")
V14_A_LABEL = "array $A$ (device\ntile); pulse reset\n$\\leq 62$/weight"


def load_fig():
    spec = importlib.util.spec_from_file_location("make_fig_arch_under_test", os.path.join(HERE, "make_fig_arch.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def experiment():
    """The selected configurations and what every main-experiment device record carries."""
    import memsim_rev as M
    ch = json.load(open(CHOICES, "rb"))["tt"]
    recs = {}
    for p in sorted(glob.glob(os.path.join(E3, "*.json"))):
        r = json.load(open(p, "rb"))
        if r["arm"] == "device":
            recs.setdefault(r["algo"], []).append(r["ucfg"])
    out = {}
    for algo in ("sgd",) + TT:
        u = recs.get(algo, [])
        out[algo] = dict(
            n_records=len(u), first_ucfg=u[0] if u else None,
            reset_in_records=sorted({M.reset_mode(x.get("tt_reset")) for x in u}) if algo != "sgd" else None,
            tt_gamma_in_records=sorted({x.get("tt_gamma") for x in u}),
            reset_selected=M.reset_mode(ch[algo]["ucfg"]["tt_reset"]) if algo in ch else None)
    return out


def layer(M, algo, ucfg=None):
    import torch
    spec = M.DeviceSpec(n_states=60, asym=0.1, gamma_up=0.4, gamma_dn=0.4, c2c=0.05, d2d=0.1, ref_err=0.02, name="check")
    if ucfg is None:     # version 14's synthetic configuration: the pulse reset for all three TT algorithms
        u = M.UpdateCfg(lr=0.2, algo=algo, tt_lr_ratio=1.0 if algo == "sgd" else 10.0, tt_lambda=1.0, tt_period=1, tt_reset="pulse",
                        tt_rho=0.5)
    else:
        u = M.UpdateCfg(**dict(ucfg, lr=0.2))
    st = M.Streams(0, "split", device="cpu")
    torch.manual_seed(0)
    return M.AnalogLinear(12, 6, spec, u, None, "cpu", streams=st)


def sim_facts(F, exp, synthetic=False):
    """What the simulator holds and does, per algorithm, in the main experiment's configuration (or version 14's synthetic one)."""
    import torch
    import memsim_rev as M
    facts = {}
    for algo in ("sgd",) + TT:
        L = layer(M, algo, None if synthetic else exp[algo]["first_ucfg"])
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
                           exact_updates=exact, buffer_changed=None if h0 is None else bool(not torch.equal(h0, L.H)),
                           reset_mode=L.reset, resets=float(L.n_reset), reset_pulses=float(L.n_reset_pulses),
                           chopper=L.chop is not None)
    return facts


def judge_settings(F, exp):
    """0. The figure's SETTINGS against the selected configurations and the main-experiment records; its labels derived from them."""
    bad = []
    for algo in TT:
        s, e = F.SETTINGS[algo], exp[algo]
        if e["n_records"] == 0:
            bad.append(f"{algo}: no main-experiment device record")
        if s["reset"] != e["reset_selected"]:
            bad.append(f"{algo}: figure says reset {s['reset']}, the selected configuration has {e['reset_selected']}")
        if e["reset_in_records"] != [s["reset"]]:
            bad.append(f"{algo}: figure says reset {s['reset']}, the main-experiment records have {e['reset_in_records']}")
        if e["tt_gamma_in_records"] != [0.0]:
            bad.append(f"{algo}: tt_gamma in the records is {e['tt_gamma_in_records']}, the figure draws forward weight C")
    a_lab, p_lab, key = F.labels(F.SETTINGS)
    boxes = {b[0]: b for b in F.BOXES}
    if boxes["b_A"][7] != a_lab:
        bad.append("the A box's label is not the one derived from SETTINGS")
    if boxes["b_prob"][7] != p_lab:
        bad.append("the pulse-probability box's label is not the one derived from SETTINGS")
    if F.KEY != key:
        bad.append("the key is not the one derived from SETTINGS")
    if tuple(F.H_ALSO.get("chop", ())) != F.chopped(F.SETTINGS):
        bad.append("the chopper entry of the buffer box does not follow SETTINGS")
    return bad


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
        if algo in TT:
            s = F.SETTINGS[algo]
            reset_seen = f["resets"] > 0 and f["reset_pulses"] > 0
            if f["reset_mode"] != s["reset"]:
                bad.append(f"{algo}: figure says reset {s['reset']}, the simulated layer has {f['reset_mode']}")
            if reset_seen != (s["reset"] == "pulse"):
                bad.append(f"{algo}: figure says reset {s['reset']}, the simulator {'reset' if reset_seen else 'did not reset'} A "
                           f"({f['resets']:g} weights, {f['reset_pulses']:g} pulses)")
            if f["chopper"] != s["chopper"]:
                bad.append(f"{algo}: figure says chopper {s['chopper']}, the simulated layer has chopper {f['chopper']}")
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
    (x0, y0), (x1, y1) = inv.transform([[bb["settings"].x0, bb["settings"].y0], [bb["settings"].x1, bb["settings"].y1]])
    if x0 < 3.13 or x1 > F.W_IN or y1 > F.H_IN:
        bad.append("the key leaves panel (b)")
    import matplotlib.pyplot as plt
    plt.close(fig)
    return bad


def variant(F, **settings_change):
    """A copy of the figure's tables with SETTINGS changed and everything derived from SETTINGS re-derived."""
    G = types.SimpleNamespace(**{k: getattr(F, k) for k in ("BOXES", "ARROWS", "H_ALSO", "SETTINGS", "KEY", "labels", "chopped")})
    S = {k: dict(v) for k, v in F.SETTINGS.items()}
    for algo, ch in settings_change.items():
        S[algo].update(ch)
    G.SETTINGS = S
    a_lab, p_lab, G.KEY = F.labels(S)
    G.BOXES = [b[:7] + ((a_lab if b[0] == "b_A" else p_lab),) + b[8:] if b[0] in ("b_A", "b_prob") else b for b in F.BOXES]
    G.H_ALSO = dict(F.H_ALSO, chop=F.chopped(S))
    return G


def main():
    F = load_fig()
    exp = experiment()
    facts = sim_facts(F, exp)
    res = dict(experiment={k: {kk: vv for kk, vv in v.items() if kk != "first_ucfg"} for k, v in exp.items()},
               settings=F.SETTINGS, facts=facts, settings_problems=judge_settings(F, exp), sim_problems=judge(F, facts),
               layout_problems=layout(F))
    res["ok"] = not res["settings_problems"] and not res["sim_problems"] and not res["layout_problems"]
    if "--selftest" in sys.argv:
        st = {}
        both = lambda G, fc=facts: bool(judge_settings(G, exp) or judge(G, fc))
        G = types.SimpleNamespace(**{k: getattr(F, k) for k in ('BOXES', 'ARROWS', 'H_ALSO', 'SETTINGS', 'KEY', 'labels', 'chopped')})
        G.BOXES = [b[:6] + ("device",) + b[7:] if b[0] == "b_H" else b for b in F.BOXES]
        st["buffer_as_device"] = both(G)
        G = types.SimpleNamespace(**{k: getattr(F, k) for k in ('BOXES', 'ARROWS', 'H_ALSO', 'SETTINGS', 'KEY', 'labels', 'chopped')})
        G.H_ALSO = {k: v for k, v in F.H_ALSO.items() if k != "chop"}
        st["chopper_left_out"] = both(G)
        st["read_as_device"] = bool(judge(F, facts, read_kind="device"))
        moved = [b[:2] + (F.BOXES[1][2], F.BOXES[1][3]) + b[4:] if b[0] == "a_W" else b for b in F.BOXES]
        st["label_on_label"] = bool(layout(F, boxes=moved))
        st["agad_drawn_with_pulse_reset"] = both(variant(F, agad=dict(reset="pulse")))
        st["ttv2_drawn_with_chopper"] = both(variant(F, ttv2=dict(chopper=True)))
        st["v14_synthetic_configuration_simulated"] = bool(judge(F, sim_facts(F, exp, synthetic=True)))
        G = types.SimpleNamespace(**{k: getattr(F, k) for k in ('BOXES', 'ARROWS', 'H_ALSO', 'SETTINGS', 'KEY', 'labels', 'chopped')})
        G.BOXES = [b[:7] + (V14_A_LABEL,) + b[8:] if b[0] == "b_A" else b for b in F.BOXES]
        st["v14_a_label_put_back"] = both(G)
        res["selftest"] = dict(faults=st, ok=all(st.values()))
    res["all_ok"] = res["ok"] and res.get("selftest", {"ok": True})["ok"]
    print("settings problems", len(res["settings_problems"]), "| sim problems", len(res["sim_problems"]), "| layout problems",
          len(res["layout_problems"]),
          ("| faults caught %d of %d" % (sum(res["selftest"]["faults"].values()), len(res["selftest"]["faults"]))) if "selftest" in res else "",
          "|", "FIG_ARCH_OK" if res["all_ok"] else "FIG_ARCH_NOT_OK")
    for p in res["settings_problems"] + res["sim_problems"] + res["layout_problems"]:
        print("  ", p)
    if "--json" in sys.argv:
        jp = sys.argv[sys.argv.index("--json") + 1]
        os.makedirs(os.path.dirname(os.path.abspath(jp)), exist_ok=True)
        open(jp, "wb").write((json.dumps(res, indent=1) + "\n").encode("utf-8"))
    sys.exit(0 if res["all_ok"] else 1)


if __name__ == "__main__":
    main()
