# TH-SENSOR-H2W-123 Rev A — biến thể dùng pin CR123A

Biến thể của TH-SENSOR-H2W (module ESP32-H2-WROOM-02C-H4S do người dùng tự mua và hàn) chạy bằng **một pin CR123A** (IEC CR17345, Li-MnO2 3 V, 1550 mAh) thay cho CR2450. Pin nằm **bên cạnh** phần mạch trong một đế hàn xuyên lỗ; không còn tụ đệm 470 µF; có thêm cầu chì tự phục hồi ngay tại cực + của pin. Mạch còn lại giữ nguyên: AO3401A chống ngược cực, TPS63900 3.3 V, giám sát áp, SHT40 trên lưỡi tách nhiệt, LED, cầu đo pin, một nút USER/BOOT bấm cạnh, J1 là pad dán. Firmware dùng chung mã nguồn, build thêm lớp cấu hình `sdkconfig.defaults.cr123a` (mục 7). Rev B, H2C và H2W không thay đổi.

Yêu cầu của người dùng ngày 2026-11-11, sau bản đánh giá so sánh CR2450 với CR123A: "Làm mục 1 và 3, chiều ngang board là 34,5cm bố trí như hình vẽ. Màu đen là cr123a xanh lá là pcb đỏ là esp h2 wroom hồng là cảm sht40, tổng thể thiết bị là vuông" (hình vẽ: pin đứng cạnh bo, module ở trên, SHT40 ở cạnh dưới). Cách hiểu đã báo người dùng kèm hình bố trí đúng tỉ lệ trước khi đi dây:

- "34,5cm" là **34.5 mm, bề rộng phần mạch** (vùng màu xanh). Không thể là cạnh của cả thiết bị: riêng đế pin đã dài 43.3 mm.
- Bo là **một tấm liền**, đế pin hàn lên bo: mọi đế CR123A có ở JLC đều là loại hàn lên bo.
- Pin nằm **bên trái** thay vì bên phải (ảnh gương của hình vẽ), lý do ở mục 5.

## 1. Trạng thái

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Schematic: ERC | ĐÃ XÁC MINH: 0 lỗi, 0 cảnh báo | `hardware/wroom123/reports/erc_report.txt` |
| PCB: DRC + schematic parity | ĐÃ XÁC MINH: 0 vi phạm, 0 pad chưa nối, 0 lỗi parity (mọi mức) | `hardware/wroom123/reports/drc_report.txt` |
| Pin map firmware ↔ module | ĐÃ XÁC MINH | `python3 tools/check_pinmap.py --variant wroom123` |
| Kích thước: bo 53.3 × 47.3 mm, ăng-ten nhô 6.0 mm ⇒ khung 53.3 × 53.3 mm | ĐÃ XÁC MINH trên file board | mục 4 |
| Gerber 4 lớp, drill, BOM (26 dòng), CPL (39 linh kiện, tất cả mặt trên) | ĐÃ XÁC MINH là sinh được; **chưa gửi nhà máy** | `hardware/wroom123/production/` |
| Tái tạo giống từng byte (schematic, board, project) | ĐÃ XÁC MINH (chạy hai lần) | mục 10 |
| Firmware với lớp `cr123a`: build | ĐÃ XÁC MINH (build được); chạy trên bo: **CHƯA KIỂM THỬ** | `docs/reports/firmware_build.md` |
| Khả năng cấp xung của CR123A, tuổi thọ 2.3–2.6 năm | **ƯỚC TÍNH** (mô hình khớp theo đồ thị datasheet) | mục 2, `hardware/analysis/results/cr123a_summary.md` |
| Footprint đế pin BH-123A-A1CJ002 | vẽ theo bản vẽ MY-CP-0398; **chưa so với đế thật** (nhất là phía đặt chốt định vị) | mục 6 |
| Bảng phần trăm pin của CR123A | **ƯỚC TÍNH** (đọc từ đồ thị 20 mA); thô ở nửa trên | mục 7 |
| Ăng-ten với pin cách 16 mm, điện, cảm biến, Matter, dòng ngủ | **CHƯA KIỂM THỬ** | mục 9, `docs/test_plan.md` |

Không có bo nào được đặt, làm hay đo. Không tuyên bố chứng nhận nào.

## 2. Vì sao CR123A — kết quả mô hình (ƯỚC TÍNH)

Mô hình nguồn của dự án (`hardware/analysis/power_model.py`) kết luận thiết kế CR2450 **chưa đạt**: pin đồng xu không cấp nổi xung dòng, nên từ khoảng giữa đời pin thiết bị không khởi động lại được, và tuổi thọ chỉ 0.55–0.77 năm (`docs/power_budget.md`). `hardware/analysis/cr123a_study.py` chạy đúng các dạng tải và mô hình bộ chuyển đổi đó với một pin CR123A.

