"""Study 05 - Wing area and span: a carpet search over the closed design.

Every grid point is a fully closed aircraft (mass, tail sizing, CG, drag, propeller,
performance) - not just a constraint diagram. Objective and constraints:

  minimise   fuel per 100 km at 200 km/h, 1500 m          (the efficiency headline)
  subject to range >= 800 km with 2 x 77 kg + 10 kg, 45-min reserve (Hansa-NG model: ~710 km)
             V_S0 <= 81.5 km/h   (CS-VLA 49: 83 km/h CAS, minus 2 % model margin)
             ROC  >= 3.5 m/s     (beat Hansa-NG's 3.3)
             TO to 15 m <= 450 m (Hansa-NG brochure value)
Mass is the bottom-up model (study 01). With Raymer's statistical wing mass (first version of this
study) every extra metre of span looked expensive and the optimum sat at the shortest span; the
load-sized wing shows span is cheap (skins scale with area), so the optimum moves outboard.

The classical T/W - W/S constraint diagram (the team's original method) is also redrawn
here with the calibrated drag polar, so both views agree.
"""
from _common import ROOT, style, write_json, write_csv
import numpy as np
import matplotlib.pyplot as plt

from eidolon.aircraft import eidolon, G
from eidolon.design import close
from eidolon.model import V_CRUISE, CRUISE_ALT

OUT = style.out("05_wing_sizing")
VS0_MAX, ROC_MIN, TO_MAX, RANGE_MIN = 81.5, 3.5, 450.0, 800.0


def evaluate(S, b):
    c = close(eidolon("912iSc", S, b))
    M = c.model; P = M.plane; W = M.W
    return dict(S=S, b=b, AR=b * b / S,
                vs0=float(P.v_stall(W, M.polar.cl_max_land)) * 3.6,
                roc=P.max_roc(W, 0, 0, "takeoff")[0],
                to=P.takeoff_distance(W)[1],
                f100=P.fuel_per_100km(W, V_CRUISE, CRUISE_ALT)[0],
                rng=P.range_km(W, M.fuel_kg, V_CRUISE, CRUISE_ALT)[0],
                empty=M.empty_kg, cd0=M.polar.cd0)


