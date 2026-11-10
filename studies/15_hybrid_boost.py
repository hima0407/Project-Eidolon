"""Study 15 (appendix) - Hybrid boost for hot-and-high Indian airfields.

Question: on a 45 C day at a 600 m airfield, the naturally-aspirated 912 iSc loses ~18 % power.
How much electric boost restores sea-level ISA take-off and climb, and what does it cost in mass
(paid for in fuel, since MTOW is fixed at 750 kg)?
"""
from _common import ROOT, style, write_json, write_csv
import numpy as np
import matplotlib.pyplot as plt

from eidolon.design import eidolon_v1
from eidolon.hybrid import boost_mass_kg
from eidolon.model import V_CRUISE, CRUISE_ALT
from eidolon import atmosphere as isa
from eidolon.aircraft import G

OUT = style.out("15_hybrid")
H_AF = 600.0
DT = isa.isa_dT_for_oat(45.0, H_AF)


def main():
    c = eidolon_v1(); M = c.model; P = M.plane; W = M.W
    to_isa = P.takeoff_distance(W)[1]
    roc_isa = P.max_roc(W, 0.0, 0.0, "takeoff")[0]
    rows = []
    for pe in np.arange(0, 41, 5.0):
        to_g, to15, vlof = P.takeoff_distance(W, H_AF, DT, extra_power_w=pe * 1e3)
        Vc, roc_c = P.roc_curve(W, H_AF, DT, "takeoff")
        etas = P.eta(Vc, H_AF, DT, "takeoff")
        roc = float(np.max(roc_c + etas * pe * 1e3 / W))
        t_boost = to_g / max(vlof / 2, 1) + 300.0 / max(roc, 0.5)    # ground roll + climb to 300 m AGL
        m = boost_mass_kg(pe, t_boost)
        fuel_lost = m["total"]
        rng = P.range_km(W, max(M.fuel_kg - fuel_lost, 0), V_CRUISE, CRUISE_ALT)[0]
        rows.append((pe, to15, roc, m["total"], m["energy_kwh"], rng))
    A = np.array(rows)
    write_csv(OUT / "hybrid_sweep.csv", ["P_electric_kW", "TO_15m_hot_m", "ROC_hot_ms", "added_mass_kg", "battery_kWh", "range_2crew_km"], rows)
    fig, axs = plt.subplots(1, 3, figsize=(13.5, 4))
    axs[0].plot(A[:, 0], A[:, 1], color=style.EIDOLON, marker="o", ms=5); axs[0].axhline(to_isa, color=style.INK2, ls=":")
    axs[0].text(1, to_isa * 1.02, "ISA sea-level value", fontsize=8.5, color=style.INK2)
    axs[0].set_title("Take-off to 15 m, 45 °C at 600 m"); axs[0].set_xlabel("Electric boost [kW]"); axs[0].set_ylabel("m")
    axs[1].plot(A[:, 0], A[:, 2], color=style.EIDOLON, marker="o", ms=5); axs[1].axhline(roc_isa, color=style.INK2, ls=":")
    axs[1].set_title("Max rate of climb, hot day"); axs[1].set_xlabel("Electric boost [kW]"); axs[1].set_ylabel("m/s")
    axs[2].plot(A[:, 0], A[:, 3], color=style.HANSA, marker="o", ms=5, label="added mass [kg]")
    axs[2].plot(A[:, 0], A[:, 5] / 10, color=style.EIDOLON, marker="o", ms=5, label="range with 2 crew [km/10]")
    axs[2].set_title("What it costs"); axs[2].set_xlabel("Electric boost [kW]"); axs[2].legend(fontsize=8.5)
    style.note(fig, "Motor 5 kW/kg, inverter 12 kW/kg, pack 160 Wh/kg, 80 % DoD [A]. Boost for ground roll + climb to 300 m. "
               "Mass is paid for in fuel (MTOW fixed).")
    style.save(fig, OUT / "hybrid_boost.png")
    i = int(np.argmin(np.abs(A[:, 1] - to_isa)))
    write_json(OUT / "hybrid_summary.json", {"hot_day": {"oat_C": 45, "elevation_m": H_AF, "dT": DT},
                                             "isa_sl_takeoff_m": to_isa, "isa_sl_roc": roc_isa,
                                             "boost_to_restore_isa_takeoff_kW": A[i, 0],
                                             "row": dict(zip(["P_e", "TO", "ROC", "mass", "kWh", "range"], A[i]))})
    print(A)


if __name__ == "__main__":
    main()
