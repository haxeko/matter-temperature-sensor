# Manufacturing blockers and open checks (Rev A)

Status from the JLC parts snapshot taken 2026-11-11 02:15 UTC (`jlc_parts_snapshot.jsonl`).
Nothing here has been ordered. Re-run `tools/jlc_lookup.py` and this script before ordering.

## Blocking

- none in the BOM (U4, the module, is bought separately by the user: see below)

## Low stock (< 1000 at snapshot time)

- U3 (TPS3839K33DBZR, C96333): 733 pcs

## Extended parts (each adds JLC's extended-part setup fee)

- BT1: BH-123A-A1CJ002 (C5290177)
- F1: BSMD1206-050-6V (C883122)
- L1: DFE201612E-2R2M=P2 (C337893)
- R3: 0603WAF1052T5E (C22855)
- R4: 0603WAF1622T5E (C22885)
- SW1: EVQP7A01P (C79167)
- U1: TPS63900DSKR (C1518762)
- U3: TPS3839K33DBZR (C96333)
- U5: SHT40-AD1B-R3 (C2848306)

## Checks that need a person

- Placement preview: every line of `orientation_check.md` (holder, LED, ICs, MOSFETs).
- Holder BT1 (MYOUNG BH-123A-A1CJ002, through-hole): its + terminal goes in the square pad at the top (silkscreen '+'), the locating post in the 2.0 mm hole next to it; the post makes a reversed holder impossible if the footprint is right. The footprint is drawn from drawing MY-CP-0398 in the LCSC datasheet, including the side of the locating post: compare it with a real holder first (docs/cr123a_variant.md). BT1 is in the BOM and the CPL as a through-hole part: order JLC's through-hole assembly for it or solder its two pins by hand.
- No bulk capacitor C5 on this board (the CR123A supplies the radio bursts); F1 (resettable fuse) is not polarised.
- J1 is not fitted / not in the BOM (debug pads only).
- Test pads TP1..TP6 (silkscreen shows their net names) and fiducials have no parts.
- PCB options: 4 layers, 1.6 mm, JLC stack-up JLC04161H-7628 (no impedance control needed: no RF line on this board), tented vias (set in the board file), lead-free HASL or ENIG. The SHT40 tongue is cut free by a 1 mm L-shaped slot from the right edge (routed, not V-cut).
- U4 (ESP32-H2-WROOM-02C-H4S) is NOT in this BOM/CPL: the user buys it and solders it by hand (castellated pads with an iron; the thermal pad from the back through the 0.8 mm hole, docs/wroom_variant.md). Its PCB antenna must overhang the top edge.
- One-sided assembly: every part is on the top side. Fit the holder last (it covers nothing, but it is the tallest part).
- Firmware for this board: build with the sdkconfig.defaults.cr123a overlay (docs/cr123a_variant.md).
- Nothing here proves the design works: see docs/test_plan.md (no prototype has been built).
