# TH-SENSOR-H2C Rev A — biến thể dùng chip ESP32-H2 rời

Biến thể của TH-SENSOR-H2 Rev B trong đó module ESP32-H2-MINI-1-H4S được thay bằng **chip ESP32-H2FH4S** (QFN32 4 × 4 mm, bước chân 0.4 mm, 4 MB flash trong vỏ), thạch anh 32 MHz, mạng phối hợp RF và **ăng-ten in trên PCB** (inverted-F theo TI DN007). Mọi phần khác giữ như Rev B: cùng kích thước bo 41.5 × 57.5 mm, cùng đường nguồn (1 × CR2450, AO3401A, TPS63900 3.3 V, tụ đệm), cùng SHT40 trên lưỡi tách nhiệt, cùng nút, LED, cầu đo pin, cùng **firmware** (mọi GPIO giữ chức năng). Rev B (module) không thay đổi.

Lựa chọn của người dùng ngày 2026-11-06: ăng-ten PCB, PCB 4 lớp, linh kiện phối hợp RF cỡ 0201, và "không có máy phân tích mạng (VNA), vẫn làm". Vì vậy mọi thứ liên quan RF trong tài liệu này là **CHƯA KIỂM THỬ** và giá trị linh kiện RF chỉ là **giá trị khởi đầu**, phải chỉnh bằng VNA trên bo thật.

## 1. Trạng thái

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Schematic: ERC | ĐÃ XÁC MINH: 0 lỗi, 0 cảnh báo | `hardware/chip/reports/erc_report.txt` |
| PCB: DRC + schematic parity | ĐÃ XÁC MINH: 0 vi phạm, 0 pad chưa nối, 0 lỗi parity (mọi mức) | `hardware/chip/reports/drc_report.txt` |
| Pin map firmware ↔ chip | ĐÃ XÁC MINH | `python3 tools/check_pinmap.py --variant chip` |
| Gerber 4 lớp, drill, BOM, CPL | ĐÃ XÁC MINH là sinh được; **chưa gửi nhà máy** | `hardware/chip/production/` |
| Tái tạo giống từng byte (schematic, board, project, thư viện) | ĐÃ XÁC MINH | chạy lại chuỗi ở mục 11 |
| Trở kháng đường RF, stub HDG, cặp USB | ƯỚC TÍNH (công thức Hammerstad–Jensen, chưa chạy máy tính trở kháng của JLC) | mục 6, 7 |
| Ăng-ten, phối hợp RF, công suất phát, tầm phủ | **CHƯA KIỂM THỬ** — chưa đo, chưa mô phỏng | mục 5, 10 |
| Tần số thạch anh 32 MHz (±10 ppm), tụ tải | **CHƯA KIỂM THỬ** | mục 10 |
| ESP32-H2FH4S tại JLC | **tồn kho 0** (tra 2026-11-06) — chặn lắp ráp toàn bộ | `hardware/chip/production/manufacturing_blockers.md` |

Không có bo nào được đặt, làm hay đo. Không tuyên bố chứng nhận nào (Matter, FCC/CE, …); bản chip rời cũng không thừa hưởng chứng nhận RF của module (datasheet module ghi "RF certification: See certificates").

## 2. Khác biệt so với Rev B (module)

