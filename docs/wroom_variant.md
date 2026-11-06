# TH-SENSOR-H2W Rev A — biến thể dùng module ESP32-H2-WROOM-02C, bo vuông

Biến thể của TH-SENSOR-H2 Rev B dùng **module ESP32-H2-WROOM-02C-H4S** (20 × 18 × 3.2 mm, 4 MB flash, ăng-ten PCB trên module) thay cho ESP32-H2-MINI-1-H4S, trên một bo **4 lớp nhỏ nhất có thể và vuông khi tính cả phần ăng-ten của module nhô ra ngoài mép bo**. Mạch điện giữ như Rev B: 1 × CR2450, AO3401A, TPS63900 3.3 V, tụ đệm 10 µF + 2 × 100 µF + 470 µF, giám sát áp, SHT40 trên lưỡi tách nhiệt, hai nút, LED, cầu đo pin, J1 debug; **firmware giống hệt** (mọi GPIO giữ chức năng). Rev B và H2C không thay đổi.

Yêu cầu của người dùng ngày 2026-11-06: "thiết kế bản sử dụng module wroom, kích thước nhỏ nhất có thể, kích thước vuông tính cả phần ăng ten nhô ra của module" và "dùng module wroom h2-02c, nhưng cái này tôi sẽ tự mua và hàn". Vì vậy U4 **không có trong BOM/CPL của JLC**; footprint được làm để hàn tay (mục 4).

## 1. Trạng thái

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Schematic: ERC | ĐÃ XÁC MINH: 0 lỗi, 0 cảnh báo | `hardware/wroom/reports/erc_report.txt` |
| PCB: DRC + schematic parity | ĐÃ XÁC MINH: 0 vi phạm, 0 pad chưa nối, 0 lỗi parity (mọi mức) | `hardware/wroom/reports/drc_report.txt` |
| Pin map firmware ↔ module | ĐÃ XÁC MINH | `python3 tools/check_pinmap.py --variant wroom` |
| Kích thước: bo 37.6 × 31.6 mm, ăng-ten nhô 6.0 mm ⇒ khung 37.6 × 37.6 mm | ĐÃ XÁC MINH trên file board (Edge.Cuts, footprint U4) | mục 2 |
| Gerber 4 lớp, drill, BOM (27 dòng), CPL (40 linh kiện, BT1 ở mặt dưới) | ĐÃ XÁC MINH là sinh được; **chưa gửi nhà máy** | `hardware/wroom/production/` |
| Tái tạo giống từng byte (schematic, board, project, thư viện) | ĐÃ XÁC MINH (chạy hai lần) | mục 11 |
| Symbol, footprint WROOM-02C | vẽ theo datasheet v1.2 (bảng 2, hình 7); **chưa so với module thật** | mục 4 |
| Hiệu năng ăng-ten của module trên bo này, tầm phủ | **CHƯA KIỂM THỬ** | mục 5, 10 |
| Hàn tay module (cạnh + pad tản nhiệt qua lỗ) | **CHƯA KIỂM THỬ** | mục 4, 9 |
| Điện, cảm biến, Matter, dòng ngủ | **CHƯA KIỂM THỬ** (như Rev B) | `docs/test_plan.md` |

Không có bo nào được đặt, làm hay đo. Không tuyên bố chứng nhận nào; datasheet WROOM-02C ghi "RF certification: See certificates" cho module — module nằm đúng vị trí khuyến nghị nhưng điều đó không phải là chứng nhận cho sản phẩm.

## 2. Kích thước — vì sao 37.6 × 37.6 mm

