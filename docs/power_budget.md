# Ngân sách năng lượng và phân tích pin — TH-SENSOR-H2 Rev B (1 × CR2450)

**Trạng thái toàn bộ tài liệu này: ƯỚC TÍNH.** Không có con số nào ở đây là phép đo. Nguồn dữ liệu đầu vào ghi ở mục 1; mô hình là `hardware/analysis/power_model.py` (kiến trúc "S"), kết quả đầy đủ ở `hardware/analysis/results/` (`power_model_summary.md`, `power_model_results.json`, `power_model_traces.png`). Các phép đo thay thế ước tính được liệt kê trong `docs/test_plan.md` mục D.

Rev B chạy bằng **một CR2450** (Rev A: hai CR2032, mỗi cell một bộ chuyển đổi). Lý do đổi: người dùng yêu cầu một pin và bo gọn hơn; mô hình cho thấy một CR2032 trong cùng mạch bị reset khi khởi động và khi commissioning ngay cả lúc pin mới (mục 4.4), nên người dùng chọn CR2450 (`docs/decisions.md` D20).

**Kết luận: thiết kế nguồn Rev B CHƯA ĐẠT** yêu cầu "chạy bằng pin đến khi hết pin". Mô hình cho thấy:
- pin mới, 25 °C: mọi tải (poll, report, khởi động, commissioning danh nghĩa và bi quan) đều ổn;
- pin mới, 10 °C (nội suy): khởi động và commissioning danh nghĩa ổn (sát giới hạn), commissioning bi quan bị reset;
- pin mới, 0 °C (nội suy) và −10 °C: poll/report ổn, **khởi động và commissioning bị reset**;
- pin giữa đời (đã dùng khoảng một nửa), 25 °C: poll/report ổn, **khởi động và commissioning bị reset** ⇒ từ đây, **mọi lần reset** (sụt áp, watchdog, nút RST, lỗi firmware) có thể làm thiết bị không khởi động lại được cho tới khi thay pin;
- pin cuối đời (late), 25 °C: poll ổn, **report bị reset**;
- tuổi thọ ở dòng trung bình 63–68 µA lấy từ cell: **khoảng 0.5–0.8 năm** (không phải 1–2 năm).

So với Rev A (2 × CR2032, ƯỚC TÍNH cùng mô hình): tuổi thọ ~0.55–0.77 năm thay vì 0.35–0.58 năm, diện tích bo nhỏ hơn 43 % (41.5 × 57.5 mm thay vì 72 × 58 mm), nhưng **mất khả năng khởi động lại khi pin đã dùng một nửa** (Rev A còn khởi động được ở giữa đời, 25 °C).

## 1. Đầu vào và nguồn

