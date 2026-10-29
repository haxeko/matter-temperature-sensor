#!/usr/bin/env python3
"""
Generate the KiCad 9 project for TH-SENSOR-H2 Rev A from design.py:

  hardware/kicad/th_sensor_h2.kicad_sch     schematic (one A3 sheet)
  hardware/kicad/lib/th_sensor.kicad_sym    project symbols (ESP32-H2-MINI-1, AO3401A, 2N7002)
  hardware/kicad/lib/th_sensor.pretty/      project footprints (module, Murata DFE201612E)
  hardware/kicad/lib/3dmodels/              module STEP (Espressif library, CC-BY-SA 4.0 + design exception)
  hardware/kicad/sym-lib-table, fp-lib-table

After writing, it asks kicad-cli for the netlist and compares every pin's net
with design.py (exit code 1 on any difference).

Usage: python3 gen_schematic.py [--no-check]
"""
import os
import re
import shutil
import subprocess
import sys

import design as D
from kicad_sexpr import SymbolSource, fmt, new_uuid, outward_dir, transform

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "kicad"))
LIB = os.path.join(OUT, "lib")
SCH = os.path.join(OUT, D.PROJECT + ".kicad_sch")
GRID = 1.27

# ---------------------------------------------------------------- libraries
SYM = {}


def load_symbols():
    for lib_id, (path, name) in D.SYMBOLS.items():
        nick, new_name = lib_id.split(":")
        overrides = None
        if lib_id == "th_sensor:ESP32-H2-MINI-1":
            overrides = {"Footprint": "th_sensor:ESP32-H2-MINI-1",
                         "Description": "ESP32-H2-MINI-1 module (Espressif KiCad library, CC-BY-SA 4.0 with "
                                        "design exception), 4 MB flash variant -H4S"}
        SYM[lib_id] = SymbolSource(path, name, nick, new_name=new_name, overrides=overrides)


def write_project_libs():
    os.makedirs(os.path.join(LIB, "th_sensor.pretty"), exist_ok=True)
    os.makedirs(os.path.join(LIB, "3dmodels"), exist_ok=True)
    entries = [SYM[k].library_entry() for k in sorted(SYM) if k.startswith("th_sensor:")]
    with open(os.path.join(LIB, "th_sensor.kicad_sym"), "w") as f:
        f.write('(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "th_sensor_gen")\n\t(generator_version "9.0")\n')
        for e in entries:
            f.write("\t" + e + "\n")
        f.write(")\n")
    # module footprint + 3D model from the Espressif library
    src_fp = os.path.join(D.ESPRESSIF_LIB, "footprints", "Espressif.pretty", "ESP32-H2-MINI-1.kicad_mod")
    fp = open(src_fp).read()
    fp = re.sub(r'\(model "[^"]*"', '(model "${KIPRJMOD}/lib/3dmodels/ESP32-H2-MINI-1.STEP"', fp)
    open(os.path.join(LIB, "th_sensor.pretty", "ESP32-H2-MINI-1.kicad_mod"), "w").write(fp)
    shutil.copyfile(os.path.join(D.ESPRESSIF_LIB, "3dmodels", "espressif.3dshapes", "ESP32-H2-MINI-1.STEP"),
                    os.path.join(LIB, "3dmodels", "ESP32-H2-MINI-1.STEP"))
    shutil.copyfile(os.path.join(D.ESPRESSIF_LIB, "LICENSE.md"), os.path.join(LIB, "LICENSE-espressif-kicad-libraries.md"))
    open(os.path.join(LIB, "th_sensor.pretty", "L_Murata_DFE201612E.kicad_mod"), "w").write(murata_dfe201612e())
    with open(os.path.join(OUT, "sym-lib-table"), "w") as f:
        f.write('(sym_lib_table\n\t(version 7)\n\t(lib (name "th_sensor")(type "KiCad")(uri "${KIPRJMOD}/lib/th_sensor.kicad_sym")'
                '(options "")(descr "TH-SENSOR-H2 project symbols"))\n)\n')
    with open(os.path.join(OUT, "fp-lib-table"), "w") as f:
        f.write('(fp_lib_table\n\t(version 7)\n\t(lib (name "th_sensor")(type "KiCad")(uri "${KIPRJMOD}/lib/th_sensor.pretty")'
                '(options "")(descr "TH-SENSOR-H2 project footprints"))\n)\n')


