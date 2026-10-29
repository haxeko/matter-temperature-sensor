# Ngân sách năng lượng và phân tích pin — TH-SENSOR-H2 Rev A

**Trạng thái toàn bộ tài liệu này: ƯỚC TÍNH.** Không có con số nào ở đây là phép đo. Nguồn dữ liệu đầu vào ghi ở mục 1; mô hình là `hardware/analysis/power_model.py`, kết quả đầy đủ ở `hardware/analysis/results/` (`power_model_summary.md`, `power_model_results.json`, `power_model_traces.png`). Các phép đo thay thế ước tính được liệt kê trong `docs/test_plan.md`.

**Kết luận: thiết kế nguồn Rev A CHƯA ĐẠT** yêu cầu "chạy bằng 2 × CR2032 đến khi hết pin". Mô hình cho thấy:
- pin mới, 25 °C: mọi tải (poll, report, khởi động, commissioning) đều ổn;
- pin ở giữa vòng đời, 25 °C: poll/report/khởi động ổn, **commissioning bị reset** sau 10–50 s;
- pin gần cuối đời (late), 25 °C: **report và khởi động bị reset**; ở 0 °C (nội suy) ngay cả pin mới cũng reset khi khởi động, ở −10 °C pin mới reset cả khi report;
- chỉ một cell: poll ổn, report ổn với cell mới, **khởi động và commissioning bị reset**;
- tuổi thọ ở dòng trung bình 65 µA: **0.35–0.58 năm** (không phải 1–2 năm).

## 1. Đầu vào và nguồn

| Đại lượng | Giá trị dùng | Nguồn | Loại |
|---|---|---|---|
| CR2032 danh định | 3 V, 225 mAh, dòng liên tục 0.2 mA, −30…+85 °C | Panasonic CR2032 datasheet (2026) | ĐÃ XÁC MINH (datasheet) |
| Điện trở xung CR2032 | ~10 Ω mới, ~20 Ω khi đã dùng ~60 %, > 40 Ω gần "đầu gối" | TI SWRA349 hình 6 | ƯỚC TÍNH (đọc đồ thị) |
| Phân cực DC | khớp với đường "operating voltage vs load resistance" Panasonic (1 kΩ, 50 % DoD: ~2.75 V ở 20 °C, ~2.4 V ở −10 °C) | Panasonic | ƯỚC TÍNH (khớp đường cong) |
| Nhiệt độ +10 / 0 °C | nội suy giữa 20 °C và −10 °C | — | ƯỚC TÍNH (không có số liệu gốc) |
| ESP32-H2-MINI-1 TX 802.15.4 | +7 dBm 54 mA, −2 dBm 38 mA, RX 29 mA (3.3 V, 25 °C) | Module datasheet v1.6 | ĐÃ XÁC MINH (datasheet) |
| TX ở +5 dBm (firmware) | 50 mA | nội suy | ƯỚC TÍNH |
| Đáy ngủ light sleep | 27 µA | Espressif đo cho ICD trên ESP32-H2 (esp-matter `examples/icd_app`) | ƯỚC TÍNH (số đo của Espressif trên board khác) |
| Điện tích 1 lần poll Thread | 0.25 mC | Espressif đo 0.31–0.40 mC ở 20 dBm, quy đổi về +5 dBm | ƯỚC TÍNH |
| Report Matter + 1 s active mode | 1.42 mC | ước lượng từ chuỗi TX/RX + CPU | ƯỚC TÍNH |
| Tải commissioning (90 s) | 3 profile: 6/12/20 mA nền, RX 30/35/41 mA | không có số đo công bố | ƯỚC TÍNH (giả định) |
| TPS63900 | UVLO 1.75 V lên / 1.65 V xuống, IQ 75 nA, giới hạn dòng vào trung bình 100 mA, hiệu suất 0.9 | SLVSET3D (bảng 7-2) và khuyến nghị của TI dùng 0.9 khi ước tính | ĐÃ XÁC MINH (datasheet), hiệu suất là ƯỚC TÍNH |
| Diode | B5819W (JSCJ), RB521S30 (onsemi rev. 9) — mô hình Shockley khớp đồ thị | datasheet | ƯỚC TÍNH |
| SHT40 | trung bình 0.4 µA (1 phép đo/s), idle 80 nA | Sensirion SHT4x v7.3 | ĐÃ XÁC MINH (datasheet) |
| TPS3839K33 | 150 nA điển hình (500 nA max) | SBVS193D | ĐÃ XÁC MINH (datasheet) |

## 2. Dòng trung bình (tại rail 3V3 và lấy từ cặp cell)

Topology C không có diode ở đầu vào nên dòng lấy từ cặp cell = công suất tải / (hiệu suất × điện áp cell). Bảng: µA.

