"""Study 22 - Study 14's Monte Carlo, re-run on the final carbon aircraft.

Same priors and the same common-random-number design as study 14 (glass first closure), plus one
carbon-specific unknown: how much of the modelled carbon saving is actually realised in production.
Pessimistic priors assume only 50-100 % of it; neutral priors centre it on 100 % with 15 % scatter.
Study 14 is left unchanged so the glass result stays reproducible.

Part B repeats study 09's six-tail screen on the carbon airframe, to check the tail choice still holds.
"""
from _common import ROOT, style, write_json, write_csv
import copy, dataclasses
import numpy as np
import matplotlib.pyplot as plt

from eidolon.design import eidolon_v1, eidolon_final, hansa_closed
from eidolon.model import build, V_CRUISE, CRUISE_ALT
from eidolon import structures as st

OUT = style.out("22_monte_carlo_carbon")
N = 400
rng = np.random.default_rng(2026)


def run(ac, dcd, allow, eta, bsfc_f, extra=0.0):
    M = build(ac, drag_cal=dcd, allowance_kg=allow, eta_install=eta, extra_empty_kg=extra)
    M.plane.engine = dataclasses.replace(M.plane.engine, bsfc_g_kwh=M.plane.engine.bsfc_g_kwh * bsfc_f)
    P, W = M.plane, M.W
    return P.fuel_per_100km(W, V_CRUISE, CRUISE_ALT)[0], P.range_km(W, M.fuel_kg, V_CRUISE, CRUISE_ALT)[0]


def sample(e0, h0, saving_kg, pessimistic=True):
    rows = []
    for i in range(N):
        dcd = rng.uniform(0.0032, 0.0122)
        mcal = rng.normal(st.CLASS_ALLOWANCE_KG, st.CLASS_ALLOWANCE_SD)
        eta = rng.uniform(0.87, 0.95)
        bsfc = rng.normal(1.0, 0.05)
        e = copy.deepcopy(e0); h = copy.deepcopy(h0)
        if pessimistic:
            e.wing_laminar_fraction = rng.uniform(0.10, 0.40)
            e.gear.main_leg_chord *= rng.uniform(1.0, 2.5)
            e.canopy_dq_m2 *= rng.uniform(1.0, 1.4)
            extra = rng.uniform(-5, 20)
            realised = rng.uniform(0.5, 1.0)          # only half to all of the carbon saving turns up
        else:
            e.wing_laminar_fraction = rng.uniform(0.25, 0.45)
            e.gear.main_leg_chord *= rng.uniform(1.0, 1.5)
            e.canopy_dq_m2 *= rng.uniform(0.9, 1.2)
            extra = rng.normal(0.0, 8.0)
            realised = float(np.clip(rng.normal(1.0, 0.15), 0.4, 1.3))
        extra += (1.0 - realised) * saving_kg
        h.wing_laminar_fraction = rng.uniform(0.05, 0.25)
        h.gear.main_leg_thickness *= rng.uniform(0.35, 1.0)
        fe, re = run(e, dcd, mcal, eta, bsfc, extra)
        fh, rh = run(h, dcd, mcal, eta, bsfc)
        rows.append((dcd, mcal, eta, bsfc, e.wing_laminar_fraction, realised, extra, h.wing_laminar_fraction, fe, fh, re, rh))
    return np.array(rows), rows


def summarise(A):
    fuel = A[:, 8] / A[:, 9] - 1
    rng_ = A[:, 10] / np.maximum(A[:, 11], 1) - 1
    pc = lambda x: {"p05": 100 * np.percentile(x, 5), "median": 100 * np.median(x), "p95": 100 * np.percentile(x, 95)}
    return fuel, rng_, {"fuel_burn_change_pct": pc(fuel), "P(Eidolon burns less fuel)": float(np.mean(fuel < 0)),
                        "range_change_pct": pc(rng_), "P(Eidolon flies further with 2 crew)": float(np.mean(rng_ > 0))}


