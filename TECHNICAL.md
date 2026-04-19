# 🔬 TECHNICAL.md — Tài Liệu Kỹ Thuật Chi Tiết

> PACS Mini + RAG System  
> Tài liệu dành cho **developer / giám khảo luận văn** — mô tả kiến trúc, thiết kế hệ thống, kế hoạch triển khai và đánh giá.

---

## 1. Kiến Trúc Tổng Quan

```
┌─────────────────────────────────────────────────────────────────────┐
│                          WEB BROWSER                                 │
│   login.html  │  index.html  │  viewer.html  │  report.html  │  search.html   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP / REST / JWT
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend (:8000)                         │
│                                                                      │
│  /api/auth   │  /api/dicom   │  /api/worklist  │  /api/report  │  /api/search │
│      │               │               │                │               │        │
│   JWT Auth    DICOM Upload    Worklist Filter    PDF Export     RAG Engine      │
│              Orthanc Client                      BCrypt Hash   BGE-M3 Encode   │
└─────────┬──────────────┬────────────────────────────────────────────┘
          │              │
          ▼              ▼
┌─────────────────┐  ┌───────────────────────────────────────┐
│ PostgreSQL :5432│  │         Orthanc Server :8042           │
│  + pgvector     │  │                                        │
│                 │  │  - Lưu file DICOM (.dcm)               │
│  users          │  │  - REST API: /studies /instances       │
│  patients       │  │  - WADO: stream ảnh cho Cornerstone.js │
│  studies        │  │  - DICOM Protocol port :4242           │
│  diagnostic_    │  │    (nhận C-STORE từ máy chụp thật)     │
│   reports       │  └───────────────────────────────────────┘
│  embedding      │
│  vector(1024)   │
└─────────────────┘
```

### Luồng dữ liệu chính

```
[Kỹ thuật viên upload .dcm]
    → Orthanc lưu file + trả về orthanc_id
    → Backend lưu study vào PostgreSQL (status: PENDING)

[Bác sĩ viết báo cáo]
    → POST /api/report → lưu findings + conclusion vào DB
    → BGE-M3 encode text → vector 1024 chiều
    → Lưu embedding vào cột vector(1024) của diagnostic_reports

[Bác sĩ tìm kiếm]
    → POST /api/search {query: "tổn thương phổi phải"}
    → BGE-M3 encode query → vector
    → pgvector: SELECT ... ORDER BY embedding <=> query_vec LIMIT K
    → Trả danh sách kết quả + similarity_score
```

---

## 2. Module Chi Tiết

### 2.1 `backend/core/embeddings.py` — BGE-M3 Encoder

**Mô hình**: `BAAI/bge-m3` (FlagEmbedding 1.2.10)

```python
# Cách hoạt động
from FlagEmbedding import BGEM3FlagModel

model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)

def encode_text(text: str) -> list[float]:
    # Trả về dense vector 1024 chiều
    output = model.encode([text], batch_size=1, max_length=512)
    return output["dense_vecs"][0].tolist()
```

**Tại sao BGE-M3?**
- Đa ngôn ngữ (hỗ trợ tiếng Việt tốt)
- Vector 1024 chiều cho độ chính xác cao
- Hỗ trợ cả dense + sparse retrieval
- Open-source, chạy được trên CPU (dù chậm hơn GPU)

**Lưu ý về performance**:
| Hardware | Thời gian encode 1 báo cáo |
|---|---|
| CPU (Intel i7) | ~3-5 giây |
| GPU (RTX 3060) | ~0.1 giây |

---

### 2.2 `backend/core/rag_engine.py` — Vector Search

Sử dụng **pgvector cosine similarity** (`<=>` operator):

```sql
-- Cosine similarity distance (nhỏ = gần nhau)
-- Similarity score = 1 - distance
1 - (embedding <=> '[0.1, 0.2, ...]'::vector) AS similarity_score
```

**IVFFlat Index** để tăng tốc tìm kiếm:
```sql
CREATE INDEX idx_reports_embedding
ON diagnostic_reports USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);
-- lists = 50: phù hợp với dataset ~500-5000 báo cáo
```

**So sánh 2 phương pháp tìm kiếm**:

| Tiêu chí | RAG (Vector Search) | Keyword Search (SQL ILIKE) |
|---|---|---|
| Hiểu ngữ nghĩa | ✅ Có | ❌ Không |
| Tìm từ đồng nghĩa | ✅ Có | ❌ Không |
| Tốc độ | ⚡ Nhanh (có index) | ⚡ Rất nhanh |
| Không cần internet | ✅ Có | ✅ Có |
| Minh bạch | ❌ Black box | ✅ Rõ ràng |

---

### 2.3 `backend/api/dicom.py` — DICOM Upload & Stream

**Upload flow**:
```
1. Client gửi multipart/form-data chứa file .dcm
2. Backend đọc file bằng pydicom → parse metadata
   (PatientName, StudyDate, Modality, BodyPart, StudyInstanceUID)
3. Gửi file raw lên Orthanc: POST /instances
4. Orthanc trả về orthanc_id (UUID)
5. Backend lưu study vào PostgreSQL
```

**WADO Stream** (Web Access to DICOM Objects):
```
GET /api/dicom/wado?objectId={instance_id}
→ Backend gọi Orthanc: GET /instances/{id}/file
→ Stream bytes trực tiếp về browser
→ Cornerstone.js render ảnh DICOM
```

---

### 2.4 `backend/api/report.py` — Báo Cáo Chẩn Đoán

**Tạo báo cáo** (POST /api/report):
1. Lưu `findings`, `conclusion`, `recommendation` vào DB
2. Gọi `encode_text(findings + " " + conclusion)` → vector
3. Lưu vector vào `embedding` column
4. Cập nhật `studies.status = 'REPORTED'`

**Xuất PDF** (GET /api/report/{id}/pdf):
- Dùng `reportlab` tạo PDF
- Bao gồm: tiêu đề bệnh viện, thông tin BN, ngày chụp, kết quả, chữ ký bác sĩ

---

### 2.5 `backend/core/auth_utils.py` — Authentication

```python
# JWT Flow
POST /api/auth/login {username, password}
→ Verify password với bcrypt hash
→ Tạo JWT token (expire 8 giờ)
→ Client lưu token vào localStorage

# Mỗi request tiếp theo
Authorization: Bearer <JWT_TOKEN>
→ Backend decode → lấy user_id, role
→ Kiểm tra quyền (doctor/admin/technician)
```

---

## 3. Schema Cơ Sở Dữ Liệu — Chi Tiết

### Bảng `users`
```sql
id            SERIAL PRIMARY KEY
username      VARCHAR(50) UNIQUE NOT NULL
password_hash VARCHAR(255) NOT NULL        -- bcrypt hash
full_name     VARCHAR(100)
role          VARCHAR(20) CHECK IN ('admin','doctor','technician')
is_active     BOOLEAN DEFAULT TRUE
created_at    TIMESTAMP DEFAULT NOW()
```

### Bảng `patients`
```sql
id          SERIAL PRIMARY KEY
patient_id  VARCHAR(50) UNIQUE              -- Mã bệnh nhân bệnh viện
full_name   VARCHAR(100) NOT NULL
birth_date  DATE
gender      CHAR(1) CHECK IN ('M','F')
phone       VARCHAR(20)
address     TEXT
created_at  TIMESTAMP DEFAULT NOW()
```

### Bảng `studies` (Ca chụp)
```sql
id            SERIAL PRIMARY KEY
study_uid     VARCHAR(200) UNIQUE           -- DICOM Study Instance UID (global unique)
patient_id    INT REFERENCES patients(id)
study_date    DATE NOT NULL
modality      VARCHAR(10) CHECK IN ('CR','CT','MR','US','DX','MG')
body_part     VARCHAR(50)                   -- CHEST, HEAD, ABDOMEN, SPINE...
description   TEXT
status        VARCHAR(20) DEFAULT 'PENDING' -- PENDING → REPORTED → VERIFIED
technician_id INT REFERENCES users(id)
orthanc_id    VARCHAR(200)                  -- UUID trong Orthanc server
num_instances INT DEFAULT 0                 -- Số ảnh trong study
created_at    TIMESTAMP DEFAULT NOW()
```

