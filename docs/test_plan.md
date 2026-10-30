# Kế hoạch bring-up và kiểm thử — TH-SENSOR-H2 Rev B

**Tất cả các mục dưới đây: CHƯA KIỂM THỬ** (chưa có bo). Khi làm, ghi kết quả, ngày, số serial bo và dụng cụ đo vào cột "Kết quả" của một bản sao tài liệu này; thay số ƯỚC TÍNH trong `docs/power_budget.md` bằng số đo.

Dụng cụ cần: nguồn bench có giới hạn dòng, đồng hồ vạn năng, máy đo dòng có dải µA và lấy mẫu nhanh (ví dụ Nordic PPK2, Joulescope hoặc tương đương), oscilloscope, vài CR2450 mới cùng lô và vài cell đã xả có kiểm soát tới ~50 % và ~80 % dung lượng, tủ lạnh/tủ nhiệt (0 °C và −10 °C), cảm biến tham chiếu nhiệt ẩm, một Thread Border Router + Matter controller (xem `docs/commissioning.md`).

Điểm đo (silkscreen ghi tên net, không ghi số TP): TP1 VBAT, TP2 VIN, TP3 VOUT, TP4 +3V3 ("3V3"), TP5 GND, TP6 EN; BOOT ở J1 chân 5. Link đo dòng: R1 (dòng cell), R21 (tải sau bộ chuyển đổi).

**Quy tắc an toàn cho cả tài liệu: không bao giờ cấp nguồn bench khi pin đang nằm trong holder.** Bo không có rào cản phần cứng nào chống nạp ngược ngoài bản thân bộ chuyển đổi (`docs/limitations.md` mục 3).

## A. Bo trần và đường nguồn (trước khi lắp pin)

| ID | Kiểm tra | Cách làm | Tiêu chí đạt |
|---|---|---|---|
| T-01 | Ngắn mạch | Đo điện trở VBAT (TP1), VIN (TP2), VOUT (TP3), +3V3 (TP4) so với GND (TP5) | > 10 kΩ (tụ đang nạp, nhất là C5 470 µF, cho số thấp lúc đầu; chờ ổn định) |
| T-02 | Khởi động bộ chuyển đổi | Tháo R21 (cách ly tải). Cấp 3.0 V, giới hạn 50 mA vào TP1, GND ở TP5 | VOUT (TP3) = 3.30 V ±2 %; dòng vào ghi lại sau 1 min và sau 10 min (tụ điện phân còn đang ổn định, xem T-39) |
| T-03 | Ngược cực | Cấp −3.0 V (giới hạn 10 mA) vào TP1 | VIN (TP2) ≈ 0 V; dòng ≤ ~6 µA (chỉ còn đường qua R31 470 kΩ tới diode kẹp của GPIO5 và diode thân của Q3, ƯỚC TÍNH ≈ 5 µA); không phần nào nóng |
| T-04 | Sụt áp R1 + P-MOSFET | Tải 50 mA ở VOUT (R21 tháo, tải điện tử ở TP3), đo TP1 − TP2 | < 20 mV ở 2.9 V vào; ghi lại ở 1.8 V vào |
| T-05 | Dòng ngược vào nguồn cell | Tháo R1, đặt ampe kế giữa hai pad R1; nguồn 2.6 V ở TP1 qua ampe kế; ép VOUT (TP3) lên 3.45 V bằng nguồn thứ hai (cao hơn điểm đặt 3.3 V). Đo ở 25 °C và 60 °C | dòng chảy vào phía cell ≤ 2 µA (Panasonic: tổng điện tích nạp vào coin cell trong đời sử dụng ≤ 3 % dung lượng; 620 mAh × 3 % / 1 năm ≈ 2.1 µA) |
| T-06 | Giới hạn dòng vào | Nguồn 2.9 V nối tiếp 10 Ω (giả lập CR2450 mới theo mô hình) vào TP1, tải xung 60 mA / 5 ms ở TP3 | dòng vào trung bình không vượt ~100 mA; rail không sụt dưới 3.0 V |
| T-07 | Supervisor | R21 tháo, U4 chưa lắp; cấp nguồn ngoài vào TP4 (+3V3) rồi hạ dần; đo nRST (pad R22 phía U3) và EN (TP6) | nRST xuống thấp tại 2.86–2.97 V (VIT− của TPS3839K33); lên lại sau 120–350 ms; EN theo sau qua RC 10 kΩ / 1 µF (τ ≈ 10 ms) |
| T-08 | Holder và cực | Footprint holder là footprint tự vẽ: trước khi hàn, đặt holder thật lên bo và so pad; sau khi hàn (R21 tháo, không nguồn bench) lắp CR2450 mặt + theo hướng dẫn của holder | holder nằm đúng pad; TP1 = +2.9…3.3 V so với TP5 (không phải âm); cell giữ chắc, không chạm linh kiện bên cạnh; tháo cell ra trước bước tiếp theo |