| | Rev B (module) | H2C Rev A (chip rời) |
|---|---|---|
| Radio | ESP32-H2-MINI-1-H4S (anten, thạch anh, phối hợp RF có sẵn) | ESP32-H2FH4S QFN32 + Y2 32 MHz + L3 24 nH + 5 vị trí phối hợp RF 0201 + ăng-ten PCB |
| Ăng-ten | anten PCB của module, rãnh khoét bo 16.2 × 6 mm | IFA TI DN007 (vẽ đối xứng gương) dọc mép trên, 25.6 × 7.5 mm, không có đồng ở mọi lớp trong vùng 0…31.8 × 0…7.52 mm |
| Lớp | 2 lớp 1.6 mm | 4 lớp 1.6 mm, stack-up JLC04161H-7628, có kiểm soát trở kháng |
| Via | 0.6 / 0.3 mm | 0.45 / 0.2 mm (127 via) và 0.6 / 0.3 mm (11 via, đường nguồn) |
| Tụ decoupling của radio | C23 10 µF, C24 100 nF | C40…C48 (9 tụ, theo sơ đồ tham chiếu HDG) |
| J1 debug | 1 × 6, ngay dưới rãnh anten | 2 × 3 (không lắp), dưới chip, xa ăng-ten nhất có thể; chân như cũ: 1 TX, 2 RX, 3 D+, 4 D−, 5 BOOT, 6 GND |
| Số linh kiện trong `design.py` | 50 | 68 |
| Dòng BOM / linh kiện gắn máy | 28 / 41 | 36 / 57 |
| Hàn tay | được với mỏ hàn trừ U1, U5, module | **không** hàn mỏ được: QFN 0.4 mm có pad tản nhiệt và 4 linh kiện 0201 cần stencil + reflow/khí nóng |
| File | `hardware/kicad`, `hardware/production`, … | `hardware/chip/kicad`, `hardware/chip/production`, … |
| Firmware | — | **giống hệt** (không cần build riêng) |

## 3. Linh kiện mới

Mã LCSC, tình trạng Basic/Extended và tồn kho: ảnh chụp từ trang linh kiện JLC ngày 2026-11-06 (`hardware/chip/production/jlc_parts_snapshot.jsonl`), phải tra lại trước khi đặt.

| Ref | Linh kiện | LCSC | JLC | Ghi chú |
|---|---|---|---|---|
| U4 | Espressif ESP32-H2FH4S | C50392664 | Extended, **tồn kho 0** | mã đặt hàng trong datasheet ESP32-H2 v1.3. JLC còn ESP32-H2FH4 (C22470214, có hàng khi tra) — mã đặt hàng cũ hơn: phải đối chiếu revision chip trong datasheet trước khi dùng thay; **chưa làm** |
| Y2 | YXC X322532MLB4SI, 32 MHz, 3225 4 chân | C5210649 | Extended | HDG bắt buộc ±10 ppm. "CL 9 pF, ±10 ppm, 40 Ω" là theo mô tả trên trang LCSC, chưa đối chiếu datasheet YXC |
| L3 | Murata LQW18AN24NG00D 24 nH 2 % 0603 | C162644 | Extended | linh kiện nối tiếp trên XTAL_P, HDG: "ban đầu dùng cuộn cảm 24 nH" |
| C49, C50 | 12 pF C0G 0603 | C38523 | Basic | tụ tải khởi đầu: 12 × 12 / 24 + ~3 pF ký sinh (ƯỚC TÍNH) = 9 pF |
| R40 | 499 Ω 0603 | C23065 | Extended | nối tiếp U0TXD (HDG khuyến nghị) |
| C40…C48 | 10 µF, 1 µF, 100 nF, 10 nF 0603 | như Rev B | Basic | xem mục 4 |
| C51, C52 | Murata GRM0335C1H1R5BA01D 1.5 pF 0201 | C161414 | Extended | giá trị khởi đầu, trong khoảng HDG 1.2…1.8 pF |
| L4 | Murata LQP03TN2N4B02D 2.4 nH 0201 | C98042 | Extended | giá trị khởi đầu, trong khoảng HDG 2.0…3.0 nH |
| R41 | 0 Ω 0201 | C473473 | Extended | vị trí nối tiếp phía ăng-ten, để 0 Ω tới khi chỉnh |
| L5 | — | — | không lắp | vị trí song song phía ăng-ten, để trống tới khi chỉnh |
| AE1 | ăng-ten PCB | — | không có trong BOM | chỉ là đồng trên bo |

## 4. Đối chiếu ESP32-H2 Hardware Design Guidelines v1.6

Nguồn: HDG v1.6 (2025-06-05), các chương "Schematic Checklist" và "PCB Layout Design" (địa chỉ ở mục 12). ✓ = theo đúng; ≈ = theo một phần; ✗ = lệch có chủ đích hoặc chưa làm.

