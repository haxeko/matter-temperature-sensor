# Các quyết định thiết kế — TH-SENSOR-H2 Rev B

Mỗi mục: quyết định, lý do, phương án đã cân nhắc, trạng thái bằng chứng. Rev B (một CR2450) thay đổi D2, D3, D8, D14, D16–D18; lý do ở D20. Các mục Rev A được giữ làm hồ sơ khi chúng giải thích vì sao Rev B như hiện tại.

## D1. Module ESP32-H2-MINI-1-H4S

- **Quyết định**: dùng module có anten PCB, flash 4 MB (H4S), không thiết kế chip-down.
- **Lý do**: phần RF, thạch anh 32 MHz, flash đã được Espressif thiết kế sẵn; 4 MB đủ cho hai slot app 1.875 MB (A/B) nếu sau này bật OTA. Firmware hiện chiếm 1.60 MB (battery) / 1.66 MB (debug), còn trống 18 % slot (ĐÃ XÁC MINH bằng `idf.py size`).
- **Rủi ro**: JLC tồn kho 0 ngày 2026-10-29 và lại 0 khi tra lại ngày 2026-10-30 (`hardware/production/manufacturing_blockers.md`). Order code đã kiểm: ESP32-H2-MINI-1-H4S, LCSC C47967030.

## D2. Kiến trúc nguồn Rev A: một TPS63900 cho mỗi cell (topology C) — đã thay bằng D20

Hồ sơ của Rev A (2 × CR2032). Các phương án được mô phỏng cùng tải, cùng tụ (ƯỚC TÍNH, nửa sau của `hardware/analysis/results/power_model_summary.md`):

| Mã | Mô tả | Ưu điểm | Nhược điểm chính (theo mô hình) |
|---|---|---|---|
| A2 | 2 Schottky nối tiếp mỗi cell (RB521S30 + B5819W) → VBAT_OR → 1 TPS63900 3.3 V | đúng nguyên văn "VBAT_OR", hai rào cản | sụt áp diode 0.38 V: ngay cả pin mới, 25 °C, cũng reset khi khởi động và commissioning |
| A1 | 1 Schottky/cell → 1 TPS63900 | sụt áp nhỏ hơn A2 | một rào cản; dòng ngược 1.4 µA khi lệch cell; pin giữa đời reset khi khởi động |
| B | 1 TPS63900 3.3 V/cell, Schottky ở đầu vào | mỗi cell một bộ chuyển đổi | Schottky ở đầu vào ăn vào khoảng UVLO; pin giữa đời reset khi khởi động |
| B0 | như B nhưng P-MOSFET thay Schottky | ít sụt áp | chỉ một rào cản chống sạc ngược |
| **C** | **1 TPS63900 3.4 V/cell, P-MOSFET ở vào, B5819W ở ra** | **không sụt áp ở đầu vào (cell xuống tới UVLO 1.65 V); hai rào cản; dòng ngược 0 µA** | **vẫn CHƯA ĐẠT khi pin giữa đời commission, pin cuối đời, lạnh, thiếu cell** |
| C50 | như C, giới hạn 50 mA | sụt áp cell nhỏ hơn | một cell không đủ cho report; không cải thiện trường hợp nào |

- **Quyết định Rev A**: C. Đây vẫn là "song song có cách ly ngược từng cell": mỗi cell chỉ cấp vào bộ chuyển đổi của riêng nó; hai đầu ra OR qua Schottky.
- Hai rào cản chống sạc cell: (1) TPS63900 không có đường dẫn từ VOUT về VIN khi VOUT cao hơn điểm đặt (4 khóa, không đóng cắt), (2) Schottky ra. Hành vi (1) suy ra từ cấu trúc trong datasheet, **CHƯA KIỂM THỬ**; test T-05 đo trực tiếp.
- Rev B giữ phần đầu vào của C (P-MOSFET, một TPS63900, giới hạn 100 mA) cho một cell và bỏ Schottky đầu ra (D20).

## D3. Điện áp ra: Rev B 3.3 V (SEL = GND), Rev A 3.4 V

