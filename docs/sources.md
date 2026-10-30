# Nguồn tài liệu

Phiên bản tài liệu là bản đã đọc khi thiết kế (2026-10). Đường dẫn của nhà sản xuất có thể đổi; tên và mã phiên bản là thứ cần đối chiếu.

## Espressif

| Tài liệu | Phiên bản | Dùng cho |
|---|---|---|
| ESP32-H2-MINI-1 & MINI-1U Datasheet — https://www.espressif.com/sites/default/files/documentation/esp32-h2-mini-1_mini-1u_datasheet_en.pdf | v1.6 | sơ đồ chân module (bảng 3), vùng keepout anten trên module, dòng TX/RX, kích thước |
| ESP32-H2 Series Datasheet — https://www.espressif.com/sites/default/files/documentation/esp32-h2_datasheet_en.pdf | v1.3 | chân strap (GPIO8/9/25), GPIO25 không có pull nội (mục 3.3), ADC1 |
| ESP32-H2 Hardware Design Guidelines — https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32h2/ | bản "latest" 2026-10 | vị trí module và vùng keepout anten (hình "Keepout Zone ... feed point on the left"), thạch anh, USB, UART |
| ESP-Matter `examples/icd_app` — https://github.com/espressif/esp-matter/tree/main/examples/icd_app | esp_matter 1.6.0~1 | cấu hình ICD SIT, số đo dòng ngủ/poll của Espressif |
| Espressif KiCad libraries — https://github.com/espressif/kicad-libraries | git dd76561812ab300351234ba6e0ec1295641796f0 | symbol, footprint, mô hình 3D ESP32-H2-MINI-1 (CC-BY-SA 4.0 với ngoại lệ cho thiết kế; bản sao + license trong `hardware/kicad/lib/`) |

## Texas Instruments

| Tài liệu | Phiên bản | Dùng cho |
|---|---|---|
| TPS63900 datasheet — https://www.ti.com/lit/ds/symlink/tps63900.pdf | SLVSET3D (10/2020) | chân, bảng cấu hình RCFG (7-2, 7-3), UVLO, giới hạn dòng vào, ví dụ layout (hình 10-1), land pattern DSK |
| TPS3839 datasheet — https://www.ti.com/lit/ds/symlink/tps3839.pdf | SBVS193D (07/2015) | ngưỡng K33 2.93 V, trễ 200 ms, 150 nA |
| SWRA349 "Coin cells and peak current draw" — https://www.ti.com/lit/an/swra349/swra349.pdf | — | điện trở xung CR2032 theo mức xả (hình 6, cơ sở cho CR2450 sau khi nhân tỉ lệ diện tích), công thức tụ đệm |

## Pin và holder

| Tài liệu | Phiên bản | Dùng cho |
|---|---|---|
| Panasonic CR2450 — https://energy.panasonic.com/na/business/products/lithium/coin-cr-standard/models/CR2450 (datasheet PDF `CR2450_Datasheet_EN.pdf` trên trang) | 2026 | **Rev B**: 3 V, 620 mAh, dòng liên tục 0.2 mA, Ø24.5 × 5.0 mm, 6.2 g, −30…+85 °C; đường "capacity vs load"; đường kính trong trên bản vẽ (tỉ lệ diện tích dùng trong mô hình) |
| Panasonic CR2032 — https://energy.panasonic.com/na/business/products/lithium/coin-cr-standard/models/CR2032 (datasheet PDF trên trang) | 2026 | 3 V, 225 mAh, dòng liên tục 0.2 mA, −30…+85 °C, đường điện áp theo tải và nhiệt độ (cơ sở của mô hình cell; Rev A) |
| Panasonic Lithium Handbook (trang tải: https://energy.panasonic.com/eu/business/downloads/material) | 2025 | diode chặn ngược + điện trở bảo vệ khi cell có thể bị nạp, tổng điện tích nạp ≤ 3 % dung lượng với coin cell |
| MYOUNG BS-24-B4AA016 — datasheet trên LCSC: https://www.lcsc.com/datasheet/lcsc_datasheet_2012181809_MYOUNG-BS-24-B4AA016_C964809.pdf | bản vẽ MY-CP-0138 (2018-05-30) | **Rev B**: holder SMT CR2450, kích thước thân, land pattern (footprint dự án), cực +; −25…+85 °C, tiếp điểm đồng phosphor mạ vàng (mô tả LCSC) |
| KNSCHA RVT 470 µF 6.3 V (RVT470UF6.3V67RV0038) — datasheet trên LCSC: https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2109301630_KNSCHA-RVT470UF6-3V67RV0038_C2901342.pdf | — | **Rev B**: tụ đệm C5, Ø6.3 × 7.7 mm, ±20 %, 2000 h ở 105 °C, dòng rò ≤ 0.01 CV hoặc 3 µA sau 2 phút ở điện áp định mức |
| Keystone 1060 (catalog coin cell holders) | catalog M65 | holder CR2032 của Rev A (không còn dùng) |

## Sensirion

| Tài liệu | Phiên bản | Dùng cho |
|---|---|---|
| SHT4x datasheet — trang sản phẩm https://sensirion.com/products/catalog/SHT40 | Version 7.3 (06/2026) | độ chính xác điển hình ±0.2 °C / ±1.8 %RH, dòng 0.4 µA trung bình / 80 nA idle, nhiệt trở (mục 5.5), lệnh heater, tham chiếu "Handling Instructions SHT" |

## Linh kiện khác (datasheet qua LCSC/nhà sản xuất)

AO3401A (Alpha & Omega, Vgs(th) −0.5/−0.9/−1.3 V), 2N7002 (JSCJ), Murata DFE201612E-2R2M, Epson FC-135 32.768 kHz (CL 12.5 pF), XKB TS-1187A. B5819W (JSCJ) và RB521S30T1G (onsemi rev. 9) chỉ còn trong mô hình (các kiến trúc Rev A).

## Nguồn cung

- JLCPCB parts search (công cụ `tools/jlc_lookup.py`, endpoint của trang jlcpcb.com/parts, không phải API công bố chính thức) — ảnh chụp dữ liệu 2026-10-30 06:47 UTC trong `hardware/production/jlc_parts_snapshot.jsonl` (lần tra trước: 2026-10-29 08:55 UTC, Rev A).

## Công cụ đã dùng

| Công cụ | Phiên bản |
|---|---|
| ESP-IDF | v5.5.5 |
| espressif/esp_matter | 1.6.0~1 |
| espressif/button | 4.2.1 |
| KiCad (kicad-cli, pcbnew Python) | 9.0.9 |
| Python | 3.13; numpy cho router; mô hình năng lượng chỉ dùng thư viện chuẩn (matplotlib khi chạy `--plots`) |
