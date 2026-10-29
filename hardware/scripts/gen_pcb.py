#!/usr/bin/env python3
"""
Build hardware/kicad/th_sensor_h2.kicad_pcb from design.py: placement, board
outline, rule areas, hand-routed converter blocks, routing (router.py), ground
planes, stitching vias and silkscreen.

Board: 72 x 58 mm, 2 layers, 1.6 mm FR-4, all parts on the top side.
Coordinates below are relative to the board's top-left corner (KiCad y down).

Usage: python3 gen_pcb.py [--no-route]
"""
import math
import os
import re
import subprocess
import sys

import pcbnew

import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
KDIR = os.path.normpath(os.path.join(HERE, "..", "kicad"))
PCB = os.path.join(KDIR, D.PROJECT + ".kicad_pcb")
SCH = os.path.join(KDIR, D.PROJECT + ".kicad_sch")
KFP = "/usr/share/kicad/footprints/"
PROJ_FP = os.path.join(KDIR, "lib", "th_sensor.pretty")
REPORTS = os.path.normpath(os.path.join(HERE, "..", "reports"))

OX, OY = 100.0, 60.0          # board origin on the KiCad page
W, H = 72.0, 58.0             # board size
CORNER_R = 1.5

# Module position follows the ESP32-H2 hardware design guidelines, section
# "Positioning a Module on a Base Board", figure "Keepout Zone for ESP32-H2
# Module's Antenna (feed point on the left)": module in the top-left corner,
# module edge <= 2 mm from the left board edge, <= 1 mm from the top edge, and
# no board material for >= 15 mm beside the 5.4 mm antenna region.
MOD_X, MOD_Y = 8.6, 8.8                      # module centre; body 13.2 x 16.6 mm
MOD_L, MOD_T = MOD_X - 6.6, MOD_Y - 8.3      # 2.0 / 0.5 mm from the edges
NOTCH_X1, NOTCH_X2, NOTCH_D = MOD_X + 6.8, MOD_X + 6.8 + 15.2, 6.0
SHT_TONGUE = dict(x1=61.0, slot_y=13.0, bridge_y2=3.4, slot_w=1.0)
CELL_R = 10.6                                 # CR2032 radius 10.0 + 0.6 margin
SIGNAL_W, POWER_W = 0.25, 0.4

mm = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


# ------------------------------------------------------------------ placement
# (x, y, rotation in degrees counter-clockwise) relative to the board corner
PLACE = {}


def at(ref, x, y, rot=0):
    PLACE[ref] = (x, y, rot)


at("U4", MOD_X, MOD_Y, 0)
at("C24", 1.0, 7.6, 90)            # 100 nF beside pad 3 (3V3), in the 2 mm strip left of the module
# debug header (not fitted) under the antenna notch: order follows the module pins
at("J1", 17.3, 7.9, 90)            # 1 TXD 2 RXD 3 D+ 4 D- 5 BOOT 6 3V3_DBG 7 GND, pitch 2.54 along +x
at("R29", 18.0, 12.4, 0)           # USB D+ 22R
at("R28", 18.0, 14.2, 0)           # USB D- 22R
at("R25", 16.2, 17.4, 90)          # LED, beside the module corner (LED pad at the bottom)
at("D3", 17.9, 17.4, 90)           # anode at the top, next to R25
# user/boot button, pull-ups, rail junction (bulk caps, load link, debug-supply jumper, test pads)
at("SW1", 36.0, 3.2, 180)          # BTN pads at the bottom
at("R23", 41.4, 5.2, 180)
at("R24", 41.4, 7.0, 180)
at("JP1", 30.0, 11.5, 270)
at("TP7", 30.0, 14.6, 0)
at("C21", 32.6, 13.0, 90)          # 3V3_PWR pad at the bottom
at("C22", 35.2, 13.0, 90)
at("R21", 37.8, 13.4, 90)
at("TP8", 40.2, 11.6, 0)
at("FID2", 47.0, 9.0, 0)
# SHT40 on the slotted tongue (top-right corner), pull-ups on the main board side of the bridge
at("U5", 67.4, 5.4, 270)
at("C29", 67.4, 8.6, 0)
at("R26", 54.8, 4.6, 270)
at("R27", 56.6, 4.6, 270)
# 32.768 kHz crystal under XTAL_32K_P/N (pads 12/13), load caps under it
at("Y1", 3.6, 20.4, 180)
at("C27", 2.35, 23.3, 270)
at("C28", 4.85, 23.3, 270)
# cell-voltage dividers below pads 16/18/19
at("C32", 9.4, 23.1, 270)
at("R34", 9.4, 26.5, 270)
at("Q4", 9.4, 30.1, 90)
at("R33", 11.6, 25.1, 90)
at("C31", 14.2, 23.1, 270)
at("R32", 14.2, 26.5, 270)
at("Q3", 14.2, 30.1, 90)
at("R31", 16.4, 25.1, 90)
at("R35", 11.8, 33.1, 0)
# supervisor, EN RC, module bulk cap, reset button: along the EN lane on the left edge
at("U3", 3.8, 27.6, 0)
at("C26", 6.6, 28.6, 270)
at("C23", 6.6, 32.2, 270)
at("R22", 2.6, 31.0, 180)
at("C25", 2.6, 33.2, 180)
at("SW2", 3.0, 38.75, 90)
at("TP9", 9.0, 35.8, 0)
at("FID1", 16.4, 33.6, 0)
at("TP10", 69.4, 38.0, 0)


