#!/usr/bin/env python3
"""
Time-domain and energy model of the TH-SENSOR-H2 power path.

STATUS: ESTIMATE (ƯỚC TÍNH). Nothing here is a measurement. Every input is an
assumption with a source; bring-up measurements (docs/test_plan.md) replace them.

Rev B (current design) runs from ONE CR2450: architecture S below, results first in
results/power_model_summary.md. The two-CR2032 comparison (A2/A1/B/C, Rev A) is kept as
the record of how the power path was chosen; the same circuit with one CR2032 is
included to show why the cell was changed (boot and commissioning fail).

Architectures compared (same cells, same load profiles, same capacitors):

  A2  prompt default "VBAT_OR": per cell 2 Schottky in series (RB521S30 + B5819W,
      the "protective diode" pair of the Panasonic/UL guidance) into one VBAT_OR
      node, one TPS63900 (3.3 V) -> 3V3.
  A1  as A2 with a single Schottky (B5819W) per cell (no second barrier).
  B   one TPS63900 (3.3 V) per cell, outputs paralleled (datasheet: "Stackable:
      parallel multiple devices"), Schottky in front of each converter.
  C   Rev A choice: one TPS63900 per cell set to 3.4 V, P-MOSFET (AO3401A) at the
      input for reverse polarity, B5819W from each converter output to the 3V3
      rail. Barriers against charging a cell: (1) the converter (4-switch
      topology, does not switch while VOUT is above target: no body-diode path
      VOUT->VIN) and (2) the output Schottky. The Schottky drop is taken at the
      rail (3.07-3.33 V, inside the module's 3.0-3.6 V range) instead of at the
      converter input, so the cell can sag to the 1.65 V UVLO before dropping out.
  C50 C with a 50 mA input current limit (VO(2) = 3.4 V: RCFG1 0 Ohm, RCFG2 13.3 kOhm).
  B0  B with a P-MOSFET instead of the Schottky: no second barrier (reference).
  S   Rev B: ONE cell, P-MOSFET at the input, one TPS63900 at 3.3 V (SEL = low,
      VO(1) from RCFG3 16.2 kOhm; 100 mA input limit from RCFG1 0 Ohm / RCFG2
      10.5 kOhm), converter output = 3V3 rail (no output diode: nothing else can
      feed the rail, so there is nothing to OR). S_xxx variants: same with a
      larger effective input buffer of xxx uF.

Inputs and their sources (discussion in docs/power_budget.md):
  * ESP32-H2-MINI-1 currents: module datasheet v1.6 (3.3 V, 25 degC):
    802.15.4 TX +7 dBm 54 mA, -2 dBm 38 mA, RX 29 mA; BLE TX +7 dBm 55 mA.
    Firmware sets +5 dBm (802.15.4) -> 50 mA assumed.
  * Sleep floor 27 uA: Espressif ESP32-H2 ICD measurement
    (esp-matter examples/icd_app, image sit_icd_*.png).
  * Thread poll charge 0.25 mC: Espressif measured 0.31-0.40 mC per poll at
    20 dBm; scaled for +5 dBm.
  * CR2032: pulse resistance 10..45 Ohm vs used capacity (TI SWRA349 fig. 6),
    DC polarisation fitted to Panasonic CR2032 datasheet (Feb 2026) "operating
    voltage vs load resistance" (1 kOhm at 50 % DoD: ~2.75 V at 20 degC,
    ~2.4 V at -10 degC).
  * Diodes: Shockley fits to onsemi RB521S30T1G rev. 9 fig. 1/2 and JSCJ B5819W.
  * TPS63900 SLVSET3D: UVLO 1.75 V rising / 1.65 V falling, average input current
    limit 100 mA (table 7-2, VO(2) = 3.4 V: RCFG1 0 Ohm, RCFG2 10.5 kOhm),
    efficiency: TI's own design rule "use ... 0.9 as an assumption"; 75 nA IQ.
  * Commissioning load: NO Espressif measurement found; three assumed profiles
    (optimistic / nominal / pessimistic) are simulated.

Usage: python3 power_model.py [--outdir DIR] [--plots] [--quick]
"""
import argparse
import json
import math
import os
from dataclasses import dataclass, field, replace

VT25 = 0.02569  # thermal voltage at 25 degC [V]


# ---------------------------------------------------------------- components
@dataclass(frozen=True)
class Diode:
    name: str
    i_s: float        # saturation current at 25 degC [A]
    n: float          # ideality factor
    r_s: float        # series resistance [Ohm]
    r_leak: float     # reverse leakage modelled as a resistor at 25 degC [Ohm]

    def vf(self, i, dt_c=0.0):
        if i <= 0:
            return 0.0
        vt = VT25 * (298.15 + dt_c) / 298.15
        i_s = self.i_s * 2 ** (dt_c / 10.0)
        return self.n * vt * math.log(i / i_s + 1.0) + i * self.r_s

    def i_of_v(self, v, dt_c=0.0, i_guess=1e-4):
        """Forward current [A] and conductance dI/dV [S] at forward voltage v."""
        if v <= 0:
            return 0.0, 1.0 / (self.r_leak * 2 ** (-dt_c / 10.0))
        vt = VT25 * (298.15 + dt_c) / 298.15
        i_s = self.i_s * 2 ** (dt_c / 10.0)
        # start from the exponential-only solution, then Newton on the full equation
        i = min(max(i_guess, 1e-12), i_s * math.expm1(min(v / (self.n * vt), 60.0)))
        for _ in range(40):
            f = self.n * vt * math.log(i / i_s + 1.0) + i * self.r_s - v
            df = self.n * vt / (i + i_s) + self.r_s
            i_new = max(i - f / df, i * 0.1)
            if abs(i_new - i) < 1e-12 + 1e-8 * i:
                i = i_new
                break
            i = i_new
        return i, 1.0 / (self.n * vt / (i + i_s) + self.r_s)


# onsemi RB521S30T1G: ~0.16 V @ 10 uA, 0.28 V @ 1 mA, 0.36 V @ 10 mA; IR ~0.5 uA @ 1 V, 25 degC
RB521S30 = Diode("RB521S30T1G", i_s=2.1e-8, n=1.0, r_s=0.8, r_leak=2.0e6)
# JSCJ B5819W: 1 A / 40 V SOD-123, ~0.28 V @ 0.1 A; IR ~5 uA @ 1 V, 25 degC
B5819W = Diode("B5819W", i_s=2.0e-6, n=1.05, r_s=0.10, r_leak=2.0e5)


