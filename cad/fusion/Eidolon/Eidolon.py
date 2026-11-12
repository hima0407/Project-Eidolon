"""Fusion 360 script: build the Eidolon v1 solid model from eidolon_geometry.json.

How to run (Fusion 360):
  1. Utilities > Add-Ins > Scripts and Add-Ins (Shift+S) > Scripts tab > the green "+" > choose this folder.
  2. Select "Eidolon" and press Run. A new design opens and about 25 bodies are lofted (1-3 minutes).
  3. File > Export > STEP to get cad/eidolon_v1.step for the repository.

Bodies are grouped in two components: "Airframe" (the outer skin) and "Internals" (engine, firewall,
battery, panel, seats and crew, baggage, spars, ribs, fuel tanks, carry-through box, pushrod, gear
sensors, CG and neutral-point markers, all at the design model's stations). With XRAY = True the
Airframe is made see-through; hide or show either group from the browser.

Every body is a loft through closed sections. Each section is a fitted spline sketched on an offset
construction plane, through the real airfoil coordinates (NACA 63-415 -> 63-412 wing, NACA 0012/0009
tails), with twist, dihedral, taper and positions taken from the design closure. The JSON is regenerated
by `python3 studies/16_geometry_3d.py`, so the CAD always matches the analysis.
Coordinates are already Fusion's (Y up, centimetres). The model is built in a new document.
"""
import json
import os
import traceback

import adsk.core
import adsk.fusion

COLORS = {}
XRAY = True          # make the Airframe group see-through so the Internals show
XRAY_OPACITY = 0.22


def _plane(comp, axis, offset_cm):
    """Offset construction plane normal to axis, verified against its real position."""
    base = {"x": comp.yZConstructionPlane, "y": comp.xZConstructionPlane, "z": comp.xYConstructionPlane}[axis]
    idx = {"x": 0, "y": 1, "z": 2}[axis]
    planes = comp.constructionPlanes
    for sign in (1, -1):
        inp = planes.createInput()
        inp.setByOffset(base, adsk.core.ValueInput.createByReal(sign * offset_cm))
        cp = planes.add(inp)
        o = cp.geometry.origin
        pos = (o.x, o.y, o.z)[idx]
        if abs(pos - offset_cm) < 1e-4 or abs(offset_cm) < 1e-9:
            cp.isLightBulbOn = False
            return cp
        cp.deleteMe()
    raise RuntimeError("could not place construction plane")


def _section(comp, axis, ring, closed_loop, polyline=False):
    """Sketch one closed section and return its (largest) profile."""
    off = sum(p[{"x": 0, "y": 1, "z": 2}[axis]] for p in ring) / len(ring)
    cp = _plane(comp, axis, off)
    sk = comp.sketches.add(cp)
    sk.isVisible = False
    pts = adsk.core.ObjectCollection.create()
    sk_pts = [sk.modelToSketchSpace(adsk.core.Point3D.create(*p)) for p in ring]
    for p in sk_pts:
        pts.add(p)
    if polyline:                                     # straight-edged section (boxes, rods)
        lines = sk.sketchCurves.sketchLines
        first = prev = lines.addByTwoPoints(sk_pts[0], sk_pts[1])
        for q in sk_pts[2:]:
            prev = lines.addByTwoPoints(prev.endSketchPoint, q)
        lines.addByTwoPoints(prev.endSketchPoint, first.startSketchPoint)
    elif closed_loop:
        pts.add(sk_pts[0])
        spl = sk.sketchCurves.sketchFittedSplines.add(pts)
        try:
            spl.isClosed = True
        except Exception:
            pass
    else:
        spl = sk.sketchCurves.sketchFittedSplines.add(pts)
        sk.sketchCurves.sketchLines.addByTwoPoints(spl.endSketchPoint, spl.startSketchPoint)
    best, area = None, -1.0
    for i in range(sk.profiles.count):
        pr = sk.profiles.item(i)
        a = pr.areaProperties().area
        if a > area:
            best, area = pr, a
    if best is None:
        raise RuntimeError("section did not close into a profile")
    return best


