# Project Eidolon: Requirements and Design Baseline

**Status:** preliminary design; not a certified or experimentally validated aircraft.

This document separates mission requirements from model inputs and calculated results. Values marked *provisional* must not be presented as measured or validated aircraft properties.

## 1. Mission requirements and evolved ambitions

The design history contains an original mission baseline and a later, more aggressive architecture proposal. They must not be silently combined because the mass and wing-loading values do not currently close to one consistent configuration.

### Original mission baseline

| Parameter | Original target | Notes |
|---|---:|---|
| Maximum take-off mass (MTOW) | 750 kg | Mission design limit used by the current constraint script |
| Empty mass | ≤550 kg | Target, not yet demonstrated by a closed mass budget |
| Useful load at these two limits | 200 kg | Must cover occupants, usable fuel, and other useful load as defined by the final mass statement |
| Range | 800 km | Must be verified with a consistent mission profile and fuel model |
| Cruise speed | 200 km/h | Nominal cruise target; altitude assumed to be approximately 1,500 m for the current constraint model |
| Maximum speed | 225 km/h | Current constraint model evaluates this at sea level; confirm the intended requirement altitude |
| Sea-level rate of climb | 3.0 m/s | Mission requirement |
| Service ceiling | 3,000 m | Current model uses 0.508 m/s (100 ft/min) as the ceiling ROC criterion |
| Stall speed | ≤85 km/h | Preliminary landing/stall requirement; configuration and applicable standard require confirmation |

### Later ambition recorded in the conversation

| Parameter | Later ambition | Status |
|---|---:|---|
| MTOW | 705.7 kg | Proposed in the later structural-sizing discussion; not reconciled with the original 750 kg baseline |
| Empty mass | 500 kg | Stretch target; not demonstrated by a component mass budget or structural analysis |
| Range | 1,000 km | Stretch target; not demonstrated by a closed mission fuel calculation |
| Fuel tanks | 25 L | Proposed later concept; usable fuel, density, reserves, and mission feasibility still need checking |
| Ultimate structural load factor | +4.4 g | Proposed preliminary structural-sizing input; applicable design category/load cases need confirmation |
| CG envelope | 20–30% MAC | Proposed target to verify across loading and fuel states, not an established safe envelope |

**Configuration decision still required:** choose whether the next sizing iteration is to preserve the original 750 kg / 800 km requirements or formally promote the later 705.7 kg / 1,000 km concept to the governing baseline. Until then, the supplied constraint script deliberately remains on the original 750 kg mission baseline. Do not claim that the later ambitions have been achieved.

## 2. Geometry and aerodynamic inputs

| Input | Current working value | Status / rationale |
|---|---:|---|
| Candidate wing loading, W/S | 520 N/m² | Candidate point carried forward from the design plan; not yet proven optimal |
| Implied wing area at 750 kg MTOW | ≈14.14 m² | Derived from MTOW and candidate wing loading |
| Aspect ratio, AR | 8.55 | Provisional geometry input; reconcile with the final CAD/XFLR5 geometry |
| Aircraft-level parasite drag coefficient, CD0 | 0.024 | Provisional baseline chosen from the design-history values; sensitivity over 0.022–0.025 is recommended |
| Oswald efficiency factor, e | 0.80 | Provisional assumption; not measured or validated |
| Landing-configuration maximum lift coefficient, CLmax | 1.8 | Provisional assumption from the original brief; verify flap/airfoil configuration and evidence |
| Climb speed for the 3.0 m/s climb constraint | 32 m/s | Assumption retained from the sizing discussion; sensitivity analysis required |
| Propeller efficiency | Unknown | Do not hard-code a “verified” value until a credible propeller model or reliable test/manufacturer data supports it |

The atmosphere values used by the current conceptual constraint script are 1.225 kg/m³ at sea level, 1.0581 kg/m³ at the nominal cruise condition, and 0.9093 kg/m³ at 3,000 m. They are approximations from the project notes, not a complete atmospheric model.

## 3. Design and analysis ambitions

1. **Constraint sizing:** calculate the cruise, maximum-speed, climb, service-ceiling, and stall constraints. Plot required thrust-to-weight ratio against wing loading, identify the governing constraint, and document the candidate design point.
2. **Airfoil trade study:** compare the legacy NACA 23012 and the selected NACA 63-415 at matched Reynolds numbers and analysis settings. Report the actual polar results rather than presuming a fixed percentage improvement.
3. **Finite-wing aerodynamics:** use XFLR5 to analyze the current wing geometry with the NACA 63-415 sections. Record geometry, Reynolds-number assumptions, solver settings, convergence/limitations, and exported polars.
4. **Propulsion matching:** model or source available propeller thrust and power over the speed range, then compare available thrust with aircraft drag at compatible operating conditions. Treat the current BEMT code as exploratory until independently checked.
5. **Mass and centre-of-gravity closure:** develop a component mass budget, occupant/fuel allocation, structural load assumptions, and CG travel envelope. Do not claim a 500 kg or 550 kg empty mass until the budget supports it.
6. **Range verification:** calculate mission fuel fraction/range using consistent engine, propeller, cruise, reserve, and payload assumptions. Do not claim 800 km capability until the calculation is closed.
7. **Integration:** connect the verified sizing, aerodynamic, propulsion, mass, and CG outputs to the CAD configuration and document revision history.

## 4. Evidence status

- **Requirement:** a target the design must satisfy.
- **Assumption:** an input used because stronger evidence is not yet available.
- **Calculated result:** an output produced by a stated model; its credibility depends on model validity.
- **Validated result:** a result checked against suitable independent evidence, experimental data, or a verified method.

The NACA 63-415 XFLR5 files are preliminary simulation outputs. A wing polar is not the complete aircraft drag polar, and a successful solver run does not by itself prove maximum speed, climb, range, or engine suitability.
