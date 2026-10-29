# TH-SENSOR-H2 — nhiệt ẩm kế Matter over Thread (ESP32-H2, 2 × CR2032)

Thiết kế firmware và phần cứng (Rev A) cho một nhiệt ẩm kế không màn hình:

- module **ESP32-H2-MINI-1-H4S** (4 MB flash, anten PCB), **Matter over Thread** (Sleepy End Device, ICD SIT), BLE chỉ dùng khi commissioning;
- cảm biến **SHT40-AD1B-R3** trên một "lưỡi" PCB tách nhiệt, đo mỗi 60 s;
- nguồn **2 × CR2032 song song, cách ly theo từng cell**: mỗi cell một P-MOSFET chống ngược cực và một bộ buck-boost TPS63900 (3.4 V), hai đầu ra OR qua Schottky;
- một nút USER, một nút RST, một LED; không màn hình.

Firmware dùng ESP-IDF thuần (ESP-Matter chính thức, FreeRTOS, `i2c_master`, ADC có hiệu chuẩn, NVS, power management). PCB là KiCad 9 gốc, 2 lớp, 72 × 58 mm, sinh hoàn toàn bằng script trong `hardware/scripts/`.

## Trạng thái — đọc trước

Nhãn dùng trong toàn bộ repo: **ĐÃ XÁC MINH** (kiểm bằng công cụ hoặc đọc từ tài liệu gốc), **ƯỚC TÍNH** (tính toán/mô phỏng), **CHƯA KIỂM THỬ** (chưa có phần cứng).

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Firmware build: `battery`, `debug`, `battery` + lớp phủ sản xuất `prod` | ĐÃ XÁC MINH (build sạch từ bản clone, ESP-IDF v5.5.5, 0 cảnh báo trong mã dự án) | `docs/reports/firmware_build.md` |
| Firmware chạy trên chip (mọi profile; prod còn cần dữ liệu factory riêng từng máy) | **CHƯA KIỂM THỬ** | `docs/test_plan.md` |
| Unit test logic thuần trên host | ĐÃ XÁC MINH: 40 test, 208 kiểm tra, 0 lỗi | `docs/reports/host_tests.txt` |
| ERC schematic | ĐÃ XÁC MINH: 0 lỗi, 0 cảnh báo | `hardware/reports/erc_report.txt` |
| DRC PCB + schematic parity | ĐÃ XÁC MINH: 0 vi phạm, 0 pad chưa nối, 0 lỗi parity | `hardware/reports/drc_report.txt` |
| Pin map firmware ↔ schematic | ĐÃ XÁC MINH | `tools/check_pinmap.py`, `docs/pinmap.md` |
| Gerber, drill, BOM, CPL (định dạng JLC) | ĐÃ XÁC MINH là sinh được từ board; **chưa gửi nhà máy** | `hardware/production/` |
| Năng lượng, tuổi thọ pin | ƯỚC TÍNH — **CHƯA ĐẠT** | `docs/power_budget.md` |
| Điện, RF, cảm biến, Matter, dòng ngủ trên bo thật | **CHƯA KIỂM THỬ** (chưa có bo nào được làm) | `docs/test_plan.md` |
| OTA | **không triển khai** (`CONFIG_ENABLE_OTA_REQUESTOR=n`) | |
| Chứng nhận (Matter, FCC/CE, an toàn pin) | **không tuyên bố** | |

Chưa có đơn đặt PCB hay linh kiện nào. Chưa đo dòng, chưa ghép Matter với controller nào.

## Cảnh báo chính

1. **Thiết kế nguồn CHƯA ĐẠT** (ƯỚC TÍNH): theo mô hình, commissioning bị reset khi pin đã dùng khoảng một nửa (25 °C) hoặc khi lạnh (≤ 0 °C ngay cả với pin mới); khởi động/report thất bại gần cuối đời pin, khi lạnh, hoặc khi chỉ còn một cell. Tuổi thọ ở 65 µA trung bình: **0.35–0.58 năm, không phải 1–2 năm**. Phương án dự phòng (chưa áp dụng): `docs/power_budget.md` mục 7. Thiết kế không tự đổi sang pin khác.
2. **ESP32-H2-MINI-1-H4S tồn kho JLC = 0** (tra ngày 2026-10-29) — chặn lắp ráp toàn bộ tại JLC; xem `docs/assembly.md`.
3. **Dữ liệu Matter thử nghiệm**: bản build mặc định dùng VID 0xFFF1 / PID 0x8000, passcode 20202021, discriminator 3840, DAC thử nghiệm — chỉ để phát triển, không bao giờ giao thiết bị như vậy.
4. **Không giả định** Apple Home, Google Home, Alexa, SmartThings, Home Assistant… sẽ chấp nhận firmware tự build này; thử lần đầu bằng `chip-tool` + OpenThread Border Router (`docs/commissioning.md`).
5. **Không bao giờ sao chép** toàn bộ flash/NVS, Thread dataset hay thông tin xác thực giữa các thiết bị.
6. **Chỉ dùng CR2032, không sạc** (in trên silkscreen: "CR2032 ONLY" / "NO CHARGE", cực + cạnh mỗi holder). Rev A không có điện trở bảo vệ nối tiếp theo khuyến nghị Panasonic — xem `docs/limitations.md` mục 3.

