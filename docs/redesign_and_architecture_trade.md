# Eidolon redesign: mission, benchmark, and architecture trade

**Status:** preliminary decision framework, 31 October 2026. No aircraft configuration or engine is selected by this document.

## Design direction

The owner’s current priority is a useful two-person aircraft optimized first for range and efficiency. India is the jurisdiction to investigate, with DGCA as the regulator. The numeric mission and applicable airworthiness/certification basis are not yet frozen. Until they are, the existing 750 kg / 800 km analysis remains a historical reference case, and 705.7 kg / 1,000 km remains an unverified ambition.

Do not call the aircraft an Indian “LSA” or infer its regulatory category from a 600 kg mass. Ask DGCA or an appropriately qualified Indian airworthiness specialist to establish the applicable approval path and design basis before using certification language. DGCA’s airworthiness procedures describe issuance of a certificate of airworthiness for a complete aircraft against its type design and a safe-for-flight finding; this project is not at that stage.

## Why DarkAero 1 is ahead today

The gap is primarily **program maturity and engineering integration**, not one missing airfoil, engine, or propeller trick. Eidolon currently has a concept-level sizing script, preliminary wing-only XFLR5 outputs, an exploratory BEMT script, and no closed mass/CG/range or structure model. DarkAero reports a physical prototype, taxi testing, ongoing ground-test development, manufacturing equipment/capacity, and design reviews directed at production. Their September 2026 update describes landing-gear drop-test fixture fabrication and structural ground-test work.

DarkAero’s headline performance figures are not a fair measured-versus-measured comparison: its FAQ explicitly describes performance figures as calculated projections that remain to be proven in flight. Treat it as a benchmark for disciplined integration, weight reduction, testing, and manufacturing development—not as evidence that Eidolon can achieve the same speed or range by copying a component.

The practical areas where Eidolon most needs to catch up are:

1. A single mission and controlled configuration baseline.
2. A mass statement and CG envelope tied to actual components and loading cases.
3. Whole-aircraft aerodynamic drag, including cooling, canopy, gear, propeller and interference effects.
4. Engine/propeller matching over takeoff, climb, cruise and altitude—not a single assumed efficiency.
5. Structural load paths, laminate/metal sizing, joints, fatigue, damage tolerance and landing loads.
6. Packaging and maintainability: occupants, visibility, egress, cooling, fuel, controls and service access.
7. Reproducible verification: model inputs, checks, test plans, uncertainty and design reviews.
8. Manufacturing process definition and inspection. A visually impressive CAD model is not a manufacturing plan.

## Engine comparison: do not select by horsepower alone

| Candidate/reference | Published rating and weight | What the numbers mean here |
|---|---|---|
| Rotax 912 iS/iSc Sport reference | 100 hp; 63.6 kg for the engine with reduction gearbox and overload clutch | The manufacturer lists other installation items separately, including exhaust, mount, external alternator, air guide and fuel pumps. The current Eidolon baseline is sized around roughly 100 hp, not yet proven adequate. |
| ULPower UL520iS / DarkAero reference | 200 hp; ULPower lists 108 kg installed weight including starter and alternator | This is twice the nominal power and materially more engine mass than the 100 hp reference. The installation boundary differs from Rotax’s published 63.6 kg figure, so a valid comparison must normalize to a complete firewall-forward mass including mount, exhaust, cooling, oil, propeller/governor, controls, electrical and fuel-system items. |

These are manufacturer-published figures, not an apples-to-apples installed-system comparison. The UL520iS could improve climb and high-speed capability **if** the airframe, propeller, cooling, structure, fuel capacity, and mission support it. It does not automatically improve range or efficiency. If the airframe needs 100 hp to meet its efficient cruise point, selecting 200 hp adds engine and installation mass and may invite higher speed, drag, fuel burn, and structural requirements without solving a real requirement.

**Recommendation:** retain a 100 hp class engine as the reference case while reopening power sizing from the governing mission. Add the 200 hp UL520iS as a sensitivity/trade case, not the new baseline. Compare both at equal mission payload, range, reserve, and takeoff/climb requirements using complete installation mass and manufacturer power/fuel maps. Do not size Eidolon around DarkAero’s engine before proving the required power.

## Tractor versus pusher propeller

Moving the propeller aft can improve packaging and appearance, keep the nose clear, and avoid some tractor-propeller/fuselage or wing slipstream interactions. Those benefits depend on the airframe layout. A pusher propeller commonly ingests the fuselage boundary layer and disturbed wake; installed efficiency, noise/vibration, cooling flow, propeller clearance, aft-CG management, engine access, and crash/load-path concerns can offset any reduction in external drag. A pusher layout is not a free drag reduction.

DarkAero 1 itself uses a **tractor** propeller. DarkAero publicly discussed why a pusher had been hypothesized for its mission, then retained the tractor arrangement after considering the aircraft-specific trade and cooling installation. That makes the right lesson “compare the installed aircraft,” not “copy a pusher because it looks cleaner.”

Available tests are configuration-specific. NASA’s historical wing/nacelle tests found that adding the wing reversed the isolated-nacelle comparison in favor of the tractor installation. A 2024 NASA Ames/Army pusher-fuselage wind-tunnel study found an installed pusher efficiency deficit relative to an isolated propeller, shrinking at higher speed. Other arrangements can favor a pusher, which is why Eidolon must compare its own geometry rather than transfer a generic percentage.

