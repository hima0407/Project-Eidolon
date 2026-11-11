"""Unit cost: the Eastlake general-aviation cost model as given by Gudmundsson (2013), calibrated on
Hansa-NG's reported price, plus a bottom-up premium for a carbon airframe.

Eastlake / Gudmundsson (General Aviation Aircraft Design, 2013, ch. 2), W_af in lb, V_H in KTAS:
    H_eng  = 0.0396 W^0.791 V^1.526 N^0.183 F_comp         engineering hours
    H_tool = 1.0032 W^0.764 V^0.899 N^0.178 Q^0.066 F_comp  tooling hours
    H_mfg  = 9.6613 W^0.74  V^0.543 N^0.524 F_comp          manufacturing hours
    C_dev  = 0.06458 W^0.873 V^1.89 Np^0.346 CPI F_comp     development support
    C_ft   = 0.009646 W^1.16 V^1.3718 Np^1.281 CPI          flight-test operations
    C_qc   = 0.13 C_mfg F_comp                              quality control
    C_mat  = 24.896 W^0.689 V^0.624 N^0.792 CPI             materials
Composite factors (all-composite airframe, Eastlake): engineering x2.0, tooling x2.0,
manufacturing x1.25, QC and development x1.5. Rates (2012 USD/h): engineering 92, tooling 61,
manufacturing 53. Engine 174 USD/hp, constant-speed propeller 209.66 D^2 (P/D)^0.12, avionics 15,000 USD.

Calibration, in the spirit of the rest of the project: one labour-rate factor k is fitted so the
identical model reproduces Hansa-NG's reported price (about Rs 3 crore; NAL director, Deccan Herald
2025), then applied unchanged to Eidolon.

Carbon premium (bottom-up, [A]): fabric price difference over the laminate area (Easy Composites
volume prices, 200 g/m2 twill: carbon GBP 20.50/m2, glass GBP 2.65/m2), lightning mesh, more
inspection (ultrasonic NDI) and one-off material qualification spread over the production run.
Labour hours stay at the glass airframe size: part count and size drive hours, not mass.
"""
from __future__ import annotations

LB, KT = 0.45359237, 1.852
CPI = 1.41                 # [A] US CPI 2012 -> 2025
INR_PER_USD = 88.0         # [A]
USD_PER_GBP = 1.27         # [A]
N_BUILT = 180              # 5 years at the 36-per-year Hansa-NG plant (Deccan Herald 2025)
N_PROTO = 2                # [A]
RATES = dict(eng=92.0, tool=61.0, mfg=53.0)            # 2012 USD/h (Gudmundsson)
F_COMP = dict(eng=2.0, tool=2.0, mfg=1.25, qc=1.5, dev=1.5)
HANSA_PRICE_INR = 3.0e7    # about Rs 3 crore per aircraft (reported)
HANSA_EMPTY_KG = 540.0     # published
LIABILITY = 0.15           # product liability, fraction of unit cost [A]
AIRFRAME_FRACTION = 0.65   # airframe weight / empty weight [A]

FABRIC_USD_M2 = {"glass": 2.65 * USD_PER_GBP, "carbon": 20.50 * USD_PER_GBP}
PLIES = {"glass": 4, "carbon": 3}
WASTE = 1.4                # cutting and scrap [A]
INTERNAL = 1.15            # ribs, bulkheads and control surfaces on top of the wetted skin [A]

PROCESS = {
    # extra material factor on carbon fabric, mfg-hour and QC multipliers, one-off USD, extra USD/aircraft
    "glass": dict(fabric_factor=1.0, mfg=1.0, qc=1.0, one_off=0.0, extra=0.0),
    "infusion": dict(fabric_factor=1.0, mfg=1.0, qc=1.10, one_off=0.2e6, extra=500.0),
    "prepreg": dict(fabric_factor=2.0, mfg=1.15, qc=1.30, one_off=2.0e6, extra=1500.0),
}


