#!/usr/bin/env python3
"""
Build hardware/wroom123/kicad/th_sensor_h2w123.kicad_pcb: TH-SENSOR-H2W-123 Rev A, the ESP32-H2-WROOM-02C board
with one CR123A cell (docs/cr123a_variant.md).

Arrangement (user's sketch, 2026-11-11): the cell beside the electronics, the module at the top with its antenna
overhanging the top edge, the SHT40 at the bottom edge, the whole device square. The electronics area is 34.5 mm
wide (user's dimension); the through-hole holder (43.3 x 18.2 mm, drawing MY-CP-0398) takes an 18.8 mm strip, so
the board is 53.3 x 47.3 mm and, with the 6 mm antenna overhang, the device is 53.3 x 53.3 mm.

Mirror image of the sketch: the cell is on the LEFT. The WROOM-02C antenna feed is on the right of its antenna and
the ESP32-H2 Hardware Design Guidelines want it at a board corner ("Positioning a Module on a Base Board", figure
"antenna feed point on the right", position 3) and metal 15 mm away from the antenna: the module is in the
top-right corner and the cell (a steel can) 16 mm left of it.

Mounting: on a wall, back to the wall, antenna up. The side-push USER button is on the bottom edge (pressed from
below) and the SHT40 tongue is the bottom-right corner, below the module and away from the converter.

Everything is on the front. Stack-up JLC04161H-7628 (4 layers, 1.6 mm), as on the H2W board:
  L1 F.Cu    parts, short connections, GND pour
  L2 In1.Cu  GND plane, no tracks
  L3 In2.Cu  second routing layer (signals, power), GND pour in the rest
  L4 B.Cu    GND pour (the holder's two pins and its locating post come through)
Coordinates are relative to the board's top-left corner (KiCad y down), as in gen_pcb.py.

Usage: TH_VARIANT=wroom123 python3 gen_pcb_wroom123.py [--no-route] [--silk-draft] [--place-only]
"""
import math
import os
import subprocess
import sys

if os.environ.get("TH_VARIANT", "wroom123") != "wroom123":
    raise SystemExit("gen_pcb_wroom123.py builds the CR123A board: run it with TH_VARIANT=wroom123")
os.environ["TH_VARIANT"] = "wroom123"

import pcbnew  # noqa: E402

import design as D  # noqa: E402
import gen_pcb as G  # noqa: E402  (helpers; its module-level placement is for Rev B and is not used here)

HERE = os.path.dirname(os.path.abspath(__file__))
KDIR = os.path.join(D.HW_DIR, "kicad")
PCB = os.path.join(KDIR, D.PROJECT + ".kicad_pcb")
SCH = os.path.join(KDIR, D.PROJECT + ".kicad_sch")
REPORTS = os.path.join(D.HW_DIR, "reports")
OX, OY = G.OX, G.OY
ELEC_W = 34.5                    # width of the electronics area (user's dimension)
HOLDER_W = 18.2                  # holder body (drawing MY-CP-0398: 43.3 x 18.2 mm)
W = round(0.3 + HOLDER_W + 0.3 + ELEC_W, 2)     # 53.3: edge margin, holder, gap, electronics
H = round(W - 6.0, 2)            # 47.3: square with the module's 6 mm antenna overhang
# gen_pcb's helpers read these module globals
G.KDIR, G.SCH, G.PCB, G.PROJ_FP = KDIR, SCH, PCB, os.path.join(KDIR, "lib", "th_sensor.pretty")
G.W, G.H = W, H
V, mm = G.V, G.mm
CU4 = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")
SIGNAL_W, POWER_W = 0.25, 0.4
VIA_S = (0.45, 0.2)              # JLC multilayer: 0.2 mm hole, 0.45 mm pad, no surcharge
CORNER_R = 1.5

# ------------------------------------------------------------------ module, holder, sensor tongue
MOD = (W - 0.8 - 9.0, 4.0)       # module centre (43.5, 4): body x 34.5..52.5, y -6..14; antenna y -6..0 (off board)
DX = MOD[0] - 27.8               # shift of everything placed against the module, relative to the H2W board
HOLDER = (0.3 + HOLDER_W / 2, H / 2)     # holder centre; body x 0.3..18.5, y 2.0..45.3
# SHT40 tongue in the bottom-right corner: x W-TX..W, y H-TY..H. A 1 mm slot runs in from the right edge above
# the tongue and turns down along its left side; it stops BY above the bottom edge, which leaves the bridge
# (x W-TX-1..W-TX, y H-BY..H) as the only connection to the board. This is the H2W tongue turned by 180 degrees.
TONGUE = dict(tx=6.6, ty=5.4, by=2.6, sw=1.0)

