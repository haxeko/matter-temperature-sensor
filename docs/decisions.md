# Các quyết định thiết kế — TH-SENSOR-H2 Rev A

Mỗi mục: quyết định, lý do, phương án đã cân nhắc, trạng thái bằng chứng.

## D1. Module ESP32-H2-MINI-1-H4S

- **Quyết định**: dùng module có anten PCB, flash 4 MB (H4S), không thiết kế chip-down.
- **Lý do**: phần RF, thạch anh 32 MHz, flash đã được Espressif thiết kế sẵn; 4 MB đủ cho hai slot app 1.875 MB (A/B) nếu sau này bật OTA. Firmware hiện chiếm 1.60 MB (battery) / 1.66 MB (debug), còn trống 18 % slot (ĐÃ XÁC MINH bằng `idf.py size`).
- **Rủi ro**: JLC tồn kho 0 ngày 2026-10-29 (`hardware/production/manufacturing_blockers.md`). Order code đã kiểm: ESP32-H2-MINI-1-H4S, LCSC C47967030.

## D2. Kiến trúc nguồn: một TPS63900 cho mỗi cell (topology C)

Các phương án được mô phỏng cùng tải, cùng tụ (`docs/power_budget.md`, ƯỚC TÍNH):

| Mã | Mô tả | Ưu điểm | Nhược điểm chính (theo mô hình) |
|---|---|---|---|
| A2 | 2 Schottky nối tiếp mỗi cell (RB521S30 + B5819W) → VBAT_OR → 1 TPS63900 3.3 V | đúng nguyên văn "VBAT_OR", hai rào cản | sụt áp diode 0.38 V: ngay cả pin mới, 25 °C, cũng reset khi khởi động và commissioning |
| A1 | 1 Schottky/cell → 1 TPS63900 | sụt áp nhỏ hơn A2 | một rào cản; dòng ngược 1.4 µA khi lệch cell; pin giữa đời reset khi khởi động |
| B | 1 TPS63900 3.3 V/cell, Schottky ở đầu vào | mỗi cell một bộ chuyển đổi | Schottky ở đầu vào ăn vào khoảng UVLO; pin giữa đời reset khi khởi động |
| B0 | như B nhưng P-MOSFET thay Schottky | ít sụt áp | chỉ một rào cản chống sạc ngược |
| **C** | **1 TPS63900 3.4 V/cell, P-MOSFET ở vào, B5819W ở ra** | **không sụt áp ở đầu vào (cell xuống tới UVLO 1.65 V); hai rào cản; dòng ngược 0 µA** | **vẫn CHƯA ĐẠT khi pin giữa đời commission, pin cuối đời, lạnh, thiếu cell** |
| C50 | như C, giới hạn 50 mA | sụt áp cell nhỏ hơn | một cell không đủ cho report; không cải thiện trường hợp nào |

- **Quyết định**: C. Đây vẫn là "song song có cách ly ngược từng cell": mỗi cell chỉ cấp vào bộ chuyển đổi của riêng nó; hai đầu ra OR qua Schottky.
- Hai rào cản chống sạc cell: (1) TPS63900 không có đường dẫn từ VOUT về VIN khi VOUT cao hơn điểm đặt (4 khóa, không đóng cắt), (2) Schottky ra. Hành vi (1) suy ra từ cấu trúc trong datasheet, **CHƯA KIỂM THỬ**; test T-05 đo trực tiếp.

## D3. VO(2) = 3.4 V

Rail sau Schottky = 3.4 V − Vf ⇒ 3.07–3.33 V theo dòng (ƯỚC TÍNH), luôn ≥ 3.0 V (min của module) và cao hơn ngưỡng supervisor 2.93 V (±1 %) với khoảng dự trữ. Cấu hình theo bảng 7-2 SLVSET3D: RCFG1 = 0 Ω, RCFG2 = 10.5 kΩ (100 mA); RCFG3 = 16.2 kΩ (VO(1) = 3.3 V, không dùng vì SEL nối VIN). Điện trở 1 %/100 ppm đúng yêu cầu ±1 %, ±200 ppm của TI.

