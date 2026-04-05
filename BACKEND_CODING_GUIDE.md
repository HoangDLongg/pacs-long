# 🛠️ Backend PACS++ — Hướng dẫn Code từng file

> **Dành cho**: Người chưa từng code API  
> **Cách học**: Mình hướng dẫn từng dòng, bạn tự gõ  
> **Quy tắc**: Mỗi file xong → chạy test → hiểu rồi → sang file tiếp

---

# NGÀY 1: PACS Core (14 files, ~6-8 giờ)

---

## File 1/14: `requirements.txt` ⏱️ 5 phút

**Mục đích**: Khai báo thư viện Python cần cài.

**Nơi tạo**: `pacs_rag_system/backend-v2/requirements.txt`

**Nội dung cần gõ**:
```text
fastapi==0.111.0
uvicorn[standard]==0.30.1
psycopg2-binary==2.9.9
pgvector==0.2.5
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydicom==2.4.4
requests==2.32.3
python-multipart==0.0.9
python-dotenv==1.0.1
reportlab==4.2.0
FlagEmbedding==1.2.10
torch==2.3.0
Pillow==10.3.0
```

**Sau khi tạo, chạy**:
```powershell
cd pacs_rag_system/backend-v2
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Kiểm tra**: `pip list` thấy fastapi, uvicorn là OK.

---

## File 2/14: `.env` ⏱️ 5 phút

**Mục đích**: Cấu hình database, Orthanc, JWT. File này KHÔNG commit Git.

**Nơi tạo**: `backend-v2/.env`

**Nội dung cần gõ**:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=pacs_db
DB_USER=pacs_user
DB_PASS=pacs_password

ORTHANC_URL=http://localhost:8042

JWT_SECRET=pacs-plus-plus-secret-key-2026
JWT_EXPIRE_HOURS=8

OLLAMA_URL=http://localhost:11434
```

**Giải thích**:
- `DB_*`: Thông tin kết nối PostgreSQL (chạy trong Docker)
- `ORTHANC_URL`: Orthanc DICOM server (chạy trong Docker)
- `JWT_SECRET`: Key để mã hoá token đăng nhập
- `JWT_EXPIRE_HOURS`: Token hết hạn sau 8 giờ

---

## File 3/14: `config.py` ⏱️ 10 phút

**Mục đích**: Đọc `.env` thành biến Python. Các file khác import từ đây.

**Nơi tạo**: `backend-v2/config.py`

**Khái niệm cần hiểu**:
- `os.getenv("TÊN", "mặc_định")` = lấy biến môi trường, nếu không có thì dùng giá trị mặc định
- `load_dotenv()` = đọc file `.env` vào môi trường

**Cấu trúc code**:
```
1. import os
2. from dotenv import load_dotenv
3. load_dotenv()
4. DB_HOST = os.getenv(...)
5. DB_PORT = int(os.getenv(...))  ← port là số, cần int()
6. ... tương tự cho các biến khác
```

**Test**: Tạo file `test_config.py`, import config, print ra xem đúng không.

---

## File 4/14: `database/init_db.sql` ⏱️ 20 phút

**Mục đích**: Tạo 4 bảng trong PostgreSQL.

**Nơi tạo**: `backend-v2/database/init_db.sql`

**Khái niệm cần hiểu**:
- `SERIAL PRIMARY KEY` = ID tự tăng
- `VARCHAR(50) UNIQUE NOT NULL` = chuỗi tối đa 50 ký tự, không trùng, bắt buộc
- `REFERENCES bảng(cột)` = foreign key (liên kết bảng)
- `CHECK (cột IN ('a','b','c'))` = chỉ chấp nhận giá trị trong danh sách
- `DEFAULT 'giá_trị'` = giá trị mặc định
- `vector(1024)` = kiểu dữ liệu vector (cần pgvector extension)

**Thứ tự tạo bảng** (quan trọng vì FK):
```
1. CREATE EXTENSION IF NOT EXISTS vector;
2. Bảng patients (không phụ thuộc ai)
3. Bảng users (FK → patients cho linked_patient_id)
   - role CHECK IN ('admin','doctor','technician','patient')
4. Bảng studies (FK → patients, FK → users)
5. Bảng diagnostic_reports (FK → studies UNIQUE, FK → users)
6. CREATE INDEX trên studies (patient_id, study_date, status)
7. CREATE INDEX trên diagnostic_reports (embedding vector_cosine_ops)
```

