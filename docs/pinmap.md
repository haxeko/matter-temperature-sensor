# Pin map — ESP32-H2-MINI-1-H4S trên TH-SENSOR-H2 Rev B

Nguồn sự thật duy nhất cho firmware: `firmware/components/board/include/board_pins.h`. Phía phần cứng: `hardware/scripts/design.py` → schematic KiCad. Hai phía được kiểm chéo bằng:

```
python3 tools/check_pinmap.py            # thoát mã 1 nếu lệch
python3 tools/check_pinmap.py --markdown # in lại bảng dưới đây
```

Kết quả lần chạy cuối: `pin map OK: 13 defines, 6 unused GPIOs checked against the schematic` (**ĐÃ XÁC MINH** với netlist xuất từ schematic Rev B).

Ánh xạ pad module → GPIO lấy từ ESP32-H2-MINI-1 & MINI-1U Datasheet v1.6, bảng 3 "Pin Description"; kênh ADC từ cùng bảng.

## GPIO

| Module pad | GPIO | board_pins.h | Net |
|---|---|---|---|
| 5 | GPIO2 | `unused (input off, pull-down)` | - |
| 6 | GPIO3 | `unused (input off, pull-down)` | - |
| 9 | GPIO0 | `unused (input off, pull-down)` | - |
| 10 | GPIO1 | `unused (input off, pull-down)` | - |
| 12 | GPIO13 | `BOARD_GPIO_XTAL32K_P` | XTAL_32K_P |
| 13 | GPIO14 | `BOARD_GPIO_XTAL32K_N` | XTAL_32K_N |
| 16 | GPIO12 | `BOARD_GPIO_VBAT_MEAS_EN` | VBAT_MEAS_EN |
| 18 | GPIO4 | `unused (input off, pull-down)` | - |
| 19 | GPIO5 | `BOARD_GPIO_VBAT_SENSE` | VBAT_SENSE |
| 20 | GPIO10 | `BOARD_GPIO_I2C_SDA` | I2C_SDA |
| 21 | GPIO11 | `BOARD_GPIO_I2C_SCL` | I2C_SCL |
| 22 | GPIO8 | `BOARD_GPIO_STRAP8` | STRAP_GPIO8 |
| 23 | GPIO9 | `BOARD_GPIO_USER_BUTTON` | BTN_USER |
| 24 | GPIO22 | `BOARD_GPIO_LED` | LED |
| 25 | GPIO25 | `unused (input off, pull-down)` | - |
| 26 | GPIO26 | `BOARD_GPIO_USB_DM` | USB_DM |
| 27 | GPIO27 | `BOARD_GPIO_USB_DP` | USB_DP |
| 30 | GPIO23 | `BOARD_GPIO_UART0_RX` | U0RXD |
| 31 | GPIO24 | `BOARD_GPIO_UART0_TX` | U0TXD |

## Nguồn, EN và GND

| Pad module | Tên | Net | Ghi chú |
|---|---|---|---|
| 3 | 3V3 | +3V3 | C24 100 nF đặt sát trong dải 2 mm bên trái module |
| 15 | VBAT (tên chân của module) | +3V3 | nội bộ module nối 3V3 mặc định; nối thêm ở ngoài; không liên quan tới net VBAT của cell |
| 8 | EN | EN | R22 10 kΩ từ TPS3839 (nRST), C25 1 µF, nút RST (SW2), test pad TP6 |
| 1, 2, 11, 14, 36–53 | GND | GND | 3 × 3 ô pad 49 ở giữa có 4 via GND giữa các ô |
| 4, 7, 17, 28, 29, 32–35 | NC | — | không nối |

## Ghi chú

