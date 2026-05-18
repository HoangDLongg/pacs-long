# PACS++ — Vấn đề, kế hoạch sửa & cách làm đúng

> Tài liệu này tổng hợp từ **đọc code thực tế** (không chỉ README).  
> Cập nhật: 2026-05-19

---

## Mục lục

1. [Tóm tắt ưu tiên](#1-tóm-tắt-ưu-tiên)
2. [Danh sách vấn đề chi tiết](#2-danh-sách-vấn-đề-chi-tiết)
3. [Kế hoạch sửa theo phase](#3-kế-hoạch-sửa-theo-phase)
4. [Cách làm đúng (patterns)](#4-cách-làm-đúng-patterns)
5. [Checklist xác minh sau khi sửa](#5-checklist-xác-minh-sau-khi-sửa)

---

## 1. Tóm tắt ưu tiên

| Mức | Số vấn đề | Nhóm |
|-----|-----------|------|
| **P0** | 4 | Doc/model lệch, DB layer trùng, test hỏng, bảo mật API search |
| **P1** | 6 | Scale RAG, health/deploy, NL2SQL config, WADO, env/CI |
| **P2** | 5 | Audit, answer LLM, dọn repo, index pgvector, UX nhỏ |
| **P3** | 3 | HashRouter, password BN demo, Graph RAG (planned) |

---

## 2. Danh sách vấn đề chi tiết

### P0 — Phải xử lý trước khi demo / bảo vệ / deploy

#### P0-1. Tài liệu và code dùng **hai model embedding khác nhau**

| | Thực tế |
|---|--------|
| **Code production** | `intfloat/multilingual-e5-large` (`core/embeddings.py`) |
| **Tài liệu** | Nhiều file vẫn ghi **BGE-M3** (`TECHNICAL.md`, `PACS_MASTER_DOCUMENT.md`, `docs/07_feature_list.md`, …) |
| **Fine-tune** | `embedding_finetuning/` fine-tune **BAAI/bge-m3** |

**Hậu quả:** Reproduce sai, benchmark/luận văn mô tả không khớp hệ thống chạy, model fine-tune không gắn được vào RAG hiện tại.

**Ý tưởng sửa:**
- Chọn **một** model chính thức (khuyến nghị: giữ **e5-large** vì code + benchmark nội bộ đã dùng).
- Cập nhật toàn bộ doc → e5-large.
- Hoặc: migrate code sang BGE-M3 + re-embed toàn DB (tốn công hơn).

**Cách làm đúng:**
1. Ghi rõ trong `README.md` mục **Embedding model (source of truth)**.
2. `grep -r "BGE-M3\|bge-m3"` → sửa hoặc thêm footnote “deprecated”.
3. `embedding_finetuning`: đổi `BASE_MODEL` sang `intfloat/multilingual-e5-large` **hoặc** tách README “experimental branch”.
4. Sau khi đổi model: chạy `scripts/embed_existing.py` re-embed 100% `diagnostic_reports`.

---

#### P0-2. Trùng lặp `database/base.py` và `database/connection.py`

| | Thực tế |
|---|--------|
| **Hiện trạng** | Cả hai file đều tạo `engine`, `SessionLocal`, pool psycopg2, `init_db()`. |
| **Import** | Models → `database.base.Base`; Auth → `database.connection.get_db`. |

**Hậu quả:** Hai SQLAlchemy engine, khó bảo trì, dễ lệch config pool.

**Ý tưởng sửa:** Một module DB duy nhất.

**Cách làm đúng:**

```
database/
  __init__.py      # export get_db, get_connection, Base, engine
  session.py       # SQLAlchemy engine + SessionLocal + Base
  pool.py          # psycopg2 pool + get_connection / release
  init_db.sql      # giữ nguyên
```

- `base.py` chỉ còn `Base = declarative_base()` **hoặc** gộp vào `session.py`.
- `connection.py` chỉ wrap psycopg2, **không** tạo engine thứ hai.
- Xóa file trùng sau khi đổi import toàn project.

---

#### P0-3. Test router **lỗi thời** (import function không tồn tại)

| | Thực tế |
|---|--------|
| **Test** | `tests/test_query_router.py` import `_looks_like_name` |
| **Code** | `core/query_router.py` dùng `_detect_vn_name` |

**Hậu quả:** `pytest` fail ngay khi import; CI không tin được.

**Ý tưởng sửa:**
- Đổi test dùng `_detect_vn_name`, **hoặc**
- Thêm alias tương thích: `_looks_like_name = _detect_vn_name` (nhanh, ít đụng test).

**Cách làm đúng:**
1. Sửa import trong `test_query_router.py`.
2. Bổ sung test cho `classify()` (PATIENT_LOOKUP / STRUCTURED / SEMANTIC) — không chỉ heuristic tên.
3. Thêm `pytest` vào `requirements-dev.txt` hoặc `requirements.txt` optional.
4. CI: `pip install -r requirements.txt && pytest tests/`.

---

#### P0-4. API Search / Ask **không enforce role** ở backend

| | Thực tế |
|---|--------|
| **Frontend** | `RoleGuard` chỉ `admin`, `doctor` vào `/search` |
| **Backend** | `search.py`, `ask.py` chỉ `Depends(get_current_user)` — **technician/patient** gọi trực tiếp API vẫn được |

**Hậu quả:** Lỗ hổng phân quyền nếu biết endpoint + token.

**Ý tưởng sửa:** Dependency `require_roles("admin", "doctor")` trên router search + ask.

**Cách làm đúng:**

```python
# core/auth_utils.py
def require_roles(*roles):
    def dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Không có quyền")
        return user
    return dep

# api/search.py, api/ask.py
current_user: User = Depends(require_roles("admin", "doctor"))
```

- Đồng bộ với ma trận trong `docs/07_feature_list.md`.

---

### P1 — Quan trọng cho vận hành & scale

#### P1-1. `/health` không kiểm tra dependency

**Hiện trạng:** `main.py` trả `{"status": "ok"}` — không ping Postgres, Orthanc, Ollama.

**Ý tưởng sửa:** Health có `checks: { database, orthanc, ollama }` + HTTP 503 nếu DB down.

**Cách làm đúng:**
- `SELECT 1` qua pool (timeout 2s).
- `GET {ORTHANC_URL}/system` (timeout 2s).
- `GET {OLLAMA_URL}/api/tags` (optional, `degraded` nếu off).

---

#### P1-2. BM25 rebuild **full scan** mỗi lần corpus đổi

**Hiện trạng:** `_load_all_reports()` + build BM25 in-memory trong `rag_engine.py`.

**Ý tưởng sửa:**
- Cache BM25 + version theo `MAX(report.id)` hoặc `COUNT(*)`.
- Hoặc persist sparse index (pickle/redis) khi > 500 reports.
- Background job rebuild sau `POST /api/report`.

**Cách làm đúng:** Singleton index với TTL hoặc invalidate on report create/update.

---

#### P1-3. Index IVFFlat có thể **không được tạo**

**Hiện trạng:** `init_db.sql` chỉ tạo IVFFlat khi chạy init **và** đã có ≥10 embedding.

**Ý tưởng sửa:** Script `scripts/ensure_vector_index.py` gọi sau `embed_existing.py`.

**Cách làm đúng:**

```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reports_embedding
  ON diagnostic_reports USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);  -- tăng lists khi > 1k vectors
```

---

#### P1-4. Ollama **hardcode** URL và model

**Hiện trạng:** `nl2sql_engine.py` → `http://localhost:11434`, model `gemma4:e4b`.

**Ý tưởng sửa:** Dùng `config.OLLAMA_URL`, `OLLAMA_NL2SQL_MODEL` từ `.env`.

**Cách làm đúng:** Giống `ORTHANC_URL` trong `config.py`; không hardcode trong core.

---

#### P1-5. Secrets trong `docker-compose.yml`

**Hiện trạng:** `POSTGRES_PASSWORD: pacs_pass` plaintext.

**Ý tưởng sửa:** `.env` + `env_file` trong compose; `.env.example` không commit secret thật.

---

#### P1-6. Môi trường dev thiếu hướng dẫn / CI

**Hiện trạng:** Chạy `pytest` trên máy global → thiếu `pytest`, `sqlalchemy`.

**Ý tưởng sửa:**
- `requirements-dev.txt`: `pytest`, `httpx` (test API).
- GitHub Actions: postgres service + `pytest tests/`.
- `Makefile` hoặc `scripts/dev.ps1`: venv + docker up + migrate.

---

### P2 — Chất lượng sản phẩm & compliance

#### P2-1. Audit log chỉ ghi **login**

**Hiện trạng:** `audit_logger` dùng ở `api/auth.py` only.

**Ý tưởng sửa:** Log thêm: upload DICOM, create/update report, export PDF, search/ask (metadata, không log full query PII nếu cần).

**Cách làm đúng:** JSON line log → file hoặc bảng `audit_events` sau này.

---

#### P2-2. `generate_answer()` chỉ template

**Hiện trạng:** Không gọi LLM lần 2; HYBRID không tổng hợp SQL + RAG thành câu tự nhiên.

**Ý tưởng sửa (tùy scope):**
- **Ngắn hạn:** Template tốt hơn (liệt kê modality, tên BN từ SQL rows).
- **Dài hạn:** LLM summarize với context giới hạn (không gửi password/schema nhạy cảm).

---

#### P2-3. WADO không kiểm tra **quyền trên study**

**Hiện trạng:** Token hợp lệ + `objectId` → stream DICOM.

**Ý tưởng sửa:** Map `instanceId` → study → check patient isolation / role.

**Cách làm đúng:** Orthanc API parent study → so `studies.orthanc_id` + `linked_patient_id`.

---

#### P2-4. Upload DICOM: Orthanc fail **vẫn commit DB**

**Hiện trạng:** `orthanc_study_id = ""`, study vẫn tạo.

**Ý tưởng sửa:**
- **Strict:** rollback DB nếu Orthanc fail (production).
- **Resilient:** giữ hiện tại nhưng set `studies.sync_status = 'ORTHANC_PENDING'` + job retry.

---

#### P2-5. Thư mục / file nhiễu

| File | Đề xuất |
|------|---------|
| `javapacs/` | Xóa hoặc move ra ngoài repo / `.gitignore` |
| Script `_test_*.py` rải rác | Gom `scripts/` vs `tests/` |

---

### P3 — Cải thiện nhỏ / backlog

#### P3-1. `HashRouter` (`#/worklist`)

Chấp nhận được cho demo static. Production: `BrowserRouter` + server fallback `index.html`.

#### P3-2. Mật khẩu patient auto `{PatientID}@`

Chỉ demo. Production: invite link / OTP / đổi mật khẩu lần đầu.

#### P3-3. Graph RAG (Sprint 5)

Đã planned trong `docs/09_graph_rag_plan.md` — không block hiện tại.

---

## 3. Kế hoạch sửa theo phase

### Phase A — 1–2 ngày (ổn định nền)

| # | Việc | File chính |
|---|------|------------|
| A1 | Sửa test router + thêm `pytest` dev dep | `tests/test_query_router.py`, `requirements-dev.txt` |
| A2 | `require_roles` cho search/ask | `core/auth_utils.py`, `api/search.py`, `api/ask.py` |
| A3 | Gộp DB layer (xóa duplicate engine) | `database/*` |
| A4 | Đồng bộ doc embedding → e5-large | `README.md`, `TECHNICAL.md`, `docs/*.md` |

**Verify:** `pytest tests/` pass; technician token → 403 trên `/api/ask`.

---

### Phase B — 3–5 ngày (vận hành)

| # | Việc | File chính |
|---|------|------------|
| B1 | Health check đầy đủ | `main.py` |
| B2 | Ollama từ `.env` | `config.py`, `nl2sql_engine.py`, `.env.example` |
| B3 | `ensure_vector_index.py` | `scripts/` |
| B4 | Docker secrets qua `.env` | `docker-compose.yml` |
| B5 | CI pytest | `.github/workflows/test.yml` |

---

### Phase C — 1–2 tuần (chất lượng)

| # | Việc |
|---|------|
| C1 | BM25 cache / invalidate on report save |
| C2 | WADO ownership check |
| C3 | Audit mở rộng |
| C4 | `generate_answer` cải thiện hoặc LLM summarize |
| C5 | Align `embedding_finetuning` với e5-large |
| C6 | Dọn `javapacs/`, chuẩn hóa scripts |

---

## 4. Cách làm đúng (patterns)

### 4.1 Một nguồn sự thật cho embedding

```
Lưu báo cáo → make_report_text(findings, conclusion)
            → encode() với prefix "passage:"
Search query  → encode_query() với prefix "query:"
```

- Không embed `recommendation` nếu muốn RAG chỉ match findings/conclusion (hiện tại đúng spec UC18).
- Đổi model = **re-embed all** + rebuild index + cập nhật doc.

### 4.2 Phân quyền: defense in depth

```
UI RoleGuard  +  API require_roles  +  Row-level check (patient linked_patient_id)
```

- Mọi endpoint trả dữ liệu BN/study/report đều có check `patient` role.

### 4.3 NL2SQL an toàn (giữ và mở rộng)

Đã làm tốt:
- Whitelist bảng trong prompt + `_validate_sql`
- READ ONLY + timeout + limit rows

Nên thêm:
- Log SQL đã execute (audit, không log PII query tùy chính sách)
- Unit test regression trong `test_nl2sql_security.py` (đã có — giữ chạy CI)

### 4.4 RAG scale

| Quy mô | Dense | Sparse |
|--------|-------|--------|
| < 500 reports | pgvector + in-memory BM25 OK | |
| 500–50k | IVFFlat/HNSW, lists tune | Persist BM25 hoặc PostgreSQL FTS |
| > 50k | Consider dedicated vector DB | |

### 4.5 Viewer DICOM

- Token qua query param là **trade-off** của Cornerstone — bắt buộc thêm **authorization trên WADO** (P2-3).
- Không log token trong access log production.

---

## 5. Checklist xác minh sau khi sửa

### Sau Phase A

- [ ] `python -m pytest tests/ -v` — all pass
- [ ] `grep -r "BGE-M3" docs/` — chỉ còn trong lịch sử / benchmark so sánh (có ghi chú)
- [ ] Login `tech.hung` → `POST /api/ask` → **403**
- [ ] Login `dr.nam` → `POST /api/ask` → **200**
- [ ] Chỉ một `create_engine` trong codebase (`grep create_engine database/`)

### Sau Phase B

- [ ] `GET /health` — `database: ok`, `orthanc: ok|degraded`
- [ ] Đổi `OLLAMA_URL` trong `.env` — NL2SQL dùng URL mới
- [ ] `EXPLAIN` query dense có dùng `idx_reports_embedding`
- [ ] CI green trên PR

### Sau Phase C

- [ ] Tạo report mới → BM25 cache invalidate / rebuild đúng
- [ ] Patient token không WADO được instance của BN khác
- [ ] Audit file có dòng `REPORT_CREATE`, `DICOM_UPLOAD`

---

## Phụ lục — File liên quan nhanh

| Chức năng | File |
|-----------|------|
| Entry API | `backend-v2/main.py` |
| RAG | `backend-v2/core/rag_engine.py` |
| Router intent | `backend-v2/core/query_router.py`, `config/vocab.json` |
| NL2SQL | `backend-v2/core/nl2sql_engine.py` |
| Embedding | `backend-v2/core/embeddings.py` |
| Auth | `backend-v2/core/auth_utils.py`, `api/auth.py` |
| DICOM | `api/dicom.py`, `core/orthanc_client.py` |
| FE Search | `frontend-react/src/pages/Search/index.jsx` |
| Schema DB | `backend-v2/database/init_db.sql` |

---

*Tác giả ghi chú: khi sửa xong từng mục P0, đánh dấu [x] trong checklist và cập nhật ngày ở đầu file.*
