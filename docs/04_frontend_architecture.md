# 04 — Frontend Architecture: React + Vite SPA

## Quyết định kỹ thuật quan trọng

| Vấn đề | Lựa chọn | Lý do |
|---|---|---|
| Framework | **React 18** | Component-based, ecosystem lớn, phù hợp SPA |
| Build tool | **Vite** | HMR nhanh, cấu hình đơn giản, no CDN issues |
| Routing | **React Router v6** | Standard cho React SPA |
| CSS | **Vanilla CSS** (file riêng) | Kiểm soát hoàn toàn, không phụ thuộc framework |
| State | **useState + useEffect** | Đủ dùng, không cần Redux |
| HTTP | **fetch API** (wrapper) | Nhẹ, không cần axios |
| Deploy | Vite build → FastAPI serve static | Không cần server riêng |

---

## Cấu trúc thư mục Frontend

```
frontend-react/
├── index.html               # HTML shell — Vite entry point
├── vite.config.js           # Proxy /api → localhost:8000
├── package.json
│
├── src/
│   ├── main.jsx             # React app mount vào #root
│   ├── App.jsx              # Router setup, auth guard
│   │
│   ├── styles/              # CSS tách riêng từng layer
│   │   ├── variables.css    # Design tokens (màu, spacing, font)
│   │   ├── base.css         # Reset, typography, animations, utilities
│   │   ├── layout.css       # Sidebar, Topbar, AppShell layout
│   │   └── components.css   # Button, Card, Table, Form, Badge...
│   │
│   ├── api/                    # API wrappers (tách 6 file)
│   │   ├── auth.js             # Login, Register, Refresh
│   │   ├── worklist.js         # Worklist CRUD
│   │   ├── dicom.js            # DICOM upload/download
│   │   ├── report.js           # Report CRUD
│   │   ├── search.js           # RAG search + NL2SQL
│   │   └── patient.js          # Patient lookup
│   │
│   ├── hooks/
│   │   └── useAuth.js       # Custom hook: token, user, login, logout
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.jsx  # Navigation sidebar (collapsible)
│   │   │   ├── Topbar.jsx   # Page header + actions
│   │   │   └── AppLayout.jsx# Shell = Sidebar + main area + Outlet
│   │   │
│   │   └── shared/
│   │       ├── FilterBar.jsx      # Search/filter bar
│   │       ├── RoleGuard.jsx      # Role-based access control
│   │       ├── StatCard.jsx       # Dashboard thống kê
│   │       ├── StatusBadge.jsx    # PENDING/REPORTED/VERIFIED
│   │       └── UploadZone.jsx     # Drag & drop DICOM upload
│   │
│   └── pages/
│       ├── Login.jsx        # Đăng nhập
│       ├── Worklist.jsx     # Danh sách ca chụp (trang chính)
│       ├── Viewer.jsx       # Xem ảnh DICOM
│       ├── Report.jsx       # Nhập/xem báo cáo chẩn đoán
│       ├── Search.jsx       # Tìm kiếm thông minh
│       └── Admin.jsx        # Quản trị hệ thống
│
├── dist/                    # Output sau `vite build` — copy vào backend/frontend/
└── public/                  # Static assets (favicon, v.v.)
```

---

## Sơ đồ Component Tree

```
App (Router)
├── /login → Login
│   ├── BrandingPanel (bên trái)
│   └── LoginForm (bên phải)
│
└── AppLayout (Protected — check JWT)
    ├── Sidebar
    │   ├── LogoSection (PACS++)
    │   ├── NavItems (filter by role)
    │   │   ├── NavItem: Worklist
    │   │   ├── NavItem: Tìm kiếm
    │   │   ├── NavItem: Báo cáo
    │   │   └── NavItem: Quản trị (admin only)
    │   └── UserFooter (avatar, name, role, logout)
    │
    └── MainArea
        ├── Topbar (title, subtitle, actions)
        │
        └── PageContent (Outlet)
            ├── /worklist → Worklist
            │   ├── StatCards (Tổng / Chờ / Báo cáo / Xác nhận)
            │   ├── UploadZone (technician + admin only)
            │   ├── FilterBar (date, modality, status)
            │   └── DataTable (danh sách ca chụp)
            │
            ├── /search → Search
            │   ├── SearchTabs (keyword/dense/hybrid/ask)
            │   ├── SearchInput + Submit
            │   ├── NL2SQLResultBox (chỉ tab "ask")
            │   └── ResultCards (báo cáo phù hợp + score bar)
            │
            ├── /report → Report
            │   ├── StudyInfoPanel (readonly)
            │   └── ReportForm (findings, conclusion, recommendation)
            │
            ├── /viewer → Viewer
            │   ├── StudyInfoPanel (metadata sidebar)
            │   ├── ViewerControls (zoom, pan, reset)
            │   └── DicomCanvas (Orthanc iframe hoặc Cornerstone.js)
            │
            └── /admin → Admin
                ├── UserTable
                └── SystemInfoCards
```

---

## Mô tả từng trang (Pages)

### 1. Login `/login`

**Chức năng:**
- Form đăng nhập username + password
- Gọi `POST /api/auth/login`
- Lưu JWT token vào `localStorage`
- Redirect về `/worklist` nếu đã đăng nhập

**Layout:** 2 cột — trái: branding PACS++, phải: form

