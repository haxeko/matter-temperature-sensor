# Manufacturing blockers and open checks (Rev A)

Status from the JLC parts snapshot taken 2026-11-11 02:15 UTC (`jlc_parts_snapshot.jsonl`).
Nothing here has been ordered. Re-run `tools/jlc_lookup.py` and this script before ordering.

## Blocking

- none in the BOM (U4, the module, is bought separately by the user: see below)

## Low stock (< 1000 at snapshot time)

- U3 (TPS3839K33DBZR, C96333): 733 pcs

## Extended parts (each adds JLC's extended-part setup fee)

- F1: BSMD1206-050-6V (C883122)
- L1: DFE201612E-2R2M=P2 (C337893)
- R3: 0603WAF1052T5E (C22855)
- R4: 0603WAF1622T5E (C22885)
- SW1: EVQP7A01P (C79167)
- U1: TPS63900DSKR (C1518762)
- U3: TPS3839K33DBZR (C96333)
- U5: SHT40-AD1B-R3 (C2848306)

## Checks that need a person

- Placement preview: every line of `orientation_check.md` (LED, ICs, MOSFETs).
- The cell is NOT on this board. BT1 is two plated 1.0 mm holes on the left edge for the wires from a CR123A holder mounted beside the board: square pad = + (marked '+' on both sides), round pad = -. No holder is in the BOM/CPL; the user chooses and wires it (docs/cr123a_variant.md).
- No bulk capacitor C5 on this board (the CR123A supplies the radio bursts); F1 (resettable fuse) is not polarised.
- J1 is not fitted / not in the BOM (debug pads only, on the back).
- Test pads TP1..TP6 (silkscreen shows their net names; on the back) and fiducials have no parts.
- PCB options: 2 layers, 1.6 mm FR-4, 1 oz, standard process (0.3 mm via holes; no impedance control needed: no RF line on this board), tented vias (set in the board file), lead-free HASL or ENIG. The SHT40 tongue is cut free by a 1 mm L-shaped slot from the left edge (routed, not V-cut).
- U4 (ESP32-H2-WROOM-02C-H4S) is NOT in this BOM/CPL: the user buys it and solders it by hand (castellated pads with an iron; the thermal pad from the back through the 0.8 mm hole, docs/wroom_variant.md). Its PCB antenna must overhang the top edge.
- One-sided assembly: every part is on the top side; the back carries only bare pads (J1, TP1..TP6) and the two wire holes.
- Firmware for this board: build with the sdkconfig.defaults.cr123a overlay (docs/cr123a_variant.md).
- Nothing here proves the design works: see docs/test_plan.md (no prototype has been built).