PLACE = {}


def at(ref, x, y, rot=0, back=False):
    PLACE[ref] = (round(x, 4), round(y, 4), rot, back)


def turned(x, y):
    """H2W tongue coordinates (top-left corner) -> this board (bottom-right corner): half a turn."""
    return (round(W - x, 4), round(H - y, 4))


at("U4", *MOD, 0)
# holder turned so that + (pin 1, next to the locating post) is at the top and the post hole is on the inner side
# (on the outer side it would break through the board edge)
at("BT1", *HOLDER, 270)
at("F1", 22.4, 3.4, 0)                  # fuse right at the + pin; pad 1 (VCELL) towards the holder
# tongue: as on H2W (SCL/SDA face the bridge, C29 on the far side between VDD and GND), turned with the tongue
at("U5", *turned(3.4, 2.4), 0)
at("C29", *turned(1.4, 2.4), 90)
at("R26", *turned(10.2, 4.0), 270)      # I2C pull-ups past the bridge, pad 2 (SDA / SCL) down
at("R27", *turned(11.7, 4.0), 270)
# left of the module: decoupling at pin 1, EN cap at pin 2, divider at pin 4, pull-ups at pins 7/8
at("C24", 16.55 + DX, 1.1, 180)         # pad 1 (+3V3) next to pin 1
at("C25", 16.55 + DX, 2.65, 180)        # pad 1 (EN) next to pin 2
at("C31", 16.55 + DX, 5.8, 180)         # pad 1 (VBAT_SENSE) next to pin 4
# supervisor and sense divider: as on H2W but CL further from the module, which leaves a channel between them and
# the column of parts at the module pins for the I2C lines running down to the tongue
CL = DX - 2.6
at("R32", 12.7 + CL, 7.6, 90)
at("R31", 14.2 + CL, 7.6, 90)
at("U3", 10.0 + CL, 7.8, 0)
at("C26", 9.6 + CL, 10.6, 0)
at("R22", 12.6 + CL, 10.6, 0)
at("Q3", 12.6 + CL, 13.05, 0)
at("R35", 16.55 + DX, 13.3, 180)        # pad 1 (VBAT_MEAS_EN) towards pin 10
at("R24", 16.55 + DX, 10.1, 180)        # pad 2 (STRAP_GPIO8) next to pin 7
at("R23", 16.55 + DX, 11.65, 180)       # pad 2 (BTN_USER) next to pin 8
# USER/BOOT: side-push switch on the bottom edge, actuator 0.5 mm over the edge (pads 0.35 mm inside)
at("SW1", 36.0, H - 1.6, 0)
# under the module: 32.768 kHz crystal at pins 11/12, LED at pin 15
at("Y1", 23.3 + DX, 16.4, 180)          # pad 1 (XTAL_32K_P) left, under pin 11; pad 2 under pin 12
at("C27", 21.3 + DX, 19.1, 270)         # load caps beyond the crystal, signal pad up
at("C28", 25.3 + DX, 19.1, 270)
at("C23", 27.05 + DX, 16.3, 270)        # 10 uF at pin 14 (VBAT, tied to 3V3 in the module), pad 1 up
at("R25", 28.6 + DX, 16.4, 90)
at("D3", 28.6 + DX, 19.4, 90)
# converter (Rev A block orientation: input on the left, towards the cell)
BLOCK = dict(ux=34.0, uy=29.0)


def block_xy(x, y):
    return BLOCK["ux"] + x, BLOCK["uy"] + y


for key, x, y, rot in G.BLOCK_PLACE:
    ref = G.BLOCK_REFS[key]
    if ref.startswith("TP"):
        continue
    at(ref, *block_xy(x, y), rot)
