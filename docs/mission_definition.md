# Project Eidolon: governing mission definition

**Revision:** 0.1, 31 October 2026  
**Status:** working mission for preliminary sizing; several mass, reserve, and operating assumptions still need owner confirmation.  
**Regulatory context:** India / DGCA to investigate; applicable category and certification/design basis are not determined.

## Design objective

Find the **lowest feasible take-off mass** for a two-seat aircraft that can complete the governing mission and meet the performance guardrails below. MTOW is an output of the sizing process, not a preset 600 kg, 705.7 kg, or 750 kg cap. The optimization must include payload, fuel and reserve, airframe/engine installation mass, and any changes in structure, wing area, landing gear, and systems caused by mass changes.

Do not minimize mass by quietly reducing occupant payload, fuel reserve, structural margins, durability, or required performance. Report the assumptions and trade-offs that define the feasible solution.

## Governing mission inputs

| Input | Working value | Status |
|---|---:|---|
| Occupants | 2 | User-selected mission requirement |
| Occupant mass | 80 kg each | User-confirmed working assumption |
| Baggage | 10 kg | User-confirmed working assumption |
| Design range | 1,000 km | User-selected target; mission definition and reserve treatment remain open |
| Cruise speed | 230 km/h | User-selected target; use TAS initially, confirm final convention and power condition |
| Cruise altitude | TBD | 3,000 m is the ceiling, not the cruise condition. First comparison sweeps sea level, 1,500 m historical reference, and 3,000 m. |
| Reserve and alternate fuel | TBD | Must be set from the agreed mission and regulatory/design basis; do not assume zero |
| Maximum take-off mass | Optimized output | No numerical MTOW limit selected |
| Baggage/fuel loading states | TBD | Needed for mass statement and CG analysis |

The working payload is 160 kg occupants plus 10 kg baggage, separate from fuel and aircraft empty mass. Range cannot be accepted until its segments, wind allowance, reserve, and alternate policy are defined.

