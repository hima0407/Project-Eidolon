#!/usr/bin/env python3
"""Readiness checklist for Project Eidolon's propeller BEMT work.

The historical implementation used placeholder blade geometry and a generic
section-polar approximation. It produced numerical outputs, but those outputs
were not sufficiently grounded to support a propeller-efficiency claim, a blade
count winner, or engine selection. This replacement intentionally does not
produce performance numbers until validated inputs and a reviewed solver are
available. That is more useful than manufacturing precision from assumptions.
"""
from __future__ import annotations

REQUIRED_INPUTS = {
    "propeller geometry": "manufacturer or measured chord and twist distribution versus radius",
    "blade section data": "section Cl/Cd polars at relevant Reynolds numbers and Mach numbers",
    "operating point": "cruise speed, altitude/atmosphere, propeller RPM and advance ratio",
    "power boundary": "engine power available at the selected RPM and altitude, plus gearbox losses",
    "model formulation": "documented BEMT equations, loss factors, sign conventions, and convergence criteria",
    "validation": "comparison against credible manufacturer maps, published data, or test data",
}


def main() -> None:
    print("PROJECT EIDOLON | PROPULSION MODEL READINESS")
    print("Status: exploratory BEMT implementation is not ready to generate design claims.")
    print("Working cruise target: 200 km/h (55.56 m/s). This is a mission target, not a verified propeller operating point.")
    print("Required before a quantitative run:")
    for name, description in REQUIRED_INPUTS.items():
        print(f"  [ ] {name}: {description}")
    print("\nNo efficiency, thrust, blade-count winner, or engine rating is reported.")
    print("Do not reintroduce the old placeholder outputs as validated results.")

if __name__ == "__main__":
    main()
