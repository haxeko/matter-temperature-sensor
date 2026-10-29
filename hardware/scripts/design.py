"""
TH-SENSOR-H2 Rev A - single source of truth for the electrical design.

Every part: reference, symbol, footprint, value, sourcing fields and the net of
every pin. gen_schematic.py draws the schematic from this table and then
checks the netlist exported by KiCad against it (parity); gen_pcb.py loads the
nets from the KiCad netlist.

Sourcing fields were looked up on the JLCPCB parts API on 2026-10-29
(tools/jlc_lookup.py); stock and Basic/Extended status change daily and must be
re-checked before ordering (docs/assembly.md).
"""

PROJECT = "th_sensor_h2"
TITLE = "TH-SENSOR-H2 thermo-hygrometer"
REV = "A"
DATE = "2026-10-29"

KSYM = "/usr/share/kicad/symbols/"
# Espressif KiCad libraries (github.com/espressif/kicad-libraries, git dd76561812ab300351234ba6e0ec1295641796f0).
# Only needed to refresh the vendored copies in hardware/kicad/lib; without it the generators use those copies.
import os as _os
ESPRESSIF_LIB = _os.environ.get("ESPRESSIF_KICAD_LIB", "/tmp/claude-0/ext/espressif-kicad-libraries")

# symbol sources: lib_id -> (library file, symbol name in that file, nick)
SYMBOLS = {
    "Device:R": (KSYM + "Device.kicad_sym", "R"),
    "Device:C": (KSYM + "Device.kicad_sym", "C"),
    "Device:L": (KSYM + "Device.kicad_sym", "L"),
    "Device:D_Schottky": (KSYM + "Device.kicad_sym", "D_Schottky"),
    "Device:LED": (KSYM + "Device.kicad_sym", "LED"),
    "Device:Battery_Cell": (KSYM + "Device.kicad_sym", "Battery_Cell"),
    "Device:Crystal": (KSYM + "Device.kicad_sym", "Crystal"),
    "Switch:SW_Push": (KSYM + "Switch.kicad_sym", "SW_Push"),
    "Connector:TestPoint": (KSYM + "Connector.kicad_sym", "TestPoint"),
    "Connector_Generic:Conn_01x07": (KSYM + "Connector_Generic.kicad_sym", "Conn_01x07"),
    "Jumper:SolderJumper_2_Open": (KSYM + "Jumper.kicad_sym", "SolderJumper_2_Open"),
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
    "th_sensor:AO3401A": (KSYM + "Transistor_FET.kicad_sym", "AO3401A"),
    "th_sensor:2N7002": (KSYM + "Transistor_FET.kicad_sym", "2N7002"),
}

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
    "22R": ("C23345", "UNI-ROYAL", "0603WAF220JT5E"),
    "100n": ("C14663", "YAGEO", "CC0603KRX7R9BB104"),
    "1u": ("C15849", "Samsung", "CL10A105KB8NNNC"),
    "10u": ("C19702", "Samsung", "CL10A106KP8NNNC"),
    "22u_0805": ("C45783", "Samsung", "CL21A226MAQNNNE"),
    "100u_1206": ("C15008", "Samsung", "CL31A107MQHNNNE"),
    "22n": ("C21122", "Samsung", "CL10B223KB8NNNC"),
    "18p": ("C1647", "Samsung", "CL10C180JB8NNNC"),
    "AO3401A": ("C15127", "Alpha & Omega", "AO3401A"),
    "2N7002": ("C8545", "JSCJ", "2N7002"),
    "B5819W": ("C8598", "JSCJ", "B5819W SL"),
    "TPS63900": ("C1518762", "Texas Instruments", "TPS63900DSKR"),
    "TPS3839K33": ("C96333", "Texas Instruments", "TPS3839K33DBZR"),
    "DFE201612E": ("C337893", "Murata", "DFE201612E-2R2M=P2"),
    "1060TR": ("C238069", "Keystone", "1060TR"),
    "H2MINI": ("C47967030", "Espressif", "ESP32-H2-MINI-1-H4S"),
    "SHT40": ("C2848306", "Sensirion", "SHT40-AD1B-R3"),
    "FC135": ("C32346", "Seiko Epson", "Q13FC13500004"),
    "TS1187A": ("C318884", "XKB", "TS-1187A-B-A-B"),
    "KT0603R": ("C2286", "KENTO", "KT-0603R"),
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


