# Dàn bài — "Luận giải Vận trình năm {YYYY}" (theo Bát Tự)
**Sản phẩm: bài thường niên, mua một lần (ritual đầu năm/Tết).**
Khung kỹ thuật đúng: **Lưu niên (vận năm) + Lưu nguyệt (vận tháng) + Lưu nhật (vận ngày, cho lịch)**, đặt trên nền **Đại vận** đang chạy.
Version: v1.1 (annual — chuẩn thuật ngữ Bát Tự) · Đọc cùng: `tieu-van-thang-outline-v2.md` (bản monthly) · FE: `fe-van-trinh-nam.md` · API: `api-spec.md` § `GET /v1/luu-nien/luan-context`.

---

## 0. Thuật ngữ Bát Tự (chuẩn — dùng nhất quán cả portfolio)

Phân tầng vận trong Bát Tự / Tử Bình, lớn → nhỏ:

| Tầng | Thuật ngữ đúng | Chu kỳ | Vai trò trong bài |
|---|---|---|---|
| Lá số gốc | **Nguyên cục / bản mệnh** | cố định | nền so sánh (A·2, D) |
| 大運 | **Đại vận** | 10 năm | bối cảnh lớn (A·2, D) |
| 流年 | **Lưu niên** | 1 năm | chủ đề năm + 4 khía cạnh (Phần A) |
| 流月 | **Lưu nguyệt** | 1 tháng | từng tháng (Phần B) |
| 流日 | **Lưu nhật** | 1 ngày | lịch ngày tốt/xấu (B·b3) |

**Hai từ phải loại (sai hệ — đây là chỗ power-user bắt lỗi):**
- ✗ **"Tiểu hạn" (小限)** — thuật ngữ **Tử Vi Đẩu Số**, không thuộc Bát Tự. Vận năm Bát Tự gọi đúng là **Lưu niên**.
- ✗ **"Tiểu vận" (小運)** — trong Bát Tự là **vận-theo-tuổi** (thứ yếu, dùng cho giai đoạn trước khởi đại vận đầu); KHÁC lưu niên. Không dùng làm tên cho bài vận năm.

> **Trade-off & cách giữ cả hai:** "lưu niên/lưu nguyệt" ít được dân thường search hơn "xem tiểu hạn / vận năm". Xử lý: **tên & nội dung dùng từ vừa đúng vừa dễ hiểu** ("Vận trình năm", "vận tháng", "ngày tốt" — *diễn nôm, không sai hệ*); thuật ngữ Bát Tự đúng (Lưu niên/Lưu nguyệt/Lưu nhật/Đại vận) đặt ở **header mục + `mechanics`**; còn "tiểu hạn/tiểu vận/xem vận năm" chỉ để ở **SEO keyword/meta**, KHÔNG vào header hay lời hứa thương hiệu. Trang vẫn rank cho truy vấn dân gian mà bài không dùng sai một chữ.

---

## 1. Trục thiết kế: Năm (tổng hợp) → Tháng (nhịp) → Chiều sâu (gập)

Khác bản monthly (mở bằng hook cảm xúc của *một* tháng), bản năm mở bằng **bức tranh năm** rồi mới bổ xuống tháng:

1. **Phần A — NĂM:** chạm cảm xúc → chủ đề năm (tiểu hạn) → 4 khía cạnh **luận sâu MỘT lần**.
2. **Phần B — 12 THÁNG:** nhịp năm; mỗi tháng **không lặp đủ 4 mảng**, chỉ nói *mảng nào sống dậy* + lịch ngày cụ thể (moat).
3. **Phần C — KẾT:** 3 xu hướng + câu mang theo.

Nguyên tắc chống lặp (xương sống của giá trị bài năm): **4 khía cạnh nằm ở cấp năm; cấp tháng chỉ nói cái DỊCH CHUYỂN so với nền năm đó.** Nói "tháng này KHÁC năm chung ở đâu", không kể lại 4 mảng 12 lần.

