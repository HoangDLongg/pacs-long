# PACS++ — Test Plan

**Version**: 1.1  
**Date**: 2026-04-10  
**Scope**: US1 → US8 (Core Authentication & Main Features)  
**Environment**: Backend `localhost:8000`, Frontend `localhost:5173`

---

### Tài khoản Test

| Role       | Username     | Password       | Ghi chú                          |
|------------|--------------|----------------|----------------------------------|
| Admin      | `admin`      | `admin123`     | Full quyền                       |
| Doctor     | `dr.nam`     | `doctor123`    | Viết & xem báo cáo               |
| Technician | `tech.hung`  | `tech123`      | Upload DICOM                     |
| Patient    | `AP-6H6G`    | `AP-6H6G@`     | 7 studies                        |
| Patient    | `AP-95DK`    | `AP-95DK@`     | 5 studies                        |
| Inactive   | `inactive`   | `test123`      | Tài khoản bị khóa (`is_active=false`) |

---

### TC-01: Authentication & JWT (US1)

| ID            | Test Case                                      | Input / Action                                                                 | Expected Result                                                                 |
|---------------|------------------------------------------------|--------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| TC-01-01      | Login thành công - Admin                       | `POST /api/auth/login` với `admin` / `admin123`                                | 200 + `access_token`, `refresh_token`, `role = "admin"`                         |
| TC-01-02      | Login thành công - Doctor                      | `POST /api/auth/login` với doctor account                                      | 200 + `role = "doctor"`                                                         |
| TC-01-03      | Login thành công - Patient                     | `POST /api/auth/login` với `AP-6H6G`                                           | 200 + `role = "patient"`, `linked_patient_id` ≠ null                           |
| TC-01-04      | Login sai mật khẩu                             | Password sai                                                                   | 401 + `"Sai tài khoản hoặc mật khẩu"`                                           |
| TC-01-05      | Login tài khoản bị khóa                        | Sử dụng tài khoản `inactive`                                                   | 403 + `"Tài khoản đã bị khóa"`                                                  |
| TC-01-06      | GET /me với Access Token hợp lệ                | `GET /api/auth/me` + Bearer `<access_token>`                                   | 200 + thông tin user đầy đủ                                                     |
| TC-01-07      | GET /me với Access Token không hợp lệ          | Token sai hoặc hết hạn                                                         | 401 + `"Access token không hợp lệ hoặc đã hết hạn"`                             |
| TC-01-08      | Refresh Token thành công                       | `POST /api/auth/refresh` với refresh_token hợp lệ                              | 200 + access_token mới + refresh_token mới (rotation)                           |
| TC-01-09      | Refresh Token hết hạn hoặc bị revoke           | Dùng refresh_token cũ hoặc đã revoke                                           | 401                                                                              |
| TC-01-10      | Logout thành công                              | `POST /api/auth/logout` với refresh_token                                      | 200 + refresh_token bị revoke trong DB                                          |

---

### TC-02: Worklist & Dashboard (US2)

| ID            | Test Case                                      | Input / Action                                      | Expected Result                                                                 |
|---------------|------------------------------------------------|-----------------------------------------------------|----------------------------------------------------------------------------------|
| TC-02-01      | Admin/Doctor/Tech xem Worklist                 | `GET /api/worklist`                                 | 200 + danh sách studies                                                         |
| TC-02-02      | Patient KHÔNG xem Worklist chung               | `GET /api/worklist` với token Patient               | 403                                                                              |
| TC-02-03      | Filter theo Modality                           | `?modality=CT`                                      | Chỉ trả về các ca có `modality = "CT"`                                          |
| TC-02-04      | Filter theo Status                             | `?status=PENDING`                                   | Chỉ trả về các ca có `status = "PENDING"`                                       |
| TC-02-05      | Filter theo ngày                               | `?date=2016-03-12`                                  | Chỉ trả về các ca đúng ngày                                                     |
| TC-02-06      | Dashboard Statistics                           | `GET /api/worklist/stats/dashboard`                 | Trả về `total`, `pending`, `reported`, `verified`                               |
| TC-02-07      | Xem chi tiết Study                             | `GET /api/worklist/{study_id}`                      | 200 + đầy đủ thông tin study + patient                                           |
| TC-02-08      | Pagination & Sorting                           | `?page=1&limit=20&sort=study_date`                 | Hoạt động đúng                                                                   |
| TC-02-09      | Tìm kiếm theo Patient Name/ID                  | `?search=Nguyen Van A`                              | Trả về kết quả tìm kiếm                                                          |

