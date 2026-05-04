# 🏥 PACS++ — Tổng quan dự án

> Hệ thống lưu trữ hình ảnh y tế (PACS) tích hợp AI tìm kiếm thông minh (RAG)
> Giúp bác sĩ quản lý, tra cứu kết quả chẩn đoán hình ảnh (CT, MRI, X-ray) nhanh chóng.

---

## 1. Kiến trúc hệ thống

```
┌──────────────────────────────────────────────────────────────┐
│                     🖥️  React Frontend                       │
│                   Vite + React 18 (Port 5173)                │
│   Pages: Login | Worklist | Report | Search | Viewer | Admin │
└──────────────────────┬───────────────────────────────────────┘
                       │ fetch /api/*
┌──────────────────────▼───────────────────────────────────────┐
│                    ⚙️  FastAPI Backend                        │
│                    Python 3.12 (Port 8000)                    │
│                                                               │
│  ┌─────────┐  ┌───────────┐  ┌──────────┐  ┌─────────────┐  │
│  │ Auth    │  │ Worklist  │  │ DICOM    │  │ Report      │  │
│  │ JWT     │  │ CRUD      │  │ Upload   │  │ CRUD + PDF  │  │
│  └─────────┘  └───────────┘  └──────────┘  └──────┬──────┘  │
│                                                     │         │
│  ┌──────────────────────────────────────────────────▼──────┐  │
│  │              🧠 AI / RAG Engine                         │  │
│  │                                                         │  │
│  │  Query Router ──► Hybrid Search (Dense+BM25+RRF)        │  │
│  │       │                                                 │  │
│  │       ├──────► NL2SQL (Ollama/Gemini → SQL)             │  │
│  │       │                                                 │  │
│  │       └──────► Patient Lookup (ILIKE)                   │  │
│  └─────────────────────────────────────────────────────────┘  │
└───────┬──────────────────┬───────────────────┬────────────────┘
        │                  │                   │
┌───────▼──────┐  ┌────────▼───────┐  ┌────────▼───────┐
│ PostgreSQL   │  │ Orthanc DICOM  │  │ Ollama         │
│ + pgvector   │  │ Port 8042/4242 │  │ Port 11434     │
│ Port 5432    │  │                │  │ gemma4:e4b     │
│ (Docker)     │  │ (Docker)       │  │ qwen2.5-coder  │
└──────────────┘  └────────────────┘  └────────────────┘
```

---

## 2. Vai trò người dùng

| Role | Worklist | Upload DICOM | Viết Report | AI Search | Admin |
|---|:---:|:---:|:---:|:---:|:---:|
| 👑 `admin` | ✅ | ✅ | ✅ | ✅ | ✅ |
| 👨‍⚕️ `doctor` | ✅ | ❌ | ✅ | ✅ | ❌ |
| 🔧 `technician` | ✅ | ✅ | ❌ | ❌ | ❌ |
| 🧑 `patient` | Chỉ ca mình | ❌ | ❌ | ❌ | ❌ |

---

## 3. Cấu trúc thư mục