- **GPIO8, GPIO9, GPIO25 là chân strap** (ESP32-H2 datasheet v1.3 mục 3). GPIO9 = nút USER/BOOT (10 kΩ kéo lên): giữ khi reset ⇒ download mode. GPIO8 kéo lên 10 kΩ (cần mức cao để download mode hoạt động). GPIO25 không có điện trở kéo nội và chỉ có tác dụng strap khi eFuse `EFUSE_STRAP_JTAG_SEL_ENABLE` được đốt (mặc định không) — để hở, firmware tắt bộ đệm vào.
- Chân không dùng (GPIO0, 1, 2, 3, 4, 25): firmware cấu hình tắt input, bật pull-down (GPIO25 không có pull nội, chỉ tắt input). GPIO4 (ADC1_CH3) là chân đo cell thứ hai ở Rev A.
- Rev A đổi ba chân so với bản trước để dải 2 mm cạnh trái module (yêu cầu vị trí anten của Espressif) chỉ còn 3V3 và EN: VBAT_MEAS_EN GPIO0 → GPIO12, VBAT1_SENSE GPIO1/ADC1_CH0 → GPIO5/ADC1_CH4, LED GPIO12 → GPIO22 (`docs/decisions.md` D13). Rev B giữ GPIO5/ADC1_CH4 cho cell duy nhất (net VBAT_SENSE).
- I2C: SDA GPIO10, SCL GPIO11, 100 kHz, kéo lên 10 kΩ (R26/R27) đặt ở phía bo chính của cầu nối sang lưỡi cảm biến; SHT40 địa chỉ 0x44.
- USB D−/D+ (GPIO26/27) nối thẳng tới J1 pin 4/3, không có điện trở nối tiếp (R28/R29 22 Ω đã bỏ ngày 2026-11-05, `docs/decisions.md` D14). UART0 TX/RX (GPIO24/23) tới J1 pin 1/2.

## J1 (debug, không lắp, 1×6 pad 2.54 mm)

| Chân | Tín hiệu |
|---|---|
| 1 | U0TXD (GPIO24) |
| 2 | U0RXD (GPIO23) |
| 3 | USB D+ (GPIO27) |
| 4 | USB D− (GPIO26) |
| 5 | BOOT = BTN_USER (GPIO9) |
| 6 | GND |

J1 không có chân nguồn: bo chạy bằng pin, hoặc nguồn bench vào TP1 (VBAT) sau khi tháo pin. Cắm USB vào J1 không cấp điện cho bo.

## Biến thể chip rời (TH-SENSOR-H2C)

Cùng `board_pins.h` (firmware dùng chung). Số chân là chân của chip ESP32-H2 vỏ QFN32 theo bảng chân trong ESP32-H2 Series Datasheet v1.3; kiểm bằng:

```
python3 tools/check_pinmap.py --variant chip
```

Kết quả lần chạy cuối: `pin map OK (chip): 13 defines, 6 unused GPIOs checked against the chip schematic` (**ĐÃ XÁC MINH** với netlist xuất từ schematic H2C).

| Chip pin | GPIO | board_pins.h | Net |
|---|---|---|---|
| 3 | GPIO0 | `unused (input off, pull-down)` | - |
| 4 | GPIO1 | `unused (input off, pull-down)` | - |
| 5 | GPIO2 | `unused (input off, pull-down)` | - |
| 6 | GPIO3 | `unused (input off, pull-down)` | - |
| 7 | GPIO4 | `unused (input off, pull-down)` | - |
| 8 | GPIO5 | `BOARD_GPIO_VBAT_SENSE` | VBAT_SENSE |
| 10 | GPIO8 | `BOARD_GPIO_STRAP8` | STRAP_GPIO8 |
| 11 | GPIO9 | `BOARD_GPIO_USER_BUTTON` | BTN_USER |
| 12 | GPIO10 | `BOARD_GPIO_I2C_SDA` | I2C_SDA |
| 13 | GPIO11 | `BOARD_GPIO_I2C_SCL` | I2C_SCL |
| 14 | GPIO12 | `BOARD_GPIO_VBAT_MEAS_EN` | VBAT_MEAS_EN |
| 15 | GPIO13 | `BOARD_GPIO_XTAL32K_P` | XTAL_32K_P |
| 16 | GPIO14 | `BOARD_GPIO_XTAL32K_N` | XTAL_32K_N |
| 21 | GPIO22 | `BOARD_GPIO_LED` | LED |
| 22 | GPIO23 | `BOARD_GPIO_UART0_RX` | U0RXD |
| 23 | GPIO24 | `BOARD_GPIO_UART0_TX` | U0TXD |
| 24 | GPIO25 | `unused (input off, pull-down)` | - |
| 25 | GPIO26 | `BOARD_GPIO_USB_DM` | USB_DM |
| 26 | GPIO27 | `BOARD_GPIO_USB_DP` | USB_DP |

Chân nguồn và chân khác của chip (không phải GPIO): 1, 2, 27, 30, 31 VDD3P3; 9 VDDPST1; 18 VBAT; 19 VDDA_PMU; 20 VDDPST2 (đều +3V3); 17 CHIP_EN (EN); 28 XTAL_N, 29 XTAL_P (qua L3 24 nH); 32 ANT (LNA_IN); 33 pad đáy = GND. J1 của H2C là 2 × 3 (không lắp) với cùng thứ tự chân 1 TX, 2 RX, 3 D+, 4 D−, 5 BOOT, 6 GND.
