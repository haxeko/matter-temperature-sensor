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
OUT = os.path.join(D.HW_DIR, "kicad")
LIB = os.path.join(OUT, "lib")
SCH = os.path.join(OUT, D.PROJECT + ".kicad_sch")
GRID = 1.27

# ---------------------------------------------------------------- libraries
SYM = {}


def load_symbols():
    vendored = os.path.join(LIB, "th_sensor.kicad_sym")
    for lib_id, (path, name) in D.SYMBOLS.items():
        nick, new_name = lib_id.split(":")
        if path is None:                             # drawn here from the datasheet (no library has it)
            SYM[lib_id] = SymbolSource(None, name, nick, text=wroom02c_symbol())
            continue
        if not os.path.exists(path) and nick == "th_sensor":
            path, name = vendored, new_name          # external library absent: use the copy in the repo
        overrides = None
        if lib_id == "th_sensor:ESP32-H2-MINI-1":
            overrides = {"Footprint": "th_sensor:ESP32-H2-MINI-1",
                         "Description": "ESP32-H2-MINI-1 module (Espressif KiCad library, CC-BY-SA 4.0 with "
                                        "design exception), 4 MB flash variant -H4S"}
        elif lib_id == "th_sensor:ESP32-H2":
            overrides = {"Footprint": "th_sensor:QFN-32-1EP_4x4mm_P0.4mm_EP2.9x2.9mm",
                         "Description": "ESP32-H2 SoC, QFN32 4x4 mm (Espressif KiCad library, CC-BY-SA 4.0 with "
                                        "design exception)"}
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
    # module / chip footprint (+ module 3D model) from the Espressif library (kept as vendored copies when it is
    # absent)
    if os.path.isdir(D.ESPRESSIF_LIB) and not D.WROOM:
        if D.VARIANT == "module":
            src_fp = os.path.join(D.ESPRESSIF_LIB, "footprints", "Espressif.pretty", "ESP32-H2-MINI-1.kicad_mod")
            fp = open(src_fp).read()
            fp = re.sub(r'\(model "[^"]*"', '(model "${KIPRJMOD}/lib/3dmodels/ESP32-H2-MINI-1.STEP"', fp)
            open(os.path.join(LIB, "th_sensor.pretty", "ESP32-H2-MINI-1.kicad_mod"), "w").write(fp)
            shutil.copyfile(os.path.join(D.ESPRESSIF_LIB, "3dmodels", "espressif.3dshapes", "ESP32-H2-MINI-1.STEP"),
                            os.path.join(LIB, "3dmodels", "ESP32-H2-MINI-1.STEP"))
        else:
            name = "QFN-32-1EP_4x4mm_P0.4mm_EP2.9x2.9mm.kicad_mod"
            shutil.copyfile(os.path.join(D.ESPRESSIF_LIB, "footprints", "Espressif.pretty", name),
                            os.path.join(LIB, "th_sensor.pretty", name))
        shutil.copyfile(os.path.join(D.ESPRESSIF_LIB, "LICENSE.md"),
                        os.path.join(LIB, "LICENSE-espressif-kicad-libraries.md"))
    if D.VARIANT == "chip":
        open(os.path.join(LIB, "th_sensor.pretty", ANT_FP + ".kicad_mod"), "w").write(ti_dn007_ifa())
    if D.WROOM:
        open(os.path.join(LIB, "th_sensor.pretty", WROOM_FP + ".kicad_mod"), "w").write(wroom02c_footprint())
        open(os.path.join(LIB, "th_sensor.pretty", TESTPADS_FP + ".kicad_mod"), "w").write(testpads_2x03())
    open(os.path.join(LIB, "th_sensor.pretty", "L_Murata_DFE201612E.kicad_mod"), "w").write(murata_dfe201612e())
    if D.CR123:
        open(os.path.join(LIB, "th_sensor.pretty", BH123A_FP + ".kicad_mod"), "w").write(myoung_bh123a_a1cj002())
    else:
        open(os.path.join(LIB, "th_sensor.pretty", "BatteryHolder_MYOUNG_BS-24-B4AA016_1x2450.kicad_mod"), "w").write(
            myoung_bs24_b4aa016())
    with open(os.path.join(OUT, "sym-lib-table"), "w") as f:
        f.write('(sym_lib_table\n\t(version 7)\n\t(lib (name "th_sensor")(type "KiCad")(uri "${KIPRJMOD}/lib/th_sensor.kicad_sym")'
                '(options "")(descr "%s project symbols"))\n)\n' % D.BOARD_NAME)
    with open(os.path.join(OUT, "fp-lib-table"), "w") as f:
        f.write('(fp_lib_table\n\t(version 7)\n\t(lib (name "th_sensor")(type "KiCad")(uri "${KIPRJMOD}/lib/th_sensor.pretty")'
                '(options "")(descr "%s project footprints"))\n)\n' % D.BOARD_NAME)


# TI DN007 (SWRU120D, 2019) "2.4-GHz Inverted F Antenna", Table 1-1 (mm). The two ground tabs and the 45-degree
# feed section are drawn in Figure 1-1 but not dimensioned: measured from the figure (+-0.1 mm).
DN007 = dict(H1=5.70, H2=0.74, H3=1.29, H4=2.21, H5=0.66, H6=1.21, H7=0.80, H8=1.80, H9=0.61, W1=1.21, W2=0.46,
             L1=25.58, L2=16.40, L3=2.18, L4=4.80, L5=1.00, L6=1.00, L7=3.20, L8=0.45)
DN007_TABS = ((6.85, 8.18), (9.00, 10.18))            # x ranges of the two legs to the ground plane (figure)