| Đại lượng | Giá trị dùng | Nguồn | Loại |
|---|---|---|---|
| CR2450 danh định | 3 V, 620 mAh, dòng liên tục 0.2 mA, Ø24.5 × 5.0 mm, −30…+85 °C | Panasonic CR2450 datasheet (2026) | ĐÃ XÁC MINH (datasheet) |
| Điện trở xung CR2450 | điện trở CR2032 (dưới đây) × 0.60 = tỉ lệ diện tích điện cực (đường kính trong 17.0 / 22.0 mm trên bản vẽ Panasonic, (17/22)²); chạy thêm × 0.4 (lạc quan) và × 1.0 (bi quan, bằng CR2032) | suy ra; Panasonic "capacity vs load": ở 1 kΩ CR2450 cho 84 % dung lượng danh định, CR2032 69 % — cùng chiều với điện trở thấp hơn | ƯỚC TÍNH (không có số liệu xung công bố cho CR2450) |
| Điện trở xung CR2032 (cơ sở) | ~10 Ω mới, ~20 Ω khi đã dùng ~60 %, > 40 Ω gần "đầu gối" | TI SWRA349 hình 6 | ƯỚC TÍNH (đọc đồ thị) |
| Phân cực DC | khớp đường "operating voltage vs load resistance" Panasonic CR2032 (1 kΩ, 50 % DoD: ~2.75 V ở 20 °C, ~2.4 V ở −10 °C); dòng tham chiếu Tafel nhân theo diện tích cho CR2450 | Panasonic | ƯỚC TÍNH (khớp đường cong) |
| Nhiệt độ +10 / 0 °C | nội suy giữa 20 °C và −10 °C | — | ƯỚC TÍNH (không có số liệu gốc) |
| ESP32-H2-MINI-1 TX 802.15.4 | +7 dBm 54 mA, −2 dBm 38 mA, RX 29 mA (3.3 V, 25 °C) | Module datasheet v1.6 | ĐÃ XÁC MINH (datasheet) |
| TX ở +5 dBm (firmware) | 50 mA | nội suy | ƯỚC TÍNH |
| Đáy ngủ light sleep | 27 µA | Espressif đo cho ICD trên ESP32-H2 (esp-matter `examples/icd_app`) | ƯỚC TÍNH (số đo của Espressif trên board khác) |
| Điện tích 1 lần poll Thread | 0.25 mC | Espressif đo 0.31–0.40 mC ở 20 dBm, quy đổi về +5 dBm | ƯỚC TÍNH |
| Report Matter + 1 s active mode | 1.42 mC | ước lượng từ chuỗi TX/RX + CPU | ƯỚC TÍNH |
| Khởi động nguội | 0.3 s × 22 mA, 0.1 s × 45 mA (hiệu chuẩn radio), 0.4 s × 15 mA tại 3V3 | không có số đo công bố | ƯỚC TÍNH (giả định; T-33 đo) |
| Tải commissioning (90 s) | 3 profile: 6/12/20 mA nền, RX 30/35/41 mA | không có số đo công bố | ƯỚC TÍNH (giả định) |
| TPS63900 | UVLO 1.75 V lên / 1.65 V xuống, IQ 75 nA, giới hạn dòng vào trung bình 100 mA, hiệu suất 0.9 | SLVSET3D (bảng 7-2) và khuyến nghị của TI dùng 0.9 khi ước tính | ĐÃ XÁC MINH (datasheet), hiệu suất là ƯỚC TÍNH |
| Tụ đệm đầu vào | 10 µF + 2 × 100 µF MLCC (giả định ~85 µF hiệu dụng ở 3 V) + 470 µF điện phân (KNSCHA RVT, ±20 %) = 555 µF; 461 µF khi tụ điện phân ở −20 % | datasheet tụ; DC-bias MLCC là giả định | ƯỚC TÍNH |
| Rò tụ điện phân | datasheet chỉ cho ≤ 0.01 CV hoặc 3 µA sau 2 phút ở điện áp định mức (= 29.6 µA ở 6.3 V); ở ~3 V sau khi ổn định dự kiến thấp hơn nhiều nhưng không có số liệu ⇒ tính 0 / 1 / 5 µA | KNSCHA RVT datasheet (LCSC C2901342) | ƯỚC TÍNH (T-39 đo) |
| SHT40 | trung bình 0.4 µA (1 phép đo/s), idle 80 nA | Sensirion SHT4x v7.3 | ĐÃ XÁC MINH (datasheet) |
| TPS3839K33 | 150 nA điển hình (500 nA max) | SBVS193D | ĐÃ XÁC MINH (datasheet) |

Trạng thái cell trong mô hình: "mới" ≈ 0 % đã dùng, "giữa đời" ≈ 50–60 %, "late" gần đầu gối đường xả, "EOL" sau đầu gối (theo các mốc điện trở của SWRA349 hình 6).

## 2. Dòng trung bình (tại rail 3V3 và lấy từ cell)

Rev B không có diode ở đầu vào hay đầu ra, nên dòng lấy từ cell = công suất tải / (hiệu suất × điện áp cell) + rò của tụ điện phân. Bảng: µA.

