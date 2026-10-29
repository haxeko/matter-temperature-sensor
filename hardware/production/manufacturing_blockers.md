# Manufacturing blockers and open checks (Rev A)

Status from the JLC parts snapshot taken 2026-10-29 08:55 UTC (`jlc_parts_snapshot.jsonl`).
Nothing here has been ordered. Re-run `tools/jlc_lookup.py` and this script before ordering.

## Blocking

- **U4 (ESP32-H2-MINI-1-H4S, C47967030)**: JLC stock 0. Options: consigned parts (JLC global sourcing or customer-supplied), or order the bare PCB + JLC assembly without it and hand-solder it (docs/assembly.md).

## Low stock (< 1000 at snapshot time)

- BT1,BT2 (1060TR, C238069): 301 pcs
- U3 (TPS3839K33DBZR, C96333): 844 pcs

## Extended parts (each adds JLC's extended-part setup fee)

- BT1,BT2: 1060TR (C238069)
- L1,L2: DFE201612E-2R2M=P2 (C337893)
- R3,R13: 0603WAF1052T5E (C22855)
- R4,R14: 0603WAF1622T5E (C22885)
- U1,U2: TPS63900DSKR (C1518762)
- U3: TPS3839K33DBZR (C96333)
- U4: ESP32-H2-MINI-1-H4S (C47967030)
- U5: SHT40-AD1B-R3 (C2848306)

## Checks that need a person

- Placement preview: every line of `orientation_check.md` (holders, diodes, LED, ICs, MOSFETs).
- Holders BT1/BT2 (Keystone 1060TR): the + retainer side must match the silkscreen '+' mark.
- J1 and JP1 are not fitted / not in the BOM (debug only).
- Test pads TP1..TP11 (silkscreen shows their net names) and fiducials have no parts.
- PCB options: 2 layers, 1.6 mm FR-4, 1 oz, tented vias (set in the board file), lead-free HASL or ENIG. The SHT40 tongue is cut by two 1 mm slots (routed, not V-cut).
- Nothing here proves the design works: see docs/test_plan.md (no prototype has been built).
