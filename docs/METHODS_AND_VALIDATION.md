# Methods and validation

What each model does, where its equations come from, how we checked it, and what it cannot claim.
`[A]` marks an assumption in the code. Every one of them is listed in the module where it is used.

## 1. Model chain

| Discipline | Module | Method | Main reference |
|---|---|---|---|
| Atmosphere | `atmosphere.py` | ISA troposphere, hot day as ΔT at constant pressure altitude | ICAO Doc 7488 |
| Section data | `airfoil.py` | `.dat` coordinates, XFLR5/XFOIL polars | Abbott & von Doenhoff |
| Finite wing | `lifting_line.py` | Prandtl lifting line, Glauert series (40 odd terms), critical-section stall, drooped-LE clmax increment | Anderson ch. 5 |
| Parasite drag | `aero.py` | Component build-up: mixed laminar/turbulent Cf, form factors, interference, gear D/q, cooling | Raymer §12.5 |
| Induced drag | `aero.py` | Oswald e (Raymer eq. 12.48), cross-checked against Nita-Scholz from the LLT span efficiency | Raymer; Nita & Scholz 2012 |
| CLmax and flaps | `aero.py` | 0.9·cl_max and critical section averaged; slotted-flap ΔCLmax (Raymer eq. 12.21) | Raymer §12.4 |
| Propeller | `propeller.py` | BEMT with Prandtl tip/hub loss, stall, drag rise; non-dimensional C_T/C_P map | McCormick |
| Engine | `engines.py` | Data-sheet power, Gagg-Ferrar lapse, turbo flat-rating, BSFC | manufacturer data |
| **Mass** | `structures.py` | **Bottom-up**: spar caps and webs sized for 6.6 g bending/shear from the lifting-line load, sandwich skins by area, tails for the V_A tail load, catalogue systems; certified-trainer class allowance measured on 3 aircraft; per-item spreads → Monte Carlo | Megson; Niu; Torenbeek ch. 8 |
| Mass (cross-check) | `weights.py` | Raymer GA statistical equations, calibrated on Hansa-NG | Raymer §15.3 |
| Stability | `stability.py` | Neutral point (wing + fuselage + tail), CG envelope, landing-flare and take-off-rotation criteria, elevator τ | Etkin & Reid; Raymer ch. 16 |
| Empennage | `empennage.py` | Six configurations re-closed; Bowman TDPF spin screen; wing-wake crossing angle for deep stall | NASA TN D-6575; Raymer §16.7 |
| Performance | `performance.py` | Power curves, quasi-steady climb, numerically integrated range, time-stepped take-off/landing | Raymer ch. 17 |
| Loads | `loads.py` | CS-23 V-n with gust lines (K_g, U_de) | CS-23.333-341 |
| Landing gear | `landing_gear.py` | CS-23.473 energy, uniform-strength leaf, Ashby index, PVDF sensor voltage, piezo shunt-damping bound | Ashby; CS-23.473; Hagood & von Flotow 1991 |
| Closure | `design.py` | Iterates geometry → mass → CG → tail/wing position until converged | — |
| 3-D geometry | `oml.py`, `render.py` | Closed planar section rings per body → mesh, Fusion 360 loft, renders | — |

## 2. Verification (does the code solve its equations correctly?)

`python3 -m pytest -q` runs 14 tests:

| Test | Known answer |
|---|---|
| ISA density at 0 / 1500 / 3000 / 5000 m | ICAO table, within 0.2 % |
| Hot day 45 °C at sea level | ΔT = 30 K, ρ scales as 288.15/318.15 |
| Lifting line, rectangular AR 8 | e between 0.92 and 0.96 (Anderson fig. 5.20) |
| Lifting line, taper 0.4 | e > 0.985 (near-elliptic) |
| Lifting-line lift slope | Helmbold formula, within 4 % |
| BEMT efficiency | always below the actuator-disk ideal 2/(1+√(1+T/qA)) |
| Skin friction | laminar < mixed < turbulent |
| Engine lapse | 73.5 kW at sea level; turbo flat-rated at 3000 m |
| CS-23 sink speed | clipped to 7-10 ft/s |
| Mass closure | empty + payload + fuel ≤ MTOW |
| Calibration | Hansa-NG empty mass within 20 kg of 540 kg (leave-one-out), ROC 3.3 m/s reproduced |
| Requirements | Eidolon V_S0 ≤ 83 km/h, ROC ≥ 3.5 m/s, T/O ≤ 450 m, 5 % ≤ SM ≤ 20 %, nose lifts before V_LOF |
| Spar sizing | spar-cap mass rises with span and falls with thickness, as M/(σ·h) says it must |
| Elevator | effectiveness τ rises monotonically with chord ratio and stays below 1 |

The GitHub Actions workflow runs these tests and the full pipeline on every push.

## 3. Validation (does the model describe a real aircraft?)

### 3.1 Mass (study 01)

The bottom-up count is run on four real aircraft. The three certified trainers define the class allowance (mean 148.8 kg, σ 11.6 kg); leave-one-out predicts each from the other two:

| Aircraft | Published empty | Predicted (leave-one-out) | Error |
|---|---:|---:|---:|
| Hansa-NG | 540 kg | 520 kg | −3.7 % |
| Aquila A210 | 500 kg | 510 kg | +1.9 % |
| Diamond DV20 Katana | 505 kg | 516 kg | +2.1 % |

