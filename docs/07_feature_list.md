# 07 — Tổng hợp toàn bộ chức năng PACS++

> Tài liệu này liệt kê **toàn bộ tính năng** của hệ thống theo từng module.  
> Dùng để xác nhận phạm vi trước khi bắt đầu code Sprint 1.

---

## A. CHỨC NĂNG THEO TRANG WEB

---

### 🔐 Trang Đăng nhập (`/login`)

| # | Chức năng | Mô tả | Role |
|---|---|---|---|
| 1 | Đăng nhập | Nhập username + password → nhận JWT token | Tất cả |
| 2 | Lưu phiên | Lưu token vào localStorage, tự giữ phiên | Tất cả |
| 3 | Auto-redirect | Nếu đã đăng nhập → tự chuyển về Worklist | Tất cả |
| 4 | Hiển thị lỗi | Sai mật khẩu → thông báo lỗi rõ ràng | Tất cả |
| 5 | Gợi ý tài khoản | Hiện danh sách tài khoản test ngay trên màn login | Tất cả |

---

### 📋 Trang Worklist (`/worklist`)

| # | Chức năng | Mô tả | Role |
|---|---|---|---|
| **Thống kê** | | | |
| 6 | Tổng ca chụp | Hiện tổng số ca trong hệ thống | Tất cả |
| 7 | Ca chờ đọc | Số ca có status = PENDING | Tất cả |
| 8 | Ca đã báo cáo | Số ca có status = REPORTED | Tất cả |
| 9 | Ca đã xác nhận | Số ca có status = VERIFIED | Tất cả |
| **Upload DICOM** | | | |
| 10 | Upload file .dcm | Kéo thả hoặc click chọn file DICOM | tech, admin |
| 11 | Lưu Orthanc | File được đẩy lên Orthanc DICOM server | tech, admin |
| 12 | Lưu metadata DB | Thông tin ca chụp (BN, ngày, modality) vào PostgreSQL | tech, admin |
| 13 | Cập nhật worklist | Danh sách tự làm mới sau khi upload | tech, admin |
| **Bộ lọc** | | | |
| 14 | Lọc theo ngày chụp | Date picker chọn ngày | Tất cả |
| 15 | Lọc theo loại chụp | Dropdown: CR / CT / MR / US / DX / MG | Tất cả |
| 16 | Lọc theo trạng thái | PENDING / REPORTED / VERIFIED | Tất cả |
| 17 | Xoá bộ lọc | Reset tất cả filter về mặc định | Tất cả |
| **Danh sách ca chụp** | | | |
| 18 | Hiển thị bảng | Danh sách ca chụp: tên BN, mã BN, ngày, modality, vị trí, trạng thái, KTV | Tất cả |
| 19 | Click row → Viewer | Click bất kỳ dòng nào → mở trang xem ảnh | Tất cả |
| 20 | Nút "Xem" | Chuyển sang Viewer với ca chụp đó | Tất cả |
| 21 | Nút "Báo cáo" | Chuyển sang trang nhập báo cáo | doctor, admin |
| 22 | Badge trạng thái | Màu sắc khác nhau cho PENDING / REPORTED / VERIFIED | Tất cả |
| 23 | Badge modality | Hiển thị CT / MR dạng code tag | Tất cả |

---

### 🖼️ Trang Xem ảnh DICOM (`/viewer`)

| # | Chức năng | Mô tả | Role |
|---|---|---|---|
| 24 | Metadata ca chụp | Hiện tên BN, mã BN, ngày, loại, vị trí, trạng thái, Study UID | Tất cả |
| 25 | Xem ảnh DICOM | Nhúng Orthanc Web Viewer qua iframe | Tất cả |
| 26 | Thông báo chưa upload | Nếu chưa có file DICOM trên Orthanc → thông báo rõ | Tất cả |
| 27 | Nút Phóng to | Zoom in ảnh | Tất cả |
| 28 | Nút Thu nhỏ | Zoom out ảnh | Tất cả |
| 29 | Nút Di chuyển | Pan mode | Tất cả |
| 30 | Nút Đặt lại | Reset viewport | Tất cả |
| 31 | Nút → Báo cáo | Chuyển sang nhập báo cáo | doctor, admin |
| 32 | Nút → Worklist | Quay lại danh sách | Tất cả |

