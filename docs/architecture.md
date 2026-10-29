# Kiến trúc hệ thống — TH-SENSOR-H2 Rev A

Nhãn trạng thái dùng trong toàn bộ tài liệu:

- **ĐÃ XÁC MINH**: kiểm bằng công cụ (build, ERC/DRC, unit test) hoặc đọc trực tiếp từ datasheet/tài liệu gốc.
- **ƯỚC TÍNH**: tính toán hoặc mô phỏng; chưa đo.
- **CHƯA KIỂM THỬ**: chưa có phần cứng, chưa chạy trên thiết bị thật.

Chưa có bo mạch nào được sản xuất. Mọi hành vi trên thiết bị thật là **CHƯA KIỂM THỬ**.

## 1. Sơ đồ khối

```
 CR2032 #1 ── R1 0R ── Q1 AO3401A ── VIN1 ── U1 TPS63900 (3.4 V, 100 mA in) ── D1 B5819W ─┐
 (BT1)        (đo dòng)  (chống ngược cực)   C1/C2/C3                C4                     │
                                                                                            ├─ 3V3_PWR ── R21 0R ── +3V3
 CR2032 #2 ── R11 0R ── Q2 AO3401A ── VIN2 ── U2 TPS63900 (3.4 V, 100 mA in) ── D2 B5819W ─┘   C21/C22     (đo dòng tải)
 (BT2)                                         C11/C12/C13           C14                       2 x 100 uF
                                                                                                      │
   VBAT1 ─ 470k/470k + 22 nF ─ Q3 ─┐                                                                  ├─ ESP32-H2-MINI-1-H4S (U4)
   VBAT2 ─ 470k/470k + 22 nF ─ Q4 ─┴─ GPIO12 bật/tắt; ADC1_CH4 (GPIO5) / ADC1_CH3 (GPIO4)            ├─ SHT40 (U5, trên lưỡi tách nhiệt)
                                                                                                      ├─ TPS3839K33 (U3) → EN
   JP1 (hở) ── J1 pin 6 (3V3_DBG, nguồn ngoài khi debug)                                              └─ LED, nút USER (GPIO9), nút RST
```

## 2. Đường nguồn (topology "C")

Yêu cầu gốc: 2 × CR2032 mắc song song **có cách ly ngược theo từng cell**, không nối trực tiếp hai cell.

Rev A dùng **một bộ buck-boost TPS63900 cho mỗi cell**, ra chung một đường 3V3 qua Schottky:

| Phần tử | Vai trò | Trạng thái |
|---|---|---|
| R1 / R11 (0R 0805) | Link đo dòng từng cell (tháo, nối ampe kế qua 2 pad) | ĐÃ XÁC MINH (sơ đồ, layout) |
| Q1 / Q2 AO3401A (P-MOSFET) | Chống lắp ngược cell; D phía cell, S phía VIN, G nối GND | ĐÃ XÁC MINH (sơ đồ); hành vi CHƯA KIỂM THỬ |
| U1 / U2 TPS63900 | VO(2) = 3.4 V (SEL = EN = VIN; RCFG1 0 Ω, RCFG2 10.5 kΩ), giới hạn dòng vào trung bình 100 mA; RCFG3 16.2 kΩ (VO(1) = 3.3 V, không dùng) | ĐÃ XÁC MINH theo bảng 7-2/7-3 SLVSET3D |
| D1 / D2 B5819W | OR hai đầu ra; rào cản thứ hai chống dòng chảy ngược vào cell | ĐÃ XÁC MINH (sơ đồ) |
| C21/C22 2 × 100 µF, R21 0R | Tụ bulk của rail, link đo dòng tải | ĐÃ XÁC MINH (sơ đồ, layout) |
| U3 TPS3839K33 (2.93 V, 200 ms) → R22 → EN | Giữ ESP32-H2 ở reset khi rail < 2.93 V | ĐÃ XÁC MINH (datasheet SBVS193D) |

Lý do chọn và so sánh với các phương án khác (A2/A1/B/B0/C50): `docs/decisions.md`.
Rail ra: 3.4 V trừ sụt áp Schottky ⇒ khoảng **3.07–3.40 V** (ƯỚC TÍNH, mô hình diode), nằm trong dải 3.0–3.6 V của module.

Hai rào cản chống sạc ngược cell: (1) bản thân bộ chuyển đổi (không có đường diode thân từ VOUT về VIN khi không đóng cắt), (2) Schottky đầu ra. Dòng ngược tối đa trong mô phỏng: 0 µA cho topology C (ƯỚC TÍNH). Phải đo ở bring-up (`docs/test_plan.md`, T-05).

**Kết luận năng lượng: CHƯA ĐẠT** mục tiêu chạy suốt vòng đời cell trong mọi điều kiện. Xem `docs/power_budget.md` và `docs/limitations.md`.

## 3. Phần cứng khác