@dataclass(frozen=True)
class Cell:
    """CR2032 equivalent circuit: OCV - I*R_ohm - V_p1 - V_p2.
    V_p1: fast linear RC polarisation. V_p2: slow polarisation with steady state
    b2*ln(1 + I/1 mA) (Tafel-like), fitted to the Panasonic DC load curve."""
    name: str
    ocv: float
    r_ohm: float
    r_p1: float
    tau1: float
    b2: float
    tau2: float
    present: bool = True
    i_ref: float = 1e-3    # Tafel reference current of V_p2 (scales with electrode area)


CELL_STATES = {
    # state: OCV, pulse R (SWRA349 fig. 6: ~10 Ohm new, ~20 Ohm at ~60 %, >40 Ohm near the knee)
    "fresh": dict(ocv=3.10, r_ohm=12.0, r_p1=6.0, tau1=0.05, b2=0.12, tau2=20.0),
    "mid":   dict(ocv=3.00, r_ohm=18.0, r_p1=9.0, tau1=0.05, b2=0.18, tau2=20.0),
    "late":  dict(ocv=2.90, r_ohm=40.0, r_p1=20.0, tau1=0.05, b2=0.30, tau2=20.0),
    "eol":   dict(ocv=2.75, r_ohm=100.0, r_p1=50.0, tau1=0.05, b2=0.50, tau2=20.0),
}


# Temperature scaling of the cell parameters: (R factor, b2 factor, OCV shift [V],
# junction offset vs 25 degC [K]). -10 degC from the Panasonic CR2032 curve
# (1 kOhm operating voltage 2.75 V at 20 degC -> 2.4 V at -10 degC); +10 and
# 0 degC are INTERPOLATED assumptions, not datasheet values.
TEMPS = {
    "25C": (1.0, 1.0, 0.0, 0.0),
    "10C": (1.3, 1.25, 0.01, -15.0),
    "0C": (1.7, 1.6, 0.03, -25.0),
    "-10C": (2.5, 2.2, 0.05, -35.0),
}


# Cell types. CR2032 parameters are the fitted ones above. CR2450 (Panasonic datasheet Feb 2026:
# 620 mAh, 0.2 mA continuous, 24.5 x 5.0 mm, -30..+85 degC) has no published pulse resistance: its
# resistances are the CR2032 ones scaled by the electrode-area ratio (inner diameters 17.0 vs 22.0 mm
# in the Panasonic drawings: (17/22)^2 = 0.60), and the Tafel reference current is scaled by the
# inverse ratio. ESTIMATE; r_scale 0.4 and 1.0 are run as optimistic / pessimistic bounds (Panasonic
# "capacity vs load" curves: CR2450 at 1 kOhm delivers 84 % of nominal, CR2032 69 %).
CELL_TYPES = {
    "CR2032": dict(nominal_mAh=225.0, r_scale=1.0, area_ratio=1.0),
    "CR2450": dict(nominal_mAh=620.0, r_scale=(17.0 / 22.0) ** 2, area_ratio=(22.0 / 17.0) ** 2),
}


def cell(state, temp="25C", ctype="CR2032", r_scale=None):
    t = CELL_TYPES[ctype]
    k = t["r_scale"] if r_scale is None else r_scale
    p = dict(CELL_STATES[state])
    rf, bf, docv, _ = TEMPS[temp]
    p.update(ocv=p["ocv"] - docv, r_ohm=p["r_ohm"] * rf * k, r_p1=p["r_p1"] * rf * k, b2=p["b2"] * bf,
             i_ref=1e-3 * t["area_ratio"])
    return Cell(name=f"{ctype} {state}@{temp}", **p)


SCENARIOS = {
    "fresh 25C":           (lambda: [cell("fresh"), cell("fresh")], 0.0),
    "mid-life 25C":        (lambda: [cell("mid"), cell("mid")], 0.0),
    "late 25C":            (lambda: [cell("late"), cell("late")], 0.0),
    "end-of-life 25C":     (lambda: [cell("eol"), cell("eol")], 0.0),
    "fresh 10C (interp.)": (lambda: [cell("fresh", "10C"), cell("fresh", "10C")], -15.0),
    "mid-life 10C (interp.)": (lambda: [cell("mid", "10C"), cell("mid", "10C")], -15.0),
    "fresh 0C (interp.)":  (lambda: [cell("fresh", "0C"), cell("fresh", "0C")], -25.0),
    "fresh -10C":          (lambda: [cell("fresh", "-10C"), cell("fresh", "-10C")], -35.0),
    "mid-life -10C":       (lambda: [cell("mid", "-10C"), cell("mid", "-10C")], -35.0),
    "one cell only (mid)": (lambda: [cell("mid"), replace(cell("mid"), present=False)], 0.0),
    "mismatch fresh+late": (lambda: [cell("fresh"), cell("late")], 0.0),
    # one converter per cell drains the leading cell first: asymmetric states
    "one cell only (fresh)": (lambda: [cell("fresh"), replace(cell("fresh"), present=False)], 0.0),
    "eol + fresh":         (lambda: [cell("eol"), cell("fresh")], 0.0),
    "late + mid":          (lambda: [cell("late"), cell("mid")], 0.0),
    "eol + mid":           (lambda: [cell("eol"), cell("mid")], 0.0),
}

# Rev B: one cell. Keys "<scenario>" use CR2450 with the central resistance scaling; the
# one-cell CR2032 case that led to the change is kept under "CR2032 ..." keys.
def _one(state, temp, ctype="CR2450", r_scale=None):
    return lambda: [cell(state, temp, ctype, r_scale)]


