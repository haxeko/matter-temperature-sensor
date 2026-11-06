#!/usr/bin/env python3
"""Cross-check firmware/components/board/include/board_pins.h against the KiCad netlist.

Every `#define BOARD_GPIO_* <gpio>  /* module pad <n>, net <NET> ... */` must satisfy:
  - module pad <n> is GPIO <gpio> on the ESP32-H2-MINI-1 (datasheet v1.6, table 3 "Pin Description"),
  - the schematic connects U4 pad <n> to net <NET>.
ADC channel defines must match the ESP32-H2 ADC1 mapping, and every GPIO in
BOARD_UNUSED_GPIO_LIST must sit on a module pad the schematic leaves unconnected.

With --variant chip the same header is checked against the bare-chip board (TH-SENSOR-H2C,
hardware/chip/kicad): GPIO <gpio> must sit on the QFN32 pin of the ESP32-H2 datasheet v1.3 pin table and
that pin must carry <NET> (the firmware is shared by both boards).

Usage:
    tools/check_pinmap.py                 # exit 1 on any mismatch
    tools/check_pinmap.py --variant chip  # the bare-chip board
    tools/check_pinmap.py --markdown      # also print the pin table used in docs/pinmap.md
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
PINS_H = os.path.join(ROOT, "firmware", "components", "board", "include", "board_pins.h")
SCH = os.path.join(ROOT, "hardware", "kicad", "th_sensor_h2.kicad_sch")
SCH_CHIP = os.path.join(ROOT, "hardware", "chip", "kicad", "th_sensor_h2c.kicad_sch")

# ESP32-H2-MINI-1 / MINI-1U datasheet v1.6, table 3: module pad -> GPIO
PAD_GPIO = {5: 2, 6: 3, 9: 0, 10: 1, 12: 13, 13: 14, 16: 12, 18: 4, 19: 5, 20: 10, 21: 11, 22: 8, 23: 9,
            24: 22, 25: 25, 26: 26, 27: 27, 30: 23, 31: 24}
# ESP32-H2 ADC1 channels (same table): GPIO -> channel
ADC1 = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4}
# ESP32-H2 chip, QFN32 (datasheet v1.3, pin table): GPIO -> pin number
CHIP_GPIO_PIN = {0: 3, 1: 4, 2: 5, 3: 6, 4: 7, 5: 8, 8: 10, 9: 11, 10: 12, 11: 13, 12: 14, 13: 15, 14: 16,
                 22: 21, 23: 22, 24: 23, 25: 24, 26: 25, 27: 26}


def netlist_u4(sch=SCH):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "n.net")
        subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, sch],
                       check=True, capture_output=True)
        text = open(out).read()
    pads = {}
    for ch in re.split(r'\(net \(code "\d+"\) ', text[text.index("(nets"):])[1:]:
        name = re.match(r'\(name "([^"]+)"\)', ch).group(1)
        for m in re.finditer(r'\(node \(ref "U4"\) \(pin "(\d+)"\)', ch):
            pads[int(m.group(1))] = name.lstrip("/")
    return pads


def parse_header():
    defs = {}
    for line in open(PINS_H):
        m = re.match(r"#define\s+(BOARD_\w+)\s+(.+?)\s*(?:/\*(.*)\*/)?\s*$", line)
        if m:
            defs[m.group(1)] = (m.group(2).strip(), (m.group(3) or "").strip())
    return defs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--markdown", action="store_true")
    ap.add_argument("--variant", choices=("module", "chip"), default="module")
    a = ap.parse_args()
    defs = parse_header()
    if a.variant == "chip":
        return check_chip(defs, netlist_u4(SCH_CHIP), a.markdown)
    u4 = netlist_u4()
    errors, rows = [], []
    gpio_of = {}
    for name, (val, comment) in defs.items():
        if not name.startswith("BOARD_GPIO_"):
            continue
        gpio = int(val)
        gpio_of[name] = gpio
        m = re.search(r"module pad (\d+)", comment)
        if not m:
            errors.append("%s: no 'module pad N' in the comment" % name)
            continue
        pad = int(m.group(1))
        if PAD_GPIO.get(pad) != gpio:
            errors.append("%s = GPIO%d but module pad %d is GPIO%s" % (name, gpio, pad, PAD_GPIO.get(pad)))
        mn = re.search(r"net (\w+)", comment)
        net = u4.get(pad, "")
        if mn:
            if net != mn.group(1):
                errors.append("%s: header says net %s, schematic has %s on U4 pad %d" % (name, mn.group(1), net, pad))
        elif net and not net.startswith("unconnected-"):
            errors.append("%s: pad %d carries net %s in the schematic, header names none" % (name, pad, net))
        rows.append((pad, gpio, name, net or "-"))
    for n, chan_def in (("BOARD_GPIO_VBAT_SENSE", "BOARD_VBAT_ADC_CHANNEL"),):
        g = gpio_of.get(n)
        ch = int(defs[chan_def][0]) if chan_def in defs else None
        if ADC1.get(g) != ch:
            errors.append("%s = %s but GPIO%s is ADC1 channel %s" % (chan_def, ch, g, ADC1.get(g)))
    unused = [int(x) for x in re.findall(r"\d+", defs.get("BOARD_UNUSED_GPIO_LIST", ("", ""))[0])]
    gpio_pad = {g: p for p, g in PAD_GPIO.items()}
    for g in unused:
        p = gpio_pad.get(g)
        net = u4.get(p, "")
        if p is None:
            errors.append("unused GPIO%d is not on a module pad" % g)
        elif net and not net.startswith("unconnected-"):
            errors.append("unused GPIO%d (pad %d) is connected to %s" % (g, p, net))
        rows.append((p, g, "unused (input off, pull-down)", "-"))
    used_pads = {r[0] for r in rows}
    for p, g in PAD_GPIO.items():
        net = u4.get(p, "")
        if p not in used_pads and net and not net.startswith("unconnected-"):
            errors.append("U4 pad %d (GPIO%d) carries %s but board_pins.h does not mention it" % (p, g, net))
    if a.markdown:
        print("| Module pad | GPIO | board_pins.h | Net |")
        print("|---|---|---|---|")
        for pad, gpio, name, net in sorted(rows):
            print("| %s | GPIO%d | `%s` | %s |" % (pad, gpio, name, net))
    if errors:
        print("\n".join("MISMATCH: " + e for e in errors), file=sys.stderr)
        return 1
    print("pin map OK: %d defines, %d unused GPIOs checked against the schematic" % (len(gpio_of), len(unused)),
          file=sys.stderr)
    return 0


def check_chip(defs, u4, markdown):
    """Bare-chip board: the GPIO numbers of board_pins.h on the QFN32 pins, nets from the header comments."""
    errors, rows = [], []
    gpio_of = {}
    for name, (val, comment) in defs.items():
        if not name.startswith("BOARD_GPIO_"):
            continue
        gpio = int(val)
        gpio_of[name] = gpio
        pin = CHIP_GPIO_PIN.get(gpio)
        if pin is None:
            errors.append("%s = GPIO%d: not a GPIO pin of the ESP32-H2 QFN32" % (name, gpio))
            continue
        net = u4.get(pin, "")
        mn = re.search(r"net (\w+)", comment)
        if mn and net != mn.group(1):
            errors.append("%s: header says net %s, chip schematic has %s on U4 pin %d" % (name, mn.group(1), net, pin))
        rows.append((pin, gpio, name, net or "-"))
    g = gpio_of.get("BOARD_GPIO_VBAT_SENSE")
    ch = int(defs["BOARD_VBAT_ADC_CHANNEL"][0]) if "BOARD_VBAT_ADC_CHANNEL" in defs else None
    if ADC1.get(g) != ch:
        errors.append("BOARD_VBAT_ADC_CHANNEL = %s but GPIO%s is ADC1 channel %s" % (ch, g, ADC1.get(g)))
    unused = [int(x) for x in re.findall(r"\d+", defs.get("BOARD_UNUSED_GPIO_LIST", ("", ""))[0])]
    for gpio in unused:
        pin = CHIP_GPIO_PIN.get(gpio)
        net = u4.get(pin, "")
        if pin is None:
            errors.append("unused GPIO%d is not a chip GPIO pin" % gpio)
        elif net and not net.startswith("unconnected-"):
            errors.append("unused GPIO%d (pin %d) is connected to %s" % (gpio, pin, net))
        rows.append((pin, gpio, "unused (input off, pull-down)", "-"))
    used = {r[0] for r in rows}
    for gpio, pin in CHIP_GPIO_PIN.items():
        net = u4.get(pin, "")
        if pin not in used and net and not net.startswith("unconnected-"):
            errors.append("U4 pin %d (GPIO%d) carries %s but board_pins.h does not mention it" % (pin, gpio, net))
    if markdown:
        print("| Chip pin | GPIO | board_pins.h | Net |")
        print("|---|---|---|---|")
        for pin, gpio, name, net in sorted(rows):
            print("| %s | GPIO%d | `%s` | %s |" % (pin, gpio, name, net))
    if errors:
        print("\n".join("MISMATCH: " + e for e in errors), file=sys.stderr)
        return 1
    print("pin map OK (chip): %d defines, %d unused GPIOs checked against the chip schematic"
          % (len(gpio_of), len(unused)), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
