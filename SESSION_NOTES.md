# 📋 SESSION NOTES — PACS Mini + RAG System
> Hoàng Đức Long — Luận văn Tốt nghiệp  
> Cập nhật: 26/03/2026

---

## 🧠 Tóm Tắt Những Gì Đã Thảo Luận

### Hiện trạng dự án
- **Code đã có đầy đủ** tại `e:\HoangDucLong_javisai\pacs_rag_system\`
- Code **VƯỢT kế hoạch gốc** — đã có thêm: Hybrid Search, NL2SQL, Query Router, Answer Generator, Vietnamese Normalizer
- **Chưa chạy được** vì chưa cài môi trường (Docker, Python đúng cách)

### Môi trường máy (26/03/2026)
- Windows 10 Home Single Language
- Python 3.12.9 ✅ (đã cài)
- Docker Desktop: **vừa cài, đang cần restart máy** ⚠️
- Ollama: chưa cài

---

## 🏗️ PHÂN TÍCH HỆ THỐNG PACS

### 6 Module chức năng

| Module | Chức năng | Vai trò |
|--------|-----------|---------|
| 1. Auth | Đăng nhập JWT, phân quyền | Admin/Doctor/Tech |
| 2. Worklist | Danh sách ca chụp, filter, stats | Tất cả |
| 3. DICOM Upload & Viewer | Upload .dcm, Cornerstone.js | Tech & Tất cả |
| 4. Báo cáo chẩn đoán | CRUD báo cáo + PDF | Doctor |
| 5. Tìm kiếm thông minh | Keyword / Dense / Hybrid / NL2SQL | Doctor |
| 6. Admin Panel | Quản lý users (**CHƯA CÓ - cần làm**) | Admin |

### 3 tài khoản mặc định
```
admin      / admin123   → Quản trị
dr.nam     / doctor123  → Bác sĩ
tech.hung  / tech123    → Kỹ thuật viên
```

---

## 🗄️ THIẾT KẾ CSDL

### 4 bảng chính
```
users → patients → studies → diagnostic_reports
                                    ↓
                            embedding vector(1024) ← BGE-M3
```

### Luồng chính
```
Upload .dcm → Orthanc lưu → DB lưu study (PENDING)
Bác sĩ viết báo cáo → BGE-M3 encode → vector lưu vào DB (REPORTED)
Tìm kiếm → pgvector cosine similarity → kết quả
```

---

## 🎨 THIẾT KẾ WEB (Frontend)

### Design System
```
Màu nền:      #0a0f1e  (dark navy)
Màu card:     #0f1729
Màu accent:   #00c8ff  (cyan - brand)
Màu AI/RAG:   #7c3aed  (purple)
Font:         Inter (Google Fonts)
```

### 6 trang cần có
| Trang | File | Trạng thái |
|-------|------|-----------|
| Đăng nhập | login.html | ✅ Có (cần redesign) |
| Worklist | index.html | ✅ Có (cần redesign) |
| DICOM Viewer | viewer.html | ✅ Có (cần redesign) |
| Báo cáo | report.html | ✅ Có (cần redesign) |
| Tìm kiếm | search.html | ✅ Có (cần redesign) |
| Admin Panel | admin.html | ❌ **CHƯA CÓ - cần tạo mới** |

### Layout chính
```
┌──────────────┬─────────────────────────────────┐
│ SIDEBAR 220px│ MAIN CONTENT (topbar + content)  │
│ - Logo       │                                  │
│ - Menu       │                                  │
│ - User info  │                                  │
└──────────────┴─────────────────────────────────┘
```
> ⚠️ UI hiện tại không có sidebar — cần rebuild theo layout mới

---

## 📦 DATA MẪU

### Tình trạng data tiếng Việt
| Nguồn | Nội dung | Cách lấy |
|-------|---------|---------|
| VinDr-CXR | 18k DICOM X-quang + labels tiếng Việt | physionet.org (đăng ký 3-7 ngày) |
| VinDr Kaggle | DICOM (không có text báo cáo) | kaggle.com (đăng ký miễn phí) |
| ViX-Ray | 5,400 X-quang + findings tiếng Việt | Chưa public, email tác giả |

### Kế hoạch lấy data
```
DICOM files  → Kaggle VinDr (nếu có tài khoản Kaggle)
              hoặc OsiriX sample: https://www.osirix-viewer.com/resources/dicom-image-library/
Text báo cáo → Sinh 100 báo cáo tiếng Việt tổng hợp (AI sinh)
              → Song song đăng ký PhysioNet VinDr-CXR cho luận văn thật
