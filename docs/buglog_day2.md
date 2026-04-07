# Buglog Day 2 — Frontend Sprint 2

## Ngày: 2026-04-07

---

## Bug 1: JWT "Subject must be a string"
- **File**: `backend-v2/core/auth_utils.py`
- **Triệu chứng**: Login 200 OK nhưng mọi API khác (worklist, stats) trả 401 "Invalid or expired token"
- **Nguyên nhân**: `python-jose` yêu cầu claim `sub` phải là string theo chuẩn JWT. Code cũ truyền integer: `"sub": user_id` (e.g., `6`)
- **Fix**: `"sub": str(user_id)` — cast sang string
- **Debug**: Thêm `print(f"[DEBUG] JWT decode error: {e}")` vào `get_current_user()` → thấy rõ lỗi "Subject must be a string"

---

## Tóm tắt công việc Day 2

### Phase 1: Layout System ✅
| File | Mô tả |
|---|---|
| `src/styles/layout.css` | CSS grid layout: sidebar + topbar + main |
| `src/components/layout/Sidebar.jsx` | Menu theo role, avatar, logout |
| `src/components/layout/Topbar.jsx` | Breadcrumb + role badge |
| `src/components/layout/AppLayout.jsx` | Wrapper: Sidebar + Topbar + Outlet |
| `src/components/shared/RoleGuard.jsx` | Chặn truy cập theo role |
| `src/App.jsx` | Router đầy đủ: 7 routes + RoleGuard |
| Placeholder pages | Viewer, Report, Search, MyStudies, Admin |

### Phase 2: Shared Components + API ✅
| File | Mô tả |
|---|---|
| `src/components/shared/StatusBadge.jsx` | PENDING/REPORTED/VERIFIED badge |
| `src/components/shared/StatCard.jsx` | Card thống kê (value + label) |
| `src/components/shared/FilterBar.jsx` | Filter: date, modality, status |
| `src/components/shared/UploadZone.jsx` | Drag & drop upload DICOM |
| `src/api/worklist.js` | getWorklist, getStats, getStudyDetail |
| `src/api/dicom.js` | uploadDicom, getWadoUrl |
| `src/api/report.js` | getReport, createReport, updateReport |
| `src/api/patient.js` | getMyStudies |

### Phase 3: Worklist Page ✅
| File | Mô tả |
|---|---|
| `src/pages/Worklist/index.jsx` | Dashboard stats + Filter + Data table + Pagination |

### CSS Updates
- `src/styles/layout.css` — Layout grid (sidebar 240px, topbar 56px)
- `src/styles/components.css` — Thêm status-badge, stat-card, filter-bar, upload-zone, data-table, pagination
- `src/main.jsx` — Import layout.css

### Backend Fix
- `backend-v2/core/auth_utils.py` — `"sub": str(user_id)` fix JWT decode error

### Test phân quyền
- Admin: 3 menu (Worklist, Tim kiem, Quan tri) + Upload DICOM
- Doctor: 2 menu (Worklist, Tim kiem) — không có Quan tri, không Upload