- Thứ quyết định bề rộng là **land pattern của holder CR2450** BS-24-B4AA016: 37.00 mm tính tới mép ngoài hai pad (bản vẽ MY-CP-0138). Cộng khoảng cách đồng–mép 0.3 mm mỗi bên (luật của dự án, JLC cho phép ≥ 0.2 mm với mép phay) ⇒ **W = 37.6 mm**. Pin không thể đứng dọc để thu nhỏ: khi đó chiều cao bo ≥ 37.6 mm và khung vuông còn lớn hơn.
- Holder nằm ở **mặt dưới**, mọi linh kiện khác ở mặt trên, nên module và pin chồng lên nhau theo hình chiếu. Bo cao **H = W − 6.0 = 31.6 mm**: vùng ăng-ten 6 mm của module nằm ngoài mép trên, nên cả cụm (bo + ăng-ten) vừa khít **37.6 × 37.6 mm**. Mép phải của module cách mép bo 0.8 mm (pad răng cưa ló ra 0.5 mm ngoài thân module, cộng 0.3 mm tới mép).
- Mật độ: mặt trên chứa 48 linh kiện + module; 24 ký hiệu linh kiện không còn chỗ trên silkscreen (vẫn có trên lớp Fab, `hardware/wroom/production/assembly_top.pdf`). Nhỏ hơn nữa thì phải bỏ hoặc thay linh kiện (ví dụ tụ điện phân C5, nút 5 × 5 mm) — không làm khi chưa hỏi.
- Góc trên phải vuông (pad chân 28 của module cách hai mép 0.3 mm), ba góc còn lại bo tròn R1.5.

## 3. Khác biệt so với Rev B (module MINI-1)

| | Rev B (MINI-1) | H2W Rev A (WROOM-02C) |
|---|---|---|
| Module | ESP32-H2-MINI-1-H4S, 13.2 × 16.6 mm, trong BOM JLC (tồn kho 0) | ESP32-H2-WROOM-02C-H4S, 18 × 20 mm, **người dùng tự mua và hàn**, không trong BOM/CPL |
| Bo | 41.5 × 57.5 mm, 2 lớp | **37.6 × 31.6 mm (37.6 × 37.6 tính cả ăng-ten)**, 4 lớp |
| Ăng-ten | trên bo, rãnh khoét 16.2 × 6 mm cạnh ăng-ten | **nhô ra ngoài mép trên** (vị trí ③ của HDG, mục 5) |
| Holder CR2450 | mặt trên | **mặt dưới**, + bên trái (nhìn từ trên) |
| Test pad | mặt trên | mặt trên (cùng 6 điểm, silkscreen ghi tên net) |
| J1 debug | 1 × 6 dưới rãnh ăng-ten | 2 × 3 (không lắp) ở góc dưới phải, xa ăng-ten nhất; chân như cũ: 1 TX, 2 RX, 3 D+, 4 D−, 5 BOOT, 6 GND |
| C23 10 µF | cạnh pad 3V3 | cạnh chân 14 (VBAT, nối 3V3 trong module); C24 100 nF cạnh chân 1 |
| Via | 0.6 / 0.3 mm | 0.45 / 0.2 mm (124) và 0.6 / 0.3 mm (18, đường nguồn) |
| Số linh kiện trong `design.py` | 50 | 50 (U4 và J1 khác) |
| Dòng BOM / linh kiện gắn máy | 28 / 41 | 27 / 40 (không có module) |
| File | `hardware/kicad`, `hardware/production`, … | `hardware/wroom/kicad`, `hardware/wroom/production`, … |
| Firmware | — | **giống hệt** (cần bản -H4S: bảng phân vùng dùng 4 MB) |

## 4. Module, symbol, footprint

Nguồn: *ESP32-H2-WROOM-02C Datasheet* v1.2 — bảng 2 "Pin Definitions", hình 6 "Physical Dimensions", hình 7 "Recommended PCB Land Pattern", chương 8 "Module Schematics", chương 9 "Peripheral Schematics". Thư viện KiCad của Espressif (commit dd76561) không có module này, nên symbol và footprint được vẽ trong `gen_schematic.py` (`wroom02c_symbol()`, `wroom02c_footprint()`).