| Hạng mục | Danh nghĩa (SIT 15 s, 1 report/5 min) | Bận (1 report/min) | Yên (chỉ keep-alive) | Mặc định ví dụ icd_app (poll 5 s) |
|---|---|---|---|---|
| Đáy light sleep | 27.0 | 27.0 | 27.0 | 27.0 |
| Poll Thread | 16.7 | 16.7 | 16.7 | 50.1 |
| Report Matter + active mode | 4.72 | 23.62 | 0.0 | 4.72 |
| Keep-alive subscription (300 s) | 0.0 | 0.0 | 4.72 | 0.0 |
| Đo SHT40 mỗi 60 s | 1.43 | 1.43 | 1.43 | 1.43 |
| Đo pin mỗi 6 h | 0.14 | 0.14 | 0.14 | 0.14 |
| MLE/SRP (giả định) | 1.0 | 1.0 | 1.0 | 1.0 |
| Rò SHT40 + TPS3839 + tụ MLCC/PCB | 0.53 | 0.53 | 0.53 | 0.53 |
| **Tổng tại 3V3** | **51.5** | **70.4** | **51.5** | **84.9** |
| **Lấy từ CR2450, rò tụ điện phân 0 µA** | **63.1** | **86.1** | **63.1** | **103.9** |
| **… rò 1 µA** | **64.1** | **87.1** | **64.1** | **104.9** |
| **… rò 5 µA** | **68.1** | **91.1** | **68.1** | **108.9** |

## 3. Tuổi thọ theo dòng trung bình (yêu cầu: 25/50/100/200 µA)

Dung lượng dùng được trước khi report bắt đầu làm reset: 310 / 370 / 435 mAh = 50 / 60 / 70 % của 620 mAh (bi quan / trung tâm / lạc quan, ƯỚC TÍNH: với tụ đệm Rev B, report bắt đầu hỏng giữa trạng thái "giữa đời" và "late"). Đã tính tự xả 1 %/năm.

| Dòng trung bình | 310 mAh | 370 mAh | 435 mAh |
|---|---|---|---|
| 25 µA | 1.38 năm | 1.64 năm | 1.93 năm |
| 50 µA | 0.70 năm | 0.83 năm | 0.98 năm |
| 64 µA (danh nghĩa Rev B, rò 1 µA) | 0.55 năm | 0.65 năm | 0.77 năm |
| 100 µA | 0.35 năm | 0.42 năm | 0.49 năm |
| 200 µA | 0.18 năm | 0.21 năm | 0.25 năm |

Muốn đạt 1 năm cần dòng trung bình lấy từ cell khoảng 35–49 µA, tức tải 3V3 chỉ ~30–40 µA, trong khi riêng đáy ngủ 27 µA + poll SIT 15 s đã là 43.7 µA ⇒ **không đạt được với Matter SIT trên ESP32-H2 theo số liệu hiện có**. Không hứa hẹn 1–2 năm.

Lưu ý: tuổi thọ trên chỉ tính tới khi report hỏng. Khả năng **khởi động lại** mất sớm hơn nhiều (mục 4): sau khoảng một nửa dung lượng, thiết bị chỉ chạy tiếp được nếu không bị reset.

## 4. Mô phỏng miền thời gian (dòng xung)

Mô hình: mạch tương đương cell (OCV − I·R − 2 phân cực RC), P-MOSFET + holder + link 0R (0.15 Ω), giới hạn dòng vào trung bình của TPS63900, UVLO, hiệu suất 0.9, tụ đệm, supervisor 2.93 V. Bước 1 ms, giải ẩn (Newton) cho các nút; đã kiểm tra hội tụ với bước 50 µs. "RESET" = rail 3V3 < 2.93 V lâu hơn ngưỡng của supervisor.

### 4.1 Rev B, tụ đệm danh nghĩa 555 µF

| Trạng thái cell / nhiệt độ | poll ×5 | report + active | khởi động | commissioning danh nghĩa | commissioning bi quan |
|---|---|---|---|---|---|
| mới, 25 °C | ổn | ổn | ổn | ổn | ổn |
| giữa đời, 25 °C | ổn | ổn | **RESET** | **RESET** (10 s) | **RESET** |
| cuối đời (late), 25 °C | ổn | **RESET** | **RESET** | **RESET** | **RESET** |
| hết (EOL), 25 °C | ổn | **RESET** | **RESET** | **RESET** | **RESET** |
| mới, 10 °C (nội suy) | ổn | ổn | ổn | ổn (bộ chuyển đổi chạm UVLO, rail giữ được) | **RESET** (10 s) |
| giữa đời, 10 °C (nội suy) | ổn | ổn | **RESET** | **RESET** | **RESET** |
| mới, 0 °C (nội suy) | ổn | ổn | **RESET** | **RESET** (10 s) | **RESET** |
| giữa đời, 0 °C (nội suy) | ổn | ổn (VIN xuống 1.68 V) | **RESET** | **RESET** | **RESET** |
| mới, −10 °C | ổn | ổn | **RESET** | **RESET** | **RESET** |
| giữa đời, −10 °C | ổn | **RESET** | **RESET** | **RESET** | **RESET** |