# one cell's converter, laid out like the TPS63900 datasheet example: inductor
# above the IC, input capacitors left, output capacitor right, CFG resistors below
def block_refs(n, o):
    return dict(U=f"U{n}", L=f"L{n}", Q=f"Q{n}", D=f"D{n}", RL=f"R{1 + o}", C1=f"C{1 + o}", C2=f"C{2 + o}",
                C3=f"C{3 + o}", C4=f"C{4 + o}", RC1=f"R{2 + o}", RC2=f"R{3 + o}", RC3=f"R{4 + o}",
                TPB=f"TP{n}", TPI=f"TP{2 + n}", TPO=f"TP{4 + n}")


def block_nets(n):
    return dict(VIN=f"VIN{n}", VBAT=f"VBAT{n}", VBAT_L=f"VBAT{n}_L", LX1=f"LX1_{n}", LX2=f"LX2_{n}",
                VOUT=f"VOUT{n}", CFG1=f"CFG1_{n}", CFG2=f"CFG2_{n}", CFG3=f"CFG3_{n}", GND="GND")


BLOCKS = {1: dict(o=0, ux=37.9, uy=27.0), 2: dict(o=10, ux=59.4, uy=27.0)}
BLOCK_PLACE = [("U", 0.0, 0.0, 90), ("L", 0.0, -3.15, 0), ("C1", -2.4, -0.45, 270), ("C2", -7.5, 0.25, 270),
               ("C3", -5.0, 0.25, 270), ("C4", 2.7, -0.25, 270), ("RC1", 0.0, 3.6, 270), ("RC2", 1.65, 3.6, 270),
               ("RC3", 3.3, 3.6, 270), ("D", 3.0, -4.6, 270), ("Q", -10.75, -0.275, 180),
               ("RL", -12.6, 3.3, 90), ("TPB", -12.6, 6.7, 0), ("TPI", -6.25, -3.6, 0), ("TPO", 5.55, -1.0, 0)]
# hand-routed copper inside a block: (net, width, points); a point is (part key, pad) or local (x, y)
BLOCK_ROUTES = [
    ("VIN", 0.5, [("Q", "2"), ("C2", "1"), ("C3", "1"), (-3.5, -1.225), ("C1", "1"), (-1.6, -1.225)]),
    ("VIN", 0.25, [(-1.6, -1.225), ("U", "10")]),
    ("VIN", 0.4, [("TPI", "1"), (-6.25, -1.225)]),
    ("VIN", 0.25, [("U", "2"), (-0.5, 1.75), (-3.5, 1.75), (-3.5, -1.225)]),     # EN = SEL = VIN
    ("VIN", 0.25, [("U", "1"), (-1.0, 1.75)]),
    ("VBAT_L", 0.5, [("Q", "3"), (-12.25, -0.275), (-12.25, 2.35), ("RL", "2")]),
    ("VBAT", 0.5, [("RL", "1"), ("TPB", "1")]),
    ("LX1", 0.25, [("U", "9"), (-0.5, -2.45), ("L", "1")]),
    ("LX2", 0.25, [("U", "7"), (0.5, -2.45), ("L", "2")]),
    ("GND", 0.25, [("U", "8"), (0.0, -0.3)]),
    ("VOUT", 0.25, [("U", "6"), (1.6, -1.21)]),
    ("VOUT", 0.5, [(1.6, -1.21), ("C4", "1"), (3.0, -1.2), ("D", "2")]),
    ("VOUT", 0.4, [("C4", "1"), ("TPO", "1")]),
    ("GND", 0.3, [("C1", "2"), (-1.95, 0.2), (-0.6, 0.2)]),
    ("GND", 0.3, [(0.6, 0.35), (2.7, 0.35)]),
    ("GND", 0.4, [("C4", "2"), (4.2, 1.0)]),
    ("GND", 0.4, [("Q", "1"), (-8.76, 1.725), ("C2", "2"), ("C3", "2")]),
    ("GND", 0.4, [(-6.25, 1.725), (-6.25, 3.0)]),
    ("CFG1", 0.25, [("U", "3"), ("RC1", "1")]),
    ("CFG2", 0.25, [("U", "4"), (0.5, 1.95), (1.25, 2.7), ("RC2", "1")]),
    ("CFG3", 0.25, [("U", "5"), (1.0, 1.75), (1.25, 2.0), (3.0, 2.0), (3.3, 2.3), ("RC3", "1")]),
    ("GND", 0.3, [("RC1", "2"), ("RC2", "2"), ("RC3", "2")]),
    ("GND", 0.3, [(-1.1, 4.375), ("RC1", "2")]),
]
BLOCK_VIAS = [("GND", (4.2, 1.0)), ("GND", (-6.25, 3.0)), ("GND", (-1.1, 4.375))]

