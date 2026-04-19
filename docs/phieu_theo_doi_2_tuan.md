# PHIẾU THEO DÕI HƯỚNG DẪN SINH VIÊN THỰC HIỆN HỌC PHẦN TỐT NGHIỆP

---

## 1. Thông tin Giảng viên/Cán bộ hướng dẫn
- **Họ và tên:** ThS. Vũ Thành Vinh
- **Đơn vị công tác:** Bộ môn Mạng và An toàn thông tin, Khoa Công nghệ thông tin

## 2. Thông tin sinh viên
- **Họ và tên:** Hoàng Đức Long — **MSV:** 2251162062 — **Lớp:** 64HTTT4
- **Đợt thực hiện:** HKII-2025-2026
- **Tên đề tài:** Xây dựng hệ thống PACS Mini tích hợp RAG hỗ trợ tìm kiếm thông minh kết quả chẩn đoán hình ảnh y tế

---

## 3. Quá trình hướng dẫn của Giảng viên

| Ngày tháng | Nội dung công việc Giảng viên đã thực hiện | Nhận xét, góp ý, đánh giá của GV | Địa điểm thực hiện |
|---|---|---|---|
| 24/03/2026 | Hướng dẫn sinh viên thiết kế kiến trúc hệ thống PACS Mini: xác định các thành phần chính gồm FastAPI Backend, PostgreSQL + pgvector, Orthanc DICOM Server, và Frontend React SPA. Góp ý về mô hình micro-services cho hệ thống RAG. | Sinh viên nắm bắt nhanh yêu cầu, đã phác thảo được sơ đồ kiến trúc tổng quan. Cần bổ sung thêm phần ERD chi tiết và flow xác thực JWT. | Online (Google Meet) |
| 26/03/2026 | Hướng dẫn thiết kế cơ sở dữ liệu: 4 bảng chính (users, patients, studies, diagnostic_reports) với PostgreSQL 16 và extension pgvector (dimension 1024). Góp ý về chuẩn hóa tên bệnh nhân tiếng Việt trong DICOM. | Thiết kế ERD hợp lý, quan hệ giữa các bảng rõ ràng. Đề nghị thêm constraint CHECK cho trường modality và role. | Online (Google Meet) |
| 28/03/2026 | Review tài liệu thiết kế hệ thống (9 file docs). Góp ý hoàn thiện README.md với sơ đồ Mermaid trực quan hóa kiến trúc, ERD, và luồng dữ liệu RAG. | Tài liệu đầy đủ, trình bày rõ ràng. Cần bổ sung phần mô tả API endpoints chi tiết hơn và thêm use cases cho từng vai trò người dùng. | Online (Google Meet) |
| 31/03/2026 | Hướng dẫn triển khai Backend v2 (FastAPI): cấu trúc thư mục modular, 5 API routers (auth, worklist, dicom, report, search). Góp ý về cách xử lý xác thực JWT và connection pooling PostgreSQL. | Sinh viên đã hoàn thành backend với 14 files. Code có cấu trúc tốt, tách biệt rõ ràng giữa API layer, business logic, và database layer. | Phòng lab CNTT |
| 02/04/2026 | Hướng dẫn xử lý dữ liệu DICOM: viết script bulk_upload để đẩy 13.499 file DICOM lên Orthanc, script edit_names để chuẩn hóa tên bệnh nhân tiếng Việt có dấu. Kiểm tra kết quả seed data (21 bệnh nhân, 75 ca chụp, 26 tài khoản). | Dữ liệu nạp thành công. Phát hiện 4 file DICOM lỗi do modality "SEG" chưa được hỗ trợ — cần xử lý. Đề nghị viết thêm validation script. | Phòng lab CNTT |
| 05/04/2026 | Hướng dẫn phát triển Frontend React (Sprint 1): thiết lập Vite + React Router, xây dựng trang Login với thiết kế hospital dark theme. Kiểm tra kết nối FE-BE, phát hiện và sửa 4 lỗi tích hợp (API format, error handling, token mismatch). | Giao diện Login chuyên nghiệp với ảnh nền bệnh viện, glassmorphism card. Phát hiện bug FE gửi form-urlencoded thay vì JSON — đã fix kịp thời. Sinh viên cần rút kinh nghiệm kiểm tra API contract trước khi code. | Online (Google Meet) |
| 07/04/2026 | Review tiến độ 2 tuần. Lên kế hoạch Sprint 2: Layout system (Sidebar + Topbar), API layer, trang Worklist. Thảo luận về tích hợp Cornerstone.js cho DICOM Viewer. | Tiến độ tốt, hoàn thành đúng kế hoạch Sprint 1. Cần tập trung vào trang Worklist (trang chính) và chuẩn bị tích hợp Cornerstone.js Legacy cho phần xem ảnh DICOM. | Online (Google Meet) |

---

## 4. Nhận xét

**a. Tinh thần thái độ làm việc của Sinh viên:**
Sinh viên có tinh thần làm việc tích cực, chủ động tìm hiểu và giải quyết vấn đề. Luôn hoàn thành công việc đúng tiến độ được giao, có ý thức ghi chép lỗi phát sinh (bug log) và rút kinh nghiệm sau mỗi phiên làm việc. Tương tác tốt với giảng viên hướng dẫn, tiếp thu góp ý nhanh chóng.

**b. Tính đến thời điểm 07/04/2026, sinh viên đã:**
Hoàn thành thiết kế kiến trúc hệ thống và tài liệu kỹ thuật (9 file docs + README với sơ đồ Mermaid). Triển khai thành công Backend v2 với FastAPI (14 files, 5 API routers). Nạp dữ liệu DICOM thực tế (13.499 files, 21 bệnh nhân, 75 ca chụp) lên Orthanc Server. Xây dựng Frontend React SPA với trang đăng nhập hoàn chỉnh, kết nối thành công với Backend qua JWT authentication. Đẩy mã nguồn lên GitHub repository. Đạt khoảng 40% khối lượng công việc tổng thể của đồ án.

---

Bộ môn (phụ trách ngành) &emsp;&emsp;&emsp;&emsp;&emsp;&emsp; Hà Nội, ngày ....... tháng ....... năm 2026

&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; GV/cán bộ hướng dẫn
