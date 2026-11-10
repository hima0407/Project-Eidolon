"""Parallel-hybrid take-off/climb boost (appendix concept, not part of the IC-engine baseline).

An electric motor on the propeller shaft adds P_e for take-off and the first climb segment.
Mass model [A]:  motor 5 kW/kg (axial-flux class), inverter 12 kW/kg,
                 battery 160 Wh/kg at pack level, 80 % usable depth of discharge,
                 drivetrain efficiency battery->shaft 0.90, +2 kg wiring/cooling/mounts.
Energy: E = P_e * (t_takeoff + t_climb) / 0.90.
"""
from __future__ import annotations


def boost_mass_kg(p_e_kw: float, t_boost_s: float) -> dict:
    if p_e_kw <= 0:
        return {"motor": 0.0, "inverter": 0.0, "battery": 0.0, "integration": 0.0, "total": 0.0, "energy_kwh": 0.0}
    e_kwh = p_e_kw * t_boost_s / 3600 / 0.90
    batt = e_kwh / 0.80 / 0.160
    d = {"motor": p_e_kw / 5.0, "inverter": p_e_kw / 12.0, "battery": batt, "integration": 2.0}
    d["total"] = sum(d.values())
    d["energy_kwh"] = e_kwh
    return d
