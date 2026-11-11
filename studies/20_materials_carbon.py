"""Study 20 - Airframe material: glass sandwich (first closure) against carbon sandwich (final aircraft).

Geometry is frozen; only the laminate set changes (eidolon/structures.py AIRFRAME) and the design is
re-closed. Carbon keeps certified-trainer thicknesses (2 plies outside, 1 inside) and adds lightning
protection, bonding and antenna windows. The 148.8 kg class allowance, measured on glass trainers,
is left unchanged (conservative). The gear stays S-glass (study 13); the spar caps were already carbon.

Outputs: mass by group, what the saving buys at a fixed 750 kg (fuel, range with 2 x 77 kg and
2 x 90 kg crews), the mass growth that would erase the range lead over Hansa-NG, a span check of the
wing carpet with carbon mass, and cost efficiency with the study 18 cost model.
"""
from _common import style, write_json
from contextlib import contextmanager
import numpy as np
import matplotlib.pyplot as plt

import eidolon.stability as stab
import eidolon.weights as wts
from eidolon import cost
from eidolon.aircraft import eidolon
from eidolon.design import BASELINE, close, eidolon_v1, eidolon_final, hansa_closed, headline
from eidolon.model import build, V_CRUISE, CRUISE_ALT

OUT = style.out("20_materials")
HANSA_USEFUL_KG = 210.0   # published (CSIR-NAL brochure)


@contextmanager
def crew(kg):
    old = wts.OCCUPANT_KG, stab.OCCUPANT_KG
    wts.OCCUPANT_KG = stab.OCCUPANT_KG = kg
    try:
        yield
    finally:
        wts.OCCUPANT_KG, stab.OCCUPANT_KG = old


def range_km(M):
    return M.plane.range_km(M.W, M.fuel_kg, V_CRUISE, CRUISE_ALT)[0]


def growth_to_lose_lead(ac, target_km):
    """Extra empty mass [kg] at which range falls to the Hansa-NG value (bisection on the model)."""
    lo, hi = 0.0, 120.0
    for _ in range(30):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if range_km(build(ac, extra_empty_kg=mid)) > target_km else (lo, mid)
    return 0.5 * (lo + hi)