def dn007_geometry():
    """Copper of the antenna as polygons in TI's frame: x from the left end, y up from the ground-plane edge."""
    d = DN007
    top = d["H1"] + d["W1"]                    # 6.91 top edge of the radiating arm
    bar_bot, bar_top = d["H2"], d["H2"] + d["H3"]
    cut_top = top - d["H4"]                    # 4.70 bottom of the upper-left block
    blk_bot = bar_top + d["H5"]                # 2.69 feed block
    blk_top = blk_bot + d["H6"]                # 3.90 (= cut_top - H7)
    x_blk = d["L3"] + d["L4"]                  # 6.98
    x_blk_r = x_blk + d["L7"]                  # 10.18 (also the right end of the lower bar)
    x_stub = x_blk + d["L5"]                   # 7.98
    x_stub_r = x_blk_r - d["L6"]               # 9.18 (arm length to the right of it: L2)
    x_feed = x_blk_r + d["L8"]                 # 10.63
    rect = lambda x1, y1, x2, y2: [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    polys = [rect(0, d["H1"], d["L1"], top),                  # radiating arm (L1 x W1)
             rect(0, cut_top, x_stub, top),                   # upper-left block (H4)
             rect(0, bar_bot, d["L3"], top),                  # shorted leg (L3)
             rect(0, bar_bot, x_blk_r, bar_top),              # lower bar (H3)
             rect(x_stub, blk_top, x_stub_r, d["H1"]),        # tap to the arm (H8)
             rect(x_blk, blk_bot, x_blk_r, blk_top)]          # feed block (L7 x H6)
    polys += [rect(a, 0, b, bar_bot) for a, b in DN007_TABS]  # legs to ground (H2)
    w = d["W2"]
    y_l = 2.00                                  # feed line turns 45 degrees towards the block
    y_r = y_l + (w * 2 ** 0.5 - w)             # keeps the slanted part W2 wide
    polys.append([(x_feed, 0), (x_feed + w, 0), (x_feed + w, y_r), (x_blk_r, y_r + x_feed + w - x_blk_r),
                  (x_blk_r, y_l + x_feed - x_blk_r), (x_feed, y_l)])
    return polys, x_feed + w / 2, top + d["H9"]


ANT_FP = "Antenna_TI_DN007_IFA_2.4GHz_Mirrored"


def ti_dn007_ifa():
    """Footprint: mirror image of TI's drawing (open end of the radiating arm on the left, shorted section on the
    right of the feed), origin at the feed point on the ground-plane edge, antenna towards -Y. A mirror image has
    the same electrical behaviour; it puts the open end at the board edge, away from the parts on this board.
    Pads 1 (feed) and 2 (ground legs) are a net tie: the antenna shorts them at DC, as an inverted-F does."""
    u = lambda s_: new_uuid("fp-dn007m-" + s_)
    polys, xf, height = dn007_geometry()
    tx = lambda x: round(xf - x, 4)            # mirrored: TI's x grows to the left
    ty = lambda y: round(-y, 4)
    out = []
    for k, poly in enumerate(polys):
        pts = " ".join("(xy %s %s)" % (fmt(tx(x)), fmt(ty(y))) for x, y in poly)
        out.append(f'\t(fp_poly (pts {pts}) (stroke (width 0) (type solid)) (fill yes) (layer "F.Cu") '
                   f'(uuid "{u("cu%d" % k)}"))')
    x1, x2 = sorted((tx(DN007_TABS[0][0]), tx(DN007_TABS[1][1])))
    l1 = DN007["L1"]
    xl, xr = tx(l1), tx(0)                     # left (open) end, right (shorted) end
    # courtyard: the antenna area plus the two pads below the ground-plane edge, nothing else, so that the RF
    # parts can sit right under the feed
    w2 = DN007["W2"] / 2
    crt = [(xl - 0.25, ty(height)), (xr + 0.25, ty(height)), (xr + 0.25, 0), (round(x2 + 0.25, 4), 0),
           (round(x2 + 0.25, 4), 0.85), (round(x1 - 0.25, 4), 0.85), (round(x1 - 0.25, 4), 0.65), (-w2 - 0.25, 0.65),
           (-w2 - 0.25, 0), (xl - 0.25, 0)]
    crt_pts = " ".join("(xy %s %s)" % (fmt(round(x, 4)), fmt(round(y, 4))) for x, y in crt)
    return f"""(footprint "{ANT_FP}"
	(version 20241229)
	(generator "th_sensor_gen")
	(layer "F.Cu")
	(descr "2.4 GHz inverted-F PCB antenna, TI DN007 / SWRU120D (Rev. D) Figure 1-1 and Table 1-1, 25.7 x 7.5 mm, drawn as its mirror image (open end on the left); TI tuned it on 1 mm FR-4. Origin = feed point on the ground-plane edge. No copper on any layer in the antenna area (board-level rule area). Ground tabs and 45-degree feed measured from the figure.")
	(tags "antenna 2.4GHz IFA PCB TI DN007 SWRU120")
	(property "Reference" "REF**" (at {fmt(round(xl + 2.0, 4))} {fmt(ty(DN007["H1"]) + 1.0)} 0) (layer "F.Fab") (uuid "{u('ref')}") (effects (font (size 0.8 0.8) (thickness 0.12))))
	(property "Value" "{ANT_FP}" (at {fmt(round((xl + xr) / 2, 4))} {fmt(ty(DN007["H1"]) + 2.2)} 0) (layer "F.Fab") (uuid "{u('val')}") (effects (font (size 0.8 0.8) (thickness 0.12))))
	(attr smd exclude_from_pos_files exclude_from_bom)
	(net_tie_pad_groups "1,2")
{chr(10).join(out)}
	(fp_rect (start {fmt(xl)} {fmt(ty(height))}) (end {fmt(xr)} 0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "{u('fab')}"))
	(fp_poly (pts {crt_pts}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{u('crt')}"))
	(pad "1" smd rect (at 0 0.2) (size {fmt(DN007["W2"])} 0.4) (layers "F.Cu") (uuid "{u('p1')}"))
	(pad "2" smd rect (at {fmt(round((x1 + x2) / 2, 4))} 0.3) (size {fmt(round(x2 - x1, 4))} 0.6) (layers "F.Cu") (zone_connect 2) (uuid "{u('p2')}"))
	(embedded_fonts no)
)
"""


# ESP32-H2-WROOM-02C, datasheet v1.2 (Espressif, 2024): table 2 "Pin Definitions" (names, types), figure 2 pin
# layout, figure 6 dimensions, figure 7 "Recommended PCB Land Pattern". Neither KiCad nor Espressif's KiCad library
# (git dd76561) has this module, so symbol and footprint are drawn here.
WROOM_FP = "ESP32-H2-WROOM-02C"
WROOM_PINS = {   # number: (name, KiCad electrical type, side, position on that side)
    "1": ("3V3", "power_in", "L", 15.24), "14": ("VBAT", "power_in", "L", 12.7), "2": ("EN", "input", "L", 10.16),
    "3": ("IO4", "bidirectional", "L", 5.08), "4": ("IO5", "bidirectional", "L", 2.54),
    "7": ("IO8", "bidirectional", "L", 0.0), "8": ("IO9", "bidirectional", "L", -2.54),
    "5": ("IO10", "bidirectional", "L", -5.08), "6": ("IO11", "bidirectional", "L", -7.62),
    "10": ("IO12", "bidirectional", "L", -10.16), "11": ("IO13", "bidirectional", "L", -12.7),
    "12": ("IO14", "bidirectional", "L", -15.24), "15": ("IO22", "bidirectional", "L", -17.78),
    "28": ("IO0", "bidirectional", "R", 15.24), "27": ("IO1", "bidirectional", "R", 12.7),
    "26": ("IO2", "bidirectional", "R", 10.16), "25": ("IO3", "bidirectional", "R", 7.62),
    "20": ("IO25", "bidirectional", "R", 5.08), "21": ("RXD0", "bidirectional", "R", 0.0),
    "22": ("TXD0", "bidirectional", "R", -2.54), "23": ("IO26", "bidirectional", "R", -5.08),
    "24": ("IO27", "bidirectional", "R", -7.62), "16": ("NC", "no_connect", "R", -12.7),
    "17": ("NC", "no_connect", "R", -15.24), "18": ("NC", "no_connect", "R", -17.78),
    "19": ("NC", "no_connect", "R", -20.32),
    "9": ("GND", "power_in", "B", -2.54), "13": ("GND", "power_in", "B", 0.0), "29": ("GND", "power_in", "B", 2.54),
}


def wroom02c_symbol():
    """Symbol library text with the module symbol (pin names and types from the datasheet's table 2)."""
    f = '(effects (font (size 1.27 1.27)))'
    pins = []
    for num, (name, etype, side, pos) in sorted(WROOM_PINS.items(), key=lambda kv: int(kv[0])):
        x, y, a = {"L": (-15.24, pos, 0), "R": (15.24, pos, 180), "B": (pos, -25.4, 90)}[side]
        pins.append('(pin %s line (at %s %s %d) (length 2.54) (name "%s" %s) (number "%s" %s))'
                    % (etype, fmt(x), fmt(y), a, name, f, num, f))
    hid = '(effects (font (size 1.27 1.27)) (hide yes))'
    return (
        '(kicad_symbol_lib (version 20241209) (generator "th_sensor_gen") (generator_version "9.0")\n'
        '(symbol "%s" (exclude_from_sim no) (in_bom yes) (on_board yes)\n'
        '(property "Reference" "U" (at -12.7 19.05 0) (effects (font (size 1.27 1.27)) (justify left)))\n'
        '(property "Value" "%s" (at 12.7 19.05 0) (effects (font (size 1.27 1.27)) (justify right)))\n'
        '(property "Footprint" "th_sensor:%s" (at 0 -30.48 0) %s)\n'
        '(property "Datasheet" "https://www.espressif.com/sites/default/files/documentation/'
        'esp32-h2-wroom-02c_datasheet_en.pdf" (at 0 -33.02 0) %s)\n'
        '(property "Description" "ESP32-H2-WROOM-02C module (Bluetooth LE + IEEE 802.15.4), PCB antenna, 2 or 4 MB '
        'flash (-H2S / -H4S); pins from datasheet v1.2 table 2, drawn by gen_schematic.py" (at 0 -35.56 0) %s)\n'
        '(property "ki_keywords" "esp32-h2 wroom module thread zigbee matter" (at 0 0 0) %s)\n'
        '(property "ki_fp_filters" "ESP32-H2-WROOM-02C*" (at 0 0 0) %s)\n'
        '(symbol "%s_0_1" (rectangle (start -12.7 17.78) (end 12.7 -22.86) (stroke (width 0.254) (type default)) '
        '(fill (type background))))\n'
        '(symbol "%s_1_1" (text "ESP32-H2-WROOM-02C" (at 0 20.32 0) (effects (font (size 1.27 1.27))))\n%s)\n'
        '(embedded_fonts no))\n)\n'
        % (WROOM_FP, WROOM_FP, WROOM_FP, hid, hid, hid, hid, hid, WROOM_FP, WROOM_FP, "\n".join(pins)))


def wroom02c_pads():
    """(number, x, y, w, h) of the copper lands, origin = module centre, y down (module top at y = -10, the 6 mm
    antenna area above y = -4). Datasheet figure 7: side pads 1.5 x 0.9 with their centres 0.25 mm inside the module
    edge (so 0.5 mm of each pad is outside it), pitch 1.5, pins 1 and 28 7.1 mm below the module top; bottom pads
    0.9 x 1.5 centred 0.25 mm above the bottom edge, pins 10 and 19 2.25 mm from the sides; thermal pad: 2.8 x 0.55
    and 2.8 x 1.6, centred 8.53 mm from the left edge, 7.99 and 6.27 mm above the bottom edge."""
    out = []
    for k in range(1, 10):
        out.append((str(k), -8.75, round(-2.9 + 1.5 * (k - 1), 4), 1.5, 0.9))
    for k in range(10, 20):
        out.append((str(k), round(-6.75 + 1.5 * (k - 10), 4), 9.75, 0.9, 1.5))
    for k in range(20, 29):
        out.append((str(k), 8.75, round(9.1 - 1.5 * (k - 20), 4), 1.5, 0.9))
    out.append(("29", -0.47, 2.01, 2.8, 0.55))
    out.append(("29", -0.47, 3.73, 2.8, 1.6))
    return out


WROOM_EPAD_HOLE = (-0.47, 3.73, 1.4, 0.8)          # x, y, pad diameter, drill


def wroom02c_footprint():
    """Land pattern of datasheet figure 7, plus one 0.8 mm plated hole in the larger thermal-pad copper, open on
    both sides: the user solders the module by hand, and the module's EPAD can only be reached through it (solder
    fed from the back). No paste on the thermal pad for the same reason. The antenna area (top 6 mm) is meant to
    overhang the board edge (ESP32-H2 HDG, module placement figure, position 3)."""
    u = lambda s_: new_uuid("fp-wroom02c-" + s_)
    pads = []
    for i, (num, x, y, w, h) in enumerate(wroom02c_pads()):
        layers = '"F.Cu" "F.Mask" "F.Paste"' if num != "29" else '"F.Cu" "F.Mask"'
        pads.append('\t(pad "%s" smd rect (at %s %s) (size %s %s) (layers %s) (uuid "%s"))'
                    % (num, fmt(x), fmt(y), fmt(w), fmt(h), layers, u("p%d" % i)))
    hx, hy, hd, hdr = WROOM_EPAD_HOLE
    pads.append('\t(pad "29" thru_hole circle (at %s %s) (size %s %s) (drill %s) (layers "*.Cu" "*.Mask") '
                '(uuid "%s"))' % (fmt(hx), fmt(hy), fmt(hd), fmt(hd), fmt(hdr), u("hole")))
    return f"""(footprint "{WROOM_FP}"
	(version 20241229)
	(generator "th_sensor_gen")
	(layer "F.Cu")
	(descr "Espressif ESP32-H2-WROOM-02C module, 18 x 20 x 3.2 mm, land pattern per datasheet v1.2 figure 7; antenna area (top 6 mm) outside the base board; 0.8 mm plated hole in the thermal pad for hand soldering from the back")
	(tags "esp32-h2 wroom module castellated")
	(property "Reference" "REF**" (at -6 -5.2 0) (layer "F.SilkS") (uuid "{u('ref')}") (effects (font (size 1 1) (thickness 0.15))))
	(property "Value" "{WROOM_FP}" (at 0 6.5 0) (layer "F.Fab") (uuid "{u('val')}") (effects (font (size 1 1) (thickness 0.15))))
	(attr through_hole)
	(fp_line (start -9.85 -3.6) (end -9.85 9.3) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s1')}"))
	(fp_rect (start -9 -10) (end 9 10) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "{u('fab')}"))
	(fp_line (start -9 -4) (end 9 -4) (stroke (width 0.1) (type dash)) (layer "F.Fab") (uuid "{u('fab2')}"))
	(fp_poly (pts (xy -9 -3.4) (xy -8.4 -2.9) (xy -9 -2.4)) (stroke (width 0.1) (type solid)) (fill yes) (layer "F.Fab") (uuid "{u('fab3')}"))
	(fp_text user "PCB antenna: outside the board" (at 0 -7 0) (layer "F.Fab") (uuid "{u('fab4')}") (effects (font (size 0.8 0.8) (thickness 0.12))))
	(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab") (uuid "{u('fabref')}") (effects (font (size 1 1) (thickness 0.15))))
	(fp_rect (start -9.75 -10.25) (end 9.75 10.75) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{u('crt')}"))
{chr(10).join(pads)}
	(embedded_fonts no)
)
"""


TESTPADS_FP = "TestPads_2x03_P2.54mm_SMD"


def testpads_2x03():
    """Debug pads in the 2 x 3 header layout (2.54 mm, same numbering as PinHeader_2x03), SMD only (no holes):
    1.6 mm pads for soldering wires or for pogo pins; pad 1 square. No paste (nothing is placed on them)."""
    u = lambda s_: new_uuid("fp-tp2x3-" + s_)
    pads = []
    for k in range(6):
        x, y = 2.54 * (k % 2), 2.54 * (k // 2)
        shape = "rect" if k == 0 else "circle"
        pads.append('\t(pad "%d" smd %s (at %s %s) (size 1.6 1.6) (layers "F.Cu" "F.Mask") (uuid "%s"))'
                    % (k + 1, shape, fmt(x), fmt(y), u("p%d" % k)))
    return f"""(footprint "{TESTPADS_FP}"
	(version 20241229)
	(generator "th_sensor_gen")
	(layer "F.Cu")
	(descr "Debug test pads, 2 x 3 at 2.54 mm in the PinHeader_2x03 layout, SMD 1.6 mm (pad 1 square), no holes")
	(tags "test pad debug pogo smd")
	(property "Reference" "REF**" (at 1.27 -2.2 0) (layer "F.SilkS") (uuid "{u('ref')}") (effects (font (size 0.8 0.8) (thickness 0.15))))
	(property "Value" "{TESTPADS_FP}" (at 1.27 7.3 0) (layer "F.Fab") (uuid "{u('val')}") (effects (font (size 0.8 0.8) (thickness 0.12))))
	(attr smd)
	(fp_rect (start -1.27 -1.27) (end 3.81 6.35) (stroke (width 0.12) (type solid)) (fill no) (layer "F.SilkS") (uuid "{u('silk')}"))
	(fp_rect (start -1.0 -1.0) (end 3.54 6.08) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "{u('fab')}"))
	(fp_rect (start -1.05 -1.05) (end 3.59 6.13) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{u('crt')}"))
	(fp_text user "${{REFERENCE}}" (at 1.27 2.54 90) (layer "F.Fab") (uuid "{u('fabref')}") (effects (font (size 0.8 0.8) (thickness 0.12))))
{chr(10).join(pads)}
	(embedded_fonts no)
)
"""


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


def myoung_bs24_b4aa016():
    """CR2450 SMT holder MYOUNG BS-24-B4AA016 (LCSC C964809), drawing MY-CP-0138 (2018-05-30):
    land pattern 2 x 3.62 x 4.50 mm pads, 37.00 mm over the outer pad edges, 29.75 mm between them;
    body 27.0 x 16.0 mm (32.8 mm over the contact tabs, tab width 7.0 mm), 7.5 mm high; the
    24.5 mm cell overhangs the body on both long sides. Pad 1 = + (right), pad 2 = - (left)."""
    u = lambda s_: new_uuid("fp-bs24-" + s_)
    import math as _m
    # courtyard: union of pads (+0.25), tabs, body and the cell circle (r 12.25 + 0.25)
    r = 12.5
    yb = 8.25
    xa = _m.sqrt(r * r - yb * yb)
    arc = [(r * _m.cos(t), r * _m.sin(t)) for t in
           [_m.atan2(yb, xa) + k * (_m.pi - 2 * _m.atan2(yb, xa)) / 16 for k in range(17)]]
    top = [(18.75, 2.5), (16.65, 2.5), (16.65, 3.75), (13.75, 3.75), (13.75, yb)] + \
          [(x, y) for x, y in arc] + [(-13.75, yb), (-13.75, 3.75), (-16.65, 3.75), (-16.65, 2.5), (-18.75, 2.5)]
    poly = top + [(x, -y) for x, y in reversed(top)]
    crt = " ".join("(xy %.3f %.3f)" % (x, y) for x, y in poly)
    # silkscreen: body long edges and the parts of the cell outline outside the body, + / - marks
    silk_arc = lambda sgn, tag: (f'\t(fp_arc (start {-xa + 0.0:.3f} {sgn * 8.12:.3f}) (mid 0 {sgn * 12.37:.3f}) '
                                 f'(end {xa - 0.0:.3f} {sgn * 8.12:.3f}) (stroke (width 0.12) (type solid)) '
                                 f'(layer "F.SilkS") (uuid "{u(tag)}"))')
    return f'''(footprint "BatteryHolder_MYOUNG_BS-24-B4AA016_1x2450"
	(version 20241229)
	(generator "th_sensor_gen")
	(layer "F.Cu")
	(descr "CR2450 SMT coin cell holder, MYOUNG BS-24-B4AA016 (LCSC C964809), gold-plated contacts, LCP housing, 7.5 mm high; land pattern per drawing MY-CP-0138: pads 3.62 x 4.50 mm, 33.37 mm pitch")
	(tags "battery holder coin cell CR2450 smd")
	(property "Reference" "REF**" (at 0 -13.6 0) (layer "F.SilkS") (uuid "{u('ref')}") (effects (font (size 1 1) (thickness 0.15))))
	(property "Value" "BatteryHolder_MYOUNG_BS-24-B4AA016_1x2450" (at 0 13.6 0) (layer "F.Fab") (uuid "{u('val')}") (effects (font (size 1 1) (thickness 0.15))))
	(attr smd)
	(fp_line (start -13.62 -8.12) (end -{xa:.3f} -8.12) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s1')}"))
	(fp_line (start {xa:.3f} -8.12) (end 13.62 -8.12) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s2')}"))
	(fp_line (start -13.62 8.12) (end -{xa:.3f} 8.12) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s3')}"))
	(fp_line (start {xa:.3f} 8.12) (end 13.62 8.12) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s4')}"))
	(fp_line (start -13.62 -8.12) (end -13.62 -3.62) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s5')}"))
	(fp_line (start -13.62 8.12) (end -13.62 3.62) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s6')}"))
	(fp_line (start 13.62 -8.12) (end 13.62 -3.62) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s7')}"))
	(fp_line (start 13.62 8.12) (end 13.62 3.62) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s8')}"))
{silk_arc(-1, 'a1')}
{silk_arc(1, 'a2')}
	(fp_line (start 10.6 -5.6) (end 12.6 -5.6) (stroke (width 0.2) (type solid)) (layer "F.SilkS") (uuid "{u('p1')}"))
	(fp_line (start 11.6 -6.6) (end 11.6 -4.6) (stroke (width 0.2) (type solid)) (layer "F.SilkS") (uuid "{u('p2')}"))
	(fp_line (start -12.6 -5.6) (end -10.6 -5.6) (stroke (width 0.2) (type solid)) (layer "F.SilkS") (uuid "{u('m1')}"))
	(fp_rect (start -13.5 -8.0) (end 13.5 8.0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "{u('fb')}"))
	(fp_rect (start -16.4 -3.5) (end 16.4 3.5) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "{u('ft')}"))
	(fp_circle (center 0 0) (end 12.25 0) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "{u('fc')}"))
	(fp_poly (pts {crt}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{u('crt')}"))
	(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab") (uuid "{u('fabref')}") (effects (font (size 1 1) (thickness 0.15))))
	(pad "1" smd rect (at 16.685 0) (size 3.62 4.5) (layers "F.Cu" "F.Mask" "F.Paste") (uuid "{u('pad1')}"))
	(pad "2" smd rect (at -16.685 0) (size 3.62 4.5) (layers "F.Cu" "F.Mask" "F.Paste") (uuid "{u('pad2')}"))
	(embedded_fonts no)
)
'''


BH123A_FP = "BatteryHolder_MYOUNG_BH-123A-A1CJ002_1xCR123A"


def myoung_bh123a_a1cj002():
    """CR123A through-hole holder MYOUNG BH-123A-A1CJ002 (LCSC C5290177), drawing MY-CP-0398 (2024-03-07):
    body 43.3 x 18.2 mm, 14.2 mm high, two blade terminals (0.8 x 0.3 mm, 4.1 mm long) 37.5 +-0.5 mm apart on the
    centre line in 1.8 mm holes, one locating post (1.4 mm dia., 1.7 mm long) in a 2.0 mm hole, 18.95 mm from
    the centre and 8.4 mm from the terminal row, at the + end. Origin = body centre, component-side view.

    Which side of the row the post is on: the drawing's "PCB Layout Diagram" is a bottom view with '+' on the
    left, as in the top view, so it is the top view flipped about the long axis; the post is below the row there
    and therefore above it (-y) from the component side. The end view agrees (post at the top). Pad 1 = + (the
    terminal next to the post), pad 2 = -. To be compared with a real holder before ordering boards."""
    u = lambda s_: new_uuid("fp-bh123a-" + s_)
    bx, by = 21.65, 9.1
    return f'''(footprint "{BH123A_FP}"
	(version 20241229)
	(generator "th_sensor_gen")
	(layer "F.Cu")
	(descr "CR123A (CR17345) through-hole battery holder, MYOUNG BH-123A-A1CJ002 (LCSC C5290177), PA66 UL94 V-0, nickel-plated stainless contacts, 43.3 x 18.2 x 14.2 mm; PCB layout per drawing MY-CP-0398: two 1.8 mm holes 37.5 mm apart, one 2.0 mm locating hole")
	(tags "battery holder CR123A CR17345 tht")
	(property "Reference" "REF**" (at 0 -10.6 0) (layer "F.SilkS") (uuid "{u('ref')}") (effects (font (size 1 1) (thickness 0.15))))
	(property "Value" "{BH123A_FP}" (at 0 10.6 0) (layer "F.Fab") (uuid "{u('val')}") (effects (font (size 1 1) (thickness 0.15))))
	(attr through_hole)
	(fp_line (start -17.4 -{by + 0.12:.2f}) (end {bx + 0.12:.2f} -{by + 0.12:.2f}) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s1')}"))
	(fp_line (start {bx + 0.12:.2f} -{by + 0.12:.2f}) (end {bx + 0.12:.2f} {by + 0.12:.2f}) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s2')}"))
	(fp_line (start {bx + 0.12:.2f} {by + 0.12:.2f}) (end -{bx + 0.12:.2f} {by + 0.12:.2f}) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s3')}"))
	(fp_line (start -{bx + 0.12:.2f} {by + 0.12:.2f}) (end -{bx + 0.12:.2f} -6.9) (stroke (width 0.12) (type solid)) (layer "F.SilkS") (uuid "{u('s4')}"))
	(fp_line (start -15.6 0) (end -13.6 0) (stroke (width 0.2) (type solid)) (layer "F.SilkS") (uuid "{u('p1')}"))
	(fp_line (start -14.6 -1.0) (end -14.6 1.0) (stroke (width 0.2) (type solid)) (layer "F.SilkS") (uuid "{u('p2')}"))
	(fp_line (start 13.6 0) (end 15.6 0) (stroke (width 0.2) (type solid)) (layer "F.SilkS") (uuid "{u('m1')}"))
	(fp_rect (start -{bx:.2f} -{by:.2f}) (end {bx:.2f} {by:.2f}) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "{u('fb')}"))
	(fp_rect (start -17.25 -8.5) (end 17.25 8.5) (stroke (width 0.1) (type solid)) (fill no) (layer "F.Fab") (uuid "{u('fc')}"))
	(fp_rect (start -{bx + 0.25:.2f} -{by + 0.25:.2f}) (end {bx + 0.25:.2f} {by + 0.25:.2f}) (stroke (width 0.05) (type solid)) (fill no) (layer "F.CrtYd") (uuid "{u('crt')}"))
	(fp_text user "${{REFERENCE}}" (at 0 0 0) (layer "F.Fab") (uuid "{u('fabref')}") (effects (font (size 1 1) (thickness 0.15))))
	(fp_text user "CR123A" (at 0 3.0 0) (layer "F.Fab") (uuid "{u('fabcell')}") (effects (font (size 1 1) (thickness 0.15))))
	(pad "1" thru_hole rect (at -18.75 0) (size 3.2 3.2) (drill 1.8) (layers "*.Cu" "*.Mask") (uuid "{u('pad1')}"))
	(pad "2" thru_hole circle (at 18.75 0) (size 3.2 3.2) (drill 1.8) (layers "*.Cu" "*.Mask") (uuid "{u('pad2')}"))
	(pad "" np_thru_hole circle (at -18.95 -8.4) (size 2 2) (drill 2) (layers "*.Cu" "*.Mask") (uuid "{u('post')}"))
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


def power_block(yc):
    x0, dx = 12.7, 12.7
    S.frame(x0, yc - 15.24, CELL_RIGHT, yc + 50.8,
            "CR123A -> fuse -> P-MOSFET -> TPS63900 (3.3 V) -> VOUT" if D.CR123 else
            "CR2450 -> P-MOSFET -> TPS63900 (3.3 V) -> VOUT")
    c_in = ["C1", "C2", "C3"] + ([] if D.CR123 else ["C5"])
    rcfg = ["R2", "R3", "R4"]
    tp1_x = 35.56 if D.CR123 else 30.48       # the VBAT node: after the fuse on the CR123A board
    S.place("BT1", 22.86, yc + 5.08, 0, ref_off=(3.81, -1.27), val_off=(3.81, 1.27))
    S.place("R1", 40.64, yc, 90, ref_off=(-1.27, -2.54), val_off=(-1.27, 3.81))
    S.place("Q1", 63.5, yc + 2.54, 90, ref_off=(3.81, 2.54), val_off=(3.81, 5.08))
    for i, c in enumerate(c_in):
        S.place(c, 76.2 + i * 10.16, yc + 3.81, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("U1", 139.7 + dx, yc + 10.16, 0, ref_off=(-7.62, -14.22), val_off=(3.81, 13.97))
    S.place("L1", 119.38 + dx, yc + 15.24, 0, ref_off=(-5.08, -1.27), val_off=(-7.62, 1.27))
    S.place("C4", 165.1 + dx, yc + 3.81, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    for i, rr in enumerate(rcfg):
        S.place(rr, 162.56 + dx + i * 10.16, yc + 26.67, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    for tp, x in (("TP1", tp1_x), ("TP2", 116.84 + dx)):
        S.place(tp, x, yc - 5.08, 0, ref_off=(1.27, -3.81), val_off=(1.27, -6.35))
    # main chain along y = yc, split at every connection point
    if D.CR123:
        S.place("F1", 29.21, yc, 90, ref_off=(-1.27, 2.54), val_off=(-1.27, 5.08))
        S.wire(S.pin("BT1", "1"), S.pin("F1", "1"))
        S.label("VCELL", (24.13, yc), 0)
        S.wire(S.pin("F1", "2"), (tp1_x, yc), S.pin("R1", "1"))
        S.wire(S.pin("TP1", "1"), (tp1_x, yc))
        S.junction((tp1_x, yc))
        S.label("VBAT", (34.29, yc), 0)
    else:
        S.wire(S.pin("BT1", "1"), (30.48, yc), S.pin("R1", "1"))
        S.wire(S.pin("TP1", "1"), (30.48, yc))
        S.junction((30.48, yc))
        S.label("VBAT", (24.13, yc), 0)
    S.wire(S.pin("R1", "2"), S.pin("Q1", "3"))
    S.label("VBAT_L", (46.99, yc), 0)
    vin_pts = [S.pin("Q1", "2"), (71.12, yc)] + [S.pin(c, "1") for c in c_in] + [(116.84 + dx, yc),
                                                                              (124.46 + dx, yc), S.pin("U1", "10")]
    S.wire(*vin_pts)
    for p in vin_pts[1:-1]:
        S.junction(p)
    S.wire(S.pin("TP2", "1"), (116.84 + dx, yc))
    S.power("PWR_FLAG", (71.12, yc - 5.08), 0)
    S.wire((71.12, yc - 5.08), (71.12, yc))
    S.label("VIN", (99.06, yc), 0)
    # EN tied to VIN, SEL to GND (VO(1) = 3.3 V)
    S.wire((124.46 + dx, yc), (124.46 + dx, yc + 5.08), S.pin("U1", "1"))
    S.stub("U1", "2", length=2.54)
    # inductor
    lx1, lx2 = S.pin("U1", "9"), S.pin("U1", "7")
    S.wire(lx1, (119.38 + dx, lx1[1]), S.pin("L1", "1"))
    S.wire(lx2, (119.38 + dx, lx2[1]), S.pin("L1", "2"))
    S.label("LX1", (120.65 + dx, lx1[1]), 0)
    S.label("LX2", (120.65 + dx, lx2[1]), 0)
    S.stub("Q1", "1", length=2.54)
    S.stub("BT1", "2")
    for c in c_in + ["C4"]:
        S.stub(c, "2")
    S.stub("U1", "8", length=2.54)
    # output: the converter output VOUT is the rail before the R21 link (no OR diode in Rev B)
    out_pts = [S.pin("U1", "6"), S.pin("C4", "1"), (196.85, yc)]
    S.wire(*out_pts)
    S.junction(S.pin("C4", "1"))
    S.label("VOUT", (196.85, yc), 0)
    # configuration resistors via labels
    for pin in ("3", "4", "5"):
        S.stub("U1", pin, length=5.08)
    for rr in rcfg:
        S.stub(rr, "1", label_angle=0)
        S.stub(rr, "2")
    S.text("SEL = L: VO(1) = 3.3 V (RCFG3 16.2k, table 7-3). Input current limit 100 mA from RCFG1 0R / RCFG2 10.5k\n"
           "(table 7-2; 13.3k = 50 mA option). TI SLVSET3D, +-1 %% resistors. %s"
           % ("F1: resettable fuse at the cell; no 470 uF buffer (CR123A)." if D.CR123 else
              "C5: 470 uF electrolytic buffer."),
           (x0 + 1.27, yc + 41.91), size=1.27)


def rail_block():
    x1, y1 = 213.36, 17.78
    S.frame(x1, y1, 303.53, 86.36, "3V3 RAIL, SUPERVISOR, RESET")
    y = 35.56
    S.label("VOUT", (228.6, y), 180)
    S.place("TP3", 233.68, y - 5.08, 0, ref_off=(1.27, -3.81), val_off=(1.27, -6.35))
    S.place("C21", 241.3, y + 3.81, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("C22", 256.54, y + 3.81, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("R21", 280.67, y, 90, ref_off=(-1.27, -2.54), val_off=(-1.27, 3.81))
    S.place("TP4", 289.56, y + 5.08, 180, ref_off=(1.905, 3.81), val_off=(1.905, 6.35))
    rail = [(228.6, y), (233.68, y), S.pin("C21", "1"), S.pin("C22", "1"), S.pin("R21", "1")]
    S.wire(*rail)
    for p in rail[1:-1]:
        S.junction(p)
    S.wire(S.pin("TP3", "1"), (233.68, y))
    S.stub("C21", "2")
    S.stub("C22", "2")
    S.wire(S.pin("R21", "2"), (289.56, y), (297.18, y))
    S.junction((289.56, y))
    S.wire(S.pin("TP4", "1"), (289.56, y))
    S.power("+3V3", (297.18, y), 0)
    S.power("PWR_FLAG", (297.18, y), 180)

    # supervisor
    ys = 66.04
    S.place("C26", 228.6, ys, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("U3", 248.92, ys, 0, ref_off=(3.81, -6.35), val_off=(3.81, 10.16))
    S.place("R22", 266.7, ys, 90, ref_off=(-1.27, -3.81), val_off=(-1.27, 3.81))
    S.place("C25", 279.4, ys + 3.81, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    has_rst = any(q["ref"] == "SW2" for q in D.PARTS)       # the wroom board has no RST button
    if has_rst:
        S.place("SW2", 289.56, ys + 5.08, 270, ref_off=(5.08, -1.27), val_off=(5.08, 1.27))
    S.stubs("U3", ["3", "1"])
    S.stubs("C26")
    S.wire(S.pin("U3", "2"), S.pin("R22", "1"))
    S.label("nRST", (259.08, ys), 0)
    if has_rst:
        S.wire(S.pin("R22", "2"), S.pin("C25", "1"), S.pin("SW2", "1"), (293.37, ys), (297.18, ys))
        S.junction(S.pin("C25", "1"))
        S.junction(S.pin("SW2", "1"))
    else:
        S.wire(S.pin("R22", "2"), S.pin("C25", "1"), (293.37, ys), (297.18, ys))
        S.junction(S.pin("C25", "1"))
    S.label("EN", (297.18, ys), 0)
    S.place("TP6", 293.37, ys - 5.08, 0, ref_off=(1.27, -3.81), val_off=(1.27, -6.35))
    S.wire(S.pin("TP6", "1"), (293.37, ys))
    S.junction((293.37, ys))
    S.stub("C25", "2")
    if has_rst:
        S.stub("SW2", "2")
    else:
        S.text("No RST button on this board: reset = short TP6 (EN) to GND,\n"
               "or the automatic reset of the USB-Serial/JTAG port.", (276.86, ys + 7.62), size=1.0)


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
    # debug pads (USB D+/D- straight from the module, no series resistors)
    S.place("J1", 396.24, 113.03, 0, ref_off=(-2.54, -11.43), val_off=(-2.54, -8.89))
    S.stubs("J1", [str(i) for i in range(1, 6)], length=5.08)
    g = S.pin("J1", "6")
    S.wire(g, (g[0] - 2.54, g[1]), (g[0] - 2.54, g[1] + 2.54))
    S.power("GND", (g[0] - 2.54, g[1] + 2.54), 0)
    S.text("GPIO8/GPIO9 are strapping pins: GPIO9 low at reset (SW1 held) = download mode.\n"
           "VBAT (pad 15) is tied to 3V3 inside the module (R2 = 0R); connected here as well.\n"
           "Unused GPIO0/1/2/3/4/25: no connect, firmware disables input + pull-down.\n"
           "J1 is a pad row (not fitted) without a supply pin: the cell (or a bench supply on its contacts) powers the board.\n"
           "Reset for programming: SW2 (RST) or the USB-Serial/JTAG reset; EN is on test pad TP6, not on J1.",
           (x1 + 1.27, 195.58))


def chip_block():
    """Chip variant: ESP32-H2 QFN32 with the HDG v1.6 reference circuit (decoupling, 32 MHz crystal with the
    24 nH series element, RF matching network, PCB antenna), plus the parts shared with the module variant."""
    x1, y1, x2, y2 = 213.36, 91.44, 406.4, 213.36
    S.frame(x1, y1, x2, y2, "ESP32-H2FH4S CHIP, 32 MHz AND 32.768 kHz CRYSTALS, RF MATCH + PCB ANTENNA, BUTTON, LED, DEBUG")
    ux, uy = 299.72, 157.48
    S.place("U4", ux, uy, 0, ref_off=(-27.94, -34.29), val_off=(10.16, 31.75))
    # signal pins; the VDD3P3 pins 1, 2, 27, 30, 31 are stacked on one point of the symbol
    for num in ["3", "4", "5", "6", "7", "8", "10", "11", "12", "13", "14", "15", "16", "17", "21", "22", "23",
                "24", "25", "26", "28", "29", "32"]:
        S.stub("U4", num, length=5.08)
    S.stub("U4", "33")
    S.stub("U4", "1")
    top = S.pin("U4", "1")[1] - 2.54
    xs = [S.pin("U4", n)[0] for n in ("1", "18", "19", "9", "20")]
    for n in ("18", "19", "9", "20"):
        p_ = S.pin("U4", n)
        S.wire(p_, (p_[0], top))
    for a, b in zip(xs, xs[1:]):
        S.wire((a, top), (b, top))
    for x in xs[:-1]:
        S.junction((x, top))
    # decoupling (HDG reference values), one capacitor per supply pin group
    for k, ref in enumerate(["C40", "C41", "C42", "C43", "C44", "C45", "C46", "C47", "C48"]):
        S.place(ref, 228.6 + 7.62 * k, 106.68, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
        S.stubs(ref)
    S.text("C40-C42: VDD3P3 pins 1/2. C43: pins 30/31. C44, C45: pin 27. C46: VDDPST2 (20). C47: VDDA_PMU (19) and "
           "VBAT (18). C48: VDDPST1 (9).\nPlace each at its pin (HDG v1.6 schematic checklist).", (x1 + 1.27, 115.57),
           size=1.0)
    # 32 MHz crystal, load caps, series element on XTAL_P
    S.place("Y2", 236.22, 129.54, 0, ref_off=(-2.54, -3.81), val_off=(1.27, -3.81))
    S.stubs("Y2", ["1", "3"])
    S.stub("Y2", "2")
    S.place("C49", 220.98, 133.35, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("C50", 251.46, 133.35, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.stubs("C49")
    S.stubs("C50")
    S.place("L3", 226.06, 147.32, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.stubs("L3")
    # UART TX series resistor (HDG)
    S.place("R40", 360.68, 132.08, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.stubs("R40")
    # RF: ANT -> C51 (shunt) -> L4 (series) -> C52 (shunt) -> R41 (series) -> L5 (shunt, not fitted) -> AE1
    yr = 198.12
    S.place("C51", 271.78, yr + 3.81, 0, ref_off=(1.27, 1.27), val_off=(1.27, 3.81))
    S.place("L4", 279.4, yr, 90, ref_off=(-1.27, -2.54), val_off=(-1.27, -5.08))
    S.place("C52", 287.02, yr + 3.81, 0, ref_off=(1.27, 1.27), val_off=(1.27, 3.81))
    S.place("R41", 294.64, yr, 90, ref_off=(-1.27, -2.54), val_off=(-1.27, -5.08))
    S.place("L5", 302.26, yr + 3.81, 0, ref_off=(1.27, 1.27), val_off=(1.27, 3.81))
    S.place("AE1", 309.88, yr - 5.08, 0, ref_off=(3.81, -7.62), val_off=(3.81, -5.08))
    l4 = sorted([S.pin("L4", "1"), S.pin("L4", "2")])
    r41 = sorted([S.pin("R41", "1"), S.pin("R41", "2")])
    if S.pin("L4", "1")[0] > S.pin("L4", "2")[0] or S.pin("R41", "1")[0] > S.pin("R41", "2")[0]:
        raise SystemExit("RF chain: series parts are reversed")
    for a, b in [((266.7, yr), S.pin("C51", "1")), (S.pin("C51", "1"), l4[0]), (l4[1], S.pin("C52", "1")),
                 (S.pin("C52", "1"), r41[0]), (r41[1], S.pin("L5", "1")), (S.pin("L5", "1"), S.pin("AE1", "1"))]:
        S.wire(a, b)
    for p_ in (S.pin("C51", "1"), S.pin("C52", "1"), S.pin("L5", "1")):
        S.junction(p_)
    S.label("LNA_IN", (266.7, yr), 180)
    S.label("RF_M", S.pin("C52", "1"), 0)
    S.label("RF_ANT", S.pin("L5", "1"), 0)
    for ref in ("C51", "C52", "L5"):
        S.stub(ref, "2")
    g = S.pin("AE1", "2")
    S.wire(g, (g[0], g[1] + 5.08))
    S.power("GND", (g[0], g[1] + 5.08), 0)
    S.text("RF: 50 ohm line, 0201 parts. C51/L4/C52 = HDG C12/L2/C11, start values from the HDG ranges;\n"
           "R41 (HDG C3) is a 0R link, L5 (HDG L1) not fitted. All five must be tuned with a network analyser.",
           (262.89, 206.88), size=1.0)
    # 32.768 kHz crystal (same parts as the module variant)
    S.place("Y1", 238.76, 196.85, 0, ref_off=(-2.54, -3.81), val_off=(-5.08, -6.35))
    S.place("C27", 228.6, 200.66, 0, ref_off=(-6.35, -1.27), val_off=(-6.35, 1.27))
    S.place("C28", 248.92, 200.66, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.wire(S.pin("C27", "1"), S.pin("Y1", "1"))
    S.wire(S.pin("Y1", "2"), S.pin("C28", "1"))
    S.label("XTAL_32K_P", (228.6, 196.85), 180)
    S.label("XTAL_32K_N", (248.92, 196.85), 0)
    S.stub("C27", "2")
    S.stub("C28", "2")
    # USER/BOOT button and pull-ups, LED (as the module variant)
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
    S.place("R25", 370.84, 165.1, 90, ref_off=(-1.27, -2.54), val_off=(-1.27, 3.81))
    S.place("D3", 386.08, 165.1, 180, ref_off=(-2.54, -2.54), val_off=(-2.54, 3.81))
    S.stub("R25", "1")
    S.wire(S.pin("R25", "2"), S.pin("D3", "2"))
    S.label("LED_A", (375.92, 165.1), 0)
    S.stub("D3", "1")
    # debug pads, 2 x 3
    S.place("J1", 391.16, 115.57, 0, ref_off=(-2.54, -6.35), val_off=(-2.54, 6.35))
    S.stubs("J1", [str(i) for i in range(1, 6)], length=5.08)
    g = S.pin("J1", "6")
    S.wire(g, (g[0] + 2.54, g[1]), (g[0] + 2.54, g[1] + 2.54))
    S.power("GND", (g[0] + 2.54, g[1] + 2.54), 0)
    S.text("GPIO8/GPIO9 strapping: GPIO9 low at reset (SW1 held) = download mode.\n"
           "GPIO0/1/2/3/4/25: no connect, firmware disables input + pull-down.\n"
           "J1 (not fitted) has no supply pin: the cell powers the board.",
           (332.74, 95.25), size=1.0)


def wroom_block():
    """WROOM variant: ESP32-H2-WROOM-02C (datasheet v1.2 peripheral schematic: 10 uF + 0.1 uF on 3V3, external RC
    on EN), the 32.768 kHz crystal, button, pull-ups, LED and the 2 x 3 debug pads."""
    x1, y1, x2, y2 = 213.36, 91.44, 406.4, 213.36
    S.frame(x1, y1, x2, y2, "ESP32-H2-WROOM-02C-H4S (USER-SUPPLIED), 32.768 kHz CRYSTAL, USER/BOOT BUTTON, LED, DEBUG PADS")
    ux, uy = 304.8, 149.86
    S.place("U4", ux, uy, 0, ref_off=(-12.7, -24.13), val_off=(5.08, 33.02))
    for num in ["2", "3", "4", "7", "8", "5", "6", "10", "11", "12", "15",
                "28", "27", "26", "25", "20", "21", "22", "23", "24"]:
        S.stub("U4", num, length=5.08)
    # 3V3 (1) and VBAT (14) to one +3V3 symbol; the three GND pins to one GND symbol
    p1, p14 = S.pin("U4", "1"), S.pin("U4", "14")
    xs = p1[0] - 5.08
    # (wires end at every junction: kicad-cli loses the far end of a wire that a junction splits)
    S.wire(p1, (xs, p1[1]))
    S.wire(p14, (xs, p14[1]), (xs, p1[1]), (xs, p1[1] - 5.08))
    S.junction((xs, p1[1]))
    S.power("+3V3", (xs, p1[1] - 5.08), 0)
    gp = [S.pin("U4", n) for n in ("9", "13", "29")]
    yb = gp[0][1] + 2.54
    for q in gp:
        S.wire(q, (q[0], yb))
    S.wire((gp[0][0], yb), (gp[1][0], yb), (gp[2][0], yb))
    S.junction((gp[1][0], yb))
    S.wire((gp[1][0], yb), (gp[1][0], yb + 2.54))
    S.power("GND", (gp[1][0], yb + 2.54), 0)
    # module decoupling at pin 1 (datasheet peripheral schematic: 10 uF + 0.1 uF)
    S.place("C23", 231.14, 106.68, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("C24", 241.3, 106.68, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.stubs("C23")
    S.stubs("C24")
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
    # debug pads, 2 x 3 (USB D+/D- straight from the module)
    S.place("J1", 391.16, 115.57, 0, ref_off=(-2.54, -6.35), val_off=(-2.54, 6.35))
    S.stubs("J1", [str(i) for i in range(1, 6)], length=5.08)
    g = S.pin("J1", "6")
    S.wire(g, (g[0] + 2.54, g[1]), (g[0] + 2.54, g[1] + 2.54))
    S.power("GND", (g[0] + 2.54, g[1] + 2.54), 0)
    S.text("U4 is bought and hand-soldered by the user (not in the JLC BOM/CPL). Its EPAD (29) is soldered from the\n"
           "back through the 0.8 mm hole in the land pattern. GPIO8/GPIO9 strapping: GPIO9 low at reset (SW1 held) =\n"
           "download mode. VBAT (14) is tied to 3V3 inside the module (R2 = 0R); tied to +3V3 here as well.\n"
           "EN has no RC inside the module (datasheet section 8): R22/C25 on the rail block. TXD0 has a 499R series\n"
           "resistor inside the module. IO0/1/2/3/4/25: no connect, firmware disables input + pull-down; 16-19 are NC.\n"
           "J1: six SMD pads (no holes) for wires or pogo pins, no supply pin: the cell powers the board.\n"
           "SW1 is a side-push switch at the board edge; there is no RST button (see the rail block).",
           (x1 + 1.27, 195.58), size=1.0)


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
    x1, y1 = 12.7, 91.44
    S.frame(x1, y1, CELL_RIGHT, 157.48, "CELL VOLTAGE SENSE (switched 470k/470k divider, ADC1_CH4 on GPIO5)")
    x = 45.72
    S.place("R31", x, 109.22, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("R32", x, 123.19, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("C31", x + 12.7, 120.65, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.place("Q3", x - 2.54, 137.16, 0, ref_off=(3.81, -1.27), val_off=(3.81, 1.27))
    S.stub("R31", "1", label_angle=0)
    mid = (x, 115.57)
    S.wire(S.pin("R31", "2"), mid, S.pin("R32", "1"))
    S.wire(mid, (x + 12.7, 115.57), S.pin("C31", "1"))
    S.wire((x + 12.7, 115.57), (x + 22.86, 115.57))
    S.junction(mid)
    S.junction((x + 12.7, 115.57))
    S.label("VBAT_SENSE", (x + 22.86, 115.57), 0)
    S.wire(S.pin("R32", "2"), S.pin("Q3", "3"))
    S.label("SNS_LO", (x, 129.54), 0)
    S.stub("C31", "2")
    S.stub("Q3", "2")
    S.stub("Q3", "1", length=5.08)
    S.place("R35", 121.92, 137.16, 0, ref_off=(1.27, -1.27), val_off=(1.27, 1.27))
    S.stubs("R35")
    S.text("Switch open: no divider current. GPIO12 high for ~30 ms every 6 h: 470k/470k -> ~3.2 uA while on.\n"
           "The divider top is at the holder terminal (before the 0R link), so a missing cell reads ~0 V.",
           (x1 + 1.27, 148.59))


def misc_block():
    x1, y1 = 12.7, 165.1
    S.frame(x1, y1, CELL_RIGHT, 210.82, "TEST PADS, MECHANICAL, NOTES")
    S.place("TP5", 22.86, 180.34, 0, ref_off=(1.27, -3.81), val_off=(1.27, -6.35))
    S.stub("TP5", "1")
    S.power("PWR_FLAG", (50.8, 177.8), 0)
    S.wire((50.8, 177.8), (50.8, 182.88))
    S.power("GND", (50.8, 182.88), 0)
    for k, ref in enumerate(["FID1", "FID2"]):
        S.place(ref, 71.12 + k * 15.24, 180.34, 0, ref_off=(-2.54, -5.08), val_off=(-2.54, 5.08))
    S.text("CR2450 ONLY - NOT RECHARGEABLE. No other supply can reach the rail: the cell is the only energy source.\n"
           "Power-path decision and its limits: docs/decisions.md, docs/power_budget.md (ESTIMATE until measured).\n"
           "Current measurement: remove R1 (cell) or R21 (load) and insert the ammeter.\n"
           "U3 TPS3839K33: 2.93 V typ (2.857-2.974 V), push-pull ~RESET, 200 ms delay; R22 keeps it from fighting %s."
           % ("a short of TP6 (EN) to GND" if D.CR123 else "SW2 / TP6 (EN)"),
           (x1 + 1.27, 193.04))


def build():
    load_symbols()
    write_project_libs()
    power_block(33.02)
    rail_block()
    if D.VARIANT == "module":
        module_block()
    elif D.VARIANT == "chip":
        chip_block()
    else:
        wroom_block()
    sensor_block()
    sense_block()
    misc_block()
    missing = [q["ref"] for q in D.PARTS if q["ref"] not in S.placed]
    if missing:
        raise SystemExit("not placed: %s" % missing)
    lib_symbols = "\n".join(SYM[k].embedded() for k in sorted(SYM))
    title = ('(title_block (title "%s") (date "%s") (rev "%s") (company "%s") '
             '(comment 1 "%s") '
             '(comment 4 "Generated by hardware/scripts/gen_schematic.py from design.py - edit there") '
             '(comment 2 "Power path and battery life figures are ESTIMATES (docs/power_budget.md)") '
             '(comment 3 "ERC/DRC reports: %s"))'
             % (D.TITLE, D.DATE, D.REV, D.BOARD_NAME,
                {"module": "ESP32-H2 Matter over Thread, SHT40, 1 x CR2450, TPS63900 3.3 V",
                 "chip": "ESP32-H2FH4S chip + PCB antenna, Matter over Thread, SHT40, 1 x CR2450, TPS63900 3.3 V",
                 "wroom": "ESP32-H2-WROOM-02C (user-supplied), Matter over Thread, SHT40, 1 x CR2450, TPS63900 3.3 V",
                 "wroom123": "ESP32-H2-WROOM-02C (user-supplied), Matter over Thread, SHT40, 1 x CR123A, "
                             "TPS63900 3.3 V"}
                [D.VARIANT],
                {"module": "hardware/reports", "chip": "hardware/chip/reports",
                 "wroom": "hardware/wroom/reports", "wroom123": "hardware/wroom123/reports"}[D.VARIANT]))
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
