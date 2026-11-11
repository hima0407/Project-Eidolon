# Project Eidolon: requirements

**Status:** v1 baseline, 10 Nov 2026. This replaces the earlier register, which held two unreconciled baselines (750 kg / 800 km and 705.7 kg / 1,000 km). v1 settles that question: **750 kg governs**, because it puts Eidolon in the same class as the Hansa-NG and makes the comparison fair (see D1 in [DESIGN_DECISIONS.md](DESIGN_DECISIONS.md)).

Every target below is set to beat the published Hansa-NG figure. The "Eidolon final" column is the **model prediction** for the final aircraft (v1 geometry with the carbon sandwich airframe, study 20) from `run_all.py`, not a demonstrated capability. The first closure, with glass skins, is in brackets where it differs.

## 1. Mission requirements

| # | Requirement | Hansa-NG (published) | Target | Eidolon final (model) | Status |
|---|---|---:|---:|---:|---|
| R1 | MTOW | 750 kg | 750 kg | 750 kg | set |
| R2 | Seats | 2 | 2 side by side, 1.07 m cabin | 2 | set |
| R3 | Stall, landing configuration (CS-VLA 49) | 80 km/h | ≤ 83 km/h | 80.9 km/h | met (conservative model) |
| R4 | Max rate of climb, sea level | 3.3 m/s | ≥ 3.5 m/s | 3.70 m/s | met |
| R5 | Cruise at 75 % power, 1500 m | 200 km/h | ≥ 205 km/h | 215 km/h (216) | met |
| R6 | Fuel burn at 200 km/h | — (model 9.35 L/100 km) | ≤ 8.5 L/100 km | 7.85 L/100 km (7.84) | met, robust (100 % of Monte-Carlo samples) |
| R7 | Range, 2 × 77 kg + 10 kg, 200 km/h, 45-min reserve | — (model 713 km) | ≥ 800 km | 1,098 km (803) | met; tank full; lead over Hansa-NG survives 35 kg of mass growth (glass: 5 kg) |
| R8 | Take-off distance to 15 m | 450 m | ≤ 450 m | 357 m | met |
| R9 | Service ceiling | 3,048 m (operating limit) | ≥ 3,048 m | 6,317 m | met |
| R10 | Limit load factors | not published | +4.4 / −1.76 g (CS-23 utility) | V-n done (study 12) | met |
| R11 | Static margin | — | 5-20 % MAC over the CG range | 12.0-14.9 % (12.0-13.6) | met |
| R12 | Engine | 912 iSc | IC engine (course rule) | 912 iSc (study 08) | set |
| R13 | Spin recovery (trainer) | — | Bowman TDPF ≥ 200 × 10⁻⁶ | 496 × 10⁻⁶ (481) | met (study 09) |
| R14 | Ailerons effective beyond first stall | — | 100 % aileron span unstalled at +2° | 100 % up to +3° | met (study 04, drooped LE) |

## 2. Retired targets and why

| Earlier target | Outcome |
|---|---|
| 25 L fuel tank with 1,000 km range | Not feasible. At about 16 L/h, 25 L is about 1.5 h, which is about 300 km. The v1 tank is 100 L. Wing volume is not the limit (the box holds several hundred litres); payload mass is. |
| 705.7 kg MTOW, 500 kg empty | 500 kg is not supported by the bottom-up mass model (530 kg, P5-P95 500-560 kg). Retired in favour of the like-for-like 750 kg class. |
| Wing 14.15 m², AR 8.55 | Superseded by the study 05 optimum, 13.25 m² and 11.5 m (−3.6 % fuel burn, +13 % range with 2 crew). |
| Wing 13.25 m², 10.25 m | The first carpet optimum, found with Raymer's statistical mass. With sized spar caps (bottom-up mass) span is cheaper, and the optimum moved to 11.5 m. |
| Range target 600 km | Raised to 800 km, now a constraint on the fuel-burn optimisation. |
| BEMT efficiency 89.2 % | Superseded: 0.81 installed at 200 km/h, 1500 m (study 07). |
| Tail V_h 0.575, 2.23 m² | Superseded by the 40 % elevator: V_h 0.50, 1.79 m² (study 09). |
| Piezo gear for energy absorption | Not feasible: 0.04 % of the landing energy. Kept as a sensor (study 13). |

## 3. Design-variable baseline (final aircraft)

| Item | Value | Source |
|---|---|---|
| Wing | 13.25 m², b 11.5 m, AR 9.98, taper 0.60, MAC 1.18 m, −2° washout, 5° dihedral, drooped outboard LE (58-100 % semispan) | study 05, 04 |
| Sections | NACA 63-415 (root) → 63-412 (tip) | study 03 |
| Flaps | single slotted, 28 % chord, 62 % semispan, 15° T/O, 30° landing | DDR D3 |
| Horizontal tail | 1.87 m², V_h 0.525 (first closure 1.79 m², 0.50), NACA 0012, 40 % elevator, low on the tail cone | study 09, 10, 20 |
| Vertical tail | 1.52 m², V_v 0.041, NACA 0012 → 0009, + 0.18 m² ventral strake | study 09 |
| Fuselage | 7.10 m body, 1.16 × 1.28 m max, 1.07 m cabin | study 19, DDR D12 |
| Engine / propeller | Rotax 912 iSc; 1.75 m 3-blade constant speed | study 08, 07 |
| Landing gear | fixed tricycle, S-glass leaf main legs, all wheels faired; PVDF hard-landing sensing + PZT health monitoring | study 13 |
| Fuel | 100 L usable | requirement R7 |
| Airframe | carbon/foam sandwich skins, ribs, shell, cowling (vacuum infusion); CFRP spar caps; S-glass gear | study 20, DDR D13 |
| Empty mass | 500 kg (first closure in glass: 530 kg, P5-P95 500-560 kg) | studies 01, 20 |
| Unit cost (model) | ₹3.19 crore (glass ₹3.09; Hansa-NG ₹3.0 reported) | study 18 |

## 4. Evidence vocabulary

- **Requirement:** a target the design must satisfy.
- **Assumption `[A]`:** an input used because stronger evidence is not available. It is tagged where it is used in the code.
- **Model result:** an output of the calibrated pipeline.
- **Validated:** checked against independent data (studies 01-02 for Hansa-NG, Aquila A210 and DV20; test files in `tests/`).
