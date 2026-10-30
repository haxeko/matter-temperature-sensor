# Manufacturing blockers and open checks (Rev B)

Status from the JLC parts snapshot taken 2026-10-30 06:47 UTC (`jlc_parts_snapshot.jsonl`).
Nothing here has been ordered. Re-run `tools/jlc_lookup.py` and this script before ordering.

## Blocking

- **U4 (ESP32-H2-MINI-1-H4S, C47967030)**: JLC stock 0. Options: consigned parts (JLC global sourcing or customer-supplied), or order the bare PCB + JLC assembly without it and hand-solder it (docs/assembly.md).

## Low stock (< 1000 at snapshot time)

- BT1 (BS-24-B4AA016, C964809): 660 pcs
- U3 (TPS3839K33DBZR, C96333): 844 pcs

## Extended parts (each adds JLC's extended-part setup fee)

- BT1: BS-24-B4AA016 (C964809)
- C5: RVT470UF6.3V67RV0038 (C2901342)
- L1: DFE201612E-2R2M=P2 (C337893)
- R3: 0603WAF1052T5E (C22855)
- R4: 0603WAF1622T5E (C22885)
- U1: TPS63900DSKR (C1518762)
- U3: TPS3839K33DBZR (C96333)
- U4: ESP32-H2-MINI-1-H4S (C47967030)
- U5: SHT40-AD1B-R3 (C2848306)

## Checks that need a person

- Placement preview: every line of `orientation_check.md` (holder, electrolytic, LED, ICs, MOSFETs).
- Holder BT1 (MYOUNG BS-24-B4AA016): its + terminal must sit on pad 1, at the silkscreen '+' (right). The footprint is drawn from the LCSC datasheet; compare it with a real part first (docs/assembly.md).
- C5 (470 uF electrolytic): + pad up, towards the converter; reversed, it leaks heavily, drains the cell and degrades.
- J1 is not fitted / not in the BOM (debug pads only).
- Test pads TP1..TP6 (silkscreen shows their net names) and fiducials have no parts.
- PCB options: 2 layers, 1.6 mm FR-4, 1 oz, tented vias (set in the board file), lead-free HASL or ENIG. The SHT40 tongue is cut free by a 1 mm L-shaped slot that opens into the antenna notch (routed, not V-cut).
- Nothing here proves the design works: see docs/test_plan.md (no prototype has been built).