Mô hình pin: khớp theo năm điểm đọc từ đồ thị xả liên tục của datasheet Panasonic CR123A (20 °C: 20 mA 2.90 V, 100 mA 2.82 V, 300 mA 2.72 V, 500 mA 2.63 V, 1 A 2.52 V; sai số khớp 0.01 V). Không có số liệu công bố về điện trở theo mức đã dùng hay theo nhiệt độ, nên các trạng thái "late" (điện trở × 3) và "eol" (× 8) cùng hệ số nhiệt độ (−10 °C: × 2.5) là **giả định**, lấy khắt khe như của pin đồng xu.

| Trạng thái pin | CR2450 + 555 µF | CR123A, chỉ 85 µF (không có C5) |
|---|---|---|
| mới, 25 °C | mọi tải ổn | mọi tải ổn, VIN ≥ 2.94 V |
| giữa đời, 25 °C | khởi động và commissioning **RESET** | mọi tải ổn, VIN ≥ 2.88 V |
| late, 25 °C | report **RESET** | mọi tải ổn, VIN ≥ 2.62 V |
| eol, 25 °C | report **RESET** | mọi tải ổn, VIN ≥ 2.27 V |
| mới, −10 °C | khởi động và commissioning **RESET** | mọi tải ổn, VIN ≥ 2.77 V |
| late, −10 °C | — | mọi tải ổn, VIN ≥ 2.27 V |

Rail 3V3 giữ 3.30 V trong mọi trường hợp của CR123A (UVLO của TPS63900 ở 1.65 V). Thêm 470 µF không đổi kết quả, nên bo này bỏ C5.

Tuổi thọ ở tải danh nghĩa (63.1 µA lấy từ pin, tự xả 1 %/năm): CR2450 0.55 / 0.66 / 0.76 năm (dùng được 50 / 60 / 70 % dung lượng); **CR123A 2.32 / 2.45 / 2.59 năm** với giả định dùng được 85 / 90 / 95 % của 1550 mAh. Không phải số đo.

## 3. Khác biệt so với H2W (CR2450)

| | H2W Rev A | H2W-123 Rev A |
|---|---|---|
| Pin | 1 × CR2450, 620 mAh, đế SMD ở mặt dưới | **1 × CR123A, 1550 mAh**, đế xuyên lỗ MYOUNG BH-123A-A1CJ002 (LCSC C5290177) ở mặt trên, cạnh phần mạch |
| Tụ đệm C5 470 µF | tantal TAJD477K006RNJ | **không có** (mục 2) |
| Bảo vệ ngắn mạch | không (pin đồng xu tự giới hạn dòng) | **F1**, cầu chì tự phục hồi BHFUSE BSMD1206-050-6V (LCSC C883122) giữa cực + của đế và phần còn lại |
| Bo | 37.6 × 31.6 mm (37.6 × 37.6 tính cả ăng-ten) | **53.3 × 47.3 mm (53.3 × 53.3 tính cả ăng-ten)** |
| Linh kiện mặt dưới | đế pin | không có: lắp ráp một mặt |
| Nút SW1 (bấm cạnh) | giữa mép trái | **mép dưới**, bấm từ dưới lên khi gắn tường |
| Lưỡi SHT40 | góc trên trái | **góc dưới phải**, dưới module, xa bộ chuyển đổi |
| Hướng gắn tường | cạnh có nút xuống đất, ăng-ten nằm ngang | **ăng-ten hướng lên**, cảm biến và nút ở cạnh dưới |
| Chiều dày | ≈ 12.3 mm | ≈ 19–20 mm (ƯỚC TÍNH: bo 1.6 + pin Ø17 nằm trong đế; bản vẽ chỉ cho thân đế cao 14.2 mm) |
| Số linh kiện trong `design.py` | 49 | 49 (−C5, +F1) |
| Dòng BOM / linh kiện gắn máy | 26 / 39 | 26 / 39 |
| Firmware | profile `battery` | profile `battery` + lớp `cr123a` |

## 4. Kích thước

