# Design decisions

Each entry follows the same pattern: **decision → options considered → evidence → why → what would change our mind.**
Numbers are from the current `run_all.py` output (files in `results/`). If a number here and a file disagree, the file is right.

D1-D10 were taken on the **first closure**, with glass-fibre sandwich skins (studies 01-16). D13 re-closes the same geometry with carbon sandwich skins, which is the **final aircraft**; D1-D10 still hold for it (the carbon span check is in D13).

| # | Decision | Study |
|---|---|---|
| [D1](#d1-mission-mtow-and-certification-basis) | 750 kg, 2 seats, CS-VLA envelope, +4.4 g utility loads | 02, 12 |
| [D2](#d2-mass-is-estimated-bottom-up-and-the-unknown-is-measured) | Mass estimated bottom-up from sized structure; the unknown part measured on 3 certified trainers | 01 |
| [D3](#d3-wing-section-naca-63-415-blending-to-63-412) | NACA 63-415 root → 63-412 tip | 03 |
| [D4](#d4-wing-planform-1325-m-115-m-taper-06-2-washout) | 13.25 m², 11.5 m span (AR 10), taper 0.6, −2° washout | 04, 05 |
| [D5](#d5-spin-resistant-drooped-outboard-leading-edge) | Drooped outboard leading edge | 04 |
| [D6](#d6-tail-conventional-low-tail-ventral-strake-40-elevator) | Conventional low tail + ventral strake, 40 % elevator | 09, 10 |
| [D7](#d7-drag-reduction) | Faired gear, laminar wing, compact fuselage | 06 |
| [D8](#d8-engine-rotax-912-isc) | Rotax 912 iSc | 08 |
| [D9](#d9-propeller-175-m-3-blade-constant-speed) | 1.75 m, 3-blade, constant speed | 07 |
| [D10](#d10-glass-fibre-leaf-spring-gear-with-piezo-health-monitoring) | S-glass leaf-spring gear; piezo for sensing and health monitoring only | 13 |
| [D11](#d11-structure-checked-at-66-g-tip-deflection-flagged) | Structure checked at 6.6 g; tip deflection flagged | 17 |
| [D12](#d12-fuselage-length-710-m) | Fuselage body 7.10 m | 19 |
| [D13](#d13-carbon-sandwich-airframe-for-the-final-aircraft) | Carbon sandwich airframe, vacuum infusion; cost calibrated on Hansa-NG | 18, 20 |
| [D14](#d14-engine-re-checked-on-the-carbon-airframe-912-isc-stays) | Engine re-checked on the carbon airframe: 912 iSc stays; hot days via a boost option | 15, 23 |

---

## D1. Mission, MTOW and certification basis

**Decision.** Two seats side by side, MTOW **750 kg**, single piston engine. Design to the EASA **CS-VLA** envelope: MTOW ≤ 750 kg, stall speed in landing configuration ≤ 83 km/h CAS. Use **CS-23 utility-category** loads: limit +4.4 g / −1.76 g, ultimate ×1.5.

**Options.** 600 kg (light-sport class), 705.7 kg (the team's later idea), 750 kg (the original brief).

**Evidence and reasons.**
- The benchmark Hansa-NG is a 750 kg, 2-seat, Rotax 912 iSc trainer. Using the same MTOW makes the comparison fair: any improvement has to come from design, not from a different category.
- A trainer is used for spin and stall training, so +4.4 g utility loads are used rather than the +3.8 g of CS-VLA. The V-n diagram (study 12) has V_A = 202, V_C = 217 and V_D = 312 km/h. The CS-23 gust line at V_C gives n = 4.42, 0.5 % above the 4.4 manoeuvre limit. The wing is sized to 1.5 × 4.4 = 6.6 g ultimate; the 0.5 % gust excess is a known item for the detailed stress phase (about 0.04 kg of spar cap).
- Design payload: 2 × 77 kg (the standard occupant mass) + 10 kg baggage = 164 kg.

**What would change it.** A 600 kg variant would need a new engine trade. Re-running study 08 with `mtow=600` would show it.

---

## D2. Mass is estimated bottom-up, and the unknown is measured

**The question we had to answer.** Eidolon is a different aircraft from Hansa-NG: a longer, thinner wing, a carbon spar, glass leaf gear, a different tail. A statistical equation fitted to 1970s metal aircraft (Raymer's GA equations, which we used first) cannot see those differences. It just scales with area and aspect ratio.

**Decision.** Estimate the empty mass **bottom-up**, from structure that is actually sized, and treat what a bottom-up count always misses as **one measured unknown with a standard deviation**, not as a hidden fudge factor (study 01, `eidolon/structures.py`).

**How each part is estimated.**

| Group | Method | Eidolon |
|---|---|---:|
| Wing | CFRP spar caps sized so the cap stress equals the allowable (550 MPa) under the **6.6 g ultimate bending moment**, using the spanwise lift shape from our own lifting-line solution; shear webs sized for the shear (120 MPa biax); sandwich skins by wetted area (2.05 kg/m²); ribs, flaps, ailerons, root fittings, tank sealing and paint by area or count | 85.6 kg |
| Tails | Spar sized for the tail load at V_A, skins by area; ventral strake as a sandwich panel | 15.7 kg |
| Fuselage | Sandwich shell by wetted area; floor, keel, carry-through box, bulkheads, 9 g seat structure, canopy | 86.4 kg |
| Landing gear | S-glass leaf legs sized by CS-23.473 energy (D10) at a fatigue allowable; wheels, brakes and nose gear from catalogues | 29.8 kg |
| Powerplant | Engine data sheet + propeller, governor, cooling, mount, cowling, exhaust, fuel system | 108.6 kg |
| Systems and furnishings | Controls, electrical, avionics, seats, cabin heat (catalogue items) | 55.5 kg |
| **Certified-trainer class allowance** | measured, see below | **148.8 ± 11.6 kg** |
| **Empty mass** | | **530 kg** |

**The class allowance is the honest unknown.** A bottom-up count of a certified aircraft always comes out light: doublers, inserts, sealant, wiring harnesses, minimum-gauge plies, repairs, certification margins. We measured how much, by running the *same* bottom-up method on three certified two-seat trainers with published empty masses:

| Aircraft | Published empty | Bottom-up count | Gap |
|---|---:|---:|---:|
| Hansa-NG | 540 kg | 378 kg | 162 kg |
| Aquila A210 | 500 kg | 358 kg | 142 kg |
| Diamond DV20 Katana | 505 kg | 363 kg | 142 kg |
| *Pipistrel Virus SW 100 (light-sport, not used)* | *289 kg* | *343 kg* | *−54 kg* |

The mean gap is **148.8 kg with a standard deviation of 11.6 kg**. Pipistrel, a microlight built to lighter rules, comes out 54 kg *heavy*: the method sees the category difference, which is a good sign that it is measuring something real.

**Validation by leave-one-out.** Fit the allowance on two aircraft, predict the third:

| Predicted aircraft | Error |
|---|---:|
| Hansa-NG | −20 kg (−3.7 %) |
| Aquila A210 | +10 kg (+1.9 %) |
| Diamond DV20 Katana | +11 kg (+2.1 %) |

RMS error **14.2 kg**. Raymer's calibrated GA equations give 550 kg for Eidolon, inside the Monte-Carlo band, as a cross-check.

**Mass as a random variable.** Every item carries a 1σ spread (3 % for the engine data sheet, 10-30 % for allowances), and the class allowance carries its measured σ. A 5,000-sample Monte Carlo gives the empty-mass distribution: **P5 500 / P50 530 / P95 560 kg** (`results/01_mass/mass_estimation.png`). Study 14 then draws the class allowance in every sample, the same draw for both aircraft, because both are certified trainers built to the same rules.

**Why this matters.** With the bottom-up model, span became cheap (the spar cap mass grows with bending moment over depth, not with AR^0.6), and the wing optimum moved from 10.25 m to **11.5 m** (D4). The old statistical model was hiding a better wing.

**What would change it.** A real layup schedule and a first-article weighing. The allowance is the number to shrink: each kilogram is worth about **18 km of range** with two crew (D4, study 14).

---

## D3. Wing section: NACA 63-415 blending to 63-412

**Decision.** NACA 63-415 at the root, blending linearly to NACA 63-412 at the tip.

**Options.** NACA 23012 (the earlier baseline, typical of GA trainers), 2412, 4412, 63-415.

**Evidence** (study 03, `results/03_airfoil/`):

| Section | t/c | max-t at | spar-box area (15-65 % c) / c² |
|---|---:|---:|---:|
| **NACA 63-415** | 15.0 % | 35 % c | **0.0663** |
| NACA 23012 | 12.0 % | 29 % c | 0.0541 |
| NACA 2412 | 12.0 % | 30 % c | 0.0540 |
| NACA 4412 | 12.0 % | 30 % c | 0.0541 |

- **Laminar flow.** The 6-series puts its minimum pressure at about 35-40 % chord, so the boundary layer sees a favourable pressure gradient over that length. In the XFLR5 polar at Re 6 M, transition stays at x/c ≈ 0.34-0.50 on the upper surface and 0.27-0.40 on the lower surface across the cruise CL range. We use only **35 % laminar** in the drag model, leaving margin for bugs, rain and manufacturing waviness. Study 14 varies it from 10 % to 45 %.
- **Structure.** At 15 % thickness the spar is 25 % deeper than a 12 % section. In the bottom-up mass model (D2) the spar-cap mass goes as bending moment ÷ depth, so this directly lightens the wing and is part of why the long span pays off.
- **Fuel volume.** The wing box holds several hundred litres. The 100 L tank uses a small part of it, so fuel volume is never a constraint.
- **Tip section 63-412.** Thinner, with the same camber line, so the zero-lift angle stays matched along the span. Its lower clmax makes the washout and the leading-edge droop more important (D4, D5).

**Status of the matched comparison.** The matched XFLR5 batch (all four sections at Re 2, 3 and 4.5 M, Ncrit 9) runs through `docs/HOW_TO_RUN_XFLR5.md`. Study 03 picks those polars up automatically. Until they exist, we do not claim a percentage drag advantage over the 23012.

**What would change it.** If the matched polars show the 63-415 losing its drag bucket at the clmax we need, we would accept 63-415 with turbulators, or switch to the 23012 and lose about 0.0010 in CD0. The tornado chart in study 14 shows what that costs.

---

## D4. Wing planform: 13.25 m², 11.5 m, taper 0.6, −2° washout

**Decision.** Area **13.25 m²**, span **11.5 m** (AR 9.98), taper 0.60, linear washout of −2° at the tip, 5° dihedral, single-slotted flaps over 62 % of the semispan.

**This overturns our first wing** (14.15 m², 11.0 m, AR 8.55) and our first carpet optimum (10.25 m, found with the statistical mass model).

**Evidence** (study 05, `results/05_wing_sizing/wing_carpet.png`). A grid of wings in area and span, each one a **fully closed aircraft**: mass (bottom-up), tail size, CG, drag, propeller and performance are all recomputed.

- **Objective:** minimise fuel per 100 km at 200 km/h. Fuel burn is what a trainer fleet pays for every hour, and it is the advantage that survives every uncertainty (study 14).
- **Constraints:** range ≥ 800 km at 200 km/h with 2 crew and baggage, 45-minute reserve; V_S0 ≤ 81.5 km/h (CS-VLA 83 km/h with a 2 % model margin); ROC ≥ 3.5 m/s; take-off to 15 m ≤ 450 m.

| | First wing | **Chosen** |
|---|---:|---:|
| S, b, AR | 14.15, 11.0, 8.55 | **13.25, 11.5, 9.98** |
| Empty mass | 534 kg | **530 kg** |
| Fuel at 200 km/h | 8.13 L/100 km | **7.84 L/100 km** |
| Range with 2 crew + bag | 712 km | **803 km** |
| Stall, landing flap | 78.5 km/h | 80.9 km/h |
| Rate of climb | 3.61 m/s | 3.70 m/s |

**Why a smaller but longer wing wins.** Less area means less skin, the heaviest wing item, and less friction drag. More span means less induced drag, and with a sized spar it costs only the extra cap material. The optimum sits on the stall boundary (the smallest area that still meets V_S0) at the span where the extra spar and skin mass stop paying for the induced-drag saving.

**Washout −2°** (study 04, `stall_progression.png`). With no twist, the first stall is at 52 % semispan. With −2°, it moves to **38 %**, inboard of the ailerons, which start at 62 %. Span efficiency is *higher* with −2° (0.979) than with none (0.969), because the 0.6 taper overloads the tip slightly and the washout corrects it. At −4° the first stall moves to 23 %, but span efficiency drops to 0.88. So −2° is the sweet spot.

**Cross-check against XFLR5.** For the untwisted 14.15 m² wing, our lifting-line code gives a lift slope 4.9 % above XFLR5's VLM2 (0.0876 vs 0.0835 per degree) and a zero-lift angle within 0.1°.

**What would change it.** A real layup could move the class allowance; the optimum span is fairly flat between 11 and 12 m, so the choice is robust to that.

---

## D5. Spin-resistant drooped outboard leading edge

**Decision.** A drooped (cuffed) leading edge on the outboard 42 % of each semispan, starting just inboard of the aileron, in the style of NASA's spin-resistance research (Cirrus SR20/22 use the same idea).

**Why.** Washout alone keeps the ailerons flying only at the moment of first stall. As the pilot keeps pulling, the stall spreads outboard quickly. A trainer is flown by students who will pull; what matters is how far beyond first stall the ailerons stay effective.

**Evidence** (study 04, `leading_edge_cuff.png`). Modelled as +0.30 on the section clmax outboard of 58 % semispan:

| Angle beyond first stall | Aileron span unstalled, washout only | With drooped LE |
|---:|---:|---:|
| +1° | 75 % | **100 %** |
| +2° | 50 % | **100 %** |
| +3° | 37.5 % | **100 %** |
| +5° | 25 % | 56 % |

Cost: about **3 drag counts** (ΔCD0 0.0003), included in every performance number.

**What would change it.** The +0.30 clmax increment is from published cuff tests, not from our own analysis. A 2-D XFLR5 run of the drooped section would replace it.

---

## D6. Tail: conventional low tail + ventral strake, 40 % elevator

**Decision.** A conventional tail with the horizontal tail low on the tail cone and the fin above it, plus a **0.18 m² ventral strake** under the tail cone. Horizontal tail **1.79 m²** (V_h = 0.50), vertical tail **1.52 m²** (V_v = 0.041), tail arm 4.35 m, **elevator chord 40 %**. The wing is placed so the aft CG has exactly 12 % MAC static margin. CG range 30.5-32.2 % MAC, neutral point 44.2 % MAC.

**Method** (study 09, `eidolon/empennage.py`; study 10, `eidolon/stability.py`). Six configurations, each one **re-closed**: tail re-sized, wing re-positioned, mass and drag recomputed. Every configuration has to pass the same criteria:
1. **Static stability:** 12 % static margin at the aft CG (neutral point from wing + fuselage + tail, with dε/dα from the wing).
2. **Landing flare at the forward CG:** full up-elevator trims CLmax with the flaps down.
3. **Take-off rotation at the forward CG:** the nose wheel lifts before the lift-off speed, using moments about the main wheels and the propeller slipstream on the tail.
4. **Spin recovery:** Bowman's tail damping power factor (NASA TN D-6575), TDPF ≥ 200 × 10⁻⁶ for a trainer. It measures how much of the fin and rudder is *not* blanketed by the horizontal-tail wake in a spin.
5. **Deep stall:** the angle at which the horizontal tail would sit in the wing wake, compared with the stall angle.

**Results** (`results/09_tail/tail_configurations.png`):

| Configuration | V_h needed | Tail mass | L/100 km | Rotates before lift-off? | TDPF ×10⁻⁶ | Deep-stall risk |
|---|---:|---:|---:|---|---:|---|
| **Conventional + ventral strake** | 0.50 | 15.7 kg | 7.84 | yes (86 vs 94 km/h) | **481** | no |
| Conventional | 0.50 | 15.2 kg | 7.81 | yes | 141 (fails) | no |
| H-tail | 0.43 | 15.8 kg | 7.79 | yes | 125 (fails) | no |
| V-tail | 0.48 | 15.2 kg | 7.78 | yes | not defined | no |
| Cruciform (HT at 40 % fin) | 0.70 | 18.5 kg | 7.90 | yes | 121 (fails) | **yes** |
| T-tail | 1.00 | 22.4 kg | 7.98 | **no** (109 vs 94 km/h) | 60 (fails) | **yes** |

**Why not a T-tail?** It looks fast, but on a propeller aircraft it sits out of the slipstream. At the forward CG the elevator cannot lift the nose wheel until 109 km/h, after the aircraft would have flown off at 94 km/h. Fixing that needs V_h = 1.0, double the tail, and it still carries a deep-stall risk.

**Why the strake?** A plain conventional tail fails the spin screen because the horizontal tail's wake blankets the lower rudder. A 0.18 m² strake under the tail cone adds side area *below* the wake, in undisturbed flow, and **triples the TDPF (141 → 481)** for about 0.5 kg and 1.5 drag counts.

**Why not V-tail or H-tail, which burn slightly less?** The differences are 0.03-0.06 L/100 km, inside the model noise. The V-tail mixes rudder and elevator and has a weak spin-recovery record (the Bonanza 35); Bowman's method does not even apply to it. The H-tail has four junctions and two fins to build and inspect. For a spin trainer, the configuration that passes every screen wins (score 0.92 vs 0.74).

**Horizontal-tail height** (`ht_height_sweep.png`). Raising the horizontal tail up the fin only makes it worse: it leaves the slipstream (bigger tail needed for rotation) and from about 24 % of fin height it enters the deep-stall band. Low is best.

**Elevator chord** (`elevator_sweep.png`). A larger elevator raises the tail's maximum down-lift, which shrinks the tail needed for rotation, but raises the hinge moment and the stick force:

| Elevator chord | Tail area needed | L/100 km | Stick force (relative) |
|---:|---:|---:|---:|
| 25 % | 2.60 m² | 7.96 | 0.68 |
| 35 % | 1.97 m² | 7.87 | 0.88 |
| **40 %** | **1.79 m²** | **7.84** | **1.00** |
| 50 % | 1.53 m² | 7.80 | 1.23 |

40 % is the knee: beyond it the fuel saving is small and the stick force rises steeply. Elevator effectiveness uses thin-airfoil τ with a 0.6 viscous factor.

**CG range note.** The seats sit close to the CG, so the CG moves only 1.6 % MAC across all loadings (`cg_envelope.png`). That is why the tail can be this small.

---

## D7. Drag reduction

**Decision.** Fully faired fixed gear (streamlined leaf legs, wheel spats, faired nose leg), a laminar wing, and a compact 7.1 m fuselage body (7.5 m overall with the spinner) built around the same 1.07 m cabin width as Hansa-NG.

**Evidence** (study 06, `drag_waterfall.png`). Both aircraft use the same component build-up and the same fitted "unmodelled" increment. The parasite drag area CD0·S falls from **0.415 m² to 0.348 m² (−16 %)**; CD0 from 0.0332 to 0.0263:

| Item | Hansa-NG [m²] | Eidolon [m²] | Driver |
|---|---:|---:|---|
| Landing gear | 0.084 | 0.027 | faired leaf legs and faired nose leg |
| Wing | 0.084 | 0.071 | 35 % vs 15 % laminar run, smaller area |
| Horizontal + vertical tail | 0.028 | 0.025 | smaller horizontal tail |
| Fuselage + canopy | 0.096 | 0.094 | similar cabin |
| Leading-edge cuff, ventral strake | — | +0.006 | spin safety costs drag |
| Unmodelled (same ΔCD0 × S) | 0.103 | 0.109 | conservative to Eidolon (larger S) |

**Honest caveat.** NAL does not publish Hansa-NG's gear details. We assumed unfaired flat spring legs with wheel spats. If its legs are already faired, the gear advantage shrinks. Study 14 draws the Hansa leg drag between 35 % and 100 % of the flat-leg value, and the fuel advantage still holds in every sample.

---

## D8. Engine: Rotax 912 iSc

**Decision.** Rotax 912 iSc Sport: 73.5 kW take-off, fuel injected, 2,000 h TBO.

**Candidates.** Each engine was re-closed in its own airframe (study 08): new installed mass, empty mass, fuel, CG, tail and wing position, plus a propeller sized to keep the static tip Mach ≤ 0.80.

| Engine | Score | L/100 km | Range 2 crew | Empty | ROC SL / 45 °C | T/O 45 °C |
|---|---:|---:|---:|---:|---:|---:|
| **Rotax 912 iSc** | **0.74** | **7.84** | **803 km** | 530 kg | 3.70 / 2.64 | 539 m |
| Rotax 914 F | 0.62 | 9.34 | 598 km | 534 kg | 4.46 / 4.10 | 397 m |
| Rotax 912 ULS | 0.60 | 9.12 | 767 km | 524 kg | 3.70 / 2.64 | 539 m |
| Rotax 915 iS | 0.36 | 10.23 | 284 km | 552 kg | 5.75 / 5.34 | 331 m |
| UL Power UL520iS (DarkAero 1) | 0.29 | 10.56 | **0 km** | **576 kg** | 8.42 / 6.59 | 299 m |

Weights: fuel burn 30 %, range 25 %, hot-day climb 15 %, hot-day take-off 10 %, empty mass 10 %, TBO 10 %. A trainer flies many hours of circuits, so fuel and range dominate. Hot-day numbers matter for Indian airfields (45 °C at 600 m).

**The 6-cylinder.** The DarkAero 1's UL520iS gives 8.4 m/s climb, but it adds 46 kg to the empty mass: heavier engine, heavier propeller, a larger tail to rotate the heavier nose. With two 77 kg occupants and 10 kg of baggage, only **10 kg of fuel** fits under 750 kg, less than the 45-minute reserve. DarkAero 1 works because it is a single-purpose speed aircraft with a 6 m² wing. On a 750 kg trainer the same engine leaves no fuel for the mission.

**What would change it.** A 915 iS with a 900 kg MTOW (a different category) would be a strong touring variant. The 912 iSc beats the 912 ULS only through BSFC: 245 vs 285 g/kWh, assumed. **The 912 iSc fuel-flow figure needs checking in the Rotax Operator's Manual**; the ranking against the ULS depends on it.

---

## D9. Propeller: 1.75 m, 3-blade, constant speed

**Decision.** A 1.75 m, 3-blade, hydraulic constant-speed propeller in the MTV-21-A class (the same diameter as Hansa-NG's).

**Evidence** (study 07). Blade-element momentum theory with Prandtl tip and hub loss, stall and drag rise:
- At 200 km/h and 1500 m: BEMT η = 0.883; the actuator-disk ideal is 0.959; **installed η = 0.81** after the 0.92 installation factor. The code asserts that BEMT never exceeds the ideal.
- 3-blade vs 2-blade at the same activity factor: +0.1 % in cruise, but **+32 % static thrust** (2,430 N vs 1,850 N). That matters for take-off and for the rotation criterion (D6).
- Our earlier result of 89.2 % (`archive/first_iteration/scripts/propulsion_bemt.py`) was computed at 230 km/h and 3000 m, with an airfoil model that never stalls. It is superseded.

---

## D10. Glass-fibre leaf-spring gear, with piezo health monitoring

**Decision.** S-glass/epoxy leaf-spring main legs. Piezo elements are used for **sensing and structural health monitoring only**.

**Why S-glass** (study 13). For a spring that must store landing energy U at the lowest mass, the material index is σ²/(Eρ). Each material was sized as a uniform-strength leaf to the CS-23.473 case: sink rate 2.47 m/s, wing lift = 2/3 W, peak gear load factor 3.0, **1,476 J per leg**.

| Material | σ²/(Eρ) [J/kg] | Mass of two legs (limit stress) |
|---|---:|---:|
| **S-glass/epoxy** | **4,900** | **3.6 kg** |
| Carbon/epoxy | 4,181 | 4.2 kg |
| E-glass/epoxy | 3,878 | 4.6 kg |
| 7075 aluminium | 546 | 32.5 kg |
| 4340 spring steel | 537 | 33.0 kg |

Carbon is stiffer, but stiffness is the wrong property for a spring. The mass model uses a fatigue allowable, which roughly doubles the leaf mass (8.7 kg for two legs); glass still wins.

**Can piezo make the gear more efficient or safer?** We checked every mechanism (`results/13_landing_gear/piezo_assessment.json`, `piezo_energy.png`):

| Use | Result | Verdict |
|---|---|---|
| Absorb landing energy (shunt damping) | full PZT coverage of the leaf: 0.62 J of 1,476 J (**0.04 %**), for 0.28 kg; 4 MFC patches: 0.08 J | no |
| Change stiffness actively | free strain ~0.1 %, millijoules | no |
| Damp nose-gear shimmy | ~1-2 % added damping to one mode | marginal; a conventional damper is lighter and certifiable |
| Harvest energy | ~8 µJ per hard landing | wakes a logger, cannot power it |
| **Hard-landing detection** | peak leaf strain ∝ sink rate; PVDF film gives 26 V at 1 m/s, 63 V at the limit | **yes**, about 80 g |
| **Structural health monitoring** | PZT wafers as Lamb-wave actuators/sensors find delaminations and impact damage in the composite leaf and its attachment | **yes** |

So piezo is a **safety sensor**, not an energy absorber. In the presentation it is one line, not a slide.

**Next step.** A drop test of a 1:1 leaf with a film bonded, to calibrate volts to sink rate and measure rebound damping.

---

## D11. Structure checked at 6.6 g; tip deflection flagged

**Decision.** Keep the load-sized structure of D2 and check it as a structure, not only as a mass (study 17, `results/17_structures/`).

**Evidence** (first closure, glass skins; the carbon airframe is within 2 %):

| Item | Load case | Result | Status |
|---|---|---|---|
| Spar caps (CFRP UD) | 6.6 g bending | at the 550 MPa allowable to 4.4 m; 40 mm² minimum gauge outboard | sized, margin 0 by construction |
| Shear webs (±45° CFRP) | 6.6 g shear | 1.1 mm at the root; 0.8 mm minimum over 70 % of the span | sized |
| Root | 6.6 g | shear 22.4 kN, bending 49.7 kN·m, cap force 288 kN (root-fitting design load), spar depth 173 mm | input to fitting design |
| Wing stiffness | 4.4 g limit | caps-only tip deflection 532 mm = 9.2 % of semispan (E = 125 GPa [A]) | **flag**: 6 % costs about 4.3 kg of cap |
| Tail cone | tail load 5.3 kN (CL_h 1.0 at V_A, ×1.5) | 16.5 kN·m, 172 MPa in the glass faces vs 250 MPa | margin +0.45, no longerons |
| Main gear leaf | CS-23.473, 2.47 m/s | 1,476 J per leg, 11.0 kN, n = 3.0 | sized (D10) |

**What it showed.** The wing is skin-driven: of 85.6 kg, the sandwich skins are 48.6 kg (57 %) and the strength-sized spar caps 7.9 kg (9 %). That is why span was cheap (D4) and why the skin laminate is the lever in D13.

**What would change it.** Skin stiffness in the deflection estimate (it is caps-only, so conservative), a torsion and flutter check, and FEA of the spar, carry-through box and fittings.

---

## D12. Fuselage length 7.10 m

**Decision.** Body length 7.10 m (7.5 m with spinner), maximum section 1.16 × 1.28 m around a 1.07 m cabin.

**Physics.** Fuselage drag is C_f × FF × S_wet with Torenbeek's wetted area S_wet = πDL(1 − 2/f)^(2/3)(1 + 1/f²) and Raymer's form factor FF = 1 + 60/f³ + f/400, f = L/D. A shorter body has less skin but a bluffer shape and a shorter tail arm, so a bigger tail; a longer one is the reverse plus more structure. At 7.10 m: f = 5.83, FF = 1.32, S_wet = 21.1 m², body drag area 0.069 m² (+0.025 m² canopy, together 27 % of the parasite drag area).

**Evidence** (study 19, `results/19_fuselage/fuselage_trade.png`). Eight bodies, 6.5-7.9 m, each re-closed (tail re-sized, wing moved, mass and drag recomputed); cabin and stations fixed:

| Length | 6.5 | 6.7 | 6.9 | **7.1** | 7.3 | 7.5 | 7.7 | 7.9 m |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| L/100 km | 7.926 | 7.883 | 7.860 | **7.841** | 7.839 | 7.841 | 7.845 | 7.851 |
| Range, km | 810 | 817 | 812 | **803** | 782 | 760 | 736 | 712 |
| HT area, m² | 2.46 | 2.15 | 1.96 | **1.79** | 1.72 | 1.66 | 1.61 | 1.56 |

**Why.** Fuel burn is flat from 7.1 to 7.5 m (within 0.03 %) and rises fast below 7 m as the tail grows. 7.10 m is the shortest body at the fuel-burn minimum, the same objective as the wing carpet. Range peaks at 6.7 m in glass, but with the carbon airframe (D13) the tank is full and range is no longer mass-limited.

**Cabin and CG.** Seats at 2.25 m sit almost on the CG (2.27-2.29 m for every loading), so the CG travels only 1.6 % MAC; that is what lets the tail be V_h 0.50 instead of the textbook 0.70.

---

## D13. Carbon sandwich airframe for the final aircraft

**Decision.** Build the skins, ribs, control surfaces, fuselage shell and cowling as carbon/foam sandwich by vacuum infusion, keeping the v1 geometry. Spar caps were already carbon; the gear stays S-glass (D10).

**Laminate** (`eidolon/structures.py`, `AIRFRAME`). Glass: 2 + 2 plies of 200 g/m² glass on 5 mm foam, 2.05 kg/m² (wing). Carbon: 2 plies of 160-200 g/m² outside (impact side), 1 inside, same core, 1.53 kg/m², keeping certified-trainer thicknesses rather than light-sport ones. Tail 1.55 → 1.20, cabin 2.60 → 2.00, cone 2.10 → 1.60, control surfaces 3.1 → 2.5 kg/m². Carbon adds 2.5 kg for lightning protection over the tank bays, electrical bonding and glass antenna windows.

**Evidence** (study 20, `results/20_materials/`):

| At 750 kg MTOW | Glass skins | **Carbon skins** |
|---|---:|---:|
| Empty mass | 530 kg | **500 kg** (wing 85.6 → 71.2, fuselage 86.4 → 73.7, tail 15.7 → 13.6) |
| Useful load | 220 kg | **250 kg** |
| Fuel with 2 × 77 kg + 10 kg | 55.7 kg | **72.0 kg (tank full)** |
| Range, 2 × 77 kg + 10 kg | 803 km | **1,098 km** |
| Range, 2 × 90 kg + 10 kg | 334 km | **884 km** |
| Mass growth before the range lead over Hansa-NG goes | 5 kg | **35 kg** |
| Fuel per 100 km at 200 km/h | 7.84 L | 7.85 L |

Re-closing also re-sizes the tail: the lighter airframe makes the crew a larger share of the mass, so the CG range widens from 1.6 to 2.8 % MAC and the horizontal tail grows from 1.79 to 1.87 m² (V_h 0.525). Static margin 12.0-14.9 %, TDPF 496 × 10⁻⁶, nose-wheel lift at 86 km/h: every screen of D6 still passes.

Carbon buys payload, range and margin, not speed: the wing is still sized by stall at 750 kg, so drag does not change. With carbon mass the wing carpet's fuel optimum moves slightly outboard (12.0 m span: 7.817 vs 7.852 L/100 km, −0.4 %), too small to redo the wing.

**Cost** (study 18, `eidolon/cost.py`). Gudmundsson's Eastlake GA cost model, one labour factor fitted so the same model gives Hansa-NG its reported ₹3.0 crore, 180 aircraft over five years. Glass ₹3.09 crore; **carbon by infusion ₹3.19 crore (+3 %)**: fabric at £20.50/m² vs £2.65/m² (+₹5.2 lakh of material), +10 % inspection (ultrasonic NDI, because carbon hides impact damage) and ₹1.8 crore of one-off material qualification over the run. Labour hours are held at the glass airframe size. Prepreg and oven cure would be ₹3.66 crore (+18 %). Per kilogram of useful load: Hansa-NG ₹1.43 lakh, glass ₹1.41 lakh, **carbon ₹1.27 lakh**; per km of range: ₹42,000, ₹38,500, **₹29,000**.

**Caveats.** The 148.8 kg class allowance was measured on glass trainers and is left unchanged (if its structural part shrinks too, empty mass would be about 488 kg; not claimed). Cost is a class-level estimate, not a quote. Carbon needs lightning protection, galvanic isolation at aluminium fittings and white paint for the Indian ramp; impact damage can be invisible, which makes the PZT monitoring of D10 more valuable.

**What would change it.** Supplier quotes, a real layup schedule and a first-article weighing. (The carbon re-run of the Monte Carlo is done: study 22, range better in 98 % of pessimistic samples.)


## D14. Engine re-checked on the carbon airframe: 912 iSc stays

**Question.** D8 chose the 912 iSc with glass skins, where a heavy engine eats the fuel. The carbon airframe (D13) frees about 30 kg. Does that now pay for a bigger engine, in particular the six-cylinder UL Power UL520iS, with the 100 L tank to fill?

**How.** Study 23 re-closes all five engines again with carbon skins (tail, wing position, propeller, fuel) and scores them with the D8 weights.

| Carbon airframe | Score | Range, 2 × 77 kg + 10 kg | L/100 km | Climb SL / 45 °C | Take-off 45 °C | Empty |
|---|---|---|---|---|---|---|
| **Rotax 912 iSc** | **0.74** | **1,098 km** | **7.85** | 3.70 / 2.64 m/s | 539 m | 500 kg |
| Rotax 914 F | 0.61 | 897 km | 9.36 | 4.46 / 4.10 | 398 m | 503 kg |
| Rotax 912 ULS | 0.55 | 923 km | 9.13 | 3.70 / 2.64 | 539 m | 494 kg |
| Rotax 915 iS | 0.39 | 704 km | 10.24 | 5.75 / 5.34 | 331 m | 521 kg |
| UL Power UL520iS (6-cyl) | 0.29 | 349 km | 10.57 | 8.42 / 6.59 | 299 m | 546 kg |

**Why the six-cylinder still does not fit.** Carbon helps every engine equally, so the gap stays. At 750 kg the UL520iS airframe weighs 546 kg empty, leaving only 40 kg (56 L) of fuel with two 77 kg crew and bags: 349 km, under the 800 km requirement and half of Hansa-NG's 713 km. The **tank is never the limit, the weight is**: reaching 800 km would need 75 kg of fuel (104 L, more than the tank) and an MTOW of 785 kg, outside the 750 kg class this whole comparison is built on. With two 90 kg adults its range is 5 km. It also burns 35 % more fuel per kilometre. The 915 iS comes closest (704 km; 7 kg short of 800 km) but burns 30 % more.

**What a bigger engine would buy, and the cheaper way to get it.** The only real gain is hot-day take-off and climb. Study 15's 30 kW electric boost on the 912 iSc gives a 45 °C, 600 m take-off of 399 m (914 F: 398 m) and 5.2 m/s climb (914 F: 4.1 m/s) for 16 kg. On the carbon airframe that mass comes out of spare useful load, so range only drops 1,098 → 1,065 km and fuel burn is unchanged.

**Decision.** Keep the Rotax 912 iSc. Hot-and-high capability is offered as the hybrid-boost option (appendix), not by a bigger engine.

**What would change it.** A move to a heavier class (MTOW near 800 kg, CS-23 normal), or a much lighter six-cylinder.

