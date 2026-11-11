# Báo cáo build firmware — TH-SENSOR-H2 Rev B

Ngày: 2026-10-30; build lại ngày 2026-11-11 sau khi sửa firmware và thêm lớp `cr123a` (mục 7). **Build: ĐÃ XÁC MINH. Chạy trên chip/bo thật: CHƯA KIỂM THỬ** (chưa nạp vào thiết bị nào).

## 1. Cách kiểm

Bản clone mới của repo tại commit `359f772` (mã firmware Rev B, một CR2450; các commit sau chỉ đổi tài liệu), thư mục build mới, chưa có `managed_components/`: component manager tải lại 9 phụ thuộc theo `firmware/dependencies.lock`. Hash của cả 8 component tải về khớp với lock; trình quản lý chỉ thông báo có `espressif/cmake_utilities` 1.3.0 mới hơn và vẫn dùng 1.2.0 đã khóa (file lock không đổi). Mỗi cấu hình build trong thư mục riêng, lần lượt trên cùng một máy 4 nhân. Rev A (commit `742f2a1`) cũng đã build sạch cả ba cấu hình theo đúng cách này (lịch sử git của file này).

```sh
. /opt/esp/esp-idf-v5.5.5/export.sh
cd firmware
idf.py -B build_battery -D SDKCONFIG=build_battery/sdkconfig \
       -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.battery" build
idf.py -B build_debug -D SDKCONFIG=build_debug/sdkconfig \
       -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.debug" build
idf.py -B build_prod -D SDKCONFIG=build_prod/sdkconfig \
       -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.battery;sdkconfig.defaults.prod" build
# sau mỗi build: cùng tham số + "size"
```

## 2. Môi trường

| Thành phần | Phiên bản |
|---|---|
| ESP-IDF | v5.5.5 |
| Trình biên dịch | riscv32-esp-elf GCC 14.2.0 (bản Espressif esp-14.2.0_20260121) |
| CMake / Ninja | 3.28.3 / 1.11.1 (của hệ thống) |
| Python (môi trường IDF) | 3.13.17 |
| Target | esp32h2, flash 4 MB |

Phụ thuộc đã khóa (`dependencies.lock`; manifest khai báo đúng phiên bản bằng `==`):

| Component | Phiên bản |
|---|---|
| espressif/esp_matter | 1.6.0~1 |
| espressif/button | 4.2.1 |
| espressif/esp_secure_cert_mgr | 2.9.3 |
| espressif/esp_encrypted_img | 2.7.0 |
| espressif/esp_delta_ota | 1.1.4 |
| espressif/mdns | 1.14.1 |
| espressif/cjson | 1.7.19~2 |
| espressif/cmake_utilities | 1.2.0 |

## 3. Kết quả

| Cấu hình | Kết quả | Thời gian | `th_sensor.bin` | Trống trong slot app 0x1E0000 | Bootloader (trống) |
|---|---|---|---|---|---|
| battery | exit 0 | 612 s (gồm tải component) | 1 604 880 B (0x187D10) | 0x582F0 (18 %) | 0x4B60 (61 %) |
| debug | exit 0 | 505 s | 1 656 544 B (0x1946E0) | 0x4B920 (16 %) | 0x5590 (55 %) |
| battery + prod | exit 0 | 514 s | 1 618 672 B (0x18B2F0) | 0x54D10 (18 %) | 0x4B60 (61 %) |

Lớp phủ prod được kiểm là đã áp dụng trong `build_prod/sdkconfig`: `CONFIG_ENABLE_ESP32_FACTORY_DATA_PROVIDER=y`, `CONFIG_ENABLE_ESP32_DEVICE_INSTANCE_INFO_PROVIDER=y`, `CONFIG_CHIP_FACTORY_NAMESPACE_PARTITION_LABEL="fctry"`, `CONFIG_SEC_CERT_DAC_PROVIDER=y` (DAC thử nghiệm `CONFIG_EXAMPLE_DAC_PROVIDER` tắt), `CONFIG_ENABLE_ROTATING_DEVICE_ID=y`. Build được **không** có nghĩa là chạy được: firmware prod cần dữ liệu factory riêng của từng máy trong `fctry` và `esp_secure_cert` (`docs/commissioning.md` mục 5), chưa có máy nào được nạp.

### Bộ nhớ (`idf.py size`, byte)