SCENARIOS_1 = {
    "fresh 25C":              (_one("fresh", "25C"), 0.0),
    "mid-life 25C":           (_one("mid", "25C"), 0.0),
    "late 25C":               (_one("late", "25C"), 0.0),
    "end-of-life 25C":        (_one("eol", "25C"), 0.0),
    "fresh 10C (interp.)":    (_one("fresh", "10C"), -15.0),
    "mid-life 10C (interp.)": (_one("mid", "10C"), -15.0),
    "fresh 0C (interp.)":     (_one("fresh", "0C"), -25.0),
    "mid-life 0C (interp.)":  (_one("mid", "0C"), -25.0),
    "fresh -10C":             (_one("fresh", "-10C"), -35.0),
    "mid-life -10C":          (_one("mid", "-10C"), -35.0),
    "CR2032 fresh 25C":       (_one("fresh", "25C", "CR2032"), 0.0),
    "CR2032 mid-life 25C":    (_one("mid", "25C", "CR2032"), 0.0),
}
for _st in ("fresh", "mid", "late"):
    for _k, _lab in ((0.4, "optimistic R x0.4"), (1.0, "pessimistic R x1.0")):
        SCENARIOS_1[f"{_st} 25C, {_lab}"] = (_one(_st, "25C", "CR2450", _k), 0.0)


# ---------------------------------------------------------------- architectures
@dataclass(frozen=True)
class Arch:
    key: str
    title: str
    node_c: tuple          # effective capacitance of each converter input node [F]
    branch_node: tuple     # input node of each cell branch
    series: tuple          # diodes in series in each cell branch
    r_extra: float         # holder contact + 0R link (+ P-MOSFET) per branch [Ohm]
    conv_node: tuple       # input node of each converter
    conv_vset: tuple       # converter set points (+/-1.5 % spread: one converter leads)
    i_lim: float = 0.100   # average input current limit per converter [A]
    c_out: float = 100e-6  # effective 3V3 capacitance [F]
    node_leak: float = 0.0 # leakage per input node [A]
    uvlo_on: float = 1.75
    uvlo_off: float = 1.65
    v_reset: float = 2.93  # TPS3839K33 threshold
    eta: float = 0.90
    iq: float = 75e-9
    out_series: object = None  # Schottky between each converter output and the 3V3 rail (topology C)
    n_cells: int = 2


C_IN_EACH = 85e-6   # 2 x 100 uF 1206 X5R 6.3 V at ~3 V (~40 % left, ASSUMED) + 10 uF 0603
ARCHS = {
    "A2": Arch("A2", "diode-OR, 2 Schottky/cell, 1 converter 3.3 V (prompt default)", node_c=(2 * C_IN_EACH,),
               branch_node=(0, 0), series=(RB521S30, B5819W), r_extra=0.05, conv_node=(0,), conv_vset=(3.30,)),
    "A1": Arch("A1", "diode-OR, 1 Schottky/cell, 1 converter 3.3 V", node_c=(2 * C_IN_EACH,),
               branch_node=(0, 0), series=(B5819W,), r_extra=0.05, conv_node=(0,), conv_vset=(3.30,)),
    "B":  Arch("B", "1 converter/cell 3.3 V, Schottky at each converter input", node_c=(C_IN_EACH, C_IN_EACH),
               branch_node=(0, 1), series=(B5819W,), r_extra=0.05, conv_node=(0, 1), conv_vset=(3.30, 3.27)),
    "C":  Arch("C", "1 converter/cell 3.4 V, P-MOSFET in, Schottky at each output (Rev A)",
               node_c=(C_IN_EACH, C_IN_EACH), branch_node=(0, 1), series=(), r_extra=0.15,
               conv_node=(0, 1), conv_vset=(3.40, 3.35), out_series=B5819W),
    "C50": Arch("C50", "as C with 50 mA input current limit", node_c=(C_IN_EACH, C_IN_EACH),
                branch_node=(0, 1), series=(), r_extra=0.15, conv_node=(0, 1), conv_vset=(3.40, 3.35),
                i_lim=0.050, out_series=B5819W),
    "B0": Arch("B0", "as B with P-MOSFET instead of Schottky (no 2nd barrier, reference)",
               node_c=(C_IN_EACH, C_IN_EACH), branch_node=(0, 1), series=(), r_extra=0.15,
               conv_node=(0, 1), conv_vset=(3.30, 3.27)),
    "S": Arch("S", "Rev B: 1 cell, P-MOSFET in, 1 converter 3.3 V, no output diode",
              node_c=(C_IN_EACH,), branch_node=(0,), series=(), r_extra=0.15, conv_node=(0,),
              conv_vset=(3.30,), n_cells=1),
}


# Rev B input buffer: 10 uF 0603 + 2 x 100 uF 1206 X5R (~85 uF at ~3 V, as Rev A) plus one
# 470 uF 6.3 V aluminium electrolytic (6.3 x 7.7 mm, as tall as the holder). Nominal 555 uF; 461 uF
# with the electrolytic at -20 % tolerance. A second 470 uF (or 1000 uF) keeps reports alive to late
# cell life at 25 degC (see the buffer sweep) but costs ~65 mm2 of board; Rev B favours size.
# Electrolytic leakage is specified only as <= 0.01 CV or 3 uA after 2 min at rated voltage
# (29.6 uA); at ~3 V after conditioning it is expected to be far lower, but no datasheet value
# exists: 0 / 1 / 5 uA are budgeted and test T-39 measures it.
REVB_C_IN_UF = 85 + 470
REVB_C_IN_MIN_UF = 85 + 470 * 0.8
REVB_LEAK_A = (0.0, 1e-6, 5e-6)
# usable charge of one CR2450 before reports start to fail (50 / 60 / 70 % of 620 mAh, ESTIMATE:
# with the Rev B buffer reports fail between the "mid-life" and "late" cell states)
REVB_USABLE_MAH = (310.0, 370.0, 435.0)


def single(c_in_uF):
    """Rev B arch with a given effective input buffer."""
    return replace(ARCHS["S"], key=f"S_{c_in_uF:g}", node_c=(c_in_uF * 1e-6,),
                   title=f"Rev B with {c_in_uF:g} uF effective input buffer")


# ---------------------------------------------------------------- load profiles
# A profile is a list of (duration_s, current_A at the 3.3 V rail).
SLEEP_A = 27e-6
TX_A = 50e-3       # 802.15.4 TX at +5 dBm (between the +7 dBm 54 mA and -2 dBm 38 mA table rows)
RX_A = 29e-3


def poll():
    """Thread data poll: wake, CCA, data request, ACK, short RX window (~0.25 mC)."""
    return [(0.006, 10e-3), (0.003, RX_A), (0.001, TX_A), (0.0015, RX_A), (0.001, 10e-3)]


