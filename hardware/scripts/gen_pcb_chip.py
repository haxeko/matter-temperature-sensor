#!/usr/bin/env python3
"""
Build hardware/chip/kicad/th_sensor_h2c.kicad_pcb: TH-SENSOR-H2C Rev A, the bare-chip variant of the
TH-SENSOR-H2 board (docs/chip_variant.md).

Same outline (41.5 x 57.5 mm), power section, CR2450 holder and SHT40 tongue as Rev B (gen_pcb.py); the
module is replaced by an ESP32-H2FH4S (QFN32 4 x 4 mm), its 32 MHz crystal and decoupling, the RF matching
network and a printed inverted-F antenna (TI DN007, drawn as its mirror image) along the top edge.

Stack-up (ESP32-H2 Hardware Design Guidelines v1.6, "General Principles of PCB Layout for the Chip"),
JLCPCB JLC04161H-7628:
  L1 F.Cu    parts, signals, 50-ohm RF line, GND pour
  L2 In1.Cu  GND plane, no tracks (reference of the RF line; cleared under the HDG stub only)
  L3 In2.Cu  GND plane, no tracks (reference of the stub), with a +3V3 island under the chip that ties the
             decoupling groups together through vias (HDG: power on layer 3, ground under RF and crystals)
  L4 B.Cu    signals, GND pour; no parts
Coordinates are relative to the board's top-left corner (KiCad y down), as in gen_pcb.py. The fixed copper
(RF line and stub, QFN escapes, decoupling, crystals) is drawn here; router.py routes the rest.

Usage: TH_VARIANT=chip python3 gen_pcb_chip.py [--no-route] [--silk-draft]
       --silk-draft: report texts that find no room instead of stopping (layout work only)
"""
import math
import os
import subprocess
import sys

if os.environ.get("TH_VARIANT", "chip") != "chip":
    raise SystemExit("gen_pcb_chip.py builds the chip variant: run it with TH_VARIANT=chip")
os.environ["TH_VARIANT"] = "chip"

import pcbnew  # noqa: E402

import design as D  # noqa: E402
import gen_pcb as G  # noqa: E402  (helpers; its module-level placement is for Rev B and is not used here)

HERE = os.path.dirname(os.path.abspath(__file__))
KDIR = os.path.join(D.HW_DIR, "kicad")
PCB = os.path.join(KDIR, D.PROJECT + ".kicad_pcb")
SCH = os.path.join(KDIR, D.PROJECT + ".kicad_sch")
REPORTS = os.path.join(D.HW_DIR, "reports")
# gen_pcb's helpers read these module globals
G.KDIR, G.SCH, G.PCB, G.PROJ_FP = KDIR, SCH, PCB, os.path.join(KDIR, "lib", "th_sensor.pretty")

OX, OY, W, H = G.OX, G.OY, G.W, G.H
V, mm = G.V, G.mm
CU4 = ("F.Cu", "In1.Cu", "In2.Cu", "B.Cu")
SIGNAL_W, POWER_W = 0.25, 0.4
RF_W = 0.35                      # 50 ohm on L1 over the L2 ground (JLC04161H-7628, docs/chip_variant.md)
STUB_W, STUB_L = 0.5, 0.381      # HDG stub: 15 mil long, 100 ohm over L3 (L2 cleared under it)
VIA_S = (0.45, 0.2)              # small vias near the chip (JLC: 0.2 mm hole, 0.45 mm pad, no surcharge)

# ------------------------------------------------------------------ outline
GE = 7.52                        # ground-plane edge = antenna feed line; no copper on any layer above it
SLOT_X1, SLOT_W = 31.8, 1.0      # tongue slot from the top edge down to the slot under the tongue (as Rev B)
TONGUE = dict(x1=SLOT_X1 + SLOT_W, y2=12.0, bridge_x1=W - 3.4)

# ------------------------------------------------------------------ antenna, chip, RF chain
ANT_X0 = 1.2                     # left (open) end of the antenna
FX = ANT_X0 + 14.72              # feed point (mirrored DN007: feed 14.72 mm from the open end)
CX, CY = FX - 4.15, 16.6         # chip centre; pin 32 (ANT) leaves east at the chip's north-east corner

PLACE = {}


def at(ref, x, y, rot=0):
    PLACE[ref] = (round(x, 4), round(y, 4), rot)