def main():
    hansa = hansa_closed(); hh = headline(hansa)
    hansa_range = hh["Range @200 km/h, design payload, 45 min reserve [km]"]
    cases = {"glass": eidolon_v1(), "carbon": eidolon_final()}
    out = {}
    for name, c in cases.items():
        M = c.model; h = headline(c)
        with crew(90.0):
            c90 = close(c.model.ac.copy())
        out[name] = dict(empty_kg=M.empty_kg, useful_kg=M.ac.mtow - M.empty_kg, fuel_2x77_kg=M.fuel_kg,
                         range_2x77_km=range_km(M), range_2x90_km=range_km(c90.model),
                         f100=h["Fuel per 100 km @200 km/h [L]"], cruise_kmh=h["Cruise speed @75% 1500 m [km/h]"],
                         roc=h["Max ROC SL [m/s]"], takeoff_m=h["Take-off to 15 m [m]"], stall_kmh=h["Stall, landing flap [km/h]"],
                         ld_max=h["L/D max"], static_margin=h["Static margin, aft CG [%MAC]"],
                         growth_to_lose_lead_kg=growth_to_lose_lead(M.ac, hansa_range),
                         groups=M.mass.model.groups())
    # cost efficiency with the study 18 model
    vh_h = hansa.model.plane.v_max(hansa.model.W, 0.0) * 3.6
    k = cost.calibrate_labour(vh_h)
    g = cases["glass"].model
    vh_e = g.plane.v_max(g.W, 0.0) * 3.6
    price = {"glass": cost.unit_cost(g.ac, vh_e, g.empty_kg, k, "glass")["total_inr"],
             "carbon": cost.unit_cost(g.ac, vh_e, g.empty_kg, k, "infusion")["total_inr"]}
    eff = {"Hansa-NG": dict(price_inr=cost.HANSA_PRICE_INR, useful_kg=HANSA_USEFUL_KG, range_km=hansa_range)}
    for n in ("glass", "carbon"):
        eff[f"Eidolon, {n}"] = dict(price_inr=price[n], useful_kg=out[n]["useful_kg"], range_km=out[n]["range_2x77_km"])
    for v in eff.values():
        v["inr_lakh_per_kg_useful"] = v["price_inr"] / 1e5 / v["useful_kg"]
        v["inr_per_km_range"] = v["price_inr"] / v["range_km"]
    # span check: does carbon mass move the wing optimum? (same area, two spans)
    span = {}
    for b in (11.5, 12.0):
        ac = eidolon(**dict(BASELINE, span=b)); ac.airframe = "carbon"
        M = close(ac).model
        span[f"{b:.1f} m"] = M.plane.fuel_per_100km(M.W, V_CRUISE, CRUISE_ALT)[0]

    # figure 1: structure by group
    groups = ["Wing", "Fuselage", "Tail", "Landing gear"]
    gv = [out["glass"]["groups"][x] for x in groups]; cv = [out["carbon"]["groups"][x] for x in groups]
    fig, ax = plt.subplots(figsize=(10, 5.0)); idx = np.arange(len(groups)); hgt = 0.34
    ax.barh(idx - hgt / 2 - 0.01, gv, height=hgt, color=style.EIDOLON, label=f"Glass skins (first closure): {sum(gv):.0f} kg")
    ax.barh(idx + hgt / 2 + 0.01, cv, height=hgt, color=style.SERIES[2], label=f"Carbon skins, certified thickness: {sum(cv):.0f} kg")
    for i, (a, b) in enumerate(zip(gv, cv)):
        ax.text(a + 1, i - hgt / 2, f"{a:.1f}", va="center", fontsize=10.5, color=style.INK2)
        ax.text(b + 1, i + hgt / 2, f"{b:.1f}", va="center", fontsize=10.5, color=style.INK2)
    ax.set_yticks(idx, groups); ax.invert_yaxis(); ax.set_xlabel("kg"); ax.grid(axis="y", visible=False)
    ax.set_xlim(0, max(gv) * 1.2); ax.set_title("Airframe structure: glass vs carbon"); ax.legend(loc="lower right", fontsize=10.5)
    fig.tight_layout()
    style.note(fig, "Carbon: 3 plies of 160–200 g/m² carbon per sandwich instead of 4 plies of 200 g/m² glass; +2.5 kg lightning "
                    "protection. Gear stays S-glass. studies/20_materials_carbon.py")
    style.save(fig, OUT / "glass_vs_carbon.png")

    # figure 2: cost per kg of useful load
    names = list(eff); vals = [eff[n]["inr_lakh_per_kg_useful"] for n in names]
    cols = [style.HANSA, style.MUTED, style.EIDOLON]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.barh(names, vals, height=0.55, color=cols); ax.invert_yaxis()
    for i, v in enumerate(vals):
        ax.text(v + 0.02, i, f"₹{v:.2f} lakh per kg", va="center", fontsize=11, color=style.INK2)
    ax.set_xlim(0, max(vals) * 1.3); ax.grid(axis="y", visible=False); ax.set_xlabel("₹ lakh per kg of useful load")
    ax.set_title("Unit cost per kilogram of useful load")
    fig.tight_layout()
    style.note(fig, "Unit cost from study 18 (Hansa-NG: reported ₹3.0 crore, 210 kg published useful load). studies/20_materials_carbon.py")
    style.save(fig, OUT / "cost_efficiency.png")

    write_json(OUT / "materials.json", {"aircraft": out, "hansa_range_km": hansa_range, "cost_efficiency": eff,
                                       "carbon_span_check_f100": span})
    for n, v in out.items():
        print(n, {kk: round(float(vv), 2) for kk, vv in v.items() if not isinstance(vv, dict)})
    print("efficiency", {n: (round(v["inr_lakh_per_kg_useful"], 3), round(v["inr_per_km_range"])) for n, v in eff.items()})
    print("span check", {k: round(v, 3) for k, v in span.items()})


if __name__ == "__main__":
    main()
