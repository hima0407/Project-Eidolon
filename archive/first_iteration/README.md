# First-iteration scripts (kept for history)

These are the team's first-pass tools, from October 2026. Each one is superseded by a module in `eidolon/` and a study in `studies/`:

| Script | Superseded by | What changed |
|---|---|---|
| `constraint_analysis.py` | `studies/05_wing_sizing.py` | Every carpet point is now a fully closed aircraft with a calibrated drag polar, not assumed CD0/e/η |
| `propulsion_bemt.py` | `eidolon/propeller.py`, `studies/07_propeller.py` | Stall + drag rise in the blade model, ideal-pitch twist, momentum-theory bound, run at the real cruise condition (200 km/h, 1500 m) instead of 230 km/h / 3000 m |
| `landing_energy_screening.py` | `eidolon/landing_gear.py`, `studies/13_landing_gear.py` | CS-23.473 sink rate and wing-lift energy, real leaf sizing for 5 materials, piezo checked for damping (0.04 % of the landing energy) and kept as a sensor |
| `fetch_airfoils.py` | still usable to download coordinates into `xflr5/airfoils/` | — |

Their original outputs are in `results/` next to this file (constraint diagram and landing-energy screen).