at("C21", BLOCK["ux"] + 5.6, BLOCK["uy"] - 2.7, 90)
at("C22", BLOCK["ux"] + 8.3, BLOCK["uy"] - 2.7, 90)
at("R21", BLOCK["ux"] + 5.8, BLOCK["uy"] + 2.4, 0)
at("J1", 48.6, 32.6, 0)
at("FID1", 23.6, 44.6, 0)
at("FID2", 50.6, 23.4, 0)
# test pads (front), next to their nets
for ref, (x, y) in {"TP1": (21.3, 14.2), "TP2": (25.0, 22.4), "TP3": (44.9, 22.6), "TP4": (36.0, 23.2),
                    "TP5": (47.7, 22.6), "TP6": (13.75 + DX, 2.4)}.items():
    at(ref, x, y, 0)


# ------------------------------------------------------------------ outline and rule areas
def outline(board):
    """Square top-right corner (module pad 28 is 0.3 mm from both edges there), rounded elsewhere; the tongue
    slot starts at the right edge and ends in a half circle (router bit)."""
    L = pcbnew.Edge_Cuts
    r = CORNER_R
    t = TONGUE
    tx, ty, by, sw = t["tx"], t["ty"], t["by"], t["sw"]
    xs = W - tx - sw                 # left wall of the vertical slot
    ys = H - ty - sw                 # upper wall of the horizontal slot
    path = [((r, 0), (W, 0)),
            ((W, 0), (W, ys)),
            ((W, ys), (xs, ys)),
            ((xs, ys), (xs, H - by - sw / 2)),
            ((xs + sw, H - by - sw / 2), (xs + sw, ys + sw)),
            ((xs + sw, ys + sw), (W, ys + sw)),
            ((W, ys + sw), (W, H - r)),
            ((W - r, H), (r, H)),
            ((0, H - r), (0, r))]
    for a, b in path:
        G.add_line(board, L, a, b)
    G.add_arc(board, L, (xs, H - by - sw / 2), (xs + sw / 2, H - by), (xs + sw, H - by - sw / 2))     # slot end
    G.corner(board, L, W - r, H - r, r, 0)
    G.corner(board, L, r, H - r, r, 90)
    G.corner(board, L, r, r, r, 180)


def outline_polygon():
    r = CORNER_R
    t = TONGUE
    tx, ty, by, sw = t["tx"], t["ty"], t["by"], t["sw"]
    xs, ys = W - tx - sw, H - ty - sw
    pts = [(W, 0), (W, ys), (xs, ys), (xs, H - by), (xs + sw, H - by), (xs + sw, ys + sw), (W, ys + sw)]
    for cx, cy, a0 in ((W - r, H - r, 0), (r, H - r, 90), (r, r, 180)):
        for k in range(0, 91, 15):
            tt = math.radians(a0 + k)
            pts.append((cx + r * math.cos(tt), cy + r * math.sin(tt)))
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
    tb.SetComment(0, "ESP32-H2-WROOM-02C Matter/Thread thermo-hygrometer, 1 x CR123A, TPS63900 3.3 V")
    tb.SetComment(1, "Generated by hardware/scripts/gen_pcb_wroom123.py - 4 layers, 1.6 mm, JLC04161H-7628")

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
    G.rule_area(board, "SHT40_TONGUE", rect(W - t["tx"] - t["sw"], H - t["ty"], W, H), layers=CU4, tracks=False,
                vias=True, pour=True)
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
# SHT40 tongue (tracks only, all on F.Cu): the H2W tongue copper turned by 180 degrees with the tongue (turned()).
# H2W coordinates: lanes through the bridge at 0.5 mm pitch, from the board edge inwards VDD, SCL, SDA, GND; past
# the bridge SDA and SCL run into their pull-ups, VDD into the +3V3 pad of R27 and GND drops to a via.
_BRIDGE_END = TONGUE["tx"] + TONGUE["sw"] + 0.5
_H2W_TONGUE = [
    ("+3V3", SIGNAL_W, [("U5", "3"), (2.1, 2.0), ("C29", "1")]),
    ("+3V3", SIGNAL_W, [("C29", "1"), (1.4, 0.55), (_BRIDGE_END, 0.55)]),
    ("I2C_SCL", SIGNAL_W, [("U5", "2"), (4.8, 2.0), (4.8, 1.05), (_BRIDGE_END, 1.05)]),
    ("I2C_SDA", SIGNAL_W, [("U5", "1"), (5.3, 2.8), (5.3, 1.55), (_BRIDGE_END, 1.55)]),
    ("GND", SIGNAL_W, [("U5", "4"), (2.1, 2.8), ("C29", "2")]),
    ("GND", SIGNAL_W, [("C29", "2"), (1.4, 4.6), (6.1, 4.6), (6.1, 2.05), (_BRIDGE_END + 0.1, 2.05),
                       (_BRIDGE_END + 0.1, 2.7)]),
    ("I2C_SDA", SIGNAL_W, [(_BRIDGE_END, 1.55), (8.6, 1.55), (10.2, 3.15), ("R26", "2")]),
    ("I2C_SCL", SIGNAL_W, [(_BRIDGE_END, 1.05), (10.9, 1.05), (11.7, 1.85), ("R27", "2")]),
    ("+3V3", SIGNAL_W, [(_BRIDGE_END, 0.55), (12.1, 0.55), (12.6, 1.05), (12.6, 4.825), ("R27", "1")]),
]
TONGUE_ROUTES = [(net, w, [q if isinstance(q[0], str) else turned(*q) for q in pts]) for net, w, pts in _H2W_TONGUE]
TONGUE_VIAS = [("GND", turned(_BRIDGE_END + 0.1, 2.7))]

