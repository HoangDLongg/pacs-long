# PACS++ — Benchmark Report

> Theo dõi metric router & RAG theo phase. Mọi thay đổi router/embedding phải cập nhật bảng này.

---

## 1. Query Router

### Baseline 2026-05-19 (Phase 1.1)

- Gold set: **74 câu** ([`backend-v2/tests/data/router_gold.jsonl`](../backend-v2/tests/data/router_gold.jsonl))
- Evaluator: `python -m tests.benchmark.run_router_eval`
- Code: `core/query_router.py` (rule-based, vocab.json)

| Metric | Giá trị |
|--------|---------|
| **Overall accuracy** | **82.4%** (61/74) |
| PATIENT_LOOKUP | 94.4% (17/18) |
| STRUCTURED | 86.4% (19/22) |
| SEMANTIC | 100.0% (24/24) |
| HYBRID | **10.0%** (1/10) ⚠️ |

**Confusion (kỳ vọng → dự đoán, count):**

| Expected | Predicted | Count |
|----------|-----------|-------|
| HYBRID | SEMANTIC | 6 |
| HYBRID | STRUCTURED | 3 |
| STRUCTURED | SEMANTIC | 3 |
| PATIENT_LOOKUP | SEMANTIC | 1 |

### Phân tích

- **HYBRID rất yếu:** câu có cả medical term + counting/listing (ví dụ "bao nhiêu ca CT có tổn thương phổi") gần như luôn bị nhận thành SEMANTIC vì boost medical kéo gap quá xa khỏi STRUCTURED.
- **STRUCTURED edge cases:** "ca chụp tháng 1", "modality nào nhiều nhất" rơi vào fallback SEMANTIC (confidence 0.3) vì chỉ chứa **1 tín hiệu** structured nhưng dưới `LOW_CONFIDENCE`.
- **SEMANTIC & PATIENT_LOOKUP tốt:** vocab + heuristic tên VN hiện đủ dùng.

### Threshold CI hiện tại

| Intent | Threshold |
|--------|-----------|
| Overall | ≥ 75% |
| PATIENT_LOOKUP | ≥ 85% |
| STRUCTURED | ≥ 75% |
| SEMANTIC | ≥ 90% |
| HYBRID | *chưa đặt* — sẽ thêm sau khi tune |

> Khi commit thay đổi router → chạy `pytest tests/test_router_gold.py` → nếu giảm so với baseline thì roadmap fail.

### Plan tune (Phase 1.2–1.5)

1. Tăng cường rule HYBRID: khi `has_medical_term AND (has_counting_kw OR has_listing_kw OR has_stats_kw)` → boost STRUCTURED đủ để gap < `HYBRID_MAX_GAP`.
2. Hạ `LOW_CONFIDENCE` xuống 0.2 hoặc loại fallback SEMANTIC khi đã có signal structured đơn lẻ.
3. Mở rộng gold set 74 → 100+ khi pilot có log thật.

---

## 2. RAG (Dense / Hybrid)

*Chưa có baseline — Phase 1.2 sẽ tạo `rag_gold.jsonl` (50 câu + relevant report_ids) và đo nDCG@10, P@5.*

---

## 3. NL2SQL

*Chưa benchmark độ chính xác sinh SQL — chỉ có security tests (`test_nl2sql_security.py`). Phase 1+ sẽ thêm execution accuracy.*

---

## Lịch sử thay đổi

| Date | Metric | Trước | Sau | Commit |
|------|--------|-------|-----|--------|
| 2026-05-19 | Router accuracy | — | 82.4% | baseline |