- Phần mạch rộng 34.5 mm (yêu cầu của người dùng). Đế pin rộng 18.2 mm, cộng 0.3 mm tới mép bo và 0.3 mm tới phần mạch ⇒ bo rộng **53.3 mm**.
- Thiết bị vuông tính cả 6 mm ăng-ten nhô khỏi mép trên ⇒ bo cao 53.3 − 6.0 = **47.3 mm**. Đế pin dài 43.3 mm nằm trọn trong chiều cao đó (cách mép trên và dưới 2.0 mm).
- Hình vuông nhỏ nhất có thể với đế này là khoảng 44 mm, nhưng khi đó pin chỉ cách module khoảng 7 mm. Với 34.5 mm, pin cách module 16 mm (mục 5).
- Góc trên phải vuông (pad chân 28 của module cách hai mép 0.3 mm), ba góc còn lại bo tròn R1.5.

## 5. Bố trí (mặt trên, gốc tọa độ góc trên trái)

- **Pin bên trái, module ở góc trên phải.** Điểm cấp của ăng-ten WROOM-02C nằm ở phía phải vùng ăng-ten. ESP32-H2 Hardware Design Guidelines ("Positioning a Module on a Base Board", hình "antenna feed point on the right") chỉ đánh dấu ✓ cho vị trí ③ (góc trên phải) và ④, và khuyên chừa ≥ 15 mm quanh ăng-ten. Nếu giữ pin bên phải như hình vẽ, module phải lùi sang trái (vị trí ① không được đánh dấu) hoặc đứng sát vỏ thép của pin. Đặt ảnh gương thì module ở vị trí ③ và mép đế pin cách module **16.0 mm**. Ảnh hưởng thực tế của pin tới ăng-ten: CHƯA KIỂM THỬ (K-04).
- Module: thân x 34.5–52.5 mm, y −6…14 mm; hàng 14 via GND bước 1 mm dọc mép trên dưới module; các linh kiện sát chân module (C24, C25, C31, R23, R24, R35, Y1, C27, C28, C23, R25, D3) đặt y hệt bo H2W.
- Đế pin: tâm (9.4, 23.65), thân x 0.3–18.5, y 2.0–45.3; cực + ở **trên** (pad vuông), lỗ chốt định vị ở phía trong bo (nếu quay ngược, lỗ chốt sẽ cắt vào mép bo). F1 ngay cạnh cực +.
- Giám sát áp U3, cầu chia R31/R32/Q3: giữa đế pin và module, lùi 2.6 mm so với cột linh kiện ở chân module để chừa rãnh cho hai đường I2C chạy xuống lưỡi cảm biến.
- Khối chuyển đổi (Q1, R1, C1–C4, U1, L1, R2–R4) ở giữa phần mạch, đầu vào quay về phía pin; C21/C22/R21 bên phải nó.
- **Lưỡi SHT40** ở góc dưới phải (6.6 × 5.4 mm), cắt bằng rãnh 1 mm hình chữ L từ mép phải; cầu nối 1 × 2.6 mm ở mép dưới mang 4 dây bước 0.5 mm; không via, không đổ đồng trên lưỡi (cả 4 lớp). Đây là lưỡi của H2W quay 180°. SHT40 cách U1 22.5 mm, cách tâm module 41 mm; khi gắn tường nó nằm dưới mọi nguồn nhiệt.
- **SW1** giữa phần mạch trên mép dưới, núm nhô 0.5 mm ra ngoài mép. J1 (6 pad dán) ở cạnh phải, dưới module. Test pad: VBAT, VIN, VOUT, 3V3, GND, EN như H2W.
- Gắn tường: mặt sau áp vào tường, ăng-ten hướng lên. Thay pin từ mặt trước, không phải gỡ thiết bị.

## 6. Đế pin và cầu chì

**Đế MYOUNG BH-123A-A1CJ002** (LCSC C5290177, PA66 UL94 V-0, tiếp điểm thép không gỉ mạ nickel, −25…+85 °C), bản vẽ MY-CP-0398 (2024-03-07): thân 43.3 × 18.2 × 14.2 mm; hai chân dẹt 0.8 × 0.3 mm dài 4.1 mm, cách nhau 37.5 ± 0.5 mm trên trục giữa, lỗ Ø1.8 mm; một chốt định vị Ø1.4 × 1.7 mm trong lỗ Ø2.0 mm, cách tâm 18.95 mm và cách hàng chân 8.4 mm, ở đầu cực +.