def main():
    Ss = np.arange(12.0, 14.76, 0.25)
    bs = np.arange(9.75, 12.01, 0.25)
    grid = [[evaluate(S, b) for b in bs] for S in Ss]
    rows = [list(d.values()) for r in grid for d in r]
    write_csv(OUT / "carpet.csv", list(grid[0][0].keys()), rows)
    A = lambda k: np.array([[d[k] for d in r] for r in grid])
    rng, vs0, roc, to, f100 = A("rng"), A("vs0"), A("roc"), A("to"), A("f100")
    feas = (vs0 <= VS0_MAX) & (roc >= ROC_MIN) & (to <= TO_MAX) & (rng >= RANGE_MIN)
    i, j = np.unravel_index(np.argmin(np.where(feas, f100, 99)), rng.shape)
    best = grid[i][j]
    v0 = evaluate(14.15, 11.0)
    write_json(OUT / "wing_choice.json", {"optimum": best, "team_v0_wing": v0,
                                          "constraints": {"vs0_max_kmh": VS0_MAX, "roc_min": ROC_MIN, "to_max_m": TO_MAX, "range_min_km": RANGE_MIN},
                                          "objective": "min fuel per 100 km at 200 km/h"})

    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    B, SS = np.meshgrid(bs, Ss)
    cf = ax.contourf(B, SS, f100, levels=14, cmap="Blues_r", alpha=0.9)
    cb = fig.colorbar(cf, ax=ax, pad=0.02); cb.set_label("Fuel at 200 km/h, 1500 m [L/100 km]  (lower = better)")
    cs = ax.contour(B, SS, rng, levels=8, colors=style.INK2, linewidths=0.8, linestyles=":")
    ax.clabel(cs, fmt="%.0f km", fontsize=7.5)
    for Z, lev, col, lab in ((rng, RANGE_MIN, style.SERIES[2], f"range {RANGE_MIN:.0f} km"),
                             (vs0, VS0_MAX, style.BAD, f"stall {VS0_MAX} km/h"),
                             (roc, ROC_MIN, style.HANSA, f"ROC {ROC_MIN} m/s"),
                             (to, TO_MAX, style.SERIES[6], f"take-off {TO_MAX:.0f} m")):
        c = ax.contour(B, SS, Z, levels=[lev], colors=[col], linewidths=2.2)
        ax.clabel(c, fmt={lev: lab}, fontsize=8.5)
    ax.contourf(B, SS, (~feas).astype(float), levels=[0.5, 1.5], colors="none", hatches=["////"])
    ax.plot(best["b"], best["S"], "*", ms=20, color=style.EIDOLON, mec="white", mew=1.5, zorder=5)
    ax.annotate(f"Eidolon v1\nS {best['S']:.2f} m², b {best['b']:.2f} m\n{best['rng']:.0f} km, {best['f100']:.2f} L/100km",
                (best["b"], best["S"]), xytext=(12, 10), textcoords="offset points", fontsize=9, weight="semibold")
    ax.plot(11.0, 14.15, "o", ms=10, color=style.HANSA, mec="white", mew=1.5, zorder=5)
    ax.annotate(f"team wing v0\n{v0['f100']:.2f} L/100km, {v0['rng']:.0f} km", (11.0, 14.15), xytext=(8, -26), textcoords="offset points", fontsize=9)
    ax.set_xlabel("Span b [m]"); ax.set_ylabel("Wing area S [m²]")
    ax.set_title("Wing sizing carpet: every point is a fully closed aircraft")
    ax.grid(False)
    style.note(fig, "Hatched = violates a constraint. Dotted = range with 2 crew + bag. Bottom-up mass (study 01). Engine 912 iSc. studies/05_wing_sizing.py")
    style.save(fig, OUT / "wing_carpet.png")

    # ---- classical constraint diagram (power loading form) with the calibrated polar
    from eidolon.design import eidolon_v1
    c = close(eidolon("912iSc", best["S"], best["b"]))
    M = c.model; pol = M.polar; P = M.plane
    ws = np.linspace(350, 750, 200)
    from eidolon import atmosphere as isa
    def p_w_level(V, h):
        q = 0.5 * isa.density(h) * V**2
        return (q * pol.cd0 / ws + pol.k * ws / q) * V
    eta = 0.80
    curves = {
        "Cruise 200 km/h @1500 m (75 % power)": p_w_level(V_CRUISE, CRUISE_ALT) / (eta * 0.75 * float(isa.sigma(CRUISE_ALT))),
        "Climb 3.5 m/s @ Vy, SL": (p_w_level(35.0, 0) + ROC_MIN) / (eta * 0.866),
        "Ceiling 4000 m, 0.5 m/s": (p_w_level(np.sqrt(2 * ws / (isa.density(4000) * 0.9)), 4000) + 0.508) / (eta * 0.866 * float(isa.sigma(4000) - (1 - isa.sigma(4000)) / 7.55)),
    }
    fig, ax = plt.subplots(figsize=(9, 5))
    for (k, v), col in zip(curves.items(), style.SERIES[:3]):
        ax.plot(ws, v, color=col, label=k)
    ws_stall = 0.5 * isa.RHO0 * (VS0_MAX / 3.6) ** 2 * pol.cl_max_land
    ax.axvline(ws_stall, color=style.BAD, lw=2, label=f"Stall {VS0_MAX} km/h, CLmax,L {pol.cl_max_land:.2f}")
    gov = np.maximum.reduce(list(curves.values()))
    ax.fill_between(ws, gov, 120, where=ws <= ws_stall, color=style.EIDOLON, alpha=0.07, label="feasible")
    wsd = M.ac.wing_loading
    ax.plot(wsd, 73.5e3 / M.W, "*", ms=18, color=style.EIDOLON, mec="white", label=f"Eidolon v1 (912 iSc): {wsd:.0f} N/m²")
    ax.set_xlabel("Wing loading W/S [N/m²]"); ax.set_ylabel("Required shaft power-to-weight P/W [W/N]")
    ax.set_ylim(0, 16); ax.legend(fontsize=8.5, loc="upper right")
    ax.set_title("Constraint diagram (calibrated polar)")
    style.note(fig, f"CD0 {pol.cd0:.4f}, k {pol.k:.4f}, installed eta 0.80 assumed for the diagram only; climb/TO use the BEMT model elsewhere.")
    style.save(fig, OUT / "constraint_diagram.png")
    print("optimum", {k: round(v, 3) for k, v in best.items()})
    print("team v0", {k: round(v, 3) for k, v in v0.items()})


if __name__ == "__main__":
    main()