for n, b in BLOCKS.items():
    refs = block_refs(n, b["o"])
    for key, x, y, rot in BLOCK_PLACE:
        at(refs[key], b["ux"] + x, b["uy"] + y, rot)

# holders: + pad (pad 1) on the right with rotation 180; cell centre = footprint origin
CELLS = {"BT1": (19.0, 46.6), "BT2": (53.0, 46.6)}
for ref, (x, y) in CELLS.items():
    at(ref, x, y, 180)

# module GND pad array (pad 49, 3 x 3): vias in the gaps between the pads, tented
MOD_GND_VIAS = [(MOD_X + dx, MOD_Y + dy) for dx in (-0.9875, 0.9875) for dy in (1.7125, 3.6875)]
MOD_STUB = 1.2           # straight escape from every used module pad, routed before anything else

# fixed copper outside the converter blocks: pad 3 decoupling, and the SHT40 tongue. The four
# sensor nets cross the bridge in the pads' cyclic order (SDA, SCL, VDD, GND) so nothing crosses
# inside the tongue, where vias are not allowed; GND wraps round C29 and drops to a via on the
# main board next to the slot.
FIXED_ROUTES = [
    ("+3V3", 0.3, [("U4", "3"), (1.7, 9.1), ("C24", "1")]),
    ("GND", 0.3, [("C24", "2"), (1.7, 7.5), ("U4", "1")]),
    ("I2C_SDA", SIGNAL_W, [(58.6, 0.85), (67.8, 0.85), ("U5", "1")]),
    ("I2C_SCL", SIGNAL_W, [(58.6, 1.45), (67.0, 1.45), ("U5", "2")]),
    ("+3V3", 0.3, [(58.6, 2.05), (65.8, 2.05), (65.8, 7.0), (67.0, 7.0), ("U5", "3")]),
    ("+3V3", 0.3, [(65.8, 7.0), (65.8, 8.6), ("C29", "1")]),
    ("GND", 0.3, [(59.3, 4.3), (59.3, 2.65), (65.0, 2.65), (65.0, 9.6), (68.9, 9.6), (68.9, 7.0), (67.8, 7.0),
                  ("U5", "4")]),
    ("GND", 0.3, [("C29", "2"), (68.9, 8.6)]),
]
FIXED_VIAS = [("GND", (59.3, 4.3))]