# module thermal pad: the datasheet's via pattern (3 in the 2.8 x 0.55 strip, the 4 corners of the 2.8 x 1.6 area;
# the centre of that area is the 0.8 mm hand-soldering hole of the footprint)
EPAD_VIAS = [(round(MOD[0] - 0.47 + dx, 4), round(MOD[1] + 2.01, 4)) for dx in (-1.05, 0.0, 1.05)] + \
            [(round(MOD[0] - 0.47 + dx, 4), round(MOD[1] + 3.73 + dy, 4)) for dx in (-1.05, 1.05) for dy in (-0.5, 0.5)]
# module escapes: pin 1 (+3V3) to C24 and a via inside the pad ring, pin 14 to C23, the UART/USB pins of the
# right column (no room right of them: board edge) inwards to a column of vias
MOD_VIA_X1, MOD_VIA_X2 = round(MOD[0] - 7.35, 4), round(MOD[0] + 7.1, 4)
MOD_ROUTES = [
    ("+3V3", POWER_W, [("U4", "1"), ("C24", "1")]),
    ("+3V3", POWER_W, [("U4", "1"), (MOD_VIA_X1, 1.1)]),
    ("+3V3", POWER_W, [("U4", "14"), ("C23", "1")]),
] + [(net, SIGNAL_W, [("U4", pin), (MOD_VIA_X2, round(MOD[1] - 2.9 + 1.5 * (28 - int(pin)), 4))])
     for pin, net in (("21", "U0RXD"), ("22", "U0TXD"), ("23", "USB_DM"), ("24", "USB_DP"))]
MOD_VIAS = [("+3V3", (MOD_VIA_X1, 1.1))] + [(net, (MOD_VIA_X2, round(MOD[1] - 2.9 + 1.5 * (28 - int(pin)), 4)))
                                       for pin, net in (("21", "U0RXD"), ("22", "U0TXD"), ("23", "USB_DM"),
                                                        ("24", "USB_DP"))]


def hand_copper(board, nets):
    def point(p):
        return G.pad_xy(board, *p) if isinstance(p[0], str) else p

    for net, w, pts in TONGUE_ROUTES:
        ps = [point(p) for p in pts]
        for a, c in zip(ps[:-1], ps[1:]):
            G.add_track(board, nets[net], a, c, w)
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


# ------------------------------------------------------------------ routing
ROUTE_PLAN = [
    # (net, width, layer costs F.Cu / In2.Cu, small vias)
    ("XTAL_32K_P", SIGNAL_W, (1.0, 50.0), True),
    ("XTAL_32K_N", SIGNAL_W, (1.0, 50.0), True),
    # the short connections at the module pins first: the long I2C lines must not close them in
    ("STRAP_GPIO8", SIGNAL_W, (1.0, 2.0), True),
    ("VBAT_SENSE", SIGNAL_W, (1.0, 2.0), True),
    ("LED", SIGNAL_W, (1.0, 2.0), True),
    ("LED_A", SIGNAL_W, (1.0, 2.0), True),
    ("U0TXD", SIGNAL_W, (2.0, 1.0), True),
    ("U0RXD", SIGNAL_W, (2.0, 1.0), True),
    ("USB_DP", SIGNAL_W, (2.0, 1.0), True),
    ("USB_DM", SIGNAL_W, (2.0, 1.0), True),
    ("BTN_USER", SIGNAL_W, (1.0, 1.5), True),
    ("VBAT_MEAS_EN", SIGNAL_W, (1.0, 1.5), True),
    ("EN", SIGNAL_W, (1.5, 1.0), True),
    ("nRST", SIGNAL_W, (1.0, 1.5), True),
    ("SNS_LO", SIGNAL_W, (1.0, 2.0), True),
    ("I2C_SDA", SIGNAL_W, (1.0, 1.5), True),
    ("I2C_SCL", SIGNAL_W, (1.0, 1.5), True),
    ("VCELL", 0.5, (1.0, 2.0), False),       # holder + pin to the fuse
    ("VIN", POWER_W, (1.0, 2.0), False),
    ("VOUT", POWER_W, (1.0, 2.0), False),
    ("VBAT", POWER_W, (1.5, 1.0), False),
    ("+3V3", POWER_W, (1.5, 1.0), False),
]
ROUTE_LAYERS = (pcbnew.F_Cu, pcbnew.In2_Cu)