at("AE1", FX, GE, 0)
at("U4", CX, CY, 270)
# RF chain on the vertical part of the line (x = FX), zigzag: C51 east, C52 west, L5 east (HDG "RF")
at("C51", FX + 0.625, 13.4, 0)        # shunt at the chip end, HDG stub on its ground pad (east)
at("L4", FX, 12.25, 90)               # series, pin 1 (chip side) down
at("C52", FX - 0.625, 11.1, 180)      # shunt
at("R41", FX, 9.95, 90)               # series (antenna side match), pin 1 down
at("L5", FX + 0.625, 8.8, 0)          # shunt (not fitted)
# decoupling (HDG v1.6 reference schematic): pins 1/2 north, 30/31 east, 27 east, 18-20 south, 9 west
at("C42", 13.2, 13.15, 0)             # 100 nF pins 1/2
at("C41", 13.0, 11.6, 0)              # 1 uF
at("C40", 13.0, 10.05, 0)             # 10 uF
at("C43", 16.175, 15.6, 0)            # 10 nF pins 30/31
at("C44", 15.5, 19.25, 270)           # 100 nF pin 27
at("C45", 17.1, 19.25, 270)           # 1 uF pin 27
at("C47", 11.145, 20.8, 270)          # 100 nF pins 18/19/20 (all three land on its pad)
at("C46", 9.55, 21.1, 270)            # 100 nF pin 20 (next to C47, west of it)
at("C48", 7.5, 14.75, 180)            # 100 nF pin 9
# 32 MHz crystal east of the chip: series L3 on XTAL_P near the chip, load caps at the far end of each clock trace
at("L3", 19.25, 16.4, 0)
at("Y2", 22.6, 15.6, 270)             # pin 1 XTAL_P top-left, pin 3 XTAL_N bottom-right
at("C49", 22.6, 12.6, 0)              # XTAL_P load above pin 1, ground pad above pin 4
at("C50", 25.25, 15.6, 90)            # XTAL_N load right of pin 3, ground pad right of pin 4
at("R40", 13.1, 21.0, 270)            # U0TXD series, pad 1 up (chip side)
# cell-voltage divider north-west, next to pin 8 (VBAT_SENSE)
at("C31", CX - 1.4, 12.0, 90)         # pad 1 (VBAT_SENSE) down
at("R32", 8.4, 12.0, 90)              # pad 1 (VBAT_SENSE) down
at("R31", 6.8, 12.0, 270)             # pad 2 (VBAT_SENSE) down
at("Q3", 4.0, 10.0, 0)
at("R35", 1.2, 10.0, 270)             # pad 1 (gate) up
# 32.768 kHz crystal west of the chip, load caps beyond its pads
at("Y1", 6.9, 20.6, 90)               # pad 1 (XTAL_32K_P) up
at("C27", 4.15, 19.35, 180)
at("C28", 4.15, 21.85, 180)
# button, pull-ups, LED
at("SW1", 28.9, 12.0, 90)             # right of the antenna's shorted end, BTN pads west
at("R23", 4.3, 13.65, 0)
at("R24", 4.3, 15.25, 0)
at("R25", 16.6, 21.7, 0)
at("D3", 16.6, 23.3, 0)
# debug header (not fitted) south of the chip, away from the antenna (HDG "RF": UART/USB away from it)
at("J1", 9.0, 27.2, 0)
# sensor tongue and pull-ups: as Rev B
for ref in ("U5", "C29", "R26", "R27"):
    PLACE[ref] = G.PLACE[ref]
# power section, supervisor, holder, fiducials: as Rev B
for ref in ("BT1", "R22", "C25", "SW2", "C5", "TP5", "FID1", "FID2"):
    PLACE[ref] = G.PLACE[ref]
for key in G.BLOCK_REFS:
    PLACE[G.BLOCK_REFS[key]] = G.PLACE[G.BLOCK_REFS[key]]
at("TP3", 17.3, 25.6, 0)               # VOUT test pad 0.65 mm left of its Rev B spot: room for its label
at("U3", 3.6, 26.8, 0)
at("C26", 6.4, 27.3, 270)
at("TP6", 5.8, 31.4, 0)
at("C21", 18.2, 30.6, 0)
at("C22", 27.0, 31.0, 0)
at("R21", 18.4, 27.9, 0)              # pad 1 (VOUT) west under TP3, pad 2 (+3V3) east
at("TP4", 32.9, 19.9, 0)


# ------------------------------------------------------------------ outline and rule areas
def outline(board):
    """Rounded corners; the tongue slot runs from the top edge down and turns right under the tongue."""
    L = pcbnew.Edge_Cuts
    r = G.CORNER_R
    t = TONGUE
    xb, y2, sw = t["bridge_x1"], t["y2"], SLOT_W
    path = [((r, 0), (SLOT_X1, 0)),
            ((SLOT_X1, 0), (SLOT_X1, y2 + sw)),
            ((SLOT_X1, y2 + sw), (xb - sw / 2, y2 + sw)),
            ((xb - sw / 2, y2), (t["x1"], y2)),
            ((t["x1"], y2), (t["x1"], 0)),
            ((t["x1"], 0), (W - r, 0))]
    for a, b in path:
        G.add_line(board, L, a, b)
    G.add_arc(board, L, (xb - sw / 2, y2 + sw), (xb, y2 + sw / 2), (xb - sw / 2, y2))
    G.corner(board, L, W - r, r, r, -90)
    G.add_line(board, L, (W, r), (W, H - r))
    G.corner(board, L, W - r, H - r, r, 0)
    G.add_line(board, L, (W - r, H), (r, H))
    G.corner(board, L, r, H - r, r, 90)
    G.add_line(board, L, (0, H - r), (0, r))
    G.corner(board, L, r, r, r, 180)