---

## 2. Prompt rules toàn cục (kế thừa v2 + bổ sung annual)

| # | Rule |
|---|------|
| G1 | Hook & diễn giải phải cụ thể từ lá số thật. Cấm câu Barnum. |
| G2 | Mọi cảnh báo BẮT BUỘC kèm ≥1 hành động hóa giải. Không doom trần trụi. |
| G3a | **Thuật ngữ khung** (Lưu niên, Lưu nguyệt, Lưu nhật, Đại vận, Bát Tự): dùng ĐÚNG ở header/cấu trúc — đây là phần tạo uy tín "đúng nghề". |
| G3b | **Thuật ngữ luận sâu** (tên Thập Thần, cường nhược, Dụng/Kỵ/Hỷ Thần, cơ chế ngũ hành): CHỈ trong `mechanics`. Phần A–B diễn giải bằng ngôn ngữ đời sống. |
| G4 | Chủ đề năm & chủ đề tháng = ngôn ngữ người, không phải tên Thập Thần. |
| G5 | Mọi lời khuyên không trái Dụng/Hỷ Thần; không đẩy Kỵ Thần. |
| G6 | Không thay tư vấn y tế/pháp lý/tài chính. Disclaimer 1 dòng. |
| G7 | Không có tín hiệu rõ → KHÔNG bịa cho đủ mục. Thà ngắn còn hơn loãng. |
| G8 | Tông: hào phóng, gần gũi, cố vấn tin cậy. Không transactional, không hù dọa, không tâng bốc. |
| **A1** | **4 khía cạnh chỉ luận sâu Ở CẤP NĂM. Cấp tháng chỉ nhắc khi tháng đó có dịch chuyển rõ.** |
| **A2** | **Mỗi tháng nêu emphasis 1–2 mảng (ranked), KHÔNG dàn đủ 4.** Mảng neutral → bỏ. |
| **A3** | **Giọng/độ dài 12 tháng phải đều. Cấm nhạt dần từ tháng 8.** (QA bắt buộc — mục 5.) |

---

## PHẦN A — NĂM

### A·1 — `hook_year` · Mở chạm + Chủ đề năm (Lưu niên)
**Editorial:** 1–2 câu phản chiếu trạng thái năm + 1 câu chủ đề năm bằng ngôn ngữ đời sống. Đây là "câu để nhớ cả năm".

| Lấy từ engine | → Output |
|---|---|
| `opening_context.year_theme_vi`, `year_rating` | `year_theme_line` (≤22 từ, ngôn ngữ người) |
| `opening_context.year_can_chi` | nền ẩn, không hiện tên Can Chi ở câu mở |
| `natal` tổng hợp (signal năm) | `hook_body` 2–3 câu |

> Ví dụ `year_theme_line`: *"Năm củng cố gốc rễ — chưa phải năm bung ra, mà là năm xây cho chắc thứ mình đã có."* (KHÔNG: "năm Bính Ngọ, Thương Quan vượng".)

### A·2 — `you_this_year` · Bạn trong năm này (NÉN — phần tĩnh)
**Editorial:** 2–3 câu nối lá số với năm. **Đây là phần dễ lặp mỗi năm → giữ rất ngắn.** Chi tiết Nhật chủ/Dụng Thần đẩy hết xuống `mechanics`.

| Lấy từ engine | → Output |
|---|---|
| `natal.nhat_chu`, `chart_strength` (chỉ ý, không thuật ngữ) | 1 câu "bạn là người…" đời thường |
| `dai_van_current.display`, `relation_to_dung_than_vi` | 1 câu "giai đoạn lớn đang…" |

> Cảnh báo retention: nếu sản phẩm bán lại mỗi năm, đây là khối mòn nhất → **mỗi năm phải nối nó vào chủ đề năm khác nhau**, không copy nguyên.