---

### 📝 Trang Báo cáo (`/report`)

| # | Chức năng | Mô tả | Role |
|---|---|---|---|
| **Xem thông tin** | | | |
| 33 | Thông tin ca chụp | Hiện metadata: BN, ngày, loại, vị trí, status, bác sĩ đọc | Tất cả |
| **Nhập báo cáo** | | | |
| 34 | Nhập Findings | Textarea nhập kết quả hình ảnh (bắt buộc) | doctor, admin |
| 35 | Nhập Conclusion | Textarea nhập kết luận chẩn đoán (bắt buộc) | doctor, admin |
| 36 | Nhập Recommendation | Textarea nhập đề nghị xử trí (tuỳ chọn) | doctor, admin |
| 37 | Tạo báo cáo mới | POST nếu ca chụp chưa có báo cáo | doctor, admin |
| 38 | Cập nhật báo cáo | PUT nếu báo cáo đã tồn tại | doctor, admin |
| 39 | Thông báo lưu OK | Alert success khi lưu thành công | doctor, admin |
| 40 | Xem-only mode | Technician chỉ xem, không edit được | technician |
| **Xuất báo cáo** | | | |
| 41 | Xuất PDF | Tải file PDF báo cáo chẩn đoán | Tất cả |
| **Tự động** | | | |
| 42 | Auto-embed vector | Khi lưu báo cáo → tự tạo embedding BGE-M3 vào DB | system |
| 43 | Cập nhật status | Ca chụp tự chuyển sang REPORTED sau khi lưu | system |

---

### 🔍 Trang Tìm kiếm (`/search`)

| # | Chức năng | Mô tả | Role |
|---|---|---|---|
| **Tìm kiếm từ khoá** | | | |
| 44 | Keyword search | Tìm trong findings + conclusion bằng SQL ILIKE | doctor, admin |
| 45 | Kết quả text match | Hiện tên BN, modality, đoạn text phù hợp | doctor, admin |
| **Tìm kiếm ngữ nghĩa** | | | |
| 46 | Dense search | BGE-M3 encode query → cosine similarity với pgvector | doctor, admin |
| 47 | Hybrid search | Dense + BM25 sparse + Keyword, tổng hợp RRF | doctor, admin |
| 48 | Similarity score | Hiển thị % độ tương đồng dạng progress bar | doctor, admin |
| **Hỏi đáp AI (NL2SQL + RAG)** | | | |
| 49 | Câu hỏi tự nhiên | Nhập câu hỏi tiếng Việt bất kỳ | doctor, admin |
| 50 | Phân loại tự động | Hệ thống tự nhận: STRUCTURED / SEMANTIC / HYBRID | system |
| 51 | Sinh SQL tự động | Ollama/Gemini sinh SQL từ câu hỏi | system |
| 52 | Hiện SQL được sinh | Cho xem câu SQL backend đã tạo | doctor, admin |
| 53 | Hiện kết quả SQL | Bảng dữ liệu thô từ PostgreSQL | doctor, admin |
| 54 | Câu trả lời tự nhiên | AI tổng hợp từ SQL + RAG → câu trả lời text | doctor, admin |
| 55 | Kết quả RAG | Danh sách báo cáo liên quan (semantic) | doctor, admin |

---

### ⚙️ Trang Quản trị (`/admin`)

| # | Chức năng | Mô tả | Role |
|---|---|---|---|
| 56 | Danh sách users | Hiện tất cả tài khoản, role, trạng thái | admin |
| 57 | Tài khoản mặc định | Xem thông tin các tài khoản có sẵn | admin |
| 58 | Thông tin hệ thống | Stack kỹ thuật, phiên bản | admin |
| 59 | Bảo vệ route | Tự redirect về Worklist nếu không phải admin | system |

---

## B. CHỨC NĂNG BACKEND (không UI)