RMS 14.2 kg. The light-sport Pipistrel Virus is over-predicted by 54 kg, which is the category effect showing up, so the allowance is only used for certified-class aircraft.

### 3.2 Performance (study 02)

Two factors are fitted on Hansa-NG:

| Factor | Value | Fitted to |
|---|---:|---|
| Unmodelled drag (additive) | ΔCD0 = +0.0083 | 200 km/h at 75 % rated power, 1500 m |
| Climb excess power | ×0.866 | max ROC 3.3 m/s |

Then the model is compared with numbers that were **not** fitted:

| Published Hansa-NG | Published | Model | Error |
|---|---:|---:|---:|
| Empty mass (leave-one-out, 3.1) | 540 kg | 520 kg | −3.7 % |
| Stall, flap 20° | 80 km/h | 86.3 km/h | +8 % (conservative) |
| Take-off distance | 450 m | 405 m | −10 % |
| Landing distance | 600 m | 511 m | −15 % |
| Endurance at 65 % power, full fuel | 6.0 h | 5.85 h | −2 % |
| Range at 75 % power, full fuel, 45-min reserve | 926 km | 833 km | −10 % |
| Ceiling | ≥ 3,048 m (operating limit) | 5,490 m | consistent |

All predicted numbers are within ±15 %. Stall is predicted high and range low, so the models lean conservative.

A second, independent check is the wing: our lifting-line code and the team's XFLR5 VLM2 run agree on lift slope to 4.9 %.

**Why the factors are reasonable.**
- **ΔCD0 = 0.0083.** Cooling inlets, control gaps, steps, antennas and the propeller slipstream. The total Hansa-NG CD0 of 0.033 is typical of fixed-gear trainers (a Cessna 172 is about 0.031). It is additive, so it cannot inflate Eidolon's savings.
- **Climb ×0.87.** At low speed and high power the slipstream raises fuselage and tail drag, and the installed propeller efficiency drops.

**Sensitivity of the calibration.** The published 200 km/h "max cruise" has no stated power setting. We assumed 75 %. Across 65-85 %, the fitted ΔCD0 ranges from 0.0032 to 0.0122 (`calibration_vs_cruise_power_assumption.csv`). Study 14 samples that whole range, with the same draw for both aircraft.

## 4. Uncertainty (study 14)

The Monte Carlo uses common random numbers. Anything that affects both aircraft alike gets the same draw for both: ΔCD0, the class mass allowance, BSFC ±5 %, propeller installation 0.87-0.95. Aircraft-specific unknowns get separate draws. We ran it twice:

| Eidolon-specific draw | Pessimistic (biased against Eidolon) | Neutral |
|---|---|---|
| Laminar extent | 10-40 % (design 35 %) | 25-45 % |
| Gear-fairing quality, leg drag | ×1 to ×2.5 | ×1 to ×1.5 |
| Canopy drag | ×1 to ×1.4 | ×0.9 to ×1.2 |
| Empty-mass growth (novel parts) | −5 to +20 kg | normal, σ 8 kg |
| Hansa-NG laminar extent; gear legs partly faired | 5-25 %; 35-100 % | same |

| Result (400 samples each) | Pessimistic | Neutral |
|---|---:|---:|
| Fuel burn vs Hansa-NG, P5 / median / P95 | −14 / −9 / −4 % | −17 / −13 / −8 % |
| P(Eidolon burns less fuel) | **100 %** | **100 %** |
| Range with 2 crew, median | −12 % | +12 % |
| P(Eidolon flies further with 2 crew) | 30 % | 66 % |

**Reading it honestly.** The fuel-burn advantage is aerodynamic and survives every draw. The range advantage is a **mass-budget race**: at 750 kg with two crew, every kilogram of empty mass is a kilogram of fuel, about **18 km of range**. Eidolon's nominal range lead over the Hansa-NG model disappears if its empty mass grows **5 kg** beyond the estimate. So the range claim is conditional on hitting the mass estimate, and the next phase is a real layup and a weight-tracking budget.

## 5. Known limitations (what this pipeline does not claim)

1. **No trim drag** and no propeller-slipstream lift in cruise. Both aircraft are treated alike, so the effect on the comparison is second-order.
2. **The class allowance** is one number for everything a bottom-up count misses. It is measured on three aircraft (σ 11.6 kg), but it is not broken down.
3. **CLmax** comes from the critical-section method and Raymer's flap increments, not tests or CFD. The model is about 8 % conservative on Hansa-NG. The drooped-LE increment (+0.30 clmax) is from published cuff tests.
4. **BSFC** is assumed constant above 55 % power. The 912 iSc value (245 g/kWh) needs checking against the Operator's Manual.
5. **Hansa-NG geometry** that NAL does not publish (taper, airfoil, tail sizes, gear legs) uses generic values. This is why the head-to-head compares against the *model* of Hansa-NG rather than its brochure.
6. **Spin** is screened with Bowman's TDPF, an empirical criterion from 1970s spin-tunnel data. It is a screen, not a prediction of spin behaviour.
7. **Lateral-directional stability** (dihedral, fin) is sized by tail volume and the spin screen, not by a full stability-derivative analysis.
8. **Landing-gear sizing** is energy-based, with no attachment design.
9. **The 3-D model** is a lofted outer mould line for packaging, visualisation and a starting solid in Fusion 360, not a production surface model.