def main():
    e0, h0 = eidolon_final().model.ac, hansa_closed().model.ac
    saving = build(eidolon_v1().model.ac).empty_kg - build(e0).empty_kg
    A, rows = sample(e0, h0, saving, pessimistic=True)
    An, _ = sample(e0, h0, saving, pessimistic=False)
    write_csv(OUT / "monte_carlo.csv", ["dCD0", "class_allowance_kg", "eta_install", "bsfc_factor", "eid_laminar",
                                       "carbon_saving_realised", "eid_extra_kg", "hansa_laminar",
                                       "eid_L100", "hansa_L100", "eid_range", "hansa_range"], rows)
    fuel, rr, res = summarise(A)
    fn, rn, res_n = summarise(An)

    Mh = build(h0); r_h = Mh.plane.range_km(Mh.W, Mh.fuel_kg, V_CRUISE, CRUISE_ALT)[0]
    xs = np.arange(0, 60.5, 0.5)
    rs = np.array([(lambda m: m.plane.range_km(m.W, m.fuel_kg, V_CRUISE, CRUISE_ALT)[0])(build(e0, extra_empty_kg=x)) for x in xs])
    be = float(np.interp(0, (rs - r_h)[::-1], xs[::-1]))
    res = {"N": N, "aircraft": "eidolon_final (carbon)", "modelled_carbon_saving_kg": float(saving), **res,
           "neutral_priors": res_n, "range_break_even_extra_empty_kg": be}
    write_json(OUT / "monte_carlo_summary.json", res)

    fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
    for ax, d, dn, title in ((axs[0], 100 * fuel, 100 * fn, "Fuel per 100 km at 200 km/h"),
                             (axs[1], 100 * rr, 100 * rn, "Range with 2 crew + bag")):
        bins = np.linspace(-100, 100, 41) if "Range" in title else 32
        ax.hist(np.clip(d, -100, 100), bins=bins, color=style.EIDOLON, alpha=0.85, edgecolor=style.SURFACE, linewidth=1,
                label="pessimistic priors")
        ax.hist(np.clip(dn, -100, 100), bins=bins, histtype="step", color=style.INK2, lw=1.3, label="neutral priors")
        ax.axvline(0, color=style.INK2, lw=1.2)
        for p, ls in ((5, ":"), (50, "-"), (95, ":")):
            v = np.percentile(d, p)
            ax.axvline(v, color=style.HANSA, ls=ls, lw=1.6)
            ax.text(v, ax.get_ylim()[1] * 0.93, f" P{p}\n {v:+.0f}%", fontsize=8.5, color=style.INK2)
        ax.set_title(title); ax.set_xlabel("Eidolon (carbon) vs Hansa-NG [%]"); ax.set_ylabel("samples"); ax.grid(axis="x", visible=False)
    axs[1].legend(loc="upper left", fontsize=8.5, frameon=False)
    fig.suptitle(f"{N}+{N} Monte-Carlo designs, carbon airframe:  P(less fuel) = {res['P(Eidolon burns less fuel)']:.0%},  "
                 f"P(more range) = {res['P(Eidolon flies further with 2 crew)']:.0%} pessimistic, "
                 f"{res_n['P(Eidolon flies further with 2 crew)']:.0%} neutral", x=0.01, ha="left", fontsize=12, weight="semibold")
    fig.tight_layout()
    style.note(fig, "Priors as study 14, plus the carbon saving realised: 50-100 % (pessimistic) or 100 % +/- 15 % (neutral). "
               f"Range break-even: Eidolon may grow {be:.1f} kg over its mass estimate.")
    style.save(fig, OUT / "monte_carlo.png")
    print(res)
    tail_screen_carbon()


def tail_screen_carbon():
    import importlib, math
    from eidolon.aircraft import eidolon
    from eidolon.design import BASELINE
    from eidolon.empennage import PRESETS, apply, TDPF_REQUIRED
    s9 = importlib.import_module("09_tail_configuration")
    base = eidolon(**BASELINE); base.airframe = "carbon"
    out = {}
    for n in PRESETS:
        r = s9.evaluate(apply(base, n)); r.pop("closed")
        out[n] = {k: r[k] for k in ("Sh", "f100", "range", "v_rot", "v_lof", "TDPF", "alpha_wake", "alpha_stall", "deep_stall_risk")}
        out[n]["TDPF_x1e6"] = None if math.isnan(r["TDPF"]) else r["TDPF"] * 1e6
        out[n]["rotates_before_liftoff"] = bool(r["v_rot"] <= r["v_lof"] * 1.001)
        out[n]["passes_spin_screen"] = bool(not math.isnan(r["TDPF"]) and r["TDPF"] >= TDPF_REQUIRED)
        print(f"  {n:40s} Sh {r['Sh']:.2f}  TDPF {out[n]['TDPF_x1e6']}  rotates {out[n]['rotates_before_liftoff']}  deep stall {r['deep_stall_risk']}")
    write_json(OUT / "tail_screen_carbon.json", {"tdpf_required_x1e6": TDPF_REQUIRED * 1e6, "results": out})


if __name__ == "__main__":
    main()