| # | Chức năng | Mô tả |
|---|---|---|
| 60 | JWT Auth middleware | Tất cả API (trừ /login) đều kiểm tra Bearer token |
| 61 | Role-based access | API kiểm tra role trước khi cho phép thao tác |
| 62 | DICOM tag extraction | Tự parse Patient Name, Study Date, Modality từ file .dcm |
| 63 | Orthanc sync | Upload DICOM → lưu UUID Orthanc vào DB |
| 64 | BGE-M3 auto-embed | Khi báo cáo được lưu → tự encode text → lưu vector 1024d |
| 65 | pgvector ANN search | Tìm kiếm vector nhanh bằng IVFFlat index |
| 66 | BM25 sparse search | Tính điểm text relevance cho hybrid search |
| 67 | RRF fusion | Kết hợp rank từ Dense + BM25 bằng Reciprocal Rank Fusion |
| 68 | SQL Validator | Kiểm tra SQL an toàn (chỉ SELECT, không DROP/DELETE) |
| 69 | NL2SQL Rule-based | Regex patterns cho các câu hỏi phổ biến (không cần LLM) |
| 70 | NL2SQL Ollama | Gọi Ollama local nếu rule-based không match |
| 71 | NL2SQL Gemini fallback | Gọi Gemini cloud nếu Ollama không chạy |
| 72 | PDF generation | ReportLab tạo PDF báo cáo chẩn đoán |
| 73 | Health check | GET /health → kiểm tra DB + Orthanc đang chạy |
| 74 | CORS middleware | Cho phép frontend dev (localhost:5173) gọi API |
| 75 | Static file serve | FastAPI serve dist/ của Vite build (production) |

---

## C. MA TRẬN PHÂN QUYỀN

| Chức năng | Admin | Doctor | Technician |
|---|:---:|:---:|:---:|
| Đăng nhập | ✅ | ✅ | ✅ |
| Xem Worklist | ✅ | ✅ | ✅ |
| Filter Worklist | ✅ | ✅ | ✅ |
| Upload DICOM | ✅ | ❌ | ✅ |
| Xem ảnh DICOM | ✅ | ✅ | ✅ |
| Tạo báo cáo | ✅ | ✅ | ❌ |
| Sửa báo cáo | ✅ | ✅ | ❌ |
| Xem báo cáo | ✅ | ✅ | ✅ (readonly) |
| Xuất PDF | ✅ | ✅ | ✅ |
| Tìm kiếm | ✅ | ✅ | ❌ |
| Hỏi đáp AI | ✅ | ✅ | ❌ |
| Trang quản trị | ✅ | ❌ | ❌ |

---

## D. CHỨC NĂNG CHƯA LÀM (Sprint 2+)

| # | Chức năng | Sprint |
|---|---|---|
| F1 | Cornerstone.js viewer (xem DICOM thực sự, không iframe) | Sprint 2 |
| F2 | Window/Level (WW/WL) điều chỉnh độ tương phản | Sprint 2 |
| F3 | Xem multi-frame (scroll CT/MR) | Sprint 2 |
| F4 | PDF template đẹp với logo bệnh viện | Sprint 2 |
| F5 | Gợi ý findings từ RAG khi bác sĩ đang gõ | Sprint 3 |
| F6 | Chat interface real-time streaming | Sprint 3 |
| F7 | Biểu đồ thống kê (theo tháng, theo modality) | Sprint 3 |
| F8 | User management CRUD (thêm/sửa/khoá user) | Sprint 4 |
| F9 | Audit log (log mọi thao tác) | Sprint 4 |
| F10 | Responsive mobile | Sprint 4 |

---

## E. TÓM TẮT SỐ LIỆU

| Hạng mục | Số lượng |
|---|---|
| Tổng chức năng đã thiết kế | **75** |
| Chức năng frontend (UI) | **59** |
| Chức năng backend (API/logic) | **16** |
| Số trang web | **6** |
| Số API endpoint | **15** |
| Bảng database | **4** |
| Role người dùng | **3** |
| Chức năng chưa làm (Sprint 2+) | **10** |