# ------------------------------------------------------------------ helpers
def load_footprint(fpid):
    lib, name = fpid.split(":")
    path = PROJ_FP if lib == "th_sensor" else KFP + lib + ".pretty"
    fp = pcbnew.FootprintLoad(path, name)
    if fp is None:
        raise SystemExit("footprint not found: " + fpid)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def schematic_netlist():
    """From the KiCad netlist: reference -> symbol UUID (links footprints to symbols) and
    (ref, pin) -> net name exactly as the schematic names it (local labels carry a '/')."""
    net = os.path.join(KDIR, D.PROJECT + ".net")
    subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net, SCH],
                   check=True, capture_output=True)
    text = open(net).read()
    paths = {}
    for m in re.finditer(r'\(comp \(ref "([^"]+)"\).*?\(tstamps "([^"]+)"\)', text, re.S):
        paths[m.group(1)] = m.group(2)
    pins = {}
    chunks = re.split(r'\(net \(code "\d+"\) ', text[text.index("(nets"):])[1:]
    for ch in chunks:
        name = re.match(r'\(name "([^"]+)"\)', ch).group(1)
        for n in re.finditer(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', ch):
            pins[(n.group(1), n.group(2))] = name
    return paths, pins


KN = {}          # design.py net name -> KiCad net name, filled by build_board()


def add_line(board, layer, a, b, width=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(*a))
    s.SetEnd(V(*b))
    s.SetLayer(layer)
    s.SetWidth(mm(width))
    board.Add(s)
    return s


def add_arc(board, layer, start, mid, end, width=0.1):
    s = pcbnew.PCB_SHAPE(board)
    s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetArcGeometry(V(*start), V(*mid), V(*end))
    s.SetLayer(layer)
    s.SetWidth(mm(width))
    board.Add(s)


def corner(board, layer, cx, cy, r, a0):
    """Quarter arc around (cx, cy) from angle a0 to a0 + 90 degrees (y down, angles clockwise)."""
    pts = []
    for a in (a0, a0 + 45, a0 + 90):
        t = math.radians(a)
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    add_arc(board, layer, *pts)


def outline(board):
    """Rounded rectangle; antenna notch top-left; SHT40 tongue top-right cut free by 1 mm slots."""
    L = pcbnew.Edge_Cuts
    r = CORNER_R
    t = SHT_TONGUE
    sw = t["slot_w"]
    xs, ys, by2 = t["x1"], t["slot_y"], t["bridge_y2"]
    path = [((r, 0), (NOTCH_X1, 0)),
            ((NOTCH_X1, 0), (NOTCH_X1, NOTCH_D)),
            ((NOTCH_X1, NOTCH_D), (NOTCH_X2, NOTCH_D)),
            ((NOTCH_X2, NOTCH_D), (NOTCH_X2, 0)),
            ((NOTCH_X2, 0), (W - r, 0))]
    for a, b in path:
        add_line(board, L, a, b)
    corner(board, L, W - r, r, r, -90)                                   # top-right
    add_line(board, L, (W, r), (W, ys))                                  # tongue right edge
    add_line(board, L, (W, ys), (xs, ys))                                # tongue bottom edge
    add_line(board, L, (xs, ys), (xs, by2 + sw / 2))                     # tongue left edge (slot side)
    add_arc(board, L, (xs, by2 + sw / 2), (xs - sw / 2, by2), (xs - sw, by2 + sw / 2))   # slot end
    add_line(board, L, (xs - sw, by2 + sw / 2), (xs - sw, ys + sw))      # main board side of the slot
    add_line(board, L, (xs - sw, ys + sw), (W, ys + sw))                 # main board edge under the slot
    add_line(board, L, (W, ys + sw), (W, H - r))
    corner(board, L, W - r, H - r, r, 0)                                 # bottom-right
    add_line(board, L, (W - r, H), (r, H))
    corner(board, L, r, H - r, r, 90)                                    # bottom-left
    add_line(board, L, (0, H - r), (0, r))
    corner(board, L, r, r, r, 180)                                       # top-left


def outline_polygon():
    """Simplified board outline (no slot) used for the copper zones."""
    r = CORNER_R
    pts = [(r, 0), (NOTCH_X1, 0), (NOTCH_X1, NOTCH_D), (NOTCH_X2, NOTCH_D), (NOTCH_X2, 0), (W - r, 0)]
    for cx, cy, a0 in ((W - r, r, -90), (W - r, H - r, 0), (r, H - r, 90), (r, r, 180)):
        for k in range(0, 91, 15):
            t = math.radians(a0 + k)
            pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts


def circle_pts(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def rule_area(board, name, poly, layers=("F.Cu", "B.Cu"), tracks=True, vias=True, pour=True, pads=False,
              footprints=False):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    z.SetZoneName(name)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(board.GetLayerID(l))
    z.SetLayerSet(ls)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowCopperPour(pour)
    z.SetDoNotAllowPads(pads)
    z.SetDoNotAllowFootprints(footprints)
    o = z.Outline()
    o.NewOutline()
    for x, y in poly:
        o.Append(mm(OX + x), mm(OY + y))
    board.Add(z)
    return z


def copper_zone(board, layer, net, poly, priority=0, clearance=0.25, min_width=0.25, name=""):
    z = pcbnew.ZONE(board)
    z.SetLayer(board.GetLayerID(layer))
    z.SetNet(net)
    z.SetZoneName(name)
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(min_width))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.35))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    o = z.Outline()
    o.NewOutline()
    for x, y in poly:
        o.Append(mm(OX + x), mm(OY + y))
    board.Add(z)
    return z


def silk_text(board, text, x, y, size=1.0, rot=0, layer="F.SilkS", bold=False, justify=None, thick=None):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(V(x, y))
    t.SetLayer({"F.SilkS": pcbnew.F_SilkS, "B.SilkS": pcbnew.B_SilkS, "F.Fab": pcbnew.F_Fab}[layer])
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size)))
    t.SetTextThickness(mm(thick if thick else max(0.15, size * 0.15)))
    t.SetTextAngleDegrees(rot)
    t.SetBold(bold)
    if justify == "left":
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    elif justify == "right":
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_RIGHT)
    if layer.startswith("B."):
        t.SetMirrored(True)
    board.Add(t)
    return t