---

### TC-03: Upload DICOM (US3)

| ID            | Test Case                                      | Input / Action                                      | Expected Result                                                                 |
|---------------|------------------------------------------------|-----------------------------------------------------|----------------------------------------------------------------------------------|
| TC-03-01      | Technician/Admin upload file .dcm hợp lệ       | `POST /api/dicom/upload` + file `.dcm`              | 200 + tạo study + patient nếu chưa có                                            |
| TC-03-02      | Upload trùng StudyUID                          | Upload cùng file 2 lần                              | Lần 2: `num_instances` tăng, không tạo study mới                                 |
| TC-03-03      | Upload file không phải .dcm                    | File `.png`, `.jpg`                                 | 400 + `"Chỉ chấp nhận file .dcm"`                                               |
| TC-03-04      | Upload file giả .dcm (corrupt)                 | File text đổi đuôi `.dcm`                           | 400 + thông báo thiếu PatientID/StudyUID                                        |
| TC-03-05      | Doctor KHÔNG được upload                       | Token Doctor                                        | 403                                                                              |
| TC-03-06      | Patient KHÔNG được upload                      | Token Patient                                       | 403                                                                              |

---

### TC-04: DICOM Viewer & Instances (US4)

| ID            | Test Case                                      | Input / Action                                      | Expected Result                                                                 |
|---------------|------------------------------------------------|-----------------------------------------------------|----------------------------------------------------------------------------------|
| TC-04-01      | Lấy danh sách instances của study              | `GET /api/dicom/instances/{study_id}`               | 200 + danh sách instances                                                        |
| TC-04-02      | Patient xem study của chính mình               | Token Patient + study thuộc họ                      | 200                                                                              |
| TC-04-03      | Patient xem study của người khác               | Token Patient + study khác                          | 403                                                                              |
| TC-04-04      | Viewer UI - Load study có dữ liệu              | Mở `/viewer/{id}`                                   | Load ảnh từ Orthanc (nếu có)                                                     |
| TC-04-05      | Viewer UI - Study chưa có DICOM                | Mở viewer study chưa upload                         | Hiển thị Empty state                                                             |

---

### TC-05: Báo cáo Chẩn đoán (US5)

| ID            | Test Case                                      | Input / Action                                      | Expected Result                                                                 |
|---------------|------------------------------------------------|-----------------------------------------------------|----------------------------------------------------------------------------------|
| TC-05-01      | Doctor/Admin tạo báo cáo mới                   | `POST /api/report` với findings, conclusion         | 200 + status study chuyển thành `"REPORTED"`                                    |
| TC-05-02      | Technician KHÔNG tạo được report               | Token Technician                                    | 403                                                                              |
| TC-05-03      | Xem báo cáo (tất cả role)                      | `GET /api/report/{study_id}`                        | 200 (Patient chỉ xem được report của chính mình)                                 |
| TC-05-04      | Cập nhật báo cáo                               | `PUT /api/report/{id}`                              | 200                                                                              |
| TC-05-05      | Xuất PDF báo cáo                               | `GET /api/report/{id}/pdf`                          | 200 + file PDF có header bệnh viện                                              |

---

### TC-06: Patient Data Isolation (US8)

