#!/usr/bin/env python3
"""Preliminary wing-loading/TW sweep for the current Eidolon mission.

This preserves the project assumptions as explicit scenario inputs. It does
not determine MTOW, wing area, engine selection, aircraft drag, or flight
performance. Cruise speed is treated as TAS for the first altitude comparison.
"""
from __future__ import annotations

import argparse
import csv
from html import escape
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results" / "constraints"

# Current owner-selected mission targets.
CRUISE_KMH = 230.0
CRUISE_ALTITUDES_M = [0.0, 1500.0, 3000.0]

# Historical/provisional requirements and aerodynamic assumptions. These are
# sensitivity inputs, not validated Eidolon properties.
STALL_KMH = 85.0
CL_MAX_LANDING = 1.8
CD0_AIRCRAFT = 0.024
ASPECT_RATIO = 8.55
OSWALD_E = 0.80
ROC_SEA_LEVEL_MS = 3.0
CLIMB_SPEED_MS = 32.0
ROC_CEILING_MS = 0.508  # historical 100 ft/min screening criterion
SERVICE_CEILING_M = 3000.0
PROP_EFFICIENCY_SCENARIOS = [0.75, 0.80, 0.85]
WS_MIN = 200.0
WS_MAX = 1000.0
N_POINTS = 401

G = 9.80665
R_AIR = 287.05287
T0 = 288.15
P0 = 101325.0
LAPSE = 0.0065
K = 1.0 / (math.pi * OSWALD_E * ASPECT_RATIO)


def isa_density(altitude_m: float) -> float:
    """ISA troposphere density, valid for the requested 0–3,000 m sweep."""
    if not 0.0 <= altitude_m <= 11000.0:
        raise ValueError("This preliminary atmosphere model supports 0–11,000 m")
    temp = T0 - LAPSE * altitude_m
    pressure = P0 * (temp / T0) ** (G / (R_AIR * LAPSE))
    return pressure / (R_AIR * temp)


def level_flight_tw(ws: float, speed_ms: float, rho: float) -> float:
    q = 0.5 * rho * speed_ms**2
    return q * CD0_AIRCRAFT / ws + K * ws / q


def best_ld_speed(ws: float, rho: float) -> float:
    cl_at_min_drag = math.sqrt(CD0_AIRCRAFT / K)
    return math.sqrt(2.0 * ws / (rho * cl_at_min_drag))