def add_track(board, net, a, b, width, layer=pcbnew.F_Cu):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(V(*a))
    t.SetEnd(V(*b))
    t.SetWidth(mm(width))
    t.SetLayer(layer)
    t.SetNet(net)
    board.Add(t)
    return t


def add_via(board, net, p, dia=0.6, drill=0.3):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(V(*p))
    v.SetWidth(mm(dia))
    v.SetDrill(mm(drill))
    v.SetNet(net)
    board.Add(v)
    return v


def pad_xy(board, ref, num):
    fp = board.FindFootprintByReference(ref)
    for p in fp.Pads():
        if p.GetNumber() == num:
            q = p.GetPosition()
            return (pcbnew.ToMM(q.x) - OX, pcbnew.ToMM(q.y) - OY)
    raise KeyError(ref + "." + num)


# ------------------------------------------------------------------ board
def build_board(path=PCB):
    board = pcbnew.NewBoard(path)
    board.SetCopperLayerCount(2)
    bds = board.GetDesignSettings()
    bds.m_TrackMinWidth = mm(0.127)
    bds.m_MinClearance = mm(0.127)
    bds.m_ViasMinSize = mm(0.6)
    bds.m_MinThroughDrill = mm(0.3)
    bds.m_ViasMinAnnularWidth = mm(0.15)
    bds.m_CopperEdgeClearance = mm(0.3)
    bds.m_HoleToHoleMin = mm(0.5)
    bds.m_HoleClearance = mm(0.25)
    tb = board.GetTitleBlock()
    tb.SetTitle("TH-SENSOR-H2")
    tb.SetRevision(D.REV)
    tb.SetDate(D.DATE)
    tb.SetComment(0, "ESP32-H2 Matter/Thread thermo-hygrometer, 2 x CR2032 (one TPS63900 per cell)")
    tb.SetComment(1, "Generated by hardware/scripts/gen_pcb.py - 2 layers, 1.6 mm, JLCPCB standard rules")

    paths, sch_pins = schematic_netlist()
    for name, members in D.nets().items():
        kn = {sch_pins.get(m) for m in members}
        if len(kn) != 1 or None in kn:
            raise SystemExit("net %s: schematic names %s" % (name, kn))
        KN[name] = kn.pop()
    nets = {}
    for name in D.nets():
        ni = pcbnew.NETINFO_ITEM(board, KN[name])
        board.Add(ni)
        nets[name] = ni
    nc_nets = {}
    for key, kname in sorted(sch_pins.items()):
        if kname.startswith("unconnected-"):
            ni = pcbnew.NETINFO_ITEM(board, kname)
            board.Add(ni)
            nc_nets[key] = ni
    for p in D.PARTS:
        ref = p["ref"]
        if ref not in PLACE:
            raise SystemExit("no placement for " + ref)
        fp = load_footprint(p["footprint"])
        fp.SetReference(ref)
        fp.SetValue(p["value"])
        x, y, rot = PLACE[ref]
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(rot)
        for k, v in (("LCSC", p["lcsc"]), ("MPN", p["mpn"]), ("Manufacturer", p["mfr"]), ("Spec", p["spec"])):
            if v:
                fp.SetField(k, v)
                f = fp.GetFieldByName(k)
                f.SetVisible(False)
                f.SetLayer(pcbnew.F_Fab)
        if ref in paths:
            fp.SetPath(pcbnew.KIID_PATH("/" + paths[ref]))
        fp.SetDNP(bool(p["dnp"]))
        fp.SetExcludedFromBOM(not p["in_bom"])
        if not p["in_bom"] or p["dnp"]:
            fp.SetExcludedFromPosFiles(True)
        board.Add(fp)
        for pad in fp.Pads():
            net = p["pins"].get(pad.GetNumber())
            if net:
                pad.SetNet(nets[net])
            elif (ref, pad.GetNumber()) in nc_nets:
                pad.SetNet(nc_nets[(ref, pad.GetNumber())])
        fp.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        fp.Reference().SetTextThickness(mm(0.15))
        fp.Value().SetVisible(False)

    outline(board)
    # antenna: no copper left of the module's own keepout either (module footprint carries the rest)
    rule_area(board, "ANTENNA_KEEPOUT", [(0, 0), (NOTCH_X1, 0), (NOTCH_X1, NOTCH_D), (0, NOTCH_D)])
    t = SHT_TONGUE
    # tongue: tracks only, no vias, no pour (thermal isolation of the SHT40)
    rule_area(board, "SHT40_TONGUE", [(t["x1"] - t["slot_w"], 0), (W, 0), (W, t["slot_y"]),
                                      (t["x1"] - t["slot_w"], t["slot_y"])], tracks=False, vias=True, pour=True)
    # nothing on F.Cu under the cells: the CR2032 can (+) rim sits close to the board surface
    for ref, (cx, cy) in CELLS.items():
        rule_area(board, "CELL_" + ref, circle_pts(cx, cy, CELL_R), layers=("F.Cu",))
    return board, nets


