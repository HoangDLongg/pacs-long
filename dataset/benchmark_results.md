# Benchmark Results — Query Router Accuracy
**Date**: 2026-05-17
**Test file**: dataset/datatest.json (1000 cases)
**Model**: multilingual-e5-large (embedding similarity)

## Overall: 34.2% (342/1000)

## Per-Intent Accuracy

| Intent | Correct | Total | Accuracy |
|--------|---------|-------|----------|
| PATIENT_LOOKUP | 245 | 251 | **97.6%** |
| STRUCTURED | 72 | 425 | **16.9%** |
| SEMANTIC | 25 | 324 | **7.7%** |

## Confusion Matrix

| Actual \ Predicted | PATIENT_LOOKUP | SEMANTIC | STRUCTURED | HYBRID |
|---|---|---|---|---|
| PATIENT_LOOKUP (251) | **245** | 0 | 0 | 6 |
| SEMANTIC (324) | 45 | **25** | 0 | 254 |
| STRUCTURED (425) | 40 | 0 | **72** | 313 |

## Per-Group Accuracy

### PATIENT_LOOKUP (97.6% overall)
| Group | Accuracy |
|-------|----------|
| Tên VN có dấu | 100% (50/50) |
| Tên VN không dấu | 100% (40/40) |
| Có prefix tìm kiếm | 100% (50/50) |
| Mã bệnh nhân | 100% (30/30) |
| Tên 2 từ (dễ nhầm) | 100% (30/30) |
| Tên kèm context | 86.7% (26/30) |
| Tên viết tắt / nickname | 95% (19/20) |

### STRUCTURED (16.9% overall)
| Group | Accuracy |
|-------|----------|
| Đếm ca theo modality | ~30% |
| Đếm ca theo status | ~25% |
| Đếm chung | ~30% |
| Thống kê / phân tích | ~10% |
| Danh sách ca | ~20% |
| Danh sách bệnh nhân | ~40% |
| Tra cứu entity (BN) | ~0% |
| Tra cứu entity (BS) | ~10% |
| Tra cứu ca cụ thể | ~10% |
| Câu dài / tự nhiên | ~15% |
| Viết tắt / typo | ~15% |

### SEMANTIC (7.7% overall)
| Group | Accuracy |
|-------|----------|
| Bệnh phổi | ~15% |
| Bệnh tim mạch | ~10% |
| Bệnh xương khớp | ~10% |
| Bệnh gan / ổ bụng | ~5% |
| Bệnh não / thần kinh | ~10% |
| Bệnh vú / tuyến | ~15% |
| Bệnh khác | ~5% |
| Tìm ca tương tự | ~10% |
| Y khoa tiếng Anh | 0% |
| Y khoa dài / mô tả | ~10% |

## Root Cause Analysis

### Problem 1: HYBRID over-triggering (573/1000 = 57.3%)
- Embedding similarity scores are too close between intents (gap < 0.10)
- Training examples only ~50 total → insufficient coverage
- HYBRID threshold too aggressive

### Problem 2: SEMANTIC → PATIENT_LOOKUP (45 cases)
- Short medical terms (2 words) confused with Vietnamese names
- e.g., "lách to", "u gan", "áp xe gan" → classified as name

### Problem 3: STRUCTURED → HYBRID (313 cases)
- STRUCTURED intent has most diverse query patterns
- Counting keywords not distinguished from semantic terms
- Training examples don't cover enough variations

## Conclusion
Embedding-based classifier with ~50 training examples is **fundamentally insufficient**.
Recommend: Multi-signal scoring (regex + keyword rules) for STRUCTURED/PATIENT_LOOKUP,
with SEMANTIC as default fallback.