- **Module**: ESP32-H2-MINI-1-H4S (4 MB flash, anten PCB), đặt ở góc trên-trái, mép module cách mép bo 2.0 mm, cách mép trên 0.5 mm, có rãnh khoét bo 15.2 × 6 mm cạnh anten theo hình "Keepout Zone" của ESP32-H2 Hardware Design Guidelines (ĐÃ XÁC MINH so với hình vẽ HDG; hiệu năng RF CHƯA KIỂM THỬ).
- **Cảm biến**: SHT40-AD1B-R3 trên một "lưỡi" 11 × 13 mm tách khỏi bo bằng hai rãnh 1 mm, chỉ nối qua cầu 3.4 mm; không đổ đồng, không via trên lưỡi; bốn đường SDA/SCL/VDD/GND đi qua cầu theo thứ tự chân để không phải bắt chéo (ĐÃ XÁC MINH bằng DRC; hiệu quả cách nhiệt CHƯA KIỂM THỬ).
- **Đo điện áp cell**: mỗi cell một cầu chia 470k/470k được đóng bằng 2N7002 phía thấp (GPIO12), tụ giữ 22 nF tại chân ADC, τ = 5.2 ms; firmware chờ 30 ms. Cell trống đọc ~0 V.
- **Thạch anh 32.768 kHz** (Epson FC-135, CL 12.5 pF) cho RTC/BLE LP clock; tụ tải 18 pF là giá trị **ƯỚC TÍNH**, phải chỉnh ở bring-up (T-09).
- **Debug**: J1 (1×7, 2.54 mm, không lắp): TX, RX, D+, D−, BOOT, 3V3_DBG, GND. 3V3_DBG chỉ cấp vào rail khi hàn nối JP1.
- **Nút**: SW1 USER/BOOT (GPIO9, strap), SW2 RST (EN).
- **Điểm đo**: TP1 VBAT1, TP2 VBAT2, TP3/TP4 VIN1/VIN2, TP5/TP6 VOUT1/VOUT2, TP7 3V3_PWR (tương đương "VBAT_OR" trong yêu cầu, sau OR), TP8 +3V3, TP9/TP10 GND.

## 4. Firmware

Nền tảng (ĐÃ XÁC MINH bằng build): ESP-IDF v5.5.5, `espressif/esp_matter` 1.6.0~1, `espressif/button` 4.2.1, FreeRTOS, `i2c_master`, `esp_adc` (curve fitting), NVS, power management (auto light sleep). Không dùng Arduino/ESPHome/LVGL.

```
firmware/
  main/                 app_main.cpp (khởi động), app_controller.c (luồng điều khiển), Kconfig.projbuild
  components/
    sht40/              driver I2C + giao thức (CRC-8, giải mã, retry); không bật heater khi đo
    battery/            đo 2 cell qua ADC1 (hiệu chuẩn curve fitting), khóa PM khi đo
    board/              pin map (board_pins.h), LED, chân không dùng, bật/tắt cầu chia
    user_button/        espressif/button → nhận dạng thao tác
    matter_bridge/      data model esp_matter, ICD, cửa sổ commissioning, Power Source
    power_guard/        chống vòng reset do sụt áp (trạng thái trong NVS)
    app_config/         cấu hình người dùng trong NVS (chỉ ghi khi giá trị đổi)
    maint_console/      console bảo trì qua USB-Serial/JTAG
    app_logic/          logic thuần C, có unit test trên máy host
  test/host/            40 test, 208 kiểm tra (ĐÃ XÁC MINH: chạy trên host, 0 lỗi)
```

### 4.1 Luồng chạy

1. `app_main`: NVS → `power_guard_init` → đo pin lúc khởi động → `power_guard_check` (có thể ngủ sâu nếu cell quá yếu hoặc đang lặp reset) → board, cảm biến, nút, Matter → `app_controller_start`.
2. `app_controller` là một task duy nhất xử lý hàng đợi sự kiện: đo SHT40 mỗi `APP_MEASURE_INTERVAL_S` (mặc định 60 s), đo pin mỗi `APP_BATTERY_INTERVAL_S` (6 h), sự kiện nút, sự kiện Matter, lệnh console.
3. Giữa các lần làm việc chip ở **auto light sleep**; Thread là Sleepy End Device theo ICD SIT.

### 4.2 Data model Matter

| Endpoint | Device type | Cluster chính |
|---|---|---|
| 0 | Root Node | Basic Information, General Commissioning, Network Commissioning (Thread), ICD Management, **Power Source** (Battery + Replaceable, 2 cell, Li-MnO2) |
| 1 | Temperature Sensor | Temperature Measurement (−40.00…125.00 °C, Tolerance 0.20 °C) |
| 2 | Humidity Sensor | Relative Humidity Measurement (0…100.00 %, Tolerance 1.80 %) |

