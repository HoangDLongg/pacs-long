# 05 — Sprint Plan & Roadmap

## Sprint 0 — Infrastructure Setup ✅ HOÀN THÀNH

| Hạng mục | Trạng thái |
|---|---|
| Docker Compose: PostgreSQL 16 + pgvector | ✅ Done |
| Docker Compose: Orthanc 24.5.3 | ✅ Done |
| FastAPI backend khởi động thành công (:8000) | ✅ Done |
| JWT Auth, Worklist, Dicom, Report, Search, Ask API | ✅ Done |
| Seed data: 5 users, 30 bệnh nhân, 44 ca chụp | ✅ Done |
| NL2SQL engine: Rule-based + Ollama + Gemini fallback | ✅ Done |
| BGE-M3 embedding model tích hợp pgvector | ✅ Done |
| Cấu hình Ollama (qwen2.5-coder:7b) thay Gemini | ✅ Done |

---

## Sprint 1 — React + Vite Frontend Migration 🚧 ĐANG LÀM

### Mục tiêu
Thay thế HTML thuần bằng React SPA chuyên nghiệp, đầy đủ tính năng.

### Cách tiếp cận (đã quyết định)

> **Dùng Vite** thay vì CDN Babel — tránh mọi vấn đề scope/transpile của CDN approach.

```bash
# Tạo project Vite trong thư mục frontend
cd pacs_rag_system
npx create-vite@latest frontend-react -- --template react
cd frontend-react
npm install
npm install react-router-dom
npm run dev   # dev server :5173, proxy /api → :8000
```

### Deliverables Sprint 1

| Hạng mục | Ưu tiên |
|---|---|
| Vite project setup + proxy config | P0 |
| Design system CSS (4 files) | P0 |
| Auth utility + API layer | P0 |
| AppLayout + Sidebar + Topbar | P0 |
| Login page | P0 |
| Worklist page (stat cards + table) | P0 |
| Report page (create + update) | P1 |
| Search page (4 tabs) | P1 |
| Viewer page (Orthanc iframe) | P1 |
| Admin page | P2 |

### Tiêu chí Done Sprint 1
- [ ] Đăng nhập thành công với admin/admin123
- [ ] Sidebar collapse/expand hoạt động
- [ ] Worklist load danh sách 44 ca chụp từ API
- [ ] Filter theo date, modality, status
- [ ] Tạo/cập nhật báo cáo từ doctor account
- [ ] Tìm kiếm keyword trả kết quả

---

## Sprint 2 — DICOM Viewer + PDF Report

| Hạng mục | Mô tả |
|---|---|
| Cornerstone.js integration | Xem ảnh DICOM trực tiếp, không cần Orthanc web UI |
| Viewport tools | Window/Level (WW/WL), Zoom, Pan, Reset |
| Multi-frame support | Scroll qua các frame CT/MR |
| ReportLab PDF polish | Template chuyên nghiệp với logo bệnh viện |
| Print stylesheet | In báo cáo trực tiếp từ browser |

---

## Sprint 3 — AI Features

| Hạng mục | Mô tả |
|---|---|
| RAG UI nâng cao | Highlight match trong kết quả |
| Chat interface | Chat box hỏi đáp Real-time streaming |
| Semantic search auto-suggest | Gợi ý câu hỏi khi gõ |
| Report template | Gợi ý findings từ RAG khi bác sĩ đang gõ |
| Analytics dashboard | Biểu đồ thống kê theo tháng/modality |

---

## Sprint 4 — Admin + Polish

| Hạng mục | Mô tả |
|---|---|
| User management CRUD | Thêm/sửa/khoá user |
| Role-based audit log | Log mọi action |
| Responsive mobile | Sidebar collapse auto trên màn nhỏ |
| Dark/light mode toggle | |
| Loading skeleton | Thay spinner bằng skeleton animation |
| Error boundary | Bắt lỗi React toàn cục |

---

## Lệnh khởi chạy hệ thống

```powershell
# 1. Khởi động Docker (PostgreSQL + Orthanc)
cd pacs_rag_system
docker compose up -d

# 2. Khởi động Ollama (terminal riêng)
ollama serve
# Nếu chưa có model:
ollama pull qwen2.5-coder:7b

# 3. Khởi động Backend
cd backend
.\venv\Scripts\activate
python main.py  # Port 8000

# 4. Khởi động Frontend (dev mode)
cd ..\frontend-react
npm run dev  # Port 5173

# Truy cập:
# Frontend: http://localhost:5173
# Backend API docs: http://localhost:8000/docs
# Orthanc: http://localhost:8042
```

---

## Cấu trúc thư mục dự án tổng thể

```
pacs_rag_system/
├── docker-compose.yml          # PostgreSQL + Orthanc
├── .gitignore
│
├── backend/                    # FastAPI
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── .env                    # KHÔNG commit
│   ├── api/
│   ├── core/
│   ├── database/
│   ├── scripts/
│   └── frontend/               # Sau khi build Vite: copy dist/ vào đây
│
└── frontend-react/             # React + Vite (Sprint 1)
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── styles/
        ├── api/
        ├── hooks/
        ├── components/
        └── pages/
```