| Hạng mục | Danh nghĩa (SIT 15 s, 1 report/5 min) | Bận (1 report/min) | Yên (chỉ keep-alive) | Mặc định ví dụ icd_app (poll 5 s) |
|---|---|---|---|---|
| Đáy light sleep | 27.0 | 27.0 | 27.0 | 27.0 |
| Poll Thread | 16.7 | 16.7 | 16.7 | 50.1 |
| Report Matter + active mode | 4.72 | 23.62 | 0.0 | 4.72 |
| Keep-alive subscription (300 s) | 0.0 | 0.0 | 4.72 | 0.0 |
| Đo SHT40 mỗi 60 s | 1.43 | 1.43 | 1.43 | 1.43 |
| Đo pin mỗi 6 h | 0.14 | 0.14 | 0.14 | 0.14 |
| MLE/SRP (giả định) | 1.0 | 1.0 | 1.0 | 1.0 |
| Rò rỉ SHT40 + TPS3839 + tụ/PCB | 0.53 | 0.53 | 0.53 | 0.53 |
| **Tổng tại 3V3** | **51.5** | **70.4** | **51.5** | **84.9** |
| **Lấy từ 2 cell (topology C)** | **65.0** | **88.8** | **65.0** | **107.1** |

So sánh các kiến trúc khác ở kịch bản danh nghĩa: A2 (2 Schottky/cell, 1 bộ chuyển đổi) 72.2 µA; A1 65.9 µA; B 66.3 µA; C 65.0 µA.

## 3. Tuổi thọ theo dòng trung bình (yêu cầu: 25/50/100/200 µA)

Dung lượng dùng được của cặp cell trước khi xung radio bắt đầu làm sụt áp quá mức: 200 / 270 / 330 mAh (bi quan / trung tâm / lạc quan, ƯỚC TÍNH). Danh định 2 × 225 mAh không bao giờ dùng hết được với tải xung 50 mA. Đã tính tự xả 1 %/năm.

| Dòng trung bình | 200 mAh | 270 mAh | 330 mAh |
|---|---|---|---|
| 25 µA | 0.89 năm | 1.21 năm | 1.48 năm |
| 50 µA | 0.45 năm | 0.61 năm | 0.75 năm |
| 65 µA (danh nghĩa Rev A) | 0.35 năm | 0.47 năm | 0.58 năm |
| 100 µA | 0.23 năm | 0.31 năm | 0.37 năm |
| 200 µA | 0.11 năm | 0.15 năm | 0.19 năm |

Muốn đạt 1 năm cần ~25 µA trung bình, tức gần như chỉ còn đáy ngủ 27 µA của Espressif ⇒ **không đạt được với Matter SIT trên ESP32-H2 theo số liệu hiện có**. Không hứa hẹn 1–2 năm.

## 4. Mô phỏng miền thời gian (dòng xung)

Mô hình: mạch tương đương cell (OCV − I·R − 2 phân cực RC), giới hạn dòng vào trung bình của TPS63900, UVLO, hiệu suất 0.9, Schottky OR, tụ, supervisor 2.93 V. Bước 1 ms, giải ẩn (Newton) cho các nút; đã kiểm tra hội tụ với bước 50 µs.

Kết quả rút gọn cho topology C (đầy đủ: `power_model_summary.md`). "RESET" = rail 3V3 < 2.93 V lâu hơn ngưỡng của supervisor.

| Trạng thái cell / nhiệt độ | poll ×5 | report + active | khởi động | commissioning danh nghĩa | commissioning bi quan |
|---|---|---|---|---|---|
| mới, 25 °C | ổn | ổn | ổn | ổn | ổn |
| giữa đời, 25 °C | ổn | ổn | ổn | **RESET** (50 s) | **RESET** (10 s) |
| cuối đời (late), 25 °C | ổn | **RESET** | **RESET** | **RESET** | **RESET** |
| hết (EOL), 25 °C | **RESET** | **RESET** | **RESET** | **RESET** | **RESET** |
| mới, 10 °C (nội suy) | ổn | ổn | ổn | ổn | ổn |
| giữa đời, 10 °C (nội suy) | ổn | ổn | **RESET** | **RESET** | **RESET** |
| mới, 0 °C (nội suy) | ổn | ổn | **RESET** | **RESET** | **RESET** |
| mới, −10 °C | ổn | **RESET** | **RESET** | **RESET** | **RESET** |
| chỉ 1 cell mới | ổn | ổn | **RESET** | **RESET** | **RESET** |
| chỉ 1 cell giữa đời | ổn | **RESET** | **RESET** | **RESET** | **RESET** |
| lệch: mới + late | ổn | ổn | ổn | **RESET** | **RESET** |
| lệch: EOL + mới | ổn | ổn | **RESET** | **RESET** | **RESET** |

