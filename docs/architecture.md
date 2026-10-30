# Kiến trúc hệ thống — TH-SENSOR-H2 Rev B

Nhãn trạng thái dùng trong toàn bộ tài liệu:

- **ĐÃ XÁC MINH**: kiểm bằng công cụ (build, ERC/DRC, unit test) hoặc đọc trực tiếp từ datasheet/tài liệu gốc.
- **ƯỚC TÍNH**: tính toán hoặc mô phỏng; chưa đo.
- **CHƯA KIỂM THỬ**: chưa có phần cứng, chưa chạy trên thiết bị thật.

Chưa có bo mạch nào được sản xuất. Mọi hành vi trên thiết bị thật là **CHƯA KIỂM THỬ**.

Rev B chạy bằng **một CR2450** trên bo 41.5 × 57.5 mm. Rev A (hai CR2032, bo 72 × 58 mm, mỗi cell một bộ chuyển đổi) được giữ trong lịch sử git; lý do đổi: `docs/decisions.md` D20.

## 1. Sơ đồ khối

```
 CR2450 (BT1) ── R1 0R ── Q1 AO3401A ── VIN ── U1 TPS63900 (3.3 V) ── VOUT ── R21 0R ──┬─ +3V3
 holder BS-24    (đo dòng)  (chống ngược)  │                              │      (đo dòng │
                                           C1 10 µF, C2/C3 2 × 100 µF,    C4 22 µF,     │  tải)
                                           C5 470 µF điện phân            C21/C22 2 × 100 µF
                                                                                        ├─ ESP32-H2-MINI-1-H4S (U4)
                                                                                        ├─ SHT40 (U5, trên lưỡi tách nhiệt)
                                                                                        ├─ TPS3839K33 (U3) → R22 → EN
                                                                                        └─ LED (GPIO22), nút USER/BOOT (GPIO9), nút RST (EN), TP6 (EN)

 VBAT ─ R31 470k ─┬─ R32 470k ─ Q3 2N7002 ─ GND     Q3 bật bằng GPIO12; VBAT_SENSE → ADC1_CH4 (GPIO5)
                  └─ C31 22 nF ─ GND
```

## 2. Đường nguồn (kiến trúc "S")

| Phần tử | Vai trò | Trạng thái |
|---|---|---|
| BT1 MYOUNG BS-24-B4AA016 | holder SMT CR2450, tiếp điểm mạ vàng; pad 1 = + (phải) | kích thước land pattern lấy từ bản vẽ MY-CP-0138 trong datasheet LCSC (ĐÃ XÁC MINH: đọc từ bản vẽ); khớp với linh kiện thật và cực tính CHƯA KIỂM THỬ |
| R1 (0R 0805) | Link đo dòng cell (tháo, nối ampe kế qua 2 pad) | ĐÃ XÁC MINH (sơ đồ, layout) |
| Q1 AO3401A (P-MOSFET) | Chống lắp ngược cell; D phía cell, S phía VIN, G nối GND | ĐÃ XÁC MINH (sơ đồ); hành vi CHƯA KIỂM THỬ |
| C1, C2, C3, C5 | tụ đệm đầu vào: 10 µF + 2 × 100 µF MLCC + 470 µF điện phân (~555 µF hiệu dụng, ƯỚC TÍNH) | ĐÃ XÁC MINH (sơ đồ); điện dung hiệu dụng và dòng rò CHƯA KIỂM THỬ (T-38, T-39) |
| U1 TPS63900 | SEL = GND ⇒ VO(1) = 3.3 V từ RCFG3 16.2 kΩ (bảng 7-3); RCFG1 0 Ω + RCFG2 10.5 kΩ đặt giới hạn dòng vào trung bình 100 mA (bảng 7-2; VO(2) 3.4 V của hàng này không được chọn); EN = VIN | ĐÃ XÁC MINH theo bảng 7-2/7-3 SLVSET3D |
| C4 22 µF, C21/C22 2 × 100 µF, R21 0R | tụ ra, tụ bulk của rail, link đo dòng tải | ĐÃ XÁC MINH (sơ đồ, layout) |
| U3 TPS3839K33 (2.93 V, 200 ms) → R22 → EN | Giữ ESP32-H2 ở reset khi rail < 2.93 V | ĐÃ XÁC MINH (datasheet SBVS193D) |

Rail ra: 3.3 V trực tiếp từ bộ chuyển đổi (không có diode đầu ra), trong dải 3.0–3.6 V của module.

