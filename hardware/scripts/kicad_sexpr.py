"""
Minimal helpers for KiCad 9 S-expression files (symbol libraries, schematics).

Only what gen_schematic.py needs: extract a symbol block from a .kicad_sym
library, flatten 'extends' inheritance, read pin geometry, and format UUIDs.
"""
import math
import re
import uuid as _uuid

KICAD_SYMBOL_DIR = "/usr/share/kicad/symbols"


def new_uuid(seed=None):
    """Deterministic UUIDs (uuid5 of a seed string) keep regenerated files diff-friendly."""
    if seed is None:
        return str(_uuid.uuid4())
    return str(_uuid.uuid5(_uuid.NAMESPACE_URL, "th-sensor-h2/" + seed))


def find_block(text, head):
    """Return the balanced S-expression starting with `head` (e.g. '(symbol "R"')."""
    i = text.find(head)
    if i < 0:
        raise KeyError(head)
    depth = 0
    in_str = False
    esc = False
    for j in range(i, len(text)):
        ch = text[j]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return text[i:j + 1]
    raise ValueError("unbalanced block " + head)


def top_level_children(block):
    """Split the direct children of a block into a list of strings (strings are skipped)."""
    out = []
    depth = 0
    in_str = False
    esc = False
    start = None
    for j, ch in enumerate(block):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "(":
            depth += 1
            if depth == 2:
                start = j
        elif ch == ")":
            if depth == 2 and start is not None:
                out.append(block[start:j + 1])
                start = None
            depth -= 1
    return out


def downgrade_v10_symbol(block):
    """Make a KiCad 10 (format 2025-10) symbol readable by KiCad 9: drop tokens KiCad 9
    does not know and move property-level (hide yes) into the effects block."""
    block = re.sub(r'\s*\((?:in_pos_files|duplicate_pin_numbers_are_jumpers|show_name|do_not_autoplace) (?:yes|no)\)',
                   "", block)
    out = []
    pos = 0
    for m in re.finditer(r'\(property "', block):
        if m.start() < pos:
            continue
        prop = find_block(block[m.start():], '(property "')
        kids = top_level_children(prop)
        if any(k == "(hide yes)" for k in kids):
            new_kids = [k for k in kids if k != "(hide yes)"]
            new_kids = [k[:-1].rstrip() + " (hide yes))" if k.startswith("(effects") else k for k in new_kids]
            head = prop[:prop.index(kids[0])]
            prop_new = head + " ".join(new_kids) + ")"
        else:
            prop_new = prop
        out.append(block[pos:m.start()])
        out.append(prop_new)
        pos = m.start() + len(prop)
    out.append(block[pos:])
    return "".join(out)


class SymbolSource:
    """A symbol taken from a .kicad_sym file, flattened, ready to embed."""

    def __init__(self, lib_path, name, lib_nick, new_name=None, overrides=None):
        text = open(lib_path, encoding="utf-8").read()
        block = find_block(text, '(symbol "%s"' % name)
        if re.search(r'\(version 2025(?:0[2-9]|1)', text[:200]):
            block = downgrade_v10_symbol(block)
        m = re.search(r'\(extends "([^"]+)"\)', block)
        if m:
            parent = find_block(text, '(symbol "%s"' % m.group(1))
            block = self._flatten(parent, m.group(1), block, name)
        self.name = new_name or name
        if self.name != name:
            block = block.replace('(symbol "%s"' % name, '(symbol "%s"' % self.name, 1)
            block = re.sub(r'\(symbol "%s_(\d+)_(\d+)"' % re.escape(name), r'(symbol "%s_\1_\2"' % self.name, block)
        self.lib_nick = lib_nick
        self.block = block
        if overrides:
            for k, v in overrides.items():
                self.set_property(k, v)
        self.pins = self._pins()

    @staticmethod
    def _flatten(parent, parent_name, child, child_name):
        kids = top_level_children(child)
        child_props = [k for k in kids if k.startswith("(property ")]
        pkids = top_level_children(parent)
        body = [k for k in pkids if not k.startswith("(property ")]
        body = [re.sub(r'\(symbol "%s_(\d+)_(\d+)"' % re.escape(parent_name), r'(symbol "%s_\1_\2"' % child_name, k)
                for k in body]
        return '(symbol "%s"\n' % child_name + "\n".join(child_props + body) + "\n)"

    def set_property(self, key, value):
        pat = re.compile(r'\(property "%s" "((?:[^"\\]|\\.)*)"' % re.escape(key))
        if pat.search(self.block):
            self.block = pat.sub(lambda _m: '(property "%s" "%s"' % (key, value), self.block, count=1)
        else:
            raise KeyError(key)

    def _pins(self):
        pins = []
        for m in re.finditer(r'\(pin (\w+) (\w+)\s*\(at ([-0-9.]+) ([-0-9.]+) ([-0-9.]+)\)\s*\(length ([-0-9.]+)\)',
                             self.block):
            rest = self.block[m.end():m.end() + 400]
            name = re.search(r'\(name "([^"]*)"', rest).group(1)
            number = re.search(r'\(number "([^"]*)"', rest).group(1)
            hidden = bool(re.match(r'\s*\(hide yes\)', rest)) or bool(re.match(r'\s*hide', rest))
            pins.append(dict(type=m.group(1), x=float(m.group(3)), y=float(m.group(4)), angle=float(m.group(5)),
                             length=float(m.group(6)), name=name, number=number, hidden=hidden))
        return pins

    def embedded(self):
        """Block for the schematic lib_symbols section (lib_id = nick:name)."""
        return self.block.replace('(symbol "%s"' % self.name, '(symbol "%s:%s"' % (self.lib_nick, self.name), 1)

    def library_entry(self):
        return self.block


def transform(px, py, x, y, rot):
    """Symbol-local point (y up) to schematic coordinates (y down) for rotation rot (ccw)."""
    a = math.radians(rot)
    rx = px * math.cos(a) - py * math.sin(a)
    ry = px * math.sin(a) + py * math.cos(a)
    return (round(x + rx, 4), round(y - ry, 4))


def outward_dir(pin_angle, rot):
    """Unit vector (schematic frame) pointing away from the symbol body at a pin end."""
    a = math.radians(pin_angle + 180.0 + rot)
    return (round(math.cos(a)), round(-math.sin(a)))


def fmt(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s
