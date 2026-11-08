#!/usr/bin/env python3
"""
Build hardware/wroom/kicad/th_sensor_h2w.kicad_pcb: TH-SENSOR-H2W Rev A, the ESP32-H2-WROOM-02C variant of the
TH-SENSOR-H2 board (docs/wroom_variant.md).

Square outline including the module antenna: the board is 37.6 x 31.6 mm and the module's 6 mm antenna area
overhangs its top edge, so the whole assembly fits a 37.6 x 37.6 mm square. 37.6 mm is the CR2450 holder's land
pattern (37.0 mm over the pads, drawing MY-CP-0138) plus 0.3 mm copper-to-edge on each side. The holder and the
SHT40 (with C29) sit on the back, everything else on the front: the sensor faces down, away from settling dust,
and C5 is a 3.1 mm tantalum, so the front is no taller than the module.

Module position: ESP32-H2 Hardware Design Guidelines, "Positioning a Module on a Base Board", figure "antenna feed
point on the right", position 3 (marked as strongly recommended): module in the top-right corner, its PCB antenna
outside the base board. The WROOM-02C feed is on the right of its antenna (datasheet figure 6).

Stack-up JLC04161H-7628 (4 layers, 1.6 mm):
  L1 F.Cu    parts, short connections, GND pour
  L2 In1.Cu  GND plane, no tracks
  L3 In2.Cu  second routing layer (signals, power), GND pour in the rest
  L4 B.Cu    holder pads, SHT40 and its tracks on the back of the tongue, GND pour outside the cell (the holder's
             - pad sits in it); no tracks and no pour under the cell and the holder body, only tented vias (the cell
             rests on the holder's plastic floor, not on the board: drawing MY-CP-0138, side view)
Coordinates are relative to the board's top-left corner (KiCad y down), as in gen_pcb.py.

Usage: TH_VARIANT=wroom python3 gen_pcb_wroom.py [--no-route] [--silk-draft]
"""
import math
import os
import subprocess
import sys

if os.environ.get("TH_VARIANT", "wroom") != "wroom":
    raise SystemExit("gen_pcb_wroom.py builds the WROOM variant: run it with TH_VARIANT=wroom")
os.environ["TH_VARIANT"] = "wroom"

import pcbnew  # noqa: E402

import design as D  # noqa: E402
import gen_pcb as G  # noqa: E402  (helpers; its module-level placement is for Rev B and is not used here)

HERE = os.path.dirname(os.path.abspath(__file__))
KDIR = os.path.join(D.HW_DIR, "kicad")
PCB = os.path.join(KDIR, D.PROJECT + ".kicad_pcb")
SCH = os.path.join(KDIR, D.PROJECT + ".kicad_sch")
REPORTS = os.path.join(D.HW_DIR, "reports")
OX, OY = G.OX, G.OY
W, H = 37.6, 31.6
# gen_pcb's helpers read these module globals
G.KDIR, G.SCH, G.PCB, G.PROJ_FP = KDIR, SCH, PCB, os.path.join(KDIR, "lib", "th_sensor.pretty")
G.W, G.H = W, H
V, mm = G.V, G.mm
CU4 = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")
SIGNAL_W, POWER_W = 0.25, 0.4
VIA_S = (0.45, 0.2)              # JLC multilayer: 0.2 mm hole, 0.45 mm pad, no surcharge
CORNER_R = 1.5

# ------------------------------------------------------------------ module, holder, sensor tongue
MOD = (27.8, 4.0)                # module centre: body x 18.8..36.8, y -6..14; antenna area y -6..0 (off board)
CELL = (W / 2, H - 12.25 - 0.3)  # CR2450 centre (holder on the back), cell edge 0.3 mm inside the bottom edge
CELL_R = 12.25 + 0.6
CELL_BODY = (13.6, 8.1)          # holder body half-size (27.0 x 16.0 mm + margin)
# SHT40 tongue in the top-left corner: x 0..TX, y 0..TY. A 1 mm slot runs in from the left edge under the
# tongue and turns up along its right side; it stops BY below the top edge, which leaves the bridge
# (x TX..TX+1, y 0..BY) as the only connection to the board.
TONGUE = dict(tx=6.6, ty=5.4, by=2.6, sw=1.0)