- Footprint do `gen_schematic.py` vẽ (`myoung_bh123a_a1cj002()`): pad 1 = + (vuông, 3.2 mm, lỗ 1.8 mm), pad 2 = − (tròn), một lỗ không mạ Ø2.0 mm cho chốt.
- **Phía đặt chốt** (trên hay dưới hàng chân) được suy từ bản vẽ: "PCB Layout Diagram" là hình nhìn từ dưới với dấu + ở bên trái giống hình nhìn từ trên, tức là hình nhìn từ trên lật quanh trục dọc của đế; chốt nằm dưới hàng chân ở hình đó nên nằm trên hàng chân khi nhìn từ mặt linh kiện. Hình chiếu cạnh cho cùng kết quả. Nếu suy luận này sai, đế không cắm vừa (không thể cắm ngược cực) và phải cắt chốt hoặc khoan thêm lỗ ⇒ **so với đế thật trước khi đặt PCB** (K-01).
- Chốt định vị làm cho đế chỉ cắm được một chiều; cực + của pin vẫn phải đặt đúng theo dấu trên đế. Q1 chặn pin lắp ngược.

**F1** (1206, giữ 0.5 A, ngắt 1 A, 6 V, chịu tới 100 A, 0.15–0.7 Ω theo trang JLC): một CR123A cấp được 1.5 A liên tục và 3.5 A xung (datasheet Energizer 123), đủ làm nóng đường mạch khi có chập; pin đồng xu thì không. F1 đứng ngay sau cực +, trước cả cầu đo pin. Sụt áp ở giới hạn 100 mA của bộ chuyển đổi: ≤ 0.07 V. Datasheet Energizer ghi pin của họ có PTC bên trong; datasheet Panasonic không nói, nên thiết kế không dựa vào điều đó.

## 7. Firmware

Build: `-D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.battery;sdkconfig.defaults.cr123a"` (hoặc `debug` thay cho `battery`). Lớp `cr123a` chỉ đặt `CONFIG_APP_CELL_CR123A=y`; từ đó:

| | CR2450 (mặc định) | CR123A |
|---|---|---|
| Bảng điện áp → phần trăm | bảng pin đồng xu | bảng đọc từ đồ thị 20 mA của Panasonic CR123A |
| Power Source: BatIECDesignation / BatCapacity | CR2450 / 620 mAh | CR17345 / 1550 mAh |
| Ngưỡng Warning / Critical | 40 % / 20 % | 20 % / 8 % |
| Ngưỡng Critical theo điện áp | 2600 mV | 2500 mV |
| Điện áp tối thiểu để bật radio | 2400 mV | 2200 mV |

Pin map không đổi (`tools/check_pinmap.py --variant wroom123`). Giới hạn +8 dBm của công suất phát giữ nguyên vì nó đến từ giới hạn dòng vào 100 mA của TPS63900, không chỉ từ pin.

**Phần trăm pin của CR123A chỉ mang tính chỉ báo**: điện áp gần như phẳng (khoảng 2.92 V từ vài phần trăm tới quá nửa dung lượng), nên vài mV sai số ADC làm con số lệch hàng chục phần trăm ở nửa trên; nó chỉ có ý nghĩa ở một phần ba cuối. Pin lạnh đọc thấp hơn.

## 8. Sản xuất và lắp ráp

- PCB: 4 lớp, 1.6 mm, JLC04161H-7628, via phủ mask, HASL không chì hoặc ENIG; rãnh lưỡi cảm biến 1 mm phay (không V-cut).
- **Lắp một mặt.** BT1 là linh kiện xuyên lỗ: có trong BOM và CPL; đặt thêm dịch vụ hàn xuyên lỗ của JLC hoặc tự hàn hai chân. Nên lắp đế sau cùng (cao nhất).
- **U4 tự mua** (ESP32-H2-WROOM-02C-**H4S**) và hàn tay như ở H2W (`docs/wroom_variant.md` mục 4 và 9).
- Kiểm `orientation_check.md` trong bản xem trước của JLC (LED, U1, U3, U5, Q1, Q3, đế pin: pad vuông = + ở phía trên) và SW1 (núm quay ra mép dưới).
- Không có nút RST: reset bằng cách chập TP6 (EN) xuống GND; nạp qua USB-Serial/JTAG trên 6 pad J1 (hàn dây hoặc kim pogo), như H2W.
- Không bao giờ cấp nguồn bench khi pin đang nằm trong đế.

## 9. Kiểm thử bổ sung (ngoài `docs/test_plan.md`)

Tất cả **CHƯA KIỂM THỬ**. Các mục W-02 (mối hàn module), W-05 (USB/UART qua J1) và W-06 (dòng ngủ) của H2W áp dụng nguyên.