## D4. P-MOSFET AO3401A chống ngược cực

Schottky ở đầu vào làm mất 0.2–0.3 V ngay tại chỗ cell yếu nhất; P-MOSFET (G nối GND, D phía cell) dẫn với điện trở vài chục mΩ khi Vgs ≈ −VBAT. AO3401A: Vgs(th) −0.5/−0.9/−1.3 V (min/typ/max, datasheet) — với cell xuống ~1.7 V MOSFET vẫn mở nhưng điện trở tăng; ở vùng đó bộ chuyển đổi đã gần UVLO 1.65 V. Mức sụt thực tế **CHƯA KIỂM THỬ** (T-04).

## D5. Giới hạn dòng vào 100 mA

Cần để một cell mới tự cấp được xung TX (50 mA ở 3.3 V ⇒ ~60 mA vào ở 2.9 V với hiệu suất 0.9). Giới hạn 50 mA (C50) bị loại theo mô hình (D2).

## D6. Supervisor TPS3839K33 → EN

Ngưỡng 2.93 V, trễ 200 ms, 150 nA. Giữ ESP32-H2 trong reset khi rail không đủ, tránh chạy dở dang (ghi flash dở) khi pin yếu. Đẩy-kéo nên nối EN qua R22 10 kΩ để nút RST và J1 vẫn kéo được EN. Dùng thêm brown-out detector bên trong chip ở mức mặc định của ESP-IDF.

## D7. Power guard trong NVS

Reset bởi EN xóa RAM RTC (không giữ được bộ đếm qua `RTC_NOINIT_ATTR`), vì vậy số lần khởi động không ổn định và điện áp cell lần cuối được lưu trong NVS. Có ngủ sâu backoff để không lặp vô hạn. Logic thuần C có 4 test (ĐÃ XÁC MINH trên host).

## D8. Đo từng cell bằng cầu chia có công tắc

Cầu chia luôn bật (470k + 470k) tiêu thụ ~3.2 µA mỗi cell — bằng 5 % ngân sách 65 µA. 2N7002 phía thấp, gate kéo xuống 1M, chỉ bật 30 ms mỗi 6 giờ. Tụ 22 nF tại chân ADC giữ điện tích cho mạch lấy mẫu. ADC1_CH3 (GPIO4) và ADC1_CH4 (GPIO5), suy hao 6 dB, hiệu chuẩn curve fitting.

## D9. SHT40-AD1B, không dùng heater khi đo thường

- Địa chỉ 0x44, lệnh đo độ chính xác cao, CRC-8 kiểm từng word (driver `components/sht40`, có test).
- Heater chỉ có qua lệnh bảo trì `heater <mW> <ms>`; sau xung nhiệt, firmware không công bố số đo trong 120 s (`APP_HEATER_HOLDOFF_S`).
- Cảm biến đặt trên lưỡi tách nhiệt ở góc trên-phải, xa bộ chuyển đổi và module; không đổ đồng trên lưỡi. Lý do: datasheet SHT4x v7.3 mục 5.5 cho nhiệt trở R_θJA ~250–360 K/W, nên nhiệt dẫn qua đồng từ phần còn lại của bo đi thẳng vào số đo nhiệt độ. Hiệu quả của lưỡi tách **CHƯA KIỂM THỬ** (T-12).

## D10. Thạch anh 32.768 kHz

RTC dùng thạch anh ngoài để đồng hồ ngủ chính xác (SED Thread thức dậy đúng lịch poll, ít phải mở cửa sổ nhận rộng). Tụ tải 18 pF tính cho CL 12.5 pF với giả định ~3 pF ký sinh: **phải chỉnh ở bring-up** (T-09).

## D11. ICD SIT, slow poll 15 s

SIT không đòi controller hỗ trợ LIT/check-in. 15 s là mức tối đa cho phép của SIT; so với 5 s của ví dụ, dòng trung bình giảm từ 107 µA xuống 65 µA (ƯỚC TÍNH). Đổi lại độ trễ lệnh từ controller tới thiết bị lên tới 15 s (cảm biến chỉ đọc nên chấp nhận được).

