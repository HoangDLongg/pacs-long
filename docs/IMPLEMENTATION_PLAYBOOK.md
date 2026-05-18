# PACS++ — Implementation Playbook (toàn bộ task còn lại)

> **Mục đích:** Bản hướng dẫn tự đứng cho **mọi task còn lại** từ Phase 1 đến Phase 3.  
> Đọc xong là biết: **làm gì, file nào, verify thế nào, khi nào xong**.  
> Dùng được khi quay lại sau vài tuần/tháng hoặc khi handoff.

**Liên quan:**
- Tổng kế hoạch: [DEVELOPMENT_ROADMAP.md](./DEVELOPMENT_ROADMAP.md)
- Vấn đề baseline: [ISSUES_AND_FIX_PLAN.md](./ISSUES_AND_FIX_PLAN.md)
- Metric hiện tại: [BENCHMARK_REPORT.md](./BENCHMARK_REPORT.md)

**Đang ở:** `phase-1-intelligence` — đã commit 1.1 baseline (82.4% router).

---

## Mục lục

- [Quy tắc chung khi làm task](#quy-tắc-chung-khi-làm-task)
- [Thứ tự đề xuất toàn cục](#thứ-tự-đề-xuất-toàn-cục)
- **Phase 1 — AI chất lượng** (6 task)
  - [1.7 Ollama config từ .env](#task-17--ollama-config-từ-env)
  - [1.6 BM25 cache invalidation](#task-16--bm25-cache-invalidation)
  - [1.2 Tune router HYBRID + edge cases](#task-12--tune-router-hybrid--edge-cases)
  - [1.3 RAG gold set + benchmark](#task-13--rag-gold-set--benchmark)
  - [1.4 Fine-tune e5](#task-14--fine-tune-e5)
  - [1.5 Tích hợp fine-tuned model](#task-15--tích-hợp-fine-tuned-model)
- **Phase 2 — Pilot nội bộ** (13 task)
  - [2.11 Docker compose profile dev/demo](#task-211--docker-compose-profile-devdemo)
  - [2.10 Không log JWT / commit .env](#task-210--không-log-jwt--commit-env)
  - [2.7 WADO check quyền study](#task-27--wado-check-quyền-study-bảo-mật-pilot)
  - [2.8 Audit log mở rộng](#task-28--audit-log-mở-rộng)
  - [2.9 Patient đổi mật khẩu lần đầu](#task-29--patient-đổi-mật-khẩu-lần-đầu)
  - [2.5 Worklist pagination + search BN](#task-25--worklist-pagination--search-bn)
  - [2.1 Search: giải thích intent + lý do](#task-21--search-giải-thích-intent--lý-do)
  - [2.2 generate_answer v2](#task-22--generateanswer-v2)
  - [2.3 Lịch sử câu hỏi gần đây](#task-23--lịch-sử-câu-hỏi-gần-đây)
  - [2.4 Report autosave draft](#task-24--report-autosave-draft)
  - [2.6 Onboarding 1 trang](#task-26--onboarding-1-trang)
  - [2.12 Script backup DB](#task-212--script-backup-db)
  - [2.13 Staging deploy](#task-213--staging-deploy)
- **Phase 3 — Pattern queries & Scale** (9 task)
  - [3.7 PostgreSQL FTS thay BM25](#task-37--postgresql-fts-thay-bm25)
  - [3.6 IVFFlat/HNSW tune](#task-36--ivfflathnsw-tune)
  - [3.9 API pagination chuẩn](#task-39--api-pagination-chuẩn)
  - [3.1 Entity extractor (Light KG)](#task-31--entity-extractor-light-kg)
  - [3.2 Migration entities JSONB + GIN](#task-32--migration-entities-jsonb--gin)
  - [3.3 Backfill entities cho corpus](#task-33--backfill-entities-cho-corpus)
  - [3.4 NL2SQL prompt bổ sung JSONB](#task-34--nl2sql-prompt-bổ-sung-jsonb)
  - [3.5 Pattern gold set + benchmark](#task-35--pattern-gold-set--benchmark)
  - [3.8 Background worker embed/entity](#task-38--background-worker-embedentity)
- [Khi quay lại sau vài tuần](#khi-quay-lại-sau-vài-tuần)

---

## Quy tắc chung khi làm task

1. **Đo trước, sửa sau.** Chạy baseline → ghi số → sửa → chạy lại → ghi delta.
2. **Commit nhỏ.** Mỗi commit 1 mục trong playbook. Message có trước/sau metric nếu có.
3. **Không tăng pytest threshold quá tham.** Threshold = `current - 5%` để buffer.
4. **Update `BENCHMARK_REPORT.md`** mỗi lần đổi metric.
5. **Không mở task sau khi task trước chưa Done.** Tránh nhánh hở.
6. **Tradeoff trước khi code.** Nếu task > 8h ước lượng → ghi câu hỏi mở vào commit hoặc playbook.

---

## Thứ tự đề xuất toàn cục

| # | Task | Lý do | Ước lượng |
|---|------|-------|-----------|
| 1 | **1.7** Ollama config | Quick win, không phụ thuộc | 1h |
| 2 | **1.6** BM25 cache | Quick win, không cần data | 2–4h |
| 3 | **1.2** Tune router HYBRID | Cải thiện baseline đã đo | 8–12h |
| 4 | **1.3** RAG gold + benchmark | Mở khoá Phase 1.4/1.5 + 3.5 | 12–16h |
| 5 | **1.4 + 1.5** Fine-tune e5 + tích hợp | Optional, dựa A/B | 24–36h |
| 6 | **2.11** Docker profile | Tách dev/demo trước deploy | 2h |
| 7 | **2.10** Không log JWT | Bảo mật trước pilot | 2h |
| 8 | **2.7** WADO ownership | Bảo mật trước pilot | 4–6h |
| 9 | **2.8** Audit mở rộng | Compliance pilot | 4–6h |
| 10 | **2.9** Patient đổi mật khẩu | Bảo mật pilot | 3h |
| 11 | **2.5** Pagination worklist | UX khi data > 75 | 4h |
| 12 | **2.1–2.4, 2.6** UX search/report | Cho pilot dùng được | 12–20h |
| 13 | **2.12 + 2.13** Backup + Staging | Pre-pilot ops | 6–10h |
| 14 | **3.9** API pagination chuẩn | Nợ kỹ thuật trước scale | 4h |
| 15 | **3.7** PostgreSQL FTS | Khi corpus > 500 | 8h |
| 16 | **3.6** Vector index tune | Khi corpus > 500 | 2h |
| 17 | **3.1–3.5** Light KG JSONB | Pattern queries | 30–40h |
| 18 | **3.8** Background worker | Khi upload hàng loạt | 6h |

---

# PHASE 1 — AI CHẤT LƯỢNG

## Task 1.7 — Ollama config từ `.env`

### Background

`core/nl2sql_engine.py` hardcode `"http://localhost:11434"` + `"gemma4:e4b"` → đổi máy/model phải sửa code.

### Pre-conditions
- `config.OLLAMA_URL` đã có (xác nhận: `backend-v2/config.py`).
- `.env.example` đã có `OLLAMA_URL`.

### Cách làm

1. Thêm vào `config.py`:
   ```python
   OLLAMA_NL2SQL_MODEL = os.getenv("OLLAMA_NL2SQL_MODEL", "gemma4:e4b")
   OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))
   ```
2. Cập nhật `backend-v2/.env.example`:
   ```env
   OLLAMA_URL=http://localhost:11434
   OLLAMA_NL2SQL_MODEL=gemma4:e4b
   OLLAMA_TIMEOUT=60
   ```
3. Sửa `core/nl2sql_engine.py` (2 chỗ hardcode) → import từ config.

### Acceptance

- [ ] `rg "11434|gemma4:e4b" backend-v2/core` → trống.
- [ ] Đổi URL sai trong `.env` → error log có URL mới.
- [ ] Pytest 53/53 pass.

### Risk
Rất thấp.

### Commit gợi ý
```
refactor(nl2sql): read Ollama URL + model from config
```

---

## Task 1.6 — BM25 cache invalidation

### Background

`core/rag_engine._get_bm25()` cache theo `count(reports)`:
- Mỗi search vẫn `_load_all_reports()` để đếm → full table scan.
- UPDATE report mà count không đổi → BM25 stale → search lệch.

### Pre-conditions
- Postgres chạy + ≥ 20 reports.
- Hiểu `BM25Okapi` không hỗ trợ incremental → phải rebuild.

### Cách làm

1. Helper trong `rag_engine.py`:
   ```python
   def _bm25_corpus_fingerprint() -> tuple[int, str]:
       cur.execute("""
           SELECT COUNT(*), COALESCE(MAX(updated_at), 'epoch')::text
           FROM diagnostic_reports
       """)
       return tuple(cur.fetchone())
   ```
2. Sửa `_get_bm25()`:
   - Gọi `_bm25_corpus_fingerprint()` **trước**.
   - Nếu khớp cache → return cached, **bỏ qua** `_load_all_reports()`.
   - Lệch → load + rebuild + cập nhật fingerprint.
3. Optional: `POST /api/admin/bm25/rebuild` để force.

### Acceptance

- [ ] Log `[BM25] fingerprint <a>→<b> rebuild` chỉ xuất hiện khi corpus đổi.
- [ ] UPDATE report → BM25 search phản ánh content mới (manual test).
- [ ] Latency hybrid search 75 reports không tăng.
- [ ] Pytest 53/53 pass.

### Risk
Trung bình — đụng hot path. Thêm log để dễ debug.

### Commit gợi ý
```
perf(rag): BM25 cache by (count, max(updated_at)) fingerprint
```

---

## Task 1.2 — Tune router HYBRID + edge cases

### Background (từ baseline 1.1)

**82.4% overall** — PL 94% · STR 86% · SEM 100% · **HYB 10%**. 13 mismatch:

| Case | Câu | Expected | Got | Lý do |
|------|-----|----------|-----|-------|
| H001–H010 | "bao nhiêu ca CT có tổn thương phổi" | HYBRID | SEMANTIC/STRUCTURED | Medical boost kéo gap > `HYBRID_MAX_GAP` |
| R013 | "tên Nguyen Thi B" | PATIENT_LOOKUP | SEMANTIC | "B" 1 ký tự, `_detect_vn_name` skip |
| S011 | "ca chụp tháng 1" | STRUCTURED | SEMANTIC | 1 tín hiệu time, conf 0.3 → fallback |
| S018 | "modality nào nhiều nhất" | STRUCTURED | SEMANTIC | Stats weak |
| E002 | "CT" | STRUCTURED | SEMANTIC | Modality 1 từ |

### Mục tiêu

| Intent | Hiện | Mục tiêu | Threshold CI |
|--------|------|----------|--------------|
| Overall | 82.4% | ≥ 90% | ≥ 85% |
| PL | 94% | ≥ 95% | ≥ 90% |
| STR | 86% | ≥ 90% | ≥ 85% |
| SEM | 100% | ≥ 95% | ≥ 90% |
| **HYB** | **10%** | **≥ 60%** | ≥ 50% |

### Cách làm — 3 sub-task

#### 1.2a — HYBRID early-return

Trước `select_intent` chọn best:
```python
has_struct = any(features.get(k) for k in ("has_counting_kw","has_listing_kw","has_stats_kw","has_status_kw"))
has_semantic = any(features.get(k) for k in ("has_medical_term","has_medical_en"))
if has_struct and has_semantic:
    return "HYBRID", min(scores["STRUCTURED"], scores["SEMANTIC"]), debug
```

#### 1.2b — STRUCTURED weak-signal fallback

Trong fallback `LOW_CONFIDENCE`:
```python
if best_score < LOW_CONFIDENCE:
    if features.get("has_time_kw") or features.get("has_modality_kw") or features.get("has_stats_kw"):
        return "STRUCTURED", best_score, debug
    return "SEMANTIC", DEFAULT_SEMANTIC_SCORE, debug
```

#### 1.2c — PATIENT_LOOKUP prefix-strong rule

Khi prefix "tên/tim/bệnh nhân/bn" + 2+ từ phía sau → boost PL 0.5 (bất kể `_detect_vn_name` trả gì).

### Workflow

```
Sub-task 1.2a:
  sửa → python -m tests.benchmark.run_router_eval → ghi số → commit nhỏ
Sub-task 1.2b:
  sửa → eval → so sánh → commit
Sub-task 1.2c:
  sửa → eval → commit
```

### Acceptance

- [ ] Overall ≥ 85%, HYBRID ≥ 50%, không intent nào tụt > 3%.
- [ ] `tests/test_router_gold.py`: thêm `MIN_PER_INTENT["HYBRID"]`, bump overall.
- [ ] `BENCHMARK_REPORT.md` mục "Lịch sử thay đổi" có dòng mới.
- [ ] Pytest pass.

### Files
- `backend-v2/core/query_router.py`
- `backend-v2/config/vocab.json` (có thể)
- `backend-v2/tests/test_router_gold.py`
- `docs/BENCHMARK_REPORT.md`

### Risk
**Trung bình–cao.** Đo từng sub-task, không batch.

---

## Task 1.3 — RAG gold set + benchmark

### Background

Có baseline router. Chưa có baseline **chất lượng tìm kiếm**. Cần để đo trước/sau fine-tune e5.

### Pre-conditions
- Postgres + ≥ 75 reports đã embed.
- `sentence-transformers` load được.
- Hiểu P@5, nDCG@10.

### Cách làm

#### 1.3a — `rag_gold.jsonl`

Schema:
```json
{"id":"RAG001","query":"tổn thương phổi dạng nốt","relevant_report_ids":[12,47,88],"tags":["medical_vn"]}
```

Build semi-automated:
1. Script `scripts/extract_rag_queries.py`: lấy `findings + conclusion` từ 25–50 report đa modality, LLM sinh 1 query tự nhiên/report → `rag_gold_draft.jsonl`.
2. Review tay, đánh dấu `relevant_report_ids` (bao gồm report nguồn + tương đồng).
3. Save `tests/data/rag_gold.jsonl`.

Bắt đầu 25 câu, mở rộng dần.

#### 1.3b — `tests/benchmark/run_rag_eval.py`

```python
def compute_ndcg(retrieved, relevant, k=10):
    dcg = sum(1/math.log2(i+2) for i,d in enumerate(retrieved[:k]) if d in relevant)
    ideal = sum(1/math.log2(i+2) for i in range(min(len(relevant), k)))
    return dcg/ideal if ideal else 0

def evaluate_rag(gold):
    for item in gold:
        results = hybrid_search(item["query"], top_k=10)
        ids = [r["report_id"] for r in results]
        p5 = len(set(ids[:5]) & set(item["relevant_report_ids"])) / 5
        ndcg = compute_ndcg(ids, set(item["relevant_report_ids"]))
        ...
    return {"mean_p5":..., "mean_ndcg10":..., "latency_ms":...}
```

#### 1.3c — Pytest integration

Mark `@pytest.mark.integration` + skip nếu không có DB:
```python
@pytest.mark.integration
@pytest.mark.skipif(not _db_available(), reason="Postgres required")
def test_rag_baseline():
    stats = evaluate_rag(load_gold("rag_gold.jsonl"))
    assert stats["mean_p5"] >= 0.4
```

### Acceptance

- [ ] `rag_gold.jsonl` ≥ 25 câu, mỗi câu ≥ 1 `relevant_report_ids`.
- [ ] `run_rag_eval` < 60s với 75 reports.
- [ ] Output: `mean_p5`, `mean_ndcg10`, `mean_latency_ms`, top-5 worst.
- [ ] `BENCHMARK_REPORT.md` §2 có baseline.

### Files
- `backend-v2/scripts/extract_rag_queries.py` (mới)
- `backend-v2/tests/data/rag_gold.jsonl` (mới)
- `backend-v2/tests/benchmark/run_rag_eval.py` (mới)
- `backend-v2/tests/test_rag_gold.py` (mới)
- `docs/BENCHMARK_REPORT.md`

### Risk
Trung bình. Annotation chủ quan → ghi rõ tiêu chí trong gold file.

---

## Task 1.4 — Fine-tune e5

### Background

`embedding_finetuning/scripts/02_kaggle_finetune.py` đang BGE-M3 (lệch production). Cần fine-tune e5-large trên `vietnamese-medical-qa`.

### Pre-conditions
- Kaggle account hoặc GPU ≥ 16GB.
- Task 1.3 xong (có baseline để so).

### Cách làm

1. `02_kaggle_finetune.py`:
   ```python
   BASE_MODEL = "intfloat/multilingual-e5-large"
   OUTPUT_PATH = "/kaggle/working/e5-large-medical-vn"
   ```
   Lưu ý: e5 cần prefix `passage:` / `query:` trong training pairs.

2. Config: `MultipleNegativesRankingLoss`, batch 16, 3 epoch, LR 2e-5, eval 80/20.

3. Output: `embedding_finetuning/models/e5-large-medical-vn/` (gitignore). Lưu `eval_results.json`.

### Acceptance

- [ ] Notebook chạy không OOM.
- [ ] Eval P@5 val ≥ baseline.
- [ ] `embedding_finetuning/RESULTS_YYYY-MM-DD.md` có config + metric.

### Files
- `embedding_finetuning/scripts/02_kaggle_finetune.py`
- `embedding_finetuning/README.md`
- `.gitignore`

### Risk
**Cao.** Có thể không cải thiện. Chỉ ship khi A/B (1.5) chứng minh tốt hơn.

---

## Task 1.5 — Tích hợp fine-tuned model

### Pre-conditions
- Task 1.4 có model dir.
- Task 1.3 có baseline.

### Cách làm

1. `config.py`:
   ```python
   EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")
   ```
2. `core/embeddings.py`: `SentenceTransformer(EMBEDDING_MODEL)`.
3. Re-embed: `EMBEDDING_MODEL=path/local python scripts/embed_existing.py`.
4. Drop + tạo lại pgvector index (dimension không đổi nhưng vector phân bố khác).
5. A/B benchmark Task 1.3:
   | Model | P@5 | nDCG@10 | Latency |
   |-------|-----|---------|---------|
   | e5-large HF | ? | ? | ? |
   | e5-finetuned | ? | ? | ? |
6. Ship nếu delta ≥ 5% relative.

### Acceptance

- [ ] Đổi `EMBEDDING_MODEL` trong `.env` → log: `Loading <new>`.
- [ ] Re-embed 75 reports không lỗi.
- [ ] A/B bảng trong `BENCHMARK_REPORT.md`.
- [ ] README cập nhật nếu ship.

### Files
- `backend-v2/config.py`, `.env.example`
- `backend-v2/core/embeddings.py`
- `backend-v2/scripts/embed_existing.py` (verify)
- `docs/BENCHMARK_REPORT.md`, `README.md`

### Risk
Trung bình. Drop index **trước** khi re-embed.

---

# PHASE 2 — PILOT NỘI BỘ

> **Mục tiêu:** 3–5 bác sĩ/KTV dùng 1–2 tuần, có feedback log thật.

## Task 2.11 — Docker compose profile dev/demo

### Background

`docker-compose.yml` hiện 1 profile. Pilot cần tách `dev` (volume local) và `demo` (init seed data).

### Cách làm

```yaml
services:
  postgres:
    profiles: [dev, demo]
    ...
  postgres-seed:
    profiles: [demo]
    image: pgvector/pgvector:pg16
    depends_on: [postgres]
    command: ["psql", "-h", "postgres", "-U", "${DB_USER}", "-f", "/seed/seed.sql"]
    volumes:
      - ./backend-v2/scripts/seed.sql:/seed/seed.sql
```

Chạy: `docker compose --profile demo up`.

### Acceptance
- [ ] `docker compose --profile dev up` → chỉ Postgres + Orthanc.
- [ ] `docker compose --profile demo up` → thêm seed.
- [ ] README mục Quick start update 2 mode.

### Risk
Thấp.

---

## Task 2.10 — Không log JWT / commit `.env`

### Background

Pre-pilot: rà soát secret leak.

### Cách làm

1. `grep -rn "token\|secret\|password" backend-v2/ --include="*.py"` → review log statement.
2. Đảm bảo `.env` trong `.gitignore` (✅ đã có).
3. `git log --all -p | grep -i "JWT_SECRET\|pacs_pass"` → nếu có history → tài liệu xóa hoặc rotate.
4. Thêm pre-commit hook hoặc CI check `truffleHog`/`gitleaks` (optional).

### Acceptance
- [ ] Không có `print(token)` hoặc `logger.info(f"... {jwt} ...")` trong code.
- [ ] `git secrets --scan` (hoặc gitleaks) clean.
- [ ] `.env.example` không chứa secret thật.

### Risk
Thấp.

---

## Task 2.7 — WADO check quyền study (BẢO MẬT pilot)

### Background

`/api/dicom/wado?objectId=...&token=...` chỉ validate JWT, **không** check `objectId` thuộc study của user. Patient với token có thể stream ảnh BN khác nếu biết Orthanc instance ID.

### Pre-conditions
- Hiểu Orthanc API: `GET /instances/{id}/study` trả parent study UID.

### Cách làm

1. Trong `api/dicom.py` `get_wado()`:
   ```python
   parent_study_uid = OrthancClient.get_instance_study_uid(objectId)
   cursor.execute("SELECT patient_id FROM studies WHERE study_uid=%s", (parent_study_uid,))
   study_patient = cursor.fetchone()
   if user.role == "patient" and study_patient["patient_id"] != user.linked_patient_id:
       raise HTTPException(403, "Không có quyền")
   ```
2. Cache mapping `instanceId → study_id` trong memory (TTL 5 phút) để tránh gọi Orthanc mỗi request.

### Acceptance
- [ ] Patient A login → cố stream instance của patient B → **403**.
- [ ] Doctor/admin → stream được tất cả.
- [ ] Latency WADO không tăng > 100ms (do cache).

### Files
- `backend-v2/api/dicom.py`
- `backend-v2/core/orthanc_client.py` (thêm method nếu cần)

### Risk
Cao — đụng viewer. Test kỹ Cornerstone vẫn load.

### Commit gợi ý
```
fix(security): WADO checks study ownership for patient role
```

---

## Task 2.8 — Audit log mở rộng

### Background

`core/audit_logger.py` chỉ ghi login. Pilot cần log thêm để truy vết.

### Cách làm

1. Thêm `AuditAction` enum:
   ```python
   class AuditAction(str, Enum):
       LOGIN = "LOGIN"
       LOGIN_FAILED = "LOGIN_FAILED"
       REPORT_CREATE = "REPORT_CREATE"
       REPORT_UPDATE = "REPORT_UPDATE"
       DICOM_UPLOAD = "DICOM_UPLOAD"
       SEARCH_QUERY = "SEARCH_QUERY"  # log hash query, không log full
       PDF_EXPORT = "PDF_EXPORT"
   ```
2. Áp dụng vào `api/report.py`, `api/dicom.py`, `api/ask.py`:
   ```python
   log_action(request, AuditAction.REPORT_CREATE, user_id=user.id, study_id=body.study_id)
   ```
3. SEARCH log hash query (SHA256 first 8 char) để không lộ PII nếu chính sách yêu cầu.

### Acceptance
- [ ] Mỗi action có dòng JSON trong audit log file.
- [ ] Log có `timestamp`, `action`, `user_id`, `entity_id`, `ip`.
- [ ] Không log JWT / password / full SQL.

### Files
- `backend-v2/core/audit_logger.py`
- `backend-v2/api/report.py`
- `backend-v2/api/dicom.py`
- `backend-v2/api/ask.py`

### Risk
Thấp.

---

## Task 2.9 — Patient đổi mật khẩu lần đầu

### Background

Patient auto-create với password `{PatientID}@` — dễ đoán. Pilot cần bắt đổi.

### Cách làm

1. Thêm cột `users.must_change_password BOOLEAN DEFAULT FALSE` + migration.
2. Khi `api/dicom.py` tạo user patient → set `must_change_password=TRUE`.
3. `/api/auth/login` response thêm flag `must_change_password`.
4. Frontend: nếu flag → redirect `/change-password` trước khi vào `/my-studies`.
5. `POST /api/auth/change-password` validate + update.

### Acceptance
- [ ] Patient mới login → trang đổi mật khẩu hiện trước.
- [ ] Đổi xong → vào MyStudies.
- [ ] Doctor/admin không bị ép.

### Files
- `backend-v2/database/init_db.sql` (migration thêm cột)
- `backend-v2/models/user.py`
- `backend-v2/api/auth.py`
- `backend-v2/api/dicom.py`
- `frontend-react/src/pages/ChangePassword/` (mới)
- `frontend-react/src/App.jsx`

### Risk
Trung bình — auth flow.

---

## Task 2.5 — Worklist pagination + search BN

### Background

`GET /api/worklist` trả full list. Với > 200 ca sẽ chậm + lag UI.

### Cách làm

1. API:
   ```python
   def get_worklist(
       page: int = 1, page_size: int = 50,
       patient_search: str | None = None,
       ...
   ):
       offset = (page - 1) * page_size
       # WHERE patient.full_name ILIKE %s OR patient_id ILIKE %s
       # SELECT ... LIMIT %s OFFSET %s
       # SELECT COUNT(*) ... → total
       return {"items":..., "total":..., "page":..., "page_size":...}
   ```
2. FE: component `Pagination`, input search BN có debounce 300ms.

### Acceptance
- [ ] Tải 200 ca → < 500ms.
- [ ] Search tên BN → kết quả realtime.
- [ ] URL có `?page=2&search=...` (deep link).

### Files
- `backend-v2/api/worklist.py`
- `frontend-react/src/pages/Worklist/index.jsx`
- `frontend-react/src/api/worklist.js`

### Risk
Trung bình.

---

## Task 2.1 — Search: giải thích intent + lý do

### Background

Search trả intent + kết quả nhưng người dùng không biết **tại sao** AI chọn intent đó / score đến từ đâu.

### Cách làm

1. Backend trả về `router_debug` đã có (`scores`, `gap`, `features`).
2. FE component `<IntentExplainer />`:
   - Badge intent + confidence.
   - Tooltip: "Câu chứa từ y khoa 'tràn dịch' (+0.7), từ đếm 'bao nhiêu' (+0.7) → HYBRID."
   - Hiển thị scores bar mini.
3. Mỗi result card: tooltip score breakdown (`dense_score`, `sparse_score`).

### Acceptance
- [ ] Hover badge intent → giải thích tiếng Việt.
- [ ] Card RAG hover → "Dense 0.85, Sparse 0.72, RRF rank 1".
- [ ] Không clutter UI khi không hover.

### Files
- `frontend-react/src/pages/Search/index.jsx`
- `frontend-react/src/components/shared/IntentExplainer.jsx` (mới)

### Risk
Thấp.

---

## Task 2.2 — `generate_answer` v2

### Background

Hiện chỉ template "Tìm thấy N kết quả". HYBRID không tổng hợp SQL + RAG.

### Cách làm — 2 hướng

**Hướng A (rẻ, đủ cho pilot):** template giàu hơn.
- STRUCTURED count: "Có **5** ca CT trong ngày 19/05/2026 (4 PENDING, 1 REPORTED)."
- STRUCTURED list: liệt kê top 3 ca + "... và 17 ca khác."
- SEMANTIC: "Tìm thấy **8** báo cáo liên quan đến *tràn dịch*. Báo cáo phù hợp nhất: BN Nguyễn Văn A (CT ngực, 18/05)."

**Hướng B (đắt, sau pilot):** LLM summarize với context giới hạn.
- Truyền SQL rows + top 3 RAG snippets vào Ollama → 1 đoạn text.
- Rate limit chặt: 10/phút (đã có).
- Cache theo hash query.

Bắt đầu hướng A. Hướng B chỉ làm nếu pilot feedback yêu cầu.

### Acceptance
- [ ] STRUCTURED có ≥ 1 con số cụ thể trong answer.
- [ ] HYBRID nêu cả SQL count + RAG top result.
- [ ] Không gọi LLM lần 2 (hướng A).

### Files
- `backend-v2/core/nl2sql_engine.py` (`generate_answer`)

### Risk
Thấp (hướng A).

---

## Task 2.3 — Lịch sử câu hỏi gần đây

### Background

Tiện tra lại câu hỏi trước.

### Cách làm

1. **Hướng đơn giản:** `localStorage` array max 20 query.
   ```js
   const STORAGE_KEY = 'pacs_search_history';
   function pushHistory(q) {
     const arr = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
     const next = [q, ...arr.filter(x => x !== q)].slice(0, 20);
     localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
   }
   ```
2. UI: dropdown dưới input search.
3. (Sau) đồng bộ qua DB nếu cần multi-device.

### Acceptance
- [ ] Click history → fill input.
- [ ] Max 20 entry, dedupe.
- [ ] Persist sau reload.

### Files
- `frontend-react/src/pages/Search/index.jsx`

### Risk
Rất thấp.

---

## Task 2.4 — Report autosave draft

### Background

Bác sĩ mất kết nối / refresh → mất nội dung đang viết.

### Cách làm

1. `localStorage` key `pacs_report_draft_{study_id}`.
2. Debounce 2s sau mỗi keystroke → save.
3. Khi mở report:
   - Nếu draft tồn tại + khác content server → banner "Khôi phục bản nháp / Bỏ".
4. Sau khi `POST /api/report` thành công → xóa draft.

### Acceptance
- [ ] Gõ → đợi 2s → reload → draft khôi phục.
- [ ] Submit thành công → draft bị xóa.
- [ ] Draft chỉ scope theo `study_id`.

### Files
- `frontend-react/src/pages/Report/index.jsx`

### Risk
Thấp.

---

## Task 2.6 — Onboarding 1 trang

### Background

Pilot user không đọc README → cần hướng dẫn ngắn trong app.

### Cách làm

`/help` page hoặc modal "Hướng dẫn" trong Topbar:
- 4 role: làm gì
- 3 ví dụ câu Search ("Nguyễn Văn A", "bao nhiêu ca CT hôm nay", "tổn thương phổi")
- Cách upload DICOM (technician)
- Cách viết báo cáo (doctor)
- Hotline support

### Acceptance
- [ ] Modal/page accessible từ Topbar.
- [ ] Có ảnh chụp màn hình hoặc GIF cho mỗi flow.
- [ ] Mobile-friendly.

### Files
- `frontend-react/src/pages/Help/` (mới) hoặc `components/HelpModal.jsx`

### Risk
Rất thấp.

---

## Task 2.12 — Script backup DB

### Background

Pilot có data thật → cần backup trước khi update.

### Cách làm

`scripts/backup_db.sh` (hoặc `.ps1`):
```bash
#!/usr/bin/env bash
TS=$(date +%Y%m%d_%H%M%S)
OUT="backups/pacs_db_${TS}.sql.gz"
mkdir -p backups
docker exec pacs_postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$OUT"
echo "Backup: $OUT ($(du -h "$OUT" | cut -f1))"
# Giữ 7 backup gần nhất
ls -1t backups/*.sql.gz | tail -n +8 | xargs -r rm
```

Schedule (Windows): Task Scheduler 1x/ngày. (Linux): cron.

### Acceptance
- [ ] Script chạy được, output file < 100MB cho 75 reports.
- [ ] Restore test: `gunzip < backup.sql.gz | psql ...` → đếm rows khớp.
- [ ] `backups/` trong `.gitignore`.

### Files
- `scripts/backup_db.sh` (hoặc `.ps1`)
- `.gitignore`

### Risk
Thấp.

---

## Task 2.13 — Staging deploy

### Background

Pilot không thể local-only. Cần URL public (giới hạn IP / VPN nội bộ).

### Cách làm — 2 hướng

**Hướng A (rẻ):** 1 VPS (Hetzner / Vultr ~5$/tháng).
- Docker compose stack: Postgres + Orthanc + backend + nginx (FE static).
- Caddy/Traefik auto HTTPS.
- IP allowlist hoặc basic auth.

**Hướng B (free):** Railway / Render.
- Postgres managed.
- Orthanc khó vì cần persistent storage > free tier.
- Backend free tier hạn chế.

Chọn A nếu pilot > 1 tuần.

### Acceptance
- [ ] `https://staging.pacs.example.com` truy cập được.
- [ ] HTTPS hợp lệ.
- [ ] Auth + role hoạt động.
- [ ] CI deploy tự động khi push `main`.

### Files
- `deploy/docker-compose.prod.yml`
- `deploy/Caddyfile` hoặc `nginx.conf`
- `.github/workflows/deploy-staging.yml`
- `docs/DEPLOY_STAGING.md` (mới)

### Risk
Trung bình–cao. Bắt đầu manual deploy trước khi tự động.

---

# PHASE 3 — PATTERN QUERIES & SCALE

## Task 3.7 — PostgreSQL FTS thay BM25

### Background

BM25 in-memory không scale > 2.000 reports. PostgreSQL FTS native + GIN index.

### Pre-conditions
- Hiểu `tsvector`, `tsquery`, Vietnamese dictionary (config `simple` đủ).

### Cách làm

1. Migration:
   ```sql
   ALTER TABLE diagnostic_reports
     ADD COLUMN search_tsv tsvector
     GENERATED ALWAYS AS (
       to_tsvector('simple', coalesce(findings,'') || ' ' || coalesce(conclusion,''))
     ) STORED;
   CREATE INDEX idx_reports_tsv ON diagnostic_reports USING GIN (search_tsv);
   ```
2. `core/rag_engine.py` thêm `fts_search()`:
   ```python
   cursor.execute("""
     SELECT ..., ts_rank(search_tsv, query) AS score
     FROM diagnostic_reports r, plainto_tsquery('simple', %s) query
     WHERE search_tsv @@ query
     ORDER BY score DESC LIMIT %s
   """, (q, top_k))
   ```
3. Trong `hybrid_search`: switch sparse từ BM25 sang FTS theo flag env hoặc theo corpus size.

### Acceptance
- [ ] FTS search < 100ms với 2.000 reports.
- [ ] RAG benchmark (Task 1.3) không tụt > 5%.
- [ ] BM25 path vẫn giữ làm fallback.

### Files
- `backend-v2/database/init_db.sql`
- `backend-v2/core/rag_engine.py`
- `docs/BENCHMARK_REPORT.md`

### Risk
Trung bình. Vietnamese FTS không có stemmer tốt → có thể recall giảm cho từ biến thể.

---

## Task 3.6 — IVFFlat/HNSW tune

### Background

`init_db.sql` IVFFlat `lists=10` — phù hợp < 1k vectors. Khi 2.000+ → recall giảm.

### Cách làm

1. Tăng `lists`:
   ```sql
   DROP INDEX idx_reports_embedding;
   CREATE INDEX idx_reports_embedding ON diagnostic_reports
     USING ivfflat (embedding vector_cosine_ops)
     WITH (lists = 100);  -- ~sqrt(N) cho N vectors
   ```
2. Hoặc thử HNSW (pgvector ≥ 0.5):
   ```sql
   CREATE INDEX idx_reports_embedding_hnsw ON diagnostic_reports
     USING hnsw (embedding vector_cosine_ops)
     WITH (m = 16, ef_construction = 64);
   ```
3. Benchmark Task 1.3 trước/sau → ghi.

### Acceptance
- [ ] Index tạo xong < 30s.
- [ ] Latency dense search giảm hoặc giữ.
- [ ] Recall không tụt > 5%.

### Files
- `backend-v2/database/init_db.sql`
- `backend-v2/scripts/ensure_vector_index.py` (mới)

### Risk
Thấp.

---

## Task 3.9 — API pagination chuẩn

### Background

Worklist (Task 2.5) đã pagination. Cần áp dụng cho search, admin/users, report list nếu có.

### Cách làm

1. Helper `core/pagination.py`:
   ```python
   class Page(BaseModel):
       items: list
       total: int
       page: int
       page_size: int
       has_next: bool
   ```
2. Áp dụng `GET /api/search/keyword`, `GET /api/admin/users`, etc.
3. FE: shared `<Pagination />` component.

### Acceptance
- [ ] 3+ endpoint paginated consistent.
- [ ] FE component reuse được.

### Files
- `backend-v2/core/pagination.py` (mới)
- API liên quan
- `frontend-react/src/components/shared/Pagination.jsx`

### Risk
Thấp.

---

## Task 3.1 — Entity extractor (Light KG)

### Background

Cần extract entity y khoa (disease, anatomy, severity) từ findings/conclusion → lưu JSONB. Phase 3 dùng để pattern queries.

### Cách làm

1. `core/entity_extractor.py`:
   ```python
   PROMPT = """Trích xuất entity y khoa từ báo cáo X-quang tiếng Việt.
   Trả về JSON: {"diseases":[], "anatomy":[], "severity":"", "modality":""}
   Không thêm giải thích.

   Báo cáo: {text}
   JSON:"""

   def extract_entities(text: str) -> dict:
       resp = requests.post(f"{OLLAMA_URL}/api/generate",
           json={"model": OLLAMA_NL2SQL_MODEL, "prompt": PROMPT.format(text=text), "stream": False, "format":"json"},
           timeout=60)
       return json.loads(resp.json()["response"])
   ```
2. Test trên 10 báo cáo mẫu → tinh chỉnh prompt.

### Acceptance
- [ ] 10 mẫu test có ≥ 80% entity đúng (review tay).
- [ ] Output luôn parse JSON được (`format: json` của Ollama).
- [ ] Có file `tests/data/entity_examples.jsonl` ghi golden output.

### Files
- `backend-v2/core/entity_extractor.py` (mới)
- `backend-v2/tests/data/entity_examples.jsonl` (mới)
- `backend-v2/tests/test_entity_extractor.py` (mới, integration)

### Risk
Trung bình. Prompt sensitive — track version.

---

## Task 3.2 — Migration entities JSONB + GIN

### Cách làm

1. `init_db.sql`:
   ```sql
   ALTER TABLE diagnostic_reports
     ADD COLUMN IF NOT EXISTS entities JSONB;
   CREATE INDEX IF NOT EXISTS idx_reports_entities
     ON diagnostic_reports USING GIN (entities);
   ```
2. Pipeline `api/report.py`: sau embed → gọi `extract_entities()` → UPDATE.
3. Async optional (Task 3.8).

### Acceptance
- [ ] Migration apply không lỗi.
- [ ] Report mới có `entities` populated.
- [ ] Query `WHERE entities->'diseases' ? 'X'` < 50ms với 500 reports.

### Files
- `backend-v2/database/init_db.sql`
- `backend-v2/api/report.py`

### Risk
Thấp.

---

## Task 3.3 — Backfill entities cho corpus

### Cách làm

`scripts/extract_entities.py`:
```python
def main(batch_size=10):
    cur.execute("SELECT id, findings, conclusion FROM diagnostic_reports WHERE entities IS NULL")
    for row in cur.fetchall():
        text = f"{row['findings']} {row['conclusion']}"
        ents = extract_entities(text)
        cur.execute("UPDATE diagnostic_reports SET entities=%s WHERE id=%s", (json.dumps(ents), row['id']))
        if i % batch_size == 0:
            conn.commit()
            print(f"Processed {i}/{total}")
```

### Acceptance
- [ ] 100% reports có `entities IS NOT NULL` sau chạy.
- [ ] Spot check 20 mẫu → ≥ 80% đúng.

### Files
- `backend-v2/scripts/extract_entities.py` (mới)

### Risk
Thấp.

---

## Task 3.4 — NL2SQL prompt bổ sung JSONB

### Cách làm

Bổ sung vào prompt của `llm_nl2sql()`:
```
Bảng diagnostic_reports có cột entities JSONB với schema:
  {"diseases":[...], "anatomy":[...], "severity":"...", "modality":"..."}

Ví dụ:
Q: bệnh nào hay đi kèm tràn dịch
SQL: SELECT jsonb_array_elements_text(entities->'diseases') AS d, COUNT(*)
     FROM diagnostic_reports
     WHERE entities->'diseases' ? 'tràn dịch'
     GROUP BY d ORDER BY 2 DESC LIMIT 10;
```

### Acceptance
- [ ] LLM sinh SQL JSONB đúng cho 5/5 ví dụ test.
- [ ] `_validate_sql` accept JSONB syntax.

### Files
- `backend-v2/core/nl2sql_engine.py`

### Risk
Trung bình. Test prompt cẩn thận.

---

## Task 3.5 — Pattern gold set + benchmark

### Cách làm

`tests/data/pattern_gold.jsonl` (~20 câu):
```json
{"id":"P001","query":"bệnh nào hay đi kèm tràn dịch","expected_results_contain":["viêm phổi","u phổi"]}
{"id":"P002","query":"modality nào hay phát hiện u gan","expected_results_contain":["CT","MR"]}
```

Eval: `tests/benchmark/run_pattern_eval.py` chạy NL2SQL → execute_sql → so kết quả với `expected_results_contain` (substring match).

### Acceptance
- [ ] ≥ 15/20 câu pattern trả lời đúng.
- [ ] Cập nhật `BENCHMARK_REPORT.md` §4 (mới).

### Files
- `backend-v2/tests/data/pattern_gold.jsonl`
- `backend-v2/tests/benchmark/run_pattern_eval.py`
- `docs/BENCHMARK_REPORT.md`

### Risk
Trung bình.

---

## Task 3.8 — Background worker embed/entity

### Background

Upload hàng loạt DICOM → embed + entity blocking → request chậm.

### Cách làm

1. Thư viện đơn giản: `rq` (Redis Queue) hoặc cron Python.
2. `POST /api/report` enqueue job, return ngay.
3. Worker process: pop job → embed → entity → UPDATE.
4. Compose thêm Redis service.

### Acceptance
- [ ] POST report response < 200ms (không chờ embed).
- [ ] Worker log success/fail.
- [ ] Embedding cuối cùng vẫn populated trong DB.

### Files
- `backend-v2/core/worker.py` (mới)
- `backend-v2/api/report.py`
- `docker-compose.yml`
- `backend-v2/requirements.txt` (`rq`, `redis`)

### Risk
Cao — thêm infra. Chỉ làm khi pilot có pain point thật.

---

## Khi quay lại sau vài tuần

### Checklist 5 phút khởi động

```powershell
cd e:\HoangDucLong_javisai\pacs_rag_system
git checkout phase-1-intelligence  # hoặc branch hiện tại
git pull
cd backend-v2
.\venv\Scripts\activate
python -m pytest tests/ -q                          # tất cả pass?
python -m tests.benchmark.run_router_eval           # số khớp BENCHMARK_REPORT?
```

Đối chiếu với `docs/BENCHMARK_REPORT.md` §"Lịch sử thay đổi". Nếu pytest fail → `git log -10`.

### Chọn task tiếp theo

1. Mở [Thứ tự đề xuất toàn cục](#thứ-tự-đề-xuất-toàn-cục).
2. Tìm task đầu tiên chưa Done (chưa có commit + chưa check trong roadmap).
3. Đọc spec task đó trong playbook này.
4. Bắt đầu.

### Khi gặp blocker

- Spec không đủ rõ → ghi câu hỏi vào commit message `[QUESTION] ...` và playbook section "Open questions" (chưa có, tạo khi cần).
- Metric tụt sau khi sửa → revert nhanh, không cố cứu.
- Phụ thuộc bên ngoài (Kaggle, Ollama, VPS) → skip task đó, sang task khác trong cùng phase.

---

*Playbook này tự đứng — không cần đọc file khác để biết Phase 1–3 còn gì.*
