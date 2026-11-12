# The 3-D model

The CAD is **generated from the design closure**, not drawn by hand. One geometry description feeds every output, so the model you see is always the aircraft the numbers describe.

```text
eidolon/design.py  (closed aircraft: wing position, tail sizes, gear station, CG)
        │
        ▼
eidolon/oml.py     every body as a stack of closed planar section rings
        │            real NACA 63-415 → 63-412 coordinates, twist, dihedral, taper,
        │            drooped outboard LE, flap/aileron/elevator/rudder split lines,
        │            superellipse fuselage frames, canopy, spinner, 3 blades, faired gear
        │
        ├──► cad/fusion/Eidolon/eidolon_geometry.json  → Fusion 360 script lofts B-rep solids
        ├──► cad/generated/*.stl                       → one mesh per body + the complete aircraft
        ├──► docs/viewer/model.json + specs.json      → interactive three.js viewer
        └──► results/16_geometry/*.png                 → studio renders and the dimensioned three-view
```

Regenerate everything with `python3 run_all.py 16` (about 45 s).

## Main dimensions (v1)

| | |
|---|---|
| Span | 11.50 m |
| Length (with spinner) | 7.53 m |
| Height (fin tip above ground) | 2.91 m |
| Wing area / AR | 13.25 m² / 9.98 |
| Root / tip chord | 1.440 / 0.864 m |
| Main-gear track / wheelbase | 2.10 / 1.79 m |
| Horizontal tail / vertical tail | 1.79 m² / 1.52 m² + 0.18 m² ventral strake |

## Bodies

| Group | Bodies |
|---|---|
| Wing | `wing_inboard`, `wing_outboard_cuffed` (drooped LE, 58-100 % semispan), `wing_tip`, `flap`, `aileron`, `wing_te_filler` |
| Tail | `stabiliser`, `stabiliser_tip`, `elevator` (40 % chord), `fin`, `fin_tip`, `rudder`, `dorsal_fin`, `ventral_strake` |
| Fuselage | `fuselage`, `canopy` |
| Propeller | `spinner`, `propeller_blade` (× 3, circular pattern) |
| Landing gear | `main_gear_leg` (S-glass leaf), `main_wheel_fairing`, `nose_gear_leg`, `nose_wheel_fairing` |

Control surfaces are separate bodies with their real chord ratios, so they can be deflected in Fusion with a joint.

## Internal components (X-ray)

`eidolon/internals.py` places the internal layout at the stations the design model uses, and study 16 writes it out with the skin:

| Item | Where | Shape |
|---|---|---|
| Engine, firewall, battery, panel | 0.55 · 1.05 · 1.30 · 1.55 m | boxes; firewall is the real fuselage frame at 1.05 m |
| Seats, crew (2 × 77 kg), sticks | 2.25 m, ±0.27 m | boxes, spherical heads |
| Baggage | 2.95 m | box |
| Main and rear spar | 30 % and 65 % chord, full span | chord slices of the real NACA 63-415 → 63-412 sections |
| Ribs | every 0.5 m from 0.62 m | real airfoil sections, 12 mm thick |
| Fuel tanks | between the spars, 0.65–1.55 m each side | airfoil-bounded, 2 × 50 L class |
| Carry-through box | between the spars, across the cabin | airfoil-bounded |
| Pushrod, gear sensors | stick to tail; on each main leg | rods / PVDF patches |
| CG and neutral-point markers | CG range mid-point; neutral point | spheres |

x-stations are the model's own; component sizes, tank span and the marker height are schematic.

- **Fusion 360:** running the script now builds two groups in the browser, **Airframe** and **Internals**. The Airframe is set see-through (22 %) where the Fusion API allows it; otherwise right-click **Airframe → Opacity Control**. Hide either group with its eye icon.
- **STL:** one file per item in `cad/generated/internals/`, plus `eidolon_v1_internals_all.stl`. Insert them next to `eidolon_v1_complete.stl` in any viewer or slicer; they share its coordinates.

## Building the solid model in Fusion 360

1. In Fusion 360: **Utilities → Add-Ins → Scripts and Add-Ins** (Shift+S) → **Scripts** tab → green **+** → choose the folder `cad/fusion/Eidolon`.
2. Select **Eidolon** and press **Run**. A new design opens and each body is lofted through its sections (1-3 minutes). A progress bar shows the part being built.
3. At the end a message lists the bodies built and any that failed, with the reason.
4. **File → Export → STEP** and save it as `cad/eidolon_v1.step` for the repository.

The script uses only offset construction planes, fitted splines and lofts, so every body is an editable parametric feature. Coordinates in the JSON are already Fusion's (Y up, centimetres): aircraft (x, y, z) in metres maps to Fusion (100x, 100z, −100y).

**If a body fails** (most likely a thin trailing edge or a tip ring), the rest still build. Two fixes, in order:
- In `studies/16_geometry_3d.py`, raise `_dedupe`'s `tol_cm` from 0.02 to 0.05 and re-run study 16. That thins out near-coincident points that can make a fitted spline loop.
- As a fallback, **Insert → Insert Mesh** the matching `cad/generated/eidolon_v1_<body>.stl`, then **Mesh → Convert Mesh** (prismatic) to get a solid.

The script has been checked for planar, monotonic, closed sections outside Fusion. It has not yet been run inside Fusion by the team; please report the result.

## The interactive viewer

`docs/viewer/index.html` loads `model.json` (all bodies, base64 float32 triangles with colours) and `specs.json` (dimensions and the Hansa-NG comparison).

- Locally: `python3 -m http.server -d docs/viewer`, then open http://localhost:8000. (Opening the file directly won't work, because browsers block `fetch` from `file://`.)
- On GitHub: **Settings → Pages → Deploy from branch → `main`, folder `/docs`**. The viewer is then at `https://<user>.github.io/<repo>/viewer/`.

## Renders

`eidolon/render.py` is a small numpy software renderer (no Blender needed): z-buffered rasterisation, crease-aware smooth normals, a 2048² shadow map with soft filtering, an analytic ground plane, key + fill + sky lighting and 2× supersampling. It writes `render_hero.png`, `render_rear.png`, `render_top.png` and `render_front.png`.
