# Project Eidolon landing gear concept study

This package is a research-stage feasibility screen for the proposed Piezoelectric Active-Tension Carbon Ribbon idea.

**Do not treat the concept as selected or validated.** The package deliberately keeps a conventional composite leaf spring as the reference architecture and treats piezoelectric assistance as an experimental branch.

Contents:
- `docs/piezoelectric_ribbon_landing_gear_concept.md`: assumptions, limits, comparison and evidence needed.
- `scripts/landing_energy_screening.py`: reproducible parameter sweep.
- `results/landing_gear/landing_energy_screening.csv`: all swept cases.
- `results/landing_gear/landing_energy_screening.png`: illustrative plot.

Run from repository root:
`python3 scripts/landing_energy_screening.py`

Dependencies: Python 3, pandas, matplotlib.

The script uses illustrative screening assumptions only. It does not size a landing gear, establish attachment loads, choose a composite layup, or demonstrate that a piezoelectric system can absorb/dissipate landing energy.