## Cấu trúc repo

```
firmware/                    dự án ESP-IDF (target esp32h2)
  main/                      app_main.cpp, app_controller.c, Kconfig.projbuild
  components/                sht40, battery, board, user_button, matter_bridge,
                             power_guard, app_config, maint_console, app_logic
  test/host/                 unit test chạy trên máy host
  sdkconfig.defaults(.battery|.debug|.prod), partitions.csv, dependencies.lock
hardware/
  scripts/                   design.py (BOM + netlist nguồn), gen_schematic.py, gen_pcb.py,
                             router.py, gen_project.py, gen_reports.py, gen_production.py
  kicad/                     th_sensor_h2.kicad_sch / .kicad_pcb / .kicad_pro, thư viện riêng (lib/)
  production/                Gerber + drill (zip), BOM/CPL JLC, bản vẽ lắp ráp, trở ngại sản xuất
  reports/                   ERC, DRC, routing log, tóm tắt
  renders/                   schematic.pdf, ảnh PCB (SVG, 3D PNG)
  analysis/                  power_model.py và kết quả mô phỏng
tools/                       check_pinmap.py, jlc_lookup.py
docs/                        tài liệu thiết kế (danh sách bên dưới), docs/reports/
```

## Firmware

Cần: ESP-IDF **v5.5.5** (đã dùng toolchain riscv32-esp-elf esp-14.2.0_20260121, CMake 3.28, Ninja 1.11). Component manager tự tải `espressif/esp_matter` 1.6.0~1, `espressif/button` 4.2.1 và các phụ thuộc theo `firmware/dependencies.lock`; không cần checkout ESP-Matter riêng.

```sh
. $HOME/esp/esp-idf-v5.5.5/export.sh        # đường dẫn tùy máy
cd firmware
P=battery                                    # hoặc: debug
idf.py -B build_$P -D SDKCONFIG=build_$P/sdkconfig \
       -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.$P" build
idf.py -B build_$P -D SDKCONFIG=build_$P/sdkconfig \
       -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.$P" -p /dev/ttyACM0 flash monitor
```

| Profile | Dùng khi | Khác biệt |
|---|---|---|
| `battery` | chạy bằng pin | log WARN, power guard bật |
| `debug` | bring-up bằng nguồn bench | log INFO, power guard tắt |
| `prod` (lớp phủ thêm sau `battery`) | sản xuất, cần dữ liệu factory riêng từng máy | build được; chạy CHƯA KIỂM THỬ — `docs/commissioning.md` mục 5 |

Nạp firmware qua USB-Serial/JTAG trên J1 (D+, D−, GND; header 1×7 không lắp sẵn). Bo phải có nguồn: pin, hoặc **tháo pin** rồi hàn JP1 và cấp 3.0–3.3 V vào J1 pin 6 (3V3_DBG). Vào chế độ download bằng tay: giữ USER (SW1, GPIO9) trong khi nhấn và thả RST (SW2). Trên thiết bị đã có dữ liệu factory, **không** chạy `idf.py erase-flash` (xóa luôn phân vùng `fctry` và `esp_secure_cert`).

### Nút và LED

| Thao tác nút USER | Hành động | LED |
|---|---|---|
| Nhấn ngắn | đo ngay (tối đa 1 lần / 5 s) | 1 nháy nếu đo được, 2 nháy dài nếu lỗi |
| Nhấn 3 lần trong 2 s | mở cửa sổ commissioning 180 s, **giữ nguyên các fabric** | 3 nháy |
| Giữ ≥ 10 s rồi thả | factory reset (fabric, Thread, cấu hình app; không xóa dữ liệu factory) | sáng liên tục khi đủ 10 s, 8 nháy khi chấp nhận |
| Giữ ≥ 60 s | coi là kẹt nút, không reset | tắt |

Chi tiết: `docs/architecture.md` mục 4.4.

### Console bảo trì (USB-Serial/JTAG)