### 4.2 Tụ đệm tối thiểu (461 µF, tụ điện phân −20 %)

Khác với 4.1 ở: giữa đời 0 °C report bị **RESET**; mới −10 °C report còn ổn nhưng VIN xuống 1.68 V (sát UVLO 1.65 V).

### 4.3 Độ nhạy theo điện trở CR2450

| Trạng thái, 25 °C | R × 0.4 (lạc quan) | R × 0.6 (trung tâm, bảng 4.1) | R × 1.0 (bi quan, bằng CR2032) |
|---|---|---|---|
| mới | report, khởi động, commissioning ổn | ổn | report ổn; **khởi động và commissioning RESET** |
| giữa đời | report, khởi động, commissioning danh nghĩa ổn | khởi động/commissioning **RESET** | report ổn (VIN 1.75 V); khởi động/commissioning **RESET** |
| late | report ổn (VIN 1.69 V); khởi động **RESET** | report **RESET** | report **RESET** |

Commissioning 90 s với pin mới: ổn với cả ba profile ở 25 °C; ở 10 °C ổn với profile lạc quan và danh nghĩa, reset với bi quan. Pin giữa đời 25 °C: reset với cả ba profile.

Điện trở thật của CR2450 là ẩn số lớn nhất của Rev B: nếu nó gần CR2032 (× 1.0) thì ngay cả pin mới cũng không khởi động được theo mô hình. T-35 đo trực tiếp.

### 4.4 Tham chiếu: một CR2032 trong cùng mạch

| Trạng thái | poll ×5 | report | khởi động | commissioning |
|---|---|---|---|---|
| CR2032 mới, 25 °C | ổn | ổn | **RESET** | **RESET** |
| CR2032 giữa đời, 25 °C | ổn | ổn (VIN 1.75 V) | **RESET** | **RESET** |

Đây là kết quả đã đưa người dùng tới quyết định chọn CR2450 thay vì CR2032.

Dòng ngược vào cell: 0 µA trong mọi trường hợp (trên bo không có nguồn nào khác ngoài cell).

## 5. Tụ đệm

Công thức TI SWRA349 cho tụ đệm cung cấp phần dòng mà cell không cấp được trong xung dài t:

C = (Q_xung − V_min / R_i · t) / (V_max − V_min)

Mô phỏng tìm tụ hiệu dụng tối thiểu ở nút VIN để chuỗi tải không reset:

| Kịch bản | poll ×5 | report + active | khởi động |
|---|---|---|---|
| giữa đời, 25 °C | 85 µF | 85 µF | 2200 µF |
| late, 25 °C | 85 µF | 765 µF | > 4700 µF |
| mới, −10 °C | 85 µF | 400 µF | > 4700 µF |
| giữa đời, 0 °C | 85 µF | 555 µF | > 4700 µF |
| giữa đời, −10 °C | 85 µF | 765 µF | > 4700 µF |
| late, 25 °C, R × 1.0 | 220 µF | 1025 µF | > 4700 µF |

Rev B đặt ở nút VIN: 10 µF (0603) + 2 × 100 µF (1206 X5R 6.3 V, giả định ~85 µF hiệu dụng ở ~3 V) + **một tụ điện phân 470 µF 6.3 V** (Ø6.3 × 7.7 mm, cao bằng holder) = 555 µF danh nghĩa. Thêm một tụ 470 µF nữa (≥ 765 µF) sẽ giữ report tới trạng thái late ở 25 °C, nhưng tốn ~65 mm² bo; Rev B ưu tiên kích thước (D20). Khởi động khi pin đã giữa đời cần ≥ 2200 µF — không có phương án tụ hợp lý trên bo này.

Tụ điện phân có dòng rò: datasheet chỉ cho giới hạn ở điện áp định mức (29.6 µA); ở 3 V sau khi ổn định chưa có số liệu. Ngân sách tính 0 / 1 / 5 µA (tương đương 0 / 1.6 / 8 % dòng danh nghĩa). Nếu T-39 đo được > 5 µA sau 24 h ở 3 V: thay bằng loại rò thấp (polymer hoặc loại "low leakage") có số liệu rò công bố.

