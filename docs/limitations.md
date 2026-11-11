# Giới hạn đã biết và rủi ro — TH-SENSOR-H2 Rev B

Đọc tài liệu này trước khi đặt sản xuất hay dùng thiết bị.

## 1. Chưa có phần cứng thật

Không có bo nào được sản xuất, lắp ráp, cấp nguồn hay đo. Những gì đã được kiểm (ĐÃ XÁC MINH):
- firmware build sạch từ bản clone mới cho ESP32-H2: profile battery, debug và battery + lớp phủ prod (`docs/reports/firmware_build.md`);
- chuỗi script phần cứng tái tạo schematic và board giống từng byte;
- 43 unit test / 264 kiểm tra logic thuần trên máy host, 0 lỗi (`docs/reports/host_tests.txt`);
- ERC 0 lỗi 0 cảnh báo; DRC 0 vi phạm, 0 pad chưa nối, schematic parity 0 lỗi (`hardware/reports/`);
- pin map firmware ↔ schematic khớp (`tools/check_pinmap.py`).

Mọi hành vi điện, RF, cảm biến, Matter/Thread, tuổi thọ pin: **CHƯA KIỂM THỬ**.

## 2. Năng lượng: CHƯA ĐẠT

Theo mô hình (ƯỚC TÍNH, `docs/power_budget.md`), với một CR2450:
- commissioning chỉ ổn với pin mới ở nhiệt độ phòng (ở 10 °C sát giới hạn; ở 0 °C và −10 °C bị reset);
- **khởi động bị reset khi pin đã dùng khoảng một nửa**, hoặc ở ≤ 0 °C ngay cả với pin mới. Hệ quả: sau giữa đời, một lần reset bất kỳ (sụt áp, watchdog, nút RST, lỗi firmware) có thể làm thiết bị ngừng hoạt động tới khi thay pin;
- report hỏng khi pin tới trạng thái late (25 °C), hoặc giữa đời ở −10 °C;
- tuổi thọ ở ~64 µA trung bình: khoảng 0.55–0.77 năm; **không đạt 1–2 năm**;
- điện trở xung của CR2450 không có số liệu công bố: mô hình nhân điện trở CR2032 với 0.6 (tỉ lệ diện tích điện cực). Nếu thực tế gần CR2032 (× 1.0), ngay cả pin mới cũng không khởi động được theo mô hình — đây là rủi ro lớn nhất của Rev B, phải đo trước khi làm nhiều bo (T-35);
- dạng dòng khởi động là giả định (T-33).

Phương án dự phòng (chưa áp dụng, cần quyết định của người dùng): `docs/power_budget.md` mục 7. Thiết kế không tự đổi sang AAA hay loại pin khác.

## 3. Bảo vệ cell sơ cấp

Panasonic khuyến nghị diode chặn ngược **và** điện trở bảo vệ nối tiếp khi cell có thể bị nạp từ nguồn khác (Panasonic Lithium Handbook). Rev B không có nguồn nào khác trên bo: J1 không có chân nguồn, USB không cấp điện cho bo, không có Schottky hay điện trở nối tiếp. Rủi ro nạp ngược chỉ còn khi người dùng cấp nguồn bench **trong khi pin vẫn lắp** (tài liệu yêu cầu tháo pin trước): cấp vào TP1 hay VIN sẽ nạp thẳng vào cell (P-MOSFET đã mở dẫn theo cả hai chiều); cấp vào rail (VOUT/+3V3) thì chỉ còn bộ chuyển đổi chặn, vì nó không có đường dẫn ngược VOUT→VIN khi không đóng cắt (CHƯA KIỂM THỬ, T-05). Mức tuân thủ UL/IEC chưa được đánh giá; cần xem lại nếu đưa sản phẩm đi chứng nhận.

## 4. Linh kiện và sản xuất