## B. Module, firmware, cảm biến

| ID | Kiểm tra | Cách làm | Tiêu chí đạt |
|---|---|---|---|
| T-09 | Thạch anh 32.768 kHz | Build debug, log nguồn RTC slow clock khi khởi động; đo tần số gián tiếp (so RTC với thời gian thực trong 24 h) | khởi động với `RTC_CLK_SRC_EXT_CRYS`; sai số < 20 ppm sau khi chỉnh tụ C27/C28 (bắt đầu từ 18 pF; mỗi pF ký sinh sai lệch ~ vài ppm) |
| T-10 | Nạp firmware | USB-Serial/JTAG qua J1 (D+/D−/GND); bo chạy bằng nguồn bench 3.0 V vào TP1 (đã tháo pin) hoặc bằng pin | `idf.py flash monitor` chạy; `status` trên console |
| T-11 | Đo SHT40 | Lệnh `measure`, `status`; so với cảm biến tham chiếu trong hộp kín 30 min | đề xuất: lệch ≤ 0.4 °C và ≤ 3 %RH trước hiệu chỉnh (SHT40 điển hình ±0.2 °C, ±1.8 %RH); CRC lỗi = 0 trong 1000 lần đo |
| T-12 | Tự sưởi / cách nhiệt lưỡi cảm biến | So nhiệt độ báo cáo khi radio nghỉ và trong 10 min commissioning/poll dày | chênh < 0.2 °C |
| T-13 | Đo điện áp cell | Nguồn bench vào TP1 (đã tháo pin); so `status` (VBAT) với đồng hồ ở TP1 tại 3.0, 2.6, 2.2 V | sai số ≤ 30 mV sau hiệu chuẩn ADC |
| T-14 | Null khi lỗi cảm biến | Rút SDA (cắt tạm hoặc giữ SCL thấp) trong lúc chạy | sau 3 lần đọc lỗi, controller thấy MeasuredValue = null; khôi phục khi nối lại |
| T-15 | Nút | Nhấn ngắn, 3 lần trong 2 s, giữ 10 s rồi thả, giữ 60 s | đúng hành vi và LED theo `docs/architecture.md` §4.4; nhấn ngắn liên tục bị giới hạn 1 lần / 5 s |
| T-16 | Power guard | Cell yếu giả lập (nguồn 2.3 V nối tiếp 50 Ω vào TP1) | không vòng reset liên tục; vào ngủ sâu backoff; nút USER đánh thức |
| T-17 | Heap | Dòng `heap` của lệnh `status` sau khởi động, ngay sau commissioning, sau 24 h và sau 7 ngày | ghi lại số đo; "free" ở cùng trạng thái nghỉ không giảm dần giữa các lần đo (không rò bộ nhớ); "minimum since boot" là biên an toàn còn lại; không có reset do thiếu bộ nhớ |

## C. Matter / Thread