```
pacs_rag_system/
│
├── docker-compose.yml                   # PostgreSQL + Orthanc
│
├── backend-v2/                          # ⚙️ FASTAPI BACKEND
│   ├── main.py                          # App entry + routers
│   ├── config.py                        # Đọc .env
│   ├── .env                             # DB, JWT, Ollama config
│   ├── requirements.txt                 # Dependencies
│   │
│   ├── api/                             # ── API Endpoints ──
│   │   ├── auth.py                      # /api/auth — JWT login/register
│   │   ├── worklist.py                  # /api/worklist — Quản lý ca chụp
│   │   ├── dicom.py                     # /api/dicom — Upload/download .dcm
│   │   ├── report.py                    # /api/report — Báo cáo + auto-embed
│   │   ├── search.py                    # /api/search — RAG search (UC12-14)
│   │   ├── ask.py                       # /api/ask — Hỏi đáp NL2SQL (UC15)
│   │   ├── admin.py                     # /api/admin — Quản trị users
│   │   └── dicom_editor.py              # /api/editor — Sửa metadata DICOM
│   │
│   ├── core/                            # ── Business Logic ──
│   │   ├── auth_utils.py                # JWT + password hashing
│   │   ├── embeddings.py                # e5-large model (1024 dim)
│   │   ├── rag_engine.py                # Keyword + Dense + Hybrid search
│   │   ├── query_router.py              # Intent classifier (semantic)
│   │   ├── nl2sql_engine.py             # Câu hỏi → SQL (LLM)
│   │   ├── orthanc_client.py            # HTTP client → Orthanc
│   │   └── dicom_parser.py              # Parse .dcm metadata
│   │
│   ├── database/                        # ── Database ──
│   │   ├── connection.py                # Connection pool (psycopg2)
│   │   ├── base.py                      # CRUD helpers
│   │   └── init_db.sql                  # Schema: 5 tables + pgvector
│   │
│   ├── models/                          # ── Data Models ──
│   │   ├── patient.py                   # Patient
│   │   ├── study.py                     # Study (ca chụp)
│   │   ├── report.py                    # DiagnosticReport
│   │   ├── user.py                      # User
│   │   └── refresh_token.py             # JWT Refresh Token
│   │
│   └── scripts/                         # ── Scripts tiện ích ──
│       ├── seed_data.py                 # Tạo data mẫu (patients, users)
│       ├── seed_reports.py              # Tạo 75 báo cáo y tế mẫu
│       ├── embed_existing.py            # Batch embed reports → vector
│       ├── bulk_upload.py               # Bulk upload DICOM
│       ├── benchmark_embeddings.py      # So sánh embedding models
│       └── ...                          # check_data, export, test scripts
│
├── frontend-react/src/                  # 🖥️ REACT FRONTEND
│   ├── App.jsx                          # Router + Auth guard
│   │
│   ├── api/                             # ── API wrappers (fetch) ──
│   │   ├── auth.js                      # Login, Register
│   │   ├── worklist.js                  # Worklist CRUD
│   │   ├── dicom.js                     # DICOM upload/download
│   │   ├── report.js                    # Report CRUD
│   │   ├── search.js                    # RAG search + NL2SQL
│   │   └── patient.js                   # Patient lookup
│   │
│   ├── components/                      # ── Components ──
│   │   ├── layout/
│   │   │   ├── AppLayout.jsx            # Main wrapper
│   │   │   ├── Sidebar.jsx              # Navigation
│   │   │   └── Topbar.jsx               # Header + user info
│   │   └── shared/
│   │       ├── FilterBar.jsx            # Search/filter
│   │       ├── RoleGuard.jsx            # Phân quyền UI
│   │       ├── StatCard.jsx             # Thẻ thống kê
│   │       ├── StatusBadge.jsx          # Badge trạng thái
│   │       └── UploadZone.jsx           # Drag & drop upload
│   │
│   ├── pages/                           # ── Pages ──
│   │   ├── Login/                       # 🔐 Đăng nhập
│   │   ├── Worklist/                    # 📋 Danh sách ca chụp
│   │   ├── Report/                      # 📝 Viết báo cáo
│   │   ├── Search/                      # 🔍 AI tìm kiếm
│   │   ├── Viewer/                      # 🖼️ Xem ảnh DICOM
│   │   ├── MyStudies/                   # 🧑 Ca chụp của tôi
│   │   ├── Admin/                       # 👑 Quản trị
│   │   └── Compare/                     # 🔄 So sánh studies
│   │
│   └── styles/                          # ── CSS ──
│       ├── variables.css                # Design tokens
│       ├── base.css                     # Reset
│       ├── layout.css                   # Grid/Flex
│       └── components.css               # UI components
│
└── docs/                                # 📚 Tài liệu
    ├── 00_project_overview.md           # ← File này
    ├── 01_system_overview.md            # Tổng quan hệ thống
    ├── 02_erd_database.md               # Database schema
    ├── 03_backend_architecture.md       # Kiến trúc backend
    ├── 04_frontend_architecture.md      # Kiến trúc frontend
    ├── 05_sprint_roadmap.md             # Lộ trình phát triển
    ├── 06_ui_wireframes.md              # Wireframes
    ├── 07_feature_list.md               # Danh sách tính năng
    ├── 08_use_cases.md                  # Use cases (UC01-UC20)
    ├── 09_graph_rag_plan.md             # [PLANNED] Graph RAG
    └── 10_graph_rag_analysis.md         # Phân tích Graph RAG
```

---

## 4. Database Schema

```
patients ──1:N──► studies ──1:1──► diagnostic_reports
                     │                     │
                     │ technician_id       │ doctor_id
                     ▼                     ▼
                   users ◄─────────────── users
                     │
                     │ linked_patient_id
                     ▼
                   patients
```

**5 bảng chính:**

| Bảng | Mô tả | Cột quan trọng |
|---|---|---|
| `patients` | Bệnh nhân | patient_id, full_name, gender, birth_date |
| `studies` | Ca chụp | modality (CR/CT/MR/US/DX/MG), status, study_date |
| `diagnostic_reports` | Báo cáo | findings, conclusion, **embedding** (vector 1024d) |
| `users` | Tài khoản | role (admin/doctor/technician/patient) |
| `refresh_tokens` | JWT tokens | token_hash, expires_at, revoked |