**Cột mỗi bảng**:

| Bảng | Cột chính |
|---|---|
| patients | id, patient_id(UK), full_name, birth_date, gender(M/F), phone, address |
| users | id, username(UK), password_hash, full_name, role, is_active, linked_patient_id(FK) |
| studies | id, study_uid(UK), patient_id(FK), study_date, modality, body_part, description, status, technician_id(FK), orthanc_id, num_instances |
| diagnostic_reports | id, study_id(FK+UK), doctor_id(FK), findings, conclusion, recommendation, report_date, embedding, created_at, updated_at |

---

## File 5/14: `database/connection.py` ⏱️ 15 phút

**Mục đích**: Kết nối PostgreSQL, cung cấp hàm get/close connection.

**Nơi tạo**: `backend-v2/database/connection.py`

**Khái niệm cần hiểu**:
- **Connection Pool**: Giữ sẵn N kết nối DB, lấy ra dùng rồi trả lại (nhanh hơn tạo mới mỗi lần)
- **Cursor**: Con trỏ để chạy SQL query
- **RealDictCursor**: Trả kết quả dạng dict `{"id": 1, "name": "A"}` thay vì tuple `(1, "A")`
- **commit()**: Xác nhận thay đổi vào DB
- **rollback()**: Huỷ thay đổi nếu lỗi

**Các hàm cần viết**:
```
1. init_pool() → tạo SimpleConnectionPool(1, 10, host, port, dbname, user, password)
2. get_connection() → pool.getconn()
3. release_connection(conn) → pool.putconn(conn)
4. init_db() → đọc init_db.sql, chạy SQL, commit
```

**Test**: Chạy `init_db()` → kiểm tra bảng đã tạo trong PostgreSQL.

---

## File 6/14: `core/auth_utils.py` ⏱️ 20 phút

**Mục đích**: Mã hoá password + tạo/đọc JWT token.

**Nơi tạo**: `backend-v2/core/auth_utils.py`

**Khái niệm cần hiểu**:
- **bcrypt hash**: Mã hoá password 1 chiều. "admin123" → "$2b$12$xyz..." Không giải mã ngược được.
- **JWT**: Chuỗi token chứa thông tin user (id, role). Server ký bằng secret key. Client gửi kèm mỗi request.
- **JWT cấu trúc**: `header.payload.signature`
  - payload = `{"sub": 1, "username": "admin", "role": "admin", "exp": 1234567890}`

**Các hàm cần viết**:
```
1. hash_password(password: str) → str
   - Dùng passlib CryptContext(schemes=["bcrypt"])
   - return context.hash(password)

2. verify_password(plain: str, hashed: str) → bool
   - return context.verify(plain, hashed)

3. create_token(user_id: int, username: str, role: str) → str
   - payload = {"sub": user_id, "username": username, "role": role, 
                "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS)}
   - return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

4. decode_token(token: str) → dict
   - return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

5. get_current_user(request: Request) → dict
   - Lấy header "Authorization"
   - Tách "Bearer xxx" → lấy phần xxx
   - decode_token(xxx) → trả dict user
   - Nếu lỗi → raise HTTPException(status_code=401)
```

**Test**: hash_password("admin123") → verify_password("admin123", hash) → True

---

## File 7/14: `api/auth.py` ⏱️ 20 phút

**Mục đích**: API đăng nhập. Frontend gọi endpoint này.

**Nơi tạo**: `backend-v2/api/auth.py`

**Khái niệm cần hiểu**:
- **APIRouter**: Nhóm các endpoint lại, đặt prefix chung
- **BaseModel (Pydantic)**: Validate dữ liệu đầu vào tự động
- **POST**: Gửi dữ liệu lên server (body JSON)
- **GET**: Lấy dữ liệu từ server

**Endpoints cần viết**:
```
router = APIRouter(prefix="/api/auth", tags=["Auth"])

POST /api/auth/login
  Input:  {"username": "admin", "password": "admin123"}
  Logic:  1. Query DB tìm user theo username
          2. Nếu không có → 401 "Sai thông tin"
          3. verify_password → nếu sai → 401
          4. Nếu is_active=False → 403 "Tài khoản bị khoá"
          5. create_token()
  Output: {"token": "eyJ...", "user": {"id": 1, "username": "admin", ...}}

GET /api/auth/me
  Input:  Header: Authorization: Bearer eyJ...
  Logic:  get_current_user(request) → user info
  Output: {"id": 1, "username": "admin", "role": "admin", ...}
```