def murata_dfe201612e():
    """Land pattern from Murata DFE201612E spec J(E)TE243A-0006-01 p.5 'Recommended PCB pattern':
    two 0.8 x 1.8 mm pads, 0.8 mm gap (2.4 mm overall). 'Do not make through holes or copper
    pattern under the coil except the electrodes' -> F.Cu keep-out between the pads."""
    u = lambda s: new_uuid("fp-dfe-" + s)
    return f'''(footprint "L_Murata_DFE201612E"
	(version 20241229)
	(generator "th_sensor_gen")
	(layer "F.Cu")
	(descr "Inductor, Murata DFE201612E, 2.0x1.6x1.2 mm, land pattern per Murata spec J(E)TE243A-0006-01 (pads 0.8x1.8 mm, gap 0.8 mm)")
	(tags "inductor murata dfe201612e power")
	(property "Reference" "REF**" (at 0 -1.9 0) (layer "F.SilkS") (uuid "{u('ref')}") (effects (font (size 0.8 0.8) (thickness 0.12))))
	(property "Value" "L_Murata_DFE201612E" (at 0 1.9 0) (layer "F.Fab") (uuid "{u('val')}") (effects (font (size 0.8 0.8) (thickness 0.12))))
	(attr smd)
	(fp_line (start -0.3 -1.06) (end 0.3 -1.06) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s1')}"))
	(fp_line (start -0.3 1.06) (end 0.3 1.06) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s2')}"))
	(fp_rect (start -1.0 -0.8) (end 1.0 0.8) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "{u('fab')}"))
	(fp_rect (start -1.45 -1.15) (end 1.45 1.15) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{u('crt')}"))
	(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab") (uuid "{u('fabref')}") (effects (font (size 0.5 0.5) (thickness 0.08))))
	(pad "1" smd roundrect (at -0.8 0) (size 0.8 1.8) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.15) (uuid "{u('p1')}"))
	(pad "2" smd roundrect (at 0.8 0) (size 0.8 1.8) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.15) (uuid "{u('p2')}"))
	(zone (net 0) (net_name "") (layers "F.Cu") (uuid "{u('keepout')}") (name "DFE_no_copper_between_pads") (hatch edge 0.3)
		(connect_pads (clearance 0))
		(min_thickness 0.25) (filled_areas_thickness no)
		(keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed))
		(placement (enabled no) (sheetname ""))
		(fill (thermal_gap 0.5) (thermal_bridge_width 0.5))
		(polygon (pts (xy -0.35 -0.9) (xy 0.35 -0.9) (xy 0.35 0.9) (xy -0.35 0.9))))
	(embedded_fonts no)
)
'''


