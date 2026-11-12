"""Study 23 - Does the carbon airframe change the engine choice?

Study 08 picked the Rotax 912 iSc with glass skins, where a heavy engine eats the fuel. The carbon
airframe (study 20) frees about 30 kg, so the question is whether that now pays for a bigger engine,
including the six-cylinder UL Power UL520iS. Every engine is re-closed again, now with carbon skins, and
scored with the same weights as study 08 (docs/DESIGN_DECISIONS.md, D6).

Also: (B) what the six-cylinder would need to meet the 800 km requirement, (C) the hot-day options side by
side, including the 912 iSc with study 15's electric boost, now charged correctly against a full tank, and
(D) range with two 90 kg adults.
"""
from _common import ROOT, style, write_json, write_csv
import importlib
import numpy as np
import matplotlib.pyplot as plt

from eidolon.engines import ENGINES
from eidolon.design import eidolon_v1, eidolon_final
from eidolon.model import build, V_CRUISE, CRUISE_ALT
from eidolon.hybrid import boost_mass_kg


def fmt(v):
    return f"{v:,.0f}" if abs(v) >= 100 else f"{v:.3g}"

s08 = importlib.import_module("08_engine_trade")
s20 = importlib.import_module("20_materials_carbon")
OUT = style.out("23_engine_carbon")
WEIGHTS, LOWER, HOT = s08.WEIGHTS, s08.LOWER_BETTER, s08.HOT
RANGE_REQ = 800.0
NAME = {k: ENGINES[k].name.replace(" (DarkAero 1 engine)", "").replace(" Sport", "") for k in ENGINES}


def run(builder):
    s08.eidolon_v1 = builder
    rows = [s08.metrics(k) for k in ENGINES]
    s08.eidolon_v1 = eidolon_v1
    for m in WEIGHTS:
        v = np.array([r[m] for r in rows], float); lo, hi = v.min(), v.max()
        for r, x in zip(rows, v):
            s = (x - lo) / (hi - lo) if hi > lo else 1.0
            r[f"score_{m}"] = 1 - s if m in LOWER else s
    for r in rows:
        r["score"] = sum(WEIGHTS[m] * r[f"score_{m}"] for m in WEIGHTS)
        r["meets_800km"] = bool(r["range_design_payload"] >= RANGE_REQ)
    return {r["key"]: r for r in rows}


def range_for(M, fuel):
    W = (M.empty_kg + M.payload_kg + fuel) * 9.80665
    return M.plane.range_km(W, fuel, V_CRUISE, CRUISE_ALT)[0]


def needs_for_800(key):
    M = eidolon_final(key).model
    lo, hi = 0.0, 150.0
    for _ in range(40):
        f = 0.5 * (lo + hi)
        lo, hi = (f, hi) if range_for(M, f) < RANGE_REQ else (lo, f)
    f800 = hi
    return {"empty_kg": M.empty_kg, "fuel_for_800km_kg": f800, "fuel_for_800km_L": f800 / 0.72,
            "mtow_needed_kg": M.empty_kg + M.payload_kg + f800,
            "empty_reduction_needed_kg": max(M.empty_kg + M.payload_kg + f800 - M.ac.mtow, 0.0)}


def hybrid_carbon(pe_kw=30.0):
    c = eidolon_final(); M = c.model; P = M.plane; W = M.W
    to_g, to15, vlof = P.takeoff_distance(W, HOT["h"], HOT["dT"], extra_power_w=pe_kw * 1e3)
    Vc, roc_c = P.roc_curve(W, HOT["h"], HOT["dT"], "takeoff")
    roc = float(np.max(roc_c + P.eta(Vc, HOT["h"], HOT["dT"], "takeoff") * pe_kw * 1e3 / W))
    m = boost_mass_kg(pe_kw, to_g / max(vlof / 2, 1) + 300.0 / max(roc, 0.5))["total"]
    Mb = build(M.ac, extra_empty_kg=m)                      # mass paid from useful load; fuel capped by the tank
    return {"label": f"912 iSc + {pe_kw:.0f} kW boost", "added_kg": m, "takeoff_hot_day": to15, "roc_hot_day": roc,
            "range_design_payload": Mb.plane.range_km(Mb.W, Mb.fuel_kg, V_CRUISE, CRUISE_ALT)[0],
            "fuel_per_100km": Mb.plane.fuel_per_100km(Mb.W, V_CRUISE, CRUISE_ALT)[0], "fuel_kg": Mb.fuel_kg}