At 230 km/h, a 1,000 km still-air cruise leg takes about 4.35 hours before climb, descent, wind, or reserve. A historical 25 L tank proposal would allow only about 5.75 L/h across that idealized leg, before reserve. This is a screening check, not a fuel-flow model; it flags the 25 L proposal as unsubstantiated for the selected mission. ULPower’s [product page](https://ulpower.com/en/engines/ul520/ul520is) gives a rough cruise-consumption estimate around 25 L/h for the UL520 family, dependent on aircraft and operating conditions; using that only for scale gives roughly 109 L for 4.35 hours before reserve. Obtain the selected engine’s applicable operating/fuel map before setting tank volume.

Using the project’s historical approximate fuel density of 0.72 kg/L, that UL520 screening case represents about 78 kg of cruise fuel. Adding the confirmed 170 kg people-and-baggage payload and the historical 500 kg empty-mass ambition gives about 748 kg take-off mass before reserve, unusable fuel, or any omitted equipment. This does not prove a particular aircraft mass, because the engine fuel-flow estimate and aircraft power required are not validated. It does show that 705.7 kg MTOW / 500 kg empty mass cannot be carried forward as a closed design under this UL520 mission scenario.

## Performance guardrails carried from project history

| Constraint | Working value | Status / action |
|---|---:|---|
| Sea-level rate of climb | ≥3.0 m/s | Historical requirement; define mass, speed, and configuration condition |
| Service ceiling | 3,000 m | Historical requirement; define ceiling ROC criterion and mass |
| Stall speed | ≤85 km/h | Historical requirement; confirm speed type, landing configuration, and applicable basis |
| Maximum speed | Open; must exceed 230 km/h if 230 km/h is cruise | The earlier 225 km/h target conflicts with the new cruise target; retain only as history until clarified |
| Structural load factors | TBD | Earlier +4.4 g is an unverified assumption, not a governing structural requirement |

## First constraint sweep

The new [`mission_constraint_sweep.py`](../scripts/mission_constraint_sweep.py) evaluates the 230 km/h TAS cruise requirement at sea level, 1,500 m, and 3,000 m, alongside the historical climb, ceiling, and stall constraints. Its inputs remain the provisional `CD0 = 0.024`, `AR = 8.55`, `e = 0.80`, `CLmax = 1.8`, and 32 m/s climb speed.

At the historical 520 N/m² wing-loading point, it gives required T/W values of 0.125 at sea-level cruise, 0.111 at 1,500 m cruise, 0.099 at 3,000 m cruise, 0.161 for the 3.0 m/s sea-level climb case, and 0.080 for the 3,000 m ceiling case. The provisional stall boundary is 615 N/m². For a propeller-efficiency sensitivity of 0.75 / 0.80 / 0.85, estimated shaft power per aircraft mass at 1,500 m cruise is 92.6 / 86.8 / 81.7 W/kg; at sea-level cruise it is 104.5 / 97.9 / 92.2 W/kg. These are required-power scenarios only—the model does not include engine power derating, cooling drag, a full-aircraft drag build-up, or a selected mass. It cannot yet decide between the 100 hp and 200 hp engine cases.

This says only that the climb curve governs at the 520 N/m² point under the simplified T/W model; cruise can govern required shaft power depending on altitude and efficiency. The analysis does not select a wing loading, engine, wing area, or MTOW.

- [Constraint sweep graph](../results/constraints/mission_constraint_sweep.svg)
- [Full constraint sweep data](../results/constraints/mission_constraint_sweep.csv)

## Sizing sequence

1. Confirm cruise altitude and speed convention, range profile, reserves, runway assumptions, and maximum-speed requirement. Occupant and baggage working masses are currently 2 × 80 kg plus 10 kg.
2. Set an initial outer geometry and engine/propeller installation alternatives. Keep at least a 100 hp reference and a 200 hp UL520iS sensitivity case until power sizing selects among them.
3. Estimate mass with an itemized component build-up and explicit uncertainty. Use correlations only as cross-checks, not as a substitute for component mass accounting.
4. Iterate gross mass, wing area/loading, structure, propulsion, fuel, and payload until the weight statement closes.
5. Run the aerodynamic and performance constraints at the resulting mass and stated atmospheric conditions; revise the configuration and repeat.
6. Compare the tractor and pusher installations against the same closed mass and mission case. Include propeller installation performance, cooling, structural mass, CG, and fuel use.
7. Report a feasible mass range and sensitivity to uncertain empty mass, drag, engine/propeller performance, and reserves. Do not report a single precise optimized MTOW from unvalidated inputs.

## Acceptance criteria for a first sizing pass

- Every mission segment, occupant/baggage mass, fuel reserve, and cruise operating point has a stated value and source or is clearly marked unresolved.
- Empty mass is built up by component with installation boundaries and uncertainty; it is not a guessed fixed fraction presented as fact.
- Take-off mass closes as empty mass + occupants + baggage + usable/unusable fuel + other required equipment, with definitions stated.
- CG is checked for empty, take-off, landing, and relevant loading/fuel states.
- The 1,000 km range and 230 km/h cruise are evaluated together with the same payload and reserve assumptions.
- Required climb, ceiling, stall, and maximum-speed conditions are evaluated at compatible mass, altitude, atmosphere, and configuration.
- Engine/propeller and tractor/pusher comparisons use the same mission; all model limits and uncertainty are visible.
- The result is explicitly labeled conceptual preliminary sizing, not certification, flight performance, or construction data.

## Historical targets kept for comparison only

- 750 kg MTOW / 550 kg empty / 800 km range / 225 km/h maximum speed: original project baseline.
- 705.7 kg MTOW / 500 kg empty / 1,000 km range: later stretch proposal.
- 600 kg: a later landing-gear screening mass, not the aircraft's selected MTOW or a demonstrated Indian regulatory category.

None of these historical mass values is currently the governing MTOW. The old constraint chart remains a historical 750 kg case until it is replaced by a mass-closure iteration.