### A·3 — `four_aspects_year` · Bốn khía cạnh trong năm  ★ TRỌNG TÂM PHẦN A
**Editorial:** luận **SÂU, MỘT LẦN** cho cả năm. Đây là nơi 4 mảng được trải đủ — để cấp tháng khỏi lặp. Mỗi mảng: 1 câu verdict + 2–4 câu cụ thể + cửa sổ thời gian (quý/tháng) nếu engine có tín hiệu.

| Mảng | Lấy từ engine | Trọng tâm luận |
|---|---|---|
| **Sự nghiệp** | thập thần trội năm (`natal.dominant_thap_than`) + relation năm ↔ Nhật chủ | thăng tiến / ký kết / đổi việc; quý hay nửa năm nào mạnh |
| **Tài chính** | relation hành năm ↔ Dụng/Kỵ Thần | tích lũy hay phòng thủ; cảnh báo đầu cơ (kèm G2) |
| **Tình cảm** | chi năm xung/hợp tuổi (nếu có) + `quy_nhan` | hòa hợp / va chạm; người trợ duyên |
| **Sức khỏe** | hành năm = Kỵ/Dụng Thần | điểm dễ hao; nhịp nghỉ (kèm disclaimer G6) |

**Rule riêng A·3:**
- Vẫn **xếp hạng**: mảng nào năm thực sự dồn năng lượng nói trước & dài hơn; mảng êm 1–2 câu (đừng cắt hẳn ở cấp năm — người mua bài năm kỳ vọng thấy đủ 4, đây là ngoại lệ có chủ đích so với rule A2 ở cấp tháng).
- Mỗi mảng gắn **mốc thời gian** ("nửa cuối năm…", "khoảng tháng 7–9…") để tạo cầu nối xuống Phần B.

---

## PHẦN B — 12 THÁNG

### B·0 — Nguyên tắc nhịp
Mỗi tháng là một **biến tấu trên nền năm**, không phải bài độc lập. Khung mỗi tháng **gọn**, gồm 4 thành phần — bỏ thành phần nào không có tín hiệu:

### B·n — `month[n]` (lặp 12, cùng khung)

| Thành phần | Editorial | Lấy từ engine | Rule |
|---|---|---|---|
| **b1. Chủ đề tháng** | 1 câu ngôn ngữ người | `flow_month` → `month_archetype` (nâng đỡ/gieo hạt/thu hoạch/phòng thủ/chuyển động) | G4 |
| **b2. Mảng sống dậy** | 1–2 mảng nổi bật tháng + tháng KHÁC nền năm ở đâu | `subsections.*.signal` + `month_emphasis` (ranked ≤2) | **A1, A2** — KHÔNG đủ 4 mảng |
| **b3. Lịch ngày** ★ (Lưu nhật) | 3 ngày vàng + 3 ngày hạn + giờ đẹp lặp nhiều | `calendar_month.best_days[3]`, `avoid_days[3]`, `top_hours` | G2 (ngày hạn kèm gợi ý), date_vi có thứ+ngày |
| **b4. Nên / Tránh** | 2 nên, 2 tránh, dứt khoát | `lich_khuyen_nghi.nen_lam_vi[]`, `tranh_vi[]` | G5 |

> **b3 là moat của bài năm** — concrete, có ngày thật, ChatGPT không tính đúng. Đây là lý do bài năm "đáng tiền" hơn một bài chung chung. Mỗi tháng phải có lịch, kể cả tháng êm.

**Độ dài mục tiêu mỗi tháng:** ~80–120 từ. Tháng có signal mạnh được dài hơn tháng êm — nhưng **không tháng nào dưới 60 từ** (tránh cảm giác bị bỏ rơi) và **không tháng nào quá 150** (tránh phình + nhạt).

---

## PHẦN C — KẾT

### C·1 — `closing_year`
| Thành phần | Editorial | Lấy từ engine |
|---|---|---|
| **3 xu hướng năm** | LLM tổng hợp từ 12 tháng (không field riêng) | synthesis trên `months[]` |
| **Câu mang theo** | ≤20 từ, nối mạch `year_theme_line` | — |
| **3 tags** | tái dùng/aggregate | `template_tags` |

