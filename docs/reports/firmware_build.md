# Báo cáo build firmware — TH-SENSOR-H2 Rev B

Ngày: 2026-10-30. **Build: ĐÃ XÁC MINH. Chạy trên chip/bo thật: CHƯA KIỂM THỬ** (chưa nạp vào thiết bị nào).

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

40 test, 208 kiểm tra, 0 lỗi, chạy lại trên bản clone sạch của commit `359f772` (`docs/reports/host_tests.txt`; lệnh trong `README.md`). Đây là logic thuần C (giao thức SHT40/CRC, quy đổi Matter, chính sách báo cáo/null, giới hạn cấu hình, nhận dạng thao tác nút, mô hình pin, backoff, power guard) — không thay cho kiểm thử trên chip.

## 6. Chưa làm

- Chưa nạp firmware vào ESP32-H2 thật; chưa chạy với SHT40, ADC, nút, LED; chưa commissioning; chưa đo heap và dòng (`docs/test_plan.md`).
- OTA không bật (`CONFIG_ENABLE_OTA_REQUESTOR=n`); bảng phân vùng có sẵn hai slot A/B.
- Secure Boot V2, Flash Encryption, NVS encryption: tắt (`docs/limitations.md` mục 5).
- Build không tái lập từng byte: `CONFIG_APP_COMPILE_TIME_DATE=y`, `CONFIG_APP_REPRODUCIBLE_BUILD` tắt; ở Rev A, hai lần build battery của cùng mã nguồn (`f07d835`) cho file cùng kích thước nhưng khác 76 byte.
