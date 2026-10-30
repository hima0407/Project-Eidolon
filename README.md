# Project Eidolon

**Computational preliminary design of a two-seat light aircraft**

Project Eidolon brings together conceptual aircraft sizing, airfoil and finite-wing aerodynamics, propulsion matching, mass/centre-of-gravity analysis, and CAD integration. The goal is a traceable engineering design process: every requirement, assumption, model output, and design decision should be distinguishable and reproducible.

> **Project status:** preliminary design. Mission targets are not yet demonstrated aircraft capabilities. Current aerodynamic results are simulation outputs, and the propulsion, mass-budget, CG, and range models still require verification.

## Mission baseline and evolved ambitions

The original mission brief specifies the baseline below. Later in the design conversation, a more aggressive concept was proposed. Because the mass, wing-loading, fuel, and range figures have not yet been reconciled into one configuration, the sizing script currently uses the original baseline while the newer goals remain stretch ambitions.

| Parameter | Original baseline | Later ambition in design history |
|---|---:|---:|
| MTOW | 750 kg | 705.7 kg proposed |
| Empty mass | ≤550 kg | 500 kg stretch target |
| Range | 800 km | 1,000 km stretch target |
| Cruise speed | 200 km/h | 200 km/h working cruise condition |
| Maximum speed | 225 km/h | To be re-verified against the chosen configuration |
| Sea-level rate of climb | 3.0 m/s | 3.0 m/s working requirement |
| Service ceiling | 3,000 m | 3,000 m working requirement |
| Fuel tank proposal | Not fixed in original baseline | 25 L proposed later; feasibility not yet established |

The later discussion also proposes preliminary +4.4 g structural sizing and a 20–30% MAC CG target. These remain unverified design inputs. See [`docs/requirements.md`](docs/requirements.md) for the full register and the configuration decision that must be resolved before the newer ambitions can govern the calculations.

## Current design baseline

The project is carrying a **candidate** wing loading of 520 N/m². At the 750 kg MTOW target, this implies a wing area of approximately 14.14 m². This is a starting point from the design plan, not a demonstrated global optimum.

The current conceptual constraint model uses provisional values of `CD0 = 0.024`, `AR = 8.55`, `e = 0.80`, and `CLmax = 1.8` for the assumed landing configuration. These are model inputs, not measured aircraft properties. The project should test sensitivity to uncertain inputs instead of quietly treating them as facts. Propeller efficiency remains unknown until a defensible model or source establishes it.

## Workstreams

### Redesign decision framework

The current redesign direction prioritizes a two-person range/efficiency mission and uses India as the regulatory context to investigate. The mission numbers and applicable DGCA design/certification basis still need to be formally confirmed. Do not infer an Indian “LSA” category from a 600 kg mass assumption.

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