Chống sạc ngược cell: trên bo không có nguồn nào khác ngoài cell (J1 không có chân nguồn, USB không cấp điện). Nếu rail bị cấp từ ngoài trong khi có pin, bộ chuyển đổi không có đường diode thân từ VOUT về VIN khi không đóng cắt (suy ra từ cấu trúc trong datasheet, **CHƯA KIỂM THỬ**, T-05). Quy trình: luôn tháo pin trước khi cấp nguồn bench.

**Kết luận năng lượng: CHƯA ĐẠT** mục tiêu chạy suốt vòng đời cell trong mọi điều kiện (khởi động lại và commissioning cần pin còn mới, ở nhiệt độ phòng). Xem `docs/power_budget.md` và `docs/limitations.md`.

## 3. Phần cứng khác

- **Module**: ESP32-H2-MINI-1-H4S (4 MB flash, anten PCB), đặt ở góc trên-trái, mép module cách mép bo 2.0 mm, cách mép trên 0.5 mm, có rãnh khoét bo 17.2 × 6.0 mm cạnh anten theo hình "Keepout Zone" của ESP32-H2 Hardware Design Guidelines (ĐÃ XÁC MINH so với hình vẽ HDG; hiệu năng RF CHƯA KIỂM THỬ).
- **Cảm biến**: SHT40-AD1B-R3 trên một "lưỡi" 8.7 × 12 mm ở góc trên-phải, tách khỏi bo bằng một rãnh 1 mm hình chữ L (đi tiếp mép phải của rãnh anten xuống dưới, rồi rẽ phải dưới lưỡi), chỉ nối qua cầu 3.4 mm ở mép phải; không đổ đồng, không via trên lưỡi; bốn đường SDA/SCL/VDD/GND đi qua cầu theo thứ tự chân để không phải bắt chéo; điện trở kéo lên R26/R27 nằm phía bo chính (ĐÃ XÁC MINH bằng DRC; hiệu quả cách nhiệt CHƯA KIỂM THỬ).
- **Đo điện áp cell**: một cầu chia 470k/470k từ cực + của holder (trước R1), đóng bằng 2N7002 phía thấp (GPIO12), tụ giữ 22 nF tại chân ADC, τ = 5.2 ms; firmware chờ 30 ms. Số đo là điện áp cell khi chip đang thức (có tải), không phải điện áp nghỉ.
- **Thạch anh 32.768 kHz** (Epson FC-135, CL 12.5 pF) cho RTC/BLE LP clock; tụ tải 18 pF là giá trị **ƯỚC TÍNH**, phải chỉnh ở bring-up (T-09).
- **Debug**: J1 (1×6 pad 2.54 mm, không lắp) dưới rãnh anten: TX, RX, D+, D−, BOOT, GND. **Không có chân nguồn**: bo chạy bằng pin, hoặc bằng nguồn bench vào TP1 (VBAT) sau khi đã tháo pin.
- **Nút**: SW1 USER/BOOT (GPIO9, strap), SW2 RST (EN).
- **Điểm đo** (pad 1.5 mm; silkscreen ghi tên net cạnh mỗi pad, số TP chỉ có trên bản vẽ lắp ráp): TP1 VBAT, TP2 VIN, TP3 VOUT, TP4 +3V3 (in "3V3"), TP5 GND, TP6 EN. BOOT (GPIO9) có ở J1 chân 5 và nút SW1 (in "USER/BOOT").
- **"VBAT1/VBAT2/VBAT_OR"** của yêu cầu gốc là cho hai cell. Với một cell: điện áp cell ở **TP1 VBAT**; nút sau P-MOSFET, chỗ hai cell sẽ gặp nhau nếu có, là **TP2 VIN**. Không có nút OR.

## 4. Firmware

Nền tảng (ĐÃ XÁC MINH bằng build): ESP-IDF v5.5.5, `espressif/esp_matter` 1.6.0~1, `espressif/button` 4.2.1, FreeRTOS, `i2c_master`, `esp_adc` (curve fitting), NVS, power management (auto light sleep). Không dùng Arduino/ESPHome/LVGL.

