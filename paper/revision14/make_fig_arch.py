"""Version 15 (review 12, finding B; derived from revision13/make_fig_arch.py of version 14): fig_arch, which parts of one learned
weight matrix are simulated as device operations and which are digital, for plain SGD (a) and the Tiki-Taka family as run in the
main table (b: TTv2, c-TTv2, AGAD; forward weight C, since tt_gamma = 0 in every main-table record).  Version 14 drew one shared
panel whose A box said "pulse reset" and whose input was c (.) x for all three algorithms; the selected settings differ
(Table rev_selection): TTv2 and c-TTv2 reset A with pulses, AGAD does not reset A; TTv2 has no chopper (c = 1), c-TTv2 and AGAD
use chopper signs.  SETTINGS below states this per algorithm; the A box, the pulse-probability box, the chopper entry of the buffer
box (H_ALSO) and the key "Selected settings" are all derived from it.

The figure is drawn from the tables BOXES and ARROWS below; revision14/check_fig_arch.py checks SETTINGS against the selected
configurations (records/revision/CHOICES-REVISION.json) and against every main-experiment record (records/revision/runs/e3), checks
every box's class against the simulator built with those configurations (sim/memsim_rev.py: which state is a device Tile and which
a digital tensor, that the reads are the ideal fp32 product, which tiles receive pulses, whether A is reset), and that no two
labels overlap.

    python -B revision14/make_fig_arch.py --out tex/figs          (from paper/; matplotlib 3.9.2, as the other figures)
"""
import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402

W_IN, H_IN, FS = 6.5, 2.42, 6.5
STYLE = {  # kind -> face, edge, line style
    "device": ("#fbe3c8", "#b85c00", "-"),
    "digital": ("#dbe8f6", "#1f5a99", "-"),
    "read": ("#ececec", "#555555", "--"),
}
TT = ("ttv2", "cttv2", "agad")
NAME = {"ttv2": "TTv2", "cttv2": "c-TTv2", "agad": "AGAD"}
# the selected settings of the main experiment (Table rev_selection; checked by revision14/check_fig_arch.py): the reset of A
# ("pulse": at most 62 pulses per weight in 2 read-correct iterations; "none") and whether the inputs carry chopper signs c
SETTINGS = {"ttv2": dict(reset="pulse", chopper=False),
            "cttv2": dict(reset="pulse", chopper=True),
            "agad": dict(reset="none", chopper=True)}


def labels(settings=None):
    """The labels that depend on the selected settings: the A box, the pulse-probability box and the key."""
    s = settings or SETTINGS
    pulse = [NAME[a] for a in TT if s[a]["reset"] == "pulse"]
    nores = [NAME[a] for a in TT if s[a]["reset"] == "none"]
    unchopped = [NAME[a] for a in TT if not s[a]["chopper"]]
    if pulse:
        a = "array $A$ (device\ntile); pulse reset\n$\\leq 62$/weight" + (f"\n(not {', '.join(nores)})" if nores else "")
    else:
        a = "array $A$\n(device tile);\nno reset"
    prob = "pulse probabilities\nfrom $c\\odot x$, $\\delta$\n($BL=31$, clipped at 1)" + (
        f"\n($c=1$ in {', '.join(unchopped)})" if unchopped else "")
    key = ["Selected settings:"] + [
        f"{NAME[k]}: " + ("pulse reset of $A$" if s[k]["reset"] == "pulse" else "no reset of $A$") + "; "
        + ("chopper signs $c$" if s[k]["chopper"] else "$c=1$ (no chopper)") for k in TT]
    return a, prob, "\n".join(key)


def chopped(settings=None):
    s = settings or SETTINGS
    return tuple(a for a in TT if s[a]["chopper"])