| ID | Kiểm tra | Tiêu chí đạt |
|---|---|---|
| T-20 | Commissioning BLE với chip-tool hoặc một hệ sinh thái cụ thể (ghi tên, phiên bản) | ghép thành công bằng CR2450 mới ở nhiệt độ phòng; ghi lại thời gian và dòng (T-33) |
| T-21 | Mở lại cửa sổ (nhấn 3 lần) và thêm fabric thứ hai | fabric cũ vẫn còn; fabric mới thêm được qua mạng |
| T-22 | Subscription và báo cáo | controller nhận nhiệt/ẩm khi thay đổi vượt deadband; Power Source đọc đúng (1 × CR2450, BatVoltage gần số đo ở TP1) |
| T-23 | Mất Border Router 30 min rồi bật lại | thiết bị tự gắn lại Thread, không factory reset, không mở BLE |
| T-24 | Factory reset | fabric, Thread, cấu hình app bị xóa; `fctry`/`esp_secure_cert` còn nguyên |
| T-25 | Tầm phủ RF | RSSI/LQI tại 5 m, 10 m qua tường; so với module dev kit cùng vị trí |

## D. Năng lượng (thay ƯỚC TÍNH bằng số đo)

Đo bằng máy đo dòng ở vị trí R21 (dòng tải 3V3) và ở R1 (dòng cell), USB rút ra (USB giữ chip thức có chủ đích). T-35 và T-37 nên làm **trước khi** làm nhiều bo: chúng quyết định Rev B có dùng được hay không.

| ID | Đại lượng | Ước tính hiện tại | Ghi kết quả |
|---|---|---|---|
| T-30 | Đáy light sleep giữa hai poll | 27 µA tại 3V3 | |
| T-31 | Điện tích một poll Thread (slow poll 15 s) | 0.25 mC | |
| T-32 | Điện tích một report + active mode | 1.42 mC | |
| T-33 | Dạng dòng khởi động (0–10 s) và commissioning (toàn bộ) | khởi động: 0.3 s × 22 mA, 0.1 s × 45 mA, 0.4 s × 15 mA; commissioning: 3 profile giả định | |
| T-34 | Dòng trung bình 24 h ở trạng thái "yên" | 51.5 µA (3V3) / 63–68 µA (cell) | |
| T-35 | Sụt áp cell và điện trở xung (ΔV/ΔI) trong xung TX và khi khởi động, CR2450 mới / đã xả 50 % / đã xả 80 % | ~0.6 × điện trở CR2032 (~7 Ω + phân cực khi mới); nếu gần CR2032 thì pin mới cũng không khởi động được | |
| T-36 | Như T-35 ở 0 °C và −10 °C | dự kiến RESET khi khởi động | |
| T-37 | Khởi động lại (nút RST) và commissioning với CR2450 đã xả ~50 % | dự kiến RESET (mô hình) | |
| T-38 | Điện dung hiệu dụng nút VIN ở 3 V (đo bằng xung dòng) | ~555 µF (85 µF MLCC + 470 µF) | |
| T-39 | Dòng rò C5 (470 µF điện phân) ở 3.0 V sau 1 h, 24 h, 7 ngày: đo riêng tụ trước khi hàn, hoặc so dòng vào TP1 (R21 tháo) có và không có C5 | 0–5 µA (không có số liệu ở 3 V) | |

Sau T-30…T-39: chạy lại `hardware/analysis/power_model.py` với số đo, cập nhật `docs/power_budget.md` và đánh giá lại mục "CHƯA ĐẠT".

## E. Môi trường và độ bền (sau khi các phần trên đạt)

| ID | Kiểm tra | Ghi chú |
|---|---|---|
| T-40 | Chạy liên tục 30 ngày, ghi dòng trung bình và số reset | |
| T-41 | Chu kỳ nhiệt 0…40 °C, độ ẩm 20…80 %RH | so với tham chiếu; holder ghi −25…+85 °C |
| T-42 | ESD tiếp xúc trên nút và holder | theo yêu cầu của vỏ hoàn chỉnh |

Chứng nhận (Matter, FCC/CE, an toàn pin) **không nằm trong phạm vi** và không được tuyên bố.
