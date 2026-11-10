"""Project Eidolon conceptual design toolkit.

Everything is SI unless a function name says otherwise (Raymer's statistical
weight equations are evaluated in imperial units internally and converted back).

Module map
----------
atmosphere     ISA with hot-day temperature offset
airfoil        coordinate loading, section area (fuel volume), XFLR5 polar parsing
geometry       wing / tail / fuselage planform maths
aircraft       the two aircraft definitions: Eidolon and the Hansa-NG benchmark
engines        engine database with sources
lifting_line   Prandtl lifting-line (Glauert series) for span loading and stall onset
aero           component drag build-up, lift curve, CLmax with flaps, drag polar
propeller      blade-element momentum theory with Prandtl tip/root loss
weights        Raymer general-aviation statistical weight equations
stability      neutral point, static margin, CG envelope
performance    power curves, climb, ceiling, range, endurance, take-off and landing
loads          V-n diagram (CS-23 manoeuvre + gust)
landing_gear   composite leaf-spring sizing and piezo self-sensing estimate
hybrid         parallel-hybrid take-off boost concept (appendix study)
"""

__version__ = "1.0.0"