`status` (cảm biến, pin, Matter/Thread, power guard, heap), `measure`, `battery`, `config` / `config set <key> <value>` (khóa: `temp_offset`, `rh_offset`, `meas_interval`, `bat_interval`, `temp_deadband`, `rh_deadband`, `led`, `tx_power`; chỉ ghi NVS khi giá trị đổi), `heater <20|110> <100|1000>` (xung heater để bảo trì; số đo lúc nóng không được phát; phép đo thường không bao giờ bật heater), `window`, `factory_reset confirm`, `reboot`. Khi USB đang nối, chip không vào light sleep (có chủ đích): rút USB khi đo dòng ngủ.

### Unit test trên host

```sh
cmake -S firmware/test/host -B build/host-tests
cmake --build build/host-tests
ctest --test-dir build/host-tests --output-on-failure
```

## Phần cứng

Cần: KiCad **9.0** có module Python `pcbnew` và `kicad-cli` (đã dùng 9.0.9), Python 3 với numpy. Thư viện chuẩn của KiCad đọc từ `/usr/share/kicad/`. Symbol, footprint, mô hình 3D của module lấy từ thư viện Espressif và đã được sao vào `hardware/kicad/lib/`; chỉ cần bản checkout thư viện đó (biến `ESPRESSIF_KICAD_LIB`) khi muốn làm mới các bản sao.

Tái tạo toàn bộ, theo thứ tự (chạy từ gốc repo):

```sh
python3 hardware/scripts/gen_schematic.py    # schematic, thư viện dự án, kiểm parity với design.py
python3 hardware/scripts/gen_pcb.py          # đặt linh kiện, đi dây (router.py), đổ đồng, silkscreen (~20 s)
python3 hardware/scripts/gen_project.py      # .kicad_pro: luật thiết kế JLC 2 lớp, net class
python3 hardware/scripts/gen_reports.py      # ERC, DRC + parity, PDF/SVG/3D
python3 hardware/scripts/gen_production.py   # Gerber, drill, BOM, CPL, bản vẽ lắp ráp
python3 tools/check_pinmap.py                # board_pins.h ↔ netlist
```

Chạy lại chuỗi trên cho ra schematic và board **giống từng byte**; chỉ dấu thời gian trong Gerber/drill/báo cáo/PDF/ZIP và ảnh render 3D thay đổi.

Điểm đo trên bo (silkscreen ghi tên net): VBAT1, VBAT2, VIN1/VIN2, VOUT1/VOUT2, 3V3_PWR (điểm OR hai nhánh), 3V3, GND × 2, EN; BOOT ở J1 chân 5. Link đo dòng: R1 (cell 1), R11 (cell 2), R21 (tải 3V3), đều là 0R 0805. Thứ tự bring-up: `docs/test_plan.md`.

Mô hình năng lượng: `python3 hardware/analysis/power_model.py --plots` (~5 phút). Tra lại tồn kho JLC trước khi đặt: `python3 tools/jlc_lookup.py --json <mã LCSC…>` (endpoint không chính thức của trang jlcpcb.com/parts).

## Tài liệu

| File | Nội dung |
|---|---|
| `docs/architecture.md` | sơ đồ khối, đường nguồn, firmware, data model Matter, ICD, nút/LED |
| `docs/pinmap.md` | bảng chân module ↔ net ↔ GPIO (sinh bằng `check_pinmap.py --markdown`), J1 |
| `docs/power_budget.md` | ngân sách dòng, tuổi thọ 25/50/100/200 µA, mô phỏng xung, tụ đệm, chế độ hỏng, phương án dự phòng |
| `docs/decisions.md` | các quyết định thiết kế và lý do (D1–D19) |
| `docs/commissioning.md` | ghép Matter, cửa sổ commissioning, factory reset, dữ liệu sản xuất |
| `docs/assembly.md` | file sản xuất, kiểm tra preview JLC, lắp tay, link đo dòng |
| `docs/test_plan.md` | kế hoạch bring-up và kiểm thử T-01…T-42 |
| `docs/limitations.md` | giới hạn và rủi ro đã biết |
| `docs/sources.md` | datasheet, tài liệu và phiên bản công cụ đã dùng |
| `docs/reports/` | báo cáo build firmware, kết quả unit test |
| `hardware/reports/` | ERC, DRC, routing log |

## Giấy phép

Chưa chọn giấy phép cho dự án (quyết định của chủ repo). Symbol, footprint và mô hình 3D ESP32-H2-MINI-1 trong `hardware/kicad/lib/` lấy từ thư viện KiCad của Espressif và theo giấy phép của thư viện đó: `hardware/kicad/lib/LICENSE-espressif-kicad-libraries.md`.
