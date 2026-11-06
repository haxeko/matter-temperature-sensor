"""
TH-SENSOR-H2 Rev B - single source of truth for the electrical design.

Rev B runs from ONE CR2450 (Rev A: two CR2032 with one converter each). The power
path keeps the Rev A principles: P-MOSFET reverse-polarity protection, one TPS63900
with a 100 mA input current limit, current-measurement links; the output Schottky is
gone because there is nothing to OR any more (docs/decisions.md D20).

Every part: reference, symbol, footprint, value, sourcing fields and the net of
every pin. gen_schematic.py draws the schematic from this table and then
checks the netlist exported by KiCad against it (parity); gen_pcb.py loads the
nets from the KiCad netlist.

Sourcing fields were looked up on the JLCPCB parts API on 2026-10-29 / 2026-10-30
(tools/jlc_lookup.py); stock and Basic/Extended status change daily and must be
re-checked before ordering (docs/assembly.md).

Two board variants share everything except the radio part (environment variable
TH_VARIANT, default "module"):
  module  TH-SENSOR-H2 Rev B: ESP32-H2-MINI-1-H4S module -> hardware/kicad, production, ...
  chip    TH-SENSOR-H2C Rev A: bare ESP32-H2FH4S chip (QFN32, 4 MB in-package flash), 32 MHz
          crystal, RF matching network and a TI DN007 PCB antenna on a 4-layer board
          -> hardware/chip/kicad, hardware/chip/production, ... (docs/chip_variant.md)
The firmware is the same for both: every GPIO keeps its function.
"""
import os as _os

VARIANT = _os.environ.get("TH_VARIANT", "module")
if VARIANT not in ("module", "chip"):
    raise SystemExit("TH_VARIANT must be 'module' or 'chip', not %r" % VARIANT)
_HW = _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), ".."))
if VARIANT == "module":
    PROJECT = "th_sensor_h2"
    TITLE = "TH-SENSOR-H2 thermo-hygrometer"
    REV = "B"
    DATE = "2026-10-30"
    HW_DIR = _HW                                    # hardware/kicad, hardware/production, ...
    BOARD_NAME = "TH-SENSOR-H2"
else:
    PROJECT = "th_sensor_h2c"
    TITLE = "TH-SENSOR-H2C thermo-hygrometer (bare ESP32-H2 chip)"
    REV = "A"
    DATE = "2026-11-06"
    HW_DIR = _os.path.join(_HW, "chip")             # hardware/chip/kicad, hardware/chip/production, ...
    BOARD_NAME = "TH-SENSOR-H2C"

KSYM = "/usr/share/kicad/symbols/"
# Espressif KiCad libraries (github.com/espressif/kicad-libraries, git dd76561812ab300351234ba6e0ec1295641796f0).
# Only needed to refresh the vendored copies in hardware/kicad/lib; without it the generators use those copies.
ESPRESSIF_LIB = _os.environ.get("ESPRESSIF_KICAD_LIB", "/tmp/claude-0/ext/espressif-kicad-libraries")

