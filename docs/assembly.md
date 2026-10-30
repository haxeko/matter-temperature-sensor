# Sản xuất và lắp ráp — TH-SENSOR-H2 Rev B

**Không có gì đã được đặt hàng.** Mọi file ở `hardware/production/` được sinh từ board bằng `hardware/scripts/gen_production.py` (ĐÃ XÁC MINH là sinh được và DRC sạch); việc nhà máy chấp nhận file và kết quả lắp ráp là **CHƯA KIỂM THỬ**.

## 1. File đầu ra

| File | Nội dung |
|---|---|
| `th_sensor_h2_revB_gerbers.zip` | Gerber X2 (F/B Cu, Mask, Paste, Silkscreen, Edge.Cuts) + Excellon PTH/NPTH; gốc tọa độ = góc dưới-trái bo |
| `gerbers/*-drl_map.pdf` | bản đồ lỗ khoan |
| `bom_jlc.csv` | BOM theo định dạng JLC (Comment, Designator, Footprint, LCSC Part #) kèm hãng, MPN, Basic/Extended, tồn kho và thời điểm tra |
| `cpl_jlc.csv` | CPL (Designator, Mid X, Mid Y, Layer, Rotation), mm, gốc góc dưới-trái, Y hướng lên |
| `orientation_check.md` | chân 1 / cực tính của từng linh kiện có cực tính, để đối chiếu trong bản xem trước của JLC |
| `assembly_top.pdf` | bản vẽ lớp Fab có đủ ký hiệu linh kiện (20 ký hiệu không có trên silkscreen) và số TP của test pad (silkscreen ghi tên net) |
| `manufacturing_blockers.md` | trở ngại và các kiểm tra cần người làm |
| `jlc_parts_snapshot.jsonl` | dữ liệu tra JLC ngày 2026-10-30 06:47 UTC |

Tra lại tồn kho trước khi đặt: `python3 tools/jlc_lookup.py --json <mã LCSC...> > hardware/production/jlc_parts_snapshot.jsonl`, rồi chạy lại `gen_production.py`.

## 2. Thông số PCB đề nghị

Bo 41.5 × 57.5 mm, 2 lớp, FR-4, 1.6 mm, đồng 1 oz, mặt nạ xanh/đen tùy ý, **via được phủ (tented)** — đã đặt trong file board, HASL không chì hoặc ENIG (ENIG phẳng hơn cho WSON 0.5 mm và DFN của SHT40). Đường cắt viền có một rãnh khoét 17.2 × 6 mm cạnh anten và một rãnh 1 mm hình chữ L nối từ rãnh đó, tạo "lưỡi" cho SHT40: phay (routing), **không V-cut**. Góc trong của rãnh sẽ có bán kính dao phay (~0.5 mm), không ảnh hưởng chức năng.

## 3. Trở ngại hiện tại

1. **ESP32-H2-MINI-1-H4S (U4, C47967030): JLC tồn kho 0** (tra 2026-10-29 và 2026-10-30). Lựa chọn:
   - JLC Global Sourcing / gửi linh kiện (consigned) rồi để JLC lắp toàn bộ;
   - hoặc đặt JLC lắp mọi thứ trừ U4 (đánh dấu U4 "Do not place" trong bước BOM của JLC), rồi hàn U4 bằng tay (mục 5).
2. Holder BS-24-B4AA016 (BT1) tồn kho 660, TPS3839K33 (U3) 844 — đủ cho lô nhỏ, kiểm lại trước khi đặt.
3. **Footprint holder BT1 là footprint của dự án** (vẽ theo bản vẽ MY-CP-0138 trong datasheet LCSC: hai pad 3.62 × 4.50 mm, tâm cách nhau 33.37 mm, pad 1 = + ở bên phải). Trước khi đặt PCB, in bản vẽ lắp ráp 1:1 hoặc đặt một holder thật lên bản in để so pad và hướng cực +.
4. Các linh kiện Extended (phí setup mỗi loại): xem `manufacturing_blockers.md`.

## 4. Kiểm tra trong bản xem trước của JLC (bắt buộc)

Góc xoay trong CPL là góc của KiCad. Mô hình linh kiện của JLC không phải lúc nào cũng cùng hướng 0°, nên **mọi linh kiện có cực tính phải được so** với `orientation_check.md`, đặc biệt:

| Linh kiện | Cần thấy trong preview |
|---|---|
| BT1 (MYOUNG BS-24-B4AA016) | tiếp điểm + của holder nằm ở pad **phải** (pad 1), trùng dấu "+" trên silkscreen |
| C5 (470 µF điện phân) | cực + hướng **lên** (về phía bộ chuyển đổi); vạch đánh dấu cực − trên vỏ ở phía dưới |
| D3 (LED 0603) | cathode hướng **xuống** |
| Q1, Q3 (SOT-23) | chân 1 (gate) đúng góc trong bảng |
| U1 (TPS63900 WSON-10) | chấm chân 1 ở góc **trên-phải** |
| U3 (TPS3839, SOT-23) | chân 1 trên-trái |
| U4 (module) | anten ở phía **trên**, sát rãnh khoét |
| U5 (SHT40 DFN-4) | chân 1 theo bảng; DFN rất nhỏ, kiểm kỹ |

Nếu preview sai, sửa góc trong công cụ của JLC và ghi lại vào `orientation_check.md`. Không sửa trong KiCad (sẽ làm lệch các lần xuất sau).

## 5. Lắp tay / làm lại

- **Thứ tự**: linh kiện thấp trước (0603/0805, WSON, SOT-23, SHT40), sau đó U4, cuối cùng nút bấm, tụ điện phân C5 và holder.
- **TPS63900 (WSON-10, pad tản nhiệt)**: dùng stencil hoặc bôi kem mỏng; khí nóng 300–330 °C; kiểm cầu thiếc giữa các chân 0.5 mm bằng kính lúp. Không có via trong pad tản nhiệt; pad nối GND qua đồng bề mặt và via cạnh C4.
- **Module ESP32-H2-MINI-1**: có pad GND lớn ở giữa (3 × 3 ô). Hàn bằng khí nóng/bếp gia nhiệt với kem trên pad; hàn mỏ chỉ các pad viền thì pad giữa không được nối — **không chấp nhận được** (GND và tản nhiệt). Dưới module có 4 via GND giữa các ô pad, đã phủ mặt nạ.
- **SHT40**: datasheet SHT4x v7.3 yêu cầu quy trình reflow, rửa bo và làm sạch theo tài liệu "Handling Instructions SHT" của Sensirion (đọc tài liệu đó trước khi lắp); hơi dung môi, băng keo, keo dán gần cảm biến làm tăng trôi số đo ẩm. Sau khi hàn, để ổn định ở điều kiện phòng trước khi so đo.
- **Holder BS-24**: hàn chắc hai tab (lực cắm/tháo cell tác dụng lên chúng); kiểm cực + theo silkscreen và T-08.
- **C5**: tụ điện phân có cực; lắp ngược sẽ rò lớn, làm cạn pin và hỏng tụ.
- **Không lắp**: J1 (pad debug), test pad và fiducial không có linh kiện.

## 6. Cấp nguồn lần đầu

Theo đúng thứ tự `docs/test_plan.md` mục A (T-01…T-08) **trước khi** lắp pin: kiểm ngắn mạch, tháo R21, cấp nguồn bench có giới hạn dòng vào TP1 (VBAT), đo VOUT, kiểm chống ngược cực và dòng ngược, kiểm holder bằng một cell. Chỉ hàn lại R21 và lắp pin khi các bước đó đạt. Không bao giờ cấp nguồn bench khi pin đang nằm trong holder.

## 7. Link đo dòng

| Link | Dòng đo được | Cách dùng |
|---|---|---|
| R1 (0R 0805) | dòng cell | tháo R1, hàn hai dây từ hai pad tới máy đo dòng |
| R21 | dòng tải 3V3 (module, SHT40, LED, supervisor) | như trên; đây là điểm đo dòng ngủ |

Khi đo dòng ngủ: rút USB (USB-Serial/JTAG giữ chip thức có chủ đích), tắt LED nếu cần (`config set led 0`).
