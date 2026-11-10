# NACA 63-415: Preliminary Aerodynamic Results

This folder stores the preliminary XFLR5 analysis artifacts for the Project Eidolon wing using the NACA 63-415 section. These are numerical model outputs, not experimental validation or proof of complete-aircraft performance.

## Expected files

- `polar2d.txt` — 2D section polar output.
- `polar3d.csv` — exported 3D finite-wing polar.
- `analysis_log.txt` — run settings and notes.
- `polar_graphs.png` — result plots.

The airfoil coordinates are stored at [`../../../xflr5/naca63415.dat`](../../../xflr5/naca63415.dat), and the XFLR5 project is at [`../../../xflr5/projects/main.xfl`](../../../xflr5/projects/main.xfl), relative to the repository root structure.

## Reported sample from the supplied 3D polar

At `alpha = 1°`, the supplied CSV reports approximately `CL = 0.3311` and `CD = 0.00888`, giving a sampled `CL/CD ≈ 37.3`. Treat this as a sample from the current model only. Confirm the run settings and polar metadata before using it in downstream calculations.

## Interpretation limits

- The result applies to the modeled wing and its configured conditions, not automatically to the complete aircraft.
- Do not call this an experimentally verified maximum L/D.
- Do not treat this drag coefficient as aircraft-level `CD0`.
- Do not claim a percentage improvement over NACA 23012 without a matched comparison at comparable Reynolds numbers and settings.
- Record solver warnings and investigate Reynolds-number coverage rather than omitting warnings from the final report.