**Test**: Mở `http://localhost:8000/docs` → thử login → nhận token.

---

## File 8/14: `core/orthanc_client.py` ⏱️ 15 phút

**Mục đích**: Gọi Orthanc REST API — upload/download ảnh DICOM.

**Nơi tạo**: `backend-v2/core/orthanc_client.py`

**Khái niệm cần hiểu**:
- Orthanc là server DICOM, chạy port 8042
- Nó có REST API giống như backend của mình
- Mình gọi API của Orthanc bằng thư viện `requests`

**Các hàm cần viết**:
```
1. upload_dicom(file_bytes: bytes) → dict
   - requests.post(ORTHANC_URL + "/instances", data=file_bytes)
   - return response.json()

2. get_study(orthanc_id: str) → dict
   - requests.get(ORTHANC_URL + "/studies/" + orthanc_id)

3. get_study_instances(orthanc_id: str) → list
   - requests.get(ORTHANC_URL + "/studies/" + orthanc_id + "/instances")

4. get_instance_file(instance_id: str) → bytes
   - requests.get(ORTHANC_URL + "/instances/" + instance_id + "/file")
   - return response.content  ← binary data
```

**Test**: Upload 1 file .dcm thử → kiểm tra Orthanc UI `http://localhost:8042`

---

## File 9/14: `core/dicom_parser.py` ⏱️ 15 phút

**Mục đích**: Đọc metadata từ file .dcm (tên BN, ngày chụp, modality...).

**Nơi tạo**: `backend-v2/core/dicom_parser.py`

**Các hàm cần viết**:
```
1. parse_dicom(file_bytes: bytes) → dict
   - ds = pydicom.dcmread(BytesIO(file_bytes), stop_before_pixels=True)
   - Trích xuất: patient_id, patient_name, patient_sex, patient_age,
                 study_uid, study_date, study_description,
                 modality, body_part
   - Dùng getattr(ds, 'PatientID', '') để tránh lỗi nếu tag thiếu
   - Return dict chứa tất cả
```

**Test**: Đọc 1 file .dcm từ dataset → in ra metadata.

---

## File 10/14: `api/worklist.py` ⏱️ 30 phút

**Mục đích**: API danh sách ca chụp + thống kê dashboard.

**Nơi tạo**: `backend-v2/api/worklist.py`

**Endpoints cần viết**:
```
router = APIRouter(prefix="/api/worklist", tags=["Worklist"])

GET /api/worklist
  Query params: ?date=2026-03-01&modality=CT&status=PENDING (tất cả optional)
  Logic: SELECT studies + JOIN patients + JOIN users
         WHERE (filters nếu có)
         ORDER BY study_date DESC
  Auth:  Cần login (admin/doctor/tech)

GET /api/worklist/{id}
  Logic: SELECT 1 study theo id
  Auth:  Cần login

GET /api/worklist/stats/dashboard
  Logic: SELECT COUNT theo status (total, pending, reported, verified)
  Auth:  Cần login
```

---

## File 11/14: `api/dicom.py` ⏱️ 30 phút

**Mục đích**: Upload file DICOM + auto tạo patient + auto tạo account.

**Nơi tạo**: `backend-v2/api/dicom.py`

**Endpoints cần viết**:
```
router = APIRouter(prefix="/api/dicom", tags=["DICOM"])

POST /api/dicom/upload
  Input:  File .dcm (multipart/form-data)
  Logic:  1. Đọc file bytes
          2. parse_dicom() → metadata
          3. Upsert patient vào DB
          4. upload lên Orthanc → nhận orthanc_id
          5. Insert study vào DB
          ★ 6. Auto tạo user cho patient (username=patient_id, password=patient_id+"@")
  Auth:   tech/admin only

GET /api/dicom/wado
  Query:  ?objectId=xxx
  Logic:  Lấy file DICOM từ Orthanc → stream về browser
  Auth:   Cần login
```

---

## File 12/14: `api/report.py` ⏱️ 30 phút

**Mục đích**: CRUD báo cáo chẩn đoán + xuất PDF.