| Chân | Tên (datasheet) | Net | | Chân | Tên | Net |
|---|---|---|---|---|---|---|
| 1 | 3V3 | +3V3 (C24 100 nF sát chân) | | 15 | IO22 | LED |
| 2 | EN | EN (C25 1 µF sát chân) | | 16–19 | NC | — |
| 3 | IO4 | không nối | | 20 | IO25 | không nối |
| 4 | IO5 | VBAT_SENSE (ADC1_CH4) | | 21 | RXD0 (GPIO23) | U0RXD → J1.2 |
| 5 | IO10 | I2C_SDA | | 22 | TXD0 (GPIO24) | U0TXD → J1.1 |
| 6 | IO11 | I2C_SCL | | 23 | IO26 (USB D−) | USB_DM → J1.4 |
| 7 | IO8 | STRAP_GPIO8 (R24 kéo lên) | | 24 | IO27 (USB D+) | USB_DP → J1.3 |
| 8 | IO9 | BTN_USER (R23 kéo lên, SW1) | | 25–28 | IO3, IO2, IO1, IO0 | không nối |
| 9, 13, 29 | GND (29 = EPAD) | GND | | 10 | IO12 | VBAT_MEAS_EN |
| 11, 12 | IO13, IO14 | XTAL_32K_P/N (Y1) | | 14 | VBAT | +3V3 (C23 10 µF sát chân) |

- **Từ sơ đồ của module (chương 8)**: VBAT nối 3V3 bên trong qua R2 = 0 Ω (datasheet: "Connected to internal 3V3 power supply (Default)"), nên chân 14 cũng nối +3V3 như Rev B làm với MINI-1; **EN không có RC trong module**, nên R22 10 kΩ + C25 1 µF và TPS3839 giữ nguyên; TXD0 đã có 499 Ω nối tiếp trong module (bản chip phải thêm R40). GPIO8/9 không có điện trở kéo trong module (R9 "NC"), nên R23/R24 giữ nguyên. GPIO25 là chân strap nguồn JTAG chỉ khi eFuse `STRAP_JTAG_SEL` bật (mặc định tắt) — để trống như Rev B.
- **Footprint** (gốc = tâm module): pad cạnh 1.5 × 0.9 mm, tâm cách mép module 0.25 mm vào trong (ló ra 0.5 mm), bước 1.5 mm, chân 1/28 cách đỉnh module 7.1 mm; pad đáy 0.9 × 1.5 mm, chân 10/19 cách cạnh 2.25 mm; pad tản nhiệt hai miếng 2.8 × 0.55 và 2.8 × 1.6 mm, tâm cách cạnh trái 8.53 mm, cách đáy 7.99 / 6.27 mm. Vùng ăng-ten 6 mm trên cùng nằm ngoài bo.
- **Để hàn tay**: thêm một **lỗ mạ 0.8 mm (vành 1.4 mm) ở giữa miếng tản nhiệt 2.8 × 1.6 mm**, hở mask cả hai mặt: hàn các chân răng cưa bằng mỏ, rồi lật bo và **mớm thiếc từ mặt dưới qua lỗ** để nối EPAD. Lỗ nằm ngoài vùng pin/holder ở mặt dưới (cách mép pin ~2 mm), nên vẫn hàn được sau khi holder đã gắn. Miếng tản nhiệt không có lớp kem hàn (stencil). Miếng 2.8 × 0.55 mm có 3 via, bốn góc miếng lớn có 4 via (đúng mẫu "via for thermal pad" của hình 7); miếng nhỏ chỉ được hàn nếu dùng khí nóng/reflow. GND của module vẫn có qua chân 9 và 13.
- Silkscreen: một vạch dọc cạnh trái module (cạnh phải sát mép bo nên không in). Hướng module không thể lắp sai: phần ăng-ten phải nằm ngoài mép trên.
- Datasheet: MSL 3, reflow một lần, đỉnh 235–250 °C — áp dụng nếu hàn bằng khí nóng/reflow.

## 5. Vị trí module và ăng-ten