def outline_polygon():
    """Board polygon for the copper zones (zones are clipped by the edge anyway)."""
    r = G.CORNER_R
    t = TONGUE
    pts = [(r, 0), (SLOT_X1, 0), (SLOT_X1, t["y2"] + SLOT_W), (t["bridge_x1"], t["y2"] + SLOT_W),
           (t["bridge_x1"], t["y2"]), (t["x1"], t["y2"]), (t["x1"], 0)]
    for cx, cy, a0 in ((W - r, r, -90), (W - r, H - r, 0), (r, H - r, 90), (r, r, 180)):
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
    bds.m_TrackMinWidth = mm(0.1)
    bds.m_MinClearance = mm(0.1)
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
    tb.SetComment(0, "ESP32-H2 (bare chip) Matter/Thread thermo-hygrometer, 1 x CR2450, TPS63900 3.3 V")
    tb.SetComment(1, "Generated by hardware/scripts/gen_pcb_chip.py - 4 layers, 1.6 mm, JLC04161H-7628")

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
    # antenna: no copper on any layer between the top edge and the ground-plane edge, up to the tongue slot
    G.rule_area(board, "ANTENNA_KEEPOUT", rect(0, 0, SLOT_X1, GE), layers=CU4)
    t = TONGUE
    G.rule_area(board, "SHT40_TONGUE", rect(t["x1"], 0, W, t["y2"]), layers=CU4, tracks=False, vias=True, pour=True)
    bx, by = G.CELL_BODY
    for ref, (cx, cy) in G.CELLS.items():
        G.rule_area(board, "CELL_" + ref, G.circle_pts(cx, cy, G.CELL_R), layers=("F.Cu",))
        G.rule_area(board, "HOLDER_" + ref, rect(cx - bx, cy - by, cx + bx, cy + by), layers=("F.Cu",))
    return board, nets


# ------------------------------------------------------------------ placement check
def courtyard_overlaps(board):
    fps = list(board.GetFootprints())
    polys = []
    for fp in fps:
        cy = fp.GetCourtyard(pcbnew.F_CrtYd)
        polys.append((fp.GetReference(), cy))
    out = []
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
            if c.OutlineCount() and c.Area() > 1e3:            # > 0.001 mm^2
                out.append((a, b, round(c.Area() / 1e12 * 1e6, 3)))
    return out


# ------------------------------------------------------------------ fixed copper
# chip pins (rot 270): a point 0.1 mm inside the outer end of each pad
def pin_in(n):
    if 1 <= n <= 8:
        return (round(CX + 1.4 - 0.4 * (n - 1), 4), round(CY - 2.25, 4))
    if 9 <= n <= 16:
        return (round(CX - 2.25, 4), round(CY - 1.4 + 0.4 * (n - 9), 4))
    if 17 <= n <= 24:
        return (round(CX - 1.4 + 0.4 * (n - 17), 4), round(CY + 2.25, 4))
    return (round(CX + 2.25, 4), round(CY + 1.4 - 0.4 * (n - 25), 4))


P1 = (CX + 2.55, CY - 1.4)                   # end of the 0.2 mm neck at pin 32
P1b = (CX + 2.85, CY - 1.7)                  # start of the 50-ohm section
P2 = (FX, P1b[1] - (FX - P1b[0]))           # 45-degree run ends on the feed line
C51_PAD2_EDGE = PLACE["C51"][0] + 0.32 + 0.23
STUB_VIA = (round(C51_PAD2_EDGE + STUB_L + VIA_S[0] / 2, 4), PLACE["C51"][1])
EP_VIAS = [(round(CX + i * 0.9, 4), round(CY + j * 0.9, 4)) for j in (-1, 0, 1) for i in (-1, 0, 1)]
# +3V3 vias down to the L3 island (HDG: power on layer 3), one per decoupling group
# GND vias along both sides of the RF line (HDG "RF": dense ground vias around the RF trace); the router keeps
# its own vias out of this area, so they are placed here
RF_GND_VIAS = [(14.85, 8.3), (14.85, 9.2), (14.85, 10.1), (14.85, 12.0), (14.95, 12.9),
               (16.95, 9.9), (16.95, 10.8), (16.95, 11.7), (16.95, 12.55), (15.8, 14.6)]
V3V3 = {"pins30_31": (14.5, 15.8), "C40_42": (11.45, 12.4), "C46_47": (10.35, 20.45), "C44_45": (16.3, 18.475),
        "C48": (8.95, 14.3), "R21": (19.3, 26.6)}