- **Rev B**: không còn Schottky đầu ra nên rail lấy trực tiếp VO(1) = 3.3 V: SEL nối GND, RCFG3 = 16.2 kΩ (bảng 7-3 SLVSET3D). RCFG1 = 0 Ω, RCFG2 = 10.5 kΩ giữ nguyên để đặt giới hạn dòng vào 100 mA (bảng 7-2; VO(2) = 3.4 V của hàng này không được chọn). Ba điện trở và giá trị không đổi so với Rev A, chỉ đổi chân SEL. Điện trở 1 %/100 ppm đúng yêu cầu ±1 %, ±200 ppm của TI.
- Rev A: rail sau Schottky = 3.4 V − Vf ⇒ 3.07–3.33 V theo dòng (ƯỚC TÍNH), SEL nối VIN để chọn VO(2) = 3.4 V.

## D4. P-MOSFET AO3401A chống ngược cực

Schottky ở đầu vào làm mất 0.2–0.3 V ngay tại chỗ cell yếu nhất; P-MOSFET (G nối GND, D phía cell) dẫn với điện trở vài chục mΩ khi Vgs ≈ −VBAT. AO3401A: Vgs(th) −0.5/−0.9/−1.3 V (min/typ/max, datasheet) — với cell xuống ~1.7 V MOSFET vẫn mở nhưng điện trở tăng; ở vùng đó bộ chuyển đổi đã gần UVLO 1.65 V. Mức sụt thực tế **CHƯA KIỂM THỬ** (T-04).

## D5. Giới hạn dòng vào 100 mA

Cần để cell tự cấp được xung TX (50 mA ở 3.3 V ⇒ ~60 mA vào ở 2.9 V với hiệu suất 0.9). Giới hạn 50 mA (C50) bị loại theo mô hình (D2); với một cell lý do này càng chặt hơn.

## D6. Supervisor TPS3839K33 → EN

Ngưỡng 2.93 V, trễ 200 ms, 150 nA. Giữ ESP32-H2 trong reset khi rail không đủ, tránh chạy dở dang (ghi flash dở) khi pin yếu. Đẩy-kéo nên nối EN qua R22 10 kΩ để nút RST và J1 vẫn kéo được EN. Dùng thêm brown-out detector bên trong chip ở mức mặc định của ESP-IDF.

## D7. Power guard trong NVS

Reset bởi EN xóa RAM RTC (không giữ được bộ đếm qua `RTC_NOINIT_ATTR`), vì vậy số lần khởi động không ổn định và điện áp cell lần cuối được lưu trong NVS. Có ngủ sâu backoff để không lặp vô hạn. Logic thuần C có unit test (ĐÃ XÁC MINH trên host). Quy tắc được viết lại ngày 2026-11-11: D23.

## D8. Đo điện áp cell bằng cầu chia có công tắc

Cầu chia luôn bật (470k + 470k) tiêu thụ ~3.2 µA — bằng 5 % ngân sách 64 µA. 2N7002 phía thấp, gate kéo xuống 1M, chỉ bật 30 ms mỗi 6 giờ. Tụ 22 nF tại chân ADC giữ điện tích cho mạch lấy mẫu. ADC1_CH4 (GPIO5), suy hao 6 dB, hiệu chuẩn curve fitting. Rev A có hai cầu (thêm ADC1_CH3, GPIO4); Rev B bỏ cầu thứ hai, GPIO4 thành chân không dùng.

## D9. SHT40-AD1B, không dùng heater khi đo thường

- Địa chỉ 0x44, lệnh đo độ chính xác cao, CRC-8 kiểm từng word (driver `components/sht40`, có test).
- Heater chỉ có qua lệnh bảo trì `heater <mW> <ms>`; sau xung nhiệt, firmware không công bố số đo trong 120 s (`APP_HEATER_HOLDOFF_S`).
- Cảm biến đặt trên lưỡi tách nhiệt ở góc trên-phải, xa bộ chuyển đổi và module; không đổ đồng trên lưỡi. Lý do: datasheet SHT4x v7.3 mục 5.5 cho nhiệt trở R_θJA ~250–360 K/W, nên nhiệt dẫn qua đồng từ phần còn lại của bo đi thẳng vào số đo nhiệt độ. Hiệu quả của lưỡi tách **CHƯA KIỂM THỬ** (T-12).

## D10. Thạch anh 32.768 kHz

RTC dùng thạch anh ngoài để đồng hồ ngủ chính xác (SED Thread thức dậy đúng lịch poll, ít phải mở cửa sổ nhận rộng). Tụ tải 18 pF tính cho CL 12.5 pF với giả định ~3 pF ký sinh: **phải chỉnh ở bring-up** (T-09).

## D11. ICD SIT, slow poll 15 s