For the current high-wing/conventional-tail concept, there is not yet enough frozen geometry to judge the aft propeller’s wake, tail interaction, cooling, or clearance. A pusher can also require a longer shaft or aft-mounted engine structure depending on where the engine sits; that may affect mass, torsional dynamics, maintenance and crashworthiness. A larger or more powerful engine does not compensate for those issues by itself.

**Recommendation:** make tractor the analysis control and pusher a serious alternate. Compare both with the same outer mold line, mass/payload, engine, propeller diameter/RPM and mission conditions. Estimate installed propeller performance and whole-aircraft drag, cooling, structure, CG, noise and clearance in each. Select only if the pusher’s *net mission result* wins after added mass and installation losses.

## Decision sequence and gates

### Gate 0 — freeze the mission and regulatory question

Write one requirement sheet: two occupants and their design masses, baggage, range with reserve, cruise speed/altitude, climb, ceiling, takeoff/landing distance, runway surface, useful fuel, environmental assumptions, and intended use. Confirm the DGCA approval/certification path with a qualified source. Keep old and stretch missions as separate cases.

**Accept when:** every requirement has a source/owner, units, condition, and priority; the mass and payload terms are unambiguous; no model combines incompatible cases.

### Gate 1 — close weight, geometry and CG at concept level

Create an itemized mass budget with confidence bands and longitudinal stations. Reconcile wing area, span, aspect ratio, airfoil stations, washout, propeller/engine location, occupants, fuel, and gear against one CAD/geometry revision.

**Accept when:** MTOW, useful load, fuel, and CG close for empty, full-fuel, reserve-fuel, and occupant/baggage cases, with uncertainties visible.

### Gate 2 — compare propulsion and installation architectures

For tractor and pusher, model 100 hp and 200 hp engine cases using manufacturer power/torque/fuel maps, altitude derating, propeller maps, and normalized firewall-forward mass. Compare takeoff/climb margin, cruise power/fuel flow, range, noise, cooling and failure/maintenance issues.

**Accept when:** each case meets the same mission/payload/reserve definition or its shortfall is shown; no engine efficiency or airframe performance number is treated as a free constant.

### Gate 3 — connect aerodynamics and structures to performance

Rerun the current XFLR5 model after reconciling its saved geometry with the newer −2° washout and 63-412 tip blend. Then develop whole-aircraft drag increments for fuselage, canopy, cooling, gear, controls, and interference. Define preliminary load cases and size the airframe/gear only to the selected design basis.

**Accept when:** geometry and outputs have matching revisions, uncertainty and solver limits are stated, and performance predictions use whole-aircraft drag and compatible propulsion data.

### Gate 4 — verify, test, and document

Plan independent checks and appropriate ground tests. For landing gear, establish a conventional baseline first; do not assign a piezoelectric mass or performance benefit without component data and system-level evidence. Track model versions, source data, decisions, reviews and test results.

**Accept when:** another reviewer can regenerate the reported preliminary results and trace every design claim to inputs, calculations, and evidence status.

## Immediate project actions

1. Approve the mission sheet and the Indian regulatory question; leave unresolved numbers explicitly open until agreed.
2. Reconcile the updated XFLR5 geometry with the dated aerodynamic results before using those results downstream.
3. Produce the component mass/CG budget and make it the central integration artifact.
4. Replace the current unsupported “locked” engine/propeller language with comparative cases until validated.
5. Build a matched tractor/pusher installation trade and a 100/200 hp sensitivity using the same mission and complete installation mass.
6. Defer claims of LSA eligibility, 500 kg empty mass, 1,000 km range, 230 km/h cruise, propeller efficiency, or piezo gear advantage until their specific acceptance evidence exists.

## Sources

- DarkAero, [FAQ](https://www.darkaero.com/faq/), including engine selection, prototype status, and the qualification that performance figures are projections pending flight testing.
- DarkAero, [September 2026 update](https://www.darkaero.com/updates-files/sept-2026.html), on landing-gear and structural ground-test work.
- DarkAero, [September 2023 update](https://www.darkaero.com/updates-files/sept-2023.html), on its pusher-versus-tractor assessment and tractor-propeller configuration.
- ULPower, [UL520iS specifications](https://ulpower.com/en/engines/ul520/ul520is).
- BRP-Rotax, [912 iS/iSc Sport specifications](https://www.flyrotax.com/products/912-is-sport-isc-sport).
- NASA Ames/Army, [pusher propeller and fuselage wind-tunnel testing](https://hdl.handle.net/20.500.11881/4572) (2024).
- NASA, [comparison of pusher and tractor propellers mounted on a wing](https://ntrs.nasa.gov/api/citations/19850012809/downloads/19850012809.pdf?attachment=true) (reported historical test summary).
- DGCA, [Airworthiness Procedures Manual](https://www.dgca.gov.in/digigov-portal/Upload?attachId=xYHIGwwp7Y%2FIem%2FtSle%2BXw%3D%3D&baseLocale=en_US&flag=iframeAttachView), April 2025, for the Indian airworthiness/certificate context.