```

---

## 🚀 KẾ HOẠCH TRIỂN KHAI

### Sprint 0 — Setup (Làm NGAY sau restart)
```bash
# 1. Mở Docker Desktop, chờ icon xanh ở taskbar
# 2. Chạy trong terminal tại thư mục pacs_rag_system:
docker compose up -d

# 3. Kiểm tra
docker compose ps

# 4. Cài Python packages
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 5. Copy config
copy .env.example .env

# 6. Tạo data mẫu
python scripts/seed_data.py

# 7. Chạy server
python main.py

# 8. Mở browser: http://localhost:8000
```

### Sprint 1 — Redesign Frontend (Tuần 1, sau setup)
- [ ] Tạo `frontend/shared/styles.css` — design system tập trung
- [ ] Tạo `frontend/shared/sidebar.js` — sidebar dùng chung
- [ ] Rebuild `login.html` — glassmorphism, split layout
- [ ] Rebuild `index.html` — worklist với sidebar
- [ ] Rebuild `viewer.html` — DICOM viewer cải tiến
- [ ] Rebuild `report.html` — form báo cáo đẹp
- [ ] Rebuild `search.html` — search UI cải tiến
- [ ] Tạo `admin.html` — admin panel **MỚI**

### Sprint 2 — Test & Fix (Tuần 2)
- [ ] Test toàn bộ luồng
- [ ] Cài Ollama + test NL2SQL: `ollama pull qwen2.5-coder:7b`
- [ ] Vá lỗi phát sinh

### Sprint 3 — Dataset & Evaluation (Tuần 3-4)
- [ ] Sinh 100 báo cáo tiếng Việt mẫu
- [ ] Viết `scripts/evaluate.py` (Precision@K, Recall@K, MRR, NDCG)
- [ ] Chạy so sánh 3 phương pháp: Keyword / Dense / Hybrid

### Sprint 4 — Viết Luận Văn (Tháng 2-3)
- [ ] Chương 1: Giới thiệu
- [ ] Chương 2: Cơ sở lý thuyết
- [ ] Chương 3: Thiết kế hệ thống
- [ ] Chương 4: Thực nghiệm & đánh giá
- [ ] Chương 5: Kết luận
- [ ] Video demo + Slide + Bảo vệ 🎓

---

## 🔑 ĐIỂM MẠNH CỦA DỰ ÁN (Nhấn mạnh trong luận văn)

| Tính năng | Đóng góp |
|-----------|---------|
| Hybrid Search (Dense + BM25 + RRF) | Kết hợp 2 phương pháp, vượt trội đơn lẻ |
| Vietnamese Text Normalizer | Xử lý tiếng Việt y tế cho BM25 |
| NL2SQL Engine | Rule-based → Ollama → Gemini fallback |
| Query Router | Tự động phân loại STRUCTURED/SEMANTIC/HYBRID |
| `/api/ask` Unified | Một endpoint xử lý mọi câu hỏi tự nhiên |

---

## ⚠️ VIỆC CẦN LÀM SAU KHI RESTART MÁY

1. **Kiểm tra Docker Desktop** đã chạy chưa (icon taskbar)
2. **`docker compose up -d`** trong thư mục `pacs_rag_system`
3. **Báo lại** để tiếp tục Sprint 0 → Sprint 1

---

## 📁 Cấu trúc thư mục quan trọng
```
pacs_rag_system/
├── backend/
│   ├── main.py              ← Entry point
│   ├── .env                 ← Config (KHÔNG commit git)
│   ├── api/
│   │   ├── ask.py           ← NL2SQL + RAG unified
│   │   ├── search.py        ← Search endpoints
│   │   └── ...
│   ├── core/
│   │   ├── rag_engine.py    ← 3 search methods
│   │   ├── nl2sql_engine.py ← NL to SQL
│   │   ├── query_router.py  ← Intent classification
│   │   └── nlp/
│   │       └── vietnamese_normalizer.py
│   ├── database/
│   │   └── init_db.sql      ← Schema (auto-run khi Docker start)
│   └── scripts/
│       ├── seed_data.py     ← Tạo data mẫu
│       └── embed_reports.py ← Batch embed
├── frontend/                ← Cần redesign toàn bộ
├── orthanc/orthanc.json    ← DICOM server config
└── docker-compose.yml      ← PostgreSQL + Orthanc
```

---

*File này lưu toàn bộ context của buổi làm việc ngày 26/03/2026.*  
*Lần sau chat: đọc file này để nhớ lại vị trí và tiếp tục công việc.*
