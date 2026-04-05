# Day 2 Plan — Frontend Sprint 2 (2026-04-06)

## Mục tiêu: Build Layout + Worklist + API Layer

Sau Day 1 (Login xong, FE↔BE connected), Day 2 tập trung build **khung app** và **trang chính Worklist**.

---

## Buổi sáng — Layout System (est. 1.5h)

### Phase 1: CSS Layout
- [ ] `src/styles/layout.css` — Sidebar, Topbar, AppLayout grid, responsive

### Phase 2: Layout Components (3 files)
- [ ] `src/components/layout/Sidebar.jsx`
  - Logo + PACS++ title
  - Nav items filtered by role:
    - admin: Worklist, Search, Admin
    - doctor: Worklist, Search
    - technician: Worklist
    - patient: My Studies
  - Active route highlight
  - Collapse/expand toggle
  - Logout button ở bottom

- [ ] `src/components/layout/Topbar.jsx`
  - Breadcrumb (tên trang hiện tại)
  - User info: full_name + role badge
  - Logout icon button

- [ ] `src/components/layout/AppLayout.jsx`
  - Grid: Sidebar (240px) | Main content
  - Topbar fixed top
  - `<Outlet/>` cho React Router

### Phase 3: Router Update
- [ ] `src/App.jsx` — Thêm routes:
  ```
  /#/worklist        → Worklist page
  /#/viewer/:id      → Viewer page (placeholder)
  /#/report/:id      → Report page (placeholder)
  /#/search          → Search page (placeholder)
  /#/my-studies      → MyStudies page (placeholder)
  /#/admin           → Admin page (placeholder)
  ```
- [ ] `src/components/shared/RoleGuard.jsx` — Chặn truy cập theo role

### Verify:
- Login admin → thấy Sidebar đầy đủ menu
- Login doctor → sidebar chỉ có Worklist + Search
- Click menu items → navigate đúng route

---

## Buổi chiều — API Layer + Worklist (est. 2h)

### Phase 4: API Wrappers (4 files)
- [ ] `src/api/worklist.js`
  ```js
  getWorklist(filters)    // GET /api/worklist
  getStats()              // GET /api/worklist/stats/dashboard
  getStudyDetail(id)      // GET /api/worklist/{id}
  ```
- [ ] `src/api/dicom.js`
  ```js
  uploadDicom(file)       // POST /api/dicom/upload
  getWadoUrl(objectId)    // GET /api/dicom/wado
  ```
- [ ] `src/api/report.js`
  ```js
  getReport(studyId)      // GET /api/report/{study_id}
  createReport(data)      // POST /api/report
  updateReport(id, data)  // PUT /api/report/{id}
  ```
- [ ] `src/api/patient.js`
  ```js
  getMyStudies()          // GET /api/my-studies (cần thêm BE endpoint)
  ```

### Phase 5: Shared Components (3 files)
- [ ] `src/components/shared/StatusBadge.jsx` — PENDING/REPORTED/VERIFIED
- [ ] `src/components/shared/StatCard.jsx` — Icon + number + label
- [ ] `src/components/shared/FilterBar.jsx` — Date range, modality, status, search

### Phase 6: Worklist Page
- [ ] `src/pages/Worklist/index.jsx`
  - 4 StatCards row: Tổng ca, Chờ đọc, Đã đọc, Hôm nay
  - FilterBar: ngày, modality, status, tên BN
  - Data table: sortable columns
    - Tên BN | Mã BN | Ngày chụp | Modality | Status | Actions
  - Action buttons: Xem (→ /viewer/:id), Báo cáo (→ /report/:id)
  - Upload button (tech/admin only)
  - Pagination

### Verify:
- Login → Worklist hiển thị đúng data từ DB (75 studies)
- Filter by modality CT → chỉ hiện CT studies
- Click "Xem" → navigate /viewer/:id
- Stats cards hiện số đúng

---

## Cuối ngày — Review + Push

- [ ] Test tất cả routes với 4 role khác nhau
- [ ] Fix bugs phát sinh
- [ ] Viết `docs/buglog_day2.md`
- [ ] Git commit + push (chỉ frontend-react + docs)
- [ ] Cập nhật `docs/05_sprint_roadmap.md` progress

---

## Files tạo mới trong Day 2

| # | File | Mô tả |
|---|---|---|
| 1 | `src/styles/layout.css` | Layout CSS |
| 2 | `src/components/layout/Sidebar.jsx` | Menu sidebar |
| 3 | `src/components/layout/Topbar.jsx` | Top bar |
| 4 | `src/components/layout/AppLayout.jsx` | Layout wrapper |
| 5 | `src/components/shared/RoleGuard.jsx` | Role-based access |
| 6 | `src/components/shared/StatusBadge.jsx` | Status badges |
| 7 | `src/components/shared/StatCard.jsx` | Stat cards |
| 8 | `src/components/shared/FilterBar.jsx` | Filter controls |
| 9 | `src/api/worklist.js` | Worklist API |
| 10 | `src/api/dicom.js` | DICOM API |
| 11 | `src/api/report.js` | Report API |
| 12 | `src/api/patient.js` | Patient API |
| 13 | `src/pages/Worklist/index.jsx` | Worklist page |
| **Total** | **13 files mới** | + modify App.jsx |

---

## Lưu ý cho Day 2

1. **Luôn test với backend thật** — tránh lặp lại BUG-001 (Day 1)
2. **Check API response format** trước khi code FE — `console.log(result)`
3. **Commit nhỏ, push thường xuyên** — không để 63 files 1 lần nữa
4. **Sidebar cần responsive** — collapse trên màn hình nhỏ
5. **Worklist là trang quan trọng nhất** — dành thời gian cho UI/UX
