# Kế hoạch bring-up và kiểm thử — TH-SENSOR-H2 Rev A

**Tất cả các mục dưới đây: CHƯA KIỂM THỬ** (chưa có bo). Khi làm, ghi kết quả, ngày, số serial bo và dụng cụ đo vào cột "Kết quả" của một bản sao tài liệu này; thay số ƯỚC TÍNH trong `docs/power_budget.md` bằng số đo.

Dụng cụ cần: nguồn bench có giới hạn dòng, đồng hồ vạn năng, máy đo dòng có dải µA và lấy mẫu nhanh (ví dụ Nordic PPK2, Joulescope hoặc tương đương), oscilloscope, cặp CR2032 mới cùng lô và một cặp đã xả, tủ lạnh/tủ nhiệt (0 °C và −10 °C), cảm biến tham chiếu nhiệt ẩm, một Thread Border Router + Matter controller (xem `docs/commissioning.md`).

Điểm đo (silkscreen ghi tên net, không ghi số TP): TP1 VBAT1, TP2 VBAT2, TP3/TP4 VIN1/VIN2, TP5/TP6 VOUT1/VOUT2, TP7 3V3_PWR, TP8 +3V3 ("3V3"), TP9/TP10 GND, TP11 EN; BOOT ở J1 chân 5. Link đo dòng: R1 (cell 1), R11 (cell 2), R21 (tải sau bộ chuyển đổi).

## A. Bo trần và đường nguồn (trước khi cấp cho module)

| ID | Kiểm tra | Cách làm | Tiêu chí đạt |
|---|---|---|---|
| T-01 | Ngắn mạch | Đo điện trở VBAT1, VBAT2, VIN1, VIN2, VOUT1, VOUT2, 3V3_PWR, +3V3 so với GND | > 10 kΩ (tụ đang nạp có thể cho số thấp lúc đầu) |
| T-02 | Khởi động bộ chuyển đổi | Tháo R21 (cách ly tải). Cấp 3.0 V, giới hạn 50 mA vào pad + của BT1 (nối TP9 làm GND) | VOUT1 (TP5) = 3.40 V ±2 %; 3V3_PWR (TP7) 3.07–3.40 V; dòng vào < 10 µA sau khi tụ nạp |
| T-03 | Ngược cực | Cấp −3.0 V (giới hạn 10 mA) vào BT1 | dòng < 1 µA; không nóng; VIN1 ≈ 0 V |
| T-04 | Sụt áp P-MOSFET | Tải 50 mA ở 3V3_PWR (R21 tháo, tải điện tử ở TP7), đo VBAT1−VIN1 | < 20 mV ở 2.9 V vào; ghi lại ở 1.8 V vào |
| T-05 | Dòng ngược vào cell | Cấp 3.2 V vào BT2, cấp 2.6 V vào BT1 qua ampe kế đặt ở vị trí R1 (tháo R1). Đo ở 25 °C và 60 °C | dòng chảy vào cell 1 ≤ 0.7 µA (Panasonic: tổng điện tích nạp vào coin cell trong đời sử dụng ≤ 3 % dung lượng; 225 mAh × 3 % / 1 năm ≈ 0.77 µA) |
| T-06 | Giới hạn dòng vào | Một nguồn 2.9 V nối tiếp 12 Ω (giả lập cell) vào BT1, tải xung 60 mA/5 ms ở TP7 | dòng vào trung bình không vượt ~100 mA; rail không sụt dưới 3.0 V với "cell" 12 Ω |
| T-07 | Supervisor | R21 tháo, U4 chưa lắp; cấp nguồn ngoài vào TP8 (+3V3) rồi hạ dần; đo nRST (pad R22 phía U3) và EN (TP11) | nRST xuống thấp tại 2.86–2.97 V (VIT− của TPS3839K33); lên lại sau 120–350 ms; EN theo sau qua RC 10 kΩ / 1 µF (τ ≈ 10 ms) |
| T-08 | Thứ tự hai cell | Cấp hai nguồn 3.0 V và 2.7 V vào BT1/BT2, tải 20 mA | cả hai cell đều cấp dòng theo tỷ lệ (ghi lại phân chia); không có dòng ngược |

## B. Module, firmware, cảm biến