| HDG | Thiết kế này | |
|---|---|---|
| Nguồn 3.3 V, dòng ra ≥ 350 mA | TPS63900 từ một CR2450, giới hạn dòng vào 100 mA — như Rev B, xem `docs/power_budget.md` | ✗ |
| 10 µF tại lối vào nguồn; chân 1/2 (VDD3P3): 10 µF + 1 µF + 0.1 µF; chân 30/31: 10 nF; chân 27: 0.1 µF + 1 µF; chân 20, 19, 9: 0.1 µF | C42/C41/C40 ở chân 1/2, C43 ở 30/31, C44/C45 ở 27, C47 ở 18/19, C46 ở 20, C48 ở 9; lối vào là R21 với C21/C22 100 µF phía trước | ≈ (xem dòng dưới) |
| tụ đặt sát chân, có via GND sát pad GND của tụ | có; riêng **pad của C47 nhận cả chân 18, 19 và 20**, C46 nằm cạnh C47 (đường ~2 mm) chứ không riêng ở chân 20 — vì EN (chân 17) và các tín hiệu chân 21…23 phải đi ra cùng phía | ≈ |
| VBAT (chân 18) | nối thẳng +3V3 (vị trí R2 = 0 Ω của HDG bỏ đi) | ✓ |
| CHIP_EN: RC 10 kΩ / 1 µF; nguồn yếu dùng mạch giám sát ~3.0 V | R22 10 kΩ + C25 1 µF, TPS3839K33 2.93 V | ✓ |
| thạch anh 32 MHz ±10 ppm, cuộn cảm nối tiếp 24 nH trên XTAL_P, chỉnh tụ tải | Y2, L3, C49/C50 khởi đầu; chỉnh ở C-01 | ✓ (chưa chỉnh) |
| U0TXD nối tiếp 499 Ω, gần chip, xa thạch anh | R40 cách chân 23 ~2 mm, cách Y2 ~11 mm | ✓ |
| USB: chừa vị trí điện trở nối tiếp (22/33 Ω) và tụ xuống GND; vi sai 90 Ω ±10 % | không chừa (cùng lựa chọn "nối thẳng D+/D−" của Rev B); cặp 0.2 mm, khe 0.15 mm sau khi ra khỏi chân ≈ 90 Ω (ƯỚC TÍNH), dài 13–17 mm, D+ luồn giữa hai cột chân J1 | ≈ |
| ADC: tụ lọc 0.1 µF tại chân | C31 22 nF như Rev B (cầu 470 k/470 k, thời gian ổn định 30 ms) | ✗ (giữ như Rev B) |
| diode ESD ở lối vào nguồn | không có (nguồn là pin trong máy) | ✗ (như Rev B) |
| GPIO9 kéo lên, không tụ lớn; GPIO8 kéo lên cho download | R23, R24 10 kΩ | ✓ |
| RF: CLC (ưu tiên CLCCL), linh kiện 0201, xếp zigzag | C51 / L4 / C52 / R41 / L5, C51 và C52 ở hai phía đường RF | ✓ |
| stub trên pad GND của tụ song song đầu tiên phía chip: dài 15 mil, 100 Ω ±10 %, tham chiếu lớp 3, xóa đồng lớp 2 dưới stub | stub 0.5 × 0.381 mm từ pad 2 của C51 tới via GND; lớp 2 bị khoét dưới pad và stub; ≈ 100 Ω (ƯỚC TÍNH) | ✓ |
| đường RF 50 Ω, lớp ngoài, không via, bẻ 135°, mặt GND lớp kề liền, via GND dày dọc đường | 0.35 mm trên L1 tham chiếu L2, không via, hai góc 135°; L1 cách đồng 0.55 mm; 10 via GND hai bên đường, bước ~0.9 mm, cộng via GND của các tụ song song | ✓ |
| ăng-ten PCB: kiểm chứng bằng mô phỏng **và** đo; thêm CLC gần ăng-ten để chỉnh | vị trí C52/R41/L5 dùng làm CLC phía ăng-ten; **chưa mô phỏng, chưa đo** | ✗ |
| PCB 4 lớp: L1 tín hiệu + linh kiện; L2 GND không đi dây; L3 nguồn + GND dưới RF và thạch anh; L4 ít tín hiệu, không linh kiện | đúng như vậy; L3 có một "đảo" +3V3 dưới chip nối các nhóm tụ qua 6 via, phần còn lại là GND | ✓ |
| pad GND đáy chip: ≥ 9 via | 9 via 0.45 / 0.2 mm (3 × 3, bước 0.9 mm); nằm trong ô kem hàn — xem mục 9 | ✓ |
| đường nguồn chính ≥ 20 mil, chân 1/2 ≥ 15 mil, còn lại 10 mil; lỗ via trên đường nguồn ≥ bề rộng đường | đường +3V3 chính 0.4 mm (16 mil), chân 1/2 ra 0.2–0.25 mm tới bus 0.4 mm của C40–C42; via nguồn 0.3 mm và 0.2 mm | ✗ (dòng đỉnh của thiết kế này vài chục mA, sụt áp không đáng kể; ghi nhận là lệch) |
| thạch anh cách chân clock ≥ 1.8 mm; không via trên đường clock; linh kiện nối tiếp gần phía chip; tụ tải ở cuối đường clock, pad GND gần pad GND thạch anh; không đi dây dưới thạch anh; GND + via quanh đường clock | thân Y2 cách chip ~7 mm; đường clock chỉ trên L1; L3 ở 4–6 mm từ chân (ngay sau C43), Y2 ở 7–10 mm; C49 trên chân 1, C50 cạnh chân 3, cả hai chung via GND với chân 4; cấm đi dây dưới Y1/Y2 trên L1/L4 | ✓ / ≈ (L3 không sát chân) |
| giữ ăng-ten xa thạch anh; UART/USB/header xa ăng-ten | Y2 cách mép mặt đất ăng-ten ~6 mm (dưới đoạn ngắn mạch của IFA); J1 cách ~18 mm (chỗ xa nhất còn trống ngoài vùng holder) | ≈ |