```
firmware/
  main/                 app_main.cpp (khởi động), app_controller.c (luồng điều khiển), Kconfig.projbuild
  components/
    sht40/              driver I2C + giao thức (CRC-8, giải mã, retry); không bật heater khi đo
    battery/            đo điện áp cell qua ADC1 (hiệu chuẩn curve fitting), khóa PM khi đo
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
| 0 | Root Node | Basic Information, General Commissioning, Network Commissioning (Thread), ICD Management, **Power Source** (Battery + Replaceable, 1 cell CR2450, Li-MnO2, 620 mAh) |
| 1 | Temperature Sensor | Temperature Measurement (−40.00…125.00 °C, Tolerance 0.20 °C) |
| 2 | Humidity Sensor | Relative Humidity Measurement (0…100.00 %, Tolerance 1.80 %) |

- Lỗi cảm biến (CRC sai, NACK, timeout): sau `APP_SENSOR_FAIL_THRESHOLD` (3) lần liên tiếp, MeasuredValue được đặt **null**; không bao giờ phát giá trị cũ như giá trị mới.
- Deadband phát giá trị: 0.10 °C, 1.00 %RH (cấu hình được). Báo cáo tới controller do subscription và ICD quyết định.
- Offset hiệu chỉnh nhiệt/ẩm lưu NVS, **chỉ ghi khi giá trị thay đổi**.
- Power Source: BatVoltage = điện áp cell khi chip thức (có tải), BatPercentRemaining suy từ điện áp và lọc trễ, BatChargeLevel Warning khi < 40 %, Critical khi < 20 %, cell < 2.6 V hoặc số đo dưới ngưỡng "có pin" (với một cell và không có nguồn khác, đó là lỗi mạch đo). Phần trăm chỉ là chỉ báo: theo mô hình, khả năng khởi động lại mất khi số này còn quanh 50 % (`docs/power_budget.md` mục 6).

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

Reset do supervisor (EN) làm mất RAM RTC, nên trạng thái lưu trong NVS: số lần khởi động "không ổn định" và điện áp cell lần cuối. Quy tắc (`app_logic/guard_policy.c`, có unit test):
- cell < `APP_BOOT_MIN_CELL_MV` (2400 mV) ⇒ ngủ sâu, thử lại theo backoff;
- nhiều lần reset trước khi chạy ổn định `APP_STABLE_AFTER_S` (600 s) ⇒ ngủ sâu theo backoff 300 s … 4 h;
- điện áp cell tăng ≥ 150 mV so với lần lỗi trước (thay pin) hoặc restart bằng phần mềm ⇒ xóa bộ đếm.
Nút USER đánh thức sớm. Hành vi trên phần cứng: CHƯA KIỂM THỬ.

### 4.6 Hai profile build

| Profile | Lệnh defaults | Khác biệt |
|---|---|---|
| battery | `sdkconfig.defaults;sdkconfig.defaults.battery` | log WARN, power guard bật |
| debug | `sdkconfig.defaults;sdkconfig.defaults.debug` | log INFO, power guard tắt (nguồn bench) |
| prod (lớp phủ; build ĐÃ XÁC MINH, chạy CHƯA KIỂM THỬ) | thêm `sdkconfig.defaults.prod` | dữ liệu factory thật (DAC/PAI/CD, passcode riêng từng máy) |

OTA: **không triển khai** (`CONFIG_ENABLE_OTA_REQUESTOR=n`); bảng phân vùng có sẵn hai slot A/B cho bản sau.

## 5. PCB

- 41.5 × 57.5 mm, 2 lớp, FR-4 1.6 mm, linh kiện một mặt; quy tắc JLCPCB tiêu chuẩn (track/space ≥ 0.127 mm, via 0.6/0.3 mm, mép đồng ≥ 0.3 mm). Thiết kế dùng track 0.25 mm (tín hiệu), 0.4–0.5 mm (nguồn), clearance 0.2 mm.
- Bố cục: module góc trên-trái, J1 và nút USER dưới rãnh anten, lưỡi SHT40 góc trên-phải, khối nguồn ở giữa, holder CR2450 dọc mép dưới, tụ điện phân 470 µF ở vai phải cạnh holder.
- B.Cu là mặt GND gần như liền; F.Cu đổ GND; via khâu GND lưới 3.5 mm và hàng dày dọc mép vùng anten.
- Khối nguồn bố trí theo ví dụ layout của datasheet TPS63900 (cuộn cảm cạnh IC, tụ vào một phía, tụ ra phía kia) và được đi dây tay, xoay 180° so với Rev A để đầu vào quay về phía cực + của holder; phần còn lại đi dây bằng router lưới tự viết (`hardware/scripts/router.py`).
- Dưới cell và thân holder trên F.Cu không có đồng/track/via (vỏ + của cell và thân holder sát mặt bo).
- Kết quả kiểm tra (ĐÃ XÁC MINH bằng kicad-cli 9.0.9): ERC 0/0, DRC 0 vi phạm, 0 pad chưa nối, schematic parity 0 lỗi — `hardware/reports/`.
