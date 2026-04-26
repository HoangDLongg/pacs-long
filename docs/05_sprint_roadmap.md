# 05 — Sprint Plan & Roadmap

## Sprint 0 — Infrastructure Setup ✅ HOÀN THÀNH

| Hạng mục | Trạng thái |
|---|---|
| Docker Compose: PostgreSQL 16 + pgvector | ✅ Done |
| Docker Compose: Orthanc 24.5.3 | ✅ Done |
| FastAPI backend khởi động thành công (:8000) | ✅ Done |
| Cấu hình Ollama (qwen2.5-coder:7b) | ✅ Done |

---

## Sprint 1 — Backend v2 + Login + Data Pipeline ✅ HOÀN THÀNH

| Hạng mục | Trạng thái |
|---|---|
| Backend-v2 rewrite (14 files) | ✅ Done |
| JWT Auth (bcrypt + python-jose) | ✅ Done |
| Worklist API (list + filter + stats) | ✅ Done |
| DICOM Upload API (Orthanc integration) | ✅ Done |
| Report CRUD API | ✅ Done |
| Database schema: 4 bảng + pgvector | ✅ Done |
| Seed data: 5 staff + 21 patient accounts (26 users) | ✅ Done |
| DICOM Name Editor tool (web UI) | ✅ Done |
| Bulk upload 13,499 DICOM files → Orthanc | ✅ Done |
| 21 bệnh nhân, 75 ca chụp loaded | ✅ Done |
| React Vite setup + Login page | ✅ Done |
| Hospital Dark Theme CSS design system | ✅ Done |

### Dữ liệu hiện tại trong DB

| Bảng | Số lượng |
|---|---|
| patients | 21 |
| users | 26 (5 staff + 21 patient) |
| studies | 75 |
| DICOM files trên Orthanc | 13,495 |

---

## Sprint 2 — Frontend React Pages ✅ HOÀN THÀNH

### Mục tiêu
Build 8 trang cho React SPA.

| Hạng mục | Ưu tiên | Trạng thái |
|---|---|---|
| Layout: Sidebar + Topbar + AppLayout | P0 | ✅ Done |
| Shared components (StatusBadge, StatCard, FilterBar...) | P0 | ✅ Done |
| API layer (worklist.js, dicom.js, report.js, patient.js, search.js) | P0 | ✅ Done |
| Worklist page (dashboard + table + filter) | P0 | ✅ Done |
| Viewer page (Cornerstone3D v4 DICOM viewer) | P0 | ✅ Done |
| Report page (create + update + readonly + PDF) | P0 | ✅ Done |
| MyStudies page (patient portal) | P1 | ✅ Done |
| Admin page (user management) | P1 | ✅ Done |
| Search page (4 tabs: Hybrid/Dense/Keyword/NL2SQL) | P0 | ✅ Done |
| Compare page (side-by-side 2 studies) | P2 | ✅ Done |

### Backend APIs cần bổ sung cho Sprint 2

| Endpoint | Cho trang |
|---|---|
| GET /api/my-studies | MyStudies (patient) |
| GET /api/admin/users | Admin |
| GET /api/admin/system | Admin |

---

## Sprint 3 — RAG Engine Integration ✅ HOÀN THÀNH

| Hạng mục | Mô tả | Trạng thái |
|---|---|---|
| multilingual-e5-large embedding | Text → vector 1024d | ✅ Done |
| Dense search (pgvector cosine) | Tìm báo cáo tương tự | ✅ Done |
| BM25 keyword search | Tìm theo từ khóa | ✅ Done |
| Hybrid search (Dense + BM25 + RRF) | Kết hợp 2 phương pháp | ✅ Done |
| NL2SQL (Ollama/Gemini) | Câu hỏi → SQL query | ✅ Done |
| Query Router (embedding-based) | STRUCTURED/SEMANTIC/HYBRID | ✅ Done |
| Search page hoàn chỉnh | 4 tab search + NL2SQL + Compare | ✅ Done |

---

## Sprint 4 — Polish + Documentation 🚧 ĐANG LÀM

| Hạng mục | Mô tả |
|---|---|
| PDF export (ReportLab) | Xuất báo cáo PDF |
| Admin CRUD users | Thêm/sửa/khoá user |
| Responsive layout | Sidebar auto-collapse |
| Loading skeleton | Animation chuyên nghiệp |
| Error boundary | Bắt lỗi React toàn cục |
| Unit tests (Pytest) | Backend test coverage |
| Final documentation | Báo cáo luận văn |

---

## Lệnh khởi chạy hệ thống

```powershell
# 1. Khởi động Docker (PostgreSQL + Orthanc)
cd pacs_rag_system
docker compose up -d

# 2. Khởi động Backend
cd backend-v2
.\venv\Scripts\activate
python main.py  # Port 8000

# 3. Khởi động Frontend (dev mode)
cd ..\frontend-react
npm run dev  # Port 5173

# Truy cập:
# Frontend: http://localhost:5173
# Backend API docs: http://localhost:8000/docs
# Orthanc: http://localhost:8042
# DICOM Editor: http://localhost:8000/editor
```

---

## Test Accounts

| Username | Password | Role |
|---|---|---|
| admin | admin123 | Admin |
| dr.nam | doctor123 | Doctor |
| dr.lan | doctor123 | Doctor |
| tech.hung | tech123 | Technician |
| tech.mai | tech123 | Technician |

Patient accounts: `{PatientID}` / `{PatientID}@`

---

## Cấu trúc thư mục

```
pacs_rag_system/
├── docker-compose.yml
├── .gitignore
├── README.md
│
├── backend-v2/                 # FastAPI (Python 3.12)
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── .env
│   ├── api/                    # 5 routers
│   ├── core/                   # Auth, DICOM parser, Orthanc client
│   ├── database/               # Connection pool + schema SQL
│   ├── scripts/                # Seed, bulk upload, edit names
│   └── templates/              # DICOM editor web tool
│
├── frontend-react/             # React 18 + Vite 5
│   ├── vite.config.js          # Proxy /api → :8000
│   └── src/
│       ├── api/                # API wrappers
│       ├── hooks/              # useAuth
│       ├── components/         # Shared + Layout
│       ├── pages/              # 7 pages
│       └── styles/             # Hospital dark theme CSS
│
├── orthanc/                    # Orthanc config
│   └── orthanc.json
│
└── docs/                       # 8 tài liệu thiết kế
```