## 5. Ăng-ten PCB (TI DN007, vẽ đối xứng gương)

- Hình học theo TI DN007 "2.4-GHz Inverted F Antenna" (SWRU120D), Figure 1-1 và Table 1-1; hai chân nối đất và đoạn feed 45° không có kích thước trong bảng nên đo từ hình (±0.1 mm). Footprint `Antenna_TI_DN007_IFA_2.4GHz_Mirrored`: gốc tọa độ là điểm feed trên mép mặt đất; pad 1 = feed, pad 2 = hai chân đất; net-tie 1–2 (IFA nối tắt feed với đất ở DC).
- **Vẽ đối xứng gương** để đầu hở của nhánh bức xạ nằm ở mép trái bo (cách mép 1.2 mm), xa nút SW1 và lưỡi cảm biến; đoạn ngắn mạch nằm phía phải, gần chip. Ảnh gương có cùng đặc tính điện.
- TI (SWRU120D): kết quả đo dựa trên bo FR-4 dày 1 mm; trở kháng 50 Ω chỉ đúng trên bo tham chiếu và bị ảnh hưởng bởi kích thước/hình dạng mặt đất, vật ở trường gần (vỏ, pin), chiều dày và vật liệu PCB, nên TI khuyên thêm một mạng pi sát điểm feed — ở đây là C52 / R41 / L5. TI cũng khuyên chép đúng kích thước, và nếu bo rộng hơn ăng-ten thì tránh linh kiện hay mặt đất gần hai đầu ăng-ten: đầu trái là mép bo; đầu phải cách đồng gần nhất cùng hàng (lưỡi cảm biến) ~6 mm, nhưng nút SW1 nằm ngay dưới đầu phải, trong vùng mặt đất (pad cách mép mặt đất ~1 mm, thân nút ~2 mm) — một nguồn lệch tần nữa cần đo.
- Bo này dày 1.6 mm (vùng ăng-ten không có đồng ở L2–L4, nên dưới ăng-ten là toàn bộ chiều dày FR-4); mặt đất, vỏ, pin CR2450 (vỏ kim loại cách ~25 mm) cũng khác. Dự đoán (ƯỚC TÍNH, chưa mô phỏng): tần số cộng hưởng thấp hơn bản của TI ⇒ có thể phải dùng mạng pi hoặc **cắt ngắn nhánh bức xạ**; chỉ đo mới biết.
- Vùng cấm: x 0…31.8 mm, y 0…7.52 mm trên mọi lớp (không đồng, không via, không đổ đồng); không in silkscreen trên ăng-ten. Một hàng via GND dọc mép mặt đất (y ≈ 8.1 mm, bước 1 mm, bỏ những chỗ có linh kiện).
- Không có VNA thì làm được gì: so RSSI/LQI với bo module (Rev B) hoặc dev kit đặt cùng chỗ (T-25 / C-05); đo công suất phát và hài bằng máy phân tích phổ nếu có. Chỉnh ăng-ten và mạng phối hợp đúng cách **cần VNA** (hoặc gửi phòng đo).

## 6. Mạng phối hợp RF và stub

Thứ tự từ chân 32 (ANT) ra ăng-ten, tên vị trí theo hình "RF matching" của HDG:

| Vị trí HDG | Ref | Giá trị khởi đầu | Kiểu |
|---|---|---|---|
| C12 (song song, phía chip, có stub) | C51 | 1.5 pF | 0201 |
| L2 (nối tiếp) | L4 | 2.4 nH | 0201 |
| C11 (song song) | C52 | 1.5 pF | 0201 |
| C3 (nối tiếp, phía ăng-ten) | R41 | 0 Ω | 0201 |
| L1 (song song, phía ăng-ten) | L5 | không lắp | 0201 |

- Mục tiêu chỉnh của HDG: S11 nhìn từ chip gần điểm liên hợp 35 + j0 Ω; S21 < −35 dB ở 4.8 GHz và 7.2 GHz (hài bậc 2 và 3). Đo bằng VNA theo chương "RF Tuning" của HDG; HDG nói giá trị của module "không áp dụng trực tiếp được".
- Đường 50 Ω: 0.35 mm trên L1, điện môi tới L2 là prepreg 7628 0.2104 mm, εr 4.4: Hammerstad–Jensen với đồng 35 µm cho 51.7 Ω (0.38 mm → 49.5 Ω); lớp phủ solder mask (εr 3.8) kéo xuống thêm vài phần trăm. ƯỚC TÍNH — đặt JLC kiểm soát trở kháng 50 Ω ±10 % trên L1/L2 để nhà máy hiệu chỉnh bề rộng. Đổ đồng L1 cách đường RF 0.55 mm (> 2 × chiều dày điện môi) nên đường vẫn là microstrip.
- Hình học: từ chân 32 một đoạn rộng 0.2 mm (bằng pad, giữ khe 0.2 mm tới chân 31) dài ~0.6 mm có một góc 135°, rồi 0.35 mm: đoạn 45° tới đường dọc x = 15.92 mm, đoạn dọc qua C51, L4, C52, R41, L5 tới feed. Dài tổng từ tâm pad ~8.7 mm.
- Stub: 0.5 mm (≈ 100 Ω khi tham chiếu L3: điện môi 0.2104 + 0.0152 + 1.065 mm, εr ~4.57; Hammerstad–Jensen 100.2 Ω) × 0.381 mm (15 mil) từ mép pad GND của C51 tới một via GND 0.45 mm; L2 bị khoét dưới pad và stub, L1 không đổ đồng sát chúng. Điện cảm ước tính ~0.23 nH; cùng C51 và ESL của tụ tạo bẫy cộng hưởng nối tiếp gần hài bậc 2 — đó là mục đích của stub theo HDG. CHƯA KIỂM THỬ.

## 7. Stack-up, luật thiết kế, lớp