# symbol sources: lib_id -> (library file, symbol name in that file, nick)
SYMBOLS = {
    "Device:R": (KSYM + "Device.kicad_sym", "R"),
    "Device:C": (KSYM + "Device.kicad_sym", "C"),
    "Device:C_Polarized": (KSYM + "Device.kicad_sym", "C_Polarized"),
    "Device:L": (KSYM + "Device.kicad_sym", "L"),
    "Device:D_Schottky": (KSYM + "Device.kicad_sym", "D_Schottky"),
    "Device:LED": (KSYM + "Device.kicad_sym", "LED"),
    "Device:Battery_Cell": (KSYM + "Device.kicad_sym", "Battery_Cell"),
    "Device:Crystal": (KSYM + "Device.kicad_sym", "Crystal"),
    "Switch:SW_Push": (KSYM + "Switch.kicad_sym", "SW_Push"),
    "Connector:TestPoint": (KSYM + "Connector.kicad_sym", "TestPoint"),
    "Connector_Generic:Conn_01x06": (KSYM + "Connector_Generic.kicad_sym", "Conn_01x06"),
    "Regulator_Switching:TPS63900": (KSYM + "Regulator_Switching.kicad_sym", "TPS63900"),
    "Power_Supervisor:TPS3839DBZ": (KSYM + "Power_Supervisor.kicad_sym", "TPS3839DBZ"),
    "Sensor_Humidity:SHT4x": (KSYM + "Sensor_Humidity.kicad_sym", "SHT4x"),
    "Mechanical:MountingHole": (KSYM + "Mechanical.kicad_sym", "MountingHole"),
    "Mechanical:Fiducial": (KSYM + "Mechanical.kicad_sym", "Fiducial"),
    "power:GND": (KSYM + "power.kicad_sym", "GND"),
    "power:+3V3": (KSYM + "power.kicad_sym", "+3V3"),
    "power:PWR_FLAG": (KSYM + "power.kicad_sym", "PWR_FLAG"),
    # project library (hardware/kicad/lib/th_sensor.kicad_sym), written by gen_schematic.py
    "th_sensor:ESP32-H2-MINI-1": (ESPRESSIF_LIB + "/symbols/Espressif.kicad_sym", "ESP32-H2-MINI-1"),
    "th_sensor:ESP32-H2": (ESPRESSIF_LIB + "/symbols/Espressif.kicad_sym", "ESP32-H2"),
    "Device:Crystal_GND24": (KSYM + "Device.kicad_sym", "Crystal_GND24"),
    "Device:Antenna_Shield": (KSYM + "Device.kicad_sym", "Antenna_Shield"),
    "Connector_Generic:Conn_02x03_Odd_Even": (KSYM + "Connector_Generic.kicad_sym", "Conn_02x03_Odd_Even"),
    "th_sensor:AO3401A": (KSYM + "Transistor_FET.kicad_sym", "AO3401A"),
    "th_sensor:2N7002": (KSYM + "Transistor_FET.kicad_sym", "2N7002"),
}
for _k in (("th_sensor:ESP32-H2", "Device:Crystal_GND24", "Device:Antenna_Shield", "Connector_Generic:Conn_02x03_Odd_Even")
           if VARIANT == "module" else ("th_sensor:ESP32-H2-MINI-1", "Connector_Generic:Conn_01x06")):
    del SYMBOLS[_k]

FP_R0603 = "Resistor_SMD:R_0603_1608Metric"
FP_R0805 = "Resistor_SMD:R_0805_2012Metric"
FP_C0603 = "Capacitor_SMD:C_0603_1608Metric"
FP_C0805 = "Capacitor_SMD:C_0805_2012Metric"
FP_C1206 = "Capacitor_SMD:C_1206_3216Metric"
FP_SOT23 = "Package_TO_SOT_SMD:SOT-23"

# sourcing shorthands: (LCSC code, manufacturer, MPN)
SRC = {
    "0R_0805": ("C17477", "UNI-ROYAL", "0805W8F0000T5E"),
    "0R_0603": ("C21189", "UNI-ROYAL", "0603WAF0000T5E"),
    "10k": ("C25804", "UNI-ROYAL", "0603WAF1002T5E"),
    "1k": ("C21190", "UNI-ROYAL", "0603WAF1001T5E"),
    "1M": ("C22935", "UNI-ROYAL", "0603WAF1004T5E"),
    "470k": ("C23178", "UNI-ROYAL", "0603WAF4703T5E"),
    "10.5k": ("C22855", "UNI-ROYAL", "0603WAF1052T5E"),
    "16.2k": ("C22885", "UNI-ROYAL", "0603WAF1622T5E"),
    "100n": ("C14663", "YAGEO", "CC0603KRX7R9BB104"),
    "1u": ("C15849", "Samsung", "CL10A105KB8NNNC"),
    "10u": ("C19702", "Samsung", "CL10A106KP8NNNC"),
    "22u_0805": ("C45783", "Samsung", "CL21A226MAQNNNE"),
    "100u_1206": ("C15008", "Samsung", "CL31A107MQHNNNE"),
    "22n": ("C21122", "Samsung", "CL10B223KB8NNNC"),
    "18p": ("C1647", "Samsung", "CL10C180JB8NNNC"),
    "AO3401A": ("C15127", "Alpha & Omega", "AO3401A"),
    "2N7002": ("C8545", "JSCJ", "2N7002"),
    "TPS63900": ("C1518762", "Texas Instruments", "TPS63900DSKR"),
    "TPS3839K33": ("C96333", "Texas Instruments", "TPS3839K33DBZR"),
    "DFE201612E": ("C337893", "Murata", "DFE201612E-2R2M=P2"),
    "BS24SMT": ("C964809", "MYOUNG", "BS-24-B4AA016"),
    "470u_elec": ("C2901342", "KNSCHA", "RVT470UF6.3V67RV0038"),
    "H2MINI": ("C47967030", "Espressif", "ESP32-H2-MINI-1-H4S"),
    "SHT40": ("C2848306", "Sensirion", "SHT40-AD1B-R3"),
    "FC135": ("C32346", "Seiko Epson", "Q13FC13500004"),
    "TS1187A": ("C318884", "XKB", "TS-1187A-B-A-B"),
    "KT0603R": ("C2286", "KENTO", "KT-0603R"),
    # chip variant (JLC parts search 2026-11-06)
    "H2FH4S": ("C50392664", "Espressif", "ESP32-H2FH4S"),
    "XTAL32M": ("C5210649", "YXC", "X322532MLB4SI"),
    "24nH_0603": ("C162644", "Murata", "LQW18AN24NG00D"),
    "12p": ("C38523", "Samsung", "CL10C120JB8NNNC"),
    "10n": ("C57112", "FH", "0603B103K500NT"),
    "499R": ("C23065", "UNI-ROYAL", "0603WAF4990T5E"),
    "1p5_0201": ("C161414", "Murata", "GRM0335C1H1R5BA01D"),
    "2n4_0201": ("C98042", "Murata", "LQP03TN2N4B02D"),
    "0R_0201": ("C473473", "UNI-ROYAL", "0201WMF0000TEE"),
}