ROUTES = [
    # RF: 0.2 mm neck out of pin 32, 45 degrees, then the 50-ohm line through the matching network to the feed
    ("LNA_IN", 0.2, [pin_in(32), P1, P1b]),
    ("LNA_IN", RF_W, [P1b, P2, ("L4", "1")]),
    ("RF_M", RF_W, [("L4", "2"), ("R41", "1")]),
    ("RF_ANT", RF_W, [("R41", "2"), ("AE1", "1")]),
    # HDG stub on the ground pad of C51: 15 mil from the pad edge to the via, 100 ohm over L3 (L2 cleared)
    ("GND", STUB_W, [("C51", "2"), STUB_VIA]),
    ("GND", 0.3, [("C52", "2"), (14.4, 10.75)]),
    ("GND", 0.3, [("C40", "2"), (14.4, 10.75), ("C41", "2")]),
    ("GND", 0.3, [("L5", "2"), (FX + 1.4, GE + 0.95)]),
    ("GND", 0.3, [("C42", "2"), (14.7, 13.75)]),
    # pins 1/2 -> C42 -> C41/C40, divider at pin 8
    ("+3V3", 0.2, [pin_in(1), (12.82, pin_in(2)[1])]),
    ("+3V3", 0.25, [(12.82, pin_in(2)[1]), (12.82, 13.4)]),
    ("+3V3", 0.4, [("C42", "1"), (12.3, 13.15), (12.3, 10.05)]),
    ("+3V3", 0.3, [V3V3["C40_42"], (12.3, V3V3["C40_42"][1])]),
    ("VBAT_SENSE", 0.2, [pin_in(8), (pin_in(8)[0], 12.9)]),
    ("VBAT_SENSE", 0.25, [("R31", "2"), ("C31", "1")]),
    ("SNS_LO", 0.25, [("R32", "2"), (8.4, 10.35), (5.6, 10.35), (5.3, 10.05)]),
    ("VBAT", 0.3, [(5.85, 11.25), ("R31", "1")]),
    ("VBAT_MEAS_EN", 0.25, [("R35", "1"), ("Q3", "1")]),
    ("GND", 0.3, [("Q3", "2"), (2.0, 11.5)]),
    ("GND", 0.3, [("R35", "2"), (2.0, 11.5)]),
    ("GND", 0.3, [("C31", "2"), (10.37, 10.4)]),
    # pin 9 -> C48; west side: STRAP to R24, then a staircase of vias (lowest trace first)
    ("+3V3", 0.2, [pin_in(9), (8.5, pin_in(9)[1])]),
    ("+3V3", 0.3, [("C48", "1"), V3V3["C48"]]),
    ("GND", 0.3, [("C48", "2"), (6.05, 14.75)]),
    ("STRAP_GPIO8", 0.2, [pin_in(10), (5.3, pin_in(10)[1])]),
    ("BTN_USER", 0.2, [pin_in(11), (5.4, pin_in(11)[1]), (5.4, 16.55)]),
    ("I2C_SDA", 0.2, [pin_in(12), (6.2, pin_in(12)[1]), (6.2, 16.95)]),
    ("I2C_SCL", 0.2, [pin_in(13), (7.0, pin_in(13)[1]), (7.0, 17.35)]),
    ("VBAT_MEAS_EN", 0.2, [pin_in(14), (7.8, pin_in(14)[1]), (7.8, 17.75)]),
    ("+3V3", 0.3, [("R23", "1"), ("R24", "1")]),
    # 32.768 kHz crystal: no vias on the clock traces
    ("XTAL_32K_P", 0.2, [pin_in(15), (8.35, pin_in(15)[1]), (8.35, 19.35), (7.6, 19.35)]),
    ("XTAL_32K_N", 0.2, [pin_in(16), (8.75, pin_in(16)[1]), (8.75, 21.85), (7.6, 21.85)]),
    ("XTAL_32K_P", 0.2, [("C27", "1"), (6.1, 19.35)]),
    ("XTAL_32K_N", 0.2, [("C28", "1"), (6.1, 21.85)]),
    ("GND", 0.3, [("C27", "2"), (2.5, 20.6), ("C28", "2")]),
    # south side: EN down to L4 at once, pins 18-20 on C47 (+ C46 beside it), TXD into R40, LED and RXD out
    ("EN", 0.2, [pin_in(17), (10.2, 19.45)]),
    ("+3V3", 0.2, [pin_in(18), pin_in(20)]),
    ("+3V3", 0.4, [pin_in(19), (pin_in(19)[0], 19.9)]),
    ("+3V3", 0.3, [(9.9, 20.3), (10.9, 20.3)]),
    ("GND", 0.3, [("C46", "2"), (10.35, 22.4), ("C47", "2")]),
    ("U0TXD", 0.2, [pin_in(23), (pin_in(23)[0], 20.1)]),
    ("LED", 0.2, [pin_in(21), (pin_in(21)[0], 22.6), (11.6, 23.0)]),
    ("U0RXD", 0.2, [pin_in(22), (pin_in(22)[0], 23.0)]),
    # east side: pins 30/31 -> C43 (+ via to the L3 island), crystal, pin 27 -> C44/C45, USB out
    ("+3V3", 0.2, [pin_in(31), (15.15, pin_in(31)[1])]),
    ("+3V3", 0.2, [pin_in(30), (15.15, pin_in(30)[1])]),
    ("GND", 0.3, [("C43", "2"), (17.75, 15.1)]),
    ("XTAL_P_IC", 0.2, [pin_in(29), ("L3", "1")]),
    ("XTAL_P", 0.2, [("L3", "2"), (20.2, 16.4), (21.4, 15.2), ("Y2", "1")]),
    ("XTAL_P", 0.2, [("Y2", "1"), (21.8, 12.9), ("C49", "1")]),
    ("XTAL_N", 0.2, [pin_in(28), (15.5, pin_in(28)[1]), (15.95, 17.25), (20.3, 17.25), (20.8, 17.75),
                     (23.45, 17.75), ("Y2", "3")]),
    ("XTAL_N", 0.2, [("Y2", "3"), (23.9, 16.5), ("C50", "1")]),
    ("GND", 0.3, [("Y2", "4"), (24.4, 13.3)]),
    ("GND", 0.3, [("C49", "2"), (24.4, 13.3)]),
    ("GND", 0.3, [("C50", "2"), (24.4, 13.3)]),
    ("GND", 0.3, [(20.9, 16.95), ("Y2", "2")]),
    ("+3V3", 0.2, [pin_in(27), (15.1, pin_in(27)[1]), (15.1, 18.3)]),
    ("+3V3", 0.4, [("C44", "1"), ("C45", "1")]),
    ("GND", 0.3, [("C44", "2"), (16.3, 20.6), ("C45", "2")]),
    # USB as a pair down to J1 (0.2 mm tracks, 0.15 mm gap once clear of the pins: about 90 ohm differential,
    # HDG "USB"): D- ends on J1.4, D+ passes under J1.4 and up between the header columns
    ("USB_DM", 0.2, [pin_in(25), (13.9, pin_in(25)[1]), (13.9, 29.34), (13.5, 29.74), ("J1", "4")]),
    ("USB_DP", 0.2, [pin_in(26), (14.4, pin_in(26)[1]), (14.4, 18.7), (14.25, 18.85), (14.25, 30.3), (13.55, 31.0),
                     (10.27, 31.0), (10.27, 29.74), ("J1", "3")]),
    ("LED_A", 0.25, [("R25", "2"), ("D3", "2")]),
    ("+3V3", 0.4, [("R21", "2"), V3V3["R21"]]),
]
VIAS = ([("GND", STUB_VIA), ("GND", (14.4, 10.75)), ("GND", (14.7, 13.75)),
         ("GND", (2.0, 11.5)), ("GND", (10.37, 10.4)), ("GND", (6.05, 14.75)), ("VBAT", (5.85, 11.25)),
         ("BTN_USER", (5.4, 16.55)), ("I2C_SDA", (6.2, 16.95)), ("I2C_SCL", (7.0, 17.35)),
         ("VBAT_MEAS_EN", (7.8, 17.75)), ("GND", (2.5, 20.6)), ("EN", (10.2, 19.45)), ("GND", (10.35, 22.4)),
         ("LED", (11.6, 23.0)), ("GND", (17.75, 15.1)), ("GND", (24.4, 13.3)), ("GND", (20.9, 16.95)),
         ("GND", (16.3, 20.6))]
        + [("GND", p) for p in EP_VIAS + RF_GND_VIAS] + [("+3V3", p) for p in V3V3.values()])