def router_keepouts(R):
    t = TONGUE
    # the tongue carries only its four hand-routed tracks
    R.keepout_polygon(rect(W - t["tx"] - t["sw"], H - t["ty"] - t["sw"], W, H), layers=(0, 1), tracks=True,
                      vias=True)
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
        # a track counts when it passes through the via centre, not only when it ends there: the router may
        # land a via in the middle of a hand-routed segment
        layers = {t.GetLayer() for t in tracks.get(v.GetNetCode(), []) if t.HitTest(q)}
        layers |= {L for p in pads.get(v.GetNetCode(), []) for L in (pcbnew.F_Cu, pcbnew.B_Cu)
                   if p.IsOnLayer(L) and p.HitTest(q)}
        if len(layers) < 2:
            board.Remove(v)
            removed += 1
    return removed


def stitch(board, R):
    """GND vias: a row along the top edge under the module (HDG: dense ground vias near the antenna), then a
    2.5 mm grid."""
    sites = [(x, 0.7) for x in [round(MOD[0] - 7.2 + 1.0 * k, 4) for k in range(15)]]
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
SILK_LABELS = (("USER/BOOT", "SW1", (33.0, 41.6, 39.0, 43.4), (0,)),
               ("CR123A ONLY", "BT1", (19.6, 16.0, 20.6, 34.0), (90,)),
               ("NO CHARGE", "BT1", (21.0, 30.0, 22.4, 42.0), (90,)),
               # cell polarity beside the holder's ends (the marks inside the holder outline end up under it)
               ("+", "BT1", (19.5, 5.6, 20.4, 12.0), (0,)),
               ("-", "BT1", (19.6, 42.0, 22.0, 46.2), (0,)))


def silkscreen(board):
    sp = G.SilkPlacer(board)
    t = TONGUE
    tx, ty, by, sw = t["tx"], t["ty"], t["by"], t["sw"]
    sp.cuts = [(W - tx - sw, H - ty - sw, W, H - ty), (W - tx - sw, H - ty - sw, W - tx, H - by)]
    hidden, missing = [], []
    order = sorted(board.GetFootprints(), key=lambda f: -f.GetCourtyard(pcbnew.F_CrtYd).Area()
                   if f.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else 0)

    def txt(text, size=1.0, bold=False, layer="F.SilkS"):
        return G.silk_text(board, text, 0, 0, size, bold=bold, layer=layer)

    for label, ref, region, angles in SILK_LABELS:
        tl = txt(label, 1.2, bold=True) if label in "+-" else txt(label, 0.8)
        if not sp.free_spot(tl, region, step=0.1, angles=angles):
            missing.append(label)
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
    # back: product name (user's text), cell warning, board name and date; "SHT40" on the back of the tongue
    bx = 30.0
    for text, y, size, bold in (("Matter temperature Sensor", 17.0, 1.2, False), ("Villa Nest", 20.2, 1.8, True),
                                ("Made in Vietnam", 23.2, 1.2, False), ("CR123A ONLY", 29.0, 1.0, True),
                                ("NO CHARGE", 31.0, 1.0, True), ("H2W-123 Rev %s" % D.REV, 36.0, 0.8, False),
                                (D.DATE, 37.6, 0.8, False)):
        G.silk_text(board, text, bx, y, size, layer="B.SilkS", bold=bold)
    G.silk_text(board, "SHT40", W - 3.3, H - 2.7, 0.8, layer="B.SilkS")
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