PARTS = []


def part(ref, lib_id, value, footprint, pins, src=None, dnp=False, in_bom=True, on_board=True, desc="", spec="",
         **extra):
    lcsc, mfr, mpn = SRC[src] if src else ("", "", "")
    if not spec:
        if footprint.startswith("Resistor_SMD:"):
            spec = "1% " + footprint.split("_")[2]
        elif footprint.startswith("Capacitor_SMD:"):
            spec = footprint.split("_")[2]
    PARTS.append(dict(ref=ref, lib_id=lib_id, value=value, footprint=footprint, pins=pins, lcsc=lcsc, mfr=mfr,
                      mpn=mpn, dnp=dnp, in_bom=in_bom, on_board=on_board, desc=desc, spec=spec, extra=extra))


# ------------------------------------------------------------------ power path (one CR2450)
part("BT1", "Device:Battery_Cell", "CR2450 holder", "th_sensor:BatteryHolder_MYOUNG_BS-24-B4AA016_1x2450",
     {"1": "VBAT", "2": "GND"}, src="BS24SMT",
     desc="CR2450 SMT holder, gold-plated contacts, LCP housing (pad 1 = +)")
part("R1", "Device:R", "0R", FP_R0805, {"1": "VBAT", "2": "VBAT_L"}, src="0R_0805",
     desc="Cell current-measurement link (remove, insert ammeter)")
part("Q1", "th_sensor:AO3401A", "AO3401A", FP_SOT23, {"1": "GND", "2": "VIN", "3": "VBAT_L"}, src="AO3401A",
     desc="Reverse-polarity P-MOSFET (body diode forward, Vgs = -Vcell)")
part("C1", "Device:C", "10uF", FP_C0603, {"1": "VIN", "2": "GND"}, src="10u",
     spec="10V X5R 0603", desc="TPS63900 input cap, next to VIN")
part("C2", "Device:C", "100uF", FP_C1206, {"1": "VIN", "2": "GND"}, src="100u_1206",
     spec="6.3V X5R 1206", desc="Input buffer (coin cell pulse support)")
part("C3", "Device:C", "100uF", FP_C1206, {"1": "VIN", "2": "GND"}, src="100u_1206",
     spec="6.3V X5R 1206", desc="Input buffer (coin cell pulse support)")
part("C5", "Device:C_Polarized", "470uF", "Capacitor_SMD:CP_Elec_6.3x7.7", {"1": "VIN", "2": "GND"},
     src="470u_elec", spec="6.3V Al electrolytic 6.3x7.7mm",
     desc="Bulk input buffer: reports survive mid-life / cold cells (power model, ESTIMATE); leakage to be measured")