def report():
    """Matter report: crypto, 3 x (CCA + 4 ms frame + ACK), then 1 s ICD active
    mode with two fast polls."""
    seq = [(0.010, 10e-3)]
    for _ in range(3):
        seq += [(0.0015, RX_A), (0.004, TX_A), (0.001, RX_A)]
    seq += [(0.5 - 0.0315, SLEEP_A)] + poll() + [(0.5 - 0.0125, SLEEP_A)] + poll()
    return seq


def measurement():
    """SHT40 high-repeatability measurement: CPU + I2C + sensor (~0.1 mC)."""
    return [(0.002, 8e-3), (0.009, 6e-3), (0.002, 8e-3)]


def boot():
    """Cold boot: ROM/bootloader/flash + app init, then radio calibration (ASSUMED)."""
    return [(0.30, 22e-3), (0.10, 45e-3), (0.40, 15e-3)]


def commissioning(bg_ma, rx_ma, seconds=90.0):
    """BLE PASE/CASE + Thread attach (ASSUMED, no published H2 measurement):
    background bg_ma (CPU + BLE connection events every 30 ms) and a 1 s
    receive window (parent search / MLE) every 10 s at rx_ma."""
    seq = []
    t = 0.0
    while t < seconds - 1e-9:
        if int(round(t, 6)) % 10 == 0 and abs(t - round(t)) < 1e-6:
            seq.append((1.0, rx_ma * 1e-3))
            t += 1.0
        else:
            seq += [(0.0285, max(bg_ma - 1.0, 0.5) * 1e-3), (0.0015, 35e-3)]
            t += 0.030
    return seq


def repeat(seq, n, gap_s, gap_a=SLEEP_A):
    out = []
    for _ in range(n):
        out += seq + [(gap_s, gap_a)]
    return out


COMMISSIONING = {
    "optimistic (6 mA bg, 30 mA RX)": (6.0, 30.0),
    "nominal (12 mA bg, 35 mA RX)": (12.0, 35.0),
    "pessimistic (20 mA bg, 41 mA RX)": (20.0, 41.0),
}

PROFILES = {
    "poll x5": lambda: repeat(poll(), 5, 0.5),
    "report + active mode": report,
    "boot": boot,
    "commissioning nominal": lambda: commissioning(*COMMISSIONING["nominal (12 mA bg, 35 mA RX)"]),
    "commissioning pessimistic": lambda: commissioning(*COMMISSIONING["pessimistic (20 mA bg, 41 mA RX)"]),
}


# ---------------------------------------------------------------- simulation engine
@dataclass
class Result:
    arch: str
    scenario: str
    profile: str
    v_in_min: list
    v_out_min: float
    uvlo: bool
    reset: bool
    t_reset_s: float
    i_cell_peak_mA: list
    i_rev_max_uA: float
    q_cells_mC: list
    trace: dict = field(default_factory=dict)


def _branch(c, vp1, vp2, v_node, arch, dt_c, i_guess):
    """Current from cell c into its input node [A] (negative = into the cell)
    and the small-signal conductance d(i)/d(-v_node) for the implicit update."""
    if not c.present:
        return 0.0, 0.0
    v_src = c.ocv - vp1 - vp2
    r = c.r_ohm + arch.r_extra
    if not arch.series:
        i = (v_src - v_node) / r
        return i, 1.0 / r
    if v_src <= v_node:
        r_leak = sum(d.r_leak * 2 ** (-dt_c / 10.0) for d in arch.series)
        return -(v_node - v_src) / (r_leak + r), 1.0 / (r_leak + r)
    vt = VT25 * (298.15 + dt_c) / 298.15
    scale = 2 ** (dt_c / 10.0)
    i = max(i_guess, 1e-9)
    g = 1.0 / r
    for _ in range(30):
        f = v_src - i * r - v_node
        df = -r
        for d in arch.series:
            i_s = d.i_s * scale
            f -= d.n * vt * math.log(i / i_s + 1.0) + i * d.r_s
            df -= d.n * vt / (i + i_s) + d.r_s
        i_new = i - f / df
        if i_new <= 0:
            i_new = i * 0.1
        g = -1.0 / df
        if abs(i_new - i) < 1e-10 + 1e-7 * i:
            i = i_new
            break
        i = i_new
    return i, g