SIT không đòi controller hỗ trợ LIT/check-in. 15 s là mức tối đa cho phép của SIT; so với 5 s của ví dụ, dòng lấy từ cell giảm từ 104 µA xuống 63 µA (Rev B, ƯỚC TÍNH). Đổi lại độ trễ lệnh từ controller tới thiết bị lên tới 15 s (cảm biến chỉ đọc nên chấp nhận được).

## D12. BLE +3 dBm khi commissioning

Mặc định +9 dBm (~55 mA) quá gần khả năng cấp dòng của đường nguồn coin-cell. Commissioning thường làm cạnh điện thoại. BLE chỉ dùng để commission rồi được giải phóng.

## D13. Vị trí module theo hướng dẫn anten của Espressif ⇒ đổi chân GPIO

ESP32-H2 Hardware Design Guidelines (mục "Positioning a Module on a Base Board", hình "Keepout Zone ... Antenna feed point on the left"): module ở góc, mép module ≤ 2 mm từ mép bo, ≤ 1 mm từ mép trên, khoét bo ≥ 15 mm cạnh vùng anten 5.4 mm. Rev A: 2.0 mm / 0.5 mm / rãnh 15.2 × 6.0 mm.

Hệ quả: dải 2 mm bên trái module chỉ đủ cho 3V3 và EN, nên ba tín hiệu chuyển từ cạnh trái xuống cạnh dưới module:

| Tín hiệu | Trước | Rev A |
|---|---|---|
| VBAT_MEAS_EN | GPIO0 (pad 9) | GPIO12 (pad 16) |
| VBAT1_SENSE (Rev B: VBAT_SENSE) | GPIO1 / ADC1_CH0 (pad 10) | GPIO5 / ADC1_CH4 (pad 19) |
| LED | GPIO12 (pad 16) | GPIO22 (pad 24) |

Đã cập nhật đồng thời schematic (`design.py`), `board_pins.h`, `battery.c`; `tools/check_pinmap.py` kiểm hai phía khớp nhau (ĐÃ XÁC MINH).

## D14. J1 nằm ngang 1×6, không có EN, không có chân nguồn

J1 nằm dưới rãnh anten, thứ tự chân theo thứ tự chân module: TX, RX, D+, D−, BOOT, GND. EN không có trên J1: nạp firmware qua USB-Serial/JTAG tự reset được, hoặc dùng nút RST + BOOT; EN có test pad riêng TP6 (in "EN") để đo thời điểm reset. Rev A còn chân 3V3_DBG nối vào rail qua cầu hàn JP1; Rev B bỏ cả hai cho gọn bo: bo chạy bằng pin, hoặc bằng nguồn bench vào TP1 (VBAT) sau khi tháo pin — đường nguồn bench khi đó đi qua đúng P-MOSFET và bộ chuyển đổi như khi dùng pin.

Cập nhật 2026-11-05 (vẫn Rev B, bo chưa sản xuất): theo yêu cầu của người dùng, bỏ hai điện trở 22 Ω nối tiếp trên USB D+/D− (R28/R29); D+/D− đi thẳng từ module tới J1 (8–11 mm, không via). Cổng USB chỉ dùng để nạp firmware và console khi bring-up, J1 không lắp sẵn. Firmware không đổi (chỉ chú thích trong `board_pins.h`). Bo còn 41 linh kiện lắp, BOM 28 dòng. Cùng lúc đã xét bỏ một trong hai tụ rail C21/C22: mô hình cho thấy commissioning bằng pin mới ở 10 °C chuyển từ ổn (sát ngưỡng) sang reset, nên người dùng chọn giữ cả hai tụ.

## D15. Không có OTA (Rev A và Rev B)

Bảng phân vùng có hai slot A/B (giống `icd_app`), nhưng OTA Requestor tắt vì chưa được kiểm với một OTA Provider thật. Không tuyên bố hỗ trợ OTA.

## D16. Linh kiện JLC

Ưu tiên Basic. Các linh kiện Extended là bắt buộc về chức năng: TPS63900, TPS3839K33, SHT40, DFE201612E, ESP32-H2-MINI-1, holder BS-24-B4AA016, tụ điện phân 470 µF, và hai giá trị RCFG 10.5 kΩ / 16.2 kΩ (bảng cấu hình TI không có giá trị thay thế trong thư viện Basic).

## D17. PCB 2 lớp, đi dây bằng script