part("U1", "Regulator_Switching:TPS63900", "TPS63900DSKR", "Package_SON:WSON-10-1EP_2.5x2.5mm_P0.5mm_EP1.2x2mm",
     {"10": "VIN", "1": "VIN", "2": "GND", "9": "LX1", "7": "LX2", "6": "VOUT",
      "3": "CFG1", "4": "CFG2", "5": "CFG3", "8": "GND", "11": "GND"},
     src="TPS63900", desc="Buck-boost, SEL=L -> VO(1) = 3.3 V, input current limit 100 mA")
part("R2", "Device:R", "0R", FP_R0603, {"1": "CFG1", "2": "GND"}, src="0R_0603",
     desc="RCFG1 (SLVSET3D table 7-2 row RCFG1 = 0 Ohm)")
part("R3", "Device:R", "10.5k", FP_R0603, {"1": "CFG2", "2": "GND"}, src="10.5k",
     spec="1% 100ppm 0603", desc="RCFG2: 100 mA input current limit (table 7-2; option 13.3k = 50 mA)")
part("R4", "Device:R", "16.2k", FP_R0603, {"1": "CFG3", "2": "GND"}, src="16.2k",
     spec="1% 100ppm 0603", desc="RCFG3: VO(1) = 3.3 V (table 7-3), selected by SEL = low")
part("L1", "Device:L", "2.2uH", "th_sensor:L_Murata_DFE201612E", {"1": "LX1", "2": "LX2"},
     src="DFE201612E", desc="2.2 uH, Isat 2.4 A, 116 mOhm")
part("C4", "Device:C", "22uF", FP_C0805, {"1": "VOUT", "2": "GND"}, src="22u_0805",
     spec="25V X5R 0805", desc="TPS63900 output cap, next to VOUT")


# ------------------------------------------------------------------ 3V3 rail, supervisor, reset
part("C21", "Device:C", "100uF", FP_C1206, {"1": "VOUT", "2": "GND"}, src="100u_1206",
     spec="6.3V X5R 1206", desc="Rail bulk")
part("C22", "Device:C", "100uF", FP_C1206, {"1": "VOUT", "2": "GND"}, src="100u_1206",
     spec="6.3V X5R 1206", desc="Rail bulk")
part("R21", "Device:R", "0R", FP_R0805, {"1": "VOUT", "2": "+3V3"}, src="0R_0805",
     desc="Load current-measurement link (module, sensor, LED, supervisor)")
part("U3", "Power_Supervisor:TPS3839DBZ", "TPS3839K33DBZR", FP_SOT23, {"3": "+3V3", "1": "GND", "2": "nRST"},
     src="TPS3839K33", desc="2.93 V supervisor, push-pull, 200 ms delay")
