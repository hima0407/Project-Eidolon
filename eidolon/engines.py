"""Engine database.

Every number carries a source tag. ``[M]`` = manufacturer data sheet / page,
``[W]`` = Wikipedia summary of manufacturer data, ``[A]`` = project assumption
(no published figure found; sensitivity is tested in studies/14_sensitivity.py).

BSFC is brake specific fuel consumption at a typical 65-75 % cruise setting.
For the Rotax engines it is back-calculated from the Operator's Manual fuel-flow
figure where we have one; please re-check against the manual before final use.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import atmosphere as isa

FUEL_DENSITY = 0.72  # kg/L, AVGAS 100LL / MOGAS mean [A]


@dataclass
class Engine:
    key: str
    name: str
    cylinders: int
    p_takeoff_kw: float          # 5-minute take-off power, sea level ISA
    p_mcp_kw: float              # maximum continuous power
    dry_mass_kg: float           # as quoted by the manufacturer (see notes)
    accessories_kg: float        # items quoted separately (alternator, pumps, mount, exhaust ...)
    bsfc_g_kwh: float            # cruise BSFC
    prop_rpm_max: float          # propeller shaft rpm at take-off power
    prop_rpm_cruise: float
    turbo_critical_alt_m: float  # 0 for naturally aspirated
    cooling: str                 # "liquid/air" or "air"
    tbo_h: float
    sources: dict = field(default_factory=dict)

    @property
    def mass_kg(self) -> float:
        return self.dry_mass_kg + self.accessories_kg

    def power_available_kw(self, h, dT: float = 0.0, rating: str = "mcp"):
        """Shaft power at altitude.

        Naturally aspirated: Gagg-Ferrar lapse  P/P0 = sigma - (1 - sigma)/7.55.
        Turbo-normalised: flat to the critical altitude, then Gagg-Ferrar above it.
        Hot day: NA power also scales with the density ratio (via sigma with dT).
        """
        p0 = self.p_takeoff_kw if rating == "takeoff" else self.p_mcp_kw
        h = np.asarray(h, dtype=float)
        s = isa.sigma(h, dT)
        if self.turbo_critical_alt_m > 0:
            s_crit = isa.sigma(self.turbo_critical_alt_m, dT)
            s_eff = np.where(h <= self.turbo_critical_alt_m, 1.0, s / s_crit)
            # a turbo still sees hotter intake air on a hot day: 1 % per 10 K offset [A]
            s_eff = s_eff * (1 - 0.001 * max(dT, 0))
        else:
            s_eff = s
        return p0 * (s_eff - (1 - s_eff) / 7.55)

    def fuel_flow_lph(self, p_shaft_kw):
        return self.bsfc_g_kwh * np.asarray(p_shaft_kw) / 1000.0 / FUEL_DENSITY


ENGINES = {
    "912ULS": Engine(
        "912ULS", "Rotax 912 ULS", 4, 73.5, 69.0, 58.3, 6.0, 285.0,
        5800 / 2.43, 5000 / 2.43, 0.0, "liquid/air", 2000,
        {"power": "[M] Rotax 912 ULS data sheet: 73.5 kW take-off, 69 kW MCP",
         "mass": "[W] ~58 kg dry incl. gearbox, carburettors; accessories [A]",
         "bsfc": "[A] carburetted, ~285 g/kWh at 75 %",
         "tbo": "[W] 2000 h"}),
    "912iSc": Engine(
        "912iSc", "Rotax 912 iSc Sport", 4, 73.5, 72.0, 63.6, 7.0, 245.0,
        5800 / 2.43, 5000 / 2.43, 0.0, "liquid/air", 2000,
        {"power": "[M] flyrotax.com: 73.5 kW @5800 (5 min), 72.0 kW @5500 MCP",
         "mass": "[M] 63.6 kg engine with gearbox i=2.43; alternator, pumps, exhaust listed separately -> +7 kg [A]",
         "bsfc": "[A] fuel injected, lean-capable; ~245 g/kWh at 65-75 % (Rotax quotes ~30 % lower fuel burn than comparable engines)",
         "tbo": "[M] 2000 h"}),
    "914": Engine(
        "914", "Rotax 914 F", 4, 84.5, 73.5, 64.0, 10.0, 290.0,
        5800 / 2.43, 5000 / 2.43, 4880.0, "liquid/air", 2000,
        {"power": "[W] 84.5 kW take-off (5 min), 73.5 kW MCP, turbocharged",
         "mass": "[A] ~64 kg + turbo/intercooler plumbing",
         "bsfc": "[A] carburetted turbo, ~290 g/kWh",
         "tbo": "[W] 2000 h"}),
    "915iS": Engine(
        "915iS", "Rotax 915 iS", 4, 104.0, 99.0, 82.2, 7.0, 295.0,
        5800 / 2.54, 5000 / 2.54, 4570.0, "liquid/air", 1200,
        {"power": "[M] flyrotax.com: 104 kW max, 99 kW MCP @5500 rpm",
         "mass": "[M] 82.2 kg incl. gearbox i=2.54, turbo, intercooler, exhaust; +2.0 frame +3.0 alternator +1.6 pumps +0.4 hood",
         "bsfc": "[W] 280-310 g/kWh at 5500 rpm -> 295 mean",
         "tbo": "[M] 1200 h"}),
    "UL520iS": Engine(
        "UL520iS", "UL Power UL520iS (DarkAero 1 engine)", 6, 149.0, 138.0, 108.0, 4.0, 280.0,
        3300, 2800, 0.0, "air", 1500,
        {"power": "[M] ulpower.com: 200 hp @3300 rpm, 185 hp @2800 rpm (direct drive)",
         "mass": "[M] 108 kg installed incl. starter and alternator; exhaust/baffles +4 kg [A]",
         "bsfc": "[A] air-cooled, injected flat-six, ~280 g/kWh",
         "tbo": "[A] 1500 h (not published on the product page)",
         "darkaero": "[Kitplanes, Dark Aero 1 article] UL Power 520iS, 200 hp"}),
}