| Vùng | battery | debug | battery + prod | Tổng |
|---|---|---|---|---|
| Flash code (.text + .rodata + …) | 1 494 016 | 1 545 828 | 1 507 820 | — |
| DIRAM dùng | 190 754 (73.94 %) | 190 642 (73.89 %) | 190 810 (73.96 %) | 258 000 |
| — .text (IRAM) | 99 170 | 98 918 | 99 170 | |
| — .bss | 80 088 | 80 128 | 80 152 | |
| — .data | 11 496 | 11 596 | 11 488 | |
| LP SRAM | 132 | 132 | 132 | 4 096 |
| Total image size | 1 604 086 | 1 655 746 | 1 617 878 | |

So với Rev A, ảnh firmware nhỏ hơn ~270 B (bỏ kênh ADC thứ hai).

DIRAM còn ~67 kB cho heap lúc khởi động; mức heap thực tế khi chạy Matter + BLE + Thread **chưa đo**: lệnh `status` in heap còn trống và mức thấp nhất từ lúc khởi động (`docs/test_plan.md`, T-17).

## 4. Cảnh báo

- Trình biên dịch, mã của dự án (`firmware/main`, `firmware/components`): **0 cảnh báo** ở cả ba cấu hình.
- Trình biên dịch, mã bên ngoài: 0 ở battery và debug; 1 ở prod, trong connectedhomeip của esp_matter (`src/platform/ESP32/nimble/BLEManagerImpl.cpp:1949`, bỏ qua giá trị trả về `CHIP_ERROR` có thuộc tính `nodiscard` của `PlatformMgr().ScheduleWork(...)`). Không sửa mã thư viện.
- Kconfig: 2 cảnh báo ở cả ba cấu hình, đều trong `espressif/esp_matter`:
  - `default on the choice symbol SEC_CERT_DAC_PROVIDER ... will have no effect, as defaults do not affect choice symbols`
  - `the choice symbol SEC_CERT_DAC_PROVIDER ... is defined with a prompt outside the choice`

  Ký hiệu này được định nghĩa hai lần trong esp_matter (`components/esp_matter/Kconfig:48` và `connectedhomeip/config/esp32/components/chip/Kconfig:903`). Lớp phủ prod đặt `CONFIG_SEC_CERT_DAC_PROVIDER=y` trực tiếp và sdkconfig kết quả xác nhận giá trị đó.

## 5. Unit test trên host

Lần 2026-10-30: 40 test, 208 kiểm tra, 0 lỗi, chạy lại trên bản clone sạch của commit `359f772`; lần 2026-11-11: 43 test, 264 kiểm tra, 0 lỗi (mục 7) (`docs/reports/host_tests.txt`; lệnh trong `README.md`). Đây là logic thuần C (giao thức SHT40/CRC, quy đổi Matter, chính sách báo cáo/null, giới hạn cấu hình, nhận dạng thao tác nút, mô hình pin, backoff, power guard) — không thay cho kiểm thử trên chip.

## 6. Chưa làm

- Chưa nạp firmware vào ESP32-H2 thật; chưa chạy với SHT40, ADC, nút, LED; chưa commissioning; chưa đo heap và dòng (`docs/test_plan.md`).
- OTA không bật (`CONFIG_ENABLE_OTA_REQUESTOR=n`); bảng phân vùng có sẵn hai slot A/B.
- Secure Boot V2, Flash Encryption, NVS encryption: tắt (`docs/limitations.md` mục 5).
- Build không tái lập từng byte: `CONFIG_APP_COMPILE_TIME_DATE=y`, `CONFIG_APP_REPRODUCIBLE_BUILD` tắt; ở Rev A, hai lần build battery của cùng mã nguồn (`f07d835`) cho file cùng kích thước nhưng khác 76 byte.

## 7. Build lại ngày 2026-11-11

Lý do: bốn sửa đổi sau bản đánh giá (`docs/decisions.md` D23) và lớp cấu hình `sdkconfig.defaults.cr123a` cho biến thể H2W-123 (D24). Các mục 1–6 mô tả lần build 2026-10-30 và được giữ làm hồ sơ.

**Khác với cách kiểm ở mục 1**: không phải bản clone mới. Build trong cây làm việc (commit `13c74d3` cộng các thay đổi firmware của commit chứa báo cáo này), dùng `managed_components/` đã tải từ trước (`dependencies.lock` không đổi). Trước khi build, `sdkconfig` trong bốn thư mục build đầu bị xóa để cấu hình được sinh lại từ các file defaults (một `sdkconfig` cũ giữ giá trị cũ khi mặc định trong Kconfig thay đổi); tổ hợp debug + cr123a build trong thư mục mới. Mỗi cấu hình biên dịch lại toàn bộ (2051–2094 bước), lần lượt trên cùng một máy. Cùng môi trường như mục 2.