# ------------------------------------------------------------------ power path, one per cell
def cell_path(n, o):
    """Cell n (1/2); o = reference offset (0 / 10)."""
    vb, vbl, vin, vout = f"VBAT{n}", f"VBAT{n}_L", f"VIN{n}", f"VOUT{n}"
    part(f"BT{n}", "Device:Battery_Cell", "CR2032 holder", "Battery:BatteryHolder_Keystone_1060_1x2032",
         {"1": vb, "2": "GND"}, src="1060TR", desc=f"Cell {n}: Keystone 1060 SMT holder (pad 1 = + clip)")
    part(f"R{1 + o}", "Device:R", "0R", FP_R0805, {"1": vb, "2": vbl}, src="0R_0805",
         desc=f"Cell {n} current-measurement link (remove, insert ammeter)")
    part(f"Q{n}", "th_sensor:AO3401A", "AO3401A", FP_SOT23, {"1": "GND", "2": vin, "3": vbl}, src="AO3401A",
         desc="Reverse-polarity P-MOSFET (body diode forward, Vgs = -Vcell)")
    part(f"C{1 + o}", "Device:C", "10uF", FP_C0603, {"1": vin, "2": "GND"}, src="10u",
         spec="10V X5R 0603", desc="TPS63900 input cap, next to VIN")
    part(f"C{2 + o}", "Device:C", "100uF", FP_C1206, {"1": vin, "2": "GND"}, src="100u_1206",
         spec="6.3V X5R 1206", desc="Input buffer (coin cell pulse support)")
    part(f"C{3 + o}", "Device:C", "100uF", FP_C1206, {"1": vin, "2": "GND"}, src="100u_1206",
         spec="6.3V X5R 1206", desc="Input buffer (coin cell pulse support)")
    part(f"U{n}", "Regulator_Switching:TPS63900", "TPS63900DSKR",
         "Package_SON:WSON-10-1EP_2.5x2.5mm_P0.5mm_EP1.2x2mm",
         {"10": vin, "1": vin, "2": vin, "9": f"LX1_{n}", "7": f"LX2_{n}", "6": vout,
          "3": f"CFG1_{n}", "4": f"CFG2_{n}", "5": f"CFG3_{n}", "8": "GND", "11": "GND"},
         src="TPS63900", desc="Buck-boost, SEL=H -> VO(2) = 3.4 V, input current limit 100 mA")
    part(f"R{2 + o}", "Device:R", "0R", FP_R0603, {"1": f"CFG1_{n}", "2": "GND"}, src="0R_0603",
         desc="RCFG1: VO(2) = 3.4 V (SLVSET3D table 7-2)")
    part(f"R{3 + o}", "Device:R", "10.5k", FP_R0603, {"1": f"CFG2_{n}", "2": "GND"}, src="10.5k",
         spec="1% 100ppm 0603", desc="RCFG2: 100 mA input current limit at VO(2) >= 3.4 V (option 13.3k = 50 mA)")
    part(f"R{4 + o}", "Device:R", "16.2k", FP_R0603, {"1": f"CFG3_{n}", "2": "GND"}, src="16.2k",
         spec="1% 100ppm 0603", desc="RCFG3: VO(1) = 3.3 V (unused, SEL tied high)")
    part(f"L{n}", "Device:L", "2.2uH", "th_sensor:L_Murata_DFE201612E", {"1": f"LX1_{n}", "2": f"LX2_{n}"},
         src="DFE201612E", desc="2.2 uH, Isat 2.4 A, 116 mOhm")
    part(f"C{4 + o}", "Device:C", "22uF", FP_C0805, {"1": vout, "2": "GND"}, src="22u_0805",
         spec="25V X5R 0805", desc="TPS63900 output cap, next to VOUT")
    part(f"D{n}", "Device:D_Schottky", "B5819W", "Diode_SMD:D_SOD-123", {"1": "3V3_PWR", "2": vout},
         src="B5819W", desc="Output OR-ing; second barrier against charging a cell")


cell_path(1, 0)
cell_path(2, 10)

# ------------------------------------------------------------------ 3V3 rail, supervisor, reset
part("C21", "Device:C", "100uF", FP_C1206, {"1": "3V3_PWR", "2": "GND"}, src="100u_1206",
     spec="6.3V X5R 1206", desc="Rail bulk")
part("C22", "Device:C", "100uF", FP_C1206, {"1": "3V3_PWR", "2": "GND"}, src="100u_1206",
     spec="6.3V X5R 1206", desc="Rail bulk")
part("R21", "Device:R", "0R", FP_R0805, {"1": "3V3_PWR", "2": "+3V3"}, src="0R_0805",
     desc="Load current-measurement link (module, sensor, LED, supervisor)")
part("JP1", "Jumper:SolderJumper_2_Open", "DEBUG_PWR", "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
     {"1": "3V3_DBG", "2": "3V3_PWR"}, in_bom=False, desc="Close to power the board from J1 pin 6 (<= 3.6 V, cells removed)")
part("U3", "Power_Supervisor:TPS3839DBZ", "TPS3839K33DBZR", FP_SOT23, {"3": "+3V3", "1": "GND", "2": "nRST"},
     src="TPS3839K33", desc="2.93 V supervisor, push-pull, 200 ms delay")