| ID | Kiểm tra | Tiêu chí / ghi chú |
|---|---|---|
| K-01 | Đặt một đế BH-123A-A1CJ002 thật lên bản in 1:1 của footprint (hoặc bo trần): hai chân, chốt định vị, cực + | chân và chốt vào đúng lỗ; cực + của đế ở pad vuông. Làm **trước khi đặt PCB** |
| K-02 | F1: đo sụt áp TP VBAT so với cực + khi tải 100 mA; với nguồn bench 3 V (không dùng pin) nối tải 1.5 Ω vào VBAT | sụt ≤ 0.07 V; F1 ngắt trong vài giây, tự phục hồi khi bỏ tải |
| K-03 | Khởi động và commissioning với pin đã dùng nhiều (xả trước bằng tải 20 mA tới còn ~20 %) và ở 0 °C | không reset (mô hình dự đoán ổn); ghi VIN thấp nhất |
| K-04 | Tầm phủ: RSSI/LQI ở 5 m và 10 m, có pin và không pin (nguồn bench vào TP VBAT) | không kém rõ rệt khi có pin; ghi số |
| K-05 | Phần trăm pin: ghi BatVoltage và BatPercentRemaining theo thời gian trong một lần xả tăng tốc | so với bảng ở `battery_model.c`; chỉnh bảng và ngưỡng Warning/Critical |
| K-06 | Dòng trung bình 24 h và dòng ngủ | như T-30…T-34; không có rò của C5 |
| K-07 | Gắn tường: bấm SW1 từ dưới lên; T-11 (độ chính xác SHT40) ở tư thế này | thao tác nút đúng; lệch như T-11 |

## 10. Tái tạo file

```sh
TH_VARIANT=wroom123 python3 hardware/scripts/gen_schematic.py     # schematic, footprint đế pin, kiểm parity
TH_VARIANT=wroom123 python3 hardware/scripts/gen_pcb_wroom123.py  # đặt, đi dây F.Cu + In2, đổ đồng 4 lớp, silkscreen
TH_VARIANT=wroom123 python3 hardware/scripts/gen_project.py       # .kicad_pro
TH_VARIANT=wroom123 python3 hardware/scripts/gen_reports.py       # ERC, DRC + parity, PDF/SVG/3D
TH_VARIANT=wroom123 python3 hardware/scripts/gen_production.py    # Gerber 4 lớp, drill, BOM, CPL
python3 tools/check_pinmap.py --variant wroom123
python3 hardware/analysis/cr123a_study.py                        # bảng mô hình ở mục 2 (~1 phút)
```

Schematic, board và project sinh lại **giống từng byte**; chỉ dấu thời gian trong Gerber/drill/báo cáo/PDF/ZIP và ảnh render thay đổi. Tồn kho JLC tra lúc 2026-11-11 02:15 UTC (`hardware/wroom123/production/jlc_parts_snapshot.jsonl`).

Số liệu board: 317 via 0.45 / 0.2 mm (259 via khâu GND) và 21 via 0.6 / 0.3 mm; F.Cu 204 đoạn dây (280 mm), In2 65 đoạn (268 mm), In1 và B.Cu chỉ có GND; 10 ký hiệu linh kiện chỉ có trên lớp Fab. `gen_pcb_wroom123.py` là bản sao có chỉnh sửa của `gen_pcb_wroom.py`; phép kiểm "via một lớp" ở đây xét cả via nằm giữa một đoạn dây (bản H2W chỉ xét đầu đoạn dây, không gây lỗi ở bo đó).

## 11. Nguồn

- Panasonic, *CR123A — CR Cylindrical-type Lithium Battery (Standard type)* (July 2024): https://energy.panasonic.com/dam/master/pdf/en/datasheet/lithium/CR123A_Datasheet_EN.pdf — 3 V, 1550 mAh, dòng liên tục chuẩn 20 mA, Ø17.0 × 34.5 mm, ≈ 16 g, −40…+70 °C; đồ thị xả liên tục 20 mA–1 A và xả xung 0.9 A ở +20 / −20 °C (đọc 2026-11-10).
- Energizer, *Energizer 123 Product Datasheet* (form 123GL1018): https://data.energizer.com/pdfs/123.pdf — IEC CR17345, 1500 mAh tới 2.0 V, tối đa 1500 mA liên tục / 3500 mA xung, −40…+60 °C, có PTC bên trong (đọc 2026-11-10).
- MYOUNG, bản vẽ MY-CP-0398 (BH-123A-A1CJ002), datasheet LCSC C5290177 (đọc 2026-11-11).
- JLCPCB parts search cho C5290177 và C883122 (BHFUSE BSMD1206-050-6V): ảnh chụp 2026-11-11 02:15 UTC.
- Espressif, *ESP32-H2 Hardware Design Guidelines*, mục "Positioning a Module on a Base Board" (như `docs/wroom_variant.md`).