- ESP32-H2 Hardware Design Guidelines, mục "General Principles of PCB Layout for Modules (Positioning a Module on a Base Board)": "It is suggested to place the module's on-board PCB antenna outside the base board, and the feed point of the antenna close to the edge of the base board." Hình "Placement of ESP32-H2 Modules on Base Board (antenna feed point on the right)" đánh dấu ✓ ở vị trí ③ (góc trên phải, ăng-ten nhô khỏi mép trên) và ④.
- Điểm feed của ăng-ten WROOM-02C nằm ở **phía phải** vùng ăng-ten (hình 6 của datasheet: hai nhánh xuống của ăng-ten ở bên phải) ⇒ dùng **vị trí ③**: module ở góc trên phải, mép bo trùng ranh giới vùng ăng-ten (6 mm), cạnh phải module cách mép phải 0.8 mm.
- HDG: "sufficient ground copper and dense ground vias should be placed on the base board near the antenna" ⇒ GND đổ trên cả 4 lớp tới sát mép trên, một hàng **14 via GND bước 1 mm cách mép trên 0.7 mm** dưới module, cộng lưới via khâu 2.5 mm (66 via khâu).
- HDG: "A clearance of at least 15 mm is recommended in all directions" (khoảng trống quanh ăng-ten trong vỏ) — thuộc thiết kế vỏ, ghi lại ở `docs/limitations.md` mục 11.
- HDG: UART/USB (đường, via, header) xa ăng-ten nhất có thể ⇒ J1 ở góc dưới phải (~24 mm dưới mép ăng-ten); bốn chân UART/USB của module ở cột phải nên đi vào trong 1.65 mm tới via rồi chạy ở lớp In2 xuống J1 (via cách ranh giới ăng-ten 7–12 mm).
- **Pin CR2450 (vỏ kim loại) ở mặt dưới**, mép pin cách mép trên (ranh giới ăng-ten) 6.8 mm, phía sau các mặt GND. Ảnh hưởng tới ăng-ten: **CHƯA KIỂM THỬ** (W-01). Thạch anh 32 kHz Y1 ở dưới hàng chân đáy module, cách ăng-ten ~16 mm.

## 6. Holder ở mặt dưới — vùng dưới pin

- Bản vẽ MY-CP-0138 (hình cắt) cho thấy pin nằm trên **đáy nhựa của holder**, không chạm mặt bo; thân holder 27 × 16 mm, pin Ø24.5 mm nhô ra hai bên thân (hai "mảnh trăng"), ở đó mép vỏ pin (+) cao hơn mặt bo một khoảng bằng chiều dày đáy holder (bản vẽ không ghi số).
- Rev B (holder mặt trên) cấm mọi thứ trên F.Cu dưới pin và thân holder vì còn chỗ. Bản này cần vùng đó: **B.Cu dưới pin và thân holder không có đường mạch và không đổ đồng; chỉ có via phủ mask (tented)** — rule area `CELL_BT1`, `HOLDER_BT1` trên B.Cu. Rủi ro còn lại (mask trên vòng via bị trầy và pin bị ép xuống): `docs/limitations.md` mục 11; quyết định: `docs/decisions.md` D22.
- Pad + (bên trái nhìn từ trên) nối lên mặt trên bằng hai via ngay dưới pad (đoạn B.Cu 0.5 mm, ngoài vùng pin); pad − (bên phải) nằm trong vùng đổ GND của B.Cu (nối bằng thanh nhiệt, không cần via riêng).
- Silkscreen mặt dưới: "+" / "−" của holder, "CR2450 ONLY", "NO CHARGE", tên bo, ngày, và "SHT40" ở mặt sau lưỡi cảm biến.

## 7. Stack-up, luật thiết kế, lớp

- JLC04161H-7628, 4 lớp 1.6 mm (như H2C); không cần kiểm soát trở kháng (không có đường RF trên bo, chỉ cặp USB full-speed ngắn).
- Luật trong `th_sensor_h2w.kicad_pro`: như Rev B (clearance 0.127 mm, đồng–mép 0.3 mm, net class Default 0.2 / 0.15 mm, Power 0.4 / 0.2 mm) cộng via 0.45 / 0.2 mm (vòng khuyên 0.125 mm, lỗ–đồng 0.2 mm). Mọi linh kiện ≥ 0603 (trừ U1 WSON-10, U5 DFN-4 như Rev B).
- L1: linh kiện, 190 đoạn dây (236 mm), đổ GND (cả dưới module). L2 (In1): GND liền, không dây. L3 (In2): lớp đi dây thứ hai, 69 đoạn (195 mm: UART/USB, VBAT, +3V3, EN, I2C…), đổ GND phần còn lại. L4 (B.Cu): pad holder, 2 đoạn (5.8 mm, pad + tới via), đổ GND ngoài vùng pin.
- `router.py` có thêm tham số `layers`: bản này đi dây trên F.Cu + In2.Cu; đồng của lớp khác (pad holder ở B.Cu) chỉ chặn via. Mặc định giữ nguyên nên Rev B và H2C sinh lại giống từng byte (đã kiểm).
- Đi tay: lưỡi SHT40 và phần tỏa dây sau cầu nối, khối chuyển đổi (y như Rev A/B), pad tản nhiệt module, chân 1/14 (+3V3) và bốn chân UART/USB của module, pad + của holder. Còn lại do router; log: `hardware/wroom/reports/routing_log.txt`.

