#!/usr/bin/env python3
"""Project Eidolon preliminary aircraft constraint analysis.

Produces a wing-loading versus thrust-to-weight matching plot from explicit,
editable assumptions. This is a conceptual sizing model, not a validated
aircraft performance prediction.

Run from any working directory:
    python scripts/constraint_analysis.py
Optional propeller-efficiency scenario (NOT a default/validated value):
    python scripts/constraint_analysis.py --prop-eff 0.75
"""
from __future__ import annotations

import argparse
from pathlib import Path
import math
import numpy as np
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "constraints"

# Mission requirements from the Project Eidolon design brief.
G = 9.80665                         # m/s^2
MTOW_KG = 750.0                     # kg
W_N = MTOW_KG * G                   # N
V_STALL_KMH = 85.0                  # km/h, preliminary landing/stall requirement
V_CRUISE_KMH = 200.0                # km/h
V_MAX_KMH = 225.0                   # km/h
ROC_SEA_LEVEL = 3.0                 # m/s
SERVICE_CEILING_M = 3000.0          # m
ROC_CEILING = 0.508                 # m/s, 100 ft/min criterion from brief

# Atmosphere: values retained from the project brief; they are approximations.
RHO_SL = 1.225                      # kg/m^3
RHO_CRUISE = 1.0581                 # kg/m^3, approximately 1500 m
RHO_CEILING = 0.9093                # kg/m^3, approximately 3000 m

# Provisional conceptual-design assumptions. Update only with documented evidence.
CD0_AIRCRAFT = 0.024                # provisional aircraft-level parasite drag coefficient
ASPECT_RATIO = 8.55                 # provisional geometry input
OSWALD_E = 0.80                     # provisional span-efficiency factor
CL_MAX_LANDING = 1.8                # provisional landing configuration with flaps
CLIMB_SPEED_MS = 32.0               # assumed initial-climb speed; sensitivity required
WING_LOADING_CANDIDATE = 520.0      # N/m^2, candidate point from project plan
WING_LOADING_MIN = 200.0
WING_LOADING_MAX = 1000.0
N_POINTS = 801
DESIGN_MARGIN = 0.05                # explicit preliminary margin, not a certification factor

K = 1.0 / (math.pi * OSWALD_E * ASPECT_RATIO)


def level_flight_tw(ws: np.ndarray, speed: float, rho: float) -> np.ndarray:
    """Required T/W for steady level flight using a parabolic drag polar."""
    q = 0.5 * rho * speed**2
    return q * CD0_AIRCRAFT / ws + K * ws / q


def climb_tw(ws: np.ndarray, rho: float, roc: float, speed: float) -> np.ndarray:
    """Simplified required T/W = D/W + ROC/V at a specified climb speed."""
    q = 0.5 * rho * speed**2
    drag_to_weight = q * CD0_AIRCRAFT / ws + K * ws / q
    return drag_to_weight + roc / speed


def best_ld_speed(ws: np.ndarray, rho: float) -> np.ndarray:
    """Speed at minimum drag for the assumed parabolic polar."""
    cl_md = math.sqrt(CD0_AIRCRAFT / K)
    return np.sqrt(2.0 * ws / (rho * cl_md))