- ESP32-H2-MINI-1-H4S: JLC tồn kho 0 (tra 2026-10-29 và 2026-10-30) — chặn lắp ráp toàn bộ tại JLC.
- Holder MYOUNG BS-24-B4AA016: footprint là footprint của dự án, vẽ theo bản vẽ MY-CP-0138 trong datasheet LCSC; **phải so với một holder thật** (kích thước pad, vị trí cực +) trước khi đặt PCB. Holder ghi dải nhiệt −25…+85 °C (LCSC); tồn kho JLC 660 khi tra.
- Tụ điện phân 470 µF: dòng rò ở 3 V chưa có số liệu (ngân sách 0–5 µA, T-39); điện dung giảm và ESR tăng khi lạnh (chưa đưa vào mô hình); tuổi thọ định mức 2000 h ở 105 °C.
- Góc xoay CPL chưa được đối chiếu với mô hình linh kiện của JLC: phải kiểm từng linh kiện có cực tính trong bản xem trước (`hardware/production/orientation_check.md`), nhất là holder và tụ điện phân.
- Tụ tải thạch anh 32 kHz (18 pF) là ước tính; phải chỉnh theo T-09.
- Điện dung hiệu dụng của tụ MLCC 100 µF 6.3 V ở 3 V chưa được tra/đo (giả định ~85 µF cho 10 µF + 2 × 100 µF).

## 5. Matter

- Bản build mặc định dùng dữ liệu thử nghiệm (VID 0xFFF1/PID 0x8000, passcode 20202021, DAC thử nghiệm): chỉ để phát triển.
- Lớp phủ sản xuất `sdkconfig.defaults.prod` build được (ĐÃ XÁC MINH) nhưng chạy **CHƯA KIỂM THỬ**; cần dữ liệu factory riêng cho từng máy và chứng nhận Matter (ngoài phạm vi).
- Chưa thử với bất kỳ hệ sinh thái thương mại nào; không giả định chúng chấp nhận firmware này.
- **OTA không được triển khai** (`CONFIG_ENABLE_OTA_REQUESTOR=n`). Cập nhật firmware chỉ qua USB/UART (J1).
- **Secure Boot V2, Flash Encryption và NVS encryption đều tắt** trong mọi profile (kể cả lớp phủ prod). Với thiết bị thật chứa DAC và passcode riêng, cần bật và kiểm thử chúng trước khi sản xuất; việc ghi eFuse **không đảo ngược được**, nên không bật thử trên bo duy nhất.
- Không có chứng nhận Matter, FCC, CE, an toàn pin nào được tuyên bố.

## 6. Cảm biến

- Hiệu quả cách nhiệt của lưỡi SHT40 và độ chính xác trên bo này chưa được đo (T-11, T-12). Lưỡi Rev B nhỏ hơn Rev A (8.7 × 12 mm so với 11 × 13 mm); SHT40 cách IC nguồn ~25 mm và mép module ~20 mm.
- Heater chỉ chạy bằng lệnh bảo trì; không có quy trình tự động chống ngưng tụ.

## 7. Đo pin

- Phần trăm pin suy ra từ điện áp theo hình dạng đường xả CR2032 của Panasonic (15 kΩ, 20 °C), dùng nguyên cho CR2450 với giả định cùng hóa học cho cùng dạng đường cong — chưa đối chiếu với đường CR2450. Chỉ mang tính chỉ báo; phụ thuộc nhiệt độ và tải.
- Điện áp đo khi chip đang thức, tức là có tải qua bộ chuyển đổi; theo mô hình, khả năng khởi động lại mất khi phần trăm còn quanh 50 % (trên ngưỡng Warning 40 %), nên BatChargeLevel không báo trước được giới hạn ở mục 2.
- Sai số ADC + dòng rò đầu vào trên cầu 235 kΩ Thevenin chưa được đo (T-13).
- Mỗi lần đo lấy hai mẫu cách nhau 1.5 s và giữ mẫu cao hơn (từ 2026-11-11). Cách này lọc được một xung phát đơn lẻ, không lọc được tải kéo dài hơn 1.5 s (commissioning, tìm lại mạng); chưa kiểm trên phần cứng (T-16e).

## 8. PCB