## 8. Bố trí (mặt trên, gốc tọa độ góc trên trái)

- Module: thân x 18.8–36.8 mm, y −6…14 mm (vùng ăng-ten y −6…0 ngoài bo).
- Lưỡi SHT40 ở góc trên trái (6.6 × 5.4 mm), cắt bằng rãnh 1 mm hình chữ L chạy vào từ mép trái rồi lên dọc cạnh phải lưỡi; cầu nối 1 × 2.6 mm ở mép trên mang 4 dây (VDD, SCL, SDA, GND) bước 0.5 mm; không via, không đổ đồng trên lưỡi (cả 4 lớp).
- Bên trái module (từ trên xuống): C24 (chân 1), C25 (chân 2, EN), C31 (chân 4), R24/R23 (chân 7/8), R35 (chân 10); điện trở kéo I2C R26/R27 ngay sau cầu nối; giám sát U3/C26/R22, cầu chia R31/R32/Q3; SW1 (USER/BOOT) ở mép trái.
- Dưới module: Y1 + C27/C28 ngay dưới chân 11/12 (đường clock 0.8–1.3 mm, không via); C23 dưới chân 14; R25/D3 dưới chân 15; test pad 3V3, GND, VOUT.
- Nửa dưới: C5 ở mép trái, SW2 (RST) giữa, khối chuyển đổi (Q1, R1, C1–C4, U1, L1, R2–R4) dọc mép dưới với đầu vào phía pad + của holder; C21/C22/R21; J1 ở góc dưới phải; TP VBAT, VIN cạnh Q1/R1.

## 9. Sản xuất và lắp ráp

- Đặt PCB: 4 lớp, 1.6 mm, JLC04161H-7628, **via phủ mask** (đã đặt trong file board — bắt buộc vì có via dưới pin), HASL không chì hoặc ENIG. Rãnh lưỡi cảm biến 1 mm phay (không V-cut).
- **Lắp hai mặt**: BT1 ở mặt dưới (CPL ghi `Bottom`), mọi thứ khác ở mặt trên. Hoặc đặt lắp ráp cả hai mặt, hoặc chỉ mặt trên rồi tự hàn BT1 (hai pad lớn). Kiểm hướng holder trong bản xem trước mặt dưới: cực + ở **bên trái khi nhìn từ trên** (pad 1, "+" trên silkscreen mặt dưới).
- **U4 tự mua**: ESP32-H2-WROOM-02C-**H4S** (4 MB; bản -H2S 2 MB không chứa được bảng phân vùng của firmware). Hàn tay: đặt module sao cho vùng ăng-ten nằm ngoài mép trên và các pad răng cưa trùng pad bo (pad bo ló ra 0.5 mm ngoài module để chạm mỏ), hàn một chân góc, chỉnh, hàn hết các chân; rồi mớm thiếc qua lỗ 0.8 mm ở mặt dưới cho EPAD. Thứ tự gợi ý: mặt trên (JLC) → module → holder (nếu tự hàn).
- Kiểm `orientation_check.md` (holder, C5 + bên trái, LED, IC, MOSFET) trong bản xem trước của JLC.

## 10. Kiểm thử bổ sung (ngoài T-01…T-42 của `docs/test_plan.md`)