def main():
    glass, carbon = run(eidolon_v1), run(eidolon_final)
    order = sorted(carbon, key=lambda k: -carbon[k]["score"])
    need = {k: needs_for_800(k) for k in ("915iS", "UL520iS")}
    hyb = hybrid_carbon(30.0)
    heavy = {}
    with s20.crew(90.0):
        for k in ENGINES:
            M = eidolon_final(k).model
            heavy[k] = M.plane.range_km(M.W, M.fuel_kg, V_CRUISE, CRUISE_ALT)[0]
    keep = ("empty_mass", "fuel_kg", "fuel_per_100km", "range_design_payload", "cruise_75_kmh", "roc_sl", "roc_hot_day",
            "takeoff_sl", "takeoff_hot_day", "prop", "vh", "score", "meets_800km")
    res = {"weights": WEIGHTS, "hot_day": HOT, "range_requirement_km": RANGE_REQ, "carbon_ranking": order,
           "glass": {k: {m: glass[k][m] for m in keep} for k in ENGINES},
           "carbon": {k: {m: carbon[k][m] for m in keep} for k in ENGINES},
           "six_cylinder_and_915_needs": need, "hot_day_912iSc_plus_boost_carbon": hyb,
           "range_two_90kg_crew_carbon_km": heavy}
    write_json(OUT / "engine_trade_carbon.json", res)
    write_csv(OUT / "engine_trade_carbon.csv", ["engine", "airframe"] + list(keep),
              [[k, a] + [d[k][m] for m in keep] for a, d in (("glass", glass), ("carbon", carbon)) for k in ENGINES])

    # ---- figure 1: glass vs carbon for each engine, one metric per panel
    panels = [("range_design_payload", "Range, 2 crew + bag [km]", RANGE_REQ), ("fuel_per_100km", "Fuel at 200 km/h [L/100 km]", None),
              ("roc_hot_day", "Climb on a 45 °C day [m/s]", None), ("takeoff_hot_day", "Take-off, 45 °C day [m]", None),
              ("empty_mass", "Empty mass [kg]", None), ("score", "Weighted score, carbon (D6 weights)", None)]
    fig, axs = plt.subplots(2, 3, figsize=(14, 6.8))
    y = np.arange(len(order))
    for ax, (m, title, req) in zip(axs.flat, panels):
        cv = [carbon[k][m] for k in order]
        if m != "score":
            gv = [glass[k][m] for k in order]
            ax.barh(y - 0.19, gv, height=0.36, color=style.MUTED, alpha=0.55, label="glass skins (study 08)")
            ax.barh(y + 0.19, cv, height=0.36, color=[style.ENGINE_COLORS[k] for k in order], label="carbon skins")
            for i, v in enumerate(cv):
                ax.text(v, i + 0.19, " " + fmt(v), va="center", fontsize=8.5, color=style.INK2)
        else:
            ax.barh(y, cv, height=0.55, color=[style.ENGINE_COLORS[k] for k in order])
            for i, v in enumerate(cv):
                ax.text(v, i, f" {v:.2f}", va="center", fontsize=8.5, color=style.INK2)
        if req:
            ax.axvline(req, color=style.BAD, ls="--", lw=1.2); ax.text(req, len(order) - 0.45, " requirement", color=style.BAD, fontsize=8.5)
        ax.set_yticks(y, [NAME[k] for k in order], fontsize=8.5); ax.invert_yaxis(); ax.grid(axis="y", visible=False)
        ax.set_title(title, fontsize=10.5); ax.set_xlim(0, max(cv + ([req] if req else [])) * 1.25)
    h, l = axs[0, 0].get_legend_handles_labels(); fig.legend(h, l, loc="upper right", fontsize=9, frameon=False, ncol=2)
    fig.suptitle(f"Engine trade re-run on the carbon airframe: winner still {NAME[order[0]]} (score {carbon[order[0]]['score']:.2f})",
                 x=0.01, ha="left", fontsize=13, weight="semibold")
    fig.tight_layout()
    style.note(fig, "Every engine re-closed with carbon skins: tail, wing position, propeller and fuel recomputed. MTOW fixed at 750 kg; "
               f"the 100 L tank is never the limit for the heavy engines, the weight is. UL520iS needs MTOW {need['UL520iS']['mtow_needed_kg']:.0f} kg for 800 km.")
    style.save(fig, OUT / "engine_trade_carbon.png")

    # ---- figure 2: hot-day options
    opts = [("912 iSc", carbon["912iSc"]), (hyb["label"], hyb), ("Rotax 914 F", carbon["914"]), ("UL520iS (6-cyl)", carbon["UL520iS"])]
    cols = [style.SERIES[0], style.SERIES[2], style.ENGINE_COLORS["914"], style.ENGINE_COLORS["UL520iS"]]
    fig, axs = plt.subplots(1, 4, figsize=(15, 3.6))
    for ax, (m, t) in zip(axs, (("takeoff_hot_day", "Take-off, 45 °C at 600 m [m]"), ("roc_hot_day", "Climb, 45 °C day [m/s]"),
                                ("range_design_payload", "Range, 2 crew + bag [km]"), ("fuel_per_100km", "Fuel at 200 km/h [L/100 km]"))):
        v = [o[1][m] for o in opts]
        ax.barh(range(4), v, color=cols, height=0.6)
        for i, x in enumerate(v):
            ax.text(x, i, " " + fmt(x), va="center", fontsize=8.5, color=style.INK2)
        ax.set_yticks(range(4), [o[0] for o in opts] if ax is axs[0] else [""] * 4, fontsize=9); ax.invert_yaxis()
        ax.set_title(t, fontsize=10.5); ax.grid(axis="y", visible=False); ax.set_xlim(0, max(v) * 1.3)
    fig.suptitle("Hot-day performance: the boost buys most of the big engine’s take-off, without its fuel bill",
                 x=0.01, ha="left", fontsize=12.5, weight="semibold")
    fig.tight_layout()
    style.note(fig, f"Carbon airframe. Boost: motor + inverter + battery = {hyb['added_kg']:.1f} kg, paid from spare useful load (tank stays nearly full).")
    style.save(fig, OUT / "hot_day_options.png")

    for k in order:
        r = carbon[k]
        print(f"  {NAME[k]:16s} score {r['score']:.2f} range {r['range_design_payload']:.0f} (glass {glass[k]['range_design_payload']:.0f}) "
              f"L/100 {r['fuel_per_100km']:.2f} hotROC {r['roc_hot_day']:.2f} hotTO {r['takeoff_hot_day']:.0f} empty {r['empty_mass']:.0f} 2x90kg {heavy[k]:.0f}")
    print("  needs:", {k: {m: round(v, 1) for m, v in d.items()} for k, d in need.items()})
    print("  hybrid:", {m: (round(v, 2) if isinstance(v, float) else v) for m, v in hyb.items()})


if __name__ == "__main__":
    main()