def hand_routes(board, nets):
    """Converter blocks, module GND vias: fixed copper drawn before the router runs."""
    for n, b in BLOCKS.items():
        refs = block_refs(n, b["o"])
        bn = block_nets(n)

        def point(p):
            if isinstance(p[0], str):
                return pad_xy(board, refs[p[0]], p[1])
            return (b["ux"] + p[0], b["uy"] + p[1])

        for net, w, pts in BLOCK_ROUTES:
            ps = [point(p) for p in pts]
            for a, c in zip(ps[:-1], ps[1:]):
                add_track(board, nets[bn[net]], a, c, w)
        for net, (x, y) in BLOCK_VIAS:
            add_via(board, nets[bn[net]], (b["ux"] + x, b["uy"] + y))
    for p in MOD_GND_VIAS:
        add_via(board, nets["GND"], p)
    u4 = board.FindFootprintByReference("U4")
    for pad in u4.Pads():
        net = pad.GetNetname()
        if not net or net == KN["GND"]:
            continue
        x, y = pad_xy(board, "U4", pad.GetNumber())
        n = int(pad.GetNumber())
        w = POWER_W if net == KN["+3V3"] else SIGNAL_W
        if 12 <= n <= 24:                       # bottom row: escape downwards
            add_track(board, pad.GetNet(), (x, y), (x, y + MOD_STUB), w)
        elif 25 <= n <= 35:                     # right column: escape to the right
            add_track(board, pad.GetNet(), (x, y), (x + MOD_STUB, y), w)
        elif n == 8:                            # EN: into the 2 mm strip on the left
            add_track(board, pad.GetNet(), (x, y), (1.5, y), w)
    for net, w, pts in FIXED_ROUTES:
        ps = [pad_xy(board, *p) if isinstance(p[0], str) else p for p in pts]
        for a, c in zip(ps[:-1], ps[1:]):
            add_track(board, nets[net], a, c, w)
    for net, p in FIXED_VIAS:
        add_via(board, nets[net], p)


# ------------------------------------------------------------------ routing
# order and widths: power first, then signals; per-net layer costs (F.Cu, B.Cu)
ROUTE_PLAN = [
    ("XTAL_32K_P", SIGNAL_W, (1.0, 50.0)),
    ("XTAL_32K_N", SIGNAL_W, (1.0, 50.0)),
    ("USB_DP", SIGNAL_W, (1.0, 6.0)),
    ("USB_DM", SIGNAL_W, (1.0, 6.0)),
    ("USB_DP_J", SIGNAL_W, (1.0, 6.0)),
    ("USB_DM_J", SIGNAL_W, (1.0, 6.0)),
    ("U0TXD", SIGNAL_W, (1.0, 3.0)),
    ("U0RXD", SIGNAL_W, (1.0, 3.0)),
    # bottom-row pads that head east: rightmost pad first, so each takes the next lane out
    ("LED", SIGNAL_W, (1.0, 3.0)),
    ("LED_A", SIGNAL_W, (1.0, 3.0)),
    ("BTN_USER", SIGNAL_W, (1.0, 2.5)),
    ("STRAP_GPIO8", SIGNAL_W, (1.0, 2.5)),
    ("I2C_SCL", SIGNAL_W, (1.0, 2.5)),
    ("I2C_SDA", SIGNAL_W, (1.0, 2.5)),
    # divider nets go down below the east-going lanes
    ("VBAT_MEAS_EN", SIGNAL_W, (1.0, 3.0)),
    ("VBAT2_SENSE", SIGNAL_W, (1.0, 3.0)),
    ("VBAT1_SENSE", SIGNAL_W, (1.0, 3.0)),
    ("SNS1_LO", SIGNAL_W, (1.0, 3.0)),
    ("SNS2_LO", SIGNAL_W, (1.0, 3.0)),
    ("EN", SIGNAL_W, (1.0, 3.0)),
    ("nRST", SIGNAL_W, (1.0, 3.0)),
    ("3V3_PWR", POWER_W, (1.0, 5.0)),
    ("3V3_DBG", POWER_W, (1.0, 3.0)),
    ("+3V3", POWER_W, (1.0, 4.0)),
    ("VBAT1", POWER_W, (1.0, 5.0)),
    ("VBAT2", POWER_W, (1.0, 5.0)),
]