- Layout được sinh bằng script và router tự viết. Kết quả đạt DRC nhưng có vài đường chéo dài; một số đoạn đi trên B.Cu cắt mặt GND (+3V3, EN, VOUT, I2C_SDA và đường đo VBAT dài 32 mm qua 4 via); 9 kết nối dùng via (`hardware/reports/routing_log.txt`).
- 18 ký hiệu linh kiện chỉ có trên lớp Fab (bản vẽ `assembly_top.pdf`): 17 vì không đủ chỗ trên silkscreen, BT1 do chọn (holder đã có dấu +/− và dòng "CR2450 ONLY / NO CHARGE"). Test pad được ghi tên net thay cho số TP.
- Yêu cầu gốc nêu điểm "VBAT1/VBAT2/VBAT_OR" cho hai cell; Rev B một cell có VBAT (TP1) và VIN (TP2), không có nút OR.
- Render 3D chỉ có mô hình 3D của module; các linh kiện khác (kể cả holder) hiện là footprint trần vì gói mô hình 3D của KiCad không có trong môi trường sinh file.
- Hiệu năng anten khi lắp trong vỏ và gần cell chưa được đo; HDG khuyến nghị ≥ 15 mm khoảng trống quanh anten bên trong vỏ.

## 9. Công cụ

- Vùng đổ đồng được KiCad tính lại trong `gen_pcb.py` sau khi ghi file project cuối cùng, nên DRC kiểm đúng vùng đồng nằm trong file; kicad-cli 9.0.9 trong môi trường này không có tùy chọn `--refill-zones`.
- Tái tạo phần cứng cần KiCad 9 (pcbnew Python) với thư viện chuẩn; thư viện Espressif chỉ cần khi muốn làm mới bản sao trong `hardware/kicad/lib`.

## 10. Biến thể chip rời (H2C Rev A)

Các mục 1–9 áp dụng cho cả H2C (cùng nguồn, cảm biến, firmware). Thêm:

- **RF chưa có gì được đo hay mô phỏng.** Ăng-ten PCB (TI SWRU120D/DN007) được TI chỉnh trên FR-4 1 mm; bo này 1.6 mm, khác mặt đất, có nút và pin gần — dự đoán lệch tần, phải chỉnh bằng VNA (mạng pi C52/R41/L5 hoặc cắt nhánh ăng-ten). Giá trị C51/L4/C52 chỉ là điểm khởi đầu trong khoảng HDG. Không có VNA thì chỉ so được RSSI/LQI với bo module.
- **Không thừa hưởng chứng nhận RF của module**: datasheet ESP32-H2-MINI-1 ghi "RF certification: See certificates" cho module; một thiết kế chip rời phải tự làm toàn bộ thủ tục vô tuyến (ngoài phạm vi, không tuyên bố).
- ESP32-H2FH4S tồn kho JLC 0 (2026-11-06); mã thay thế ESP32-H2FH4 chưa được đối chiếu revision.
- 9 via trong pad đáy chip nằm trong ô kem hàn: có thể hút thiếc; QFN 0.4 mm và 0201 không hàn tay bằng mỏ được.
- Trở kháng đường RF (≈ 50 Ω), stub (≈ 100 Ω) và cặp USB (≈ 90 Ω) là kết quả công thức gần đúng, chưa qua máy tính trở kháng của JLC; đặt JLC kiểm soát trở kháng.
- Thạch anh 32 MHz: tụ tải 12 pF là ước tính (CL 9 pF theo mô tả LCSC, ký sinh ~3 pF), L3 cách chân 4–6 mm; lệch tần và biên độ chưa đo (C-01).
- Các lệch có chủ đích so với HDG v1.6: `docs/chip_variant.md` mục 4 (C46/C47 chung pad, đường nguồn 0.4 mm, USB không chừa R/C, tụ ADC 22 nF, nguồn < 350 mA).
- Đường VBAT từ cầu chia tới TP1 dài ~60 mm (chủ yếu trên L4) vì router không đi dưới đường RF; dòng qua nó chỉ là dòng cầu chia.
- 28 ký hiệu linh kiện chỉ có trên lớp Fab; render 3D không có mô hình chip.

## 11. Biến thể WROOM-02C (H2W Rev A)

Các mục 1–9 áp dụng cho cả H2W (cùng nguồn, cảm biến, firmware). Thêm:

- **Module do người dùng tự mua và hàn** (không có trong BOM/CPL). Footprint và symbol vẽ theo datasheet v1.2, **chưa so với module thật**; in footprint 1:1 đặt module lên kiểm trước khi đặt PCB. Pad tản nhiệt chỉ hàn được qua lỗ 0.8 mm từ mặt dưới; miếng tản nhiệt nhỏ 2.8 × 0.55 mm không hàn được bằng mỏ.
- **Via dưới pin** (mặt dưới, phủ mask): nếu mask trên vòng via bị trầy và vỏ pin (+) bị ép chạm xuống, có thể chập VBAT với GND hoặc với tín hiệu. Bản vẽ holder cho thấy pin nằm trên đáy nhựa, không chạm bo; chưa kiểm trên holder thật (W-03).
- **Pin kim loại sau mặt GND, cách ranh giới ăng-ten 6.8 mm**; ảnh hưởng tới ăng-ten của module chưa đo (W-01). HDG khuyên chừa ≥ 15 mm quanh ăng-ten bên trong vỏ — thuộc thiết kế vỏ (chưa có vỏ).
- **Lắp ráp hai mặt** (holder ở mặt dưới) hoặc tự hàn holder; xoay của linh kiện mặt dưới trong CPL phải kiểm trong bản xem trước của JLC.
- Bốn đường UART/USB đi ra từ cột chân phải của module (vào trong 1.65 mm rồi xuống In2), vì mép phải module sát mép bo; via của chúng cách ranh giới ăng-ten 7–12 mm.
- Mặt dưới in "Matter temperature Sensor / Villa Nest / Made in Vietnam" theo yêu cầu người dùng. Sản phẩm **chưa có chứng nhận Matter**; tên và logo Matter là nhãn hiệu của CSA, dùng trên sản phẩm bán ra thường đòi hỏi chứng nhận — cần kiểm chính sách của CSA trước khi bán.
- 16 ký hiệu linh kiện chỉ có trên lớp Fab; render 3D không có mô hình module.
- **C5 là tụ tantal MnO2** (TAJD477K006RNJ): datasheet chỉ cho giới hạn rò 28 µA ở 6.3 V (25 °C, sau 5 phút), ở ~3 V chưa có số liệu (T-39); datasheet không cho định mức điện áp ngược, nên tụ lắp ngược cực phải được sửa trước khi cấp điện. Giá 1.14 USD so với 0.04 USD của tụ nhôm (ảnh chụp JLC 2026-11-08), thêm một linh kiện Extended như trước.
- **Hướng lắp**: thiết kế giả định gắn tường với cạnh có SW1 quay xuống đất. Khi đó ăng-ten module nằm ngang (nhô sang bên); ảnh hưởng tới tầm phủ chưa đo (W-01). Vỏ cần lỗ thông khí ở cạnh dưới gần lưỡi cảm biến và một nút đẩy ở cạnh dưới cho SW1; độ chính xác và thời gian đáp ứng của SHT40 ở tư thế này chưa đo (W-08). Mặt sau (holder) áp vào tường, nên thay pin phải gỡ thiết bị khỏi tường.
- **Không có nút RST**: reset/vào download cần chập TP6 (EN) xuống GND hoặc tháo/lắp pin khi USB không tự reset được. SW1 bấm cạnh chỉ cao 1.35 mm, núm nhô 0.5 mm khỏi mép bo: dễ bấm nhầm khi cầm bo trần, và vỏ cần một nút đẩy đúng vị trí. J1 là pad dán: không cắm header được.

## 12. Biến thể CR123A (H2W-123 Rev A)

Các mục 1 và 3–9 áp dụng cho cả H2W-123 (cùng mạch nguồn, cảm biến, firmware); mục 2 (CR2450 "CHƯA ĐẠT") được thay bằng kết quả mô hình CR123A, vẫn là **ƯỚC TÍNH**. Các điểm của mục 11 về module tự hàn, nút bấm cạnh, không có nút RST và chữ in ở mặt sau áp dụng nguyên. Thêm:

- **Cách hiểu yêu cầu chưa được người dùng xác nhận**: pin nằm ngoài bo và nối bằng dây; bo thu xuống 24.8 × 37.3 mm; SHT40 ở góc dưới trái; J1 và test pad ở mặt sau — `docs/decisions.md` D25.
- **Pin sát bo chỉ cách module khoảng 7 mm**, và đầu trên của đế pin ngang hàng với vùng ăng-ten. Espressif khuyên chừa ≥ 15 mm quanh ăng-ten. Đây là rủi ro lớn nhất của bản này: tầm phủ có thể giảm, chưa đo (K-04). Cách sửa không cần đổi bo: đặt đế pin xa bo hơn (thiết bị khi đó không còn vuông 43.3 mm).
- **Pin, đế pin và dây không thuộc bo**: không có trong BOM, chưa chọn loại cụ thể, chưa có đế thật nào được so với bản vẽ. Bo không có chỗ kẹp dây; mối hàn dây chịu lực nếu vỏ không giữ dây. Đấu ngược cực không làm hỏng mạch nhưng phải kiểm trước khi cấp điện (K-01).
- **F1 không bảo vệ đoạn dây từ pin tới bo**: chập giữa hai dây hoặc giữa hai tiếp điểm của đế vẫn làm pin phóng hàng ampe. F1 thêm 0.15–0.7 Ω nối tiếp (số của trang JLC, chưa có datasheet đầy đủ của hãng); thời gian ngắt chưa đo (K-02).
- **J1 và test pad ở mặt sau**: nạp firmware và đo đều phải lật bo; khi bo đã gắn tường thì không tới được. Pad trần mang điện áp pin và 3.3 V nằm ở mặt áp vào tường: cần vỏ hoặc lớp cách điện.
- **Khung vuông 43.3 × 43.3 mm** chỉ đúng với một đế pin 18.2 × 43.3 mm đặt cách bo 0.3 mm; chưa có thiết kế vỏ, chưa tính chỗ cho vỏ và dây.
- **SHT40 cách bộ chuyển đổi 14 mm** (H2W-123 bản đầu: 22.5 mm). Tự sưởi chưa đo (K-08).
- **Mô hình pin CR123A** khớp theo đồ thị xả liên tục ở 20 °C của Panasonic; điện trở khi pin gần hết và khi lạnh là giả định (lấy khắt khe như pin đồng xu), không có số liệu công bố; không tính điện trở dây và tiếp điểm đế. Tuổi thọ 2.3–2.6 năm giả định dòng trung bình 63 µA chưa đo và dùng được 85–95 % dung lượng (K-03, K-06).
- **Không có C5 và không có chỗ đặt sẵn**: nếu đo thực tế cho thấy vẫn cần tụ đệm (pin hãng khác, nhiệt độ thấp, dây dài) thì phải sửa bo.
- **Phần trăm pin gần như không dùng được ở nửa trên**: đường xả CR123A phẳng, bảng điện áp → phần trăm đọc từ một đồ thị 20 mA; chỉ mức Warning/Critical ở cuối đời pin có ý nghĩa, và các ngưỡng 20 % / 8 % / 2500 mV / 2200 mV là ƯỚC TÍNH (K-05). Ngưỡng nhận ra pin mới của power guard (3000 mV) cũng chưa kiểm với CR123A: nếu pin mới đọc thấp hơn, bộ đếm không tự xóa và phải bấm nút để đánh thức sau khi thay pin.
- 17 ký hiệu linh kiện mặt trên chỉ có trên lớp Fab; render 3D không có mô hình module.

## 13. Các điểm của bản đánh giá ngày 2026-11-10 chưa xử lý

Người dùng chọn sửa bốn lỗi firmware (D23) và làm biến thể CR123A. Những điểm sau vẫn nguyên như lúc đánh giá:

- CPL của H2W: góc xoay của BT1 ở mặt dưới lấy thẳng từ KiCad (`gen_production.py`), chưa đổi sang quy ước của JLC cho mặt dưới — phải kiểm trong bản xem trước.
- Rev B: một via nằm trong pad của R26.
- Ghi chú trong schematic H2W còn vài dòng cũ.
- GPIO9 vừa là nút USER vừa là chân strap BOOT: giữ nút khi cấp nguồn/reset ⇒ vào chế độ download, thiết bị đứng yên tới lần reset sau.
- Datasheet WROOM-02C không nhất quán về mạch RC trên EN trong module: đo điện trở EN–3V3 trên module thật trước khi quyết định giữ hay bỏ R22/C25.
- Firmware: hàm xử lý `EV_RESCHEDULE` rỗng; kết quả publish không được đưa ngược về chính sách báo cáo; profile `battery` vẫn dùng credential thử nghiệm (chỉ profile `prod` dùng dữ liệu factory); công suất phát của khung đầu tiên có thể được đặt sau khi radio đã phát.
- PCB: chữ silkscreen 0.8 mm (nhỏ hơn mức JLC khuyến nghị); H2C có chữ silkscreen bị cắt và đường XTAL_N dài 12.7 mm; `gen_reports.py` không xóa báo cáo cũ khi một bước lỗi.