part("C26", "Device:C", "100nF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="100n", desc="U3 bypass")
part("R22", "Device:R", "10k", FP_R0603, {"1": "nRST", "2": "EN"}, src="10k",
     desc="Isolates the push-pull supervisor from the RST button / J1")
part("C25", "Device:C", "1uF", FP_C0603, {"1": "EN", "2": "GND"}, src="1u", desc="EN RC (Espressif reference)")
part("SW2", "Switch:SW_Push", "RST", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A", {"1": "EN", "2": "GND"},
     src="TS1187A", desc="Reset")

# ------------------------------------------------------------------ module
part("U4", "th_sensor:ESP32-H2-MINI-1", "ESP32-H2-MINI-1-H4S", "th_sensor:ESP32-H2-MINI-1",
     {"3": "+3V3", "15": "+3V3", "8": "EN",
      "16": "VBAT_MEAS_EN", "19": "VBAT1_SENSE", "18": "VBAT2_SENSE",
      "12": "XTAL_32K_P", "13": "XTAL_32K_N",
      "20": "I2C_SDA", "21": "I2C_SCL", "24": "LED", "22": "STRAP_GPIO8", "23": "BTN_USER",
      "26": "USB_DM", "27": "USB_DP", "30": "U0RXD", "31": "U0TXD",
      "5": None, "6": None, "9": None, "10": None, "25": None,
      **{str(p): "GND" for p in [1, 2, 11, 14] + list(range(36, 54))}},
     src="H2MINI", desc="4 MB flash, PCB antenna; JLC stock 0 on 2026-10-29")
part("C23", "Device:C", "10uF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="10u", spec="10V X5R 0603", desc="Module decoupling")
part("C24", "Device:C", "100nF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="100n", desc="Module decoupling")
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
part("R28", "Device:R", "22R", FP_R0603, {"1": "USB_DM", "2": "USB_DM_J"}, src="22R", desc="USB D- series")
part("R29", "Device:R", "22R", FP_R0603, {"1": "USB_DP", "2": "USB_DP_J"}, src="22R", desc="USB D+ series")
part("J1", "Connector_Generic:Conn_01x07", "DEBUG", "Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical",
     {"1": "U0TXD", "2": "U0RXD", "3": "USB_DP_J", "4": "USB_DM_J", "5": "BTN_USER", "6": "3V3_DBG",
      "7": "GND"}, dnp=True,
     desc="Debug/programming pads (not fitted): 1 TX 2 RX 3 D+ 4 D- 5 BOOT 6 3V3_DBG 7 GND")

# ------------------------------------------------------------------ sensor
part("U5", "Sensor_Humidity:SHT4x", "SHT40-AD1B-R3",
     "Sensor_Humidity:Sensirion_DFN-4_1.5x1.5mm_P0.8mm_SHT4x_NoCentralPad",
     {"1": "I2C_SDA", "2": "I2C_SCL", "3": "+3V3", "4": "GND"}, src="SHT40", desc="I2C address 0x44")
part("C29", "Device:C", "100nF", FP_C0603, {"1": "+3V3", "2": "GND"}, src="100n", desc="SHT40 bypass")
part("R26", "Device:R", "10k", FP_R0603, {"1": "+3V3", "2": "I2C_SDA"}, src="10k", desc="I2C pull-up")
part("R27", "Device:R", "10k", FP_R0603, {"1": "+3V3", "2": "I2C_SCL"}, src="10k", desc="I2C pull-up")

# ------------------------------------------------------------------ cell voltage sense
for n, o in ((1, 0), (2, 2)):
    part(f"R{31 + o}", "Device:R", "470k", FP_R0603, {"1": f"VBAT{n}", "2": f"VBAT{n}_SENSE"}, src="470k",
         desc="Divider top")
    part(f"R{32 + o}", "Device:R", "470k", FP_R0603, {"1": f"VBAT{n}_SENSE", "2": f"SNS{n}_LO"}, src="470k",
         desc="Divider bottom")
    part(f"C{31 + n - 1}", "Device:C", "22nF", FP_C0603, {"1": f"VBAT{n}_SENSE", "2": "GND"}, src="22n",
         desc="ADC hold cap, tau 5.2 ms")
    part(f"Q{2 + n}", "th_sensor:2N7002", "2N7002", FP_SOT23, {"1": "VBAT_MEAS_EN", "2": "GND", "3": f"SNS{n}_LO"},
         src="2N7002", desc="Divider low-side switch")
part("R35", "Device:R", "1M", FP_R0603, {"1": "VBAT_MEAS_EN", "2": "GND"}, src="1M",
     desc="Keeps the sense switches off in reset/sleep")

# ------------------------------------------------------------------ test points, mechanics
TEST_PADS = ["VBAT1", "VBAT2", "VIN1", "VIN2", "VOUT1", "VOUT2", "3V3_PWR", "+3V3", "GND", "GND", "EN"]
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