- KiCad 9 không chạy được FreeRouting trong môi trường này (không được tải/thực thi phần mềm bên ngoài), nên dùng router lưới tự viết (`router.py`): A* trên lưới 0.1 mm, bản đồ chiếm chỗ đã nới theo clearance, phạt rẽ, via, kiểm khoảng cách lỗ khoan. Khối nguồn và lưỡi cảm biến đi dây tay trong script.
- Kết quả có vài đoạn chéo dài và 18 ký hiệu linh kiện chỉ nằm trên lớp Fab (17 không đủ chỗ trên silkscreen, BT1 do chọn) — xem `docs/limitations.md`.
- Bộ đặt chữ silkscreen tránh pad, courtyard và nét in của linh kiện khác; cung tròn được xét theo đường cong (không theo hình chữ nhật bao). Nhãn bắt buộc (cảnh báo pin, tên bo/revision, tên net của test pad, R1/R21, RST, USER/BOOT, SHT40) phải đặt được, nếu không script dừng với lỗi.

## D18. Điểm đo và link đo dòng

R1 (dòng cell), R21 (dòng tải sau bộ chuyển đổi) là 0R 0805: tháo ra, hàn hai dây tới ampe kế/đầu đo dòng. TP1–TP6 là pad 1.5 mm cho que đo/pogo; silkscreen ghi tên net (VBAT, VIN, VOUT, 3V3, GND, EN) thay cho số TP, vì người đo cần tên tín hiệu; số TP vẫn có trên bản vẽ lắp ráp. Net ra của bộ chuyển đổi đổi tên từ 3V3_PWR (Rev A: điểm OR) thành VOUT, vì Rev B không có OR và nhãn ngắn mới vừa chỗ trên bo nhỏ.

## D19. Data model Matter

Hai endpoint riêng (Temperature Sensor, Humidity Sensor) thay vì gộp, vì đó là cách các hệ sinh thái hiện hiển thị hai giá trị. Power Source ở endpoint 0, `EndpointList` trỏ tới 0/1/2.

## D20. Rev B: một CR2450, bo 41.5 × 57.5 mm

- **Yêu cầu**: người dùng yêu cầu chỉ dùng một pin để bo gọn hơn. Mô hình cho một CR2032 trong cùng mạch (`docs/power_budget.md` mục 4.4): khởi động và commissioning bị reset ngay cả với pin mới ở 25 °C. Kết quả đó được trình cho người dùng, người dùng chọn **1 × CR2450** (cùng hóa học Li-MnO2, 620 mAh, Ø24.5 × 5.0 mm). Thiết kế không tự đổi sang loại pin khác.
- **Đường nguồn (kiến trúc S)**: CR2450 → R1 0R → AO3401A → một TPS63900 3.3 V → VOUT → R21 0R → +3V3. Bỏ Schottky đầu ra vì không còn gì để OR (trên bo không có nguồn nào khác); bỏ luôn sụt áp diode. Theo mô hình, dòng lấy từ cell ở kịch bản danh nghĩa 63 µA (Rev A: 65 µA cho cặp cell).
- **Holder**: MYOUNG BS-24-B4AA016 (LCSC C964809, SMT, tiếp điểm mạ vàng, có ở JLC); footprint dự án vẽ theo bản vẽ MY-CP-0138. Holder 27 × 16 mm đặt dọc mép dưới; cell Ø24.5 mm nhô ra hai cạnh dài của thân, nên F.Cu dưới vòng tròn cell và thân holder bị cấm đồng.
- **Tụ đệm**: thêm một tụ điện phân 470 µF 6.3 V Ø6.3 × 7.7 mm (KNSCHA RVT, LCSC C2901342; cao bằng holder) vào nút VIN, ngoài 10 µF + 2 × 100 µF MLCC. Mô hình: report sống tới trạng thái giữa đời ở 25 °C và tới −10 °C với pin mới; thêm tụ thứ hai sẽ kéo report tới trạng thái late nhưng tốn ~65 mm² bo — Rev B ưu tiên kích thước. Dòng rò tụ điện phân chưa có số liệu ở 3 V (T-39).
- **Hệ quả đã biết (CHƯA ĐẠT, ƯỚC TÍNH)**: từ khoảng một nửa dung lượng, hoặc khi ≤ 0 °C, khởi động và commissioning bị reset ⇒ phải commission bằng pin mới ở nhiệt độ phòng; một lần reset sau giữa đời có thể làm thiết bị ngừng hoạt động tới khi thay pin. Rev A (hai CR2032) còn khởi động lại được ở giữa đời, 25 °C.
- **Bo**: 72 × 58 mm → 41.5 × 57.5 mm (−43 % diện tích). J1 1×6 không có chân nguồn (D14), TP1–TP6 (D18), cầu đo pin còn một (D8), khối nguồn xoay 180°.
- **Firmware**: một kênh ADC (GPIO5/ADC1_CH4), `BAT_CELL_COUNT` = 1, Power Source báo 1 × CR2450 (620 mAh). Logic pin vẫn viết theo mảng `BAT_CELL_COUNT` nên chỉ đổi hằng số; unit test pin được viết lại cho một cell (số đo dưới ngưỡng "có pin" khi đang chạy = lỗi mạch đo ⇒ Critical).

