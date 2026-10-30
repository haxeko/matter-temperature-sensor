# Giới hạn đã biết và rủi ro — TH-SENSOR-H2 Rev B

Đọc tài liệu này trước khi đặt sản xuất hay dùng thiết bị.

## 1. Chưa có phần cứng thật

Không có bo nào được sản xuất, lắp ráp, cấp nguồn hay đo. Những gì đã được kiểm (ĐÃ XÁC MINH):
- firmware build sạch từ bản clone mới cho ESP32-H2: profile battery, debug và battery + lớp phủ prod (`docs/reports/firmware_build.md`);
- chuỗi script phần cứng tái tạo schematic và board giống từng byte;
- 40 unit test / 208 kiểm tra logic thuần trên máy host, 0 lỗi (`docs/reports/host_tests.txt`);
- ERC 0 lỗi 0 cảnh báo; DRC 0 vi phạm, 0 pad chưa nối, schematic parity 0 lỗi (`hardware/reports/`);
- pin map firmware ↔ schematic khớp (`tools/check_pinmap.py`).

Mọi hành vi điện, RF, cảm biến, Matter/Thread, tuổi thọ pin: **CHƯA KIỂM THỬ**.

## 2. Năng lượng: CHƯA ĐẠT

Theo mô hình (ƯỚC TÍNH, `docs/power_budget.md`), với một CR2450:
- commissioning chỉ ổn với pin mới ở nhiệt độ phòng (ở 10 °C sát giới hạn; ở 0 °C và −10 °C bị reset);
- **khởi động bị reset khi pin đã dùng khoảng một nửa**, hoặc ở ≤ 0 °C ngay cả với pin mới. Hệ quả: sau giữa đời, một lần reset bất kỳ (sụt áp, watchdog, nút RST, lỗi firmware) có thể làm thiết bị ngừng hoạt động tới khi thay pin;
- report hỏng khi pin tới trạng thái late (25 °C), hoặc giữa đời ở −10 °C;
- tuổi thọ ở ~64 µA trung bình: khoảng 0.55–0.77 năm; **không đạt 1–2 năm**;
- điện trở xung của CR2450 không có số liệu công bố: mô hình nhân điện trở CR2032 với 0.6 (tỉ lệ diện tích điện cực). Nếu thực tế gần CR2032 (× 1.0), ngay cả pin mới cũng không khởi động được theo mô hình — đây là rủi ro lớn nhất của Rev B, phải đo trước khi làm nhiều bo (T-35);
- dạng dòng khởi động là giả định (T-33).

Phương án dự phòng (chưa áp dụng, cần quyết định của người dùng): `docs/power_budget.md` mục 7. Thiết kế không tự đổi sang AAA hay loại pin khác.

## 3. Bảo vệ cell sơ cấp

Panasonic khuyến nghị diode chặn ngược **và** điện trở bảo vệ nối tiếp khi cell có thể bị nạp từ nguồn khác (Panasonic Lithium Handbook). Rev B không có nguồn nào khác trên bo: J1 không có chân nguồn, USB không cấp điện cho bo, không có Schottky hay điện trở nối tiếp. Rủi ro nạp ngược chỉ còn khi người dùng cấp nguồn bench **trong khi pin vẫn lắp** (tài liệu yêu cầu tháo pin trước): cấp vào TP1 hay VIN sẽ nạp thẳng vào cell (P-MOSFET đã mở dẫn theo cả hai chiều); cấp vào rail (VOUT/+3V3) thì chỉ còn bộ chuyển đổi chặn, vì nó không có đường dẫn ngược VOUT→VIN khi không đóng cắt (CHƯA KIỂM THỬ, T-05). Mức tuân thủ UL/IEC chưa được đánh giá; cần xem lại nếu đưa sản phẩm đi chứng nhận.

## 4. Linh kiện và sản xuất

- ESP32-H2-MINI-1-H4S: JLC tồn kho 0 (tra 2026-10-29 và 2026-10-30) — chặn lắp ráp toàn bộ tại JLC.
- Holder MYOUNG BS-24-B4AA016: footprint là footprint của dự án, vẽ theo bản vẽ MY-CP-0138 trong datasheet LCSC; **phải so với một holder thật** (kích thước pad, vị trí cực +) trước khi đặt PCB. Holder ghi dải nhiệt −25…+85 °C (LCSC); tồn kho JLC 660 khi tra.
- Tụ điện phân 470 µF: dòng rò ở 3 V chưa có số liệu (ngân sách 0–5 µA, T-39); điện dung giảm và ESR tăng khi lạnh (chưa đưa vào mô hình); tuổi thọ định mức 2000 h ở 105 °C.
- Góc xoay CPL chưa được đối chiếu với mô hình linh kiện của JLC: phải kiểm từng linh kiện có cực tính trong bản xem trước (`hardware/production/orientation_check.md`), nhất là holder và tụ điện phân.
- Tụ tải thạch anh 32 kHz (18 pF) là ước tính; phải chỉnh theo T-09.
- Điện dung hiệu dụng của tụ MLCC 100 µF 6.3 V ở 3 V chưa được tra/đo (giả định ~85 µF cho 10 µF + 2 × 100 µF).

