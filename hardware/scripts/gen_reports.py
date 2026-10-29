#!/usr/bin/env python3
"""
Check reports and pictures for TH-SENSOR-H2, all produced by KiCad's own command line tool:

  hardware/reports/erc_report.txt      ERC, all severities
  hardware/reports/drc_report.txt      DRC with schematic parity, all severities
  hardware/reports/summary.md          counts, tool version, date
  hardware/renders/schematic.pdf
  hardware/renders/pcb_top.svg, pcb_bottom.svg       copper + silkscreen
  hardware/renders/pcb_3d_top.png, pcb_3d_bottom.png, pcb_3d_iso.png

Only the module has a 3D model in this repository (Espressif library); the other parts render as bare
footprints because the KiCad 3D model package is not installed here.

Usage: python3 gen_reports.py   (after gen_schematic.py and gen_pcb.py)
"""
import datetime as dt
import os
import re
import subprocess

import design as D

HERE = os.path.dirname(os.path.abspath(__file__))
HW = os.path.normpath(os.path.join(HERE, ".."))
SCH = os.path.join(HW, "kicad", D.PROJECT + ".kicad_sch")
PCB = os.path.join(HW, "kicad", D.PROJECT + ".kicad_pcb")
REP = os.path.join(HW, "reports")
REN = os.path.join(HW, "renders")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    os.makedirs(REP, exist_ok=True)
    os.makedirs(REN, exist_ok=True)
    erc = os.path.join(REP, "erc_report.txt")
    drc = os.path.join(REP, "drc_report.txt")
    run(["kicad-cli", "sch", "erc", "--severity-all", "-o", erc, SCH])
    run(["kicad-cli", "pcb", "drc", "--severity-all", "--schematic-parity", "-o", drc, PCB])
    run(["kicad-cli", "sch", "export", "pdf", "-o", os.path.join(REN, "schematic.pdf"), SCH])
    for side, layers in (("top", "F.Cu,F.SilkS,F.Mask,Edge.Cuts"), ("bottom", "B.Cu,B.SilkS,B.Mask,Edge.Cuts")):
        cmd = ["kicad-cli", "pcb", "export", "svg", "--layers", layers, "--mode-single", "--fit-page-to-board",
               "--exclude-drawing-sheet", "-o", os.path.join(REN, "pcb_%s.svg" % side), PCB]
        if side == "bottom":
            cmd = cmd[:4] + ["--mirror"] + cmd[4:]
        run(cmd)
    for name, extra in (("top", ["--side", "top"]), ("bottom", ["--side", "bottom"]),
                        ("iso", ["--side", "top", "--rotate", "-40,0,25", "--perspective", "--zoom", "0.9"])):
        run(["kicad-cli", "pcb", "render", "--width", "1600", "--height", "1300", "--quality", "basic"] + extra +
            ["-o", os.path.join(REN, "pcb_3d_%s.png" % name), PCB])
    _, ver = run(["kicad-cli", "version"])
    e = open(erc).read()
    d = open(drc).read()
    erc_n = re.search(r"ERC messages: (\d+)\s+Errors (\d+)\s+Warnings (\d+)", e)
    drc_v = re.search(r"Found (\d+) DRC violations", d)
    drc_u = re.search(r"Found (\d+) unconnected pads", d)
    drc_f = re.search(r"Found (\d+) Footprint errors", d)
    lines = ["# Check summary", "",
             "Generated %s by `hardware/scripts/gen_reports.py` with kicad-cli %s." % (
                 dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"), ver.strip()), "",
             "| Check | Result | Report |", "|---|---|---|",
             "| ERC (all severities) | %s messages, %s errors, %s warnings | erc_report.txt |" % erc_n.groups(),
             "| DRC (all severities) | %s violations | drc_report.txt |" % drc_v.group(1),
             "| DRC unconnected pads | %s | drc_report.txt |" % drc_u.group(1),
             "| Schematic parity (footprints vs schematic) | %s footprint errors | drc_report.txt |" % drc_f.group(1),
             "", "Routing log: routing_log.txt (gen_pcb.py). These are design-rule checks only; no board has "
             "been made or tested."]
    with open(os.path.join(REP, "summary.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
