# Project Eidolon

**Computational preliminary design of a two-seat light aircraft**

Project Eidolon brings together conceptual aircraft sizing, airfoil and finite-wing aerodynamics, propulsion matching, mass/centre-of-gravity analysis, and CAD integration. The goal is a traceable engineering design process: every requirement, assumption, model output, and design decision should be distinguishable and reproducible.

> **Project status:** preliminary design. Mission targets are not yet demonstrated aircraft capabilities. Current aerodynamic results are simulation outputs, and the propulsion, mass-budget, CG, and range models still require verification.

## Mission baseline and evolved ambitions

The table preserves historical values for traceability. The current owner-selected direction is a minimum-feasible-mass, two-person design for 1,000 km range and 230 km/h cruise. The existing sizing script still uses the original baseline; it is not the current mission solution. See [`docs/mission_definition.md`](docs/mission_definition.md) for the governing working case and unresolved inputs.

| Parameter | Original baseline | Historical proposal / current target |
|---|---:|---:|
| MTOW | 750 kg | Optimize; no cap selected (705.7 kg is historical) |
| Empty mass | ≤550 kg | 500 kg stretch target |
| Range | 800 km | 1,000 km current target |
| Cruise speed | 200 km/h | 230 km/h current owner-selected target |
| Maximum speed | 225 km/h | Open; must exceed 230 km/h if 230 km/h is cruise |
| Sea-level rate of climb | 3.0 m/s | 3.0 m/s working requirement |
| Service ceiling | 3,000 m | 3,000 m working requirement |
| Fuel tank proposal | Not fixed in original baseline | 25 L proposed later; feasibility not yet established |

The historical discussion also proposes preliminary +4.4 g structural sizing and a 20–30% MAC CG target. These remain unverified. See [`docs/requirements.md`](docs/requirements.md) for the full register.

## Historical constraint-model case

The existing constraint script still represents the historical 750 kg / 200 km/h case. It carries a **candidate** wing loading of 520 N/m², which implies a wing area of approximately 14.14 m² at 750 kg. This is not the current mission solution or a demonstrated optimum; the new 1,000 km / 230 km/h mission requires a mass-closure redesign.

The current conceptual constraint model uses provisional values of `CD0 = 0.024`, `AR = 8.55`, `e = 0.80`, and `CLmax = 1.8` for the assumed landing configuration. These are model inputs, not measured aircraft properties. The project should test sensitivity to uncertain inputs instead of quietly treating them as facts. Propeller efficiency remains unknown until a defensible model or source establishes it.

## Workstreams

### Redesign decision framework

The current redesign objective is the lowest feasible take-off mass for two people, 1,000 km design range, and 230 km/h cruise, using India/DGCA as the regulatory context to investigate. Occupant/baggage masses, reserve policy, cruise altitude, and applicable design/certification basis remain to be confirmed. Do not infer an Indian “LSA” category from a 600 kg mass assumption. See [`docs/mission_definition.md`](docs/mission_definition.md).

See [`docs/redesign_and_architecture_trade.md`](docs/redesign_and_architecture_trade.md) for the DarkAero benchmark, engine mass/power comparison, tractor-versus-pusher trade, current recommendation, and decision gates. It is a preliminary trade study; no engine, propeller position, or aircraft configuration is selected by it.

### 1. Constraint analysis

[`scripts/constraint_analysis.py`](scripts/constraint_analysis.py) generates a wing-loading versus thrust-to-weight matching graph for cruise, maximum speed, sea-level climb, and service ceiling, alongside the stall boundary. It writes the graph and candidate-point data under `results/constraints/`.

This model is a conceptual sizing aid. Its output depends on the assumptions documented in [`docs/requirements.md`](docs/requirements.md); it is not a certified performance prediction.

### 2. Aerodynamics: NACA 63-415

The current airfoil direction is the NACA 63-415 natural-laminar-flow section, replacing the earlier NACA 23012 baseline in the current wing study. The repository contains preliminary XFLR5 2D/3D outputs and project files. These results should be compared at matched Reynolds numbers and settings before claiming an improvement over the earlier airfoil.

- [Aerodynamic methodology](docs/aerodynamics.md)
- [NACA 63-415 result package](results/aerodynamics/naca63415/readme.md)
- [XFLR5 project](xflr5/projects/main.xfl)

A wing polar does not equal the complete aircraft drag polar. It does not independently establish aircraft cruise efficiency, maximum speed, climb, or range.

### 3. Propulsion matching

The ambition is to model propeller performance across the relevant speed and operating range, then compare available thrust with aircraft drag and establish required shaft power. The existing BEMT work is exploratory until its assumptions, convergence, coefficients, and results are checked. No propeller efficiency should be described as verified without supporting evidence.

### 4. Mass, CG, and range

The 550 kg empty-mass target and 800 km range belong to the original baseline. Later design discussion proposes a 500 kg empty-mass target, 1,000 km range, 705.7 kg MTOW, 25 L fuel tanks, +4.4 g structural sizing, and a 20–30% MAC CG target. These newer ambitions are captured in the requirements register but are not yet reconciled into a single mass/geometry/mission model. Occupant/fuel allocation, structural mass, CG travel, and range must be demonstrated before any of them can be presented as achieved.

### 5. CAD and integration

The longer-term objective is to integrate the selected wing and propulsion architecture into a consistent 3D configuration, then check component packaging, mass distribution, CG travel, and structural assumptions.

## Repository map

```text
.
├── README.md
├── docs/
│   ├── requirements.md
│   └── aerodynamics.md
├── scripts/
│   ├── constraint_analysis.py
│   ├── propulsion_bemt.py
│   └── fetch_airfoils.py
├── results/
│   ├── constraints/
│   └── aerodynamics/naca63415/
└── xflr5/
    ├── naca63415.dat
    └── projects/main.xfl
```

The tree above describes the intended organization; not every path is guaranteed to exist in every checkout yet.

## Reproducibility

Python dependencies for the constraint script are NumPy and Matplotlib.

From the repository root:

```bash
python3 scripts/constraint_analysis.py
```

This regenerates the historical 750 kg constraint case. It does not yet size the current 1,000 km / 230 km/h mission or optimize MTOW; that requires the mass-closure work described in [`docs/mission_definition.md`](docs/mission_definition.md).

This generates:

- `results/constraints/constraint_analysis.png`
- `results/constraints/constraint_values.csv`

An optional propeller-efficiency scenario can be run explicitly, for example:

```bash
python3 scripts/constraint_analysis.py --prop-eff 0.75
```

The supplied efficiency is a scenario input only; it is not validated and should not be used to select an engine without further analysis.

## Engineering principles

- Requirements are not results.
- Assumptions are not measurements.
- A converged simulation is not automatically a validated model.
- Comparisons must use compatible conditions and documented settings.
- Changes to baseline assumptions must be recorded and propagated to dependent calculations and figures.

See [`docs/requirements.md`](docs/requirements.md) for the current source-of-truth requirements and assumption register.