# ---------------------------------------------------------------- schematic model
class Sheet:
    def __init__(self):
        self.items = []
        self.sym_instances = []
        self.placed = {}
        self.wire_pts = []      # for junction detection
        self.n = 0

    def uid(self, tag):
        self.n += 1
        return new_uuid("sch-%s-%d" % (tag, self.n))

    # -- primitives
    def wire(self, *pts):
        for a, b in zip(pts, pts[1:]):
            if a == b:
                continue
            self.items.append('(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) (type default)) (uuid "%s"))'
                              % (fmt(a[0]), fmt(a[1]), fmt(b[0]), fmt(b[1]), self.uid("w")))
            self.wire_pts.append((a, b))

    def junction(self, p):
        self.items.append('(junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid "%s"))'
                          % (fmt(p[0]), fmt(p[1]), self.uid("j")))

    def label(self, net, p, angle=0):
        just = "left bottom" if angle in (0, 90) else "right bottom"
        self.items.append('(label "%s" (at %s %s %d) (fields_autoplaced yes) (effects (font (size 1.27 1.27)) '
                          '(justify %s)) (uuid "%s"))' % (net, fmt(p[0]), fmt(p[1]), angle, just, self.uid("l")))

    def noconnect(self, p):
        self.items.append('(no_connect (at %s %s) (uuid "%s"))' % (fmt(p[0]), fmt(p[1]), self.uid("nc")))

    def text(self, s, p, size=1.27, bold=False):
        s = s.replace('"', "'").replace("\n", "\\n")
        self.items.append('(text "%s" (exclude_from_sim no) (at %s %s 0) (effects (font (size %s %s)%s) '
                          '(justify left top)) (uuid "%s"))'
                          % (s, fmt(p[0]), fmt(p[1]), size, size, " (bold yes)" if bold else "", self.uid("t")))

    def frame(self, x1, y1, x2, y2, title):
        self.items.append('(rectangle (start %s %s) (end %s %s) (stroke (width 0.254) (type dash)) (fill (type none)) '
                          '(uuid "%s"))' % (fmt(x1), fmt(y1), fmt(x2), fmt(y2), self.uid("r")))
        self.text(title, (x1 + 1.27, y1 + 1.27), size=1.8, bold=True)

    # -- symbols
    def place(self, ref, x, y, rot=0, ref_off=None, val_off=None):
        p = next(q for q in D.PARTS if q["ref"] == ref)
        self._symbol(p["lib_id"], ref, p["value"], p["footprint"], x, y, rot, p, ref_off, val_off)
        self.placed[ref] = (x, y, rot)

    def power(self, kind, p, rot=0):
        lib_id = {"GND": "power:GND", "+3V3": "power:+3V3", "PWR_FLAG": "power:PWR_FLAG"}[kind]
        self.n += 1
        ref = "#PWR%03d" % self.n if kind != "PWR_FLAG" else "#FLG%03d" % self.n
        # value text beyond the far end of the graphic, in the direction the symbol points
        base = (0, 1) if kind == "GND" else (0, -1)          # schematic frame, rot 0
        a = {0: (1, 0, 0, 1), 90: (0, 1, -1, 0), 180: (-1, 0, 0, -1), 270: (0, -1, 1, 0)}[rot]
        dx = a[0] * base[0] + a[1] * base[1]
        dy = a[2] * base[0] + a[3] * base[1]
        d = 4.45 if kind != "PWR_FLAG" else 4.0
        off = (dx * d, dy * d + (0.6 if dy > 0 else (-0.2 if dy < 0 else 0.4)))
        just = "center" if dx == 0 else ("left" if dx > 0 else "right")
        self._symbol(lib_id, ref, kind, "", p[0], p[1], rot, None, None, off, power=True, val_just=just)

    def _symbol(self, lib_id, ref, value, footprint, x, y, rot, part, ref_off, val_off, power=False, val_just="left"):
        u = self.uid("s-" + ref)
        sym = SYM[lib_id]
        dnp = "yes" if part and part["dnp"] else "no"
        in_bom = "no" if (power or (part and not part["in_bom"])) else "yes"
        ro = ref_off or ((2.54, -1.27) if rot in (0, 180) else (1.27, -3.81))
        vo = val_off or ((2.54, 1.27) if rot in (0, 180) else (1.27, 3.81))
        hide_ref = " (hide yes)" if power else ""
        props = [('Reference', ref, ro, hide_ref), ('Value', value, vo, ""),
                 ('Footprint', footprint, (0, 0), " (hide yes)"), ('Datasheet', "~", (0, 0), " (hide yes)")]
        if part:
            props += [("Description", part["desc"], (0, 0), " (hide yes)"),
                      ("Spec", part["spec"], (0, 0), " (hide yes)"),
                      ("LCSC", part["lcsc"], (0, 0), " (hide yes)"),
                      ("Manufacturer", part["mfr"], (0, 0), " (hide yes)"),
                      ("MPN", part["mpn"], (0, 0), " (hide yes)")]
        ptxt = []
        for k, v, off, hide in props:
            v = v.replace('"', "'")
            ang = 90 if rot in (90, 270) else 0
            just = ""
            if k in ("Reference", "Value"):
                j = val_just if (power and k == "Value") else "left"
                # text justification is applied in the symbol frame: mirror it for 180 deg
                if rot in (180, 270) and j in ("left", "right"):
                    j = "right" if j == "left" else "left"
                just = "" if j == "center" else " (justify %s)" % j
            ptxt.append('(property "%s" "%s" (at %s %s %d) (effects (font (size 1.27 1.27))%s%s))'
                        % (k, v, fmt(x + off[0]), fmt(y + off[1]), ang, just, hide))
        pins = "".join('(pin "%s" (uuid "%s"))' % (p["number"], new_uuid(u + p["number"] + str(i)))
                       for i, p in enumerate(sym.pins))
        self.items.append(
            '(symbol (lib_id "%s") (at %s %s %d) (unit 1) (exclude_from_sim no) (in_bom %s) (on_board yes) (dnp %s) '
            '(uuid "%s") %s %s (instances (project "%s" (path "/%s" (reference "%s") (unit 1)))))'
            % (lib_id, fmt(x), fmt(y), rot, in_bom, dnp, u, " ".join(ptxt), pins, D.PROJECT, ROOT_UUID, ref))

    def pin(self, ref, number):
        x, y, rot = self.placed[ref]
        p = next(q for q in D.PARTS if q["ref"] == ref)
        sp = next(q for q in SYM[p["lib_id"]].pins if q["number"] == number)
        return transform(sp["x"], sp["y"], x, y, rot)

    def pin_dir(self, ref, number):
        x, y, rot = self.placed[ref]
        p = next(q for q in D.PARTS if q["ref"] == ref)
        sp = next(q for q in SYM[p["lib_id"]].pins if q["number"] == number)
        return outward_dir(sp["angle"], rot)

    def stub(self, ref, number, length=2.54, label_angle=None):
        """Connect a pin to its design.py net with a short wire and a label/power symbol/no-connect."""
        p = next(q for q in D.PARTS if q["ref"] == ref)
        net = p["pins"][number]
        a = self.pin(ref, number)
        if net is None:
            self.noconnect(a)
            return
        dx, dy = self.pin_dir(ref, number)
        b = (round(a[0] + dx * length, 4), round(a[1] + dy * length, 4))
        self.wire(a, b)
        if net == "GND":
            self.power("GND", b, {(0, 1): 0, (0, -1): 180, (1, 0): 90, (-1, 0): 270}[(dx, dy)])
        elif net == "+3V3":
            self.power("+3V3", b, {(0, -1): 0, (0, 1): 180, (1, 0): 270, (-1, 0): 90}[(dx, dy)])
        else:
            ang = label_angle if label_angle is not None else (180 if dx < 0 else 0)
            self.label(net, b, ang)

    def stubs(self, ref, numbers=None, **kw):
        p = next(q for q in D.PARTS if q["ref"] == ref)
        for n in (numbers or p["pins"].keys()):
            self.stub(ref, n, **kw)