## D12. BLE +3 dBm khi commissioning

Mặc định +9 dBm (~55 mA) quá gần khả năng cấp dòng của đường nguồn coin-cell. Commissioning thường làm cạnh điện thoại. BLE chỉ dùng để commission rồi được giải phóng.

## D13. Vị trí module theo hướng dẫn anten của Espressif ⇒ đổi chân GPIO

ESP32-H2 Hardware Design Guidelines (mục "Positioning a Module on a Base Board", hình "Keepout Zone ... Antenna feed point on the left"): module ở góc, mép module ≤ 2 mm từ mép bo, ≤ 1 mm từ mép trên, khoét bo ≥ 15 mm cạnh vùng anten 5.4 mm. Rev A: 2.0 mm / 0.5 mm / rãnh 15.2 × 6.0 mm.

Hệ quả: dải 2 mm bên trái module chỉ đủ cho 3V3 và EN, nên ba tín hiệu chuyển từ cạnh trái xuống cạnh dưới module:

| Tín hiệu | Trước | Rev A |
|---|---|---|
| VBAT_MEAS_EN | GPIO0 (pad 9) | GPIO12 (pad 16) |
| VBAT1_SENSE | GPIO1 / ADC1_CH0 (pad 10) | GPIO5 / ADC1_CH4 (pad 19) |
| LED | GPIO12 (pad 16) | GPIO22 (pad 24) |

Đã cập nhật đồng thời schematic (`design.py`), `board_pins.h`, `battery.c`; `tools/check_pinmap.py` kiểm hai phía khớp nhau (ĐÃ XÁC MINH).

## D14. J1 nằm ngang 1×7, bỏ EN

J1 dọc 1×8 cũ tạo một "bức tường" giữa bo. J1 mới nằm dưới rãnh anten, thứ tự chân theo thứ tự chân module (TX, RX, D+, D−, BOOT, 3V3_DBG, GND). EN không còn trên J1: nạp firmware qua USB-Serial/JTAG tự reset được, hoặc dùng nút RST + BOOT.

## D15. Không có OTA trong Rev A

Bảng phân vùng có hai slot A/B (giống `icd_app`), nhưng OTA Requestor tắt vì chưa được kiểm với một OTA Provider thật. Không tuyên bố hỗ trợ OTA.

## D16. Linh kiện JLC

Ưu tiên Basic. Các linh kiện Extended là bắt buộc về chức năng: TPS63900, TPS3839K33, SHT40, DFE201612E, ESP32-H2-MINI-1, holder 1060TR, và hai giá trị RCFG 10.5 kΩ / 16.2 kΩ (bảng cấu hình TI không có giá trị thay thế trong thư viện Basic).

## D17. PCB 2 lớp, đi dây bằng script

- KiCad 9 không chạy được FreeRouting trong môi trường này (không được tải/thực thi phần mềm bên ngoài), nên dùng router lưới tự viết (`router.py`): A* trên lưới 0.1 mm, bản đồ chiếm chỗ đã nới theo clearance, phạt rẽ, via, kiểm khoảng cách lỗ khoan. Khối nguồn và lưỡi cảm biến đi dây tay trong script.
- Kết quả có vài đoạn chéo dài và 21 ký hiệu linh kiện chỉ nằm trên lớp Fab (không đủ chỗ trên silkscreen) — xem `docs/limitations.md`.

## D18. Điểm đo và link đo dòng

R1/R11 (dòng từng cell), R21 (dòng tải sau bộ chuyển đổi) là 0R 0805: tháo ra, hàn hai dây tới ampe kế/đầu đo dòng. TP1–TP10 là pad 1.5 mm cho que đo/pogo.

## D19. Data model Matter

Hai endpoint riêng (Temperature Sensor, Humidity Sensor) thay vì gộp, vì đó là cách các hệ sinh thái hiện hiển thị hai giá trị. Power Source ở endpoint 0, `EndpointList` trỏ tới 0/1/2.
