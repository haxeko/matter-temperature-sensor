# Giới hạn đã biết và rủi ro — TH-SENSOR-H2 Rev A

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

Theo mô hình (ƯỚC TÍNH, `docs/power_budget.md`):
- commissioning bị reset khi pin đã dùng khoảng một nửa (25 °C), và ở 0 °C / −10 °C ngay cả với pin mới;
- khởi động/report thất bại khi pin gần cuối đời, khi lạnh, hoặc khi chỉ còn một cell;
- tuổi thọ ở 65 µA trung bình: 0.35–0.58 năm; **không đạt 1–2 năm**.

Phương án dự phòng (chưa áp dụng, cần quyết định của người dùng): `docs/power_budget.md` mục 7. Thiết kế không tự đổi sang AAA hay loại pin khác.

## 3. Bảo vệ cell sơ cấp

Panasonic khuyến nghị diode chặn ngược **và** điện trở bảo vệ nối tiếp (giới hạn dòng nạp bất thường; CR2032: 10 mA theo bảng UL trong Panasonic Lithium Handbook). Rev A dùng hai rào cản bán dẫn (bộ chuyển đổi + Schottky đầu ra) và **không có điện trở nối tiếp** (một điện trở đủ lớn để giới hạn dòng sẽ gây sụt áp không chấp nhận được với xung 60 mA). Mức tuân thủ UL/IEC chưa được đánh giá; cần xem lại nếu đưa sản phẩm đi chứng nhận. Dòng ngược khi bình thường phải được đo (T-05, giới hạn ≤ 0.7 µA).

## 4. Linh kiện và sản xuất

- ESP32-H2-MINI-1-H4S: JLC tồn kho 0 (2026-10-29) — chặn lắp ráp toàn bộ tại JLC.
- Góc xoay CPL chưa được đối chiếu với mô hình linh kiện của JLC: phải kiểm từng linh kiện có cực tính trong bản xem trước (`hardware/production/orientation_check.md`).
- Tụ tải thạch anh 32 kHz (18 pF) là ước tính; phải chỉnh theo T-09.
- Điện dung hiệu dụng của tụ MLCC 100 µF 6.3 V ở 3 V chưa được tra/đo (giả định ~85 µF tổng mỗi nút VIN).

## 5. Matter

- Bản build mặc định dùng dữ liệu thử nghiệm (VID 0xFFF1/PID 0x8000, passcode 20202021, DAC thử nghiệm): chỉ để phát triển.
- Lớp phủ sản xuất `sdkconfig.defaults.prod` build được (ĐÃ XÁC MINH) nhưng chạy **CHƯA KIỂM THỬ**; cần dữ liệu factory riêng cho từng máy và chứng nhận Matter (ngoài phạm vi).
- Chưa thử với bất kỳ hệ sinh thái thương mại nào; không giả định chúng chấp nhận firmware này.
- **OTA không được triển khai** (`CONFIG_ENABLE_OTA_REQUESTOR=n`). Cập nhật firmware chỉ qua USB/UART (J1).
- **Secure Boot V2, Flash Encryption và NVS encryption đều tắt** trong mọi profile (kể cả lớp phủ prod). Với thiết bị thật chứa DAC và passcode riêng, cần bật và kiểm thử chúng trước khi sản xuất; việc ghi eFuse **không đảo ngược được**, nên không bật thử trên bo duy nhất.
- Không có chứng nhận Matter, FCC, CE, an toàn pin nào được tuyên bố.

## 6. Cảm biến

- Hiệu quả cách nhiệt của lưỡi SHT40 và độ chính xác trên bo này chưa được đo (T-11, T-12).
- Heater chỉ chạy bằng lệnh bảo trì; không có quy trình tự động chống ngưng tụ.

## 7. Đo pin

- Phần trăm pin suy ra từ điện áp nghỉ theo hình dạng đường xả Panasonic (15 kΩ, 20 °C) — chỉ mang tính chỉ báo; phụ thuộc nhiệt độ và tải.
- Sai số ADC + dòng rò đầu vào trên cầu 235 kΩ Thevenin chưa được đo (T-13).

## 8. PCB

- Layout được sinh bằng script và router tự viết. Kết quả đạt DRC nhưng có vài đường chéo dài; vài đoạn nhảy B.Cu ngắn (trong đó có +3V3 và EN) cắt mặt GND dưới cạnh dưới module; 9 kết nối dùng via (`hardware/reports/routing_log.txt`).
- 20 ký hiệu linh kiện ở vùng dày đặc chỉ có trên lớp Fab (bản vẽ `assembly_top.pdf`), không có trên silkscreen. Test pad được ghi tên net thay cho số TP.
- Yêu cầu gốc nêu điểm "VBAT_OR"; topology C không có nút này (hai cell chỉ gặp nhau sau bộ chuyển đổi). Điểm OR là 3V3_PWR (TP7), điện áp từng cell ở TP1/TP2.
- Render 3D chỉ có mô hình 3D của module; các linh kiện khác hiện là footprint trần vì gói mô hình 3D của KiCad không có trong môi trường sinh file.
- Hiệu năng anten khi lắp trong vỏ và gần hai cell chưa được đo; HDG khuyến nghị ≥ 15 mm khoảng trống quanh anten bên trong vỏ.

## 9. Công cụ

- Kiểm tra DRC dùng vùng đổ đồng đã được KiCad tính khi chạy `gen_pcb.py`; kicad-cli 9.0.9 trong môi trường này không có tùy chọn `--refill-zones`.
- Tái tạo phần cứng cần KiCad 9 (pcbnew Python) với thư viện chuẩn; thư viện Espressif chỉ cần khi muốn làm mới bản sao trong `hardware/kicad/lib`.
