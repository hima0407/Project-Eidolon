Aerodynamic Analysis

Overview

This directory documents the aerodynamic development of Project Eidolon, from airfoil evaluation to preliminary three-dimensional wing analysis.

The objective is to establish a reproducible aerodynamic baseline and compare candidate airfoils under consistent operating conditions.

Current Work

NACA 63-415

The NACA 63-415 candidate has undergone preliminary 2D airfoil analysis and 3D wing analysis using XFLR5.

The exported 3D polar is retained alongside the analysis configuration and numerical results.

Current status: Preliminary analysis completed; validation and comparison remain in progress.

See results/aerodynamics/naca63415/ for the available results.

NACA 23012

NACA 23012 is the reference airfoil for the planned comparison.

The comparison will use consistent wing geometry, reference dimensions, atmospheric properties, freestream conditions, and analysis settings wherever applicable.

Next Milestones

1. Verify Reynolds-number coverage and numerical consistency.
2. Run or verify the NACA 23012 baseline analysis.
3. Compare lift, drag, pitching moment, and lift-to-drag ratio.
4. Investigate mesh and operating-condition sensitivity.
5. Use the verified aerodynamic data in the aircraft performance model.

Methodological Note

XFLR5 predictions are numerical estimates, not experimental measurements. Conclusions about aircraft performance will be made only after accounting for the assumptions and limitations of the analysis methods.
