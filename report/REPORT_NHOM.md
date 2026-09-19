# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** 38
**Thành viên:**
- Nguyễn Mai Hoàng Thiện
- Nguyễn Tiến Đạt
- [Bùi Hoàng Anh]

**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân mỗi thành viên nộp riêng. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ và quy định ký túc xá sinh viên.

**Tại sao nhóm chọn chủ đề này?**

> Nhóm chọn “ký túc xá sinh viên” vì đây là một mảng dịch vụ đại học quen thuộc, có nhiều văn bản công khai từ các trường đại học Việt Nam. Dữ liệu gồm nhiều loại câu hỏi thực tế: đăng ký ở nội trú, lệ phí, số chỗ, cơ sở vật chất, điện nước và đối tượng ưu tiên. Điều này tạo đủ độ đa dạng để so sánh các chiến lược chunking và metadata filter.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|--------------------|-----------------------|----------|-----------------|
| 1 | Mức thu ký túc xá PTIT cơ sở miền Bắc 2024-2025 | https://ptit.edu.vn/thong-bao-quyet-dinh-ban-hanh-muc-thu-ky-tuc-xa-tai-co-so-mien-bac-nam-2024-2025/ | 2026-09-19 / 2024-08-23 | 871 | audience=student, department=student-dormitory, category=dormitory-fees, language=vi |
| 2 | Hướng dẫn đăng ký nội trú HUCE kỳ I 2026-2027 | https://ktx.huce.edu.vn/ban-quan-ly-ky-tuc-xa-huong-dan-dk-o-noi-tru-hoc-ky-i-nam-hoc-2026-2027 | 2026-09-19 / 2026-08-17 | 3170 | audience=student, department=dormitory-management, category=dormitory-registration, language=vi |
| 3 | Bố trí chỗ ở nội trú cho SV khóa 2025 PTIT | https://ptit.edu.vn/thong-bao-ve-viec-bo-tri-sinh-vien-khoa-2025-noi-tru-o-cac-ky-tuc-xa-tai-co-so-dao-tao-ha-noi/ | 2026-09-19 / 2025-08-26 | 3496 | audience=student, department=student-dormitory, category=dormitory-registration, language=vi |
| 4 | Ban quản lý KTX ĐH Xây dựng Hà Nội | https://ktx.huce.edu.vn/ | 2026-09-19 / not-stated | 510 | audience=all, department=dormitory-management, category=dormitory-overview, language=vi |
| 5 | KTX ĐH Bách khoa Hà Nội | https://hust.edu.vn/vi/sinh-vien/sinh-vien-hien-tai/ky-tuc-xa-51010.html | 2026-09-19 / 2016-07-10 | 1422 | audience=student, department=student-support, category=dormitory-overview, language=vi |
| 6 | Điều chỉnh giá điện nước Khu nội trú SV | https://kntsv.tmu.edu.vn/van-ban-quan-ly/dieu-chinh-muc-gia-dien-nuoc-tai-khu-noi-tru-sinh-vien-1429 | 2026-09-19 / 2024-08-05 | 536 | audience=student, department=student-dormitory, category=dormitory-fees, language=vi |
| 7 | Cách thức đăng ký KTX cơ sở Hà Nội TMU | https://kntsv.tmu.edu.vn/tin-tuc/chi-tiet/cach-thuc-dang-ky-o-ky-tuc-xa-co-so-ha-noi-23232 | 2026-09-19 / 2023-08-25 | 1360 | audience=student, department=student-dormitory, category=dormitory-registration, language=vi |
| 8 | Khu Nội trú SV Trường ĐH Thương mại | https://kntsv.tmu.edu.vn/ | 2026-09-19 / not-stated | 672 | audience=all, department=student-dormitory, category=dormitory-overview, language=vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**

- [x] Corpus chỉ chứa nguồn công khai/được phép dùng; không chứa dữ liệu cá nhân, thông tin đăng nhập hay tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc `not-stated`).
- [x] `audience` có ít nhất 2 giá trị khác nhau: `student` và `all`.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `dorm-registration` | Xác định file gốc cho mỗi chunk; hỗ trợ `delete_document` và truy vết nguồn |
| `audience` | enum | `student`, `all` | Cho phép `search_with_filter()` loại tài liệu không thuộc đối tượng người hỏi |
| `department` | string | `dormitory-management`, `student-support` | Phân biệt đơn vị quản lý/loại dịch vụ |
| `category` | string | `dormitory-registration`, `dormitory-fees`, `dormitory-overview` | Lọc câu hỏi theo nhóm quy trình, phí hoặc tổng quan |
| `source_url` | string | URL trang nguồn | Truy vết bằng chứng và kiểm tra độ tin cậy |
| `retrieved_at` | date | `2026-09-19` | Kiểm tra độ mới của dữ liệu |
| `document_version` | string | `2026-08-17` / `not-stated` | Biết văn bản đang được so với phiên bản nào |
| `language` | string | `vi` | Lọc nếu sau này bổ sung tài liệu tiếng Anh |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử một chiến lược khác nhau trên cùng bộ dữ liệu `data/dorms`. Các số liệu được đo trên **phần thân tài liệu**, không tính YAML front matter.