## D21. Biến thể chip rời TH-SENSOR-H2C Rev A (2026-11-06)

- **Yêu cầu**: người dùng yêu cầu một bản dùng chip ESP32-H2 rời thay cho module. Người dùng chọn: ăng-ten in trên PCB, PCB 4 lớp, linh kiện phối hợp RF cỡ 0201, và làm tiếp dù không có VNA. Rev B giữ nguyên.
- **Một nguồn sự thật cho hai bo**: `design.py` chọn biến thể bằng `TH_VARIANT` (`module` mặc định, `chip`); chỉ phần radio và J1 khác. Script schematic/project/báo cáo/sản xuất dùng chung; layout bản chip ở `gen_pcb_chip.py` (dùng lại helper, khối nguồn và lưỡi cảm biến của `gen_pcb.py`). Đầu ra Rev B được kiểm lại là không đổi từng byte.
- **Chip**: ESP32-H2FH4S (4 MB flash trong vỏ, đúng dung lượng của module -H4S) — tồn kho JLC 0; mã ESP32-H2FH4 có hàng nhưng là mã đặt hàng cũ hơn, chưa đối chiếu revision nên không thay.
- **Firmware dùng chung**: mọi GPIO giữ chức năng; `check_pinmap.py --variant chip` kiểm cùng `board_pins.h` với chân QFN.
- **Ăng-ten**: IFA của TI (SWRU120D/DN007) vì có kích thước công bố đầy đủ và cỡ (25.7 × 7.5 mm) vừa chiều rộng bo; vẽ **đối xứng gương** để đầu hở nằm ở mép bo, đoạn ngắn mạch phía chip. Không chép ăng-ten của module Espressif (không có bản vẽ công bố). Vùng ăng-ten trống đồng trên cả 4 lớp; mép mặt đất có hàng via GND.
- **Hướng chip**: xoay 270° để chân ANT ở góc gần ăng-ten và các chân phía ăng-ten chỉ là nguồn + chân bỏ trống + VBAT_SENSE; thạch anh, USB, UART quay ra xa ăng-ten.
- **RF**: đường 0.35 mm trên L1 tham chiếu L2 (≈ 50 Ω theo công thức), không via, góc 135°; mạng CLCCL 0201 xếp zigzag với giá trị khởi đầu giữa khoảng HDG; stub 15 mil / 100 Ω trên pad GND của tụ đầu tiên với L2 bị khoét như HDG yêu cầu; vị trí phía ăng-ten (R41 0 Ω, L5 không lắp) đồng thời là mạng pi TI khuyên.
- **Stack-up**: JLC04161H-7628 vì prepreg 0.21 mm cho đường 50 Ω rộng 0.35 mm (dễ làm hơn 0.17 mm của bản 3313) và stub 100 Ω qua L3 rộng 0.5 mm. L3 là GND + một đảo +3V3 dưới chip nối các nhóm tụ (HDG: nguồn đi ở lớp 3, giữ GND dưới RF và thạch anh).
- **J1**: 2 × 3 (gọn hơn 1 × 6), đặt dưới chip, xa ăng-ten nhất có thể ngoài vùng holder; thứ tự chân giữ như Rev B.
- **Router**: thêm cho bản chip — coi vùng đồng đã đổ của một net là đã nối (đảo +3V3 ở L3), cấm via trong pad SMD, kích thước via theo net; mặc định giữ hành vi cũ nên Rev B không đổi.
- **Lệch so với HDG (ghi nhận, không sửa)**: nguồn < 350 mA (như Rev B); C46 không đứng riêng ở chân 20 (pad C47 nhận chân 18–20); L3 cách chân 4–6 mm; đường nguồn 0.4 mm thay vì 0.5 mm, lỗ via nguồn nhỏ hơn bề rộng đường; không chừa R/C nối tiếp trên USB; tụ ADC 22 nF thay vì 0.1 µF; ăng-ten chưa mô phỏng/đo. Chi tiết: `docs/chip_variant.md` mục 4.

