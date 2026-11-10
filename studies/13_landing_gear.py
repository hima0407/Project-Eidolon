"""Study 13 - The 'cool factor': a self-sensing composite leaf-spring main gear.

Claim tested: a glass-fibre leaf spring is the lightest way to store CS-23 landing energy,
and a PVDF film sensor on it gives a signal large enough to log the sink rate of every
landing (automatic hard-landing detection for a training fleet) for ~0.1 kg.
Not claimed: that piezo material can change the gear stiffness or absorb the landing
(see docs/piezoelectric_ribbon_landing_gear_concept.md - that remains a research branch).
"""
from _common import ROOT, style, write_json
import numpy as np
import matplotlib.pyplot as plt

from eidolon.design import eidolon_v1
from eidolon.landing_gear import MATERIALS, size_leaf, sink_speed_cs23, pvdf_voltage, pvdf_energy_uJ

OUT = style.out("13_landing_gear")
SENSOR_STRAIN_FRACTION = 0.30     # film placed where strain is 30 % of the peak (PVDF fatigue margin) [A]


def main():
    c = eidolon_v1(); M = c.model; W = M.W; ws = M.ac.wing_loading
    v_lim = sink_speed_cs23(ws)
    designs = [size_leaf(W, ws, mat) for mat in MATERIALS]
    designs.sort(key=lambda d: d.mass_per_leg_kg)
    best = designs[0]
    fig, axs = plt.subplots(1, 2, figsize=(12.5, 4.4))
    names = [d.material for d in designs]
    axs[0].barh(range(len(designs)), [2 * d.mass_per_leg_kg for d in designs],
                color=[style.EIDOLON if d is best else style.MUTED for d in designs], height=0.55)
    for i, d in enumerate(designs):
        axs[0].text(2 * d.mass_per_leg_kg, i, f"  {2*d.mass_per_leg_kg:.1f} kg   (σ²/Eρ = {d.merit:.0f} J/kg)", va="center",
                    fontsize=8.5, color=style.INK2)
    axs[0].set_yticks(range(len(designs)), names); axs[0].invert_yaxis()
    axs[0].set_xlim(0, max(2 * d.mass_per_leg_kg for d in designs) * 1.6)
    axs[0].set_xlabel("Mass of two spring legs [kg]"); axs[0].grid(axis="y", visible=False)
    axs[0].set_title(f"Same landing energy, five materials")

    # sensor signal vs sink rate (peak force ~ v_sink for a linear spring)
    vs = np.linspace(0.2, 1.15 * v_lim, 100)
    eps_peak_lim = MATERIALS[best.material]["sigma"] / MATERIALS[best.material]["E"]
    eps = SENSOR_STRAIN_FRACTION * eps_peak_lim * (vs / v_lim)
    V = pvdf_voltage(eps)
    axs[1].plot(vs, V, color=style.EIDOLON, lw=2.4)
    bands = [(0, 0.9, "normal", style.GOOD), (0.9, 1.6, "firm", style.SERIES[3]), (1.6, 1.15 * v_lim, "hard: inspect", style.BAD)]
    for lo, hi, lab, col in bands:
        axs[1].axvspan(lo, hi, color=col, alpha=0.08, lw=0)
        axs[1].text((lo + hi) / 2, V.max() * 1.02, lab, ha="center", fontsize=8.5, color=style.INK2)
    axs[1].axvline(v_lim, color=style.INK2, ls="--", lw=1)
    axs[1].text(v_lim, V.max() * 0.15, f" CS-23 limit\n {v_lim:.2f} m/s", fontsize=8.5, color=style.INK2)
    axs[1].set_xlabel("Sink rate at touchdown [m/s]"); axs[1].set_ylabel("PVDF open-circuit voltage [V]")
    axs[1].set_ylim(0, V.max() * 1.12)
    axs[1].set_title("The gear reads every landing's sink rate")
    style.note(fig, f"Uniform-strength (width-tapered) leaf, 0.75 m, peak gear load factor 3.0, wing lift 2/3 W (CS-23.473). "
               f"PVDF 28 µm film at {SENSOR_STRAIN_FRACTION:.0%} of peak strain.")
    style.save(fig, OUT / "smart_gear.png")
    raymer = sum(v for k, v in M.mass.items.items() if k.startswith("Main"))
    write_json(OUT / "smart_gear.json", {
        "limit_sink_speed_ms": v_lim, "chosen_material": best.material,
        "designs": [vars(d) for d in designs],
        "two_leg_spring_mass_kg": 2 * best.mass_per_leg_kg,
        "main_gear_in_mass_model_kg (legs at fatigue allowable + wheels, brakes)": raymer,
        "sensor_voltage_at_limit_V": float(pvdf_voltage(SENSOR_STRAIN_FRACTION * eps_peak_lim)),
        "sensor_voltage_at_1ms_V": float(pvdf_voltage(SENSOR_STRAIN_FRACTION * eps_peak_lim / v_lim)),
        "harvested_energy_per_hard_landing_uJ (10 cm2 film)": pvdf_energy_uJ(SENSOR_STRAIN_FRACTION * eps_peak_lim),
        "sensing_system_mass_kg": {"4 PVDF films": 0.006, "shielded cable 3 m": 0.045, "logger + charge amp": 0.030, "total": 0.081},
    })
    # ---------------- can piezo make the gear more efficient or safer?  Energy bookkeeping per landing.
    E_leg = best.energy_per_leg_J
    eps_lim = MATERIALS[best.material]["sigma"] / MATERIALS[best.material]["E"]
    # (a) 4 MFC patches (85 x 28 x 0.3 mm active), strain capped at the MFC limit 0.45 %, k^2 = 0.1 shunt
    vol_mfc = 4 * 0.085 * 0.028 * 0.0003
    e_mfc = min(0.3 * eps_lim, 0.0045)
    U_mfc = 0.5 * 30e9 * e_mfc**2 * vol_mfc * 0.10
    # (b) both faces of both legs fully covered with PZT, strain capped at 0.15 % (brittle ceramic)
    area_full = 2 * 2 * 0.75 * best.root_width_m * 0.5
    U_full = 0.5 * 60e9 * 0.0015**2 * area_full * 0.0003 * 0.25
    m_full = area_full * 0.0003 * 7600
    # (c) PVDF film harvest (study above)
    U_pvdf = pvdf_energy_uJ(SENSOR_STRAIN_FRACTION * eps_lim) * 1e-6
    rows = [("Landing energy per leg (CS-23.473)", E_leg), ("Full PZT coverage, shunt-dissipated", U_full),
            ("4 MFC patches, resonant shunt", U_mfc), ("PVDF film, harvested", U_pvdf)]
    fig, ax = plt.subplots(figsize=(9.5, 3.6))
    ax.barh(range(len(rows)), [r[1] for r in rows], color=[style.INK2, style.HANSA, style.HANSA, style.SERIES[2]], height=0.55)
    ax.set_xscale("log"); ax.set_xlim(1e-6, 1e5)
    for i, (n, v) in enumerate(rows):
        ax.text(v * 1.6, i, f"{v:.3g} J  ({100*v/E_leg:.2g} % of landing)" if i else f"{v:.0f} J", va="center", fontsize=8.5, color=style.INK2)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows]); ax.invert_yaxis(); ax.grid(axis="y", visible=False)
    ax.set_xlabel("Energy per landing [J], log scale")
    ax.set_title("Piezo can absorb less than 0.05 % of a landing")
    style.note(fig, f"Full coverage adds {m_full:.1f} kg of ceramic for {100*U_full/E_leg:.2f} % of the energy. "
               "Piezo is useful here only as a sensor: sink-rate logging and Lamb-wave damage detection (SHM).")
    style.save(fig, OUT / "piezo_energy.png")
    write_json(OUT / "piezo_assessment.json", {
        "landing_energy_per_leg_J": E_leg,
        "mfc_shunt_J": U_mfc, "full_pzt_shunt_J": U_full, "full_pzt_mass_kg": m_full, "pvdf_harvest_J": U_pvdf,
        "verdict": {
            "efficiency (energy absorption, stiffness control)": "no: <0.5 % of the landing energy even with full coverage",
            "safety - hard-landing detection": "yes: sink-rate logging, ~80 g",
            "safety - structural health monitoring": "yes: PZT wafers as Lamb-wave actuators/sensors find delaminations and impact damage in the composite leaf and its attachment between inspections",
            "nose-gear shimmy": "marginal: shunted patches add ~1-2 % damping to a mode; a conventional shimmy damper is lighter and certifiable",
            "energy harvesting": "tens of microjoules: enough to wake a logger, not to power it"}})
    print(f"  best {best.material}: 2 legs {2*best.mass_per_leg_kg:.2f} kg, t {best.thickness_m*1e3:.1f} mm, "
          f"b0 {best.root_width_m*1e3:.0f} mm, deflection {best.deflection_m*1e3:.0f} mm, v_sink {v_lim:.2f}")


if __name__ == "__main__":
    main()