def router_keepouts(R):
    """Router-only restrictions (no KiCad rule area needed)."""
    # module underside: no signal tracks inside the pad ring on F.Cu, none under the body on B.Cu,
    # no vias except GND (the GND pad-array vias)
    x0, x1 = MOD_X - 5.9 + 0.45, MOD_X + 5.9 - 0.45
    y0, y1 = MOD_Y - 2.2 + 0.45, MOD_Y + 7.6 - 0.45
    R.keepout_polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], layers=(0,), tracks=True, vias=False)
    body = [(MOD_L, MOD_T), (MOD_L + 13.2, MOD_T), (MOD_L + 13.2, MOD_T + 16.6), (MOD_L, MOD_T + 16.6)]
    R.keepout_polygon(body, layers=(1,), tracks=True, vias=True, vias_except_gnd=True)
    # 32 kHz crystal: nothing under it on either layer (HDG crystal guidelines)
    cx, cy, _ = PLACE["Y1"]
    R.keepout_polygon([(cx - 1.0, cy - 0.9), (cx + 1.0, cy - 0.9), (cx + 1.0, cy + 0.9), (cx - 1.0, cy + 0.9)],
                      layers=(0, 1), tracks=True, vias=True)
    # fiducials keep their 2 mm mask opening free
    for ref in ("FID1", "FID2"):
        fx, fy, _ = PLACE[ref]
        R.keepout_polygon(circle_pts(fx, fy, 1.35, 24), layers=(0,), tracks=True, vias=True)


def route(board, nets):
    import router as RT
    R = RT.Router(board, OX, OY, W, H, grid=0.1, clearance=0.2, edge_clearance=0.3)
    R.build()
    router_keepouts(R)
    gnd_pads = []
    skip = {"U4", "J1"}                                   # module: pour + pad-array vias; J1: through-hole
    for fp in board.GetFootprints():
        if fp.GetReference() in skip or fp.GetReference().startswith(tuple(f"U{n}" for n in BLOCKS)):
            continue
        for p in fp.Pads():
            if p.GetNetname() == "GND":
                gnd_pads.append(p)
    # module corner GND pads sit outside the pad ring where the inner pour cannot reach them
    gnd_pads += [p for p in board.FindFootprintByReference("U4").Pads() if p.GetNumber() in ("50", "51", "52", "53")]
    # pads already tied to a via by the hand routes need nothing more
    tied = set()
    for cl in R.clusters("GND"):
        if any(t.GetClass() == "PCB_VIA" for t in cl["tracks"]):
            tied |= {RT.pad_name(p) for p in cl["pads"]}
    gnd_pads = [p for p in gnd_pads if RT.pad_name(p) not in tied]
    R.gnd_fanout(gnd_pads)
    for net, w, lc in ROUTE_PLAN:
        R.route_net(KN[net], width=w, layer_cost=lc)
    return R


def remove_dangling(board):
    """Trim track segments with a free end back to their last junction (escape stubs the router
    did not use, or used part-way); a segment with no junction at all is deleted."""
    changed = 0
    while True:
        tracks, vias, pads = {}, {}, {}
        for t in board.GetTracks():
            (vias if t.GetClass() == "PCB_VIA" else tracks).setdefault(t.GetNetCode(), []).append(t)
        for fp in board.GetFootprints():
            for p in fp.Pads():
                pads.setdefault(p.GetNetCode(), []).append(p)

        def others(t):
            me = t.m_Uuid.AsString()
            return [o for o in tracks.get(t.GetNetCode(), []) if o.GetLayer() == t.GetLayer() and o.m_Uuid.AsString() != me]

        def touches(t, pt):
            L = t.GetLayer()
            if any(p.IsOnLayer(L) and p.HitTest(pt) for p in pads.get(t.GetNetCode(), [])):
                return True
            if any(v.HitTest(pt) for v in vias.get(t.GetNetCode(), [])):
                return True
            return any(o.HitTest(pt) for o in others(t))

        work = 0
        for ts in list(tracks.values()):
            for t in ts:
                a, b = t.GetStart(), t.GetEnd()
                ca, cb = touches(t, a), touches(t, b)
                if ca and cb:
                    continue
                if not ca and not cb:
                    board.Remove(t)
                    work += 1
                    continue
                keep, free = (a, b) if ca else (b, a)
                # junctions on this segment: other segments' ends, vias, pads crossing it
                dx, dy = free.x - keep.x, free.y - keep.y
                L2 = float(dx * dx + dy * dy) or 1.0
                best = None
                cand = [q for o in others(t) for q in (o.GetStart(), o.GetEnd()) if t.HitTest(q)]
                cand += [v.GetPosition() for v in vias.get(t.GetNetCode(), []) if t.HitTest(v.GetPosition())]
                for q in cand:
                    u = ((q.x - keep.x) * dx + (q.y - keep.y) * dy) / L2
                    if 1e-6 < u < 1 - 1e-6 and (best is None or u > best):
                        best = u
                if best is None:
                    board.Remove(t)
                else:
                    end = pcbnew.VECTOR2I(int(round(keep.x + best * dx)), int(round(keep.y + best * dy)))
                    t.SetStart(keep)
                    t.SetEnd(end)
                work += 1
        if not work:
            return changed
        changed += work