## D22. Biến thể WROOM-02C TH-SENSOR-H2W Rev A (2026-11-06)

- **Yêu cầu**: "thiết kế bản sử dụng module wroom, kích thước nhỏ nhất có thể, kích thước vuông tính cả phần ăng ten nhô ra của module"; "dùng module wroom h2-02c, nhưng cái này tôi sẽ tự mua và hàn". Rev B và H2C giữ nguyên.
- **Giả định đã báo người dùng** (có thể đổi): giữ 1 × CR2450 và holder BS-24-B4AA016, giữ mọi mạch của Rev B, PCB 4 lớp, ăng-ten 6 mm nhô khỏi mép trên, module không có trong BOM JLC.
- **Kích thước**: bề rộng bị chặn dưới bởi land pattern của holder (37.0 mm) + 2 × 0.3 mm đồng–mép = 37.6 mm; holder lật xuống mặt dưới để chồng lên module theo hình chiếu; bo cao 37.6 − 6.0 = 31.6 mm để khung vuông 37.6 × 37.6 mm tính cả ăng-ten. Không bỏ hay thay linh kiện nào để bo nhỏ hơn.
- **Vị trí module**: góc trên phải, vùng ăng-ten ngoài bo — vị trí ③ trong hình "antenna feed point on the right" của HDG (đánh dấu ✓), vì feed của ăng-ten WROOM-02C ở bên phải. Hàng via GND dày dọc mép trên dưới module.
- **Vùng dưới pin ở mặt dưới**: không đường mạch, không đổ đồng; **cho phép via phủ mask** (Rev B cấm cả via dưới pin vì holder ở mặt trên và bo còn chỗ). Lý do: bản vẽ MY-CP-0138 cho thấy pin nằm trên đáy nhựa của holder, không chạm bo; cấm via ở vùng Ø25.7 mm giữa bo thì không đi được dây cho mặt trên trong kích thước này. Rủi ro còn lại ghi ở `docs/limitations.md` mục 11 và kiểm thử W-03.
- **Footprint để hàn tay**: theo land pattern hình 7 của datasheet, thêm một lỗ mạ 0.8 mm ở giữa pad tản nhiệt (mớm thiếc từ mặt dưới), không phủ kem hàn trên pad tản nhiệt. Symbol và footprint vẽ trong `gen_schematic.py` vì không thư viện nào có module này.
- **Mạch quanh module**: chân 14 (VBAT) nối +3V3 (trong module đã nối qua 0 Ω); giữ R22/C25 vì module không có RC trên EN; không thêm 499 Ω cho TXD0 (đã có trong module); C23 đặt ở chân 14, C24 ở chân 1.
- **Router**: thêm tham số lớp (`layers`) để đi dây trên F.Cu + In2.Cu, B.Cu chỉ có pad holder và đổ GND; mặc định không đổi nên Rev B và H2C sinh lại giống từng byte (đã kiểm).
- **Test pad** ở mặt trên như Rev B (đã thử đặt ở mặt dưới, nhưng chỗ trống ở mặt dưới chỉ còn sau module và làm tắc lớp In2); ký hiệu linh kiện không đủ chỗ trên silkscreen chỉ có trên lớp Fab.
- **Sửa ngày 2026-11-07 theo yêu cầu người dùng**: bỏ SW2 (RST) — reset bằng TP6 (EN) xuống GND hoặc reset tự động của USB-Serial/JTAG; SW1 thay bằng nút **bấm cạnh** Panasonic EVQP7A01P ở chính giữa mép trái (loại không chốt, nên không có lỗ xuyên vào pad + của holder ở mặt dưới; Alps SKRTLAE010 có chốt, ở giữa cạnh thì lỗ chốt rơi vào pad + nên không dùng); J1 thành 6 pad dán Ø1.6 mm theo lưới 2 × 3 bước 2.54 mm. Test pad vốn là pad dán. Người dùng giữ hình dạng bo cũ (không lấp vùng cạnh ăng-ten: hướng dẫn của Espressif yêu cầu khoét ≥ 15 mm cạnh vùng ăng-ten).
- **Sửa ngày 2026-11-08 theo yêu cầu người dùng** (giảm chiều cao; người dùng chọn cách 1 trong ba cách được đưa ra): **C5 đổi sang tụ tantal MnO2** Kyocera AVX TAJD477K006RNJ (470 µF 6.3 V ±10 %, vỏ D cao tối đa 3.1 mm, LCSC C7229) và ở lại mặt trên, nên mặt trên không cao hơn module (cả cụm ≈ 12.3 mm thay vì ≈ 16.8 mm, ước tính từ kích thước danh định). Chọn MnO2 chứ không phải tantal polymer vì loại polymer ghi giới hạn rò lớn hơn nhiều; giới hạn rò của TAJ (28 µA ở 6.3 V) cùng cỡ tụ nhôm cũ, rò thực ở ~3 V vẫn phải đo (T-39). Không chuyển tụ nhôm xuống mặt dưới: chỗ trống ở mặt dưới chỉ còn ở góc trên trái (phải dời lưỡi cảm biến) hoặc cạnh lưỡi, sát vùng ăng-ten. Ngày trên bo đổi thành 2026-11-08 để phân biệt với các bản Gerber trước (vẫn Rev A: chưa bản nào được đặt). Rev B và H2C không đổi.
- **Hướng lắp, cùng ngày 2026-11-08**: người dùng muốn cảm biến "hướng xuống" để ít bụi. SHT40 và C29 được đưa xuống mặt dưới của lưỡi một lần, rồi về lại mặt trên khi người dùng nói rõ: cảm biến cùng mặt với các linh kiện khác, cảm biến và nút đều ở phía dưới khi gắn tường. Chọn giữ nguyên bố trí và **gắn tường với cạnh có SW1 quay xuống đất**: SW1 bấm từ dưới lên, lưỡi SHT40 là góc thấp nhất và nằm dưới module (nhiệt bốc lên không qua cảm biến). Đổi lại, ăng-ten module nằm ngang (chưa kiểm thử, W-01). Cách không dùng: giữ ăng-ten ở trên và dời lưỡi cảm biến cùng SW1 xuống cạnh dưới hiện tại — phải sắp xếp lại gần hết nửa dưới bo (khối chuyển đổi, J1, test pad), lưỡi gần bộ chuyển đổi và pin hơn, chưa chắc giữ được 37.6 × 37.6 mm.