| ID | Kiểm tra | Cách làm | Tiêu chí đạt |
|---|---|---|---|
| T-09 | Thạch anh 32.768 kHz | Build debug, log nguồn RTC slow clock khi khởi động; đo tần số gián tiếp (so RTC với thời gian thực trong 24 h) | khởi động với `RTC_CLK_SRC_EXT_CRYS`; sai số < 20 ppm sau khi chỉnh tụ C27/C28 (bắt đầu từ 18 pF; mỗi pF ký sinh sai lệch ~ vài ppm) |
| T-10 | Nạp firmware | USB-Serial/JTAG qua J1 (D+/D−/GND, cấp 3V3_DBG + hàn JP1, hoặc pin) | `idf.py flash monitor` chạy; `status` trên console |
| T-11 | Đo SHT40 | Lệnh `measure`, `status`; so với cảm biến tham chiếu trong hộp kín 30 min | đề xuất: lệch ≤ 0.4 °C và ≤ 3 %RH trước hiệu chỉnh (SHT40 điển hình ±0.2 °C, ±1.8 %RH); CRC lỗi = 0 trong 1000 lần đo |
| T-12 | Tự sưởi / cách nhiệt lưỡi cảm biến | So nhiệt độ báo cáo khi radio nghỉ và trong 10 min commissioning/poll dày | chênh < 0.2 °C |
| T-13 | Đo điện áp cell | So `status` (VBAT1/VBAT2) với đồng hồ ở 3.0, 2.6, 2.2 V | sai số ≤ 30 mV sau hiệu chuẩn ADC |
| T-14 | Null khi lỗi cảm biến | Rút SDA (cắt tạm hoặc giữ SCL thấp) trong lúc chạy | sau 3 lần đọc lỗi, controller thấy MeasuredValue = null; khôi phục khi nối lại |
| T-15 | Nút | Nhấn ngắn, 3 lần trong 2 s, giữ 10 s rồi thả, giữ 60 s | đúng hành vi và LED theo `docs/architecture.md` §4.4; nhấn ngắn liên tục bị giới hạn 1 lần / 5 s |
| T-16 | Power guard | Pin yếu (nguồn 2.3 V nối tiếp 50 Ω) | không vòng reset liên tục; vào ngủ sâu backoff; nút USER đánh thức |
| T-17 | Heap | Dòng `heap` của lệnh `status` sau khởi động, ngay sau commissioning, sau 24 h và sau 7 ngày | ghi lại số đo; "free" ở cùng trạng thái nghỉ không giảm dần giữa các lần đo (không rò bộ nhớ); "minimum since boot" là biên an toàn còn lại; không có reset do thiếu bộ nhớ |

## C. Matter / Thread

| ID | Kiểm tra | Tiêu chí đạt |
|---|---|---|
| T-20 | Commissioning BLE với chip-tool hoặc một hệ sinh thái cụ thể (ghi tên, phiên bản) | ghép thành công bằng pin mới; ghi lại thời gian và dòng (T-31) |
| T-21 | Mở lại cửa sổ (nhấn 3 lần) và thêm fabric thứ hai | fabric cũ vẫn còn; fabric mới thêm được qua mạng |
| T-22 | Subscription và báo cáo | controller nhận nhiệt/ẩm khi thay đổi vượt deadband; Power Source đọc đúng |
| T-23 | Mất Border Router 30 min rồi bật lại | thiết bị tự gắn lại Thread, không factory reset, không mở BLE |
| T-24 | Factory reset | fabric, Thread, cấu hình app bị xóa; `fctry`/`esp_secure_cert` còn nguyên |
| T-25 | Tầm phủ RF | RSSI/LQI tại 5 m, 10 m qua tường; so với module dev kit cùng vị trí |

## D. Năng lượng (thay ƯỚC TÍNH bằng số đo)

Đo bằng máy đo dòng ở vị trí R21 (dòng tải 3V3) và ở R1/R11 (dòng từng cell), USB rút ra (USB giữ chip thức có chủ đích).

| ID | Đại lượng | Ước tính hiện tại | Ghi kết quả |
|---|---|---|---|
| T-30 | Đáy light sleep giữa hai poll | 27 µA tại 3V3 | |
| T-31 | Điện tích một poll Thread (slow poll 15 s) | 0.25 mC | |
| T-32 | Điện tích một report + active mode | 1.42 mC | |
| T-33 | Dạng dòng khởi động (0–10 s) và commissioning (toàn bộ) | 3 profile giả định | |
| T-34 | Dòng trung bình 24 h ở trạng thái "yên" | 51.5 µA (3V3) / 65 µA (cell) | |
| T-35 | Sụt áp cell trong xung TX với cell mới / đã xả 50 % / đã xả 80 % | xem mô phỏng | |
| T-36 | Như T-35 ở 0 °C và −10 °C | dự kiến RESET khi khởi động | |
| T-37 | Một cell: poll, report, khởi động, commissioning | poll/report ổn, khởi động/commissioning RESET | |
| T-38 | Điện dung hiệu dụng mỗi nút VIN ở 3 V (đo bằng xung dòng) | ~85 µF | |

Sau T-30…T-38: chạy lại `hardware/analysis/power_model.py` với số đo, cập nhật `docs/power_budget.md` và đánh giá lại mục "CHƯA ĐẠT".

## E. Môi trường và độ bền (sau khi các phần trên đạt)

| ID | Kiểm tra | Ghi chú |
|---|---|---|
| T-40 | Chạy liên tục 30 ngày, ghi dòng trung bình và số reset | |
| T-41 | Chu kỳ nhiệt 0…40 °C, độ ẩm 20…80 %RH | so với tham chiếu |
| T-42 | ESD tiếp xúc trên nút và vỏ pin | theo yêu cầu của vỏ hoàn chỉnh |

Chứng nhận (Matter, FCC/CE, an toàn pin) **không nằm trong phạm vi** và không được tuyên bố.
