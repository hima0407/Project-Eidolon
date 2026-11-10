"""Study 14 - Is the advantage real? Monte-Carlo over every assumption we could not pin down.

Common-random-number design: assumptions that affect both aircraft the same way (fitted drag
increment, mass calibration, BSFC, propeller installation) get the SAME draw for both, so only
differences in design and in aircraft-specific unknowns move the ratio. Aircraft-specific
unknowns are drawn separately, deliberately wide, and biased against Eidolon where in doubt.
"""
from _common import ROOT, style, write_json, write_csv
import copy, dataclasses
import numpy as np
import matplotlib.pyplot as plt

from eidolon.design import eidolon_v1, hansa_closed
from eidolon.model import build, V_CRUISE, CRUISE_ALT
from eidolon import structures as st

OUT = style.out("14_sensitivity")
N = 400
rng = np.random.default_rng(2026)


def run(ac, dcd, allow, eta, bsfc_f, extra=0.0):
    M = build(ac, drag_cal=dcd, allowance_kg=allow, eta_install=eta, extra_empty_kg=extra)
    M.plane.engine = dataclasses.replace(M.plane.engine, bsfc_g_kwh=M.plane.engine.bsfc_g_kwh * bsfc_f)
    P, W = M.plane, M.W
    return P.fuel_per_100km(W, V_CRUISE, CRUISE_ALT)[0], P.range_km(W, M.fuel_kg, V_CRUISE, CRUISE_ALT)[0]


def sample(e0, h0, pessimistic=True):
    """One Monte-Carlo pass. pessimistic=True biases every aircraft-specific unknown against Eidolon;
    pessimistic=False draws them centred on the design values (neutral priors)."""
    rows = []
    for i in range(N):
        dcd = rng.uniform(0.0032, 0.0122)           # spans the 65-85 % cruise-power calibration range (study 02)
        mcal = rng.normal(st.CLASS_ALLOWANCE_KG, st.CLASS_ALLOWANCE_SD)   # class allowance, shared draw
        eta = rng.uniform(0.87, 0.95)
        bsfc = rng.normal(1.0, 0.05)
        e = copy.deepcopy(e0); h = copy.deepcopy(h0)
        if pessimistic:
            e.wing_laminar_fraction = rng.uniform(0.10, 0.40)   # contamination, rain, bugs, production waviness
            e.gear.main_leg_chord *= rng.uniform(1.0, 2.5)      # fairing less clean than drawn
            e.canopy_dq_m2 *= rng.uniform(1.0, 1.4)
            extra = rng.uniform(-5, 20)                         # Eidolon-only mass growth (novel parts), skewed heavy
        else:
            e.wing_laminar_fraction = rng.uniform(0.25, 0.45)
            e.gear.main_leg_chord *= rng.uniform(1.0, 1.5)
            e.canopy_dq_m2 *= rng.uniform(0.9, 1.2)
            extra = rng.normal(0.0, 8.0)                        # symmetric, about the LOO scatter of the mass method
        h.wing_laminar_fraction = rng.uniform(0.05, 0.25)
        h.gear.main_leg_thickness *= rng.uniform(0.35, 1.0)     # Hansa legs may be partly faired already
        fe, re = run(e, dcd, mcal, eta, bsfc, extra)
        fh, rh = run(h, dcd, mcal, eta, bsfc)
        rows.append((dcd, mcal, eta, bsfc, e.wing_laminar_fraction, extra, h.wing_laminar_fraction, fe, fh, re, rh))
    return np.array(rows), rows


def summarise(A):
    fuel_ratio = A[:, 7] / A[:, 8] - 1
    range_ratio = A[:, 9] / np.maximum(A[:, 10], 1) - 1
    pc = lambda x: {"p05": 100 * np.percentile(x, 5), "median": 100 * np.median(x), "p95": 100 * np.percentile(x, 95)}
    return fuel_ratio, range_ratio, {"fuel_burn_change_pct": pc(fuel_ratio), "P(Eidolon burns less fuel)": float(np.mean(fuel_ratio < 0)),
                                     "range_change_pct": pc(range_ratio), "P(Eidolon flies further with 2 crew)": float(np.mean(range_ratio > 0))}