- Lỗi cảm biến (CRC sai, NACK, timeout): sau `APP_SENSOR_FAIL_THRESHOLD` (3) lần liên tiếp, MeasuredValue được đặt **null**; không bao giờ phát giá trị cũ như giá trị mới.
- Deadband phát giá trị: 0.10 °C, 1.00 %RH (cấu hình được). Báo cáo tới controller do subscription và ICD quyết định.
- Offset hiệu chỉnh nhiệt/ẩm lưu NVS, **chỉ ghi khi giá trị thay đổi**.
- Power Source: BatVoltage = cell đang gánh tải (cao hơn), BatPercentRemaining lọc trễ, BatChargeLevel Warning khi < 40 % hoặc thiếu một cell, Critical khi < 20 %, cell tốt nhất < 2.6 V hoặc không còn cell.

### 4.3 ICD (Intermittently Connected Device)

| Tham số | Giá trị | Ghi chú |
|---|---|---|
| Chế độ | SIT (Short Idle Time) | không cần controller hỗ trợ LIT/check-in |
| Slow poll | 15 s | ví dụ icd_app dùng 5 s; 15 s là mức tối đa của SIT |
| Fast poll | 500 ms | |
| Idle mode | 300 s | |
| Active mode | 1000 ms, threshold 1000 ms | |

Ảnh hưởng tới năng lượng: `docs/power_budget.md` (ƯỚC TÍNH).

### 4.4 Nút và LED

| Thao tác (nút USER) | Hành động | LED |
|---|---|---|
| Nhấn ngắn | Đo ngay (giới hạn 1 lần / 5 s) | 1 nháy 40 ms nếu đo được, 2 × 150 ms nếu lỗi |
| Nhấn 3 lần trong 2 s | Mở cửa sổ commissioning 180 s bằng `OpenBasicCommissioningWindow` (giữ nguyên fabric; nếu đã có fabric chỉ quảng bá trên mạng, chưa có thì BLE + mạng) | 3 × 80 ms khi mở |
| Giữ ≥ 10 s rồi thả | Factory reset (xóa fabric, Thread, KVS, cấu hình app; không xóa `fctry`/`esp_secure_cert`) | sáng liên tục khi đủ 10 s; 8 × 60 ms khi chấp nhận |
| Giữ ≥ 60 s | Coi là kẹt nút, hủy reset | tắt |

GPIO9 cũng là chân strap BOOT: giữ SW1 khi nhấn SW2 ⇒ vào chế độ download.

### 4.5 Bảo vệ khởi động (power guard)

Reset do supervisor (EN) làm mất RAM RTC, nên trạng thái lưu trong NVS: số lần khởi động "không ổn định" và điện áp cell tốt nhất lần cuối. Quy tắc (`app_logic/guard_policy.c`, có unit test):
- cell tốt nhất < `APP_BOOT_MIN_CELL_MV` (2400 mV) ⇒ ngủ sâu, thử lại theo backoff;
- nhiều lần reset trước khi chạy ổn định `APP_STABLE_AFTER_S` (600 s) ⇒ ngủ sâu theo backoff 300 s … 4 h;
- điện áp cell tăng ≥ 150 mV so với lần lỗi trước (thay pin) hoặc restart bằng phần mềm ⇒ xóa bộ đếm.
Nút USER đánh thức sớm. Hành vi trên phần cứng: CHƯA KIỂM THỬ.

### 4.6 Hai profile build

| Profile | Lệnh defaults | Khác biệt |
|---|---|---|
| battery | `sdkconfig.defaults;sdkconfig.defaults.battery` | log WARN, power guard bật |
| debug | `sdkconfig.defaults;sdkconfig.defaults.debug` | log INFO, power guard tắt (nguồn bench) |
| prod (lớp phủ, CHƯA KIỂM THỬ) | thêm `sdkconfig.defaults.prod` | dữ liệu factory thật (DAC/PAI/CD, passcode riêng từng máy) |

OTA: **không triển khai** (`CONFIG_ENABLE_OTA_REQUESTOR=n`); bảng phân vùng có sẵn hai slot A/B cho bản sau.

## 5. PCB

- 72 × 58 mm, 2 lớp, FR-4 1.6 mm, linh kiện một mặt; quy tắc JLCPCB tiêu chuẩn (track/space ≥ 0.127 mm, via 0.6/0.3 mm, mép đồng ≥ 0.3 mm). Thiết kế dùng track 0.25 mm (tín hiệu), 0.4–0.5 mm (nguồn), clearance 0.2 mm.
- B.Cu là mặt GND gần như liền; F.Cu đổ GND; via khâu GND lưới 3.5 mm và hàng dày dọc mép vùng anten.
- Khối nguồn của mỗi cell bố trí theo ví dụ layout của datasheet TPS63900 (cuộn cảm phía trên IC, tụ vào trái, tụ ra phải) và được đi dây tay; phần còn lại đi dây bằng router lưới tự viết (`hardware/scripts/router.py`).
- Dưới hai cell trên F.Cu không có đồng/track/via (vành vỏ + của CR2032 sát mặt bo).
- Kết quả kiểm tra (ĐÃ XÁC MINH bằng kicad-cli 9.0.9): ERC 0/0, DRC 0 vi phạm, 0 pad chưa nối, schematic parity 0 lỗi — `hardware/reports/`.