---

## PHẦN D — `mechanics` · "Vì sao năm nay như vậy"  ⌄ MẶC ĐỊNH GẬP
**Editorial:** nơi DUY NHẤT chứa thuật ngữ. Cho nhóm "học trò" / muốn bằng chứng.

| Lấy từ engine | → Output |
|---|---|
| `natal`: nhat_chu, chart_strength, dung/hi/ky/cuu_than | giải thích nền |
| `dai_van_current` | đại vận đang chạy |
| `luu_nien_pillar`, `luu_nguyet_pillar` (gọi đúng tên ở đây) | khung lưu niên–lưu nguyệt |
| `dominant_thap_than` + relation | vì sao chủ đề năm như vậy, khớp A·1 |

**Rule D:** ngoại lệ G3b (thuật ngữ luận sâu được phép). Vẫn G5: giải thích phải khớp lời khuyên ở A·3/B. **1 dòng thừa nhận khung:** "Bài phân tích theo Lưu niên (vận năm), Lưu nguyệt (vận tháng) và Lưu nhật (vận ngày), trên nền Đại vận đang vận hành."

---

## 3. Bản đồ topic yêu cầu → block

| Topic bạn yêu cầu | Nằm ở |
|---|---|
| Chủ đề trọng tâm năm (vận năm) | **A·1** (hook + theme), nền kỹ thuật **Lưu niên** ở **D** |
| 4 khía cạnh (SN–TC–TàiC–SK) trong năm | **A·3** (sâu, một lần) |
| Tình hình cụ thể từng tháng | **Phần B** (12 × khung b1–b4), lịch ngày ở **b3** |

---

## 4. Kiểm soát chất lượng (QA bắt buộc trước ship)

Bài năm chết vì **lặp** và **đuôi nhạt**. Ba phép đo trên bản nháp LLM:

1. **Anti-repeat 4 mảng:** quét xem nội dung 4 khía cạnh ở A·3 có bị lặp lại nguyên ý ở các tháng không. Cấp tháng chỉ được nói *dịch chuyển*, không kể lại verdict năm.
2. **Đuôi tháng (A3 rule):** đo độ dài + độ đa dạng từ vựng tháng 1–6 vs 7–12. Nếu tháng 7–12 sụt > ~25% độ dài hoặc lặp cấu trúc câu → reject, cân nhắc **map-reduce** (gen từng tháng rồi synthesis) thay vì one mega-prompt.
3. **Barnum check:** mỗi câu hook/verdict có gắn được với 1 fact engine cụ thể không? Không → viết lại (G1).

> Vì engine cấp `month_emphasis` ranked (xem fix P1-1 trong review API), LLM dồn được chữ vào tháng mạnh và rút gọn tháng êm — đây là cơ chế kỹ thuật chống đuôi nhạt, không chỉ dặn dò.

---

## 5. Thứ tự render & độ dài (mobile-first)

| # | Block | Trạng thái | Độ dài |
|---|---|---|---|
| A·1 | hook_year + chủ đề năm | mở | 3–4 câu |
| A·2 | bạn trong năm này | mở | 2–3 câu (nén) |
| A·3 | 4 khía cạnh năm | mở | 4 mảng, mảng mạnh 4–5 câu / mảng êm 1–2 câu |
| B·1–12 | 12 tháng | mở | mỗi tháng 80–120 từ, khung b1–b4 |
| C·1 | kết | mở | 3 xu hướng + 1 câu + 3 tags |
| D | mechanics | **gập** | 1 đoạn (chỉ khi mở) |

**Phân bổ "đất":** Phần A ~25%, Phần B ~65% (đây là nơi giá trị định kỳ-cụ thể), Phần C ~10%, D ngoài luồng. **Nếu A nuốt > 35% → đang bán lại lá số thay vì bán năm.**
