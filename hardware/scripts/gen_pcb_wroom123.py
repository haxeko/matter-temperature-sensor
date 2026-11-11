#!/usr/bin/env python3
"""
Build hardware/wroom123/kicad/th_sensor_h2w123.kicad_pcb: TH-SENSOR-H2W-123 Rev A, the ESP32-H2-WROOM-02C board
for one CR123A cell that sits BESIDE the board (docs/cr123a_variant.md).

User, 2026-11-11 (second request, marked on the layout drawing): the PCB covers the electronics only, as small as
possible; the SHT40 and the button stay on the bottom edge. The cell is therefore not on the board: BT1 is two
wire pads on the left edge, the side the cell is on. The module stays in the top-right corner with its antenna
overhanging the top edge (ESP32-H2 Hardware Design Guidelines, "Positioning a Module on a Base Board", feed point
on the right: position 3), the SHT40 tongue is the bottom-left corner and the side-push button is on the bottom
edge right of it.

Size: 24.8 x 37.3 mm, 43.3 mm high with the 6 mm antenna overhang. Next to a CR123A holder of 18.2 x 43.3 mm
(e.g. MYOUNG BH-123A-A1CJ002, drawing MY-CP-0398) and a 0.3 mm gap the whole device is 43.3 x 43.3 mm. The width
is set by the converter row (23.1 mm of courtyards: reverse-polarity FET, input capacitors, TPS63900, rail
capacitors) and by that square; the height is the module, the crystal row, the converter row and the tongue.

Mounting: on a wall, back to the wall, antenna up, sensor and button down.

All parts are on the front. The debug pads J1 and the test pads are bare pads on the BACK (nothing is fitted
there). Stack-up JLC04161H-7628 (4 layers, 1.6 mm):
  L1 F.Cu    parts, routing, GND pour
  L2 In1.Cu  GND plane, no tracks
  L3 In2.Cu  GND plane, no tracks
  L4 B.Cu    routing, J1 and test pads, GND pour
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
W = 24.8                         # see the size note above
H = 37.3                         # 43.3 with the antenna overhang: the length of a CR123A holder
# gen_pcb's helpers read these module globals
G.KDIR, G.SCH, G.PCB, G.PROJ_FP = KDIR, SCH, PCB, os.path.join(KDIR, "lib", "th_sensor.pretty")
G.W, G.H = W, H
V, mm = G.V, G.mm
CU4 = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")
SIGNAL_W, POWER_W = 0.25, 0.4
VIA_S = (0.45, 0.2)              # JLC multilayer: 0.2 mm hole, 0.45 mm pad, no surcharge
CORNER_R = 1.5

# ------------------------------------------------------------------ module, sensor tongue
MOD = (W - 0.8 - 9.0, 4.0)       # module centre (15.0, 4): body x 6..24, y -6..14; antenna y -6..0 (off board)
DX = MOD[0] - 27.8               # shift of everything placed against the module, relative to the H2W board
COL = round(16.55 + DX, 4)       # x of the 0603 column at the module's left pins (3.75)
# SHT40 tongue in the bottom-left corner: x 0..TX, y H-TY..H. A 1 mm slot runs in from the left edge above the
# tongue and turns down along its right side; it stops BY above the bottom edge, which leaves the bridge
# (x TX..TX+1, y H-BY..H) as the only connection to the board. The H2W tongue mirrored top to bottom.
TONGUE = dict(tx=6.6, ty=5.4, by=2.6, sw=1.0)

PLACE = {}


def at(ref, x, y, rot=0, back=False):
    PLACE[ref] = (round(x, 4), round(y, 4), rot, back)


def low(x, y):
    """H2W tongue coordinates (top-left corner, y from the top edge) -> this board (y from the bottom edge)."""
    return (round(x, 4), round(H - y, 4))


at("U4", *MOD, 0)
# cell wires: + (pad 1, square) below, - above; the fuse right beside the + pad
at("BT1", 1.5, 21.0, 180)
at("F1", 6.3, 21.85, 0)                 # pad 1 (VCELL) towards the + pad; room for the "+" mark between them
# tongue: SHT40 with SDA/SCL facing the bridge, C29 on the far side between VDD and GND
at("U5", *low(3.4, 2.4), 180)
at("C29", *low(1.4, 2.4), 270)          # pad 1 (+3V3) up, pad 2 (GND) at the bottom edge
at("R27", 9.0, 33.3, 270)               # I2C pull-ups past the bridge: pad 1 (+3V3) up, signal down
at("R26", 10.6, 33.3, 270)
# column at the module's left pins: the part pad that belongs to the pin faces it
at("C24", COL, 1.1, 180)                # pad 1 (+3V3) next to pin 1
at("C25", COL, 2.65, 180)               # pad 1 (EN) next to pin 2
# sense divider around its hold capacitor: the three VBAT_SENSE pads are in one line next to pin 4, so the
# high-impedance node is 3 mm long; pins 5/6 (I2C) leave through vias under the module instead of this column
at("R32", COL, 4.225, 180)              # pad 1 (VBAT_SENSE) on the module side, pad 2 (SNS_LO) outside
at("C31", COL, 5.8, 180)                # pad 1 (VBAT_SENSE) next to pin 4
at("R31", COL, 7.375, 0)                # pad 2 (VBAT_SENSE) on the module side, pad 1 (VBAT) outside
at("R24", COL, 10.1, 0)                 # pad 2 (STRAP_GPIO8) next to pin 7
at("R23", COL, 11.65, 0)                # pad 2 (BTN_USER) next to pin 8
at("R35", COL, 13.3, 180)               # pad 1 (VBAT_MEAS_EN) towards pin 10
at("Q3", 5.4, 16.8, 180)                # sense switch: drain (pad 3) on the left, gate bottom right
# under the module: 32.768 kHz crystal at pins 11/12, LED at pin 15 (as on H2W), supervisor right of them
at("Y1", 23.3 + DX, 16.4, 180)          # pad 1 (XTAL_32K_P) left, under pin 11; pad 2 under pin 12
at("C27", 21.3 + DX, 19.1, 270)         # load caps beyond the crystal, signal pad up
at("C28", 25.3 + DX, 19.1, 270)
at("C23", 27.05 + DX, 16.3, 270)        # 10 uF at pin 14 (VBAT, tied to 3V3 in the module), pad 1 up
at("R25", 28.6 + DX, 16.4, 90)
at("D3", 28.6 + DX, 19.4, 90)
at("U3", 18.9, 16.75, 0)
at("C26", 22.0, 16.45, 90)
at("R22", 19.0, 19.5, 0)                # pad 1 (nRST) under the supervisor's output, pad 2 (EN) to a via
# converter (Rev A block orientation: input on the left, towards the cell wires)
BLOCK = dict(ux=14.0, uy=25.65)


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
# USER/BOOT: side-push switch on the bottom edge, actuator 0.5 mm over the edge (pads 0.35 mm inside)
at("SW1", W - 7.4, H - 1.6, 0)
at("FID1", 22.6, 33.0, 0)
at("FID2", 23.3, 19.25, 0)
# back: debug pads under the module, next to the vias of the UART/USB pins (rows as seen in board coordinates:
# TX RX / D+ D- / BOOT GND from y = 11.04 upwards), and the test pads in one row
at("J1", 18.13, 11.04, 180, back=True)
for ref, (x, y) in {"TP1": (3.5, 25.5), "TP2": (8.0, 25.5), "TP3": (17.0, 25.5), "TP4": (21.5, 25.5),
                    "TP5": (12.5, 25.5), "TP6": (10.0, 3.0)}.items():
    at(ref, x, y, 0, back=True)


# ------------------------------------------------------------------ outline and rule areas
def outline(board):
    """Square top-right corner (module pad 28 is 0.3 mm from both edges there), rounded elsewhere; the tongue
    slot starts at the left edge and ends in a half circle (router bit)."""
    L = pcbnew.Edge_Cuts
    r = CORNER_R
    t = TONGUE
    tx, ty, by, sw = t["tx"], t["ty"], t["by"], t["sw"]
    ys = H - ty - sw                 # upper wall of the horizontal slot
    path = [((r, 0), (W, 0)),
            ((W, 0), (W, H - r)),
            ((W - r, H), (r, H)),
            ((0, H - r), (0, ys + sw)),
            ((0, ys + sw), (tx, ys + sw)),
            ((tx, ys + sw), (tx, H - by - sw / 2)),
            ((tx + sw, H - by - sw / 2), (tx + sw, ys)),
            ((tx + sw, ys), (0, ys)),
            ((0, ys), (0, r))]
    for a, b in path:
        G.add_line(board, L, a, b)
    G.add_arc(board, L, (tx, H - by - sw / 2), (tx + sw / 2, H - by), (tx + sw, H - by - sw / 2))     # slot end
    G.corner(board, L, W - r, H - r, r, 0)
    G.corner(board, L, r, H - r, r, 90)
    G.corner(board, L, r, r, r, 180)


def outline_polygon():
    r = CORNER_R
    t = TONGUE
    tx, ty, by, sw = t["tx"], t["ty"], t["by"], t["sw"]
    ys = H - ty - sw
    pts = [(W, 0)]

    def arc(cx, cy, a0):
        for k in range(0, 91, 15):
            tt = math.radians(a0 + k)
            pts.append((cx + r * math.cos(tt), cy + r * math.sin(tt)))

    arc(W - r, H - r, 0)
    arc(r, H - r, 90)
    pts.extend([(0, ys + sw), (tx, ys + sw), (tx, H - by), (tx + sw, H - by), (tx + sw, ys), (0, ys)])
    arc(r, r, 180)
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
    tb.SetComment(0, "ESP32-H2-WROOM-02C Matter/Thread thermo-hygrometer, 1 x CR123A beside the board, TPS63900 3.3 V")
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
    G.rule_area(board, "SHT40_TONGUE", rect(0, H - t["ty"], t["tx"] + t["sw"], H), layers=CU4, tracks=False,
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
# SHT40 tongue (tracks only, all on F.Cu): the H2W tongue copper mirrored top to bottom (low()). A mirror image
# swaps the two pads on each side of the SHT40, so the nets swap with it. Lanes through the bridge at 0.5 mm pitch,
# from the board edge inwards: GND, SDA, SCL, +3V3. Past the bridge SCL and SDA turn up into their pull-ups, +3V3
# runs up to the pull-ups' other pads and GND goes on along the edge to a via.
_BRIDGE_END = TONGUE["tx"] + TONGUE["sw"] + 0.5
_GND_VIA_X = 12.0
_TONGUE = [
    ("GND", SIGNAL_W, [("U5", "4"), (2.1, 2.0), ("C29", "2")]),
    ("GND", SIGNAL_W, [("C29", "2"), (1.4, 0.55), (_GND_VIA_X, 0.55)]),
    ("I2C_SDA", SIGNAL_W, [("U5", "1"), (4.8, 2.0), (4.8, 1.05), (10.6, 1.05), ("R26", "2")]),
    ("I2C_SCL", SIGNAL_W, [("U5", "2"), (5.3, 2.8), (5.3, 1.55), (9.0, 1.55), ("R27", "2")]),
    ("+3V3", SIGNAL_W, [("U5", "3"), (2.1, 2.8), ("C29", "1")]),
    ("+3V3", SIGNAL_W, [("C29", "1"), (1.4, 4.6), (6.1, 4.6), (6.1, 2.05), (_BRIDGE_END, 2.05), (_BRIDGE_END, 4.825),
                        ("R27", "1"), ("R26", "1")]),
]
TONGUE_ROUTES = [(net, w, [q if isinstance(q[0], str) else low(*q) for q in pts]) for net, w, pts in _TONGUE]
# SCL and SDA change to the back on the way up to their pull-ups
I2C_VIAS = {"I2C_SCL": low(9.0, 2.1), "I2C_SDA": low(10.6, 2.0)}
TONGUE_VIAS = [("GND", low(_GND_VIA_X, 0.55))] + sorted(I2C_VIAS.items())

# module thermal pad: the datasheet's via pattern (3 in the 2.8 x 0.55 strip, the 4 corners of the 2.8 x 1.6 area;
# the centre of that area is the 0.8 mm hand-soldering hole of the footprint)
EPAD_VIAS = [(round(MOD[0] - 0.47 + dx, 4), round(MOD[1] + 2.01, 4)) for dx in (-1.05, 0.0, 1.05)] + \
            [(round(MOD[0] - 0.47 + dx, 4), round(MOD[1] + 3.73 + dy, 4)) for dx in (-1.05, 1.05) for dy in (-0.5, 0.5)]
# module escapes: pin 1 (+3V3) to C24 and a via inside the pad ring, pin 14 to C23; the I2C and button pins (the
# column of parts is in front of them) and the UART/USB pins of the right column (board edge) inwards to vias, from where
# they run on the back
MOD_VIA_X1, MOD_VIA_X2 = round(MOD[0] - 7.35, 4), round(MOD[0] + 7.1, 4)
LEFT_ESCAPES = (("5", "I2C_SDA"), ("6", "I2C_SCL"), ("8", "BTN_USER"))     # pins that continue on the back
MOD_ROUTES = [
    ("+3V3", POWER_W, [("U4", "1"), ("C24", "1")]),
    ("+3V3", POWER_W, [("U4", "1"), (MOD_VIA_X1, 1.1)]),
    ("+3V3", POWER_W, [("U4", "14"), ("C23", "1")]),
] + [(net, SIGNAL_W, [("U4", pin), (MOD_VIA_X2, round(MOD[1] - 2.9 + 1.5 * (28 - int(pin)), 4))])
     for pin, net in (("21", "U0RXD"), ("22", "U0TXD"), ("23", "USB_DM"), ("24", "USB_DP"))] + \
    [(net, SIGNAL_W, [("U4", pin), (MOD_VIA_X1, round(MOD[1] - 4.4 + 1.5 * int(pin), 4))])
     for pin, net in LEFT_ESCAPES]
MOD_VIAS = [("+3V3", (MOD_VIA_X1, 1.1))] + \
    [(net, (MOD_VIA_X2, round(MOD[1] - 2.9 + 1.5 * (28 - int(pin)), 4)))
     for pin, net in (("21", "U0RXD"), ("22", "U0TXD"), ("23", "USB_DM"), ("24", "USB_DP"))] + \
    [(net, (MOD_VIA_X1, round(MOD[1] - 4.4 + 1.5 * int(pin), 4))) for pin, net in LEFT_ESCAPES]


# Long lines on the back, laid out so that none has to cross another (the two inner layers are ground planes, so
# the front under the module cannot help): the I2C lines leave the module westwards and run down the left side to
# the pull-ups, SCL outside; the button line runs east to its debug pad (J1 pin 5, BOOT) below the thermal-pad
# vias. EN, the supply and everything else are left to the router, around these.
_ESC = {net: (MOD_VIA_X1, round(MOD[1] - 4.4 + 1.5 * int(pin), 4)) for pin, net in LEFT_ESCAPES}
BACK_ROUTES = [
    ("I2C_SCL", SIGNAL_W, [_ESC["I2C_SCL"], (4.9, _ESC["I2C_SCL"][1]), (4.9, 30.2), (9.0, 30.2), I2C_VIAS["I2C_SCL"]]),
    ("I2C_SDA", SIGNAL_W, [_ESC["I2C_SDA"], (8.5, 7.95), (8.5, 9.3), (7.9, 9.9), (5.4, 9.9), (5.4, 29.7), (10.6, 29.7),
                           I2C_VIAS["I2C_SDA"]]),
    ("BTN_USER", SIGNAL_W, [_ESC["BTN_USER"], (11.0, 11.6), (13.6, 9.0), (16.4, 9.0), (16.4, 6.4), (16.84, 5.96),
                            ("J1", "5")]),
]


def hand_copper(board, nets):
    def point(p):
        return G.pad_xy(board, *p) if isinstance(p[0], str) else p

    for net, w, pts in BACK_ROUTES:
        ps = [point(q) for q in pts]
        for a, c in zip(ps[:-1], ps[1:]):
            G.add_track(board, nets[net], a, c, w, layer=pcbnew.B_Cu)

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
    # (net, width, layer costs F.Cu / B.Cu, small vias)
    ("XTAL_32K_P", SIGNAL_W, (1.0, 50.0), True),
    ("XTAL_32K_N", SIGNAL_W, (1.0, 50.0), True),
    ("VCELL", 0.5, (1.0, 5.0), False),       # + wire pad to the fuse
    # the short connections at the module pins first: the long lines must not close them in
    ("EN", SIGNAL_W, (1.0, 1.5), True),
    ("STRAP_GPIO8", SIGNAL_W, (1.0, 2.0), True),
    ("VBAT_SENSE", SIGNAL_W, (1.0, 1.5), True),
    ("VBAT_MEAS_EN", SIGNAL_W, (1.0, 1.5), True),
    ("SNS_LO", SIGNAL_W, (1.0, 1.5), True),
    ("LED", SIGNAL_W, (1.0, 2.0), True),
    ("LED_A", SIGNAL_W, (1.0, 2.0), True),
    ("U0TXD", SIGNAL_W, (2.0, 1.0), True),
    ("U0RXD", SIGNAL_W, (2.0, 1.0), True),
    ("USB_DP", SIGNAL_W, (2.0, 1.0), True),
    ("USB_DM", SIGNAL_W, (2.0, 1.0), True),
    ("VIN", POWER_W, (1.0, 1.5), False),
    ("VOUT", POWER_W, (1.0, 1.5), False),
    ("VBAT", POWER_W, (1.0, 1.0), False),
    ("+3V3", POWER_W, (1.0, 1.0), False),
    ("nRST", SIGNAL_W, (1.0, 1.0), True),
    ("BTN_USER", SIGNAL_W, (1.0, 1.0), True),
    ("I2C_SDA", SIGNAL_W, (1.0, 1.0), True),      # hand-routed: nothing left unless that changes
    ("I2C_SCL", SIGNAL_W, (1.0, 1.0), True),
]


def router_keepouts(R):
    t = TONGUE
    # the tongue carries only its four hand-routed tracks
    R.keepout_polygon(rect(0, H - t["ty"] - t["sw"], t["tx"] + t["sw"], H), layers=(0, 1), tracks=True, vias=True)
    # module underside on F.Cu: only escapes within 1 mm of the pad ring (vias allowed there)
    x0, x1 = MOD[0] - 9.0 + 2.0, MOD[0] + 9.0 - 2.0
    R.keepout_polygon(rect(x0, 0.0, x1, MOD[1] + 10.0 - 2.1), layers=(0,), tracks=True, vias=False)
    # 32.768 kHz crystal: nothing under it on the front, no vias (HDG crystal guidelines); the back is behind
    # two ground planes
    x, y = PLACE["Y1"][:2]
    R.keepout_polygon(rect(x - 1.0, y - 0.9, x + 1.0, y + 0.9), layers=(0,), tracks=True, vias=True)
    for ref in ("FID1", "FID2"):
        fx, fy = PLACE[ref][:2]
        R.keepout_polygon(G.circle_pts(fx, fy, 1.35, 24), layers=(0,), tracks=True, vias=True)


def route(board, nets):
    import router as RT
    R = RT.Router(board, OX, OY, W, H, grid=0.1, clearance=0.2, edge_clearance=0.3,
                  classes={"w25": 0.125, "w30": 0.15, "w40": 0.20, "w50": 0.25, "via": 0.30})
    R.build()
    router_keepouts(R)
    R.block_vias_in_smd_pads(0.6)
    # GND pads that get their own via; the bare pads on the back (J1, TP5) join the B.Cu pour instead
    skip = {"J1", "BT1", "TP5", G.BLOCK_REFS["U"]}
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
SILK_LABELS = (("USER/BOOT", None, (13.0, 31.6, 21.0, 33.6)),)
# back: one label per bare pad. J1 pads in board coordinates (the back view is the mirror image).
J1_NAMES = {"1": "TX", "2": "RX", "3": "D+", "4": "D-", "5": "BOOT", "6": "GND"}


def text_width(text, size):
    return 0.9 * size * len(text)


def silkscreen(board):
    sp = G.SilkPlacer(board)
    t = TONGUE
    tx, ty, by, sw = t["tx"], t["ty"], t["by"], t["sw"]
    sp.cuts = [(0, H - ty - sw, tx + sw, H - ty), (tx, H - ty - sw, tx + sw, H - by)]
    hidden, missing = [], []
    order = sorted(board.GetFootprints(), key=lambda f: -f.GetCourtyard(pcbnew.F_CrtYd).Area()
                   if f.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else 0)

    def txt(text, size=1.0, bold=False, layer="F.SilkS"):
        return G.silk_text(board, text, 0, 0, size, bold=bold, layer=layer)

    # polarity of the cell wires beside the two holes, drawn as lines (a text box would not fit between the
    # + hole and the fuse); repeated on the back
    bt = board.FindFootprintByReference("BT1")
    for pd in bt.Pads():
        q = pd.GetPosition()
        mx, my = pcbnew.ToMM(q.x) - OX + 1.85, pcbnew.ToMM(q.y) - OY
        G.add_line(board, pcbnew.F_SilkS, (mx - 0.45, my), (mx + 0.45, my), 0.15)
        if pd.GetNumber() == "1":
            G.add_line(board, pcbnew.F_SilkS, (mx, my - 0.45), (mx, my + 0.45), 0.15)
        sp.obst.append((mx - 0.6, my - 0.6, mx + 0.6, my + 0.6, None))
    for label, owner, (rx1, ry1, rx2, ry2) in SILK_LABELS:
        tl = txt(label, 0.8)
        nx, ny = int(round((rx2 - rx1) / 0.1)) + 1, int(round((ry2 - ry1) / 0.1)) + 1
        cands = [(rx1 + 0.1 * i, ry1 + 0.1 * k, 0) for k in range(ny) for i in range(nx)]
        if not sp.place_text(tl, cands, owner=owner):
            missing.append(label)
    # the current-measurement links first: the bring-up procedure refers to them by name
    for ref in ("R1", "R21"):
        if not sp.place_reference(board.FindFootprintByReference(ref)):
            missing.append(ref)
    for fp in order:
        ref = fp.GetReference()
        if ref in ("R1", "R21"):
            continue
        if fp.IsFlipped() or ref in ("U4", "BT1") or not sp.place_reference(fp):
            fp.Reference().SetVisible(False)
            hidden.append(ref)

    # ---- back: pad names, product name (user's text), cell warning, board name and date
    def back(text, x, y, size=0.8, bold=False):
        return G.silk_text(board, text, x, y, size, layer="B.SilkS", bold=bold)

    j1 = board.FindFootprintByReference("J1")
    xs = sorted({round(pcbnew.ToMM(pd.GetPosition().x) - OX, 3) for pd in j1.Pads()})
    for pd in j1.Pads():
        q = pd.GetPosition()
        x, y = pcbnew.ToMM(q.x) - OX, pcbnew.ToMM(q.y) - OY
        name = J1_NAMES[pd.GetNumber()]
        side = -1 if abs(x - xs[0]) < 0.01 else 1          # label on the outer side of its column
        back(name, x + side * (1.15 + text_width(name, 0.8) / 2), y)
    for fp in board.GetFootprints():
        if fp.GetReference().startswith("TP"):
            q = fp.GetPosition()
            back(fp.GetValue(), pcbnew.ToMM(q.x) - OX, pcbnew.ToMM(q.y) - OY + 1.75)
    for pd in bt.Pads():
        q = pd.GetPosition()
        back("+" if pd.GetNumber() == "1" else "-", pcbnew.ToMM(q.x) - OX + 1.9, pcbnew.ToMM(q.y) - OY, 1.2, True)
    cx = W / 2
    for text, y, size, bold in (("Matter temperature Sensor", 16.3, 0.9, False), ("Villa Nest", 18.9, 1.8, True),
                                ("Made in Vietnam", 21.6, 1.0, False), ("CR123A 3V ONLY", 30.2, 1.0, True),
                                ("NO CHARGE", 32.0, 1.0, True), ("H2W-123 Rev %s" % D.REV, 34.3, 0.8, False),
                                (D.DATE, 35.7, 0.8, False)):
        back(text, cx + (2.5 if y > 29 else 0.6), y, size, bold)
    back("SHT40", 3.3, H - 2.7)
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