def main():
    e0, h0 = eidolon_v1().model.ac, hansa_closed().model.ac
    A, rows = sample(e0, h0, pessimistic=True)
    An, _ = sample(e0, h0, pessimistic=False)
    write_csv(OUT / "monte_carlo.csv", ["dCD0", "class_allowance_kg", "eta_install", "bsfc_factor", "eid_laminar", "eid_extra_kg",
                                       "hansa_laminar", "eid_L100", "hansa_L100", "eid_range", "hansa_range"], rows)
    fuel_ratio, range_ratio, res = summarise(A)
    _, range_n, res_n = summarise(An)
    # break-even: how much extra empty mass Eidolon can carry before its 2-crew range drops to Hansa-NG's
    M0 = build(e0); Mh = build(h0)
    r_h = Mh.plane.range_km(Mh.W, Mh.fuel_kg, V_CRUISE, CRUISE_ALT)[0]
    xs = np.arange(0, 12.5, 0.5)
    rs = [build(e0, extra_empty_kg=x) for x in xs]
    rs = np.array([m.plane.range_km(m.W, m.fuel_kg, V_CRUISE, CRUISE_ALT)[0] for m in rs])
    be = float(np.interp(0, (rs - r_h)[::-1], xs[::-1]))
    res = {"N": N, **res, "neutral_priors": res_n,
           "range_break_even_extra_empty_kg": be, "range_km_per_kg_empty": float((rs[0] - rs[4]) / xs[4])}
    write_json(OUT / "monte_carlo_summary.json", res)

    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
    for ax, data, title, lab in ((axs[0], 100 * fuel_ratio, "Fuel per 100 km at 200 km/h", "Eidolon vs Hansa-NG [%]"),
                                 (axs[1], 100 * range_ratio, "Range with 2 crew + bag", "Eidolon vs Hansa-NG [%]")):
        bins = np.linspace(-100, 100, 41) if "Range" in title else 32
        ax.hist(np.clip(data, -100, 100), bins=bins, color=style.EIDOLON, alpha=0.85, edgecolor=style.SURFACE, linewidth=1)
        ax.axvline(0, color=style.INK2, lw=1.2)
        for p, ls in ((5, ":"), (50, "-"), (95, ":")):
            v = np.percentile(data, p)
            ax.axvline(v, color=style.HANSA, ls=ls, lw=1.6)
            ax.text(v, ax.get_ylim()[1] * 0.93, f" P{p}\n {v:+.0f}%", fontsize=8.5, color=style.INK2)
        ax.set_title(title); ax.set_xlabel(lab); ax.set_ylabel("samples"); ax.grid(axis="x", visible=False)
    axs[1].hist(np.clip(100 * range_n, -100, 100), bins=np.linspace(-100, 100, 41), histtype="step", color=style.INK2, lw=1.3, label="neutral priors")
    axs[1].legend(loc="upper left", fontsize=8.5, frameon=False)
    fig.suptitle(f"{N} Monte-Carlo designs, biased against Eidolon:  P(less fuel) = {res['P(Eidolon burns less fuel)']:.0%},  "
                 f"P(more range) = {res['P(Eidolon flies further with 2 crew)']:.0%}  (neutral priors: "
                 f"{res_n['P(Eidolon flies further with 2 crew)']:.0%})", x=0.01, ha="left", fontsize=12, weight="semibold")
    fig.tight_layout()
    style.note(fig, "Shared draws: fitted dCD0, class mass allowance, BSFC, propeller installation. Separate draws: laminar extent, "
               "fairing quality, Eidolon mass growth (-5..+20 kg), Hansa-NG gear legs. "
               f"Range break-even: Eidolon may grow {be:.1f} kg over its mass estimate ({res['range_km_per_kg_empty']:.0f} km per kg).")
    style.save(fig, OUT / "monte_carlo.png")

    # tornado: one-at-a-time on the Eidolon fuel burn
    base = dict(dcd=0.00825, mcal=st.CLASS_ALLOWANCE_KG, eta=0.92, bsfc=1.0, lam=0.35, extra=0.0)
    def f(**kw):
        p = {**base, **kw}; a = copy.deepcopy(e0); a.wing_laminar_fraction = p["lam"]
        return run(a, p["dcd"], p["mcal"], p["eta"], p["bsfc"], p["extra"])
    f0, r0 = f()
    tests = [("Fitted dCD0  0.0032 / 0.0122", dict(dcd=0.0032), dict(dcd=0.0122)),
             ("BSFC  -10 % / +10 %", dict(bsfc=0.9), dict(bsfc=1.1)),
             ("Prop installation 0.95 / 0.87", dict(eta=0.95), dict(eta=0.87)),
             ("Wing laminar extent 0.45 / 0.10", dict(lam=0.45), dict(lam=0.10)),
             ("Empty mass  -10 / +20 kg", dict(extra=-10), dict(extra=20))]
    fig, axs = plt.subplots(1, 2, figsize=(12, 3.6))
    for j, (ax, idx, title) in enumerate(((axs[0], 0, "Eidolon fuel per 100 km [L]"), (axs[1], 1, "Eidolon range, 2 crew [km]"))):
        ref = (f0, r0)[idx]
        for i, (lab, lo, hi) in enumerate(tests):
            a, b = f(**lo)[idx] - ref, f(**hi)[idx] - ref
            ax.barh(i, a, color=style.GOOD if (a < 0) == (idx == 0) else style.BAD, height=0.55)
            ax.barh(i, b, color=style.GOOD if (b < 0) == (idx == 0) else style.BAD, height=0.55)
        ax.set_yticks(range(len(tests)), [t[0] for t in tests] if j == 0 else [""] * len(tests))
        ax.axvline(0, color=style.INK2); ax.invert_yaxis(); ax.grid(axis="y", visible=False)
        ax.set_title(f"{title}: baseline {ref:.3g}")
    style.note(fig, "One-at-a-time swing about the baseline. Range is most sensitive to empty mass: 1 kg of structure = 1 kg of fuel.")
    style.save(fig, OUT / "tornado.png")
    print(res)


if __name__ == "__main__":
    main()
