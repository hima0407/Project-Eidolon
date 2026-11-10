# Appendix concept: hybrid take-off boost for hot Indian airfields

**Scope:** a concept for the last 2-3 minutes of the presentation. The baseline Eidolon is an IC-engine aircraft, as the course requires. This is an optional add-on studied with the same models (study 15).

## The problem

On a 45 °C day at a 600 m airfield (typical of the Deccan plateau in May), the density ratio falls to about 0.82. A naturally aspirated Rotax 912 iSc loses about 18 % of its power. For Eidolon v1 (study 15):

| | ISA sea level | 45 °C at 600 m |
|---|---:|---:|
| Take-off to 15 m | 357 m | 539 m |
| Max rate of climb | 3.70 m/s | 2.64 m/s |

## The idea

A parallel hybrid: an axial-flux electric motor on the propeller shaft adds P_e for the ground roll and the climb to 300 m, then switches off. The battery only needs to supply energy for about 2-3 minutes:

- E = P_e · t_boost / η (η = 0.90 from battery to shaft)
- mass = P_e/5 (motor) + P_e/12 (inverter) + E/(0.8 × 0.160) (battery) + 2 kg (integration)

These use assumed specific powers: motor 5 kW/kg, inverter 12 kW/kg, pack 160 Wh/kg at 80 % depth of discharge.

## Results (study 15, `results/15_hybrid/hybrid_boost.png`)

| Boost | Added mass | Battery | T/O (45 °C) | ROC (45 °C) | Range with 2 crew |
|---:|---:|---:|---:|---:|---:|
| 0 kW | 0 kg | 0 kWh | 539 m | 2.64 m/s | 803 km |
| 15 kW | 9.7 kg | 0.44 kWh | 432 m | 3.89 m/s | 627 km |
| 30 kW | 16.0 kg | 0.70 kWh | 399 m | 5.16 m/s | 514 km |

## Conclusion

- About **15 kW restores sea-level climb** on the hottest day (3.89 vs 3.70 m/s), for about 10 kg.
- Take-off improves, but it flattens out near 400 m. The 1.75 m propeller cannot absorb much more power at low speed. A larger-chord propeller would be needed.
- The mass is paid for in fuel (MTOW is fixed), so the range with 2 crew drops by about 22 % at 15 kW (18 km per kg, as everywhere on this aircraft). **Recommendation:** an operator-fitted kit for hot-and-high bases, not part of the baseline. A safe engine-only take-off with the battery flat must remain possible, and it is: 539 m on that day.