## 6. Các chế độ hỏng và xử lý

| Tình huống | Hệ quả dự kiến | Xử lý trong thiết kế | Trạng thái |
|---|---|---|---|
| Cell yếu, xung TX làm rail < 2.93 V | supervisor reset, khởi động lại lại sụt ⇒ vòng lặp reset | power guard đếm reset trong NVS, ngủ sâu backoff 5 min…4 h, nút USER đánh thức | logic có unit test; trên phần cứng CHƯA KIỂM THỬ |
| Bất kỳ reset nào sau khoảng một nửa dung lượng (sụt áp, watchdog, nút RST, lỗi firmware) | khởi động bị reset ⇒ thiết bị ngừng hoạt động tới khi thay pin; power guard giới hạn số lần thử nhưng không làm khởi động thành công | không có biện pháp phần cứng trong Rev B | **CHƯA ĐẠT** |
| Cell < 2.4 V khi khởi động | radio không chạy được | power guard ngủ sâu, không bật radio | logic có unit test |
| Commissioning với pin đã dùng hoặc lạnh | reset giữa chừng | commission bằng pin mới ở nhiệt độ phòng, hoặc bằng nguồn bench vào TP1 VBAT (**đã tháo pin**) — `docs/commissioning.md` | **CHƯA ĐẠT** |
| Lạnh ≤ 0 °C | R_i tăng 1.7–2.5 lần | report còn ổn tới −10 °C với pin mới, tới 0 °C với pin giữa đời; khởi động thì không | **CHƯA ĐẠT** |
| Lắp ngược cell | — | P-MOSFET chặn | CHƯA KIỂM THỬ (T-03) |
| Nguồn bench và pin cùng lúc | nguồn bench nạp ngược vào cell | quy trình: luôn tháo pin trước khi cấp nguồn vào TP1; J1 không có chân nguồn, cắm USB không cấp điện cho bo | quy trình, không có rào cản phần cứng |
| Rò tụ điện phân | 0–5 µA (≤ 8 % ngân sách) | đo T-39; thay loại tụ nếu vượt | ƯỚC TÍNH |
| Phần trăm pin | suy từ điện áp đo khi chip thức (tải nhẹ, sụt I·R ~0.1 V ở giữa đời); ở giữa đời số này còn quanh 50 % (bảng điện áp → phần trăm trong `firmware/components/app_logic/battery_model.c`) trong khi mô hình dự đoán đã không khởi động lại được | BatChargeLevel Warning < 40 %, Critical < 20 % hoặc cell < 2.6 V; ngưỡng là tham số Kconfig, chỉnh sau T-35/T-37 | ƯỚC TÍNH |

## 7. Phương án dự phòng nếu đo thực tế xác nhận "CHƯA ĐẠT"

Các phương án dưới đây **chưa được áp dụng**; mọi thay đổi loại pin là quyết định của người dùng, thiết kế không tự đổi sang AAA hay loại pin khác.

1. Giảm công suất phát 802.15.4 từ +5 dBm xuống 0 dBm (`config set tx_power 0`) — giảm dòng xung, cần kiểm tra link budget.
2. Thêm tụ đệm: một tụ 470 µF nữa (report tới trạng thái late theo mô hình) — bo rộng thêm; hoặc loại rò thấp dung lượng lớn hơn.
3. Firmware: giảm dòng lúc khởi động (tần số CPU thấp hơn trong lúc khởi tạo, chờ tụ nạp lại trước khi bật radio) — chỉ quyết định được sau khi đo dạng dòng khởi động thật (T-33).
4. Matter LIT (check-in) với chu kỳ poll dài hơn — cần controller hỗ trợ LIT.
5. Pin Li-MnO2 dày hơn cùng đường kính (CR2477) — cần holder khác; chỉ làm khi người dùng đồng ý.

## 8. Cách tái tạo

```
cd hardware/analysis
python3 power_model.py --plots          # ~6 phút, ghi results/ (cần matplotlib cho --plots)
```

Kết quả Rev A (2 × CR2032, các kiến trúc A2/A1/B/C/C50/B0) vẫn nằm ở nửa sau của `power_model_summary.md` để làm hồ sơ cho quyết định D2.
