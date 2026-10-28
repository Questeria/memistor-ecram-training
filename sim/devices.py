"""The device catalog of lane ME: published (or estimated, labelled) specs mapped onto DeviceSpec.

Each entry: spec (DeviceSpec fields), source, label (PUBLISHED-FIT | PARTLY-PUBLISHED | CLAIM+ESTIMATE |
ESTIMATE), and notes on every mapped number. python -B devices.py writes ../records/CATALOG.json.
"""
import json
import math
import os
import sys


def anl_of_gamma(g):
    """Asymmetric nonlinearity factor (Chen et al. 2023 definition) of the model's symmetric soft step:
    potentiation from u=-1 for N/2 pulses of 2/N (gamma k n = gamma); ANL = u_P(N/2) = -u_D(N/2)."""
    if g == 0:
        return 0.0
    return (1.0 - (1.0 + g) * math.exp(-g)) / g


def gamma_for_anl(anl):
    lo, hi = 0.0, 1.9  # anl_of_gamma rises on [0, ~1.9] (max ~0.30), then falls
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if anl_of_gamma(mid) < anl:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# Time per training sample of a pulse train of 31 slots, used only to convert a physical retention time
# into the model's drift constant (tau in batches of 128 samples).
BATCH = 128

CATALOG = {
    "widrow1960_claimed": dict(
        spec=dict(n_states=1000, asym=0.05, gamma_up=0.1, gamma_dn=0.1, c2c=0.3, d2d=0.2, bound_d2d=0.1,
                  ref_err=0.02),
        label="CLAIM+ESTIMATE",
        source="Widrow, Pierce and Angell 1961 (TR 1552-2/1851-1), quoted in Wikipedia 'Memistor': 'thousands of "
               "possible analog storage levels', '100 ohms to 1 ohm', 'about 10 seconds with several milliamperes'; "
               "Widrow 1960 TR 1553-2 via Mouttet arXiv:1012.5124: near-linear conductance vs plating charge, "
               "brighteners to eliminate hysteresis",
        notes="n_states 1000 = the low end of 'thousands' (claimed, never measured in a modern sense). asym, gamma, "
              "c2c, d2d, ref_err are ESTIMATES (no 1960s figure survives in readable form). Drift: the ideal "
              "'stays put indefinitely' is taken as claimed (tau = inf); the pessimistic twin below has drift."),
    "widrow1960_pessimistic": dict(
        spec=dict(n_states=100, asym=0.2, gamma_up=0.3, gamma_dn=0.3, c2c=1.0, d2d=0.3, bound_d2d=0.2,
                  ref_err=0.05, tau_steps=1000.0),
        label="ESTIMATE",
        source="Gaines 1967: 'electro-chemical stores ... are unreliable or require sophisticated external circuitry'",
        notes="Every number an ESTIMATE spanning Gaines's verdict: 100 usable levels, 20 % up/down asymmetry, "
              "write noise of one step, drift tau = 1000 batches."),
    "ecram_li_tang2018": dict(
        spec=dict(n_states=2 / 0.002, asym=0.0, asym_d2d=0.02, gamma_up=0.1153, gamma_dn=0.5085, c2c=0.3,
                  d2d=0.1, bound_d2d=0.05, ref_err=0.02),
        label="PUBLISHED-FIT",
        source="Tang et al., IEDM 2018 (Li-WO3 ECRAM, 1000 states, 5 ns pulses); parameters of the fit "
               "EcRamPresetDevice in the aihwkit documentation (dw_min 0.002 over range 2, gamma_up 0.1153, "
               "gamma_down 0.5085, dw_min_std 0.3, dw_min_dtod 0.1, up_down_dtod 0.01, w_max/min_dtod 0.05)",
        notes="asym_d2d = 2 x up_down_dtod (aihwkit's up = dw(1+up_down)). ref_err 0.02 assumed. Retention "
              "'good' (tau inf)."),
    "ecram_mo_kim2019": dict(
        spec=dict(n_states=2 / 2.8214e-4, asym=0.0, asym_d2d=0.02, gamma_up=0.4152, gamma_dn=0.7342, c2c=2.0,
                  d2d=0.1, bound_d2d=0.05, ref_err=0.02),
        label="PUBLISHED-FIT",
        source="Kim et al., IEDM 2019 (metal-oxide CMOS-compatible ECRAM); aihwkit EcRamMOPresetDevice "
               "(dw_min 2.8214e-4, gamma_up 0.4152, gamma_down 0.7342, dw_min_std 2.0)",
        notes="~7,089 small, noisy steps (write noise 2x the step)."),
    "protonic_onen2022": dict(
        spec=dict(n_states=1000, asym=0.05, gamma_up=0.2, gamma_dn=0.2, c2c=0.3, d2d=0.1, bound_d2d=0.05,
                  ref_err=0.02),
        label="PARTLY-PUBLISHED",
        source="Onen et al., Science 377, 539 (2022): 1000 protonating (10 V) then 1000 deprotonating (-8.5 V) "
               "5 ns pulses, 'nearly linear and symmetric', 20x dynamic range, retention ~100 s, 1e5 pulses "
               "endurance over 30 h, ~2.5 fJ per pulse (gate charging) and ~15 aJ (proton transfer)",
        notes="n_states 1000 from the 1000-pulse sweep (published). asym 0.05, gamma 0.2, c2c 0.3 are ESTIMATES "
              "('nearly linear and symmetric'; no noise figure in the text). Retention 100 s >> a training "
              "step at ns pulses: tau inf."),
    "wox_ysz_chen2023": dict(
        spec=dict(n_states=256, asym=0.0, gamma_up=gamma_for_anl(0.21), gamma_dn=gamma_for_anl(0.21),
                  c2c=0.008 * 256, d2d=0.023, bound_d2d=0.023, ref_err=0.02),
        label="PUBLISHED-FIT",
        source="Chen et al., Nat. Commun. 14, 6184 (2023), W/YSZ/WOx ECRAM 10x10 array: 256 states, ANL "
               "0.21 +- 0.05, cycle-to-cycle variation 0.8 % (of the range, the NeuroSim convention), "
               "device-to-device 2.3 %, open-loop write error 1.07 %, 100 ms write pulses",
        notes="gamma solved so the model's ANL = 0.21 (anl_of_gamma). c2c 0.008 of the range per pulse = "
              "0.008 x 256 = 2.05 steps (interpretation: NeuroSim's sigmaCtoC is relative to the range)."),
    "pencil_lead_today": dict(
        spec=dict(n_states=100, asym=0.1, gamma_up=0.3, gamma_dn=0.3, c2c=0.5, d2d=0.2, bound_d2d=0.2,
                  ref_err=0.05, tau_steps=940.0),
        label="ESTIMATE",
        source="this lane's estimate (PLAN.md section 'pencil lead built today'); to be replaced by the bench",
        notes="0.5 mm HB lead, 20 mm immersed, 5 ohm bare -> 0.5 ohm plated: Cu film 0 -> ~0.39 um, 0.33 C full "
              "range. 100 levels (read noise and morphology), plating efficiency ~0.9-0.95 vs stripping ~1 "
              "(asym 0.1), nucleation/stripping nonuniformity (gamma 0.3), write noise half a step, hand-made "
              "spread 20 %. Drift: Cu corrodes in aerated acid sulphate; central guess the full range is lost "
              "in ~10 h (tau 3.6e4 s); a 31-slot pulse train of ~10 ms slots is 0.3 s per sample, so "
              "tau = 3.6e4 / (0.3 x 128) = 940 batches."),
}