PLACE = {}


def at(ref, x, y, rot=0, back=False):
    PLACE[ref] = (round(x, 4), round(y, 4), rot, back)


at("U4", *MOD, 0)
at("BT1", *CELL, 0, back=True)          # flipped: + (pad 1) ends up on the left
# tongue, BACK side (sensor facing down): the SHT40 turned so that SDA/SCL face the bridge; C29 on the far side
# between VDD and GND, GND leaves over the top and VDD under the bottom (nothing crosses on the tongue, where vias
# are not allowed). Back footprints are mirrored: at rot 0, SDA/SCL end up on the right (bridge) side.
at("U5", 3.4, 2.4, 0, back=True)
at("C29", 1.4, 2.4, 90, back=True)
# left of the module: decoupling at pin 1, EN cap at pin 2, divider at pin 4, pull-ups at pins 7/8
at("C24", 16.55, 1.1, 180)              # pad 1 (+3V3) next to pin 1
at("C25", 16.55, 2.65, 180)             # pad 1 (EN) next to pin 2
at("C31", 16.55, 5.8, 180)              # pad 1 (VBAT_SENSE) next to pin 4
at("R27", 10.2, 4.0, 90)                # I2C pull-ups past the bridge, pad 2 (SCL / SDA) up; SCL left, SDA right,
at("R26", 11.7, 4.0, 90)                # the order in which the back lanes reach their vias
at("R32", 12.7, 7.6, 90)
at("R31", 14.2, 7.6, 90)
at("U3", 10.0, 7.8, 0)
at("C26", 9.6, 10.6, 0)
at("R22", 12.6, 10.6, 0)
at("Q3", 12.6, 13.05, 0)
at("R35", 16.55, 13.3, 180)             # pad 1 (VBAT_MEAS_EN) towards pin 10
at("R24", 16.55, 10.1, 180)             # pad 2 (STRAP_GPIO8) next to pin 7
at("R23", 16.55, 11.65, 180)            # pad 2 (BTN_USER) next to pin 8
# USER/BOOT: side-push switch in the middle of the left edge, actuator 0.5 mm over the edge (pads 0.35 mm inside)
at("SW1", 1.6, H / 2, 270)
at("FID1", 9.3, 13.6, 0)
# under the module: 32.768 kHz crystal at pins 11/12, LED at pin 15
at("Y1", 23.3, 16.4, 180)               # pad 1 (XTAL_32K_P) left, under pin 11; pad 2 under pin 12
at("C27", 21.3, 19.1, 270)              # load caps beyond the crystal, signal pad up
at("C28", 25.3, 19.1, 270)
at("C23", 27.05, 16.3, 270)             # 10 uF at pin 14 (VBAT, tied to 3V3 in the module), pad 1 up
at("R25", 28.6, 16.4, 90)
at("D3", 28.6, 19.4, 90)
# converter (Rev A block orientation: input on the left, towards the cell's + contact)
BLOCK = dict(ux=17.0, uy=26.2)


def block_xy(x, y):
    return BLOCK["ux"] + x, BLOCK["uy"] + y


for key, x, y, rot in G.BLOCK_PLACE:
    ref = G.BLOCK_REFS[key]
    if ref.startswith("TP"):
        continue
    at(ref, *block_xy(x, y), rot)
at("C5", 10.6, 18.6, 0)                 # tantalum, pad 1 (+, marked end) left
at("C21", 22.6, 23.5, 90)
at("C22", 25.3, 23.5, 90)
at("R21", 22.8, 28.6, 0)
at("J1", 33.4, 23.9, 0)
at("FID2", 30.6, 21.2, 0)
# test pads (front), next to their nets
for ref, (x, y) in {"TP1": (2.0, 24.2), "TP2": (2.0, 26.8), "TP3": (34.2, 17.2), "TP4": (19.0, 18.0),
                    "TP5": (31.6, 17.2), "TP6": (13.75, 2.4)}.items():
    at(ref, x, y, 0)