### Bảng `diagnostic_reports` (Báo cáo) — **QUAN TRỌNG**
```sql
id              SERIAL PRIMARY KEY
study_id        INT REFERENCES studies(id) UNIQUE  -- 1 study = 1 báo cáo
doctor_id       INT REFERENCES users(id)
findings        TEXT NOT NULL                       -- Mô tả kết quả hình ảnh
conclusion      TEXT NOT NULL                       -- Kết luận chẩn đoán
recommendation  TEXT                                -- Đề nghị xử lý
report_date     TIMESTAMP DEFAULT NOW()
embedding       vector(1024)                        -- BGE-M3 dense vector

-- Index vector similarity
CREATE INDEX idx_reports_embedding
ON diagnostic_reports USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 50);
```

### Quan hệ
```
patients (1) ──< studies (N) ──── diagnostic_reports (1)
                    │
                    └── users (technician_id)
                diagnostic_reports.doctor_id ──── users
```

---

## 4. Kế Hoạch Triển Khai — 3 Tháng (12 Tuần)

### 🗓️ THÁNG 1 — Nền Tảng (Tuần 1–4)

#### Tuần 1: Hạ tầng & Cơ sở dữ liệu
- [ ] Cài Docker, khởi động PostgreSQL + pgvector + Orthanc
- [ ] Viết `init_db.sql` — tạo 4 bảng chính
- [ ] Test kết nối DB với psycopg2
- [ ] Test Orthanc API (upload, download DICOM thử)
- [ ] Setup project structure: `backend/`, `frontend/`, `orthanc/`
- [ ] Tạo `.env.example` và `config.py`

**Deliverable**: Docker compose chạy ổn, DB schema đã tạo

#### Tuần 2: Authentication & User Management
- [ ] Viết `core/auth_utils.py`: bcrypt hash, JWT tạo/xác thực
- [ ] Viết `api/auth.py`: POST /api/auth/login
- [ ] Tạo `frontend/login.html` với form đăng nhập
- [ ] Middleware verify JWT cho các route cần auth
- [ ] Viết `scripts/seed_data.py`: tạo user mẫu

**Deliverable**: Có thể đăng nhập qua web

#### Tuần 3: DICOM Upload & Worklist
- [ ] Viết `core/dicom_parser.py`: parse file .dcm lấy metadata
- [ ] Viết `core/orthanc_client.py`: upload /instances, get study
- [ ] Viết `api/dicom.py`: POST /upload, GET /wado
- [ ] Viết `api/worklist.py`: GET /worklist với filter, pagination
- [ ] Tạo `frontend/index.html`: bảng worklist + filter

**Deliverable**: Upload DICOM và xem worklist được

#### Tuần 4: DICOM Viewer
- [ ] Tạo `frontend/viewer.html` tích hợp Cornerstone.js
- [ ] Kết nối WADO endpoint để load ảnh DICOM
- [ ] Các tool cơ bản: pan, zoom, window/level
- [ ] Hiển thị thông tin study (BN, ngày, modality)

**Deliverable**: Xem được ảnh DICOM trên web

---

### 🗓️ THÁNG 2 — Core Features (Tuần 5–8)

#### Tuần 5: Báo Cáo Chẩn Đoán
- [ ] Viết `api/report.py`: CRUD báo cáo
- [ ] Tạo `frontend/report.html`: form nhập chẩn đoán
- [ ] Validate: chỉ bác sĩ mới viết báo cáo
- [ ] Cập nhật `studies.status` khi có báo cáo

**Deliverable**: Bác sĩ viết và xem được báo cáo

#### Tuần 6: BGE-M3 Embedding
- [ ] Viết `core/embeddings.py`: load BGE-M3, encode text
- [ ] Test encode với tiếng Việt y tế
- [ ] Tích hợp vào POST /api/report: tự động embed khi tạo báo cáo
- [ ] Viết `scripts/embed_reports.py`: batch embed báo cáo cũ

**Deliverable**: Mỗi báo cáo mới tự động có embedding

#### Tuần 7: RAG Vector Search
- [ ] Viết `core/rag_engine.py`: `search_reports()` dùng pgvector
- [ ] Viết `core/rag_engine.py`: `search_keyword()` dùng ILIKE
- [ ] Viết `api/search.py`: POST /search, GET /search/keyword
- [ ] Tạo `frontend/search.html`: giao diện tìm kiếm

**Deliverable**: Tìm kiếm ngữ nghĩa hoạt động