Dòng ngược vào cell lớn nhất trong mọi trường hợp của topology C: 0 µA (ƯỚC TÍNH; A1 có 1.4 µA, A2 có 0.05 µA).

Biến thể giới hạn 50 mA (C50, RCFG2 = 13.3 kΩ): sụt áp cell nhỏ hơn nhưng không cải thiện kết quả nào trong bảng (commissioning giữa đời còn reset sớm hơn: 30 s so với 50 s), và **một cell không đủ cho report** (50 mA vào ⇒ ~40 mA ra ở 3.3 V < xung TX 50 mA). Rev A giữ 100 mA.

## 5. Tụ đệm

Công thức TI SWRA349 cho tụ đệm cung cấp phần dòng mà cell không cấp được trong xung dài t:

C = (Q_xung − V_min / R_i · t) / (V_max − V_min)

Với xung report (Q ≈ 1.42 mC, t ≈ 1 s), V_max 2.6 V, V_min 1.8 V:

| R_i của cell | C cần (µF) |
|---|---|
| 20 Ω | 0 |
| 40 Ω | 93 |
| 100 Ω | 1088 |
| 300 Ω | 1531 |
| 1000 Ω | 1686 |

Mô phỏng tìm tụ hiệu dụng tối thiểu ở mỗi nút VIN để 3 poll + 1 report không reset (OCV 2.9 V): 85 µF đủ khi R ≈ 12 Ω, nhưng cần 680 µF khi R ≈ 20 Ω và ≥ 1000 µF (giới hạn trên của phép tìm) khi R ≥ 30 Ω.

Rev A đặt mỗi nút VIN: 10 µF + 2 × 100 µF (1206 X5R 6.3 V). Tụ MLCC X5R mất điện dung theo điện áp DC; ở ~3 V **giả định ~85 µF hiệu dụng** (ƯỚC TÍNH, phải đo hoặc tra đường cong DC-bias của Samsung CL31A107MQHNNNE). Tăng lên ~1000 µF bằng tụ polymer/siêu tụ sẽ thêm dòng rò (thường vài µA, có loại < 1 µA) — cần chọn theo dữ liệu rò thực, nên chưa đưa vào Rev A.

## 6. Các chế độ hỏng và xử lý

| Tình huống | Hệ quả dự kiến | Xử lý trong thiết kế | Trạng thái |
|---|---|---|---|
| Cell yếu, xung TX làm rail < 2.93 V | supervisor reset, khởi động lại lại sụt ⇒ vòng lặp reset | power guard đếm reset trong NVS, ngủ sâu backoff 5 min…4 h, nút USER đánh thức | logic có unit test; trên phần cứng CHƯA KIỂM THỬ |
| Cell < 2.4 V khi khởi động | radio không chạy được | power guard ngủ sâu, không bật radio | như trên |
| Thiếu một cell | đủ cho poll, không đủ khởi động/commissioning | BatChargeLevel = Warning, log cảnh báo | firmware ĐÃ XÁC MINH bằng unit test |
| Lắp ngược một cell | — | P-MOSFET chặn | CHƯA KIỂM THỬ |
| Trộn pin cũ/mới | cell mới gánh phần lớn, cell cũ gần như không xả | mỗi cell một bộ chuyển đổi, không có dòng giữa hai cell | ƯỚC TÍNH (0 µA ngược) |
| Lạnh ≤ 0 °C | R_i tăng 1.7–2.5 lần | không có biện pháp phần cứng ở Rev A | **CHƯA ĐẠT** |
| Commissioning khi pin đã dùng một nửa | reset giữa chừng | khuyến nghị commission bằng pin mới (`docs/commissioning.md`) | **CHƯA ĐẠT** |

## 7. Phương án dự phòng nếu đo thực tế xác nhận "CHƯA ĐẠT"

Các phương án dưới đây **chưa được áp dụng**; mọi thay đổi loại pin là quyết định của người dùng, thiết kế không tự đổi sang AAA hay loại pin khác.

1. Giảm công suất phát 802.15.4 từ +5 dBm xuống 0 dBm (`config set tx_power 0`) — giảm dòng xung, cần kiểm tra link budget.
2. Tăng tụ đệm mỗi nút VIN lên ~1000 µF loại rò thấp (cần chọn linh kiện theo dòng rò đo được).
3. Matter LIT (check-in) với chu kỳ poll dài hơn — cần controller hỗ trợ LIT.
4. Pin dung lượng lớn hơn cùng hóa học Li-MnO2 (CR2450/CR2477) — cần đổi holder và kích thước bo; chỉ làm khi người dùng đồng ý.

Giới hạn dòng 50 mA (mục 4) không nằm trong danh sách vì mô hình cho thấy nó không giúp ích.

## 8. Cách tái tạo

```
cd hardware/analysis
python3 power_model.py --plots          # ~5 phút, ghi results/
```