def stitch(board, R):
    """GND stitching: dense row along the antenna keepout edge, then a 3.5 mm grid."""
    sites = [(x, NOTCH_D + 0.9) for x in [NOTCH_X1 + 1.0 + 1.5 * k for k in range(10)]]
    sites += [(0.8, 6.9)]
    step = 3.5
    y = 2.0
    while y < H - 1.0:
        x = 2.0
        while x < W - 1.0:
            sites.append((x, y))
            x += step
        y += step
    placed = R.stitch(sites)
    return placed


def add_zones(board, nets):
    poly = outline_polygon()
    copper_zone(board, "F.Cu", nets["GND"], poly, name="GND_TOP")
    copper_zone(board, "B.Cu", nets["GND"], poly, name="GND_BOTTOM")
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())


def prune_stitching(board, vias):
    """Remove stitching vias that ended up connected to only one plane."""
    zones = {z.GetLayer(): z for z in board.Zones() if not z.GetIsRuleArea()}
    removed = 0
    for v in vias:
        p = v.GetPosition()
        ok = all(zones[L].HitTestFilledArea(L, p) for L in (pcbnew.F_Cu, pcbnew.B_Cu))
        if not ok:
            board.Remove(v)
            removed += 1
    return removed


def silkscreen(board):
    silk_text(board, "TH-SENSOR-H2  Rev " + D.REV, 46.0, 54.6, 1.0, bold=True)
    silk_text(board, "CR2032 ONLY - NO CHARGE", 19.0, 56.6, 0.9)
    silk_text(board, "CR2032 ONLY - NO CHARGE", 53.0, 56.6, 0.9)
    silk_text(board, "+", 36.3, 41.4, 1.2, bold=True)
    silk_text(board, "+", 70.3, 41.4, 1.2, bold=True)
    silk_text(board, "TX RX D+ D- BOOT 3V3 GND", 24.9, 10.3, 0.7)
    silk_text(board, "RST", 3.4, 34.0, 0.8)
    silk_text(board, "USER", 36.0, 6.9, 0.8)
    silk_text(board, "SHT40", 66.0, 11.6, 0.7)
    silk_text(board, "ANTENNA KEEPOUT", 9.0, 3.0, 0.8, layer="B.SilkS")
    silk_text(board, "TH-SENSOR-H2 Rev %s  %s" % (D.REV, D.DATE), 36.0, 54.6, 1.0, layer="B.SilkS")
    silk_text(board, "2 x CR2032 in parallel through one buck-boost each - do not recharge", 36.0, 52.4, 0.8,
              layer="B.SilkS")


def place_report(board):
    lines = []
    for fp in board.GetFootprints():
        pos = fp.GetPosition()
        lines.append("%-5s %8.2f %8.2f %6.1f" % (fp.GetReference(), pcbnew.ToMM(pos.x) - OX, pcbnew.ToMM(pos.y) - OY,
                                                fp.GetOrientationDegrees()))
    return "\n".join(sorted(lines))


if __name__ == "__main__":
    board, nets = build_board()
    hand_routes(board, nets)
    report = []
    if "--no-route" not in sys.argv:
        R = route(board, nets)
        report_dangling = remove_dangling(board)
        vias = stitch(board, R)
        report += R.log
        add_zones(board, nets)
        removed = prune_stitching(board, vias)
        report.append("dangling stub segments trimmed or removed: %d" % report_dangling)
        report.append("stitching vias: %d placed, %d removed (single plane)" % (len(vias), removed))
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        silkscreen(board)
        os.makedirs(REPORTS, exist_ok=True)
        with open(os.path.join(REPORTS, "routing_log.txt"), "w") as f:
            f.write("\n".join(report) + "\n")
            f.write("unrouted: %d\n" % len(R.unrouted))
            for u in R.unrouted:
                f.write("  " + u + "\n")
        print("\n".join(report[-8:]))
        print("unrouted:", len(R.unrouted), R.unrouted[:20])
    else:
        silkscreen(board)
    pcbnew.SaveBoard(PCB, board)
    print("saved", PCB)