#### Tuần 8: Xuất PDF + Hoàn thiện UI
- [ ] Tích hợp reportlab: xuất PDF báo cáo chẩn đoán
- [ ] Hoàn thiện giao diện tất cả các trang
- [ ] Xử lý lỗi, loading states, responsive
- [ ] Test end-to-end toàn bộ luồng

**Deliverable**: Hệ thống hoàn chỉnh, dùng được

---

### 🗓️ THÁNG 3 — Đánh Giá & Báo Cáo (Tuần 9–12)

#### Tuần 9: Tạo Dataset Đánh Giá
- [ ] Chuẩn bị 50–100 báo cáo chẩn đoán mẫu (tiếng Việt)
- [ ] Viết 20–30 câu query test đại diện
- [ ] Tạo ground truth: mỗi query → list báo cáo liên quan
- [ ] Sử dụng `seed_data.py` để import dataset

**Deliverable**: Dataset đánh giá sẵn sàng

#### Tuần 10: Thực Nghiệm & Đánh Giá
- [ ] Chạy 2 hệ thống: RAG và Keyword với cùng query
- [ ] Tính các chỉ số:
  - **Precision@K** (K=5): bao nhiêu % kết quả top-K là đúng
  - **Recall@K**: bao nhiêu % relevant được tìm thấy trong top-K
  - **MRR** (Mean Reciprocal Rank): thứ hạng trung bình của kết quả đúng đầu tiên
  - **NDCG@K**: đánh giá xếp hạng có cân nhắc độ liên quan
- [ ] Ghi kết quả vào bảng đánh giá

**Deliverable**: Bảng số liệu so sánh RAG vs Keyword

#### Tuần 11: Phân Tích & Viết Báo Cáo
- [ ] Phân tích các case RAG tốt hơn / kém hơn Keyword
- [ ] Vẽ biểu đồ so sánh (bar chart, radar chart)
- [ ] Viết nhận xét: nguyên nhân, giải thích kết quả
- [ ] Viết phần kết luận cho luận văn

**Deliverable**: Chương kết quả thực nghiệm hoàn chỉnh

#### Tuần 12: Hoàn Thiện & Nộp
- [ ] Review toàn bộ code: clean up, comments
- [ ] Viết hướng dẫn cài đặt và demo
- [ ] Chuẩn bị slide thuyết trình
- [ ] Demo hệ thống live
- [ ] Nộp luận văn

---

## 5. Bộ Metrics Đánh Giá

### 5.1 Precision@K
```
Precision@K = (số kết quả đúng trong top-K) / K

Ví dụ: K=5, tìm thấy 3 kết quả đúng → Precision@5 = 3/5 = 0.6
```

### 5.2 Recall@K
```
Recall@K = (số kết quả đúng trong top-K) / (tổng số relevant)

Ví dụ: K=5, tìm 3 đúng, tổng relevant=4 → Recall@5 = 3/4 = 0.75
```

### 5.3 MRR (Mean Reciprocal Rank)
```
MRR = (1/|Q|) × Σ (1 / rank của kết quả đúng đầu tiên)

Ví dụ: query 1 → rank 1, query 2 → rank 3, query 3 → rank 2
MRR = (1/3) × (1/1 + 1/3 + 1/2) = (1/3) × 1.833 = 0.611
```

### 5.4 Kỳ vọng kết quả
| Metric | RAG (dự kiến) | Keyword (dự kiến) |
|---|---|---|
| Precision@5 | 0.65–0.80 | 0.50–0.65 |
| Recall@5 | 0.55–0.70 | 0.40–0.60 |
| MRR | 0.60–0.75 | 0.45–0.60 |

*Kỳ vọng RAG vượt trội trong các query mô tả lâm sàng, Keyword tốt hơn với từ khóa chính xác.*

---

## 6. Cấu Hình Orthanc

File `orthanc/orthanc.json`:

```json
{
  "Name": "PACS-Mini",
  "HttpPort": 8042,
  "DicomPort": 4242,
  "DicomAet": "PACS_MINI",
  "StorageDirectory": "/var/lib/orthanc/db",
  "AuthenticationEnabled": false,
  "RemoteAccessAllowed": true,
  "HttpCompressionEnabled": true
}
```