**Không cần auth** (public route)

---

### 2. Worklist `/worklist`

**Chức năng:**
- Hiển thị **4 stat cards**: Tổng ca / Chờ đọc / Đã báo cáo / Đã xác nhận
- **Upload DICOM** (chỉ technician + admin): drag & drop hoặc click chọn file .dcm
- **Filter** theo: ngày chụp, loại chụp (modality), trạng thái
- **Bảng danh sách ca chụp**: click row → viewer, nút "Xem" + "Báo cáo"
- **Phân quyền button**: chỉ doctor/admin thấy nút "Báo cáo"

**Data:** `GET /api/worklist` + `GET /api/worklist/stats/dashboard`

---

### 3. Viewer `/viewer?studyId=&orthancId=`

**Chức năng:**
- Panel bên trái: metadata ca chụp (bệnh nhân, ngày, modality, status, Study UID)
- Vùng phải: xem ảnh DICOM
  - Nếu có `orthancId` → embed Orthanc Web Viewer (iframe)
  - Nếu không có → thông báo chưa upload
- Toolbar: Phóng to / Thu nhỏ / Di chuyển / Đặt lại
- Nút "Báo cáo" (doctor/admin)

**Data:** `GET /api/worklist/{id}` + Orthanc WADO

---

### 4. Report `/report?studyId=`

**Chức năng:**
- Panel trái: thông tin ca chụp (readonly)
- Panel phải: form báo cáo
  - **Findings** (textarea): Kết quả hình ảnh
  - **Conclusion** (textarea): Kết luận chẩn đoán
  - **Recommendation** (textarea): Đề nghị xử trí
- Nếu đã có báo cáo → load lên + cho phép cập nhật
- Nút "Lưu báo cáo" / "Cập nhật"
- Nút "Xuất PDF" (nếu đã có báo cáo)
- **Phân quyền:** chỉ doctor/admin được edit, technician chỉ xem

**Data:** `GET + POST + PUT /api/report` + `GET /api/report/{id}/pdf`

---

### 5. Search `/search`

**Chức năng:**
- **4 chế độ tìm kiếm** (tabs):
  1. **Từ khoá** — SQL ILIKE trong findings + conclusion
  2. **Dense** — BGE-M3 vector similarity (cosine)
  3. **Hybrid** — Dense + BM25 + RRF fusion
  4. **NL2SQL / Hỏi đáp** — câu hỏi tự nhiên → SQL hoặc RAG
- Kết quả hiển thị dạng cards: patient name, ngày, modality, findings preview, similarity score bar
- Tab "Hỏi đáp" hiển thị thêm: intent, SQL được sinh, bảng SQL results + câu trả lời text

**Data:** `GET /api/search/keyword` + `POST /api/search` + `POST /api/ask`

---

### 6. Admin `/admin`

**Chức năng:**
- Danh sách người dùng hệ thống
- Thông tin tài khoản mặc định
- Thông tin stack kỹ thuật

**Phân quyền:** Chỉ role `admin`; redirect về `/worklist` nếu không phải admin

---

## Routing và Auth Guard

```mermaid
flowchart TD
    U[User truy cập URL] --> CHECK{Có JWT token?}
    CHECK -->|Không| LOGIN[Redirect /login]
    CHECK -->|Có| ROUTE{Route}
    
    ROUTE --> WOR[/worklist — All roles]
    ROUTE --> SEARCH[/search — doctor + admin]
    ROUTE --> REPORT[/report — doctor + admin]
    ROUTE --> VIEWER[/viewer — All roles]
    ROUTE --> ADMIN[/admin — admin only]
    
    ADMIN -->|Không phải admin| WOR
```

---

## API Layer (`src/api/`)

```javascript
// 6 file tách riêng theo domain:
// auth.js     — login, register, refresh, me
// worklist.js — getList, getStats, getDetail
// dicom.js    — upload, download, getInstances
// report.js   — get, create, update, exportPdf
// search.js   — keyword, dense, hybrid, ask
// patient.js  — getMyStudies

// Mọi request đều tự động gắn JWT header
// 401 → tự động logout + redirect /login
```

---

## Design System

### Màu sắc (Hospital Dark Theme)

| Token | Màu | Dùng cho |
|---|---|---|
| `--bg-base` | `#09111f` | App background |
| `--bg-surface` | `#0d1829` | Card, panel |
| `--bg-elevated` | `#132035` | Hover, elevated |
| `--accent` | `#3b82f6` | Primary button, link |
| `--success` | `#22c55e` | REPORTED status |
| `--warning` | `#f59e0b` | PENDING status |
| `--danger` | `#ef4444` | Error, delete |
| `--text-primary` | `#e2eaf4` | Nội dung chính |
| `--text-muted` | `#4d6a8a` | Phụ, placeholder |

### Typography

- **Heading/UI:** `Inter` (Google Fonts)
- **Code/UID:** `JetBrains Mono`

### Layout constants

- Sidebar rộng: `240px` (mở) / `64px` (thu gọn)
- Topbar cao: `60px`
- Sidebar có animation collapse khi click toggle

---

## Vite Config (proxy)

```javascript
// vite.config.js
export default {
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    }
  }
}
```

Khi build production: `npm run build` → output vào `dist/` → copy vào `backend/frontend/` → FastAPI serve static.
