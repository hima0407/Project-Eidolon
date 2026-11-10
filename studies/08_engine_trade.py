"""Study 08 - Engine selection: five candidates, each in a fully re-closed airframe.

For every engine the whole design is re-closed (installed mass -> empty mass -> fuel ->
CG -> tail size and wing position -> propeller diameter/blade count -> performance), so a heavy
engine pays for its own nose ballast-free CG fix and larger tail, and a direct-drive engine pays
for its smaller, tip-Mach-limited propeller.

Scoring: weighted sum of normalised metrics (weights justified in docs/DESIGN_DECISIONS.md, D6).
"""
from _common import ROOT, style, write_json, write_csv
import numpy as np
import matplotlib.pyplot as plt

from eidolon.engines import ENGINES
from eidolon.design import eidolon_v1
from eidolon.model import V_CRUISE, CRUISE_ALT
from eidolon import atmosphere as isa

OUT = style.out("08_engine_trade")
WEIGHTS = {"fuel_per_100km": 0.30, "range_design_payload": 0.25, "roc_hot_day": 0.15,
           "takeoff_hot_day": 0.10, "empty_mass": 0.10, "tbo": 0.10}
LOWER_BETTER = {"fuel_per_100km", "takeoff_hot_day", "empty_mass"}
HOT = dict(h=600.0, dT=isa.isa_dT_for_oat(45.0, 600.0))      # 45 deg C day at a 600 m airfield (e.g. Deccan plateau) [A]


def metrics(key):
    c = eidolon_v1(key)
    M = c.model; P = M.plane; W = M.W
    eng = ENGINES[key]
    f100, lph, pcr = P.fuel_per_100km(W, V_CRUISE, CRUISE_ALT)
    return {
        "engine": eng.name, "key": key,
        "power_kw": eng.p_takeoff_kw, "installed_kg": sum(v for k, v in M.mass.items.items()
                                                           if k in ("Engine (data sheet)", "Propeller + governor", "Cooling, mount, cowling")),
        "empty_mass": M.empty_kg, "fuel_kg": M.fuel_kg,
        "prop": f"{M.ac.prop.diameter:.2f} m / {M.ac.prop.blades}-blade",
        "fuel_per_100km": f100, "fuel_flow_200": lph,
        "range_design_payload": P.range_km(W, M.fuel_kg, V_CRUISE, CRUISE_ALT)[0],
        "cruise_75_kmh": P.speed_at_power(W, CRUISE_ALT, 0.75) * 3.6,
        "roc_sl": P.max_roc(W, 0, 0, "takeoff")[0],
        "roc_hot_day": P.max_roc(W, HOT["h"], HOT["dT"], "takeoff")[0],
        "takeoff_sl": P.takeoff_distance(W)[1],
        "takeoff_hot_day": P.takeoff_distance(W, HOT["h"], HOT["dT"])[1],
        "tbo": eng.tbo_h, "vh": M.ac.vh, "x_le": M.ac.wing.x_le_root,
    }


def main():
    rows = [metrics(k) for k in ENGINES]
    # normalised scores
    for m in WEIGHTS:
        vals = np.array([r[m] for r in rows], dtype=float)
        lo, hi = vals.min(), vals.max()
        for r, v in zip(rows, vals):
            s = (v - lo) / (hi - lo) if hi > lo else 1.0
            r[f"score_{m}"] = 1 - s if m in LOWER_BETTER else s
    for r in rows:
        r["score"] = sum(WEIGHTS[m] * r[f"score_{m}"] for m in WEIGHTS)
    rows.sort(key=lambda r: -r["score"])
    write_csv(OUT / "engine_trade.csv", list(rows[0].keys()), [list(r.values()) for r in rows])
    write_json(OUT / "engine_trade.json", {"weights": WEIGHTS, "hot_day": HOT, "ranking": rows})

    # ---- figure: small multiples, one metric per panel, same engine order and colour
    show = [("fuel_per_100km", "Fuel at 200 km/h [L/100 km]"), ("range_design_payload", "Range, 2 crew + bag [km]"),
            ("roc_hot_day", "ROC on a 45 °C day [m/s]"), ("takeoff_hot_day", "Take-off, 45 °C day [m]"),
            ("empty_mass", "Empty mass [kg]"), ("cruise_75_kmh", "Cruise at 75 % [km/h]")]
    order = [r["key"] for r in rows]
    fig, axs = plt.subplots(2, 3, figsize=(13, 6.6))
    for ax, (m, title) in zip(axs.flat, show):
        vals = [next(r[m] for r in rows if r["key"] == k) for k in order]
        cols = [style.ENGINE_COLORS[k] for k in order]
        ax.barh(range(len(order)), vals, color=cols, height=0.6)
        ax.set_yticks(range(len(order)), [ENGINES[k].name.replace(" (DarkAero 1 engine)", "\n(DarkAero 1)") for k in order], fontsize=8.5)
        ax.invert_yaxis()
        for i, v in enumerate(vals):
            ax.text(v, i, f" {v:.3g}", va="center", fontsize=8.5, color=style.INK2)
        ax.set_title(title, fontsize=10.5)
        ax.grid(axis="y", visible=False)
        ax.set_xlim(0, max(vals) * 1.2)
    fig.suptitle(f"Engine trade, each in a re-closed airframe - winner: {rows[0]['engine']} (score {rows[0]['score']:.2f})",
                 x=0.01, ha="left", fontsize=13, weight="semibold")
    fig.tight_layout()
    style.note(fig, "Order = overall weighted score (top best). Hot day: 45 °C OAT at 600 m elevation. Weights: docs/DESIGN_DECISIONS.md (D6).")
    style.save(fig, OUT / "engine_trade.png")
    for r in rows:
        print(f"  {r['engine']:40s} score {r['score']:.2f}  L/100 {r['fuel_per_100km']:.2f}  range {r['range_design_payload']:.0f}  "
              f"empty {r['empty_mass']:.0f}  ROC {r['roc_sl']:.2f}/{r['roc_hot_day']:.2f}  TO {r['takeoff_sl']:.0f}/{r['takeoff_hot_day']:.0f}  prop {r['prop']}")


if __name__ == "__main__":
    main()