def simulate(arch, cells, profile, dt=50e-6, dt_c=0.0, keep_trace=False, stop_on_reset=True):
    nc = len(cells)
    nn = len(arch.node_c)
    nv = len(arch.conv_node)
    vp1 = [0.0] * nc
    vp2 = [0.0] * nc
    # start from the quasi-static sleep operating point
    v_node = [0.0] * nn
    for k in range(nn):
        srcs = [c for j, c in enumerate(cells) if c.present and arch.branch_node[j] == k]
        if srcs:
            v_node[k] = max(c.ocv for c in srcs) - sum(d.vf(20e-6, dt_c) for d in arch.series)
    v_out = max(arch.conv_vset)
    if arch.out_series is not None:
        v_out -= arch.out_series.vf(SLEEP_A, dt_c)
    i_out_prev = [1e-5] * nv
    on = [v_node[arch.conv_node[k]] > arch.uvlo_on for k in range(nv)]
    order = sorted(range(nv), key=lambda k: -arch.conv_vset[k])
    v_in_min = [v if v > 0 else None for v in v_node]
    v_out_min = v_out
    uvlo = False
    reset = False
    t_reset = None
    i_peak = [0.0] * nc
    i_rev = 0.0
    q = [0.0] * nc
    i_prev = [1e-5] * nc
    tr = {"t": [], "v_in": [[] for _ in range(nn)], "v_out": [], "i_cell": [[] for _ in range(nc)]} \
        if keep_trace else {}
    t = 0.0
    next_sample = 0.0
    for dur, i_load in profile:
        steps = max(1, int(math.ceil(dur / dt - 1e-9)))
        h = dur / steps
        gain = 0.5 * arch.c_out / h          # converter loop: closes half the error per step
        for _ in range(steps):
            # 1. converters, highest set point first
            i_in = [0.0] * nn
            if arch.out_series is None:
                remaining = i_load
                supplied = 0.0
                for k in order:
                    if not on[k]:
                        continue
                    vin = v_node[arch.conv_node[k]]
                    i_max = arch.i_lim * vin * arch.eta / max(v_out, 0.5)
                    cmd = remaining + (arch.conv_vset[k] - v_out) * gain
                    i_k = min(max(cmd, 0.0), i_max)
                    remaining -= i_k
                    supplied += i_k
                    i_in[arch.conv_node[k]] += i_k * v_out / arch.eta / max(vin, 0.3) + arch.iq
                v_out = max(0.0, v_out + (supplied - i_load) / arch.c_out * h)
            else:
                # each converter regulates its own output at v_set; a Schottky
                # connects it to the rail (diode-OR of the two converter outputs).
                # Backward Euler on the rail, solved with bracketed Newton.
                def rail_current(v):
                    tot, gs, parts = 0.0, 0.0, []
                    for k in range(nv):
                        if not on[k] or arch.conv_vset[k] - v <= 0:
                            parts.append(0.0)
                            continue
                        vin = v_node[arch.conv_node[k]]
                        vs = arch.conv_vset[k]
                        i_k, g_k = arch.out_series.i_of_v(vs - v, dt_c, i_out_prev[k])
                        i_max = arch.i_lim * vin * arch.eta / vs
                        if i_k > i_max:
                            i_k, g_k = i_max, 0.0
                        parts.append(i_k)
                        tot += i_k
                        gs += g_k
                    return tot, gs, parts
                v_old = v_out
                lo, hi = 0.0, max(arch.conv_vset)
                v = v_old
                parts = [0.0] * nv
                for _ in range(60):
                    tot, gs, parts = rail_current(v)
                    f = arch.c_out * (v - v_old) / h - tot + i_load
                    if f > 0:
                        hi = min(hi, v)
                    else:
                        lo = max(lo, v)
                    v_new = v - f / (arch.c_out / h + gs)
                    if not lo < v_new < hi:
                        v_new = 0.5 * (lo + hi)
                    if abs(v_new - v) < 1e-7:
                        v = v_new
                        break
                    v = v_new
                v_out = v
                tot, gs, parts = rail_current(v_out)
                for k in range(nv):
                    if parts[k] > 0:
                        i_out_prev[k] = parts[k]
                        vin = v_node[arch.conv_node[k]]
                        i_in[arch.conv_node[k]] += parts[k] * arch.conv_vset[k] / arch.eta / max(vin, 0.3)
                    if on[k]:
                        i_in[arch.conv_node[k]] += arch.iq
            # 2. input nodes: backward Euler, bracketed Newton per node
            for k in range(nn):
                members = [j for j in range(nc) if arch.branch_node[j] == k and cells[j].present]
                v_old = v_node[k]
                lo = 0.0
                hi = max([cells[j].ocv for j in members] + [v_old])
                v = v_old
                for _ in range(60):
                    tot, gs = 0.0, 0.0
                    for j in members:
                        i_b, g = _branch(cells[j], vp1[j], vp2[j], v, arch, dt_c, i_prev[j])
                        i_prev[j] = max(i_b, 1e-9)
                        tot += i_b
                        gs += g
                    f = arch.node_c[k] * (v - v_old) / h - tot + i_in[k] + arch.node_leak
                    if f > 0:
                        hi = min(hi, v)
                    else:
                        lo = max(lo, v)
                    v_new = v - f / (arch.node_c[k] / h + gs)
                    if not lo < v_new < hi:
                        v_new = 0.5 * (lo + hi)
                    if abs(v_new - v) < 1e-7:
                        v = v_new
                        break
                    v = v_new
                v_node[k] = max(0.0, v)
                if v_in_min[k] is not None:
                    v_in_min[k] = min(v_in_min[k], v_node[k])
                for j in members:
                    i_b, _g = _branch(cells[j], vp1[j], vp2[j], v_node[k], arch, dt_c, i_prev[j])
                    i_prev[j] = max(i_b, 1e-9)
                    c = cells[j]
                    vp1[j] += (i_b * c.r_p1 - vp1[j]) * min(1.0, h / c.tau1)
                    v_ss = c.b2 * math.log1p(i_b / c.i_ref) if i_b > 0 else 0.0
                    vp2[j] += (v_ss - vp2[j]) * min(1.0, h / c.tau2)
                    i_peak[j] = max(i_peak[j], i_b)
                    if i_b < 0:
                        i_rev = max(i_rev, -i_b)
                    q[j] += i_b * h
            # 3. UVLO with hysteresis per converter
            for k in range(nv):
                vin = v_node[arch.conv_node[k]]
                if on[k] and vin < arch.uvlo_off:
                    on[k] = False
                    uvlo = True
                elif not on[k] and vin > arch.uvlo_on:
                    on[k] = True
            v_out_min = min(v_out_min, v_out)
            t += h
            if v_out < arch.v_reset and not reset:
                reset = True
                t_reset = t
            if keep_trace and t >= next_sample:
                tr["t"].append(t)
                for k in range(nn):
                    tr["v_in"][k].append(v_node[k])
                tr["v_out"].append(v_out)
                for j in range(nc):
                    tr["i_cell"][j].append(i_prev[j] * 1e3 if cells[j].present else 0.0)
                next_sample = t + max(h, 2e-4)
            if reset and stop_on_reset:
                break
        if reset and stop_on_reset:
            break
    return Result(arch.key, "", "", [round(v, 3) if v is not None else None for v in v_in_min],
                  round(v_out_min, 3), uvlo, reset, round(t_reset, 3) if t_reset else None,
                  [round(x * 1e3, 1) for x in i_peak], round(i_rev * 1e6, 3),
                  [round(x * 1e3, 2) for x in q], tr)


def run(arch_key, scenario, profile_key, keep_trace=False, profile=None, arch=None):
    arch = arch or ARCHS[arch_key]
    mk, dt_c = (SCENARIOS_1 if arch.n_cells == 1 else SCENARIOS)[scenario]
    prof = profile if profile is not None else PROFILES[profile_key]()
    dt = 1e-3 if "commissioning" in profile_key else 50e-6
    r = simulate(arch, mk(), prof, dt=dt, dt_c=dt_c, keep_trace=keep_trace)
    r.scenario = scenario
    r.profile = profile_key
    return r


def run_matrix(arch_keys, scenarios, profiles):
    return [run(a, s, p) for a in arch_keys for s in scenarios for p in profiles]