# ------------------------------------------------------------------ outline and rule areas
def outline(board):
    """Square top-right corner (module pad 28 is 0.3 mm from both edges there), rounded elsewhere; the tongue
    slot starts at the left edge and ends in a half circle (router bit)."""
    L = pcbnew.Edge_Cuts
    r = CORNER_R
    t = TONGUE
    tx, ty, by, sw = t["tx"], t["ty"], t["by"], t["sw"]
    path = [((r, 0), (W, 0)),
            ((W, 0), (W, H - r)),
            ((W - r, H), (r, H)),
            ((0, H - r), (0, ty + sw)),
            ((0, ty + sw), (tx + sw, ty + sw)),
            ((tx + sw, ty + sw), (tx + sw, by + sw / 2)),
            ((tx, by + sw / 2), (tx, ty)),
            ((tx, ty), (0, ty)),
            ((0, ty), (0, r))]
    for a, b in path:
        G.add_line(board, L, a, b)
    G.add_arc(board, L, (tx + sw, by + sw / 2), (tx + sw / 2, by), (tx, by + sw / 2))     # slot end
    G.corner(board, L, W - r, H - r, r, 0)
    G.corner(board, L, r, H - r, r, 90)
    G.corner(board, L, r, r, r, 180)


def outline_polygon():
    r = CORNER_R
    t = TONGUE
    tx, ty, by, sw = t["tx"], t["ty"], t["by"], t["sw"]
    pts = [(W, 0)]
    for cx, cy, a0 in ((W - r, H - r, 0), (r, H - r, 90)):
        for k in range(0, 91, 15):
            tt = math.radians(a0 + k)
            pts.append((cx + r * math.cos(tt), cy + r * math.sin(tt)))
    pts += [(0, ty + sw), (tx + sw, ty + sw), (tx + sw, by), (tx, by), (tx, ty), (0, ty)]
    for k in range(0, 91, 15):
        tt = math.radians(180 + k)
        pts.append((r + r * math.cos(tt), r + r * math.sin(tt)))
    return pts


def rect(x1, y1, x2, y2):
    return [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]


