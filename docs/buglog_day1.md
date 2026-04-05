# Bug Log — Day 1 (2026-04-05)

## Phiên làm việc: Frontend Login + Kết nối Backend

---

### BUG-001: API Content-Type sai format

| Mục | Chi tiết |
|---|---|
| **File** | `frontend-react/src/api/auth.js` |
| **Triệu chứng** | Login trả về HTTP 422 Unprocessable Entity |
| **Nguyên nhân** | Frontend gửi `Content-Type: application/x-www-form-urlencoded` với `URLSearchParams`, nhưng Backend (FastAPI) expect JSON body qua Pydantic `LoginRequest` model |
| **Error response** | `{"detail":[{"type":"model_attributes_type","loc":["body"],"msg":"Input should be a valid dictionary or object to extract fields from","input":"username=admin&password=admin123&grant_type=password"}]}` |
| **Fix** | Đổi sang `Content-Type: application/json` + `JSON.stringify({ username, password })` |
| **Status** | ✅ Fixed |

**Trước:**
```js
const body = new URLSearchParams({ username, password, grant_type: 'password' })
headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
body: body.toString()
```

**Sau:**
```js
headers: { 'Content-Type': 'application/json' }
body: JSON.stringify({ username, password })
```

---

### BUG-002: Error message hiển thị [object Object]

| Mục | Chi tiết |
|---|---|
| **File** | `frontend-react/src/api/auth.js` |
| **Triệu chứng** | Khi login fail, UI hiện `[object Object]` thay vì message lỗi |
| **Nguyên nhân** | FastAPI trả `detail` dạng array `[{type, loc, msg, input}]` khi validation fail, nhưng code FE dùng `data.detail` trực tiếp làm string |
| **Fix** | Parse detail: nếu string → dùng thẳng, nếu array → `.map(d => d.msg).join(', ')` |
| **Status** | ✅ Fixed |

**Trước:**
```js
throw new Error(data.detail || 'Sai tài khoản hoặc mật khẩu')
```

**Sau:**
```js
const detail = data.detail
const msg = typeof detail === 'string'
  ? detail
  : Array.isArray(detail)
    ? detail.map(d => d.msg).join(', ')
    : 'Sai tài khoản hoặc mật khẩu'
throw new Error(msg)
```

---

### BUG-003: Token key mismatch giữa FE và BE

| Mục | Chi tiết |
|---|---|
| **File** | `frontend-react/src/hooks/useAuth.js` |
| **Triệu chứng** | Login API thành công (200) nhưng FE không nhận được token → state vẫn null |
| **Nguyên nhân** | FE destructure `const { access_token } = await loginApi(...)` nhưng Backend trả `{ token, user }` — key là `token` chứ không phải `access_token` |
| **Fix** | Dùng `result.token || result.access_token` để tương thích cả 2 format |
| **Status** | ✅ Fixed |

**Trước:**
```js
const { access_token } = await loginApi(username, password)
const me = await getMeApi(access_token)  // access_token = undefined!
```

**Sau:**
```js
const result = await loginApi(username, password)
const jwt = result.token || result.access_token
const me = result.user  // Backend đã trả user sẵn
const userInfo = me || await getMeApi(jwt)  // fallback nếu cần
```

---

### BUG-004: Gọi /api/auth/me thừa

| Mục | Chi tiết |
|---|---|
| **File** | `frontend-react/src/hooks/useAuth.js` |
| **Triệu chứng** | Sau login thành công, FE gọi thêm GET /api/auth/me — tốn 1 request thừa |
| **Nguyên nhân** | Backend POST /login đã trả `{ token, user: { id, username, full_name, role } }` nhưng FE không dùng, gọi /me riêng |
| **Fix** | Dùng `result.user` từ login response trước, chỉ fallback gọi `/me` khi backend không trả user |
| **Status** | ✅ Fixed |

---

## Docs cập nhật trong ngày

| File | Thay đổi |
|---|---|
| `docs/01_system_overview.md` | Thêm role `patient` |
| `docs/02_erd_database.md` | Thêm `linked_patient_id`, quan hệ patient-users |
| `docs/05_sprint_roadmap.md` | Viết lại toàn bộ — Sprint 1 done, Sprint 2 in progress |

---

## Kết quả cuối ngày

| Hạng mục | Trạng thái |
|---|---|
| Login page redesign (benhvien.jpg background) | ✅ Done |
| Floating glassmorphism card | ✅ Done |
| FE → BE kết nối (JSON login) | ✅ Done |
| Login admin → redirect /worklist | ✅ Verified |
| User info hiển thị đúng | ✅ Verified |
| Docs update + Git push | ✅ Done |

---

## Bài học rút ra

1. **Luôn kiểm tra API contract giữa FE và BE** trước khi code — format request (JSON vs form), response keys (`token` vs `access_token`)
2. **FastAPI validation error** trả `detail` dạng array, không phải string — cần handle cả 2 case
3. **Không assume response shape** — luôn log `console.log(result)` khi debug API mới
4. **Test với backend thật** càng sớm càng tốt — mock data che giấu lỗi integration