**Nơi tạo**: `backend-v2/api/report.py`

**Endpoints cần viết**:
```
router = APIRouter(prefix="/api/report", tags=["Report"])

GET /api/report/{study_id}         → Xem report (all roles)
POST /api/report                   → Tạo mới (doctor/admin)
PUT /api/report/{id}               → Cập nhật (doctor/admin)
GET /api/report/{id}/pdf           → Xuất PDF (all roles)
```

---

## File 13/14: `main.py` ⏱️ 20 phút

**Mục đích**: File chính — nối tất cả routers lại, chạy server.

**Nơi tạo**: `backend-v2/main.py`

**Cấu trúc**:
```
1. Tạo app = FastAPI(title="PACS++ API")
2. Cấu hình CORS (cho phép frontend gọi)
3. Include tất cả routers (auth, worklist, dicom, report)
4. GET /health → {"status": "ok"}
5. Startup event: init_db()
6. Chạy: uvicorn.run(app, port=8000)
```

**Test**: `python main.py` → mở `http://localhost:8000/docs` → thấy Swagger UI.

---

## File 14/14: `scripts/seed_data.py` ⏱️ 20 phút

**Mục đích**: Tạo 5 user mẫu để test đăng nhập.

**Nơi tạo**: `backend-v2/scripts/seed_data.py`

**Data cần tạo**:
```
admin     / admin123   → role: admin
dr.nam    / doctor123  → role: doctor  
dr.lan    / doctor123  → role: doctor
tech.hung / tech123    → role: technician
tech.mai  / tech123    → role: technician
```

**Test**: Chạy seed → login bằng admin/admin123 qua Swagger.

---

# NGÀY 2: RAG Engine (8 files, ~6-8 giờ)

| # | File | Mục đích | Thời gian |
|---|---|---|---|
| 15 | core/embeddings.py | Load BGE-M3, encode text → vector 1024d | 30 phút |
| 16 | core/rag_engine.py | Dense search (pgvector) + BM25 + Hybrid + RRF | 90 phút |
| 17 | core/nl2sql_engine.py | Câu hỏi → SQL (Rule-based + Ollama) | 60 phút |
| 18 | core/query_router.py | Phân loại câu hỏi: STRUCTURED / SEMANTIC / HYBRID | 30 phút |
| 19 | core/answer_generator.py | Tổng hợp câu trả lời text từ kết quả | 30 phút |
| 20 | api/search.py | Keyword + Dense + Hybrid search API | 30 phút |
| 21 | api/ask.py | NL2SQL unified endpoint (POST /api/ask) | 30 phút |
| 22 | api/patient_portal.py | GET /api/my-studies (patient xem ca của mình) | 20 phút |

> Chi tiết ngày 2 sẽ được viết khi xong ngày 1.

---

# Checklist tiến độ

## Ngày 1
- [ ] File 1: requirements.txt
- [ ] File 2: .env
- [ ] File 3: config.py
- [ ] File 4: database/init_db.sql
- [ ] File 5: database/connection.py
- [ ] File 6: core/auth_utils.py
- [ ] File 7: api/auth.py
- [ ] File 8: core/orthanc_client.py
- [ ] File 9: core/dicom_parser.py
- [ ] File 10: api/worklist.py
- [ ] File 11: api/dicom.py
- [ ] File 12: api/report.py
- [ ] File 13: main.py
- [ ] File 14: scripts/seed_data.py
- [ ] ★ TEST: Login thành công qua Swagger UI

## Ngày 2
- [ ] File 15: core/embeddings.py
- [ ] File 16: core/rag_engine.py
- [ ] File 17: core/nl2sql_engine.py
- [ ] File 18: core/query_router.py
- [ ] File 19: core/answer_generator.py
- [ ] File 20: api/search.py
- [ ] File 21: api/ask.py
- [ ] File 22: api/patient_portal.py
- [ ] ★ TEST: Hỏi "Bao nhiêu ca CT?" → nhận câu trả lời

---

# Khi bắt đầu

Nhắn **"bắt đầu file 1"** → mình sẽ hướng dẫn từng dòng code.
Xong file nào → nhắn **"xong file X, tiếp"** → mình review rồi sang file tiếp.
Stuck chỗ nào → nhắn **"stuck ở dòng..."** → mình giải thích lại.
