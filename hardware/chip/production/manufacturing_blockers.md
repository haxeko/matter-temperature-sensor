# Manufacturing blockers and open checks (Rev A)

Status from the JLC parts snapshot taken 2026-11-06 07:12 UTC (`jlc_parts_snapshot.jsonl`).
Nothing here has been ordered. Re-run `tools/jlc_lookup.py` and this script before ordering.

## Blocking

- **U4 (ESP32-H2FH4S, C50392664)**: JLC stock 0. Options: consigned parts (JLC global sourcing or customer-supplied), or order the bare PCB + JLC assembly without it and hand-solder it (docs/assembly.md).

## Low stock (< 1000 at snapshot time)

- U3 (TPS3839K33DBZR, C96333): 745 pcs

## Extended parts (each adds JLC's extended-part setup fee)

- BT1: BS-24-B4AA016 (C964809)
- C5: RVT470UF6.3V67RV0038 (C2901342)
- C51,C52: GRM0335C1H1R5BA01D (C161414)
- L1: DFE201612E-2R2M=P2 (C337893)
- L3: LQW18AN24NG00D (C162644)
- L4: LQP03TN2N4B02D (C98042)
- R3: 0603WAF1052T5E (C22855)
- R4: 0603WAF1622T5E (C22885)
- R40: 0603WAF4990T5E (C23065)
- R41: 0201WMF0000TEE (C473473)
- U1: TPS63900DSKR (C1518762)
- U3: TPS3839K33DBZR (C96333)
- U4: ESP32-H2FH4S (C50392664)
- U5: SHT40-AD1B-R3 (C2848306)
- Y2: X322532MLB4SI (C5210649)

## Checks that need a person

- Placement preview: every line of `orientation_check.md` (holder, electrolytic, LED, ICs, MOSFETs).
- Holder BT1 (MYOUNG BS-24-B4AA016): its + terminal must sit on pad 1, at the silkscreen '+' (right). The footprint is drawn from the LCSC datasheet; compare it with a real part first (docs/assembly.md).
- C5 (470 uF electrolytic): + pad up, towards the converter; reversed, it leaks heavily, drains the cell and degrades.
- J1 is not fitted / not in the BOM (debug pads only).
- Test pads TP1..TP6 (silkscreen shows their net names) and fiducials have no parts.
- PCB options: 4 layers, 1.6 mm, JLC stack-up JLC04161H-7628 with impedance control (50 ohm single-ended on L1 over the L2 ground; 0.35 mm computed, confirm with JLC's calculator), tented vias, ENIG (flat pads for the QFN and 0201 parts). The SHT40 tongue is cut free by a 1 mm L-shaped slot from the top edge (routed, not V-cut).
- U4 (QFN32, 0.4 mm pitch) has 9 GND vias in its exposed pad (HDG minimum): ask for via filling/plugging or accept some solder wicking.
- RF parts C51/L4/C52/R41 are 0201 and only start values; L5 is not fitted. The PCB antenna AE1 is copper only (no part) and has not been measured: see docs/chip_variant.md.
- Y2 (32 MHz): pin 1 must match orientation_check.md (a 90-degree error puts a crystal terminal on a ground pad); load caps C49/C50 are start values.
- Nothing here proves the design works: see docs/test_plan.md (no prototype has been built).
