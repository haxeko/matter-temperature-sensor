#!/usr/bin/env python3
"""
Fabrication and assembly outputs for TH-SENSOR-H2 (revision from design.py, JLCPCB conventions).

  hardware/production/gerbers/          Gerber X2 + Excellon (drill/place origin = board bottom-left)
  hardware/production/th_sensor_h2_rev<REV>_gerbers.zip
  hardware/production/bom_jlc.csv       Comment, Designator, Footprint, LCSC Part #, ... (fitted parts only)
  hardware/production/cpl_jlc.csv       Designator, Mid X, Mid Y, Layer, Rotation (KiCad rotation, see below)
  hardware/production/assembly_top.pdf  fab layer drawing for hand assembly and for checking the CPL
  hardware/production/orientation_check.md  pin-1 / polarity of every polarised part, for the JLC preview
  hardware/production/manufacturing_blockers.md

Sourcing data comes from jlc_parts_snapshot.jsonl (tools/jlc_lookup.py --json, re-run before ordering).
Rotations in the CPL are KiCad's. JLCPCB's part models do not always use the same zero orientation, so
every polarised part must be checked in the JLC placement preview against orientation_check.md; this
script cannot see JLC's preview.

Usage: python3 gen_production.py
"""
import csv
import datetime as dt
import json
import os
import shutil
import subprocess
import zipfile

import pcbnew

import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
PCB = os.path.join(HW, "kicad", D.PROJECT + ".kicad_pcb")
OUT = os.path.join(HW, "production")
GERB = os.path.join(OUT, "gerbers")
SNAP = os.path.join(OUT, "jlc_parts_snapshot.jsonl")
LAYERS = "F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"

# parts whose orientation matters, with what pad 1 is
POLARISED = {
    "U": "pin 1",
    "Q": "pin 1 (gate)",
    "D3": "pad 1 = cathode",
    "C5": "pad 1 = + (base-plate chamfers on this side; the can marking is on the - side)",
    "BT": "pad 1 = + terminal (silkscreen '+')",
}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit("failed: %s\n%s%s" % (" ".join(cmd), r.stdout, r.stderr))
    return r.stdout


def fab_files():
    if os.path.isdir(GERB):
        shutil.rmtree(GERB)
    os.makedirs(GERB)
    run(["kicad-cli", "pcb", "export", "gerbers", "--layers", LAYERS, "--use-drill-file-origin",
         "--subtract-soldermask", "-o", GERB + "/", PCB])
    run(["kicad-cli", "pcb", "export", "drill", "--format", "excellon", "--drill-origin", "plot",
         "--excellon-units", "mm", "--excellon-separate-th", "--generate-map", "--map-format", "pdf",
         "-o", GERB + "/", PCB])
    z = os.path.join(OUT, "th_sensor_h2_rev%s_gerbers.zip" % D.REV)
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(os.listdir(GERB)):
            if not f.endswith(".pdf"):
                zf.write(os.path.join(GERB, f), f)
    return sorted(os.listdir(GERB))


def snapshot():
    out = {}
    for line in open(SNAP):
        r = json.loads(line)
        out[r["code"]] = r
    return out