def hand_copper(board, nets):
    def point(p):
        return G.pad_xy(board, *p) if isinstance(p[0], str) else p

    for net, w, pts in ROUTES:
        ps = [point(p) for p in pts]
        for a, c in zip(ps[:-1], ps[1:]):
            G.add_track(board, nets[net], a, c, w)
    for net, p in VIAS:
        G.add_via(board, nets[net], p, *VIA_S)
    # converter block and SHT40 tongue: as Rev B
    for net, w, pts in G.BLOCK_ROUTES:
        ps = [G.pad_xy(board, G.BLOCK_REFS[p[0]], p[1]) if isinstance(p[0], str) else G.block_xy(*p) for p in pts]
        for a, c in zip(ps[:-1], ps[1:]):
            G.add_track(board, nets[net], a, c, w)
    for net, p in G.BLOCK_VIAS:
        G.add_via(board, nets[net], G.block_xy(*p))
    for net, w, pts in G.FIXED_ROUTES[2:]:
        ps = [point(p) for p in pts]
        for a, c in zip(ps[:-1], ps[1:]):
            G.add_track(board, nets[net], a, c, w)
    for net, p in G.FIXED_VIAS:
        G.add_via(board, nets[net], p)
    # antenna ground pad: two vias right under it into the planes
    for x in (FX + 1.4, FX + 3.4):
        G.add_track(board, nets["GND"], (x, GE + 0.45), (x, GE + 0.95), 0.3)
        G.add_via(board, nets["GND"], (x, GE + 0.95), *VIA_S)


# ------------------------------------------------------------------ L3 power island
ISLAND_RECTS = [(9.0, 13.9, 14.3, 19.3),       # under the chip
                (10.9, 11.9, 12.0, 13.9),      # C40-C42
                (8.4, 13.8, 9.0, 15.0),        # C48
                (14.3, 15.3, 14.95, 16.2),     # pins 30/31, C43
                (9.8, 19.3, 11.6, 21.0),       # C46/C47
                (13.6, 17.9, 16.85, 19.3),     # C44/C45
                (13.6, 19.3, 16.0, 25.9),      # R21 (load-current link) -> chip
                (15.4, 25.9, 19.8, 27.1)]


def island_polygon():
    ps = pcbnew.SHAPE_POLY_SET()
    for x1, y1, x2, y2 in ISLAND_RECTS:
        r = pcbnew.SHAPE_POLY_SET()
        r.NewOutline()
        for x, y in rect(x1, y1, x2, y2):
            r.Append(mm(OX + x), mm(OY + y))
        ps.BooleanAdd(r)
    ps.Simplify()
    ol = ps.Outline(0)
    return [(pcbnew.ToMM(ol.CPoint(i).x) - OX, pcbnew.ToMM(ol.CPoint(i).y) - OY) for i in range(ol.PointCount())]


