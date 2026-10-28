"""Lane ME bench analysis (standard library only).

python -B analyze_bench.py --parts            totals of PARTS.json
python -B analyze_bench.py LOG.csv [--lead 0] fit the device spec of one lead from the memistor_bench.ino log
python -B analyze_bench.py --selftest         recover a known spec from a synthetic log (and miss a planted wrong one)

Fit (lead k): conductance G = 1000 / R_mOhm after each pulse. Steps dG of equal-charge pulses, split up (plate) / down.
u = position in [-1, 1] across the full range seen in the log (protocol step 2 sweeps bare -> plated). step_up = s_up (1 - gamma_up u), step_dn = s_dn (1 + gamma_dn u) by least
squares over the steps that stay 2 median steps inside the range (a bound truncates a step); asym = (s_up - s_dn) / ((s_up + s_dn) / 2); c2c = residual std / mean step; levels = range / mean step; drift from the
R-only reads: tau_s = (G - G_min) / (-dG/dt) at the mean G; energy per step = mean energy_uJ.
"""
import csv
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def parts():
    d = json.load(open(os.path.join(HERE, "PARTS.json"), encoding="utf-8"))
    allnew = sum(p["usd"] for p in d["parts"])
    nohh = sum(p["usd"] for p in d["parts"] if not p["household"])
    print(json.dumps(dict(total_all_new_usd=round(allnew, 2), total_without_household_usd=round(nohh, 2))))
    return allnew, nohh


def linfit(x, y):
    n = len(x)
    mx, my = sum(x) / n, sum(y) / n
    sxx = sum((a - mx) ** 2 for a in x)
    sxy = sum((a - mx) * (b - my) for a, b in zip(x, y))
    b = sxy / sxx if sxx > 0 else 0.0
    return my - b * mx, b


def fit(rows, lead):
    seq = [r for r in rows if int(r["k"]) == lead]
    g_prev, ups, dns, reads, en = None, [], [], [], []
    for r in seq:
        g = 1000.0 / float(r["R_mOhm"])
        if r["cmd"] in ("P", "D") and g_prev is not None:
            (ups if r["cmd"] == "P" else dns).append((g_prev, g - g_prev))
            en.append(float(r["energy_uJ"]))
        if r["cmd"] == "R":
            reads.append((float(r["t_ms"]) / 1000.0, g))
        g_prev = g
    allg = [a for a, _ in ups + dns]
    gmin, gmax = min(allg), max(allg)
    u = lambda g: 2 * (g - gmin) / (gmax - gmin) - 1
    med = sorted(abs(d) for _, d in ups + dns)[len(ups + dns) // 2]
    inside = lambda g, d: min(g, g + d) > gmin + 2 * med and max(g, g + d) < gmax - 2 * med  # not at a bound
    ups = [(g, d) for g, d in ups if inside(g, d)]
    dns = [(g, d) for g, d in dns if inside(g, d)]
    a_up, b_up = linfit([u(g) for g, _ in ups], [d for _, d in ups])
    a_dn, b_dn = linfit([u(g) for g, _ in dns], [-d for _, d in dns])
    s_up, s_dn = a_up, a_dn
    res = [d - (a_up + b_up * u(g)) for g, d in ups] + [-d - (a_dn + b_dn * u(g)) for g, d in dns]
    mstep = 0.5 * (s_up + s_dn)
    c2c = math.sqrt(sum(x * x for x in res) / max(1, len(res) - 4)) / mstep
    out = dict(levels=(gmax - gmin) / mstep, asym=(s_up - s_dn) / mstep, gamma_up=-b_up / s_up, gamma_dn=b_dn / s_dn,
               c2c=c2c, energy_per_step_uJ=sum(en) / max(1, len(en)), n_up=len(ups), n_dn=len(dns))
    if len(reads) >= 3:
        t0, b = linfit([t for t, _ in reads], [g for _, g in reads])
        gm = sum(g for _, g in reads) / len(reads)
        out["drift_tau_s"] = (gm - gmin) / -b if b < 0 else math.inf
    out["passes_32_levels"] = (out["levels"] >= 32 and abs(out["asym"]) <= 0.10 and abs(out["gamma_up"]) <= 0.3
                               and abs(out["gamma_dn"]) <= 0.3 and out["c2c"] <= 0.5)
    return out


def synth(levels=80, asym=0.08, gamma=0.2, c2c=0.3, seed=1, n=64):
    rnd = random.Random(seed)
    gmin, gmax = 0.2, 2.0
    k = (gmax - gmin) / levels
    g, t, rows = gmin, 0, []
    # protocol step 2 (the full plating range from bare), back to mid-range, then step 3 (3 x 64 down, 64 up)
    sweep = ["P"] * (2 * levels) + ["D"] * levels
    for cmd in sweep + (["D"] * n + ["P"] * n) * 3:
        if True:
            uu = 2 * (g - gmin) / (gmax - gmin) - 1
            if cmd == "P":
                st = k * (1 + asym / 2) * (1 - gamma * uu)
            else:
                st = -k * (1 - asym / 2) * (1 + gamma * uu)
            g = min(gmax, max(gmin, g + st + c2c * k * rnd.gauss(0, 1)))
            t += 300
            rows.append(dict(t_ms=t, cmd=cmd, k=0, charge_uC=1000, energy_uJ=1500, ms=200, R_mOhm=1000.0 / g))
    for i in range(60):
        g -= 1e-4
        t += 60000
        rows.append(dict(t_ms=t, cmd="R", k=0, charge_uC=0, energy_uJ=0, ms=0, R_mOhm=1000.0 / g))
    return rows


def selftest():
    f = fit(synth(), 0)
    ok = (abs(f["asym"] - 0.08) < 0.03 and abs(f["gamma_up"] - 0.2) < 0.08 and abs(f["gamma_dn"] - 0.2) < 0.08
          and abs(f["c2c"] - 0.3) < 0.08)
    planted = fit(synth(asym=-0.08), 0)  # the fit must see the sign of a planted asymmetry
    caught = planted["asym"] < 0
    print(json.dumps(dict(fit=f, recovers_known_spec=ok, planted_negative_asym_seen=caught)))
    return ok and caught


def main():
    if "--parts" in sys.argv:
        parts()
        return
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    lead = int(sys.argv[sys.argv.index("--lead") + 1]) if "--lead" in sys.argv else 0
    with open(sys.argv[1], newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(l for l in f if l[:1].isdigit() or l.startswith("t_ms"))]
    print(json.dumps(fit(rows, lead), indent=1))


if __name__ == "__main__":
    main()