def input_cap_sweep(arch_key, r_list=(12, 20, 30, 40, 60, 100), c_list_uF=(22, 47, 85, 150, 220, 330, 470,
                                                                            680, 1000, 1500, 2200, 3300)):
    """Smallest effective capacitance per converter input node that survives
    3 polls + 1 report without converter UVLO or 3V3 reset (OCV 2.9 V)."""
    out = []
    for r_ohm in r_list:
        need = None
        for c_uF in c_list_uF:
            base = ARCHS[arch_key]
            arch = replace(base, node_c=tuple(c_uF * 1e-6 * (2 if len(base.node_c) == 1 else 1)
                                              for _ in base.node_c))
            cl = Cell("sweep", 2.90, float(r_ohm), r_ohm * 0.5, 0.05, 0.30, 20.0)
            prof = repeat(poll(), 3, 0.5) + report()
            r = simulate(arch, [cl, replace(cl)], prof, dt=50e-6)
            if not r.reset and not r.uvlo:
                need = c_uF
                break
        out.append({"r_ohm_per_cell": r_ohm, "min_c_per_node_uF": need})
    return out


def analytic_cap(q_dis, t_tot, v_min, v_max, r_i):
    """TI SWRA349 appendix A: C = (Q_dis - V_min/R_i * t_tot) / (V_max - V_min)."""
    return max(0.0, (q_dis - v_min / r_i * t_tot) / (v_max - v_min))


# ---------------------------------------------------------------- energy budget
def energy_budget(s, arch_key, cell_side_leak=0.0, arch=None):
    items = []
    q_poll = sum(d * i for d, i in poll())
    q_report = sum(d * i for d, i in report()) - 1.0 * SLEEP_A
    q_meas = sum(d * i for d, i in measurement())
    items.append(("H2 light-sleep floor (Espressif ICD measurement)", SLEEP_A))
    items.append((f"Thread polls, {q_poll * 1e3:.2f} mC every {s['poll_s']} s", q_poll / s["poll_s"]))
    items.append((f"Matter reports incl. 1 s ICD active mode, {q_report * 1e3:.2f} mC every {s['report_s']:g} s",
                  q_report / s["report_s"]))
    items.append((f"Subscription keep-alive (max interval {s['idle_s']} s)",
                  q_report / s["idle_s"] * s["keepalive_fraction"]))
    items.append((f"SHT40 measurement every {s['meas_s']} s (CPU + I2C + sensor)", q_meas / s["meas_s"]))
    items.append(("Battery measurement every 6 h (0.5 s, light sleep blocked)", 0.5 * 6e-3 / 21600))
    items.append(("MLE/SRP housekeeping (ASSUMED)", 1.0e-6))
    items.append(("SHT40 idle 0.08 uA + TPS3839 0.15 uA + MLCC/PCB leakage 0.3 uA (ASSUMED)", 0.53e-6))
    i_rail = sum(v for _, v in items)
    arch = arch or ARCHS[arch_key]
    eta = arch.eta
    # converter output voltage: the rail itself, or the set point ahead of the output Schottky
    v_conv = max(arch.conv_vset)
    p_conv = v_conv * i_rail
    v_cell = 3.0
    if arch.n_cells == 2 and len(arch.node_c) == 1:
        i_branch = p_conv / eta / v_cell / 2       # both cells share
    else:
        i_branch = p_conv / eta / v_cell           # one cell (Rev B) or the lead cell carries the load
    # charge-weighted forward drop: 70 % of the charge flows at the average current,
    # 30 % during bursts at ~30 mA per branch
    v_drop = sum(0.7 * d.vf(i_branch) + 0.3 * d.vf(30e-3) for d in arch.series) + i_branch * arch.r_extra
    i_cells = p_conv / eta / (v_cell - v_drop) + arch.iq * len(arch.conv_node) + cell_side_leak
    return {
        "items_uA": [(k, round(v * 1e6, 2)) for k, v in items],
        "rail_uA": round(i_rail * 1e6, 1),
        "converter_eta": eta,
        "converter_output_V": v_conv,
        "series_drop_V": round(v_drop, 3),
        "cell_side_leak_uA": round(cell_side_leak * 1e6, 2),
        "cells_total_uA": round(i_cells * 1e6, 1),
    }


BUDGET_CASES = {
    "nominal (SIT 15 s poll, 1 report / 5 min)": dict(poll_s=15, report_s=300, idle_s=300,
                                                      keepalive_fraction=0.0, meas_s=60),
    "busy (1 report / min)": dict(poll_s=15, report_s=60, idle_s=300, keepalive_fraction=0.0, meas_s=60),
    "quiet (no change, keep-alive only)": dict(poll_s=15, report_s=1e9, idle_s=300, keepalive_fraction=1.0,
                                               meas_s=60),
    "ESP-Matter example default (5 s poll)": dict(poll_s=5, report_s=300, idle_s=60, keepalive_fraction=0.0,
                                                  meas_s=60),
}


def lifetime_table(currents_uA, usable_mAh, self_discharge_mAh_per_year=0.01 * 225):
    rows = []
    for i in currents_uA:
        years = usable_mAh / (i / 1000.0 * 8760 + self_discharge_mAh_per_year)
        rows.append({"I_uA": i, "years": round(years, 2)})
    return rows


# ---------------------------------------------------------------- report
def fmt_result_row(r):
    vin = "/".join(f"{v:.2f}" if v is not None else "-" for v in r.v_in_min)
    fail = f"{r.t_reset_s:.2f} s" if r.reset else "-"
    return (f"| {r.arch} | {r.scenario} | {r.profile} | {vin} | {r.v_out_min:.2f} | "
            f"{'yes' if r.uvlo else 'no'} | {'**RESET**' if r.reset else 'ok'} | {fail} | "
            f"{'/'.join(f'{x:.0f}' for x in r.i_cell_peak_mA)} | {r.i_rev_max_uA:.3f} |")


HDR = ["| arch | scenario | profile | V_in min [V] | 3V3 min [V] | conv. UVLO | 3V3 | reset at | "
       "peak I/cell [mA] | max reverse [uA] |",
       "|---|---|---|---|---|---|---|---|---|---|"]