**Giải thích các tham số**:
- `DicomAet`: Tên AE title — dùng khi cấu hình kết nối từ máy chụp thật
- `DicomPort 4242`: Port nhận DICOM (C-STORE) từ máy X-quang
- `AuthenticationEnabled: false`: Tắt auth cho môi trường dev/thesis
- `StorageDirectory`: Thư mục lưu file DICOM (persist qua Docker volume)

---

## 7. File Quan Trọng & Vị Trí

| File | Vai trò quan trọng |
|---|---|
| `backend/core/embeddings.py` | Load BGE-M3, encode text → vector |
| `backend/core/rag_engine.py` | Vector search + Keyword search logic |
| `backend/database/init_db.sql` | Schema khởi tạo — **chạy 1 lần khi Docker start** |
| `backend/scripts/seed_data.py` | Tạo data mẫu — **chạy 1 lần** |
| `backend/scripts/embed_reports.py` | Batch embed — chạy lại nếu có báo cáo chưa có vector |
| `docker-compose.yml` | Toàn bộ hạ tầng — **điểm bắt đầu dự án** |
| `.env` | Biến cấu hình — **KHÔNG commit lên git** |

---

## 8. Bắt Đầu Từ Đâu? (Gợi Ý Cho Người Mới)

### Nếu bạn muốn **chạy thử hệ thống ngay**:
```
1. docker compose up -d
2. cd backend && pip install -r requirements.txt
3. copy .env.example .env
4. python scripts/seed_data.py
5. python main.py
6. Mở http://localhost:8000 → đăng nhập admin/admin123
```

### Nếu bạn muốn **hiểu cơ chế RAG**:
```
1. Đọc backend/core/embeddings.py → hiểu BGE-M3 encode
2. Đọc backend/core/rag_engine.py → hiểu vector search với pgvector
3. Đọc backend/database/init_db.sql → hiểu cột embedding vector(1024)
4. Test: POST /api/search với nội dung tiếng Việt
```

### Nếu bạn muốn **thêm tính năng mới**:
```
1. Thêm route trong backend/api/
2. Thêm hàm logic trong backend/core/
3. Đăng ký router trong backend/main.py
4. Thêm UI trong frontend/
```

---

## 9. Các Công Nghệ & Phiên Bản Đầy Đủ

```
# Python packages (requirements.txt)
fastapi==0.111.0          # REST API framework
uvicorn[standard]==0.30.1 # ASGI server
psycopg2-binary==2.9.9    # PostgreSQL adapter
pgvector==0.2.5           # pgvector Python client
pydicom==2.4.4            # Đọc file DICOM
requests==2.32.3          # Gọi Orthanc REST API
python-jose[cryptography]==3.3.0  # JWT
passlib[bcrypt]==1.7.4    # Mã hóa mật khẩu
python-multipart==0.0.9   # Upload file
FlagEmbedding==1.2.10     # BGE-M3 model
torch==2.3.0              # PyTorch (backend cho BGE-M3)
reportlab==4.2.0          # Tạo PDF
python-dotenv==1.0.1      # Load .env file
Pillow==10.3.0            # Xử lý ảnh

# Docker images
pgvector/pgvector:pg16        # PostgreSQL 16 + pgvector extension
orthancteam/orthanc:24.5.3    # Orthanc DICOM server

# Frontend (CDN)
Bootstrap 5.3               # CSS framework
Cornerstone.js              # DICOM viewer JavaScript library
```

---

## 10. Hướng Mở Rộng (Sau Luận Văn)

| Tính năng | Mô tả |
|---|---|
| **LLM tích hợp** | Dùng GPT/Gemini để sinh báo cáo tự động từ DICOM |
| **Kết nối máy chụp thật** | Cấu hình C-STORE AE để nhận ảnh từ máy X-quang |
| **Multi-modal RAG** | Kết hợp OCR ảnh DICOM + text báo cáo |
| **Sparse retrieval** | Kết hợp BM25 + Dense vector (hybrid search) |
| **HL7 FHIR** | Tích hợp tiêu chuẩn trao đổi dữ liệu y tế |
| **Scale up** | Chuyển sang Weaviate/Qdrant cho vector DB lớn hơn |
| **GPU inference** | Tăng tốc embedding với GPU server |

---

*Tài liệu này phục vụ mục đích học thuật và luận văn. Không dùng trong môi trường y tế thực tế khi chưa được kiểm định.*