| ID            | Test Case                                      | Input / Action                                      | Expected Result                                                                 |
|---------------|------------------------------------------------|-----------------------------------------------------|----------------------------------------------------------------------------------|
| TC-06-01      | Patient xem "Ca của tôi"                       | `GET /api/worklist/my-studies`                      | 200 + chỉ thấy studies của chính mình                                            |
| TC-06-02      | Patient không xem Worklist chung               | `GET /api/worklist`                                 | 403                                                                              |
| TC-06-03      | Patient xem chi tiết study của mình            | `GET /api/worklist/{id}` (study thuộc họ)           | 200                                                                              |
| TC-06-04      | Patient xem study của người khác               | `GET /api/worklist/{id}` (study khác)               | 403                                                                              |
| TC-06-05      | Patient xem report của chính mình              | `GET /api/report/{id}`                              | 200 (nếu là report của study thuộc họ)                                           |
| TC-06-06      | Patient xem report của người khác              | `GET /api/report/{id}`                              | 403                                                                              |

---

### TC-07: Frontend UI / UX (Manual Testing)

- TC-07-01: Login page load và redirect đúng
- TC-07-02: Login Admin → vào Worklist
- TC-07-03: Login Patient → vào My Studies
- TC-07-04: Patient truy cập `/worklist` → tự redirect về `/my-studies`
- TC-07-05: Worklist load data + hiển thị 4 stat cards
- TC-07-06: Filter Worklist (Modality, Status, Date)
- TC-07-07: Mở Viewer từ Worklist
- TC-07-08: Doctor tạo report qua UI
- TC-07-09: Tech xem report ở chế độ readonly
- TC-07-10: Xuất PDF từ trang report
- TC-07-11: Silent Refresh Token khi Access Token hết hạn
- TC-07-12: Logout từ nhiều thiết bị

---

### TC-08: Edge Cases & Security

| ID            | Test Case                                      | Expected Result                                                                 |
|---------------|------------------------------------------------|----------------------------------------------------------------------------------|
| TC-08-01      | Upload file giả .dcm (không có metadata)       | 400                                                                              |
| TC-08-02      | Tạo report thiếu trường bắt buộc               | 422 (Pydantic validation)                                                        |
| TC-08-03      | Concurrent login + Refresh Token Rotation      | Refresh token cũ bị vô hiệu hóa                                                  |
| TC-08-04      | Access Token hết hạn nhưng Refresh thành công  | Hệ thống tự động refresh mà không logout                                         |
| TC-08-05      | SQL Injection / XSS cơ bản                     | Không bị tấn công                                                                |

---

### TC-09: Health & System Check

| ID            | Test Case                                      | Expected Result                                                                 |
|---------------|------------------------------------------------|----------------------------------------------------------------------------------|
| TC-09-01      | Backend Health Check                           | `GET /health` → `{"status": "ok", ...}`                                         |
| TC-09-02      | Swagger UI                                     | `/docs` hoạt động bình thường                                                    |
| TC-09-03      | Server Startup & Shutdown                      | Không lỗi khi khởi động và tắt server                                            |

---

### Kết quả Tổng hợp

| Nhóm Test                  | Số lượng TC | Pass | Fail | Skip | Ghi chú |
|----------------------------|-------------|------|------|------|--------|
| TC-01 Authentication       | 10          |      |      |      |        |
| TC-02 Worklist             | 9           |      |      |      |        |
| TC-03 Upload DICOM         | 7           |      |      |      |        |
| TC-04 DICOM Viewer         | 5           |      |      |      |        |
| TC-05 Báo cáo              | 6           |      |      |      |        |
| TC-06 Patient Isolation    | 6           |      |      |      |        |
| TC-07 Frontend UI          | 12          |      |      |      |        |
| TC-08 Edge Cases & Security| 5           |      |      |      |        |
| TC-09 Health & System      | 3           |      |      |      |        |
| **TOTAL**                  | **63**      |      |      |      |        |

---

**Tester**: ___________________  
**Date**: ___________________  
**Ghi chú chung**:
