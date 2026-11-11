# TH-SENSOR-H2W-123 Rev A — biến thể dùng pin CR123A (pin nằm cạnh bo)

Biến thể của TH-SENSOR-H2W (module ESP32-H2-WROOM-02C-H4S do người dùng tự mua và hàn) chạy bằng **một pin CR123A** (IEC CR17345, Li-MnO2 3 V, 1550 mAh) thay cho CR2450. **Pin không nằm trên bo**: bo chỉ mang phần mạch, **24.8 × 37.3 mm**; pin đặt cạnh bo trong đế riêng và nối vào bo bằng hai dây hàn vào hai lỗ ở mép trái. Không còn tụ đệm 470 µF; có thêm cầu chì tự phục hồi ngay sau lỗ +. Mạch còn lại giữ nguyên: AO3401A chống ngược cực, TPS63900 3.3 V, giám sát áp, SHT40 trên lưỡi tách nhiệt, LED, cầu đo pin, một nút USER/BOOT bấm cạnh. Firmware dùng chung mã nguồn, build thêm lớp cấu hình `sdkconfig.defaults.cr123a` (mục 7). Rev B, H2C và H2W không thay đổi.

Hai yêu cầu của người dùng, cùng ngày 2026-11-11:

1. "Làm mục 1 và 3, chiều ngang board là 34,5cm bố trí như hình vẽ. Màu đen là cr123a xanh lá là pcb đỏ là esp h2 wroom hồng là cảm sht40, tổng thế thiết bị là vuông" (hình vẽ: pin đứng cạnh bo, module ở trên, SHT40 ở cạnh dưới). Bản đầu tiên (commit `d85e807`) hiểu thành một bo liền 53.3 × 47.3 mm có đế pin hàn trên bo.
2. Trên hình bố trí của bản đó, người dùng khoanh phần mạch (không gồm pin) và viết: "Chỉ bố trí pcb khu vực này, thu gọn mạch nhỏ nhất có thể giữ nguyên vị trí sht40 và nút bấm như hình vẽ." Bản thu nhỏ (commit `bec633c`) vẫn 4 lớp.
3. Sau khi được giải thích rằng hai lớp trong của bản thu nhỏ chỉ là mặt GND, không có dây: "làm lại mạch 2 lớp". Bố trí linh kiện giữ nguyên; bo thành **2 lớp**, via 0.6 / 0.3 mm theo quy trình 2 lớp tiêu chuẩn như Rev B (mục 5, 10).

Tài liệu này mô tả bản hiện tại (yêu cầu 2 và 3); nó **thay thế** bản đầu tiên.

Cách hiểu yêu cầu thứ hai (đã báo người dùng, chưa được xác nhận lại):

- Bo chỉ là phần mạch ⇒ pin và đế pin nằm ngoài bo, nối bằng dây.
- "Nhỏ nhất có thể" ⇒ bo thu từ 34.5 mm xuống 24.8 mm bề rộng (mục 4). Để làm được, pad nạp J1 và các test pad chuyển sang **mặt sau** (pad trần, không có linh kiện).
- SHT40 và nút bấm vẫn ở mép dưới, SHT40 bên trái nút như hình vẽ. Nút cách mép phải 7.4 mm đúng như hình; SHT40 nằm ở góc dưới trái (cách nút 14 mm thay vì 10 mm trên hình) vì lưỡi tách nhiệt chỉ gọn khi ở góc.
- Vẫn là ảnh gương của hình vẽ tay ban đầu: pin bên trái, module ở góc trên phải (mục 5).

## 1. Trạng thái

| Hạng mục | Trạng thái | Bằng chứng |
|---|---|---|
| Schematic: ERC | ĐÃ XÁC MINH: 0 lỗi, 0 cảnh báo | `hardware/wroom123/reports/erc_report.txt` |
| PCB: DRC + schematic parity | ĐÃ XÁC MINH: 0 vi phạm, 0 pad chưa nối, 0 lỗi parity (mọi mức) | `hardware/wroom123/reports/drc_report.txt` |
| Pin map firmware ↔ module | ĐÃ XÁC MINH | `python3 tools/check_pinmap.py --variant wroom123` |
| Kích thước bo 24.8 × 37.3 mm, ăng-ten nhô 6.0 mm ⇒ 24.8 × 43.3 mm | ĐÃ XÁC MINH trên file board | mục 4 |
| Gerber 2 lớp, drill, BOM (25 dòng), CPL (38 linh kiện, tất cả mặt trên) | ĐÃ XÁC MINH là sinh được; **chưa gửi nhà máy** | `hardware/wroom123/production/` |
| Tái tạo giống từng byte (schematic, board, project) | ĐÃ XÁC MINH (chạy hai lần) | mục 10 |
| Firmware với lớp `cr123a`: build | ĐÃ XÁC MINH (build được); chạy trên bo: **CHƯA KIỂM THỬ** | `docs/reports/firmware_build.md` |
| Khả năng cấp xung của CR123A, tuổi thọ 2.3–2.6 năm | **ƯỚC TÍNH** (mô hình khớp theo đồ thị datasheet) | mục 2, `hardware/analysis/results/cr123a_summary.md` |
| Khung vuông 43.3 × 43.3 mm khi đặt cạnh một đế pin 18.2 × 43.3 mm | **ƯỚC TÍNH** từ bản vẽ một loại đế; đế và vỏ do người dùng chọn | mục 4, mục 6 |
| Ăng-ten khi pin chỉ cách module khoảng 7 mm | **CHƯA KIỂM THỬ**; trái khuyến nghị ≥ 15 mm của Espressif | mục 5, K-04 |
| Bảng phần trăm pin của CR123A | **ƯỚC TÍNH** (đọc từ đồ thị 20 mA); thô ở nửa trên | mục 7 |
| Điện, cảm biến, Matter, dòng ngủ | **CHƯA KIỂM THỬ** | mục 9, `docs/test_plan.md` |

Không có bo nào được đặt, làm hay đo. Không tuyên bố chứng nhận nào.

## 2. Vì sao CR123A — kết quả mô hình (ƯỚC TÍNH)

Mô hình nguồn của dự án (`hardware/analysis/power_model.py`) kết luận thiết kế CR2450 **chưa đạt**: pin đồng xu không cấp nổi xung dòng, nên từ khoảng giữa đời pin thiết bị không khởi động lại được, và tuổi thọ chỉ 0.55–0.77 năm (`docs/power_budget.md`). `hardware/analysis/cr123a_study.py` chạy đúng các dạng tải và mô hình bộ chuyển đổi đó với một pin CR123A.

Mô hình pin: khớp theo năm điểm đọc từ đồ thị xả liên tục của datasheet Panasonic CR123A (20 °C: 20 mA 2.90 V, 100 mA 2.82 V, 300 mA 2.72 V, 500 mA 2.63 V, 1 A 2.52 V; sai số khớp 0.01 V). Không có số liệu công bố về điện trở theo mức đã dùng hay theo nhiệt độ, nên các trạng thái "late" (điện trở × 3) và "eol" (× 8) cùng hệ số nhiệt độ (−10 °C: × 2.5) là **giả định**, lấy khắt khe như của pin đồng xu.

| Trạng thái pin | CR2450 + 555 µF | CR123A, chỉ 85 µF (không có C5) |
|---|---|---|
| mới, 25 °C | mọi tải ổn | mọi tải ổn, VIN ≥ 2.94 V |
| giữa đời, 25 °C | khởi động và commissioning **RESET** | mọi tải ổn, VIN ≥ 2.88 V |
| late, 25 °C | report **RESET** | mọi tải ổn, VIN ≥ 2.62 V |
| eol, 25 °C | report **RESET** | mọi tải ổn, VIN ≥ 2.27 V |
| mới, −10 °C | khởi động và commissioning **RESET** | mọi tải ổn, VIN ≥ 2.77 V |
| late, −10 °C | — | mọi tải ổn, VIN ≥ 2.27 V |

Rail 3V3 giữ 3.30 V trong mọi trường hợp của CR123A (UVLO của TPS63900 ở 1.65 V). Thêm 470 µF không đổi kết quả, nên bo này bỏ C5. Mô hình không tính điện trở của dây nối pin và tiếp điểm đế; với dây ngắn chúng nhỏ hơn nhiều so với 0.15–0.7 Ω của F1.

Tuổi thọ ở tải danh nghĩa (63.1 µA lấy từ pin, tự xả 1 %/năm): CR2450 0.55 / 0.66 / 0.76 năm (dùng được 50 / 60 / 70 % dung lượng); **CR123A 2.32 / 2.45 / 2.59 năm** với giả định dùng được 85 / 90 / 95 % của 1550 mAh. Không phải số đo.

## 3. Khác biệt so với H2W (CR2450)

| | H2W Rev A | H2W-123 Rev A |
|---|---|---|
| Pin | 1 × CR2450, 620 mAh, đế SMD ở mặt dưới bo | **1 × CR123A, 1550 mAh, ngoài bo**; trên bo chỉ có BT1 = hai lỗ hàn dây |
| Tụ đệm C5 470 µF | tantal TAJD477K006RNJ | **không có** (mục 2) |
| Bảo vệ ngắn mạch | không (pin đồng xu tự giới hạn dòng) | **F1**, cầu chì tự phục hồi BHFUSE BSMD1206-050-6V (LCSC C883122) ngay sau lỗ + |
| Bo | 37.6 × 31.6 mm (37.6 × 37.6 tính cả ăng-ten) | **24.8 × 37.3 mm (24.8 × 43.3 tính cả ăng-ten)**; cả cụm với đế pin bên cạnh: khoảng 43.3 × 43.3 mm |
| Số lớp, lớp đi dây | 4 lớp; F.Cu + In2.Cu (mặt dưới dành cho đế pin) | **2 lớp**; F.Cu + B.Cu, phần trống của cả hai mặt đổ GND |
| Via | 0.45 / 0.2 mm (quy trình nhiều lớp) | 0.6 / 0.3 mm (quy trình 2 lớp tiêu chuẩn, như Rev B) |
| Mặt dưới | đế pin (lắp ráp hai mặt) | chỉ có pad trần: J1, TP1–TP6; **lắp ráp một mặt** |
| J1 và test pad | mặt trên | **mặt dưới** |
| Nút SW1 (bấm cạnh) | giữa mép trái | **mép dưới**, bấm từ dưới lên khi gắn tường |
| Lưỡi SHT40 | góc trên trái | **góc dưới trái** |
| Hướng gắn tường | cạnh có nút xuống đất, ăng-ten nằm ngang | **ăng-ten hướng lên**, cảm biến và nút ở cạnh dưới |
| Chiều dày | ≈ 12.3 mm | riêng bo ≈ 4.8 mm (module cao 3.2 mm); cả thiết bị do pin Ø17 mm và đế quyết định |
| Số linh kiện trong `design.py` | 49 | 49 (−C5, +F1; BT1 là pad, không phải linh kiện) |
| Dòng BOM / linh kiện gắn máy | 26 / 39 | 25 / 38 |
| Firmware | profile `battery` | profile `battery` + lớp `cr123a` |

## 4. Kích thước

- Bo **24.8 × 37.3 mm**; phần ăng-ten của module nhô 6.0 mm khỏi mép trên ⇒ 24.8 × 43.3 mm. Diện tích bo 925 mm², so với 2521 mm² của bản đầu tiên và 1188 mm² của H2W.
- **Bề rộng 24.8 mm** do hàng bộ chuyển đổi quyết định: FET chống ngược cực, tụ vào, TPS63900, tụ rail xếp một hàng có tổng bề rộng courtyard 23.1 mm. Module (19 mm tính cả pad) cộng một cột linh kiện 0603 ở các chân trái của nó cần 22.9 mm.
- **Chiều cao 37.3 mm** là bốn hàng xếp sát nhau: module (14.5 mm), hàng thạch anh và giám sát áp (6.4 mm), hàng bộ chuyển đổi (10 mm), hàng lưỡi cảm biến và nút bấm (6.4 mm).
- Hai số đó cũng cho một khung vuông: bo 24.8 mm + khe 0.3 mm + một đế pin rộng 18.2 mm = 43.3 mm = chiều dài của đế đó = chiều cao bo tính cả ăng-ten. Đây là hình vuông nhỏ nhất chứa được đế loại này; với đế hoặc kẹp pin khác, con số do người dùng quyết định.
- Góc trên phải vuông (pad chân 28 của module cách hai mép 0.3 mm), ba góc còn lại bo tròn R1.5.

## 5. Bố trí (mặt trên, gốc tọa độ góc trên trái)

- **Module ở góc trên phải**, tâm (15.0, 4.0): thân x 6.0–24.0 mm, y −6…14 mm. Điểm cấp của ăng-ten WROOM-02C nằm ở phía phải vùng ăng-ten; ESP32-H2 Hardware Design Guidelines ("Positioning a Module on a Base Board", hình "antenna feed point on the right") đánh dấu ✓ cho vị trí góc trên phải. Hàng 14 via GND bước 1 mm dọc mép trên dưới module.
- **Khoảng cách pin – ăng-ten**: bo chỉ rộng hơn module 6 mm về phía pin. Pin đặt sát bo sẽ cách module khoảng 7 mm, và đầu trên của đế nằm ngang hàng với vùng ăng-ten. Cùng tài liệu trên khuyên chừa ≥ 15 mm quanh ăng-ten; bản đầu tiên giữ 16 mm, bản này đổi khoảng cách đó lấy kích thước theo yêu cầu. Ảnh hưởng tới tầm phủ: **CHƯA KIỂM THỬ** (K-04). Nếu kém, cách sửa không cần đổi bo là đặt đế pin xa bo hơn.
- **Cột linh kiện ở các chân trái của module** (x = 3.75): C24 (chân 1), C25 (EN), R32, C31, R31 (cầu đo pin quanh chân 4: ba pad của nút VBAT_SENSE thẳng hàng, nút trở kháng cao chỉ dài 3 mm), R24, R23, R35. Chân I2C (5, 6) và chân nút (8) đi vào trong 1.4 mm tới via rồi chạy ở mặt sau.
- **Dưới module**: thạch anh Y1 với C27/C28, C23, R25/D3 đặt y hệt bo H2W; bên phải là giám sát áp U3, C26, R22; bên trái là công tắc đo pin Q3.
- **Hai lỗ hàn dây pin BT1** ở mép trái, y = 18.5 (−, pad tròn) và 21.0 (+, pad vuông); cầu chì F1 ngay bên phải lỗ +.
- **Hàng bộ chuyển đổi** (y 21–31): Q1, R1, C2, C3, C1, U1, L1, C4, R2–R4, rồi C21, C22, R21; đầu vào ở bên trái, phía dây pin.
- **Lưỡi SHT40** ở góc dưới trái (6.6 × 5.4 mm), cắt bằng rãnh 1 mm hình chữ L từ mép trái; cầu nối 1 × 2.6 mm ở mép dưới mang 4 dây bước 0.5 mm (từ mép vào: GND, SDA, SCL, 3V3); không via, không đổ đồng trên lưỡi (cả hai mặt). Đây là lưỡi của H2W lật từ trên xuống dưới. Điện trở kéo lên R26/R27 ngay sau cầu nối. SHT40 cách U1 14.1 mm và cách tâm module 33 mm (bản đầu tiên: 22.5 và 41 mm); khi gắn tường nó nằm dưới mọi nguồn nhiệt. Tự sưởi: CHƯA KIỂM THỬ (K-08).
- **SW1** trên mép dưới, tâm cách mép phải 7.4 mm, núm nhô 0.5 mm ra ngoài mép.
- **Mặt sau** (chỉ pad trần và chữ): J1 nằm sau module, ba hàng tính từ mép trên xuống, nhìn từ mặt sau từ trái sang, là GND BOOT / D− D+ / RX TX (pad vuông = TX), tên in cạnh từng pad; TP6 (EN) phía trên bên cạnh; TP1–TP5 thành một hàng ở giữa bo, nhìn từ mặt sau từ trái sang: 3V3, VOUT, GND, VIN, VBAT; dấu + và − cạnh hai lỗ dây pin; tên sản phẩm, cảnh báo loại pin, tên bo và ngày.
- Gắn tường: mặt sau áp vào tường, ăng-ten hướng lên.
- **Hai lớp**: dây ở cả hai mặt, phần trống của mỗi mặt đổ GND. Mặt trên dưới module không có dây (chỉ các đoạn thoát chân dài ≤ 1.4 mm và via), nên đồng GND ở đó gần như liền; dưới module ở mặt sau có J1 và các đường tới nó. So với bản 4 lớp, mặt GND kém liền hơn: đường hồi dòng của bộ chuyển đổi và module dài hơn. Dòng vào bị giới hạn 100 mA nên rủi ro được đánh giá là thấp, nhưng chưa đo (K-04, K-06).

## 6. Nối pin và cầu chì

**BT1** là hai lỗ mạ, khoan 1.0 mm, pad 2.0 mm, cách nhau 2.54 mm, sát mép trái: pad **vuông = +**, pad tròn = −, có dấu + / − ở cả hai mặt. Hàn được dây có lõi tới khoảng 0.8 mm, hoặc một hàng chân 2 × 1 bước 2.54 mm. Footprint do `gen_schematic.py` vẽ (`battery_wire_pads()`); BT1 không có trong BOM và CPL.

- **Đế pin do người dùng chọn và tự lắp**; không có đế nào trong BOM. Một loại đã đọc bản vẽ là MYOUNG BH-123A-A1CJ002 (LCSC C5290177, bản vẽ MY-CP-0398: thân 43.3 × 18.2 × 14.2 mm, hai chân dẹt 0.8 × 0.3 mm cách nhau 37.5 mm, tiếp điểm thép không gỉ mạ nickel, −25…+85 °C): hàn dây vào hai chân của nó. Kích thước ở mục 4 lấy theo loại này. Chưa có đế thật nào được so với bản vẽ.
- Dây nên ngắn và đi vòng phía dưới hoặc bên trái bo, tránh vùng ăng-ten ở trên. Bo không có chỗ kẹp dây: phải cố định dây trong vỏ.
- Lắp ngược cực (đấu dây ngược hoặc đặt pin ngược): Q1 chặn, mạch không hỏng nhưng không chạy. Phải đo cực ở hai lỗ trước khi lắp pin lần đầu (K-01).
- Chỉ dùng pin CR123A 3 V sơ cấp; không dùng pin sạc 16340/RCR123A (3.7–4.2 V), không sạc.

**F1** (1206, giữ 0.5 A, ngắt 1 A, 6 V, chịu tới 100 A, 0.15–0.7 Ω theo trang JLC): một CR123A cấp được 1.5 A liên tục và 3.5 A xung (datasheet Energizer 123), đủ làm nóng đường mạch khi có chập; pin đồng xu thì không. F1 đứng ngay sau lỗ +, trước cả cầu đo pin, nên nó bảo vệ mọi thứ trên bo nhưng **không bảo vệ đoạn dây từ pin tới bo**. Sụt áp ở giới hạn 100 mA của bộ chuyển đổi: ≤ 0.07 V. Datasheet Energizer ghi pin của họ có PTC bên trong; datasheet Panasonic không nói, nên thiết kế không dựa vào điều đó.

## 7. Firmware

Build: `-D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.defaults.battery;sdkconfig.defaults.cr123a"` (hoặc `debug` thay cho `battery`; cả hai tổ hợp đã build, `docs/reports/firmware_build.md` mục 7). Lớp `cr123a` chỉ đặt `CONFIG_APP_CELL_CR123A=y`; từ đó:

| | CR2450 (mặc định) | CR123A |
|---|---|---|
| Bảng điện áp → phần trăm | bảng pin đồng xu | bảng đọc từ đồ thị 20 mA của Panasonic CR123A |
| Power Source: BatIECDesignation / BatCapacity | CR2450 / 620 mAh | CR17345 / 1550 mAh |
| Ngưỡng Warning / Critical | 40 % / 20 % | 20 % / 8 % |
| Ngưỡng Critical theo điện áp | 2600 mV | 2500 mV |
| Điện áp tối thiểu để bật radio | 2400 mV | 2200 mV |

Pin map không đổi (`tools/check_pinmap.py --variant wroom123`). Giới hạn +8 dBm của công suất phát giữ nguyên vì nó đến từ giới hạn dòng vào 100 mA của TPS63900, không chỉ từ pin.

**Phần trăm pin của CR123A chỉ mang tính chỉ báo**: điện áp gần như phẳng (khoảng 2.92 V từ vài phần trăm tới quá nửa dung lượng), nên vài mV sai số ADC làm con số lệch hàng chục phần trăm ở nửa trên; nó chỉ có ý nghĩa ở một phần ba cuối. Pin lạnh đọc thấp hơn.

## 8. Sản xuất và lắp ráp

- PCB: **2 lớp**, FR-4 1.6 mm, đồng 1 oz, quy trình tiêu chuẩn (lỗ via 0.3 mm), via phủ mask, HASL không chì hoặc ENIG; rãnh lưỡi cảm biến 1 mm phay (không V-cut). Không cần kiểm soát trở kháng: bo không có đường RF.
- **Lắp một mặt**, toàn linh kiện dán: 38 linh kiện trong CPL, tất cả ở mặt trên. Linh kiện Extended: F1, L1, R3, R4, SW1, U1, U3, U5. Tồn kho thấp lúc tra: U3 733 cái.
- **U4 tự mua** (ESP32-H2-WROOM-02C-**H4S**) và hàn tay như ở H2W (`docs/wroom_variant.md` mục 4 và 9).
- **Pin và đế pin tự lắp** (mục 6).
- Kiểm `orientation_check.md` trong bản xem trước của JLC (LED, U1, U3, U5, Q1, Q3) và SW1 (núm quay ra mép dưới).
- Không có nút RST: reset bằng cách chập TP6 (EN, mặt sau) xuống GND; nạp qua USB-Serial/JTAG trên 6 pad J1 ở mặt sau (hàn dây hoặc kim pogo).
- Không bao giờ cấp nguồn bench khi pin đang nối vào bo.

## 9. Kiểm thử bổ sung (ngoài `docs/test_plan.md`)

Tất cả **CHƯA KIỂM THỬ**. Các mục W-02 (mối hàn module), W-05 (USB/UART qua J1) và W-06 (dòng ngủ) của H2W áp dụng nguyên.

| ID | Kiểm tra | Tiêu chí / ghi chú |
|---|---|---|
| K-01 | Đấu dây pin: trước khi lắp pin, đo thông mạch từ tiếp điểm + của đế tới pad vuông của BT1 và từ tiếp điểm − tới pad tròn; lắp pin, đo TP VBAT (mặt sau) | đúng cực; VBAT xấp xỉ điện áp pin. Làm **trước lần cấp điện đầu tiên** |
| K-02 | F1: đo sụt áp TP VBAT so với lỗ + khi tải 100 mA; với nguồn bench 3 V (không dùng pin) nối tải 1.5 Ω vào VBAT | sụt ≤ 0.07 V; F1 ngắt trong vài giây, tự phục hồi khi bỏ tải |
| K-03 | Khởi động và commissioning với pin đã dùng nhiều (xả trước bằng tải 20 mA tới còn ~20 %) và ở 0 °C | không reset (mô hình dự đoán ổn); ghi VIN thấp nhất |
| K-04 | Tầm phủ: RSSI/LQI ở 5 m và 10 m, ba trường hợp: pin sát bo (như khung vuông 43.3 mm), pin cách bo ≥ 10 mm, không pin (nguồn bench vào TP VBAT) | ghi số; nếu pin sát bo làm kém rõ rệt thì dời đế pin ra xa hoặc quay lại bố trí rộng 53.3 mm |
| K-05 | Phần trăm pin: ghi BatVoltage và BatPercentRemaining theo thời gian trong một lần xả tăng tốc | so với bảng ở `battery_model.c`; chỉnh bảng và ngưỡng Warning/Critical |
| K-06 | Dòng trung bình 24 h và dòng ngủ | như T-30…T-34; không có rò của C5 |
| K-07 | Gắn tường: bấm SW1 từ dưới lên; T-11 (độ chính xác SHT40) ở tư thế này | thao tác nút đúng; lệch như T-11 |
| K-08 | Tự sưởi: T-12 trên bo này (SHT40 cách bộ chuyển đổi 14 mm) | chênh < 0.2 °C |

## 10. Tái tạo file

```sh
TH_VARIANT=wroom123 python3 hardware/scripts/gen_schematic.py     # schematic, footprint lỗ hàn dây, kiểm parity
TH_VARIANT=wroom123 python3 hardware/scripts/gen_pcb_wroom123.py  # đặt, đi dây F.Cu + B.Cu, đổ GND hai mặt, silkscreen
TH_VARIANT=wroom123 python3 hardware/scripts/gen_project.py       # .kicad_pro
TH_VARIANT=wroom123 python3 hardware/scripts/gen_reports.py       # ERC, DRC + parity, PDF/SVG/3D
TH_VARIANT=wroom123 python3 hardware/scripts/gen_production.py    # Gerber 2 lớp, drill, BOM, CPL
python3 tools/check_pinmap.py --variant wroom123
python3 hardware/analysis/cr123a_study.py                        # bảng mô hình ở mục 2 (~1 phút)
```

Schematic, board và project sinh lại **giống từng byte**; chỉ dấu thời gian trong Gerber/drill/báo cáo/PDF/ZIP và ảnh render thay đổi. Tồn kho JLC tra lúc 2026-11-11 02:15 UTC (`hardware/wroom123/production/jlc_parts_snapshot.jsonl`; file còn dòng của đế pin C5290177 từ bản đầu tiên, nay không thuộc BOM).

Số liệu board: 100 via 0.6 / 0.3 mm (67 via GND, trong đó 39 via khâu GND); F.Cu khoảng 208 mm dây, B.Cu khoảng 235 mm; 42 footprint ở mặt trên, 7 ở mặt sau (J1, TP1–TP6); 17 ký hiệu linh kiện mặt trên không đủ chỗ trên silkscreen, chỉ có trên lớp Fab. Đồng GND phủ 52 % mặt trên (69 % vùng dưới module, 56 % vùng bộ chuyển đổi) và 63 % mặt dưới (56 % dưới module, 74 % dưới bộ chuyển đổi); các mảng GND nối với nhau qua via. Hai túi đồng GND nhỏ bị nối bằng cổ hẹp hơn 0.13 mm được script tự loại (vùng cấm đổ đồng nhỏ, `remove_fill_slivers`).

Ba đường dài ở mặt sau (SCL, SDA từ module xuống điện trở kéo lên, và đường nút bấm tới pad BOOT của J1) được vạch tay trong `gen_pcb_wroom123.py` theo một sơ đồ không cắt nhau; phần còn lại do bộ đi dây của dự án làm. Lý do: hai lớp trong là mặt GND, mặt trước dưới module không đi dây được, nên bộ đi dây tự động xếp các đường này theo thứ tự nào cũng bao kín một net khác.

## 11. Nguồn

- Panasonic, *CR123A — CR Cylindrical-type Lithium Battery (Standard type)* (July 2024): https://energy.panasonic.com/dam/master/pdf/en/datasheet/lithium/CR123A_Datasheet_EN.pdf — 3 V, 1550 mAh, dòng liên tục chuẩn 20 mA, Ø17.0 × 34.5 mm, ≈ 16 g, −40…+70 °C; đồ thị xả liên tục 20 mA–1 A và xả xung 0.9 A ở +20 / −20 °C (đọc 2026-11-10).
- Energizer, *Energizer 123 Product Datasheet* (form 123GL1018): https://data.energizer.com/pdfs/123.pdf — IEC CR17345, 1500 mAh tới 2.0 V, tối đa 1500 mA liên tục / 3500 mA xung, −40…+60 °C, có PTC bên trong (đọc 2026-11-10).
- MYOUNG, bản vẽ MY-CP-0398 (BH-123A-A1CJ002), datasheet LCSC C5290177 (đọc 2026-11-11): chỉ dùng làm ví dụ đế pin đặt ngoài bo và để tính khung vuông.
- JLCPCB parts search cho C883122 (BHFUSE BSMD1206-050-6V): ảnh chụp 2026-11-11 02:15 UTC.
- Espressif, *ESP32-H2 Hardware Design Guidelines*, mục "Positioning a Module on a Base Board" (như `docs/wroom_variant.md`).