A_LABEL, PROB_LABEL, KEY = labels()
KEY_POS = (3.30, 2.24)            # the key "Selected settings": top left of panel (b), below its title
# id, panel, x0, y0, w, h (inches), kind, label, algorithms, the simulator state it stands for (AnalogLinear attribute or None)
BOXES = [
    ("a_W", "a", 1.90, 1.10, 1.05, 0.60, "device", "weight array $W$\n(device tile)", ("sgd",), "C"),
    ("a_read", "a", 1.90, 1.82, 1.05, 0.40, "read", "reads $Wx$, $W^{\\top}\\delta$:\nideal fp32", ("sgd",), None),
    ("a_prob", "a", 0.05, 1.10, 1.40, 0.60, "digital", "pulse probabilities\nfrom $x$, $\\delta$ ($BL=31$\nslots, clipped at 1)", ("sgd",), None),
    ("a_net", "a", 0.05, 1.82, 1.40, 0.40, "digital", "biases, norms, attention\nproducts, back-propagation", ("sgd",) + TT, "bias"),
    ("b_A", "b", 3.30, 0.10, 1.00, 0.66, "device", A_LABEL, TT, "A"),
    ("b_readA", "b", 4.55, 0.10, 0.80, 0.66, "read", "column read\nof $A$:\nideal fp32", TT, None),
    ("b_H", "b", 5.60, 0.10, 0.85, 0.66, "digital", "buffer $H$;\nchopper $c$;\nAGAD's $p$, $p^{\\mathrm{ref}}$", TT, "H"),
    ("b_prob", "b", 3.30, 1.10, 1.30, 0.60, "digital", PROB_LABEL, TT, None),
    ("b_C", "b", 5.40, 1.10, 1.05, 0.60, "device", "weight array $C$\n(device tile)", TT, "C"),
    ("b_read", "b", 5.40, 1.82, 1.05, 0.40, "read", "reads $Cx$, $C^{\\top}\\delta$:\nideal fp32", TT, None),
]
# the digital state the H box also names (chopper signs: the algorithms SETTINGS gives a chopper; AGAD's averages)
H_ALSO = {"chop": chopped(), "P": ("agad",), "Pref": ("agad",)}
# from, to, kind (device: pulses through the device model; read; digital), label, label position (inches) or None, and the
# straight line the arrow follows: ("x", value) vertical or ("y", value) horizontal, between the two boxes' facing sides
ARROWS = [
    ("a_prob", "a_W", "device", "pulses", (1.67, 1.50), ("y", 1.40)),
    ("a_W", "a_read", "read", None, None, ("x", 2.425)),
    ("b_prob", "b_A", "device", "pulses into $A$\n($10\\times$ the SGD rate)", (4.48, 0.93), ("x", 3.80)),
    ("b_A", "b_readA", "read", None, None, ("y", 0.43)),
    ("b_readA", "b_H", "digital", None, None, ("y", 0.43)),
    ("b_H", "b_C", "device", "$|H|\\geq 1$: up to\n31 pulses into $C$", (5.45, 0.93), ("x", 6.02)),
    ("b_C", "b_read", "read", None, None, ("x", 5.925)),
]
TITLES = [("(a) plain SGD", (0.05, 2.28)), ("(b) TTv2, c-TTv2 and AGAD", (3.30, 2.28))]
LEGEND = [("device", "simulated as a device: state, bounds,\nnoise and drift; every pulse counted", (0.05, 0.56)),
          ("digital", "digital, exact fp32", (0.05, 0.32)),
          ("read", "ideal fp32 read (the energy projection\nprices it as a finite-precision analog read)", (0.05, 0.06))]


def ends(b0, b1, along):
    """The arrow from box b0 to box b1 along a vertical (x) or horizontal (y) line, between their facing sides."""
    axis, v = along
    if axis == "x":
        up = b1[3] > b0[3]
        return (v, b0[3] + (b0[5] if up else 0)), (v, b1[3] + (0 if up else b1[5]))
    right = b1[2] > b0[2]
    return (b0[2] + (b0[4] if right else 0), v), (b1[2] + (0 if right else b1[4]), v)


def draw(boxes=BOXES, arrows=ARROWS, key=None):
    fig = plt.figure(figsize=(W_IN, H_IN))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W_IN)
    ax.set_ylim(0, H_IN)
    ax.axis("off")
    texts = {}
    by = {b[0]: b for b in boxes}
    for b in boxes:
        bid, _, x0, y0, w, h, kind, label = b[:8]
        fc, ec, ls = STYLE[kind]
        ax.add_patch(FancyBboxPatch((x0, y0), w, h, boxstyle="round,pad=0,rounding_size=0.05", fc=fc, ec=ec, ls=ls, lw=0.9))
        texts[bid] = ax.text(x0 + w / 2, y0 + h / 2, label, ha="center", va="center", fontsize=FS, linespacing=1.15)
    for i, (a, b, kind, label, pos, along) in enumerate(arrows):
        p0, p1 = ends(by[a], by[b], along)
        ec, ls = STYLE[kind][1], STYLE[kind][2]
        ax.annotate("", xy=p1, xytext=p0, arrowprops=dict(arrowstyle="-|>", color=ec, lw=1.0, ls=ls, shrinkA=1, shrinkB=1,
                                                          mutation_scale=7))
        if label:
            texts[f"arrow{i}"] = ax.text(pos[0], pos[1], label, ha="center", va="center", fontsize=FS - 0.5, color=ec,
                                         linespacing=1.1)
    texts["settings"] = ax.text(KEY_POS[0], KEY_POS[1], KEY if key is None else key, ha="left", va="top",
                                fontsize=FS - 0.5, linespacing=1.15)
    for t, (x, y) in TITLES:
        texts[t] = ax.text(x, y, t, ha="left", va="bottom", fontsize=FS + 1, weight="bold")
    for kind, label, (x, y) in LEGEND:
        fc, ec, ls = STYLE[kind]
        ax.add_patch(FancyBboxPatch((x, y + 0.03), 0.22, 0.13, boxstyle="round,pad=0,rounding_size=0.03", fc=fc, ec=ec, ls=ls, lw=0.9))
        texts["legend:" + kind] = ax.text(x + 0.30, y + 0.095, label, ha="left", va="center", fontsize=FS - 0.5, linespacing=1.1)
    ax.plot([3.13, 3.13], [0.05, 2.42], color="#999999", lw=0.6)
    return fig, ax, texts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    fig, _, _ = draw()
    os.makedirs(a.out, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(a.out, f"fig_arch.{ext}"), dpi=150)
    print("fig_arch written")


if __name__ == "__main__":
    main()