def build_board(path=PCB):
    pcbnew.KIID.SeedGenerator(1)
    board = pcbnew.NewBoard(path)
    board.SetCopperLayerCount(4)
    bds = board.GetDesignSettings()
    bds.m_TrackMinWidth = mm(0.127)
    bds.m_MinClearance = mm(0.127)
    bds.m_ViasMinSize = mm(0.45)
    bds.m_MinThroughDrill = mm(0.2)
    bds.m_ViasMinAnnularWidth = mm(0.125)
    bds.m_CopperEdgeClearance = mm(0.3)
    bds.m_HoleToHoleMin = mm(0.5)
    bds.m_HoleClearance = mm(0.2)
    bds.m_TentViasFront = True
    bds.m_TentViasBack = True
    bds.SetAuxOrigin(V(0, H))
    tb = board.GetTitleBlock()
    tb.SetTitle(D.BOARD_NAME)
    tb.SetRevision(D.REV)
    tb.SetDate(D.DATE)
    tb.SetComment(0, "ESP32-H2-WROOM-02C Matter/Thread thermo-hygrometer, 1 x CR2450, TPS63900 3.3 V")
    tb.SetComment(1, "Generated by hardware/scripts/gen_pcb_wroom.py - 4 layers, 1.6 mm, JLC04161H-7628")

    paths, sch_pins = G.schematic_netlist()
    KN = G.KN
    KN.clear()
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
        fp = G.load_footprint(p["footprint"])
        fp.SetReference(ref)
        fp.SetValue(p["value"])
        x, y, rot, back = PLACE[ref]
        fp.SetPosition(V(x, y))
        fp.SetOrientationDegrees(rot)
        for k, v in (("LCSC", p["lcsc"]), ("MPN", p["mpn"]), ("Manufacturer", p["mfr"]), ("Spec", p["spec"])):
            if v:
                fp.SetField(k, v)
                f = fp.GetFieldByName(k)
                f.SetVisible(False)
                f.SetLayer(pcbnew.B_Fab if back else pcbnew.F_Fab)
        if ref in paths:
            fp.SetPath(pcbnew.KIID_PATH("/" + paths[ref]))
        fp.SetDNP(bool(p["dnp"]))
        fp.SetExcludedFromBOM(not p["in_bom"])
        if not p["in_bom"] or p["dnp"]:
            fp.SetExcludedFromPosFiles(True)
        board.Add(fp)
        if back:                    # (flipping needs the board: KiCad crashes on a free footprint)
            fp.Flip(V(x, y), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
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
    t = TONGUE
    G.rule_area(board, "SHT40_TONGUE", rect(0, 0, t["tx"] + t["sw"], t["ty"]), layers=CU4, tracks=False,
                vias=True, pour=True)
    # back: nothing but tented vias under the cell and the holder body
    cx, cy = CELL
    bx, by = CELL_BODY
    G.rule_area(board, "CELL_BT1", G.circle_pts(cx, cy, CELL_R), layers=("B.Cu",), tracks=True, vias=False, pour=True)
    G.rule_area(board, "HOLDER_BT1", rect(cx - bx, cy - by, cx + bx, cy + by), layers=("B.Cu",), tracks=True,
                vias=False, pour=True)
    return board, nets


# ------------------------------------------------------------------ placement check
def courtyard_overlaps(board):
    out = []
    for layer in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
        polys = [(fp.GetReference(), fp.GetCourtyard(layer)) for fp in board.GetFootprints()]
        for i in range(len(polys)):
            for j in range(i + 1, len(polys)):
                a, pa = polys[i]
                b, pb = polys[j]
                if pa.OutlineCount() == 0 or pb.OutlineCount() == 0:
                    continue
                if not pa.BBox().Intersects(pb.BBox()):
                    continue
                c = pcbnew.SHAPE_POLY_SET(pa)
                c.BooleanIntersection(pb)
                if c.OutlineCount() and c.Area() > 1e3:
                    out.append((a, b, round(c.Area() / 1e12 * 1e6, 3)))
    return out


# ------------------------------------------------------------------ fixed copper
# SHT40 tongue (tracks only, all on B.Cu: the sensor is on the back): lanes through the bridge at 0.5 mm pitch, top
# to bottom GND, SDA, SCL, VDD. Past the bridge each lane ends in a via, the bottom one first, so that no lane
# crosses another: VDD, SCL, SDA, GND from left to right. On the front, short tracks take the vias into the pull-ups
# (R27 = SCL left, R26 = SDA right) and VDD into the +3V3 pad of R27; GND joins the planes at its via.
BCU, FCU = pcbnew.B_Cu, pcbnew.F_Cu
TV = {"+3V3": (8.3, 2.8), "I2C_SCL": (9.3, 2.3), "I2C_SDA": (10.3, 1.8), "GND": (10.9, 0.55)}
TONGUE_ROUTES = [
    ("GND", SIGNAL_W, BCU, [("U5", "4"), (2.1, 2.0), ("C29", "2")]),
    ("GND", SIGNAL_W, BCU, [("C29", "2"), (1.4, 0.55), TV["GND"]]),
    ("I2C_SDA", SIGNAL_W, BCU, [("U5", "1"), (4.8, 2.0), (4.8, 1.05), (TV["I2C_SDA"][0], 1.05), TV["I2C_SDA"]]),
    ("I2C_SCL", SIGNAL_W, BCU, [("U5", "2"), (5.3, 2.8), (5.3, 1.55), (TV["I2C_SCL"][0], 1.55), TV["I2C_SCL"]]),
    ("+3V3", SIGNAL_W, BCU, [("U5", "3"), (2.1, 2.8), ("C29", "1")]),
    ("+3V3", SIGNAL_W, BCU, [("C29", "1"), (1.4, 4.6), (6.1, 4.6), (6.1, 2.05), (TV["+3V3"][0], 2.05), TV["+3V3"]]),
    # front: vias into the pull-ups
    ("I2C_SCL", SIGNAL_W, FCU, [TV["I2C_SCL"], ("R27", "2")]),
    ("I2C_SDA", SIGNAL_W, FCU, [TV["I2C_SDA"], (11.2, 1.8), (11.7, 2.3), ("R26", "2")]),
    ("+3V3", SIGNAL_W, FCU, [TV["+3V3"], (8.3, 4.825), ("R27", "1")]),
    ("+3V3", SIGNAL_W, FCU, [("R27", "1"), ("R26", "1")]),
]
TONGUE_VIAS = sorted(TV.items())

# module thermal pad: the datasheet's via pattern (3 in the 2.8 x 0.55 strip, the 4 corners of the 2.8 x 1.6 area;
# the centre of that area is the 0.8 mm hand-soldering hole of the footprint)
EPAD_VIAS = [(round(MOD[0] - 0.47 + dx, 4), round(MOD[1] + 2.01, 4)) for dx in (-1.05, 0.0, 1.05)] + \
            [(round(MOD[0] - 0.47 + dx, 4), round(MOD[1] + 3.73 + dy, 4)) for dx in (-1.05, 1.05) for dy in (-0.5, 0.5)]
# holder on the back: B.Cu stubs from the + pad (left) to two vias just below it; the - pad (right) needs none,
# it sits in the back GND pour, outside the cell area
HOLDER_VIAS = {"VBAT": [(1.4, 21.95), (2.8, 21.95)]}
# module escapes: pin 1 (+3V3) to C24 and a via inside the pad ring, pin 14 to C23, the UART/USB pins of the
# right column (no room right of them: board edge) inwards to a column of vias
MOD_ROUTES = [
    ("+3V3", POWER_W, [("U4", "1"), ("C24", "1")]),
    ("+3V3", POWER_W, [("U4", "1"), (20.45, 1.1)]),
    ("+3V3", POWER_W, [("U4", "14"), ("C23", "1")]),
] + [(net, SIGNAL_W, [("U4", pin), (34.9, round(MOD[1] - 2.9 + 1.5 * (28 - int(pin)), 4))])
     for pin, net in (("21", "U0RXD"), ("22", "U0TXD"), ("23", "USB_DM"), ("24", "USB_DP"))]
MOD_VIAS = [("+3V3", (20.45, 1.1))] + [(net, (34.9, round(MOD[1] - 2.9 + 1.5 * (28 - int(pin)), 4)))
                                       for pin, net in (("21", "U0RXD"), ("22", "U0TXD"), ("23", "USB_DM"),
                                                        ("24", "USB_DP"))]


def hand_copper(board, nets):
    def point(p):
        return G.pad_xy(board, *p) if isinstance(p[0], str) else p

    for net, w, layer, pts in TONGUE_ROUTES:
        ps = [point(p) for p in pts]
        for a, c in zip(ps[:-1], ps[1:]):
            G.add_track(board, nets[net], a, c, w, layer=layer)
    for net, p in TONGUE_VIAS:
        G.add_via(board, nets[net], p, *VIA_S)
    # converter block (Rev A orientation): the hand routes of gen_pcb.py without the Rev B test-pad branches
    for net, w, pts in G.BLOCK_ROUTES:
        if any(isinstance(q[0], str) and q[0].startswith("TP") for q in pts):
            continue
        ps = [G.pad_xy(board, G.BLOCK_REFS[q[0]], q[1]) if isinstance(q[0], str) else block_xy(*q) for q in pts]
        for a, c in zip(ps[:-1], ps[1:]):
            G.add_track(board, nets[net], a, c, w)
    for net, q in G.BLOCK_VIAS:
        G.add_via(board, nets[net], block_xy(*q))
    for q in EPAD_VIAS:
        G.add_via(board, nets["GND"], q, *VIA_S)
    for net, w, pts in MOD_ROUTES:
        ps = [point(p) for p in pts]
        for a, c in zip(ps[:-1], ps[1:]):
            G.add_track(board, nets[net], a, c, w)
    for net, q in MOD_VIAS:
        G.add_via(board, nets[net], q, *VIA_S)
    # holder + pad (back): one 0.5 mm stub per via
    for net, pad in (("VBAT", "1"),):
        cx, cy = G.pad_xy(board, "BT1", pad)
        for vx, vy in HOLDER_VIAS[net]:
            G.add_track(board, nets[net], (vx, cy), (vx, vy), 0.5, layer=pcbnew.B_Cu)
            G.add_via(board, nets[net], (vx, vy))


# ------------------------------------------------------------------ routing
ROUTE_PLAN = [
    # (net, width, layer costs F.Cu / In2.Cu, small vias)
    ("XTAL_32K_P", SIGNAL_W, (1.0, 50.0), True),
    ("XTAL_32K_N", SIGNAL_W, (1.0, 50.0), True),
    # J1 pad 1 (TX) is the far corner of the pad block from the module: route it first
    ("U0TXD", SIGNAL_W, (2.0, 1.0), True),
    ("U0RXD", SIGNAL_W, (2.0, 1.0), True),
    ("USB_DP", SIGNAL_W, (2.0, 1.0), True),
    ("USB_DM", SIGNAL_W, (2.0, 1.0), True),
    ("LED", SIGNAL_W, (1.0, 2.0), True),
    ("LED_A", SIGNAL_W, (1.0, 2.0), True),
    ("I2C_SDA", SIGNAL_W, (1.0, 1.5), True),
    ("I2C_SCL", SIGNAL_W, (1.0, 1.5), True),
    ("STRAP_GPIO8", SIGNAL_W, (1.0, 2.0), True),
    ("BTN_USER", SIGNAL_W, (1.0, 1.5), True),
    ("VBAT_SENSE", SIGNAL_W, (1.0, 2.0), True),
    ("SNS_LO", SIGNAL_W, (1.0, 2.0), True),
    ("VBAT_MEAS_EN", SIGNAL_W, (1.0, 1.5), True),
    ("EN", SIGNAL_W, (1.5, 1.0), True),
    ("nRST", SIGNAL_W, (1.0, 1.5), True),
    ("VIN", POWER_W, (1.0, 2.0), False),
    ("VOUT", POWER_W, (1.0, 2.0), False),
    ("VBAT", POWER_W, (1.5, 1.0), False),
    ("+3V3", POWER_W, (1.5, 1.0), False),
]
ROUTE_LAYERS = (pcbnew.F_Cu, pcbnew.In2_Cu)


def router_keepouts(R):
    t = TONGUE
    # the tongue carries only its four hand-routed tracks
    R.keepout_polygon(rect(0, 0, t["tx"] + t["sw"], t["ty"] + t["sw"]), layers=(0, 1), tracks=True, vias=True)
    # module underside on F.Cu: only escapes within 1 mm of the pad ring (vias allowed there)
    x0, x1 = MOD[0] - 9.0 + 2.0, MOD[0] + 9.0 - 2.0
    R.keepout_polygon(rect(x0, 0.0, x1, MOD[1] + 10.0 - 2.1), layers=(0,), tracks=True, vias=False)
    # 32.768 kHz crystal: nothing under it (HDG crystal guidelines)
    x, y = PLACE["Y1"][:2]
    R.keepout_polygon(rect(x - 1.0, y - 0.9, x + 1.0, y + 0.9), layers=(0, 1), tracks=True, vias=True)
    for ref in ("FID1", "FID2"):
        fx, fy = PLACE[ref][:2]
        R.keepout_polygon(G.circle_pts(fx, fy, 1.35, 24), layers=(0,), tracks=True, vias=True)


def route(board, nets):
    import router as RT
    R = RT.Router(board, OX, OY, W, H, grid=0.1, clearance=0.2, edge_clearance=0.3,
                  classes={"w25": 0.125, "w30": 0.15, "w40": 0.20, "w50": 0.25, "via": 0.30}, layers=ROUTE_LAYERS)
    R.build()
    router_keepouts(R)
    R.block_vias_in_smd_pads(0.6)
    skip = {"J1", "BT1", G.BLOCK_REFS["U"]}
    gnd_pads = [p for fp in board.GetFootprints() if fp.GetReference() not in skip
                for p in fp.Pads() if p.GetNetname() == "GND" and not (fp.GetReference() == "U4" and p.GetNumber() == "29")]
    tied = set()
    for cl in R.clusters("GND"):
        if any(t.GetClass() == "PCB_VIA" for t in cl["tracks"]):
            tied |= {RT.pad_name(p) for p in cl["pads"]}
    gnd_pads = [p for p in gnd_pads if RT.pad_name(p) not in tied]
    R.gnd_fanout(gnd_pads, via_dia=VIA_S[0], via_drill=VIA_S[1])
    for net, w, lc, small in ROUTE_PLAN:
        dia, drill = VIA_S if small else (0.6, 0.3)
        R.route_net(G.KN[net], width=w, layer_cost=lc, via_dia=dia, via_drill=drill)
    return R


def drop_one_sided_vias(board):
    """Signal vias the router did not continue carry copper on one layer only: remove them."""
    planes = {"GND", "+3V3"}
    tracks, pads = {}, {}
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA":
            tracks.setdefault(t.GetNetCode(), []).append(t)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pads.setdefault(p.GetNetCode(), []).append(p)
    keep = {q for _, q in TONGUE_VIAS + MOD_VIAS}
    removed = 0
    for v in [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]:
        if v.GetNetname() in planes:
            continue
        q = v.GetPosition()
        if (round(pcbnew.ToMM(q.x) - OX, 4), round(pcbnew.ToMM(q.y) - OY, 4)) in keep:
            continue
        layers = {t.GetLayer() for t in tracks.get(v.GetNetCode(), [])
                  if v.HitTest(t.GetStart()) or v.HitTest(t.GetEnd())}
        layers |= {L for p in pads.get(v.GetNetCode(), []) for L in (pcbnew.F_Cu, pcbnew.B_Cu)
                   if p.IsOnLayer(L) and p.HitTest(q)}
        if len(layers) < 2:
            board.Remove(v)
            removed += 1
    return removed


def stitch(board, R):
    """GND vias: a row along the top edge under the module (HDG: dense ground vias near the antenna), then a
    2.5 mm grid."""
    sites = [(x, 0.7) for x in [20.6 + 1.0 * k for k in range(15)]]
    y = 1.2
    while y < H - 0.8:
        x = 1.0
        while x < W - 0.8:
            sites.append((x, y))
            x += 2.5
        y += 2.5
    return R.stitch(sites, via_dia=VIA_S[0], via_drill=VIA_S[1])


def add_zones(board, nets):
    poly = outline_polygon()
    for layer, name in (("F.Cu", "GND_L1"), ("In1.Cu", "GND_L2"), ("In2.Cu", "GND_L3"), ("B.Cu", "GND_L4")):
        G.copper_zone(board, layer, nets["GND"], poly, name=name)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def prune_stitching(board, vias):
    """Stitching vias that reach only the L2 plane (no fill of another layer around them) are removed."""
    zones = [z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname() == "GND"]
    removed = 0
    for v in vias:
        p = v.GetPosition()
        hits = sum(1 for z in zones for L in z.GetLayerSet().Seq() if z.HitTestFilledArea(L, p))
        if hits < 2:
            board.Remove(v)
            removed += 1
    return removed


# ------------------------------------------------------------------ silkscreen
SILK_LABELS = (("USER/BOOT", "SW1", (4.0, 15.0, 4.4, 16.6), (90,)),)


def silkscreen(board):
    sp = G.SilkPlacer(board)
    t = TONGUE
    tx, ty, by, sw = t["tx"], t["ty"], t["by"], t["sw"]
    sp.cuts = [(0, ty, tx + sw, ty + sw), (tx, by, tx + sw, ty + sw)]
    hidden, missing = [], []
    order = sorted(board.GetFootprints(), key=lambda f: -f.GetCourtyard(pcbnew.F_CrtYd).Area()
                   if f.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else 0)

    def txt(text, size=1.0, bold=False, layer="F.SilkS"):
        return G.silk_text(board, text, 0, 0, size, bold=bold, layer=layer)

    for label, ref, region, angles in SILK_LABELS:
        tl = txt(label, 0.8)
        if not sp.free_spot(tl, region, step=0.1, angles=angles):
            missing.append(label)
    # fixed marks: where the sensor is (front of the tongue, which carries no copper now) and "+" at the corner of
    # C5's pad 1, the end the tantalum's band marks
    x1, y1 = G.pad_xy(board, "C5", "1")
    for text, x, y, size, bold in (("SHT40", 3.3, 1.6, 0.8, False), ("ON BACK", 3.3, 3.35, 0.8, False),
                                   ("+", x1 - 1.86, y1 - 3.3, 0.8, False)):
        tm = G.silk_text(board, text, x, y, size, bold=bold)
        if not sp.free(sp._bbox(tm)):
            missing.append(text)
        sp.claim(tm)
    # J1 (not fitted): pin names beside the left column, one row per header row
    jx, jy = PLACE["J1"][:2]
    for i, line in enumerate(("TX RX", "D+ D-", "BOOT GND")):
        tj = G.silk_text(board, line, jx - 2.0, jy + 2.54 * i, 0.8, justify="right")
        if not sp.free(sp._bbox(tj)):
            missing.append(line)
        sp.claim(tj)
    # test pads show their net name (VBAT, VIN, 3V3, ...); the TP numbers stay on the assembly drawing
    tps = sorted((f for f in board.GetFootprints() if f.GetReference().startswith("TP")),
                 key=lambda f: int(f.GetReference()[2:]))
    for fp in tps:
        fp.Reference().SetVisible(False)
        if not sp.place_reference(fp, field=fp.Value()):
            missing.append(fp.GetReference() + " " + fp.GetValue())
    # then the current-measurement links: the bring-up procedure refers to them by name
    for ref in ("R1", "R21"):
        if not sp.place_reference(board.FindFootprintByReference(ref)):
            missing.append(ref)
    for fp in order:
        ref = fp.GetReference()
        if ref in ("R1", "R21") or ref.startswith("TP"):
            continue
        if fp.IsFlipped() or ref == "U4" or not sp.place_reference(fp):
            fp.Reference().SetVisible(False)
            hidden.append(ref)
    # back: cell warning and board name behind the module's right half, date in the free corner below the cell
    for text, y, bold in (("CR2450 ONLY", 5.2, True), ("NO CHARGE", 6.8, True), ("TH-SENSOR", 8.4, False),
                          ("H2W Rev %s" % D.REV, 10.0, False)):
        G.silk_text(board, text, 32.8, y, 0.8, layer="B.SilkS", bold=bold)
    G.silk_text(board, D.DATE, 5.0, 28.6, 0.8, layer="B.SilkS")
    if missing and "--silk-draft" not in sys.argv:
        raise RuntimeError("silkscreen: no room for " + ", ".join(missing))
    if missing:
        print("silkscreen: no room for " + ", ".join(missing))
    return hidden


if __name__ == "__main__":
    board, nets = build_board()
    overlaps = courtyard_overlaps(board)
    if overlaps:
        print("courtyards overlap: %s" % overlaps)
        if "--place-only" not in sys.argv:
            raise SystemExit(1)
    if "--place-only" not in sys.argv:
        hand_copper(board, nets)
        report = []
        if "--no-route" not in sys.argv:
            R = route(board, nets)
            one_sided = drop_one_sided_vias(board)
            trimmed = G.remove_dangling(board)
            report += R.log
            report.append("one-sided signal vias removed: %d; dangling stub segments trimmed or removed: %d"
                          % (one_sided, trimmed))
            hidden = silkscreen(board)              # before the stitching vias, which then keep out of the texts
            report.append("references hidden (back side, module, or no room): %s" % ", ".join(sorted(hidden)))
            vias = stitch(board, R)
            add_zones(board, nets)
            removed = prune_stitching(board, vias)
            report.append("stitching vias: %d placed, %d removed (L2 only)" % (len(vias), removed))
            pcbnew.ZONE_FILLER(board).Fill(board.Zones())
            os.makedirs(REPORTS, exist_ok=True)
            with open(os.path.join(REPORTS, "routing_log.txt"), "w") as f:
                f.write("\n".join(report) + "\n")
                f.write("unrouted: %d\n" % len(R.unrouted))
                for u in R.unrouted:
                    f.write("  " + u + "\n")
            print("\n".join(report[-3:]))
            print("unrouted:", len(R.unrouted), R.unrouted[:30])
    pcbnew.SaveBoard(PCB, board)
    subprocess.run([sys.executable, os.path.join(HERE, "gen_project.py")], check=True)
    board = pcbnew.LoadBoard(PCB)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    print("saved", PCB)
