# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Khi hai vector embedding chỉ gần như cùng hướng, góc giữa chúng nhỏ. Điều này có nghĩa hai đoạn văn bản đang nói về chủ đề, ngữ nghĩa hoặc ý tưởng rất giống nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên nộp báo cáo trước thời hạn.
- Câu B: Học viên gửi bài thu hoạch trước ngày cuối cùng.
- Tại sao tương đồng: cả hai cùng nói về việc hoàn thành và nộp tài liệu đúng hạn; bộ từ vựng và ý nghĩa gần nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Sinh viên nộp báo cáo trước thời hạn.
- Câu B: Món phở bò nóng hổi được bày ra bàn.
- Tại sao khác: chủ đề hoàn toàn khác (học tập và ẩm thực), nên vector ngữ nghĩa chỉ về hai hướng khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine quan tâm đến hướng, không quan tâm đến độ lớn của vector. Với text embedding, các đoạn văn bản dài ngắn khác nhau có thể tạo vector dài hoặc ngắn nhưng vẫn cùng ý nghĩa; cosine giúp việc so sánh ít bị ảnh hưởng bởi độ dài vector, trong khi Euclid rất nhạy với magnitude.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.11) = 23.
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk tăng lên thành làm_tròn_lên((10000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = 25 chunks. Overlap lớn hơn giúp giữ lại ngữ cảnh giữa các chunk để thông tin không bị cắt ngang và câu hỏi/ý nghĩa xuyên biên giới chunk không bị mất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Em dùng regex `.+?(?:\\.\\s|!\\s|\\?\\s|\\.$|!$|\\?$|$)` với `DOTALL` để phát hiện câu, sau đó nhóm câu theo `max_sentences_per_chunk`. Em xử lý text rỗng và text không tách được câu bằng cách trim, loại phần tử rỗng và trả về danh sách an toàn.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử từng separator theo thứ tự ưu tiên; nếu đoạn text dài hơn `chunk_size`, nó đệ quy xuống separator tiếp theo. Base case là khi `len(text) <= chunk_size`, chunk rỗng, hoặc không còn separator thì dùng fallback cắt theo ký tự với `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Em chuẩn hóa mỗi `Document` thành một record với `id`, `doc_id`, `content`, `metadata` và `embedding`, sau đó lưu vào danh sách in-memory. Với `search`, em embed query rồi dùng `_search_records` để tính dot product giữa query và các record và sắp xếp giảm dần theo score.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Em lọc metadata trước khi tìm kiếm để thu hẹp danh sách cần so sánh và bảo đảm kết quả trả về luôn thỏa filter. Với `delete_document`, em giữ lại các record không thuộc `doc_id` cần xóa; nếu có record bị bỏ đi thì trả về `True`, ngược lại `False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Em dùng pattern RAG: gọi `store.search(question, top_k)` để lấy các chunk liên quan, đánh số và ghép thành khối `Context`, sau đó tạo prompt yêu cầu LLM chỉ dựa vào context để trả lời. Cuối cùng em truyền prompt vào `llm_fn` để nhận câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= 42 passed in 0.08s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Mức phí ký túc xá hiện tại là bao nhiêu? | Ký túc xá thu bao nhiêu tiền mỗi tháng? | cao | 0.712 | Đúng |
| 2 | Quy trình đăng ký ký túc xá gồm những bước nào? | Hướng dẫn cách đăng ký ở nội trú cho sinh viên. | cao | 0.722 | Đúng |
| 3 | Ký túc xá có điều hòa không? | Nhà X2 có trang bị điều hòa và bình nước nóng không? | cao | 0.653 | Đúng |
| 4 | Sân bóng rổ của ký túc xá nằm ở đâu? | Trường có mấy dãy ký túc xá và bao nhiêu phòng ở? | thấp | 0.707 | Sai |
| 5 | Hôm nay thời tiết thế nào? | Mức giá điện nước tại khu nội trú được điều chỉnh như thế nào? | rất thấp | chưa ghi được vì hết quota API | — |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Điều bất ngờ là cặp 4 tuy cách diễn đạt khá xa nhau nhưng vẫn đạt khoảng 0.707. Điều này cho thấy embedding không chỉ so khớp từ khóa mà còn ánh xạ theo ngữ cảnh; một câu hỏi về hạ tầng/sân thể thao vẫn nằm cùng chủ đề “ký túc xá, cơ sở vật chất” nên bị xếp gần. Vì vậy, nếu muốn truy xuất chính xác từng thông tin nhỏ, chỉ dựa vào similarity đôi khi chưa đủ và cần thêm metadata filter hoặc truy vấn rõ ràng hơn.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Tân sinh viên có thể đăng ký ở nội trú qua hình thức nào? | Chunk `dorm-registration`, ngữ cảnh trực tuyến/online | 0.8509 | Có | Agent tìm được hướng dẫn đăng ký online, nhưng chưa vào đúng văn bản tổng quát nhất | 
| 2 | Mức phí ở ký túc xá PTIT cơ sở miền Bắc được ban hành theo quyết định số mấy? | Chunk `dorm-charge`, mục số quyết định 1521/QĐ-HV | 0.7931 | Có | Agent trả lời chính xác 1521/QĐ-HV | 
| 3 | Ký túc xá Đại học Bách khoa Hà Nội có tổng cộng bao nhiêu phòng ở? | Chunk `hust-dormitory-overview`, mục 435 phòng | 0.7664 | Có | Agent trả lời đúng 435 phòng | 
| 4 | Văn bản điều chỉnh mức giá điện nước tại khu nội trú TMU được ban hành khi nào? | Top-3 đều `tmu-dormitory-electric-water-fees` nhưng không chứa 05/08/2024 | 0.8101 | Có doc_id đúng nhưng sai nội dung | Không trả lời đúng ngày ban hành | 
| 5 | Đối tượng nào được ưu tiên khi xét duyệt chỗ ở nội trú? | Chunk `dorm-slot`, mục đối tượng ưu tiên | 0.8441 | Có | Agent lấy được danh sách ưu tiên | 

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 4 / 5 (riêng Q4 trả đúng tài liệu nhưng sai section)

**Failure case tôi quan sát được của chiến lược SentenceChunker:**
> Q4 trả top-3 đều thuộc tài liệu đúng, nhưng section chứa đáp án 05/08/2024 không lọt top-3. Điều này cho thấy điểm doc_id thổi phồng kết quả; phải kiểm tra nội dung từng chunk.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc cùng một query nhưng mỗi người chọn cách chia chunk khác nhau, đặc biệt là thay đổi `chunk_size`, `overlap`, hoặc dùng recursive theo đoạn, làm kết quả top-k khác nhau rõ rệt. Em hiểu thêm rằng một chiến lược không phải lúc nào cũng tốt cho mọi câu hỏi; cần so sánh bằng benchmark và xem cả metadata filter chứ không chỉ nhìn điểm similarity.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **59 / 60** |