### Phân tích đường cơ sở (Baseline Analysis)

Kết quả `ChunkingStrategyComparator().compare()` với `chunk_size=500` trên 3 tài liệu dài:

| Tài liệu | Chiến lược | Số lượng chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|------------|---------------:|------------------:|---------------------------|
| dorm-registration | FixedSizeChunker | 7 | 495.7 | Có, nhưng dễ ghép nhiều ý khác nhau |
| dorm-registration | SentenceChunker | 26 | 120.5 | Giữ ranh giới câu, nhưng chunk ngắn |
| dorm-registration | RecursiveChunker | 26 | 120.0 | Giữ ranh giới câu/dòng, vẫn nhiều chunk |
| dorm-slot | FixedSizeChunker | 8 | 480.8 | Trung bình |
| dorm-slot | SentenceChunker | 25 | 138.5 | Tốt theo câu |
| dorm-slot | RecursiveChunker | 32 | 107.6 | Nhiều mảnh nhỏ hơn |
| hust-dormitory-overview | FixedSizeChunker | 4 | 393.0 | Trung bình |
| hust-dormitory-overview | SentenceChunker | 8 | 176.2 | Khá tốt |
| hust-dormitory-overview | RecursiveChunker | 10 | 140.4 | Khá tốt, nhưng mảnh ngắn hơn |

> Nhận xét baseline: `FixedSizeChunker` có chunk dài và ít context mất mát nhất, nhưng dễ gộp nhiều thông tin không liên quan. `SentenceChunker` giữ câu rõ ràng, phù hợp tài liệu quy trình; `RecursiveChunker` tách theo dòng/đoạn, giúp bảo toàn cấu trúc nhưng tạo nhiều chunk nhỏ.

### Chiến lược của từng thành viên

> Các dòng chiến lược dưới đây là tổng hợp từ báo cáo và `bench.py`; chỗ đánh dấu `cần xác nhận` là giả định nếu thành viên đã chỉnh khác trong máy mình.

**Thành viên 1 — Nguyễn Mai Hoàng Thiện**

- Loại chiến lược: FixedSize / theo kích thước cố định `cần xác nhận`.
- Mô tả & lý do: Dùng chunk có độ dài đều, giúp dễ kiểm soát kích thước ngữ cảnh. Phù hợp tài liệu dài, ít bị đứt quá nhiều đoạn, nhưng có thể lẫn thông tin giữa các mục.
- Điểm mạnh: Ít chunk, khả năng bao phủ ngữ cảnh cao, ngưỡng embedding ổn định.
- Điểm yếu: Không bám theo ranh giới mục/câu, dễ lấy cả phần thông tin thừa.

**Thành viên 2 — Nguyễn Tiến Đạt**

- Loại chiến lược: Recursive / theo cấu trúc đoạn `cần xác nhận`.
- Mô tả & lý do: Thử tách theo paragraph/newline/câu trước, sau đó mới cắt cứng; phù hợp Markdown quy định có nhiều mục, giữ mối quan hệ ngữ cảnh giữa heading và nội dung.
- Điểm mạnh: Chunk mạch lạc theo cấu trúc, ít cắt ngang giữa câu.
- Điểm yếu: Có thể tạo nhiều chunk nhỏ, cần gom mảnh để tránh retrieval nhiễu.

**Thành viên 3 — [Bùi Hoàng Anh]**

- Loại chiến lược: `SentenceChunker(max_sentences_per_chunk=2)`.
- Mô tả & lý do: Nhóm tối đa 2 câu mỗi chunk, giữ trọn ranh giới câu và dấu câu. Phù hợp các văn bản hướng dẫn đăng ký và thông báo.
- Điểm mạnh: Rất mạch lạc với câu hỏi quy trình; dễ đọc kết quả.
- Điểm yếu: Với tài liệu ngắn dạng mục, thông tin số liệu có thể bị tách rời, không lọt top-3 như failure case Q4.

### So sánh giữa các thành viên

| Thành viên | Chiến lược | Điểm truy xuất ước tính (/10) | Điểm mạnh | Điểm yếu |
|-----------|------------|----------------:|-----------|----------|
| Nguyễn Mai Hoàng Thiện | FixedSize | 9 | Ngữ cảnh dài, bao phủ tốt nhiều câu hỏi | Lẫn thông tin thừa |
| Nguyễn Tiến Đạt | Recursive | 9 | Giữ cấu trúc đoạn/câu, mạch lạc | Có thể nhiều chunk nhỏ |
| [Thành viên 3] | Sentence max=2 | 7 | Rất rõ ràng theo câu | Sai section khi câu đáp án đứng riêng |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**