S = Sheet()
ROOT_UUID = new_uuid("root-sheet")


# ---------------------------------------------------------------- layout
CELL_RIGHT = 210.82


def cell_block(n, o, yc):
    x0 = 12.7
    S.frame(x0, yc - 15.24, CELL_RIGHT, yc + 50.8,
            f"CELL {n}: CR2032 -> P-MOSFET -> TPS63900 (3.4 V) -> Schottky -> 3V3_PWR")
    bt, r, q, u, l, d = f"BT{n}", f"R{1 + o}", f"Q{n}", f"U{n}", f"L{n}", f"D{n}"
    c_in = [f"C{1 + o}", f"C{2 + o}", f"C{3 + o}"]
    c_out = f"C{4 + o}"
    rcfg = [f"R{2 + o}", f"R{3 + o}", f"R{4 + o}"]
    tp_vbat, tp_vin, tp_vout = f"TP{n}", f"TP{2 + n}", f"TP{4 + n}"
    S.place(bt, 22.86, yc + 5.08, 0, ref_off=(3.81, -1.27), val_off=(3.81, 1.27))
    S.place(r, 40.64, yc, 90, ref_off=(-1.27, -2.54), val_off=(-1.27, 3.81))
    S.place(q, 63.5, yc + 2.54, 90, ref_off=(3.81, 2.54), val_off=(3.81, 5.08))
    for i, c in enumerate(c_in):
        S.place(c, 81.28 + i * 12.7, yc + 3.81, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place(u, 139.7, yc + 10.16, 0, ref_off=(-7.62, -14.22), val_off=(3.81, 13.97))
    S.place(l, 119.38, yc + 15.24, 0, ref_off=(-5.08, -1.27), val_off=(-7.62, 1.27))
    S.place(c_out, 165.1, yc + 3.81, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place(d, 186.69, yc, 180, ref_off=(-2.54, -2.54), val_off=(-3.81, 3.81))
    for i, rr in enumerate(rcfg):
        S.place(rr, 162.56 + i * 10.16, yc + 26.67, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    for tp, x in ((tp_vbat, 30.48), (tp_vin, 116.84), (tp_vout, 172.72)):
        S.place(tp, x, yc - 5.08, 0, ref_off=(1.27, -3.81), val_off=(1.27, -6.35))
    # main chain along y = yc, split at every connection point
    S.wire(S.pin(bt, "1"), (30.48, yc), S.pin(r, "1"))
    S.wire(S.pin(tp_vbat, "1"), (30.48, yc))
    S.junction((30.48, yc))
    S.label(f"VBAT{n}", (24.13, yc), 0)
    S.wire(S.pin(r, "2"), S.pin(q, "3"))
    S.label(f"VBAT{n}_L", (46.99, yc), 0)
    vin_pts = [S.pin(q, "2"), (73.66, yc)] + [S.pin(c, "1") for c in c_in] + [(116.84, yc), (124.46, yc),
                                                                            S.pin(u, "10")]
    S.wire(*vin_pts)
    for p in vin_pts[1:-1]:
        S.junction(p)
    S.wire(S.pin(tp_vin, "1"), (116.84, yc))
    S.power("PWR_FLAG", (73.66, yc - 5.08), 0)
    S.wire((73.66, yc - 5.08), (73.66, yc))
    S.label(f"VIN{n}", (86.36, yc), 0)
    # EN and SEL tied to VIN
    S.wire((124.46, yc), (124.46, yc + 5.08), (124.46, yc + 7.62))
    S.wire((124.46, yc + 5.08), S.pin(u, "1"))
    S.wire((124.46, yc + 7.62), S.pin(u, "2"))
    S.junction((124.46, yc + 5.08))
    # inductor
    lx1, lx2 = S.pin(u, "9"), S.pin(u, "7")
    S.wire(lx1, (119.38, lx1[1]), S.pin(l, "1"))
    S.wire(lx2, (119.38, lx2[1]), S.pin(l, "2"))
    S.label(f"LX1_{n}", (120.65, lx1[1]), 0)
    S.label(f"LX2_{n}", (120.65, lx2[1]), 0)
    S.stub(q, "1", length=2.54)
    S.stub(bt, "2")
    for c in c_in + [c_out]:
        S.stub(c, "2")
    S.stub(u, "8", length=2.54)
    # output side
    out_pts = [S.pin(u, "6"), S.pin(c_out, "1"), (172.72, yc), S.pin(d, "2")]
    S.wire(*out_pts)
    S.junction(S.pin(c_out, "1"))
    S.junction((172.72, yc))
    S.wire(S.pin(tp_vout, "1"), (172.72, yc))
    S.label(f"VOUT{n}", (152.4, yc), 0)
    S.wire(S.pin(d, "1"), (196.85, yc))
    S.label("3V3_PWR", (196.85, yc), 0)
    # configuration resistors via labels
    for pin in ("3", "4", "5"):
        S.stub(u, pin, length=5.08)
    for rr in rcfg:
        S.stub(rr, "1", label_angle=0)
        S.stub(rr, "2")
    S.text("SEL = H: VO(2) = 3.4 V (RCFG1 0R), input limit 100 mA (RCFG2 10.5k; 13.3k = 50 mA option),\n"
           "VO(1) = 3.3 V (RCFG3 16.2k, unused). TI SLVSET3D tables 7-2/7-3, +-1 % resistors.",
           (x0 + 1.27, yc + 41.91), size=1.27)


def rail_block():
    x1, y1 = 213.36, 17.78
    S.frame(x1, y1, 303.53, 86.36, "3V3 RAIL, SUPERVISOR, RESET, DEBUG SUPPLY")
    y = 35.56
    S.label("3V3_PWR", (228.6, y), 180)
    S.place("TP7", 233.68, y - 5.08, 0, ref_off=(1.27, -3.81), val_off=(1.27, -6.35))
    S.place("C21", 241.3, y + 3.81, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("C22", 256.54, y + 3.81, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("JP1", 266.7, y - 10.16, 0, ref_off=(-1.27, 3.81), val_off=(-3.81, 6.35))
    S.place("R21", 280.67, y, 90, ref_off=(-1.27, -2.54), val_off=(-1.27, 3.81))
    S.place("TP8", 289.56, y + 5.08, 180, ref_off=(1.905, 3.81), val_off=(1.905, 6.35))
    rail = [(228.6, y), (233.68, y), S.pin("C21", "1"), S.pin("C22", "1"), (270.51, y), S.pin("R21", "1")]
    S.wire(*rail)
    for p in rail[1:-1]:
        S.junction(p)
    S.wire(S.pin("TP7", "1"), (233.68, y))
    S.wire(S.pin("JP1", "2"), (270.51, y - 10.16), (270.51, y))
    S.stub("JP1", "1")
    S.stub("C21", "2")
    S.stub("C22", "2")
    S.wire(S.pin("R21", "2"), (289.56, y), (297.18, y))
    S.junction((289.56, y))
    S.wire(S.pin("TP8", "1"), (289.56, y))
    S.power("+3V3", (297.18, y), 0)
    S.power("PWR_FLAG", (297.18, y), 180)

    # supervisor
    ys = 66.04
    S.place("C26", 228.6, ys, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("U3", 248.92, ys, 0, ref_off=(3.81, -6.35), val_off=(3.81, 10.16))
    S.place("R22", 266.7, ys, 90, ref_off=(-1.27, -3.81), val_off=(-1.27, 3.81))
    S.place("C25", 279.4, ys + 3.81, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("SW2", 289.56, ys + 5.08, 270, ref_off=(5.08, -1.27), val_off=(5.08, 1.27))
    S.stubs("U3", ["3", "1"])
    S.stubs("C26")
    S.wire(S.pin("U3", "2"), S.pin("R22", "1"))
    S.label("nRST", (259.08, ys), 0)
    S.wire(S.pin("R22", "2"), S.pin("C25", "1"), S.pin("SW2", "1"), (297.18, ys))
    S.junction(S.pin("C25", "1"))
    S.junction(S.pin("SW2", "1"))
    S.label("EN", (297.18, ys), 0)
    S.stub("C25", "2")
    S.stub("SW2", "2")


def module_block():
    x1, y1, x2, y2 = 213.36, 91.44, 406.4, 213.36
    S.frame(x1, y1, x2, y2, "ESP32-H2-MINI-1-H4S, 32.768 kHz CRYSTAL, USER/BOOT BUTTON, LED, DEBUG PADS")
    ux, uy = 304.8, 154.94
    S.place("U4", ux, uy, 0, ref_off=(-33.02, -29.21), val_off=(5.08, 31.75))
    for num in ["8", "10", "12", "13", "24", "25", "9", "31", "30", "27", "26", "5", "6", "18", "19", "20", "21",
                "22", "23", "16"]:
        S.stub("U4", num, length=5.08)
    # supply pins and decoupling
    p3, p15 = S.pin("U4", "3"), S.pin("U4", "15")
    top = p3[1] - 12.7
    S.wire(p3, (p3[0], top))
    S.wire(p15, (p15[0], top))
    S.place("C23", 322.58, top + 3.81, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("C24", 332.74, top + 3.81, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.wire((297.18, top), (p3[0], top), (p15[0], top), S.pin("C23", "1"), S.pin("C24", "1"))
    S.junction((p3[0], top))
    S.junction((p15[0], top))
    S.junction(S.pin("C23", "1"))
    S.power("+3V3", (297.18, top), 0)
    S.stub("C23", "2")
    S.stub("C24", "2")
    S.stub("U4", "1", length=2.54)
    # crystal
    S.place("Y1", 241.3, 175.26, 0, ref_off=(-2.54, -3.81), val_off=(-5.08, -6.35))
    S.place("C27", 231.14, 179.07, 0, ref_off=(-6.35, -1.27), val_off=(-6.35, 1.27))
    S.place("C28", 251.46, 179.07, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.wire(S.pin("C27", "1"), S.pin("Y1", "1"))
    S.wire(S.pin("Y1", "2"), S.pin("C28", "1"))
    S.label("XTAL_32K_P", (231.14, 175.26), 180)
    S.label("XTAL_32K_N", (251.46, 175.26), 0)
    S.stub("C27", "2")
    S.stub("C28", "2")
    # USER/BOOT button and pull-ups
    S.place("R23", 360.68, 186.69, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("SW1", 370.84, 196.85, 270, ref_off=(5.08, -1.27), val_off=(5.08, 1.27))
    S.stub("R23", "1")
    S.wire(S.pin("R23", "2"), (360.68, 191.77), S.pin("SW1", "1"))
    S.wire((350.52, 191.77), (360.68, 191.77))
    S.junction((360.68, 191.77))
    S.label("BTN_USER", (350.52, 191.77), 180)
    S.stub("SW1", "2")
    S.place("R24", 388.62, 186.69, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.stub("R24", "1")
    S.stub("R24", "2", label_angle=0)
    # LED
    S.place("R25", 370.84, 165.1, 90, ref_off=(-1.27, -2.54), val_off=(-1.27, 3.81))
    S.place("D3", 386.08, 165.1, 180, ref_off=(-2.54, -2.54), val_off=(-2.54, 3.81))
    S.stub("R25", "1")
    S.wire(S.pin("R25", "2"), S.pin("D3", "2"))
    S.label("LED_A", (375.92, 165.1), 0)
    S.stub("D3", "1")
    # USB series resistors and debug pads
    S.place("R28", 373.38, 142.24, 90, ref_off=(-1.27, -2.54), val_off=(-1.27, 3.81))
    S.place("R29", 373.38, 154.94, 90, ref_off=(-1.27, -2.54), val_off=(-1.27, 3.81))
    S.stubs("R28")
    S.stubs("R29")
    S.place("J1", 396.24, 113.03, 0, ref_off=(-2.54, -11.43), val_off=(-2.54, -8.89))
    S.stubs("J1", [str(i) for i in range(1, 7)], length=5.08)
    g = S.pin("J1", "7")
    S.wire(g, (g[0] - 2.54, g[1]), (g[0] - 2.54, g[1] + 2.54))
    S.power("GND", (g[0] - 2.54, g[1] + 2.54), 0)
    S.text("GPIO8/GPIO9 are strapping pins: GPIO9 low at reset (SW1 held) = download mode.\n"
           "VBAT (pad 15) is tied to 3V3 inside the module (R2 = 0R); connected here as well.\n"
           "Unused GPIO0/1/2/3/25: no connect, firmware disables input + pull-down.\n"
           "J1 is a pad row (not fitted): pin 6 3V3_DBG only reaches the rail when JP1 is closed.\n"
           "Reset for programming: SW2 (RST) or the USB-Serial/JTAG reset; EN is not on J1.",
           (x1 + 1.27, 195.58))


def sensor_block():
    x1, y1 = 307.34, 17.78
    S.frame(x1, y1, 406.4, 86.36, "SHT40 (on a slotted tongue, away from converters and module)")
    S.place("U5", 365.76, 50.8, 0, ref_off=(-6.35, -8.89), val_off=(-15.24, 10.16))
    scl, sda = S.pin("U5", "2"), S.pin("U5", "1")
    S.place("R27", 347.98, scl[1] - 3.81, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("R26", 325.12, sda[1] - 3.81, 0, ref_off=(-5.08, -1.27), val_off=(-5.08, 1.27))
    S.wire(scl, S.pin("R27", "2"), (340.36, scl[1]))
    S.wire(sda, S.pin("R26", "2"), (317.5, sda[1]))
    S.junction(S.pin("R27", "2"))
    S.junction(S.pin("R26", "2"))
    S.label("I2C_SCL", (340.36, scl[1]), 180)
    S.label("I2C_SDA", (317.5, sda[1]), 180)
    S.stub("R27", "1")
    S.stub("R26", "1")
    S.stubs("U5", ["3", "4"])
    S.place("C29", 388.62, 50.8, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.stubs("C29")
    S.text("No copper under the sensor except its pads; do not solder the die pad (SHT4x datasheet).",
           (x1 + 1.27, 79.38))


def sense_block():
    x1, y1 = 12.7, 165.1
    S.frame(x1, y1, CELL_RIGHT, 231.14, "CELL VOLTAGE SENSE (switched 470k/470k dividers, ADC1_CH0 / ADC1_CH3)")
    for n, o, x in ((1, 0, 45.72), (2, 2, 121.92)):
        rt, rb, c, q = f"R{31 + o}", f"R{32 + o}", f"C{30 + n}", f"Q{2 + n}"
        S.place(rt, x, 182.88, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
        S.place(rb, x, 196.85, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
        S.place(c, x + 12.7, 194.31, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
        S.place(q, x - 2.54, 210.82, 0, ref_off=(3.81, -1.27), val_off=(3.81, 1.27))
        S.stub(rt, "1", label_angle=0)
        mid = (x, 189.23)
        S.wire(S.pin(rt, "2"), mid, S.pin(rb, "1"))
        S.wire(mid, (x + 12.7, 189.23), S.pin(c, "1"))
        S.wire((x + 12.7, 189.23), (x + 22.86, 189.23))
        S.junction(mid)
        S.junction((x + 12.7, 189.23))
        S.label(f"VBAT{n}_SENSE", (x + 22.86, 189.23), 0)
        S.wire(S.pin(rb, "2"), S.pin(q, "3"))
        S.label(f"SNS{n}_LO", (x, 203.2), 0)
        S.stub(c, "2")
        S.stub(q, "2")
        S.stub(q, "1", length=5.08)
    S.place("R35", 167.64, 210.82, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.stubs("R35")
    S.text("Switches open: no divider current. GPIO0 high for ~30 ms every 6 h: 470k/470k -> 3.3 uA per cell.\n"
           "Each divider top is at the holder terminal (before the 0R link), so a missing cell reads ~0 V.",
           (x1 + 1.27, 222.25))


def misc_block():
    x1, y1 = 12.7, 238.76
    S.frame(x1, y1, CELL_RIGHT, 284.48, "TEST PADS, MECHANICAL, NOTES")
    for k, i in enumerate((9, 10)):
        S.place(f"TP{i}", 22.86 + k * 12.7, 254.0, 0, ref_off=(1.27, -3.81), val_off=(1.27, -6.35))
        S.stub(f"TP{i}", "1")
    S.power("PWR_FLAG", (50.8, 251.46), 0)
    S.wire((50.8, 251.46), (50.8, 256.54))
    S.power("GND", (50.8, 256.54), 0)
    for k, ref in enumerate(["FID1", "FID2"]):
        S.place(ref, 71.12 + k * 15.24, 254.0, 0, ref_off=(-2.54, -5.08), val_off=(-2.54, 5.08))
    S.text("CR2032 ONLY - NOT RECHARGEABLE. Both cells must be the same brand/lot and replaced together.\n"
           "Power-path decision and its limits: docs/decisions.md, docs/power_budget.md (ESTIMATE until measured).\n"
           "Current measurement: remove R1 / R11 (per cell) or R21 (load) and insert the ammeter.\\n"
           "U3 TPS3839K33: 2.93 V typ (2.857-2.974 V), push-pull ~RESET, 200 ms delay; R22 keeps it from fighting SW2 / J1 EN.",
           (x1 + 1.27, 266.7))


def build():
    load_symbols()
    write_project_libs()
    cell_block(1, 0, 33.02)
    cell_block(2, 10, 106.68)
    rail_block()
    module_block()
    sensor_block()
    sense_block()
    misc_block()
    missing = [q["ref"] for q in D.PARTS if q["ref"] not in S.placed]
    if missing:
        raise SystemExit("not placed: %s" % missing)
    lib_symbols = "\n".join(SYM[k].embedded() for k in sorted(SYM))
    title = ('(title_block (title "%s") (date "%s") (rev "%s") (company "TH-SENSOR-H2") '
             '(comment 1 "ESP32-H2 Matter over Thread, SHT40, 2 x CR2032 (one TPS63900 per cell)") '
             '(comment 4 "Generated by hardware/scripts/gen_schematic.py from design.py - edit there") '
             '(comment 2 "Power path and battery life figures are ESTIMATES (docs/power_budget.md)") '
             '(comment 3 "ERC/DRC reports: hardware/reports"))' % (D.TITLE, D.DATE, D.REV))
    body = "\n".join(S.items)
    sch = ('(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0") (uuid "%s") (paper "A3")\n'
           '%s\n(lib_symbols\n%s\n)\n%s\n(sheet_instances (path "/" (page "1")))\n(embedded_fonts no)\n)\n'
           % (ROOT_UUID, title, lib_symbols, body))
    with open(SCH, "w") as f:
        f.write(sch)
    print("wrote", SCH, len(S.items), "items")


def check_parity():
    net_path = os.path.join(OUT, D.PROJECT + ".net")
    r = subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net_path, SCH],
                       capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr)
        raise SystemExit("netlist export failed")
    text = open(net_path).read()
    got = {}
    for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)\)\s*(?=\(net |\)\s*\)\s*$)', text, re.S):
        name = m.group(1).lstrip("/")
        for n in re.finditer(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)):
            got[(n.group(1), n.group(2))] = name
    want = {}
    for p in D.PARTS:
        for pin, net in p["pins"].items():
            if net:
                want[(p["ref"], pin)] = net
    errors = []
    for k, v in sorted(want.items()):
        g = got.get(k)
        if g != v:
            errors.append("%s.%s: design %s, schematic %s" % (k[0], k[1], v, g))
    for k, v in sorted(got.items()):
        if k not in want and not k[0].startswith("#"):
            if not v.startswith("unconnected-"):
                errors.append("%s.%s: on net %s in schematic, unconnected in design" % (k[0], k[1], v))
    if errors:
        print("PARITY ERRORS (%d):" % len(errors))
        print("\n".join(errors[:60]))
        return False
    print("parity: %d pins match design.py" % len(want))
    return True


if __name__ == "__main__":
    build()
    if "--no-check" not in sys.argv:
        sys.exit(0 if check_parity() else 1)