```sh
# thêm so với mục 1
idf.py -B build_cr123a -D SDKCONFIG=build_cr123a/sdkconfig \
       -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.battery;sdkconfig.defaults.cr123a" build
idf.py -B build_debug_cr123a -D SDKCONFIG=build_debug_cr123a/sdkconfig \
       -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.debug;sdkconfig.defaults.cr123a" build
```

| Cấu hình | Kết quả | Thời gian | `th_sensor.bin` | Trống trong slot app 0x1E0000 | Bootloader (trống) |
|---|---|---|---|---|---|
| battery | exit 0 | 386 s | 1 606 816 B (0x1884A0) | 0x57B60 (18 %) | 0x4B60 (61 %) |
| battery + cr123a | exit 0 | 416 s | 1 606 816 B (0x1884A0) | 0x57B60 (18 %) | 0x4B60 (61 %) |
| debug | exit 0 | 378 s | 1 658 160 B (0x194D30) | 0x4B2D0 (16 %) | 0x5590 (55 %) |
| debug + cr123a | exit 0 | 380 s | 1 658 160 B (0x194D30) | 0x4B2D0 (16 %) | 0x5590 (55 %) |
| battery + prod | exit 0 | 376 s | 1 620 608 B (0x18BA80) | 0x54580 (18 %) | 0x4B60 (61 %) |

So với lần 2026-10-30: battery và prod lớn hơn 1 936 B, debug lớn hơn 1 616 B.

| Vùng (byte) | battery | battery + cr123a | debug | battery + prod |
|---|---|---|---|---|
| Flash code | 1 495 950 | 1 495 950 | 1 547 442 | 1 509 754 |
| DIRAM dùng (trên 258 000) | 190 778 (73.94 %) | 190 778 (73.94 %) | 190 666 (73.90 %) | 190 834 (73.97 %) |
| — .text (IRAM) | 99 170 | 99 170 | 98 918 | 99 170 |
| — .bss | 80 112 | 80 112 | 80 152 | 80 176 |
| — .data | 11 496 | 11 496 | 11 596 | 11 488 |
| LP SRAM (trên 4 096) | 132 | 132 | 132 | 132 |
| Total image size | 1 606 020 | 1 606 020 | 1 657 360 | 1 619 812 |

Bản debug + cr123a có số liệu bộ nhớ trùng với cột debug. Mỗi cặp có/không có lớp cr123a cùng kích thước nhưng **khác nội dung** (đã so bằng `cmp`): bản cr123a chứa chuỗi `CR17345` và `1x CR123A, buck-boost 3.3 V`, không còn `CR2450`. `build_cr123a/sdkconfig` xác nhận lớp phủ đã áp dụng: `CONFIG_APP_CELL_CR123A=y`, `CONFIG_APP_BAT_WARN_PCT=20`, `CONFIG_APP_BAT_CRIT_PCT=8`, `CONFIG_APP_BOOT_MIN_CELL_MV=2200` (bản debug + cr123a: cùng loại pin và ngưỡng, power guard tắt như mọi bản debug); ba bản CR2450 có `CONFIG_APP_CELL_CR2450=y`, 40 / 20 / 2400. Các bản có power guard đều có `CONFIG_APP_GUARD_FREE_BOOTS=2`, `CONFIG_APP_GUARD_FRESH_CELL_MV=3000`, `CONFIG_APP_GUARD_NEW_CELL_RISE_MV=50`. Các ký hiệu của lớp prod liệt kê ở mục 3 vẫn có trong `build_prod/sdkconfig`.

Cảnh báo: như mục 4 — mã của dự án 0 cảnh báo ở cả năm cấu hình; 1 cảnh báo trình biên dịch trong connectedhomeip ở prod (`BLEManagerImpl.cpp:1949`); 2 cảnh báo Kconfig của esp_matter ở cả năm.

Unit test trên host: **43 test, 264 kiểm tra, 0 lỗi** (`docs/reports/host_tests.txt`), gồm các test mới cho quy tắc power guard (lần reset sớm đầu tiên được bỏ qua, vòng lặp sụt áp, pin mới / pin cũ hồi áp / restart, pin yếu, không có số đo) và cho bảng CR123A.

**Chưa làm**: không bản nào trong năm bản được nạp vào chip. Bốn sửa đổi (power guard, khởi động lại để mở lại BLE, đo pin hai mẫu, factory reset dự phòng) chưa chạy trên phần cứng: quy tắc power guard và bảng pin có unit test trên host; việc khởi động lại để mở lại BLE, đo pin hai mẫu và factory reset dự phòng nằm trong mã gắn với SDK nên chỉ được kiểm bằng build; hành vi thật cần T-16…T-16e (`docs/test_plan.md`). Chưa build tổ hợp prod + cr123a.