Tất cả **CHƯA KIỂM THỬ**.

| ID | Kiểm tra | Tiêu chí / ghi chú |
|---|---|---|
| W-01 | Tầm phủ: RSSI/LQI ở 5 m và 10 m qua tường, có pin trong holder, so với bo Rev B (hoặc dev kit) cùng vị trí; thử thêm khi bo nằm trong vỏ | không kém rõ rệt; ghi số. Nếu kém: kiểm ảnh hưởng của pin (đo với/không pin, nguồn bench vào TP VBAT) |
| W-02 | Mối hàn module: thông mạch mọi chân dùng tới (đầu đo trên pad bo ló ra), không chập giữa hai chân kề; EPAD: đo 0 Ω giữa lỗ mặt dưới và chân 9/13 sau khi hàn | không hở, không chập |
| W-03 | Lắp/tháo pin 10 lần, rồi soi mặt dưới dưới pin | mask trên via không trầy; không chập VBAT–GND (đo điện trở giữa TP VBAT và GND khi không có pin: không về gần 0) |
| W-04 | Footprint holder ở mặt dưới: so với holder thật trước khi đặt; cực + của pin ở pad 1 (trái nhìn từ trên) | đúng cực, pin vào được |
| W-05 | USB-Serial/JTAG và UART0 qua J1 2 × 3 | `idf.py flash monitor` chạy như T-10 |
| W-06 | Dòng ngủ và dòng trung bình (T-30…T-34) | không khác Rev B quá sai số đo (cùng chip, cùng firmware; module khác) |

## 11. Tái tạo file

Chạy từ gốc repo, theo thứ tự (`TH_VARIANT=wroom` chọn bản này; không có biến thì là Rev B):

```sh
TH_VARIANT=wroom python3 hardware/scripts/gen_schematic.py   # schematic, symbol/footprint WROOM-02C, kiểm parity
TH_VARIANT=wroom python3 hardware/scripts/gen_pcb_wroom.py   # đặt, đi dây F.Cu + In2, đổ đồng 4 lớp, silkscreen (~1 phút)
TH_VARIANT=wroom python3 hardware/scripts/gen_project.py     # .kicad_pro: luật, via 0.45 / 0.2 mm
TH_VARIANT=wroom python3 hardware/scripts/gen_reports.py     # ERC, DRC + parity, PDF/SVG/3D
TH_VARIANT=wroom python3 hardware/scripts/gen_production.py  # Gerber 4 lớp, drill, BOM, CPL (BT1 Bottom), bản vẽ lắp ráp
python3 tools/check_pinmap.py --variant wroom               # board_pins.h ↔ chân module
```

Schematic, board, project và thư viện sinh lại **giống từng byte**; chỉ dấu thời gian trong Gerber/drill/báo cáo/PDF/ZIP và ảnh render thay đổi. Tồn kho JLC tra lúc 2026-11-06 17:00 UTC: `hardware/wroom/production/jlc_parts_snapshot.jsonl` (tra lại bằng `python3 tools/jlc_lookup.py --json <mã…>`). Render 3D không có mô hình module (không có file STEP của WROOM-02C trong repo).

## 12. Nguồn

- Espressif, *ESP32-H2-WROOM-02C Datasheet* v1.2: https://espressif.com/sites/default/files/documentation/esp32-h2-wroom-02c_datasheet_en.pdf — bảng 2, hình 6, hình 7, chương 8, 9, 12 (đọc 2026-11-06).
- Espressif, *ESP32-H2 Hardware Design Guidelines* (bản latest, đọc 2026-11-06): https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32h2/pcb-layout-design.html — mục "Positioning a Module on a Base Board", hình `esp32h2-module-place-on-base-board-right.png`.
- MYOUNG, bản vẽ MY-CP-0138 (BS-24-B4AA016), datasheet LCSC C964809: https://www.lcsc.com/datasheet/lcsc_datasheet_2012181809_MYOUNG-BS-24-B4AA016_C964809.pdf
- JLCPCB: https://jlcpcb.com/impedance (JLC04161H-7628), https://jlcpcb.com/capabilities/pcb-capabilities.