def revb_study(quick=False):
    """Rev B (one CR2450, no output diode, 3.3 V): matrix, tolerance, sensitivity, buffer sizing."""
    arch = single(REVB_C_IN_UF)
    arch_min = single(round(REVB_C_IN_MIN_UF))
    main_scen = [k for k in SCENARIOS_1 if not k.startswith("CR2032") and "R x" not in k]
    rows = [run(arch.key, sc, pk, arch=arch) for sc in main_scen for pk in PROFILES]
    rows_min = [run(arch_min.key, sc, pk, arch=arch_min) for sc in main_scen
                for pk in ("poll x5", "report + active mode")]
    sens = [run(arch.key, sc, pk, arch=arch) for sc in SCENARIOS_1 if "R x" in sc
            for pk in ("report + active mode", "boot", "commissioning nominal")]
    comm = []
    for label, (bg, rx) in COMMISSIONING.items():
        for sc in ("fresh 25C", "fresh 10C (interp.)", "mid-life 25C"):
            comm.append(run(arch.key, sc, "commissioning " + label, profile=commissioning(bg, rx), arch=arch))
    # why one CR2032 was rejected: same circuit, same buffer
    ref = [run(arch.key, sc, pk, arch=arch) for sc in ("CR2032 fresh 25C", "CR2032 mid-life 25C")
           for pk in PROFILES]
    sweep = []
    if not quick:
        caps = (85, 220, 400, 555, 765, 1025, 1500, 2200, 4700)
        for sc in ("mid-life 25C", "late 25C", "fresh -10C", "mid-life 0C (interp.)", "mid-life -10C",
                   "late 25C, pessimistic R x1.0"):
            for pk in ("poll x5", "report + active mode", "boot"):
                need = None
                for c in caps:
                    if not run("S", sc, pk, arch=single(c)).reset:
                        need = c
                        break
                sweep.append({"scenario": sc, "profile": pk, "min_c_in_uF": need})
    budgets = {k: {f"leak {lk * 1e6:g} uA": energy_budget(v, "S", cell_side_leak=lk, arch=arch)
                   for lk in REVB_LEAK_A} for k, v in BUDGET_CASES.items()}
    return arch, arch_min, rows, rows_min, sens, comm, ref, sweep, budgets


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results"))
    ap.add_argument("--plots", action="store_true")
    ap.add_argument("--quick", action="store_true", help="skip the slow sweeps")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    # ---- Rev B: one CR2450
    arch_b, arch_bmin, rows_b, rows_bmin, sens_b, comm_b, ref_b, sweep_b, budgets_b = revb_study(a.quick)
    lifetime_b = {str(c): lifetime_table([25, 50, 64, 100, 200], c, 0.01 * 620) for c in REVB_USABLE_MAH}

    # ---- Rev A (two CR2032), kept for the record of decision D2
    scen = list(SCENARIOS)
    prof = list(PROFILES)
    rows = run_matrix(["A2", "A1", "B", "C"], scen, prof)
    rows_ref = run_matrix(["C50", "B0"], scen, prof)

    sens = []
    for label, (bg, rx) in COMMISSIONING.items():
        for sc in ["fresh 25C", "mid-life 25C", "late 25C", "fresh -10C"]:
            for ak in ["A2", "A1", "B", "C"]:
                r = run(ak, sc, "commissioning " + label, profile=commissioning(bg, rx))
                sens.append(r)

    sweeps = {}
    if not a.quick:
        sweeps = {k: input_cap_sweep(k) for k in ["A2", "C"]}

    budgets = {k: {ak: energy_budget(v, ak) for ak in ["A2", "A1", "B", "C"]} for k, v in BUDGET_CASES.items()}
    # analytic check (SWRA349 formula) for one report burst on one converter input
    q_burst = sum(d * i for d, i in report()[:10]) * 3.3 / 0.9 / 2.4   # charge drawn at the input, ~2.4 V
    t_burst = sum(d for d, _ in report()[:10])
    analytic = {f"R_i={ri} Ohm": round(analytic_cap(q_burst, t_burst, 1.80, 2.60, ri) * 1e6, 1)
                for ri in (20, 40, 100, 300, 1000)}

    plain = lambda rs: [vars(r) | {"trace": None} for r in rs]
    out = {
        "status": "ESTIMATE - model, not a measurement",
        "architectures": {k: v.title for k, v in ARCHS.items()},
        "rev_b": {
            "arch": arch_b.title,
            "c_in_uF": REVB_C_IN_UF, "c_in_min_uF": round(REVB_C_IN_MIN_UF),
            "matrix": plain(rows_b),
            "matrix_min_buffer": plain(rows_bmin),
            "resistance_sensitivity": plain(sens_b),
            "commissioning_sensitivity": plain(comm_b),
            "one_cr2032_reference": plain(ref_b),
            "buffer_sweep": sweep_b,
            "budgets": budgets_b,
            "lifetime_usable_mAh": lifetime_b,
        },
        "rev_a": {
            "matrix": plain(rows + rows_ref),
            "commissioning_sensitivity": plain(sens),
            "input_cap_sweep": sweeps,
            "analytic_burst_cap_uF": analytic,
            "budgets": budgets,
            "lifetime_usable_mAh": {str(c): lifetime_table([25, 50, 65, 100, 200], c, 2 * 0.01 * 225)
                                    for c in (200.0, 270.0, 330.0)},
        },
    }
    with open(os.path.join(a.outdir, "power_model_results.json"), "w") as f:
        json.dump(out, f, indent=1, default=float)

    L = ["# Power model results (ESTIMATE, generated by power_model.py)", "",
         "# Rev B: one CR2450", "",
         "Circuit: one CR2450 -> P-MOSFET -> TPS63900 at 3.3 V (100 mA input limit), no output diode; "
         f"input buffer {REVB_C_IN_UF:g} uF effective (85 uF MLCC + 470 uF electrolytic; "
         f"{round(REVB_C_IN_MIN_UF)} uF with the electrolytic at -20 %).",
         "CR2450 resistances = CR2032 fit x 0.60 (electrode-area scaling, no published pulse data).", "",
         "## Load-profile matrix (nominal buffer)", ""] + HDR
    L += [fmt_result_row(r) for r in rows_b]
    L += ["", f"## Polls and reports with the minimum buffer ({round(REVB_C_IN_MIN_UF)} uF)", ""] + HDR
    L += [fmt_result_row(r) for r in rows_bmin]
    L += ["", "## Cell resistance sensitivity (R x 0.4 optimistic, x 1.0 = CR2032 resistance)", ""] + HDR
    L += [fmt_result_row(r) for r in sens_b]
    L += ["", "## Commissioning sensitivity (90 s, profile assumed)", ""] + HDR
    L += [fmt_result_row(r) for r in comm_b]
    L += ["", "## Reference: one CR2032 in the same circuit (why Rev B uses a CR2450)", ""] + HDR
    L += [fmt_result_row(r) for r in ref_b]
    if sweep_b:
        L += ["", "## Smallest effective input buffer that survives the profile", "",
              "| scenario | profile | min C_in [uF] |", "|---|---|---|"]
        L += [f"| {x['scenario']} | {x['profile']} | {x['min_c_in_uF'] or '> 4700'} |" for x in sweep_b]
    for case, per in budgets_b.items():
        L += ["", f"## Rev B budget: {case}", "", "| item | uA at 3V3 |", "|---|---|"]
        first = next(iter(per.values()))
        L += [f"| {n} | {v} |" for n, v in first["items_uA"]]
        L += [f"| **total at the 3V3 rail** | **{first['rail_uA']}** |"]
        for lab, b in per.items():
            L += [f"| **drawn from the CR2450, electrolytic {lab}** | **{b['cells_total_uA']}** |"]
    L += ["", "## Rev B lifetime vs average cell current (self-discharge 1 %/year of 620 mAh included)", "",
          "Usable charge before reports fail: " + " / ".join(f"{c:g}" for c in REVB_USABLE_MAH) +
          " mAh (50 / 60 / 70 % of 620 mAh, pessimistic / central / optimistic ESTIMATE).", "",
          "| average current [uA] | " + " | ".join(f"years @ {c:g} mAh" for c in REVB_USABLE_MAH) + " |",
          "|---|---|---|---|"]
    keys = [str(c) for c in REVB_USABLE_MAH]
    for i, row in enumerate(lifetime_b[keys[0]]):
        L.append(f"| {row['I_uA']} | " + " | ".join(str(lifetime_b[k][i]["years"]) for k in keys) + " |")

    L += ["", "# Rev A: two CR2032 (record of decision D2)", "",
          "Architectures: " + "; ".join(f"**{k}** = {v.title}" for k, v in ARCHS.items() if k != "S"), "",
          "## Load-profile matrix", ""] + HDR
    L += [fmt_result_row(r) for r in rows]
    L += ["", "## Reference variants (C50: 50 mA input limit, B0: no second barrier)", ""] + HDR
    L += [fmt_result_row(r) for r in rows_ref]
    L += ["", "## Commissioning sensitivity (90 s, profile assumed)", ""] + HDR
    L += [fmt_result_row(r) for r in sens]
    if sweeps:
        L += ["", "## Minimum effective capacitance per converter input node (3 polls + 1 report, OCV 2.9 V)", "",
              "| R per cell [Ohm] | A2: C_buf/2 [uF] | C: C_in per converter [uF] |", "|---|---|---|"]
        for s2, sb in zip(sweeps["A2"], sweeps["C"]):
            L.append(f"| {s2['r_ohm_per_cell']} | {s2['min_c_per_node_uF'] or '> 3300'} | "
                     f"{sb['min_c_per_node_uF'] or '> 3300'} |")
    L += ["", "## SWRA349 analytic buffer capacitor for the report burst (V_max 2.6 V, V_min 1.8 V)", "",
          "| R_i | C [uF] |", "|---|---|"] + [f"| {k} | {v} |" for k, v in analytic.items()]
    for case, per in budgets.items():
        L += ["", f"## Rev A budget: {case}", "", "| item | uA at 3V3 |", "|---|---|"]
        L += [f"| {n} | {v} |" for n, v in per["C"]["items_uA"]]
        L += [f"| **total at the 3V3 rail** | **{per['C']['rail_uA']}** |"]
        for ak in ["A2", "A1", "B", "C"]:
            L += [f"| {ak}: series drop (charge-weighted) | {per[ak]['series_drop_V']} V |",
                  f"| **{ak}: drawn from the two cells** | **{per[ak]['cells_total_uA']}** |"]
    L += ["", "## Rev A lifetime vs average current drawn from the pair (self-discharge 1 %/year included)", "",
          "Usable charge of the pair before radio bursts fail: 200 / 270 / 330 mAh (pessimistic / central /",
          "optimistic ESTIMATE); 2 x 225 mAh nominal is never fully usable.", "",
          "| average current [uA] | years @ 200 mAh | years @ 270 mAh | years @ 330 mAh |", "|---|---|---|---|"]
    lt = out["rev_a"]["lifetime_usable_mAh"]
    for i, row in enumerate(lt["200.0"]):
        L.append(f"| {row['I_uA']} | {row['years']} | {lt['270.0'][i]['years']} | {lt['330.0'][i]['years']} |")
    with open(os.path.join(a.outdir, "power_model_summary.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))

    if a.plots:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        cases = [(arch_b, "fresh 25C", "report + active mode"), (arch_b, "late 25C", "report + active mode"),
                 (arch_b, "fresh 25C", "boot"), (arch_b, "mid-life 25C", "boot"),
                 (arch_b, "fresh 25C", "commissioning nominal"), (arch_b, "mid-life 25C", "commissioning nominal")]
        fig, axes = plt.subplots(3, 2, figsize=(12, 10), sharey=True)
        for ax, (ar, sc, pk) in zip(axes.flat, cases):
            mk, dt_c = SCENARIOS_1[sc]
            dt = 1e-3 if "commissioning" in pk else 50e-6
            r = simulate(ar, mk(), PROFILES[pk](), dt=dt, dt_c=dt_c, keep_trace=True, stop_on_reset=False)
            ax.plot(r.trace["t"], r.trace["v_in"][0], lw=0.8, label="V_in (CR2450 side)")
            ax.plot(r.trace["t"], r.trace["v_out"], "k", lw=1.0, label="3V3")
            ax.axhline(ar.uvlo_off, color="r", ls="--", lw=0.7)
            ax.axhline(ar.v_reset, color="m", ls=":", lw=0.7)
            ax.set_ylim(0, 3.6)
            ax.set_title(f"Rev B: {sc}, {pk}", fontsize=9)
            ax.legend(fontsize=7, loc="lower left")
        for ax in axes[-1]:
            ax.set_xlabel("time [s]")
        fig.suptitle(f"ESTIMATE - Rev B power path, one CR2450, {REVB_C_IN_UF:g} uF input buffer (power_model.py)")
        fig.tight_layout()
        fig.savefig(os.path.join(a.outdir, "power_model_traces.png"), dpi=110)
        print("plot written")


if __name__ == "__main__":
    main()
