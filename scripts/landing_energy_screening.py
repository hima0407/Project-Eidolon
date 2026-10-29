#!/usr/bin/env python3
"""Conceptual landing-energy screening for Project Eidolon.

This is NOT a structural design or airworthiness calculation. Swept parameters
are illustrative assumptions, not requirements or validated loads.
"""
from pathlib import Path
import itertools
import pandas as pd
import matplotlib.pyplot as plt

MTOW_KG = 600.0
SINK_SPEEDS_M_S = [1.5, 2.0, 2.5, 3.0]
EFFECTIVE_MASS_FRACTIONS = [0.25, 0.50, 0.75, 1.00]
GEAR_ENERGY_SHARES = [0.50, 0.70, 0.90]
STROKES_M = [0.08, 0.12, 0.16, 0.20]

def main():
    repo = Path(__file__).resolve().parents[1]
    out = repo / "results" / "landing_gear"
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for v, mass_frac, share, stroke in itertools.product(
        SINK_SPEEDS_M_S, EFFECTIVE_MASS_FRACTIONS,
        GEAR_ENERGY_SHARES, STROKES_M
    ):
        m_eff = MTOW_KG * mass_frac
        e_vertical = 0.5 * m_eff * v**2
        e_gear = e_vertical * share
        f_avg = e_gear / stroke
        k_equiv = 2.0 * e_gear / stroke**2
        f_linear_end = k_equiv * stroke
        rows.append({
            "MTOW_kg_assumed": MTOW_KG,
            "sink_speed_m_s_assumed": v,
            "effective_mass_fraction_assumed": mass_frac,
            "gear_energy_share_assumed": share,
            "stroke_m_assumed": stroke,
            "effective_mass_kg": m_eff,
            "vertical_kinetic_energy_J_screening": e_vertical,
            "gear_energy_J_screening": e_gear,
            "average_force_N_energy_over_stroke": f_avg,
            "linear_spring_equivalent_stiffness_N_m": k_equiv,
            "ideal_linear_spring_end_force_N": f_linear_end,
        })
    df = pd.DataFrame(rows)
    df.to_csv(out / "landing_energy_screening.csv", index=False)

    subset = df[(df["effective_mass_fraction_assumed"] == 1.0) &
                (df["gear_energy_share_assumed"] == 0.7)]
    fig, ax = plt.subplots(figsize=(9.5, 6))
    for stroke, group in subset.groupby("stroke_m_assumed"):
        summary = group.groupby("sink_speed_m_s_assumed")[
            "average_force_N_energy_over_stroke"
        ].mean()
        ax.plot(summary.index, summary.values, marker="o",
                label=f"Stroke assumption: {stroke:.2f} m")
    ax.set_xlabel("Assumed vertical sink speed (m/s)")
    ax.set_ylabel("Energy / assumed stroke (N)")
    ax.set_title("Eidolon landing-energy screen (illustrative, not design loads)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(out / "landing_energy_screening.png", dpi=200)
    plt.close(fig)
    print(f"Screening table: {out / 'landing_energy_screening.csv'}")
    print(f"Illustrative plot: {out / 'landing_energy_screening.png'}")
    print("WARNING: not a structural sizing, drop-test prediction, or airworthiness result.")

if __name__ == "__main__":
    main()