## 5. Matter

- Bản build mặc định dùng dữ liệu thử nghiệm (VID 0xFFF1/PID 0x8000, passcode 20202021, DAC thử nghiệm): chỉ để phát triển.
- Lớp phủ sản xuất `sdkconfig.defaults.prod` build được (ĐÃ XÁC MINH) nhưng chạy **CHƯA KIỂM THỬ**; cần dữ liệu factory riêng cho từng máy và chứng nhận Matter (ngoài phạm vi).
- Chưa thử với bất kỳ hệ sinh thái thương mại nào; không giả định chúng chấp nhận firmware này.
- **OTA không được triển khai** (`CONFIG_ENABLE_OTA_REQUESTOR=n`). Cập nhật firmware chỉ qua USB/UART (J1).
- **Secure Boot V2, Flash Encryption và NVS encryption đều tắt** trong mọi profile (kể cả lớp phủ prod). Với thiết bị thật chứa DAC và passcode riêng, cần bật và kiểm thử chúng trước khi sản xuất; việc ghi eFuse **không đảo ngược được**, nên không bật thử trên bo duy nhất.
- Không có chứng nhận Matter, FCC, CE, an toàn pin nào được tuyên bố.

## 6. Cảm biến

- Hiệu quả cách nhiệt của lưỡi SHT40 và độ chính xác trên bo này chưa được đo (T-11, T-12). Lưỡi Rev B nhỏ hơn Rev A (8.7 × 12 mm so với 11 × 13 mm); SHT40 cách IC nguồn ~25 mm và mép module ~20 mm.
- Heater chỉ chạy bằng lệnh bảo trì; không có quy trình tự động chống ngưng tụ.

## 7. Đo pin

- Phần trăm pin suy ra từ điện áp theo hình dạng đường xả CR2032 của Panasonic (15 kΩ, 20 °C), dùng nguyên cho CR2450 với giả định cùng hóa học cho cùng dạng đường cong — chưa đối chiếu với đường CR2450. Chỉ mang tính chỉ báo; phụ thuộc nhiệt độ và tải.
- Điện áp đo khi chip đang thức, tức là có tải qua bộ chuyển đổi; theo mô hình, khả năng khởi động lại mất khi phần trăm còn quanh 50 % (trên ngưỡng Warning 40 %), nên BatChargeLevel không báo trước được giới hạn ở mục 2.
- Sai số ADC + dòng rò đầu vào trên cầu 235 kΩ Thevenin chưa được đo (T-13).

## 8. PCB

- Layout được sinh bằng script và router tự viết. Kết quả đạt DRC nhưng có vài đường chéo dài; một số đoạn đi trên B.Cu cắt mặt GND (+3V3, EN, VOUT, I2C_SDA và đường đo VBAT dài 32 mm qua 4 via); 10 kết nối dùng via (`hardware/reports/routing_log.txt`).
- 20 ký hiệu linh kiện chỉ có trên lớp Fab (bản vẽ `assembly_top.pdf`): 19 vì không đủ chỗ trên silkscreen, BT1 do chọn (holder đã có dấu +/− và dòng "CR2450 ONLY / NO CHARGE"). Test pad được ghi tên net thay cho số TP.
- Yêu cầu gốc nêu điểm "VBAT1/VBAT2/VBAT_OR" cho hai cell; Rev B một cell có VBAT (TP1) và VIN (TP2), không có nút OR.
- Render 3D chỉ có mô hình 3D của module; các linh kiện khác (kể cả holder) hiện là footprint trần vì gói mô hình 3D của KiCad không có trong môi trường sinh file.
- Hiệu năng anten khi lắp trong vỏ và gần cell chưa được đo; HDG khuyến nghị ≥ 15 mm khoảng trống quanh anten bên trong vỏ.

## 9. Công cụ

- Vùng đổ đồng được KiCad tính lại trong `gen_pcb.py` sau khi ghi file project cuối cùng, nên DRC kiểm đúng vùng đồng nằm trong file; kicad-cli 9.0.9 trong môi trường này không có tùy chọn `--refill-zones`.
- Tái tạo phần cứng cần KiCad 9 (pcbnew Python) với thư viện chuẩn; thư viện Espressif chỉ cần khi muốn làm mới bản sao trong `hardware/kicad/lib`.
