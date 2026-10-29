# Project Eidolon: Piezoelectric Active-Tension Carbon Ribbon Landing Gear
## Concept screening study — not a design release

**Status:** Research hypothesis / feasibility study  
**Configuration:** Two-seat light aircraft; 600 kg is used as a screening case, not yet the governing Eidolon MTOW.  
**Decision:** Do **not** lock the piezoelectric concept as the selected landing gear. Keep a conventional composite leaf-spring leg as the reference architecture and evaluate a piezoelectric-assisted variant as a research branch.

## Executive assessment

A carbon-composite leaf spring is a credible lightweight landing-gear architecture, but the claim that adding piezoelectric fibres gives adaptive landing-gear stiffness with a mass penalty measured only in grams is not established. Piezoelectric materials generally produce small free strains, require electrical drive and electrodes, and do not automatically provide the displacement, force, energy absorption, or damping needed for aircraft touchdown. A stiff piezo actuator may alter local strain or provide sensing/limited actuation; it should not be assumed to replace a damper or absorb the landing energy.

A passive spring stores and returns energy. It does not inherently dissipate enough energy to prevent rebound. An active or semi-active system needs a credible mechanism for dissipating or controlling energy, plus sensors, control logic, power electronics, wiring, environmental protection, fault handling, and a safe passive mode. All of these count toward mass, reliability, maintenance, and certification burden.

Therefore this study models the *landing-energy envelope* and defines the evidence needed to compare:
1. a conventional composite leaf-spring baseline;
2. a composite spring with a separate passive dissipative element;
3. a piezoelectric sensing/actuation research concept, with no performance credit until supported by actuator data and tests.

## Requirements and boundaries

- Screening MTOW: 600 kg.
- Aircraft configuration, landing mass, wheel geometry, number of legs, tyre compliance, lift during touchdown, sink speed, gear stroke, and load-sharing are not yet established.
- The 600 kg figure does not by itself establish regulatory eligibility. The applicable jurisdiction, certification date, category rules, stall-speed and other criteria must be checked. The US light-sport certification framework changed in 2026; do not use a generic “LSA weight class” label as a universal legal conclusion.
- This is a conceptual energy screen only. It is not a structural sizing, stress, fatigue, composite-layup, attachment, or airworthiness analysis.

## Screening model

At touchdown, the vertical kinetic energy associated with an assumed effective mass is:

`E_vertical = 0.5 * m_effective * v_sink^2`

For screening only, define:

`m_effective = MTOW * energy_mass_fraction`

and assign a fraction of this energy to the gear set being evaluated. This simplified model does **not** represent the full landing-energy balance. It omits aircraft lift during compression, tyre energy absorption, geometry, drag, rebound, nonlinear spring response, damping, runway slope, and dynamic load distribution.

If an assumed gear stroke `s` absorbs energy `E_gear`, its average resisting force from this energy alone is approximately:

`F_average = E_gear / s`

For a linear spring storing `E = 0.5*k*s^2`, the equivalent stiffness is:

`k_equivalent = 2*E_gear/s^2`

and the ideal linear spring end force is `F_end = k_equivalent*s`. These quantities are screening indicators, not design loads or a sizing prescription. Peak force may differ substantially.

The script sweeps illustrative sink speeds, energy-share assumptions, and strokes. All are labelled as assumptions and should be replaced by requirements from the applicable standard, design brief, and verified landing-gear configuration.

## What would make the piezo concept credible?

Before assigning any mass or performance benefit, obtain or measure:
- actuator free strain and blocked force at the intended voltage and temperature;
- usable stroke under preload and realistic dynamic loading;
- bandwidth and response time under load, not just an unloaded datasheet value;
- energy consumption, driver/electronics mass, insulation and wiring mass;
- behaviour under loss of power, sensor faults, short/open circuit, moisture, impact damage, and temperature extremes;
- fatigue life, bond durability, inspection method, lightning/EMI compatibility, and repairability;
- full-system mass including protection, connectors, controller, sensors and redundancy;
- drop-test evidence for force-displacement, energy dissipation, rebound, and repeatability.

The control concept must be defined precisely. “Pre-tension milliseconds before impact” is not enough: the actuator must produce the required change in force or geometry quickly enough under load, and the control system must detect touchdown robustly without creating a destabilizing response.

## Preliminary decision matrix

| Criterion | Composite leaf spring | Spring + passive damper | Piezo-assisted research concept |
|---|---|---|---|
| Mass | Reference; must be calculated | Adds damper and mounts | Unknown; include full system |
| Energy storage | Yes | Yes | Piezo element is not a substitute for the primary spring |
| Energy dissipation | Limited unless paired with damping | Can be designed for dissipation | Not established; actuator/sensor alone does not guarantee damping |
| Complexity | Low to moderate | Moderate | High |
| Evidence maturity | Composite leaf-spring landing gear has published design/test literature | Established general engineering approach, aircraft-specific design still required | Requires actuator/system-level evidence |
| Fail-safe behaviour | Passive | Can remain passive if properly designed | Must be demonstrated, including power-off mode |
| Current project status | Baseline to model | Comparison candidate | Experimental branch only |

## Recommended next work

1. Define landing requirements and the applicable airworthiness/certification basis.
2. Establish the aircraft's landing mass, main/nose gear load distribution, tyre assumptions, sink-speed case, stroke, and allowable loads.
3. Create a baseline composite leaf-spring energy and structural model.
4. Add a damping model and evaluate rebound/energy dissipation.
5. Only then compare a piezo-assisted concept using real actuator data and a complete system mass estimate.
6. Validate the model against drop tests or suitable published test data before using it for design decisions.

## References

- CASA, “About Light Sport Aircraft”: https://www.casa.gov.au/aircraft/sport-aviation/light-sport-aircraft/about-light-sport-aircraft
- EASA, “Light Sport Aircraft”: https://www.easa.europa.eu/en/the-agency/faqs/light-sport-aircraft
- FAA, “Light-Sport Category Aircraft”: https://www.faa.gov/aircraft/gen_av/light_sport
- Kim & Hur, “Optimum design and experiment of composite leaf spring landing gear for electric aircraft,” Chinese Journal of Aeronautics (2020), https://doi.org/10.1016/j.cja.2020.03.010
- SAE AIR5552A, “Development and Qualification of Composite Landing Gears” (revised 2025-11-26), https://www.sae.org/standards/content/air5552a/

These references support background and methods, not the specific proposed piezo-ribbon architecture.