def _appearance(app, design, name, rgb, glossy=True):
    key = (name, tuple(rgb))
    if key in COLORS:
        return COLORS[key]
    base = None
    for libname in ("Fusion Appearance Library", "Fusion 360 Appearance Library"):
        try:
            lib = app.materialLibraries.itemByName(libname)
            if lib is None:
                continue
            for cand in (["Paint - Enamel Glossy (White)", "Plastic - Glossy (White)"] if glossy
                         else ["Glass - Smoked", "Glass (Smoked)", "Plastic - Translucent Glossy (Gray)"]):
                base = lib.appearances.itemByName(cand)
                if base:
                    break
        except Exception:
            base = None
        if base:
            break
    if base is None:
        COLORS[key] = None
        return None
    ap = design.appearances.itemByName(name) or design.appearances.addByCopy(base, name)
    try:
        for i in range(ap.appearanceProperties.count):
            prop = ap.appearanceProperties.item(i)
            if isinstance(prop, adsk.core.ColorProperty) and prop.name.lower() in ("color", "colour", "glazing", "base color"):
                prop.value = adsk.core.Color.create(int(rgb[0]), int(rgb[1]), int(rgb[2]), 255)
                break
    except Exception:
        pass
    COLORS[key] = ap
    return ap


GROUPS = {}


def _group(root, name):
    if name not in GROUPS:
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        occ.component.name = name
        GROUPS[name] = occ
    return GROUPS[name]


def build_part(app, design, root, part):
    parent = _group(root, part.get("group", "Airframe")).component
    occ = parent.occurrences.addNewComponent(adsk.core.Matrix3D.create())
    comp = occ.component
    comp.name = part["name"]
    profiles = [_section(comp, part["plane"], ring, part["closed_loop"], part.get("polyline", False)) for ring in part["rings"]]
    lofts = comp.features.loftFeatures
    li = lofts.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    for pr in profiles:
        li.loftSections.add(pr)
    li.isSolid = True
    feat = lofts.add(li)
    bodies = [feat.bodies.item(i) for i in range(feat.bodies.count)]
    if part.get("mirror"):
        coll = adsk.core.ObjectCollection.create()
        for b in bodies:
            coll.add(b)
        mi = comp.features.mirrorFeatures.createInput(coll, comp.xYConstructionPlane)   # aircraft y=0 is Fusion z=0
        mf = comp.features.mirrorFeatures.add(mi)
        bodies += [mf.bodies.item(i) for i in range(mf.bodies.count)]
    if part.get("pattern"):
        coll = adsk.core.ObjectCollection.create()
        for b in bodies:
            coll.add(b)
        pi = comp.features.circularPatternFeatures.createInput(coll, comp.xConstructionAxis)
        pi.quantity = adsk.core.ValueInput.createByReal(part["pattern"])
        pi.totalAngle = adsk.core.ValueInput.createByString("360 deg")
        pi.isSymmetric = False
        comp.features.circularPatternFeatures.add(pi)
    ap = _appearance(app, design, "Eidolon " + part["color"], part["rgb"], glossy=part["name"] != "canopy")
    if ap:
        for i in range(comp.bRepBodies.count):
            comp.bRepBodies.item(i).appearance = ap
    for i in range(comp.bRepBodies.count):
        comp.bRepBodies.item(i).name = part["name"]


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        here = os.path.dirname(os.path.realpath(__file__))
        with open(os.path.join(here, "eidolon_geometry.json")) as f:
            data = json.load(f)
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        #root.name = "Eidolon v1"
        ok, failed = [], []
        prog = ui.createProgressDialog()
        prog.show("Eidolon v1", "Lofting %v of %m: %p %", 0, len(data["parts"]), 1)
        for k, part in enumerate(data["parts"]):
            prog.progressValue = k
            prog.message = "Lofting " + part["name"] + "  (%v of %m)"
            try:
                build_part(app, design, root, part)
                ok.append(part["name"])
            except Exception:
                failed.append(part["name"] + ": " + traceback.format_exc().strip().splitlines()[-1])
            adsk.doEvents()
        prog.hide()
        xray_note = ""
        if XRAY and "Airframe" in GROUPS:
            done = False
            try:
                occ = GROUPS["Airframe"]
                if hasattr(occ, "opacity"):
                    occ.opacity = XRAY_OPACITY
                    done = True
                else:
                    for o in occ.component.allOccurrences:
                        for i in range(o.component.bRepBodies.count):
                            b = o.component.bRepBodies.item(i)
                            if hasattr(b, "opacity"):
                                b.opacity = XRAY_OPACITY
                                done = True
            except Exception:
                done = False
            if not done:
                xray_note = "\n\nFor the X-ray view: right-click Airframe in the browser > Opacity Control > 20 %."
        app.activeViewport.fit()
        msg = "Eidolon v1: %d bodies built from the design closure.\n" % len(ok)
        msg += data.get("summary", "") + xray_note
        if failed:
            msg += "\n\nCould not build:\n" + "\n".join(failed)
        ui.messageBox(msg)
    except Exception:
        if ui:
            ui.messageBox("Failed:\n{}".format(traceback.format_exc()))