## D23. Sửa firmware sau bản đánh giá (2026-11-11)

Người dùng chọn sửa bốn lỗi trong bản đánh giá mã nguồn ("mục 1": các lỗi số 2, 6, 7, 8). Các lỗi khác trong bản đánh giá **chưa sửa** (`docs/limitations.md` mục 13). Tất cả chỉ được kiểm bằng unit test trên host và bằng build; trên phần cứng: CHƯA KIỂM THỬ (T-16…T-16e).

- **Power guard "chết giả" (lỗi 2).** Trước đây mọi lần khởi động chưa kịp "ổn định" đều bị đếm, và chỉ một lần tháo lắp pin, nhấn reset hay nạp firmware cũng đủ đưa thiết bị vào ngủ sâu tới 4 giờ mà không có dấu hiệu gì; còn điều kiện xóa bộ đếm (điện áp tăng 150 mV) lại đúng cả với pin cũ vừa được nghỉ. Quy tắc mới (`guard_policy.c`): lần reset sớm đầu tiên được bỏ qua (`APP_GUARD_FREE_BOOTS` = 2); pin mới được nhận ra khi số đo vừa ≥ `APP_GUARD_FRESH_CELL_MV` (3000 mV) vừa cao hơn lần trước ≥ `APP_GUARD_NEW_CELL_RISE_MV` (50 mV); reset từ USB/JTAG tính như restart phần mềm; số đo dưới `APP_BAT_CELL_PRESENT_MV` là lỗi mạch đo, không phải "pin yếu"; LED nháy 3 lần trước khi ngủ sâu. Ký hiệu Kconfig `APP_GUARD_RECOVERY_MV` đổi tên thành `APP_GUARD_NEW_CELL_RISE_MV` vì ý nghĩa đã khác (một `sdkconfig` cũ sẽ không mang giá trị 150 sang).
- **Không ghép lại được sau khi gỡ fabric cuối cùng (lỗi 6).** Sau commissioning, SDK giải phóng bộ nhớ BLE và không khởi tạo lại được trong cùng một lần chạy. Khi người dùng nhấn 3 lần mà không còn fabric và BLE đã giải phóng, firmware báo LED rồi **khởi động lại**; sau khi khởi động, cửa sổ BLE tự mở (`CONFIG_CHIP_ENABLE_PAIRING_AUTOSTART=y`). Không chọn cách giữ BLE trong bộ nhớ vì tốn RAM suốt đời thiết bị cho một tình huống hiếm.
- **Đo pin trùng xung phát (lỗi 7).** Mỗi lần đo lấy hai mẫu cách nhau `APP_BAT_CONFIRM_DELAY_MS` (1.5 s) và giữ mẫu cao hơn; số đo đầu tiên được công bố là số đo lúc khởi động (trước khi bật radio); bỏ lần đo ngay khi commissioning xong (lúc radio bận nhất).
- **Factory reset không có tác dụng khi Matter chưa chạy (lỗi 8).** `esp_matter::factory_reset()` chỉ xếp việc vào vòng lặp sự kiện của CHIP. Nếu Matter chưa khởi động, hoặc thiết bị không tự khởi động lại trong 15 s, firmware tự xóa phân vùng `nvs` rồi restart. `fctry` và `esp_secure_cert` không bị đụng tới.

