# Manufacturing blockers and open checks (Rev A)

Status from the JLC parts snapshot taken 2026-11-06 17:00 UTC (`jlc_parts_snapshot.jsonl`).
Nothing here has been ordered. Re-run `tools/jlc_lookup.py` and this script before ordering.

## Blocking

- none in the BOM (U4, the module, is bought separately by the user: see below)

## Low stock (< 1000 at snapshot time)

- U3 (TPS3839K33DBZR, C96333): 749 pcs

## Extended parts (each adds JLC's extended-part setup fee)

- BT1: BS-24-B4AA016 (C964809)
- C5: RVT470UF6.3V67RV0038 (C2901342)
- L1: DFE201612E-2R2M=P2 (C337893)
- R3: 0603WAF1052T5E (C22855)
- R4: 0603WAF1622T5E (C22885)
- U1: TPS63900DSKR (C1518762)
- U3: TPS3839K33DBZR (C96333)
- U5: SHT40-AD1B-R3 (C2848306)

## Checks that need a person

- Placement preview: every line of `orientation_check.md` (holder, electrolytic, LED, ICs, MOSFETs).
- Holder BT1 (MYOUNG BS-24-B4AA016): its + terminal must sit on pad 1, at the silkscreen '+' (on the back, left seen from the top). The footprint is drawn from the LCSC datasheet; compare it with a real part first (docs/assembly.md).
- C5 (470 uF electrolytic): + pad left, at the board edge; reversed, it leaks heavily, drains the cell and degrades.
- J1 is not fitted / not in the BOM (debug pads only).
- Test pads TP1..TP6 (silkscreen shows their net names) and fiducials have no parts.
- PCB options: 4 layers, 1.6 mm, JLC stack-up JLC04161H-7628 (no impedance control needed: no RF line on this board), tented vias (set in the board file: there are vias under the cell), lead-free HASL or ENIG. The SHT40 tongue is cut free by a 1 mm L-shaped slot from the left edge (routed, not V-cut).
- U4 (ESP32-H2-WROOM-02C-H4S) is NOT in this BOM/CPL: the user buys it and solders it by hand (castellated pads with an iron; the thermal pad from the back through the 0.8 mm hole, docs/wroom_variant.md). Its PCB antenna must overhang the top edge.
- Two-sided assembly: BT1 (holder) is on the BOTTOM side (CPL layer Bottom), everything else on top. Either order assembly on both sides, or order top-side assembly only and hand-solder BT1 (two large pads). Its + terminal is on the LEFT seen from the top (pad 1, '+' on the back silkscreen).
- Nothing here proves the design works: see docs/test_plan.md (no prototype has been built).