# Provenance of every simulated field (director's item d, 2026-10-25): MEASURED = a number printed in the paper from its
# measurement; FIT = a parameter fitted to measured curves by others (aihwkit presets) or by this lane (ANL -> gamma);
# CLAIM = the authors' wording without a measurement table; ESTIMATE = this lane's assumption; ASSUMED = a lane default
# used for every device (no source).
PROVENANCE = {
    "widrow1960_claimed": dict(n_states="CLAIM ('thousands of levels')", asym="ESTIMATE", gamma="ESTIMATE ('near linear': CLAIM)",
                               c2c="ESTIMATE", d2d="ESTIMATE", bound_d2d="ESTIMATE", ref_err="ASSUMED", drift="CLAIM (stays put)"),
    "widrow1960_pessimistic": dict(all="ESTIMATE"),
    "ecram_li_tang2018": dict(n_states="FIT (aihwkit; paper CLAIMS up to 1000 states)", asym="FIT (0 after symmetry shift)",
                              asym_d2d="FIT", gamma="FIT", c2c="FIT", d2d="FIT", bound_d2d="FIT", ref_err="ASSUMED",
                              drift="CLAIM ('good retention')"),
    "ecram_mo_kim2019": dict(n_states="FIT", asym="FIT", asym_d2d="FIT", gamma="FIT", c2c="FIT", d2d="FIT", bound_d2d="FIT",
                             ref_err="ASSUMED", drift="ASSUMED (none)"),
    "protonic_onen2022": dict(n_states="MEASURED (1000 + 1000 pulse sweep)", asym="ESTIMATE ('nearly symmetric': CLAIM)",
                              gamma="ESTIMATE ('nearly linear': CLAIM)", c2c="ESTIMATE (not reported)", d2d="ESTIMATE",
                              bound_d2d="ESTIMATE", ref_err="ASSUMED", drift="MEASURED ~100 s shown; tau inf ASSUMED"),
    "wox_ysz_chen2023": dict(n_states="MEASURED (256)", asym="MEASURED via ANL (0 global)", gamma="FIT (this lane, from ANL 0.21)",
                             c2c="MEASURED-INPUT (0.8 % used in their sim; range-relative reading is this lane's)",
                             d2d="MEASURED (2.3 %)", bound_d2d="ESTIMATE (= d2d)", ref_err="ASSUMED", drift="ASSUMED (none)"),
    "pencil_lead_today": dict(all="ESTIMATE"),
}
for _k, _v in PROVENANCE.items():
    CATALOG[_k]["provenance"] = _v


def main():
    out = dict(schema="altone.x1000.me.catalog.v1", batch=BATCH, entries=CATALOG,
               gamma_for_anl_0p21=gamma_for_anl(0.21), anl_check=anl_of_gamma(gamma_for_anl(0.21)))
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "records", "CATALOG.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write((json.dumps(out, indent=1, sort_keys=True) + "\n").encode("utf-8"))
    print(json.dumps({k: v["spec"] for k, v in CATALOG.items()}, indent=0)[:1500])


if __name__ == "__main__":
    main()