> Nhóm đánh giá `RecursiveChunker` là cân bằng nhất với corpus ký túc xá vì nó vừa giữ ranh giới câu/đoạn vừa tránh cắt cụt giữa chừng. `SentenceChunker` mạnh với câu quy trình nhưng cần chú ý tham số; `FixedSizeChunker` dễ dùng nhưng ít tận dụng cấu trúc markdown nên có thể đưa phần mục sai vào top-k.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Gold Answer

| # | Câu hỏi | Gold Answer | Chunk chứa thông tin |
|---|---------|-------------|----------------------|
| 1 | KTX ĐH Bách khoa Hà Nội có bao nhiêu dãy nhà, bao nhiêu phòng và đón khoảng bao nhiêu sinh viên? | 10 dãy nhà, 435 phòng, khoảng 4.200 sinh viên | `hust-dormitory-overview#0/#1` |
| 2 | Cơ sở vật chất và lệ phí nhà X1, X2 cho tân SV K71 HUCE? | X1 không điều hòa/nóng lạnh, 2.700.000đ; X2 có điều hòa/nóng lạnh, 3.950.000đ | `dorm-registration#2` |
| 3 | PTIT bố trí bao nhiêu chỗ ở KTX B1, B2 và Ngọc Trục cho SV khóa 2025? | B1 40, B2 460, Ngọc Trục 340 | `dorm-slot#1` |
| 4 | SV ĐH Thương mại đăng ký KTX cơ sở Hà Nội theo quy trình và thời hạn nào? | Đăng ký qua biểu mẫu Google; hạn 25/08/2023–30/08/2023; SV đủ điều kiện nhận tin nhắn xác nhận | `tmu-dormitory-registration-hanoi#0` |
| 5 | Giá điện nước khu nội trú được ban hành ngày nào, file đính kèm tên gì? | Ban hành 05/08/2024; file `dieu-chinh-gia-dien-nuoc-kntpdf-1727328575.pdf` | `tmu-dormitory-electric-water-fees#0/#1` |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|--------------------|-------------------------------|---------|
| 1 | Thống kê KTX Bách Khoa | FixedSize / Recursive | Có | Số liệu 10 dãy, 435 phòng nằm trong top context |
| 2 | CSV+phí HUCE X1/X2 | Recursive | Có | Recursive tránh lấy nhầm context HUST nhờ ranh giới mục |
| 3 | Số chỗ PTIT B1/B2/Ngọc Trục | Sentence | Có | Chi tiết B1/B2/Ngọc Trục có trong top-3 |
| 4 | Quy trình đăng ký TMU | Recursive / Sentence | Có | `audience=student` giúp loại tài liệu overview |
| 5 | Ngày ban hành giá điện nước | Sentence | Có | Câu ngày và file đính kèm nằm gần nhau |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**

> Có. Câu 4 về đăng ký ký túc xá là ví dụ điển hình: lọc `audience=student` giúp loại các tài liệu overview với `audience=all`, từ đó top-3 bám sát các văn bản hướng dẫn dành cho sinh viên. Nếu không lọc, retrieval có thể trả thêm trang tổng quan chung của trường, làm loãng ngữ cảnh.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

### Những insight hay nhất nhóm sẽ trình bày

- Tài liệu quy định nên gắn metadata `audience` và `category`; chỉ cần một field hợp lý cũng cải thiện rõ độ chính xác.
- Điểm tương tự dựa trên chunk khác nhau nhiều giữa `FixedSize`, `Sentence` và `Recursive`; cùng query nhưng cách chia chunk quyết định top-k.
- Chỉ nhìn `doc_id` trong top-3 là chưa đủ; phải kiểm tra nội dung chứa đáp án thật.

### Bài học rút ra khi so sánh trong nhóm

> Dùng cùng `data/dorms` và cùng 5 query, nhưng mỗi strategy lại tạo số chunk, độ dài trung bình và ranh giới context khác nhau. `FixedSize` thường giữ nhiều ngữ cảnh nhưng dễ nhiễu; `Sentence` rõ ràng theo câu; `Recursive` khai thác cấu trúc tốt hơn. Vì vậy, không có strategy đúng tuyệt đối, mà phải chọn theo kiểu tài liệu và loại câu hỏi.

### Nếu làm lại, nhóm sẽ thay đổi gì?

> Nhóm sẽ tách thêm metadata theo từng trường/đối tượng rõ hơn, tăng `chunk_size`/`max_sentences_per_chunk` để giảm chunk quá ngắn, và thiết kế ít nhất một `CustomChunker` theo heading để lợi dụng cấu trúc `## Cơ sở vật chất`, `## Lệ phí`, `## Quy trình đăng ký`. Đồng thời nhóm sẽ ghi rõ backend benchmark để tránh nhầm kết quả mock với semantic embedding.

---

## Tự đánh giá (Phần nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu | 10 / 10 |
| Thiết kế chiến lược | 14 / 15 |
| Chất lượng truy xuất | 9 / 10 |
| Thuyết trình | 5 / 5 |
| **Tổng phần nhóm** | **38 / 40** |