def add_island(board, nets):
    z = G.copper_zone(board, "In2.Cu", nets["+3V3"], island_polygon(), priority=1, name="3V3_L3")
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_NEVER)
    return z


# ------------------------------------------------------------------ keepouts that shape the planes
def thick_segment(a, b, r):
    """Rectangle around segment a-b, r on each side, extended by r at both ends."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    ux, uy = dx / L, dy / L
    nx, ny = -uy, ux
    a2 = (a[0] - ux * r, a[1] - uy * r)
    b2 = (b[0] + ux * r, b[1] + uy * r)
    return [(a2[0] + nx * r, a2[1] + ny * r), (b2[0] + nx * r, b2[1] + ny * r),
            (b2[0] - nx * r, b2[1] - ny * r), (a2[0] - nx * r, a2[1] - ny * r)]


RF_PATH = [P1b, P2, (FX, GE)]


def plane_keepouts(board):
    # F.Cu: no pour within 0.55 mm of the RF line (coplanar gap >> 2 h, so the line stays a microstrip)
    for a, b in zip(RF_PATH[:-1], RF_PATH[1:]):
        G.rule_area(board, "RF_GAP", thick_segment(a, b, 0.55), layers=("F.Cu",), tracks=False, vias=False)
    # HDG stub: no pour around the ground pad of C51 and the stub on L1, L2 cleared under them (reference L3)
    x0, y0 = PLACE["C51"][0] + 0.32 - 0.23 - 0.15, PLACE["C51"][1]
    G.rule_area(board, "STUB_L1", rect(x0, y0 - 0.45, STUB_VIA[0] - 0.24, y0 + 0.45), layers=("F.Cu",),
                tracks=False, vias=False)
    G.rule_area(board, "STUB_L2", rect(x0, y0 - 0.5, STUB_VIA[0] - 0.24, y0 + 0.5), layers=("In1.Cu",),
                tracks=False, vias=False)


# ------------------------------------------------------------------ routing
ROUTE_PLAN = [
    # (net, width, layer costs F/B, small vias); long runs prefer L4 so that L1 keeps its ground copper
    ("U0RXD", SIGNAL_W, (1.0, 2.0), True),
    ("U0TXD_J", SIGNAL_W, (1.5, 1.0), True),
    ("LED", SIGNAL_W, (1.0, 1.5), True),
    ("nRST", SIGNAL_W, (1.0, 2.0), True),
    ("EN", SIGNAL_W, (2.0, 1.0), True),
    ("VBAT_MEAS_EN", SIGNAL_W, (2.0, 1.0), True),
    ("BTN_USER", SIGNAL_W, (2.0, 1.0), True),
    ("I2C_SCL", SIGNAL_W, (2.0, 1.0), True),
    ("I2C_SDA", SIGNAL_W, (2.0, 1.0), True),
    ("VIN", POWER_W, (1.0, 5.0), False),
    ("VOUT", POWER_W, (1.0, 3.0), False),
    ("+3V3", POWER_W, (1.5, 1.0), False),
    ("VBAT", POWER_W, (2.0, 1.0), False),
]


def router_keepouts(R):
    # F.Cu inside the chip's pad ring and the RF area: only the fixed copper
    R.keepout_polygon(rect(CX - 2.7, CY - 2.7, CX + 2.7, CY + 2.7), layers=(0,), tracks=True, vias=True)
    R.keepout_polygon(rect(FX - 1.6, GE, FX + 2.0, P2[1] + 0.4), layers=(0, 1), tracks=True, vias=True)
    R.keepout_polygon(thick_segment(P1b, P2, 0.7), layers=(0, 1), tracks=True, vias=True)
    # crystals: nothing under them; nothing along the 32 MHz clock traces on L1 (HDG "Crystal")
    for ref, (hx, hy) in (("Y2", (1.9, 2.3)), ("Y1", (1.3, 2.2))):
        x, y, _ = PLACE[ref]
        R.keepout_polygon(rect(x - hx, y - hy, x + hx, y + hy), layers=(0, 1), tracks=True, vias=True)
    R.keepout_polygon(rect(14.1, 15.2, 21.2, 18.2), layers=(0,), tracks=True, vias=True)
    for ref in ("FID1", "FID2"):
        fx, fy, _ = PLACE[ref]
        R.keepout_polygon(G.circle_pts(fx, fy, 1.35, 24), layers=(0,), tracks=True, vias=True)


def route(board, nets):
    import router as RT
    R = RT.Router(board, OX, OY, W, H, grid=0.1, clearance=0.2, edge_clearance=0.3,
                  classes={"w20": 0.10, "w25": 0.125, "w30": 0.15, "w40": 0.20, "w50": 0.25, "via": 0.30})
    R.build()
    router_keepouts(R)
    R.block_vias_in_smd_pads(0.6)
    skip = {"U4", "J1", "AE1", G.BLOCK_REFS["U"]}
    gnd_pads = [p for fp in board.GetFootprints() if fp.GetReference() not in skip
                for p in fp.Pads() if p.GetNetname() == "GND"]
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
    """Signal vias the router did not continue (it left a fixed escape elsewhere) carry copper on one layer
    only: remove them; remove_dangling() then trims what is left of their escape."""
    planes = {"GND", "+3V3"}
    tracks, pads = {}, {}
    for t in board.GetTracks():
        if t.GetClass() != "PCB_VIA":
            tracks.setdefault(t.GetNetCode(), []).append(t)
    for fp in board.GetFootprints():
        for p in fp.Pads():
            pads.setdefault(p.GetNetCode(), []).append(p)
    removed = 0
    for v in [t for t in board.GetTracks() if t.GetClass() == "PCB_VIA"]:
        if v.GetNetname() in planes:
            continue
        q = v.GetPosition()
        layers = {t.GetLayer() for t in tracks.get(v.GetNetCode(), [])
                  if v.HitTest(t.GetStart()) or v.HitTest(t.GetEnd())}
        layers |= {L for p in pads.get(v.GetNetCode(), []) for L in (pcbnew.F_Cu, pcbnew.B_Cu)
                   if p.IsOnLayer(L) and p.HitTest(q)}
        if len(layers) < 2:
            board.Remove(v)
            removed += 1
    return removed


def text_boxes(board, grow=0.35):
    """Boxes (board mm) of the visible texts on both silkscreens: the stitching keeps its holes out of them."""
    out = []
    items = [d for d in board.GetDrawings() if d.GetClass() == "PCB_TEXT"]
    for fp in board.GetFootprints():
        items += [f for f in (fp.Reference(), fp.Value()) if f.IsVisible()]
    for t in items:
        if t.GetLayer() not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            continue
        bb = t.GetBoundingBox()
        out.append((pcbnew.ToMM(bb.GetX()) - OX - grow, pcbnew.ToMM(bb.GetY()) - OY - grow,
                    pcbnew.ToMM(bb.GetRight()) - OX + grow, pcbnew.ToMM(bb.GetBottom()) - OY + grow))
    return out


def stitch(board, R):
    """GND vias: a dense row along the antenna's ground-plane edge, around the 32 MHz crystal, then a 3 mm
    grid; none through a silkscreen text (the RF line has its own, RF_GND_VIAS)."""
    sites = [(x, GE + 0.6) for x in [0.9 + 1.0 * k for k in range(31)] if x < SLOT_X1 - 0.6]
    sites += [(20.3, 13.6), (20.3, 14.6), (25.3, 13.0), (24.9, 18.2), (22.6, 18.3), (19.4, 18.0)]
    y = 2.0
    while y < H - 1.0:
        x = 1.6
        while x < W - 1.0:
            sites.append((x, y))
            x += 3.0
        y += 3.0
    boxes = text_boxes(board)
    sites = [p for p in sites if not any(b[0] <= p[0] <= b[2] and b[1] <= p[1] <= b[3] for b in boxes)]
    return R.stitch(sites, via_dia=VIA_S[0], via_drill=VIA_S[1])


def add_zones(board, nets):
    poly = outline_polygon()
    G.copper_zone(board, "F.Cu", nets["GND"], poly, name="GND_L1")
    G.copper_zone(board, "In1.Cu", nets["GND"], poly, name="GND_L2")
    G.copper_zone(board, "In2.Cu", nets["GND"], poly, name="GND_L3")
    G.copper_zone(board, "B.Cu", nets["GND"], poly, name="GND_L4")
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


# ------------------------------------------------------------------ silkscreen
SILK_WARNING_REGION = (18.6, 8.8, 24.4, 10.6)      # two lines in the free ground area east of the RF chain
SILK_NAME_REGION = (40.2, 15.0, 40.6, 20.8)        # vertical, along the right edge
SILK_LABELS = (("RST", "SW2", (0.6, 41.0, 1.8, 46.0), (90,)),
               ("USER/BOOT", "SW1", (25.5, 16.6, 31.4, 18.6), (0,)),
               ("SHT40", "U5", (33.2, 9.0, 38.0, 11.6), (0, 90)))


def silkscreen(board):
    sp = G.SilkPlacer(board)
    t = TONGUE
    sp.cuts = [(SLOT_X1, 0, t["x1"], t["y2"] + SLOT_W), (SLOT_X1, t["y2"], t["bridge_x1"], t["y2"] + SLOT_W),
               (0, 0, SLOT_X1, GE)]            # nothing printed on the antenna either
    hidden, missing = [], []
    order = sorted(board.GetFootprints(), key=lambda f: -f.GetCourtyard(pcbnew.F_CrtYd).Area()
                   if f.GetCourtyard(pcbnew.F_CrtYd).OutlineCount() else 0)

    def txt(text, size=1.0, bold=False):
        return G.silk_text(board, text, 0, 0, size, bold=bold)

    t1, t2 = txt("CR2450 ONLY", 0.8, True), txt("NO CHARGE", 0.8, True)
    if not sp.place_pair(t1, t2, SILK_WARNING_REGION, dy=1.2):
        missing.append("CR2450 ONLY / NO CHARGE")
    tn = txt("%s Rev %s" % (D.BOARD_NAME, D.REV), 0.8, True)
    if not sp.free_spot(tn, SILK_NAME_REGION, step=0.2, angles=(90,)):
        missing.append(tn.GetText())
    for label, ref, region, angles in SILK_LABELS:
        tl = txt(label, 0.8)
        if not sp.free_spot(tl, region, step=0.2, angles=angles):
            missing.append(label)
    links = ("R1", "R21")
    tps = sorted((f for f in board.GetFootprints() if f.GetReference().startswith("TP")),
                 key=lambda f: int(f.GetReference()[2:]))
    n_obst = len(sp.obst)
    failed = []
    for attempt in range(2):
        del sp.obst[n_obst:]
        failed = []
        for fp in tps:
            fp.Reference().SetVisible(False)
            if not sp.place_reference(fp, field=fp.Value()):
                failed.append(fp)
        if not failed:
            break
        tps = failed + [f for f in tps if f not in failed]
    missing += [fp.GetReference() + " " + fp.GetValue() for fp in failed]
    # then the current-measurement links: the bring-up procedure refers to them by name
    for ref in links:
        if not sp.place_reference(board.FindFootprintByReference(ref)):
            missing.append(ref)
    if missing and "--silk-draft" not in sys.argv:
        raise RuntimeError("silkscreen: no room for " + ", ".join(missing))
    if missing:
        print("silkscreen: no room for " + ", ".join(missing))
    for fp in order:
        ref = fp.GetReference()
        if ref.startswith("TP") or ref in links:
            continue
        if ref in ("BT1", "AE1") or not sp.place_reference(fp):
            fp.Reference().SetVisible(False)
            hidden.append(ref)
    # back: the full story under the holder (no parts and no through-hole pads there)
    cx, y0 = W / 2, 39.0
    G.silk_text(board, "%s Rev %s  %s" % (D.BOARD_NAME, D.REV, D.DATE), cx, y0, 1.2, layer="B.SilkS", bold=True)
    G.silk_text(board, "ESP32-H2 (bare chip) Matter/Thread", cx, y0 + 2.2, 0.8, layer="B.SilkS")
    G.silk_text(board, "temperature & humidity", cx, y0 + 3.6, 0.8, layer="B.SilkS")
    G.silk_text(board, "1 x CR2450, TPS63900 3.3 V", cx, y0 + 5.0, 0.8, layer="B.SilkS")
    G.silk_text(board, "CR2450 ONLY - NO CHARGE", cx, y0 + 7.4, 1.2, layer="B.SilkS", bold=True)
    G.silk_text(board, "primary lithium cell - never recharge", cx, y0 + 9.4, 0.8, layer="B.SilkS")
    jx, jy, _ = PLACE["J1"]
    for i, lab in enumerate(["TX", "RX", "D+", "D-", "BOOT", "GND"]):
        G.silk_text(board, lab, jx + 2.54 * (i % 2) + (-2.3 if i % 2 == 0 else 2.3), jy + 2.54 * (i // 2), 0.8,
                    layer="B.SilkS")
    G.silk_text(board, "PCB ANTENNA (TI DN007, mirrored): keep clear", 14.0, 3.8, 0.8, layer="B.SilkS")
    return hidden


if __name__ == "__main__":
    board, nets = build_board()
    overlaps = courtyard_overlaps(board)
    if overlaps:
        raise SystemExit("courtyards overlap: %s" % overlaps)
    plane_keepouts(board)
    hand_copper(board, nets)
    add_island(board, nets)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    report = []
    if "--no-route" not in sys.argv:
        R = route(board, nets)
        one_sided = drop_one_sided_vias(board)
        trimmed = G.remove_dangling(board)
        report += R.log
        report.append("one-sided signal vias removed: %d; dangling stub segments trimmed or removed: %d"
                      % (one_sided, trimmed))
        print("unrouted:", len(R.unrouted), R.unrouted[:20])
        # silkscreen before the stitching vias, which then keep out of the texts
        hidden = silkscreen(board)
        vias = stitch(board, R)
        add_zones(board, nets)
        removed = G.prune_stitching(board, vias)
        report.append("stitching vias: %d placed, %d removed (single plane)" % (len(vias), removed))
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        report.append("references on F.Fab only (no room on silk; BT1 and AE1 by choice): %s"
                      % (", ".join(sorted(hidden)) or "none"))
        print("\n".join(report[-4:]))
        os.makedirs(REPORTS, exist_ok=True)
        with open(os.path.join(REPORTS, "routing_log.txt"), "w") as f:
            f.write("\n".join(report) + "\n")
            f.write("unrouted: %d\n" % len(R.unrouted))
            for u in R.unrouted:
                f.write("  " + u + "\n")
        print("\n".join(report[-8:]))
        print("unrouted:", len(R.unrouted), R.unrouted[:20])
    pcbnew.SaveBoard(PCB, board)
    subprocess.run([sys.executable, os.path.join(HERE, "gen_project.py")], check=True)
    board = pcbnew.LoadBoard(PCB)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(PCB, board)
    print("saved", PCB)