def eastlake(empty_kg: float, vh_kmh: float, k_lab: float = 1.0, mfg_mult: float = 1.0, qc_mult: float = 1.0,
             one_off_usd: float = 0.0, material_extra_usd: float = 0.0) -> tuple[dict, float]:
    """Per-aircraft cost items [USD] and total for N_BUILT aircraft."""
    W = AIRFRAME_FRACTION * empty_kg / LB
    V = vh_kmh / KT
    N = N_BUILT
    H_eng = 0.0396 * W**0.791 * V**1.526 * N**0.183 * F_COMP["eng"]
    H_tool = 1.0032 * W**0.764 * V**0.899 * N**0.178 * (N / 60) ** 0.066 * F_COMP["tool"]
    H_mfg = 9.6613 * W**0.74 * V**0.543 * N**0.524 * F_COMP["mfg"] * mfg_mult
    C_eng = 2.0969 * H_eng * RATES["eng"] * CPI * k_lab
    C_tool = 2.0969 * H_tool * RATES["tool"] * CPI * k_lab
    C_dev = 0.06458 * W**0.873 * V**1.89 * N_PROTO**0.346 * CPI * F_COMP["dev"] * k_lab
    C_ft = 0.009646 * W**1.16 * V**1.3718 * N_PROTO**1.281 * CPI * k_lab
    C_mfg = 2.0969 * H_mfg * RATES["mfg"] * CPI * k_lab
    C_qc = 0.13 * C_mfg * F_COMP["qc"] * qc_mult
    C_mat = 24.896 * W**0.689 * V**0.624 * N**0.792 * CPI
    D = 1.75 / 0.3048
    items = {
        "Engineering & certification": (C_eng + C_dev + C_ft) / N,
        "Tooling": C_tool / N,
        "Carbon one-off (qualification, tooling)": one_off_usd / N,
        "Manufacturing labour": C_mfg / N,
        "Quality control": C_qc / N,
        "Materials": C_mat / N + material_extra_usd,
        "Engine": 174 * 100 * CPI,
        "Propeller": 209.66 * CPI * D**2 * (100 / D) ** 0.12,
        "Avionics": 15000 * CPI,
    }
    items["Product liability"] = LIABILITY * sum(items.values())
    return items, sum(items.values())


def calibrate_labour(hansa_vh_kmh: float) -> float:
    """Labour-rate factor so the model gives Hansa-NG its reported price."""
    lo, hi = 0.01, 3.0
    for _ in range(80):
        k = 0.5 * (lo + hi)
        _, p = eastlake(HANSA_EMPTY_KG, hansa_vh_kmh, k)
        lo, hi = (k, hi) if p * INR_PER_USD < HANSA_PRICE_INR else (lo, k)
    return 0.5 * (lo + hi)


def laminate_area_m2(ac) -> float:
    """Wetted skin of wing, fuselage and tails, plus internal parts."""
    return (ac.wing.wetted_area(ac.fuselage.width) + ac.fuselage.wetted_area
            + 2.04 * (ac.htail.area + ac.vtail.area)) * INTERNAL


def unit_cost(ac, vh_kmh: float, glass_empty_kg: float, k_lab: float, process: str = "glass") -> dict:
    """Unit cost of an airframe built by 'glass', 'infusion' (carbon) or 'prepreg' (carbon).
    Hours are evaluated at the glass airframe's empty mass for every process."""
    p = PROCESS[process]
    area = laminate_area_m2(ac)
    fab_glass = area * PLIES["glass"] * WASTE * FABRIC_USD_M2["glass"]
    fab_carbon = area * PLIES["carbon"] * WASTE * FABRIC_USD_M2["carbon"] * p["fabric_factor"]
    extra = 0.0 if process == "glass" else fab_carbon - fab_glass + p["extra"]
    items, total = eastlake(glass_empty_kg, vh_kmh, k_lab, p["mfg"], p["qc"], p["one_off"], extra)
    return dict(process=process, items=items, total_usd=total, total_inr=total * INR_PER_USD,
                laminate_m2=area, fabric_usd=dict(glass=fab_glass, carbon=fab_carbon))
