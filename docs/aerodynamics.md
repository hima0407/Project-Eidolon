# Aerodynamic Analysis: NACA 63-415

**Status:** preliminary numerical analysis; not experimental validation.

## Objective

The current wing study uses the NACA 63-415 section as the working candidate, following earlier consideration of the NACA 23012. The aim is to establish the section and finite-wing behavior under relevant Reynolds-number and operating conditions, then feed defensible aerodynamic inputs into the aircraft-level performance model.

## Available analysis artifacts

The current result package is intended to contain:

- `results/aerodynamics/naca63415/polar2d.txt` — 2D airfoil polar output.
- `results/aerodynamics/naca63415/polar3d.csv` — exported 3D wing polar.
- `results/aerodynamics/naca63415/analysis_log.txt` — analysis settings and run notes.
- `results/aerodynamics/naca63415/polar_graphs.png` — plotted results.
- `xflr5/naca63415.dat` — airfoil coordinates.
- `xflr5/projects/main.xfl` — XFLR5 project.

Check that these files exist in the working checkout before treating the list as a complete inventory.

## Current 3D polar sample

The supplied XFLR5 VLM2 CSV reports a freestream speed of 55.6 m/s, approximately 200 km/h. In that dataset, at the sampled angle of attack of 1 degree:

- `CL` ≈ 0.3311
- `CD` ≈ 0.00888
- sampled `CL/CD` ≈ 37.3

This is a point from the supplied simulation output, not a validated aircraft cruise L/D. The precise solver setup, Reynolds-number coverage, transition treatment, wing geometry, and polar conventions must be checked against the project file and log before using the numbers in a design calculation.

## Important limits

1. A 2D airfoil polar is not a finite-wing polar.
2. A finite-wing XFLR5 polar is not automatically the complete aircraft drag polar. Fuselage, canopy, landing gear, cooling, interference, control gaps, and other components may add drag.
3. A converged VLM2 run is a model result, not experimental validation.
4. Do not claim a fixed percentage improvement for NACA 63-415 over NACA 23012 until both airfoils are analyzed at matched Reynolds numbers, transition settings, solver settings, and comparable lift conditions.
5. Do not use the wing polar's drag coefficient directly as the aircraft-level `CD0` in constraint analysis.
6. The project discussion mentions Reynolds-number sweeps from roughly 1 million to 6 million. The actual coverage and validity must be confirmed from the saved polars, not inferred from the intended plan.

## Next aerodynamic tasks

1. Verify the airfoil coordinate file and section assignment at every relevant wing station.
2. Run matched 2D polar sweeps for NACA 63-415 and the legacy NACA 23012 over the relevant Reynolds-number range and angle-of-attack range.
3. Confirm XFLR5 settings and record the geometry, atmosphere, viscosity, transition assumptions, and solver choice.
4. Check the finite-wing polar for convergence, plausible trends, and sufficient angle-of-attack coverage; investigate any warning or out-of-envelope Reynolds-number conditions.
5. Export clean CSV data and plot `CL` vs `alpha`, `CD` vs `CL`, `CL/CD` vs `alpha`, and pitching moment vs `alpha` where available.
6. Establish a defensible bridge from the wing model to aircraft-level drag before updating the aircraft constraint assumptions.