## D24. Biến thể CR123A TH-SENSOR-H2W-123 Rev A (2026-11-11)

- **Yêu cầu**: "Làm mục 1 và 3, chiều ngang board là 34,5cm bố trí như hình vẽ. Màu đen là cr123a xanh lá là pcb đỏ là esp h2 wroom hồng là cảm sht40, tổng thế thiết bị là vuông" ("mục 3" = thiết kế một biến thể dùng CR123A, sau bản so sánh CR2450 với CR123A). Đổi loại pin là quyết định của người dùng; Rev B, H2C và H2W giữ nguyên CR2450.
- **Cách hiểu đã báo người dùng kèm hình bố trí đúng tỉ lệ, chưa được xác nhận lại**: (1) "34,5cm" là 34.5 mm và là bề rộng phần mạch — đế pin dài 43.3 mm nên cạnh thiết bị không thể là 34.5 mm; cả thiết bị vuông 53.3 mm tính cả 6 mm ăng-ten nhô ra. (2) Bo một tấm liền, đế pin hàn lên bo (hình vẽ có thể hiểu là pin nằm ngoài bo). (3) Pin ở bên **trái**, tức ảnh gương của hình vẽ, để module đứng ở vị trí ③ của HDG và cách pin 16 mm. Nếu người dùng muốn khác, cả ba điểm đều đổi được bằng cách sửa `gen_pcb_wroom123.py` và sinh lại.
- **Đế pin**: MYOUNG BH-123A-A1CJ002 (LCSC C5290177), xuyên lỗ, có chốt định vị. Chọn vì có ở JLC, có bản vẽ đầy đủ, và cùng hãng với đế CR2450 đang dùng. Footprint vẽ từ bản vẽ, chưa so với đế thật (K-01).
- **Bỏ C5**: theo mô hình, CR123A tự cấp được mọi xung dòng tới hết đời pin với 85 µF tụ gốm có sẵn; 470 µF không đổi kết quả nào (`hardware/analysis/results/cr123a_summary.md`). ƯỚC TÍNH; nếu K-03 cho kết quả khác thì không còn chỗ đặt sẵn cho C5 trên bo này.
- **Thêm F1** (PTC tự phục hồi 0.5 A giữ / 1 A ngắt) ngay sau cực +: CR123A cấp được hàng ampe khi chập mạch, khác với pin đồng xu. Đây là linh kiện mới so với mọi biến thể trước.
- **Firmware dùng chung**, chọn loại pin bằng Kconfig (`APP_CELL_TYPE`) và lớp `sdkconfig.defaults.cr123a`, thay vì tách nhánh mã: bảng phần trăm, chuỗi IEC/dung lượng của cụm Power Source và các ngưỡng mặc định phụ thuộc loại pin; pin map không đổi.
- **Chữ ở mặt sau** ("Matter temperature Sensor / Villa Nest / Made in Vietnam") được mang sang từ H2W; người dùng mới chỉ yêu cầu dòng chữ đó cho H2W. Ghi chú về nhãn hiệu Matter ở `docs/limitations.md` mục 11 áp dụng nguyên.
- **Script riêng** `gen_pcb_wroom123.py` (bản sao có chỉnh sửa của `gen_pcb_wroom.py`) thay vì thêm nhánh vào script H2W, để bo H2W sinh lại giống từng byte (đã kiểm: `git status` không thấy thay đổi ở `hardware/kicad`, `hardware/chip/kicad`, `hardware/wroom/kicad`).