part("C26", "Device:C", "100nF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="100n", desc="U3 bypass")
part("R22", "Device:R", "10k", FP_R0603, {"1": "nRST", "2": "EN"}, src="10k",
     desc="Isolates the push-pull supervisor from the RST button / J1")
part("C25", "Device:C", "1uF", FP_C0603, {"1": "EN", "2": "GND"}, src="1u", desc="EN RC (Espressif reference)")
part("SW2", "Switch:SW_Push", "RST", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", {"1": "EN", "2": "GND"},
     src="TS1187A", desc="Reset")

# ------------------------------------------------------------------ radio: module or bare chip
if VARIANT == "module":
    part("U4", "th_sensor:ESP32-H2-MINI-1", "ESP32-H2-MINI-1-H4S", "th_sensor:ESP32-H2-MINI-1",
         {"3": "+3V3", "15": "+3V3", "8": "EN",
          "16": "VBAT_MEAS_EN", "19": "VBAT_SENSE", "18": None,
          "12": "XTAL_32K_P", "13": "XTAL_32K_N",
          "20": "I2C_SDA", "21": "I2C_SCL", "24": "LED", "22": "STRAP_GPIO8", "23": "BTN_USER",
          "26": "USB_DM", "27": "USB_DP", "30": "U0RXD", "31": "U0TXD",
          "5": None, "6": None, "9": None, "10": None, "25": None,
          **{str(p): "GND" for p in [1, 2, 11, 14] + list(range(36, 54))}},
         src="H2MINI", desc="4 MB flash, PCB antenna; JLC stock 0 on 2026-10-29")
    part("C23", "Device:C", "10uF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="10u", spec="10V X5R 0603", desc="Module decoupling")
    part("C24", "Device:C", "100nF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="100n", desc="Module decoupling")
else:
    # Pin numbers: ESP32-H2 QFN32 (datasheet v1.3 / Espressif KiCad symbol "ESP32-H2"). Supply pins and
    # their capacitors follow the ESP32-H2 Hardware Design Guidelines v1.6 reference schematic
    # (esp32h2-sche-core.png): VDD3P3 pins 1/2: 10 uF + 1 uF + 0.1 uF; pins 30/31: 10 nF; pin 27: 0.1 uF +
    # 1 uF; VDDPST2 (20), VDDA_PMU (19) and VDDPST1 (9): 0.1 uF each; VBAT (18) tied to 3V3 (R2 = 0 there).
    part("U4", "th_sensor:ESP32-H2", "ESP32-H2FH4S", "th_sensor:QFN-32-1EP_4x4mm_P0.4mm_EP2.9x2.9mm",
         {"1": "+3V3", "2": "+3V3", "3": None, "4": None, "5": None, "6": None, "7": None, "8": "VBAT_SENSE",
          "9": "+3V3", "10": "STRAP_GPIO8", "11": "BTN_USER", "12": "I2C_SDA", "13": "I2C_SCL", "14": "VBAT_MEAS_EN",
          "15": "XTAL_32K_P", "16": "XTAL_32K_N", "17": "EN", "18": "+3V3", "19": "+3V3", "20": "+3V3",
          "21": "LED", "22": "U0RXD", "23": "U0TXD", "24": None, "25": "USB_DM", "26": "USB_DP", "27": "+3V3",
          "28": "XTAL_N", "29": "XTAL_P_IC", "30": "+3V3", "31": "+3V3", "32": "LNA_IN", "33": "GND"},
         src="H2FH4S", desc="ESP32-H2 QFN32 4x4, 4 MB in-package flash; JLC stock 0 on 2026-11-06 (ESP32-H2FH4, "
                            "C22470214, in stock: older ordering code, check the chip revision before using it)")
    part("C40", "Device:C", "10uF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="10u", spec="10V X5R 0603",
         desc="VDD3P3 pins 1/2 (HDG: 10 uF)")
    part("C41", "Device:C", "1uF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="1u", desc="VDD3P3 pins 1/2 (HDG: 1 uF)")
    part("C42", "Device:C", "100nF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="100n", desc="VDD3P3 pins 1/2 (HDG: 0.1 uF)")
    part("C43", "Device:C", "10nF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="10n", desc="VDD3P3 pins 30/31 (HDG: 10 nF)")
    part("C44", "Device:C", "100nF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="100n", desc="VDD3P3 pin 27 (HDG: 0.1 uF)")
    part("C45", "Device:C", "1uF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="1u", desc="VDD3P3 pin 27 (HDG: 1 uF)")
    part("C46", "Device:C", "100nF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="100n", desc="VDDPST2 pin 20 (HDG: 0.1 uF)")
    part("C47", "Device:C", "100nF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="100n",
         desc="VDDA_PMU pin 19 / VBAT pin 18 (HDG: 0.1 uF)")
    part("C48", "Device:C", "100nF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="100n", desc="VDDPST1 pin 9 (HDG: 0.1 uF)")
    # 32 MHz main crystal: HDG requires +-10 ppm; 9 pF load like the crystal in Espressif's MINI-1 BOM.
    # C49/C50 from C_L = C49*C50/(C49+C50) + C_stray with ~3 pF stray (ESTIMATE): tune at bring-up.
    part("Y2", "Device:Crystal_GND24", "32MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
         {"1": "XTAL_P", "2": "GND", "3": "XTAL_N", "4": "GND"}, src="XTAL32M",
         spec="CL 9pF, +-10ppm, 40 ohm", desc="Main crystal, 32 MHz +-10 ppm (HDG requirement)")
    part("C49", "Device:C", "12pF", FP_C0603, {"1": "XTAL_P", "2": "GND"}, src="12p", spec="50V C0G 0603",
         desc="Crystal load cap (start value, tune for +-10 ppm)")
    part("C50", "Device:C", "12pF", FP_C0603, {"1": "XTAL_N", "2": "GND"}, src="12p", spec="50V C0G 0603",
         desc="Crystal load cap (start value, tune for +-10 ppm)")
    part("L3", "Device:L", "24nH", "Inductor_SMD:L_0603_1608Metric", {"1": "XTAL_P_IC", "2": "XTAL_P"},
         src="24nH_0603", spec="2% 0603", desc="Series element on XTAL_P (HDG: 24 nH start value)")
    part("R40", "Device:R", "499R", FP_R0603, {"1": "U0TXD", "2": "U0TXD_J"}, src="499R",
         desc="U0TXD series resistor (HDG recommendation)")
    # RF: ANT -> C51 (shunt) -> L4 (series) -> C52 (shunt) -> R41 (series) -> L5 (shunt, not fitted) -> antenna.
    # HDG "CLCCL" network; positions C12/L2/C11/C3/L1 in the HDG figure. Start values from the HDG
    # recommended ranges (C 1.2-1.8 pF, L 2.0-3.0 nH), 0201 as the HDG asks; they must be tuned with a
    # network analyser (docs/chip_variant.md). R41 0R: Espressif's MINI-1 feeds its PCB antenna without a
    # DC block, so the antenna-side series position starts as a link.
    part("C51", "Device:C", "1.5pF", "Capacitor_SMD:C_0201_0603Metric", {"1": "LNA_IN", "2": "GND"}, src="1p5_0201",
         spec="50V C0G 0201 +-0.1pF", desc="RF match, shunt at the chip (HDG C12), start value: TUNE")
    part("L4", "Device:L", "2.4nH", "Inductor_SMD:L_0201_0603Metric", {"1": "LNA_IN", "2": "RF_M"}, src="2n4_0201",
         spec="0201 +-0.1nH", desc="RF match, series (HDG L2), start value: TUNE")
    part("C52", "Device:C", "1.5pF", "Capacitor_SMD:C_0201_0603Metric", {"1": "RF_M", "2": "GND"}, src="1p5_0201",
         spec="50V C0G 0201 +-0.1pF", desc="RF match, shunt (HDG C11), start value: TUNE")
    part("R41", "Device:R", "0R", "Resistor_SMD:R_0201_0603Metric", {"1": "RF_M", "2": "RF_ANT"}, src="0R_0201",
         spec="0201", desc="Antenna match, series position (HDG C3): link until tuned")
    part("L5", "Device:L", "DNP", "Inductor_SMD:L_0201_0603Metric", {"1": "RF_ANT", "2": "GND"}, dnp=True,
         desc="Antenna match, shunt position (HDG L1): not fitted until tuned")
    part("AE1", "Device:Antenna_Shield", "PCB IFA", "th_sensor:Antenna_TI_DN007_IFA_2.4GHz_Mirrored",
         {"1": "RF_ANT", "2": "GND"}, in_bom=False,
         desc="2.4 GHz inverted-F PCB antenna, TI DN007 (SWRU120D) geometry as its mirror image, copper only")
part("Y1", "Device:Crystal", "32.768kHz", "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm",
     {"1": "XTAL_32K_P", "2": "XTAL_32K_N"}, src="FC135", spec="CL 12.5pF, ESR<=70k, 20ppm", desc="Epson FC-135, ESR <= 70 kOhm")
part("C27", "Device:C", "18pF", FP_C0603, {"1": "XTAL_32K_P", "2": "GND"}, src="18p",
     spec="50V C0G 0603", desc="Load cap (CL 12.5 pF, ~3 pF stray assumed; tune at bring-up)")
part("C28", "Device:C", "18pF", FP_C0603, {"1": "XTAL_32K_N", "2": "GND"}, src="18p",
     spec="50V C0G 0603", desc="Load cap")
part("SW1", "Switch:SW_Push", "USER/BOOT", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A",
     {"1": "BTN_USER", "2": "GND"}, src="TS1187A", desc="GPIO9: user button, BOOT strap at reset")
part("R23", "Device:R", "10k", FP_R0603, {"1": "+3V3", "2": "BTN_USER"}, src="10k",
     desc="GPIO9 pull-up (strap, deep-sleep wake)")
part("R24", "Device:R", "10k", FP_R0603, {"1": "+3V3", "2": "STRAP_GPIO8"}, src="10k",
     desc="GPIO8 strap high (needed for download mode)")
part("R25", "Device:R", "1k", FP_R0603, {"1": "LED", "2": "LED_A"}, src="1k", desc="LED ~1.5 mA")
part("D3", "Device:LED", "red", "LED_SMD:LED_0603_1608Metric", {"1": "GND", "2": "LED_A"}, src="KT0603R",
     desc="Status LED")
if VARIANT == "module":
    part("J1", "Connector_Generic:Conn_01x06", "DEBUG", "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
         {"1": "U0TXD", "2": "U0RXD", "3": "USB_DP", "4": "USB_DM", "5": "BTN_USER", "6": "GND"}, dnp=True,
         desc="Debug/programming pads (not fitted): 1 TX 2 RX 3 D+ 4 D- 5 BOOT 6 GND; board powered by the cell")
else:
    part("J1", "Connector_Generic:Conn_02x03_Odd_Even", "DEBUG",
         "Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical",
         {"1": "U0TXD_J", "2": "U0RXD", "3": "USB_DP", "4": "USB_DM", "5": "BTN_USER", "6": "GND"}, dnp=True,
         desc="Debug/programming pads (not fitted), 2x3: 1 TX 2 RX 3 D+ 4 D- 5 BOOT 6 GND; board powered by the cell")

# ------------------------------------------------------------------ sensor
part("U5", "Sensor_Humidity:SHT4x", "SHT40-AD1B-R3",
     "Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad",
     {"1": "I2C_SDA", "2": "I2C_SCL", "3": "+3V3", "4": "GND"}, src="SHT40", desc="I2C address 0x44")
part("C29", "Device:C", "100nF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="100n", desc="SHT40 bypass")
part("R26", "Device:R", "10k", FP_R0603, {"1": "+3V3", "2": "I2C_SDA"}, src="10k", desc="I2C pull-up")
part("R27", "Device:R", "10k", FP_R0603, {"1": "+3V3", "2": "I2C_SCL"}, src="10k", desc="I2C pull-up")

# ------------------------------------------------------------------ cell voltage sense
part("R31", "Device:R", "470k", FP_R0603, {"1": "VBAT", "2": "VBAT_SENSE"}, src="470k", desc="Divider top")
part("R32", "Device:R", "470k", FP_R0603, {"1": "VBAT_SENSE", "2": "SNS_LO"}, src="470k", desc="Divider bottom")
part("C31", "Device:C", "22nF", FP_C0603, {"1": "VBAT_SENSE", "2": "GND"}, src="22n", desc="ADC hold cap, tau 5.2 ms")
part("Q3", "th_sensor:2N7002", "2N7002", FP_SOT23, {"1": "VBAT_MEAS_EN", "2": "GND", "3": "SNS_LO"},
     src="2N7002", desc="Divider low-side switch")
part("R35", "Device:R", "1M", FP_R0603, {"1": "VBAT_MEAS_EN", "2": "GND"}, src="1M",
     desc="Keeps the sense switch off in reset/sleep")

# ------------------------------------------------------------------ test points, mechanics
TEST_PADS = ["VBAT", "VIN", "VOUT", "+3V3", "GND", "EN"]
for i, net in enumerate(TEST_PADS, 1):
    part(f"TP{i}", "Connector:TestPoint", net.replace("+", ""), "TestPoint:TestPoint_Pad_D1.5mm", {"1": net},
         in_bom=False, desc="Test pad")
part("FID1", "Mechanical:Fiducial", "FID", "Fiducial:Fiducial_1mm_Mask2mm", {}, in_bom=False)
part("FID2", "Mechanical:Fiducial", "FID", "Fiducial:Fiducial_1mm_Mask2mm", {}, in_bom=False)


def nets():
    """net name -> sorted list of (ref, pin)"""
    out = {}
    for p in PARTS:
        for pin, net in p["pins"].items():
            if net:
                out.setdefault(net, []).append((p["ref"], pin))
    return {k: sorted(v) for k, v in sorted(out.items())}


if __name__ == "__main__":
    for net, members in nets().items():
        print(f"{net:14s} {len(members):3d}  " + " ".join(f"{r}.{p}" for r, p in members[:12]))
    print(len(PARTS), "parts")