---

## 5. API Endpoints

### Auth
| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/auth/login` | Đăng nhập → access + refresh token |
| POST | `/api/auth/register` | Đăng ký tài khoản |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Thông tin user hiện tại |

### Worklist & DICOM
| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/worklist` | Danh sách ca chụp (filter, sort, paginate) |
| GET | `/api/worklist/{id}` | Chi tiết 1 ca |
| POST | `/api/dicom/upload` | Upload file .dcm → Orthanc |
| GET | `/api/dicom/instances/{id}` | Lấy DICOM instances |

### Report
| Method | Endpoint | Mô tả |
|---|---|---|
| POST | `/api/report` | Tạo báo cáo (auto-embed vector) |
| PUT | `/api/report/{id}` | Cập nhật báo cáo |
| GET | `/api/report/{study_id}` | Xem báo cáo theo study |
| GET | `/api/report/{id}/pdf` | Xuất PDF |

### 🔍 AI Search (RAG)
| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/search/keyword?q=` | UC12: Keyword search (ILIKE) |
| POST | `/api/search` | UC13-14: Dense / Hybrid search |
| POST | `/api/ask` | UC15: Hỏi đáp tự nhiên → SQL + RAG |

### Admin
| Method | Endpoint | Mô tả |
|---|---|---|
| GET | `/api/admin/users` | Danh sách users (admin only) |
| PUT | `/api/admin/users/{id}` | Cập nhật user |

---

## 6. RAG Search Pipeline

```
User gõ câu hỏi
      │
      ▼
┌─────────────────────────────┐
│    Query Router             │  Semantic similarity classification
│    (query_router.py)        │  So sánh câu hỏi với 60+ examples
└─────────┬───────────────────┘
          │
    ┌─────┼──────────┬──────────────┐
    ▼     ▼          ▼              ▼
PATIENT  STRUCTURED  SEMANTIC     HYBRID
LOOKUP   (SQL)       (RAG)        (cả 2)
    │     │          │
    │     │     ┌────┴────┐
    │     │     ▼         ▼
    │     │   Dense     BM25
    │     │   (e5→pgvector) (keyword)
    │     │     │         │
    │     │     └────┬────┘
    │     │          ▼
    │     │     RRF Fusion
    │     │     (rank merge)
    │     │          │
    │     │     Threshold ≥70%
    │     │          │
    ▼     ▼          ▼
┌─────────────────────────┐
│       Results           │
└─────────────────────────┘
```

**4 loại intent:**
- **PATIENT_LOOKUP** → "Nguyễn Văn A" → ILIKE trên full_name
- **STRUCTURED** → "bao nhiêu ca CT hôm nay" → LLM sinh SQL → execute
- **SEMANTIC** → "tổn thương phổi dạng nốt" → Dense+BM25+RRF → top-K
- **HYBRID** → mập mờ giữa SQL và RAG → chạy cả 2

---

## 7. Khởi chạy nhanh

```bash
# 1. Infrastructure (Docker)
cd pacs_rag_system
docker-compose up -d

# 2. Backend
cd backend-v2
pip install -r requirements.txt
python main.py                    # → http://localhost:8000

# 3. Frontend
cd frontend-react
npm install && npm run dev        # → http://localhost:5173

# 4. AI (Ollama)
ollama serve                      # → http://localhost:11434
```

**Tài khoản mặc định:**

| User | Password | Role |
|---|---|---|
| `admin` | `admin123` | 👑 Admin |
| `doctor1` | `doctor123` | 👨‍⚕️ Doctor |
| `tech1` | `tech123` | 🔧 Technician |

---

## 8. Trạng thái phát triển

| Module | Trạng thái | Ghi chú |
|---|---|---|
| Auth (JWT) | ✅ Done | Login, Register, Refresh, Role guard |
| Worklist | ✅ Done | CRUD, Filter, Sort, Paginate |
| DICOM Upload | ✅ Done | Upload → Orthanc, parse metadata |
| DICOM Viewer | ✅ Done | Cornerstone.js integration |
| Report | ✅ Done | CRUD + auto-embed + PDF export |
| Keyword Search | ✅ Done | UC12: ILIKE |
| Dense Search | ✅ Done | UC13: e5-large + pgvector |
| Hybrid Search | ✅ Done | UC14: Dense + BM25 + RRF |
| NL2SQL | ✅ Done | UC15: Ollama/Gemini → SQL |
| Query Router | ✅ Done | Semantic intent classification |
| Admin Panel | ✅ Done | User management |
| **Graph RAG** | ⬜ Planned | NetworkX + Gemma 4 entity extraction |