def ceiling_tw(ws: np.ndarray) -> np.ndarray:
    """Simplified ceiling constraint at minimum-drag speed and required ROC."""
    v = best_ld_speed(ws, RHO_CEILING)
    q = 0.5 * RHO_CEILING * v**2
    drag_to_weight = q * CD0_AIRCRAFT / ws + K * ws / q
    return drag_to_weight + ROC_CEILING / v


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--prop-eff", type=float, default=None, metavar="ETA",
        help="optional assumed propeller efficiency (0 < ETA <= 1); not validated",
    )
    args = parser.parse_args()
    if args.prop_eff is not None and not (0.0 < args.prop_eff <= 1.0):
        parser.error("--prop-eff must be greater than 0 and no greater than 1")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ws = np.linspace(WING_LOADING_MIN, WING_LOADING_MAX, N_POINTS)
    v_cruise = V_CRUISE_KMH / 3.6
    v_max = V_MAX_KMH / 3.6
    v_climb = CLIMB_SPEED_MS

    stall_ws_max = 0.5 * RHO_SL * (V_STALL_KMH / 3.6)**2 * CL_MAX_LANDING
    curves = {
        "Cruise: 200 km/h at ~1,500 m": level_flight_tw(ws, v_cruise, RHO_CRUISE),
        "Maximum speed: 225 km/h at sea level": level_flight_tw(ws, v_max, RHO_SL),
        f"Sea-level climb: ROC 3.0 m/s at {v_climb:.0f} m/s": climb_tw(ws, RHO_SL, ROC_SEA_LEVEL, v_climb),
        "Service ceiling: 3,000 m, ROC 0.508 m/s": ceiling_tw(ws),
    }
    governing = np.maximum.reduce(list(curves.values()))
    feasible = ws <= stall_ws_max
    idx = int(np.argmin(np.abs(ws - WING_LOADING_CANDIDATE)))
    candidate_ws = float(ws[idx])
    candidate_tw_min = float(governing[idx])
    candidate_tw_design = candidate_tw_min * (1.0 + DESIGN_MARGIN)
    candidate_area = W_N / candidate_ws

    # Machine-readable output: every constraint at the selected candidate point.
    csv_path = OUT_DIR / "constraint_values.csv"
    with csv_path.open("w", encoding="utf-8") as f:
        f.write("wing_loading_N_m2,stall_limit_N_m2,wing_area_m2,curve,required_TW\n")
        for name, values in curves.items():
            f.write(f"{candidate_ws:.3f},{stall_ws_max:.3f},{candidate_area:.4f},{name},{values[idx]:.6f}\n")
        f.write(f"{candidate_ws:.3f},{stall_ws_max:.3f},{candidate_area:.4f},governing_minimum,{candidate_tw_min:.6f}\n")
        f.write(f"{candidate_ws:.3f},{stall_ws_max:.3f},{candidate_area:.4f},governing_plus_{DESIGN_MARGIN:.0%}_margin,{candidate_tw_design:.6f}\n")

    # Graph: required T/W vs W/S, matching the original project brief.
    fig, ax = plt.subplots(figsize=(11, 7), dpi=180)
    for name, values in curves.items():
        ax.plot(ws, values, linewidth=2, label=name)
    ax.axvline(stall_ws_max, linestyle="--", linewidth=1.8,
               label=f"Stall limit: {stall_ws_max:.0f} N/m²")
    ax.axvline(candidate_ws, linestyle=":", linewidth=1.8,
               label=f"Candidate W/S: {candidate_ws:.0f} N/m²")
    ax.scatter([candidate_ws], [candidate_tw_design], marker="*", s=170, zorder=5,
               label=f"Candidate with {DESIGN_MARGIN:.0%} margin: T/W={candidate_tw_design:.3f}")
    ax.fill_between(ws, governing, 1.0, where=feasible, alpha=0.08,
                    label="Above governing constraint and below stall limit")
    ax.set_xlim(WING_LOADING_MIN, WING_LOADING_MAX)
    ax.set_ylim(bottom=0, top=min(1.0, max(0.35, float(np.nanpercentile(governing, 95) * 1.25))))
    ax.set_xlabel("Wing loading, W/S [N/m²]")
    ax.set_ylabel("Required thrust-to-weight ratio, T/W [-]")
    ax.set_title("Project Eidolon | Preliminary Constraint Analysis")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="best")
    fig.text(0.01, 0.01,
             "Conceptual model only. CD0, e, CLmax and climb speed are provisional; not a validated aircraft prediction.",
             fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    graph_path = OUT_DIR / "constraint_analysis.png"
    fig.savefig(graph_path, bbox_inches="tight")
    plt.close(fig)

    print("PROJECT EIDOLON | PRELIMINARY CONSTRAINT ANALYSIS")
    print("Status: conceptual estimate; inputs are not all validated.")
    print(f"MTOW: {MTOW_KG:.1f} kg ({W_N:.1f} N)")
    print(f"Candidate wing loading: {candidate_ws:.1f} N/m^2")
    print(f"Implied wing area at MTOW: {candidate_area:.3f} m^2")
    print(f"Stall-derived maximum wing loading: {stall_ws_max:.1f} N/m^2")
    print("Required T/W at candidate point:")
    for name, values in curves.items():
        print(f"  {name}: {values[idx]:.4f}")
    print(f"Governing T/W before margin: {candidate_tw_min:.4f}")
    print(f"Governing T/W with {DESIGN_MARGIN:.0%} preliminary margin: {candidate_tw_design:.4f}")
    if args.prop_eff is None:
        print("Engine shaft power: NOT calculated; propeller efficiency has not been established.")
    else:
        # P_shaft = T*V/eta_p. Estimate by condition; this is a scenario only.
        conditions = {
            "Cruise": (curves["Cruise: 200 km/h at ~1,500 m"][idx], v_cruise),
            "Maximum speed": (curves["Maximum speed: 225 km/h at sea level"][idx], v_max),
            "Sea-level climb": (curves[f"Sea-level climb: ROC 3.0 m/s at {v_climb:.0f} m/s"][idx], v_climb),
            "Service ceiling": (curves["Service ceiling: 3,000 m, ROC 0.508 m/s"][idx], best_ld_speed(np.array([candidate_ws]), RHO_CEILING)[0]),
        }
        for label, (tw, speed) in conditions.items():
            shaft_kw = (tw * W_N * speed / args.prop_eff) / 1000.0
            print(f"  {label} shaft-power scenario at eta_p={args.prop_eff:.3f}: {shaft_kw:.1f} kW")
        print("WARNING: optional prop-efficiency outputs are scenarios, not validation or engine selection.")
    print(f"Graph: {graph_path.relative_to(ROOT)}")
    print(f"Data:  {csv_path.relative_to(ROOT)}")

if __name__ == "__main__":
    main()