def make_svg(curves: dict[str, list[float]], stall_ws_max: float, cruise_kmh: float) -> str:
    width, height = 1100, 740
    left, right, top, bottom = 95, 1075, 65, 630
    x_min, x_max, y_max = WS_MIN, WS_MAX, 0.5

    def px(x: float) -> float:
        return left + (x - x_min) / (x_max - x_min) * (right - left)

    def py(y: float) -> float:
        return bottom - y / y_max * (bottom - top)

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2"]
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#222}.grid{stroke:#d9d9d9;stroke-width:1}.axis{stroke:#333;stroke-width:1.5}</style>',
        f'<text x="{width/2}" y="30" text-anchor="middle" font-size="21" font-weight="bold">Project Eidolon | Preliminary {cruise_kmh:g} km/h Mission Constraint Sweep</text>',
    ]
    for y in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        parts.append(f'<line class="grid" x1="{left}" y1="{py(y):.1f}" x2="{right}" y2="{py(y):.1f}"/>')
        parts.append(f'<text x="{left-12}" y="{py(y)+5:.1f}" text-anchor="end" font-size="13">{y:.1f}</text>')
    for x in [200, 300, 400, 500, 600, 700, 800, 900, 1000]:
        parts.append(f'<line class="grid" x1="{px(x):.1f}" y1="{top}" x2="{px(x):.1f}" y2="{bottom}"/>')
        parts.append(f'<text x="{px(x):.1f}" y="{bottom+22}" text-anchor="middle" font-size="13">{x}</text>')
    parts.append(f'<line class="axis" x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}"/>')
    parts.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{bottom}"/>')
    parts.append(f'<text x="{(left+right)/2}" y="{bottom+52}" text-anchor="middle" font-size="15">Wing loading, W/S [N/m²]</text>')
    parts.append(f'<text x="24" y="{(top+bottom)/2}" text-anchor="middle" font-size="15" transform="rotate(-90 24 {(top+bottom)/2})">Required thrust-to-weight ratio, T/W [-]</text>')

    ws_values = [WS_MIN + (WS_MAX - WS_MIN) * i / (N_POINTS - 1) for i in range(N_POINTS)]
    for idx, (name, values) in enumerate(curves.items()):
        color = colors[idx % len(colors)]
        points = " ".join(f"{px(x):.1f},{py(min(y, y_max)):.1f}" for x, y in zip(ws_values, values))
        parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.5"/>')
    x_stall = px(stall_ws_max)
    parts.append(f'<line x1="{x_stall:.1f}" y1="{top}" x2="{x_stall:.1f}" y2="{bottom}" stroke="#111" stroke-width="2" stroke-dasharray="8 6"/>')

    legend_y = 82
    for idx, name in enumerate(curves):
        x0 = 640 + (idx % 2) * 220
        y0 = legend_y + (idx // 2) * 24
        color = colors[idx % len(colors)]
        parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x0+23}" y2="{y0}" stroke="{color}" stroke-width="3"/>')
        parts.append(f'<text x="{x0+29}" y="{y0+5}" font-size="11">{escape(name)}</text>')
    stall_y = legend_y + (len(curves) // 2 + 1) * 24
    parts.append(f'<line x1="640" y1="{stall_y}" x2="663" y2="{stall_y}" stroke="#111" stroke-width="2" stroke-dasharray="6 4"/>')
    parts.append(f'<text x="669" y="{stall_y+5}" font-size="11">Provisional stall boundary: {stall_ws_max:.0f} N/m²</text>')
    parts.append(f'<text x="{left}" y="{height-15}" font-size="11">Scenario only: CD0, AR, e, CLmax, climb speed and ceiling criterion are provisional. No MTOW or engine selection is implied.</text>')
    parts.append('</svg>')
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cruise-kmh", type=float, default=CRUISE_KMH)
    parser.add_argument("--altitudes-m", type=float, nargs="+", default=CRUISE_ALTITUDES_M)
    args = parser.parse_args()
    if args.cruise_kmh <= 0:
        parser.error("--cruise-kmh must be positive")
    if any(h < 0 or h > 3000 for h in args.altitudes_m):
        parser.error("--altitudes-m values must be between 0 and 3,000 m for this sweep")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ws = [WS_MIN + (WS_MAX - WS_MIN) * i / (N_POINTS - 1) for i in range(N_POINTS)]
    rows: list[tuple[float, ...]] = []
    curves: dict[str, list[float]] = {}
    cruise_ms = args.cruise_kmh / 3.6

    def data_row(ws_value: float, name: str, tw: float, rho: float,
                 speed_ms: float, roc_ms: float) -> tuple[float, ...]:
        # P_shaft / aircraft mass = g * (T/W) * V / eta_prop.
        specific_power = [G * tw * speed_ms / eta for eta in PROP_EFFICIENCY_SCENARIOS]
        return (ws_value, name, tw, rho, speed_ms, roc_ms, *specific_power)

    for altitude in args.altitudes_m:
        rho = isa_density(altitude)
        name = f"Cruise: {args.cruise_kmh:g} km/h TAS at {altitude:g} m"
        tw = [level_flight_tw(w, cruise_ms, rho) for w in ws]
        curves[name] = tw
        rows.extend(data_row(float(w), name, float(t), rho, cruise_ms, 0.0)
                    for w, t in zip(ws, tw))

    rho_sl = isa_density(0.0)
    q_climb = 0.5 * rho_sl * CLIMB_SPEED_MS**2
    climb_drag_tw = [q_climb * CD0_AIRCRAFT / w + K * w / q_climb for w in ws]
    climb_tw = [drag_tw + ROC_SEA_LEVEL_MS / CLIMB_SPEED_MS for drag_tw in climb_drag_tw]
    climb_name = f"Sea-level climb: ROC {ROC_SEA_LEVEL_MS:g} m/s at {CLIMB_SPEED_MS:g} m/s"
    curves[climb_name] = climb_tw
    rows.extend(data_row(float(w), climb_name, float(t), rho_sl, CLIMB_SPEED_MS, ROC_SEA_LEVEL_MS)
                for w, t in zip(ws, climb_tw))

    rho_ceiling = isa_density(SERVICE_CEILING_M)
    v_ceiling = [best_ld_speed(w, rho_ceiling) for w in ws]
    ceiling_tw = [level_flight_tw(w, v, rho_ceiling) + ROC_CEILING_MS / v
                  for w, v in zip(ws, v_ceiling)]
    ceiling_name = f"Ceiling: {SERVICE_CEILING_M:g} m, ROC {ROC_CEILING_MS:g} m/s"
    curves[ceiling_name] = ceiling_tw
    rows.extend(data_row(float(w), ceiling_name, float(t), rho_ceiling, float(v), ROC_CEILING_MS)
                for w, t, v in zip(ws, ceiling_tw, v_ceiling))

    stall_ws_max = 0.5 * rho_sl * (STALL_KMH / 3.6) ** 2 * CL_MAX_LANDING
    csv_path = OUT_DIR / "mission_constraint_sweep.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow([
            "wing_loading_N_m2", "condition", "required_TW", "density_kg_m3",
            "speed_m_s", "rate_of_climb_m_s",
            "specific_power_eta_075_W_kg", "specific_power_eta_080_W_kg",
            "specific_power_eta_085_W_kg",
        ])
        writer.writerows(rows)

    svg_path = OUT_DIR / "mission_constraint_sweep.svg"
    svg_path.write_text(make_svg(curves, stall_ws_max, args.cruise_kmh), encoding="utf-8")

    print("PROJECT EIDOLON | PRELIMINARY MISSION CONSTRAINT SWEEP")
    print(f"Cruise target: {args.cruise_kmh:g} km/h TAS; altitudes: {args.altitudes_m}")
    print(f"Provisional stall-derived maximum W/S: {stall_ws_max:.1f} N/m^2")
    print("Assumptions are screening inputs; MTOW, wing area, and engine are not selected.")
    print(f"Graph: {svg_path.relative_to(ROOT)}")
    print(f"Data:  {csv_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
