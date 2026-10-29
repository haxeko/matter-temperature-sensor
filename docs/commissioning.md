# Commissioning (ghép thiết bị vào mạng Matter) — TH-SENSOR-H2 Rev A

**Trạng thái: CHƯA KIỂM THỬ** trên phần cứng thật. Các lệnh và API dưới đây đã có trong firmware và build thành công (ĐÃ XÁC MINH ở mức build), nhưng chưa ghép với controller nào.

## 1. Cần có

- Một **Thread Border Router** hoạt động (ví dụ OpenThread Border Router trên Raspberry Pi với RCP 802.15.4) và một **Matter controller**.
- Với bản build phát triển (mục 2): một controller cho phép thiết bị dùng **test VID/PID và test DAC**. Cách chắc chắn nhất để thử lần đầu là `chip-tool` của dự án connectedhomeip cùng một OTBR.
- **Không giả định** rằng hub/ứng dụng thương mại (Apple Home, Google Home, Amazon Alexa, SmartThings, Home Assistant…) sẽ chấp nhận firmware tự build này. Nhiều hệ sinh thái chỉ nhận thiết bị đã chứng nhận, hoặc yêu cầu bật chế độ nhà phát triển và khai báo VID/PID thử nghiệm. Kết quả với từng hệ sinh thái phải được kiểm và ghi lại (T-20).
- **Pin mới.** Mô hình năng lượng dự đoán commissioning bị reset khi pin đã dùng khoảng một nửa, hoặc ở ≤ 10 °C (`docs/power_budget.md`, ƯỚC TÍNH). Có thể commission bằng nguồn bench: hàn JP1 và cấp 3.0–3.3 V vào J1 pin 6 (3V3_DBG), **tháo pin ra trước**.

## 2. Bản build phát triển (mặc định)

Không có lớp phủ `sdkconfig.defaults.prod`, firmware dùng dữ liệu thử nghiệm của SDK:

| Mục | Giá trị |
|---|---|
| VID / PID | 0xFFF1 / 0x8000 (test) |
| Passcode | 20202021 |
| Discriminator | 3840 |
| DAC | DAC thử nghiệm của SDK |

Mã QR và mã ghép tay được in ra log khi khởi động (build `debug`, mức log INFO): tìm các dòng `SetupQRCode` và `Manual pairing code`.

Ví dụ với chip-tool (Thread dataset lấy từ border router, dạng hex):

```
chip-tool pairing ble-thread 1 hex:<active-operational-dataset> 20202021 3840
chip-tool temperaturemeasurement read measured-value 1 1
chip-tool relativehumiditymeasurement read measured-value 1 2
chip-tool powersource read bat-voltage 1 0
```

**Không bao giờ bán/giao thiết bị dùng dữ liệu thử nghiệm này.**

## 3. Cửa sổ commissioning

| Tình huống | Hành vi firmware |
|---|---|
| Khởi động lần đầu, chưa có fabric | quảng bá BLE + DNS-SD, cửa sổ 180 s (`CONFIG_CHIP_DISCOVERY_TIMEOUT_SECS`) |
| Nhấn USER 3 lần trong 2 s | `OpenBasicCommissioningWindow(180 s)`; nếu đã có fabric chỉ quảng bá trên mạng (DNS-SD), nếu chưa có thì BLE + mạng. Các fabric hiện có **được giữ nguyên**. LED nháy 3 × 80 ms khi cửa sổ mở |
| Lệnh console `window` | như trên |
| Cửa sổ đang mở | nhấn 3 lần không mở thêm; LED vẫn báo đang mở |

Thêm thiết bị vào hệ sinh thái thứ hai (multi-admin): dùng chức năng "chia sẻ/cho phép ghép" của controller thứ nhất (cửa sổ enhanced do controller mở), hoặc nhấn 3 lần rồi dùng mã ghép của thiết bị.

BLE chỉ dùng cho commissioning và được giải phóng sau khi ghép xong (`CONFIG_USE_BLE_ONLY_FOR_COMMISSIONING`). Công suất BLE +3 dBm: commission khi điện thoại ở gần thiết bị.

## 4. Factory reset

Giữ nút USER ≥ 10 s (LED sáng liên tục) rồi **thả** ⇒ LED nháy 8 × 60 ms, xóa: các fabric, Thread dataset, KVS của Matter, cấu hình ứng dụng (offset, chu kỳ đo, LED, TX power). Không xóa phân vùng `fctry` và `esp_secure_cert` (dữ liệu nhà máy). Giữ ≥ 60 s bị coi là kẹt nút và không reset. Lệnh console: `factory_reset confirm`.

## 5. Sản xuất (CHƯA KIỂM THỬ)

Thêm lớp phủ `firmware/sdkconfig.defaults.prod` khi build (sau `sdkconfig.defaults;sdkconfig.defaults.battery`). Lớp phủ bật nhà cung cấp dữ liệu factory của ESP32 và DAC trong `esp_secure_cert`. Khi đó **mỗi thiết bị phải có dữ liệu riêng**, tạo bằng `esp-matter-mfg-tool`:

- passcode, discriminator, verifier (SPAKE2+) riêng cho từng máy; số serial; rotating device ID unique ID;
- DAC/PAI của nhà sản xuất có VID thật và Certification Declaration — cần thành viên CSA và chứng nhận Matter, **ngoài phạm vi dự án này**;
- nạp vào phân vùng `fctry` (0x3E0000) và `esp_secure_cert` (0xD000) của từng máy;
- Secure Boot V2 / Flash Encryption / NVS encryption hiện **tắt**; cần quyết định và kiểm thử trước khi sản xuất (ghi eFuse không đảo ngược được) — `docs/limitations.md` mục 5.

**Không bao giờ sao chép toàn bộ flash/NVS, Thread dataset hay thông tin xác thực từ máy này sang máy khác.** Mỗi thiết bị phải được commission riêng.

## 6. Khắc phục sự cố

| Triệu chứng | Kiểm tra |
|---|---|
| Điện thoại không thấy thiết bị qua BLE | cửa sổ đã đóng sau 180 s → nhấn 3 lần; thiết bị đã có fabric → chỉ quảng bá DNS-SD, hãy dùng controller đã ghép để chia sẻ |
| Ghép dừng ở bước Thread | border router, dataset đúng, khoảng cách tới border router |
| Thiết bị khởi động lại trong lúc ghép | pin yếu/lạnh (xem mục 1); thử pin mới hoặc nguồn bench |
| Giá trị nhiệt/ẩm là null | cảm biến lỗi ≥ 3 lần liên tiếp; xem `status` trên console |
| Sau khi mất border router thiết bị không báo cáo | firmware tự gắn lại Thread với backoff của OpenThread; không tự factory reset và không tự mở BLE |