def bom(snap):
    groups = {}
    for p in D.PARTS:
        if not p["in_bom"] or p["dnp"] or not p["on_board"]:
            continue
        key = (p["value"], p["footprint"], p["lcsc"])
        groups.setdefault(key, []).append(p["ref"])
    rows = []
    for (value, fp, lcsc), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
        part = next(p for p in D.PARTS if p["ref"] == refs[0])
        s = snap.get(lcsc, {})
        lib = s.get("library", "?")
        lib = {"base": "Basic", "expand": "Extended"}.get(lib.split("+")[0], lib) + (
            " (preferred)" if "+preferred" in lib else "")
        rows.append({
            "Comment": value + (" " + part["spec"] if part["spec"] else ""),
            "Designator": ",".join(sorted(refs, key=natural)),
            "Footprint": fp.split(":")[1],
            "LCSC Part #": lcsc,
            "Manufacturer": part["mfr"],
            "MPN": part["mpn"],
            "Qty": len(refs),
            "JLC library": lib,
            "JLC stock": s.get("stock", "?"),
            "Stock checked": s.get("queried", "?"),
        })
    with open(os.path.join(OUT, "bom_jlc.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return rows


def natural(ref):
    import re
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return (m.group(1), int(m.group(2))) if m else (ref, 0)


def cpl(board):
    """JLC CPL from the board (fitted SMD parts and the holders), drill/place origin, mm, Y up."""
    aux = board.GetDesignSettings().GetAuxOrigin()
    excluded = {p["ref"] for p in D.PARTS if p["dnp"] or not p["in_bom"]}
    rows, checks = [], []
    for fp in sorted(board.GetFootprints(), key=lambda f: natural(f.GetReference())):
        ref = fp.GetReference()
        if ref in excluded or fp.IsExcludedFromPosFiles():
            continue
        pos = fp.GetPosition()
        x = pcbnew.ToMM(pos.x - aux.x)
        y = -pcbnew.ToMM(pos.y - aux.y)
        rot = fp.GetOrientationDegrees() % 360
        rows.append({"Designator": ref, "Mid X": "%.3f" % x, "Mid Y": "%.3f" % y, "Layer": "Top",
                     "Rotation": "%g" % rot})
        kind = next((v for k, v in POLARISED.items() if ref == k or (len(k) <= 2 and ref.startswith(k)
                                                                    and ref[len(k):].isdigit())), None)
        if kind:
            p1 = next(p for p in fp.Pads() if p.GetNumber() == "1")
            d = p1.GetPosition() - pos
            dx, dy = pcbnew.ToMM(d.x), -pcbnew.ToMM(d.y)
            side = []
            if abs(dx) > 0.05:
                side.append("right" if dx > 0 else "left")
            if abs(dy) > 0.05:
                side.append("up" if dy > 0 else "down")
            checks.append((ref, fp.GetValue(), "%g" % rot, kind, " / ".join(side) or "centre",
                           "%.2f, %.2f" % (dx, dy)))
    with open(os.path.join(OUT, "cpl_jlc.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(OUT, "orientation_check.md"), "w") as f:
        f.write("# Orientation check for the JLC placement preview\n\n")
        f.write("Generated by `hardware/scripts/gen_production.py` from the board file. Board viewed from the top,\n"
                "X to the right, Y up (CPL convention). For each polarised part the offset of pad 1 from the part\n"
                "centre is given; in the JLC preview the pin-1 / polarity mark of the part model must sit on that\n"
                "side. If it does not, correct the rotation in JLC's tool (not in KiCad) and record it here.\n\n")
        f.write("| Ref | Value | KiCad rotation | Pad 1 | Pad 1 direction | Pad 1 offset X, Y (mm) |\n")
        f.write("|---|---|---|---|---|---|\n")
        for c in checks:
            f.write("| %s | %s | %s | %s | %s | %s |\n" % c)
    return rows, checks


def assembly_pdf():
    run(["kicad-cli", "pcb", "export", "pdf", "--layers", "F.Fab,Edge.Cuts", "--include-border-title",
         "--mode-single", "-o", os.path.join(OUT, "assembly_top.pdf"), PCB])


def blockers(rows, snap):
    stamp = next(iter(snap.values())).get("queried", "?")
    lines = ["# Manufacturing blockers and open checks (Rev %s)" % D.REV, "",
             "Status from the JLC parts snapshot taken %s (`jlc_parts_snapshot.jsonl`)." % stamp,
             "Nothing here has been ordered. Re-run `tools/jlc_lookup.py` and this script before ordering.", "",
             "## Blocking", ""]
    for r in rows:
        if str(r["JLC stock"]) in ("0", "?"):
            lines.append("- **%s (%s, %s)**: JLC stock %s. Options: consigned parts (JLC global sourcing or "
                         "customer-supplied), or order the bare PCB + JLC assembly without it and hand-solder "
                         "it (docs/assembly.md)." % (r["Designator"], r["MPN"], r["LCSC Part #"], r["JLC stock"]))
    low = [r for r in rows if str(r["JLC stock"]).isdigit() and 0 < int(r["JLC stock"]) < 1000]
    lines += ["", "## Low stock (< 1000 at snapshot time)", ""]
    lines += ["- %s (%s, %s): %s pcs" % (r["Designator"], r["MPN"], r["LCSC Part #"], r["JLC stock"]) for r in low] \
        or ["- none"]
    ext = [r for r in rows if r["JLC library"].startswith("Extended")]
    lines += ["", "## Extended parts (each adds JLC's extended-part setup fee)", ""]
    lines += ["- %s: %s (%s)" % (r["Designator"], r["MPN"], r["LCSC Part #"]) for r in ext]
    n_tp = sum(1 for p in D.PARTS if p["ref"].startswith("TP"))
    lines += ["", "## Checks that need a person", "",
              "- Placement preview: every line of `orientation_check.md` (holder, electrolytic, LED, ICs, "
              "MOSFETs).",
              "- Holder BT1 (MYOUNG BS-24-B4AA016): its + terminal must sit on pad 1, at the silkscreen '+' "
              "(right). The footprint is drawn from the LCSC datasheet; compare it with a real part first "
              "(docs/assembly.md).",
              "- C5 (470 uF electrolytic): + pad up, towards the converter; reversed, it leaks heavily, drains the cell "
              "and degrades.",
              "- J1 is not fitted / not in the BOM (debug pads only).",
              "- Test pads TP1..TP%d (silkscreen shows their net names) and fiducials have no parts." % n_tp,
              "- PCB options: 2 layers, 1.6 mm FR-4, 1 oz, tented vias (set in the board file), "
              "lead-free HASL or ENIG. The SHT40 tongue is cut free by a 1 mm L-shaped slot that "
              "opens into the antenna notch (routed, not V-cut).",
              "- Nothing here proves the design works: see docs/test_plan.md (no prototype has been built)."]
    with open(os.path.join(OUT, "manufacturing_blockers.md"), "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    files = fab_files()
    snap = snapshot()
    rows = bom(snap)
    board = pcbnew.LoadBoard(PCB)
    cpl_rows, checks = cpl(board)
    assembly_pdf()
    blockers(rows, snap)
    print("gerbers/drill:", ", ".join(files))
    print("BOM lines:", len(rows), " placed parts:", len(cpl_rows), " orientation checks:", len(checks))


if __name__ == "__main__":
    main()