- JLC04161H-7628 (trang https://jlcpcb.com/impedance): Cu ngoài 35 µm / prepreg 7628 0.2104 mm εr 4.4 / L2 15.2 µm / lõi 1.065 mm εr 4.6 / L3 15.2 µm / prepreg 7628 0.2104 mm / Cu ngoài 35 µm; tổng ~1.59 mm (cộng tay).
- Luật trong `th_sensor_h2c.kicad_pro`: clearance tối thiểu 0.1 mm, đường tối thiểu 0.1 mm, via tối thiểu 0.45 / 0.2 mm, vòng khuyên 0.125 mm, đồng tới mép 0.3 mm, lỗ tới lỗ 0.5 mm; net class Default 0.2 mm / 0.15 mm, Power 0.4 mm / 0.15 mm, RF 0.35 mm / 0.15 mm. Thực tế dùng: đường ≥ 0.2 mm, khe ≥ 0.15 mm. Năng lực JLC (trang capabilities, đọc 2026-11-06): nhiều lớp 0.09 / 0.09 mm; via 0.15 / 0.25 mm tối thiểu, lỗ 0.2 mm với pad ≥ 0.45 mm không tính thêm phí; đồng tới mép phay ≥ 0.2 mm; dung sai trở kháng ±10 %.
- L1: linh kiện, 233 đoạn dây, đường RF, đổ GND. L2: GND liền (một ô khoét dưới stub). L3: GND + đảo +3V3 dưới chip. L4: 69 đoạn dây (các đường dài: VBAT, I2C, nút, EN), đổ GND; không linh kiện. Via GND: 9 trong pad đáy chip, 10 dọc đường RF, 51 via khâu (tránh chữ silkscreen; hàng dày dọc mép mặt đất ăng-ten), cộng via của từng tụ.
- Đi dây: phần quanh chip, RF, thạch anh, USB vẽ tay trong `gen_pcb_chip.py`; phần còn lại do `router.py` (cấm via trong pad SMD ở bản này). Kết quả: `hardware/chip/reports/routing_log.txt`. Đường dài nhất là VBAT từ cầu chia (góc trên trái) tới TP1 (~60 mm, chủ yếu trên L4), vì router không đi dưới đường RF.

## 8. Bố trí

- Chip ở (11.8, 16.6) mm xoay 270°: chân 32 ở góc đông-bắc; phía bắc (chân 1–8: nguồn, 5 chân bỏ trống, VBAT_SENSE) quay về ăng-ten; phía đông là RF, nguồn 30/31, thạch anh, nguồn 27, USB; phía nam là EN, nguồn 18–20, LED, UART; phía tây là nguồn chân 9, GPIO8–12 và thạch anh 32 kHz.
- Các tín hiệu GPIO phía tây xuống L4 qua một "bậc thang" via; EN xuống L4 ngay tại chân 17.
- J1 dưới chip; SW1 ngay dưới đầu phải của ăng-ten, sát rãnh lưỡi cảm biến; bộ chuyển đổi, holder, lưỡi SHT40, cột giám sát/RST bên trái: như Rev B (TP3 dịch 0.65 mm, R21 nằm ngang dưới TP3, C21/C22 dời xuống dải trên holder).
- 28 ký hiệu linh kiện chỉ có trên lớp Fab (`hardware/chip/production/assembly_top.pdf`) vì không đủ chỗ trên silkscreen (AE1 và BT1 do chọn).

## 9. Sản xuất và lắp ráp

- Đặt PCB: 4 lớp, 1.6 mm, JLC04161H-7628, kiểm soát trở kháng (50 Ω đơn trên L1/L2; tùy chọn 90 Ω vi sai cho cặp USB), ENIG (pad phẳng cho QFN 0.4 mm và 0201), via phủ mask. Rãnh lưỡi cảm biến 1 mm hình chữ L từ mép trên (phay, không V-cut).
- 9 via trong pad đáy U4 nằm trong ô kem hàn: kem có thể chảy xuống via. Hỏi JLC lấp/bịt via (via-in-pad lấp epoxy là mặc định từ 6 lớp; giá cho 4 lớp không ghi trên trang capabilities) hoặc chấp nhận và kiểm mối hàn (C-06).
- **U4 tồn kho 0** tại JLC: gửi linh kiện (global sourcing / khách cấp) hoặc lắp phần còn lại và gắn U4 bằng khí nóng + stencil. Không hàn mỏ được.
- Kiểm từng dòng `orientation_check.md` trong bản xem trước của JLC, đặc biệt **Y2**: xoay sai 90° đặt một chân thạch anh lên pad GND.
- Giá trị RF và tụ tải là giá trị khởi đầu; nên đặt dư linh kiện 0201 các giá trị lân cận (1.0–2.2 pF, 1.8–3.3 nH) cho việc chỉnh.

## 10. Kiểm thử bổ sung (ngoài T-01…T-42 của `docs/test_plan.md`)

Tất cả **CHƯA KIỂM THỬ**.

| ID | Kiểm tra | Tiêu chí / ghi chú |
|---|---|---|
| C-01 | Tần số thạch anh 32 MHz: đo lệch tần (ví dụ qua công cụ RF test của Espressif hoặc đo sóng mang bằng máy phân tích phổ) ở 25 °C; biên độ dao động | lệch ≤ ±10 ppm (HDG), biên độ > 500 mV (ghi chú HDG); chỉnh C49/C50 |
| C-02 | Phối hợp phía chip bằng VNA theo chương "RF Tuning" của HDG | S11 gần 35 + j0 Ω; S21 < −35 dB ở 4.8 và 7.2 GHz; ghi lại giá trị C51/L4/C52 cuối |
| C-03 | Ăng-ten: S11 tại feed (tháo R41, hàn cáp pigtail) | đề xuất: cộng hưởng trong 2400–2483.5 MHz, S11 ≤ −10 dB trên cả dải; cắt nhánh bức xạ hoặc dùng R41/L5/C52 để chỉnh |
| C-04 | Công suất phát và hài (dẫn qua pigtail hoặc bức xạ) | so với công suất cấu hình; hài thấp |
| C-05 | Tầm phủ: RSSI/LQI ở 5 m và 10 m qua tường, so với bo Rev B (module) cùng vị trí | không kém rõ rệt so với module; ghi số |
| C-06 | Mối hàn U4 (pad đáy, chân 0.4 mm) | X-quang hoặc kiểm thông mạch/nhiệt; không cầu thiếc |
| C-07 | USB-Serial/JTAG qua J1 (D+/D−/GND), UART0 qua J1 | `idf.py flash monitor` chạy như T-10 |
| C-08 | Dòng ngủ và dòng trung bình (T-30…T-34) | không khác Rev B quá sai số đo (cùng chip, cùng firmware) |

## 11. Tái tạo file

Chạy từ gốc repo, theo thứ tự (biến `TH_VARIANT=chip` chọn bản chip; không có biến thì là Rev B):

```sh
TH_VARIANT=chip python3 hardware/scripts/gen_schematic.py   # schematic, thư viện, kiểm parity
TH_VARIANT=chip python3 hardware/scripts/gen_pcb_chip.py    # đặt, đi dây, đổ đồng 4 lớp, silkscreen (~20 s)
TH_VARIANT=chip python3 hardware/scripts/gen_project.py     # .kicad_pro: luật 4 lớp, net class RF
TH_VARIANT=chip python3 hardware/scripts/gen_reports.py     # ERC, DRC + parity, PDF/SVG/3D
TH_VARIANT=chip python3 hardware/scripts/gen_production.py  # Gerber 4 lớp, drill, BOM, CPL, bản vẽ lắp ráp
python3 tools/check_pinmap.py --variant chip               # board_pins.h ↔ chân chip
```

Schematic, board, project và thư viện sinh lại **giống từng byte**; chỉ dấu thời gian trong Gerber/drill/báo cáo/PDF/ZIP và ảnh render thay đổi. Tra tồn kho: `python3 tools/jlc_lookup.py --json <mã…> > hardware/chip/production/jlc_parts_snapshot.jsonl`.

## 12. Nguồn

- Espressif, *ESP32-H2 Hardware Design Guidelines* v1.6 (2025-06-05): https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32h2/ — "Schematic Checklist", "PCB Layout Design" (đọc 2026-11-06).
- Espressif, *ESP32-H2 Series Datasheet* v1.3 — mã đặt hàng, bảng chân QFN32.
- Thư viện KiCad của Espressif (github.com/espressif/kicad-libraries, commit dd76561812ab300351234ba6e0ec1295641796f0): symbol "ESP32-H2", footprint QFN-32-1EP_4x4mm_P0.4mm_EP2.9x2.9mm (bản sao trong `hardware/chip/kicad/lib/`, giấy phép trong cùng thư mục).
- Texas Instruments, Application Report *2.4-GHz Inverted F Antenna* (DN007), SWRU120D, sửa đổi 01/2019: https://www.ti.com/lit/an/swru120d/swru120d.pdf
- JLCPCB: https://jlcpcb.com/impedance (stack-up JLC04161H-7628), https://jlcpcb.com/capabilities/pcb-capabilities (đọc 2026-11-06), hướng dẫn máy tính trở kháng.
