"""
core/query_router.py — Multi-Signal Intent Classifier cho PACS++

Pattern từ RAGCHATBOTV2:
    extract_query_features() → compute_intent_scores() → select_intent()

Intents:
    PATIENT_LOOKUP: tìm bệnh nhân theo tên/mã
    STRUCTURED:     thống kê, đếm, danh sách → SQL
    SEMANTIC:       nội dung y khoa, tìm ca tương tự → RAG (hybrid search)
    HYBRID:         mập mờ giữa STRUCTURED & SEMANTIC → chạy cả 2

SEMANTIC = default fallback vì đây là core use case (bác sĩ tìm ca tương tự).

Vocab data loaded from config/vocab.json (tách data khỏi logic).
"""

import re
import json
import logging
from pathlib import Path
from typing import Tuple, Dict

logger = logging.getLogger(__name__)


# ============================================================
# Scoring weights — named constants (không dùng magic numbers)
# ============================================================

# PATIENT_LOOKUP weights
W_VN_NAME = 0.8          # Tên người VN detected
W_PATIENT_ID = 0.9       # Mã BN (A000801, P12345)
W_BN_PREFIX = 0.6        # Prefix BN/B.N/bệnh nhân + tên
W_NAME_INITIALS = 0.7    # Viết tắt tên: L.T.H

# STRUCTURED weights
W_COUNTING = 0.7         # bao nhiêu, mấy, đếm
W_LISTING = 0.6          # danh sách, liệt kê
W_STATS = 0.7            # thống kê, tỷ lệ
W_STATUS = 0.5           # pending, reported, verified
W_TIME = 0.3             # hôm nay, tuần này
W_MODALITY = 0.2         # CT, MR (khi không có medical)
W_DOCTOR = 0.4           # bác sĩ X
W_CASE_REF = 0.6         # ca số 123

# SEMANTIC weights
W_MEDICAL_VN = 0.7       # thuật ngữ y khoa VN
W_MEDICAL_EN = 0.6       # thuật ngữ y khoa EN
W_SIMILAR = 0.5          # tìm ca tương tự
W_ANATOMY = 0.3          # phổi, gan, não...
W_DIAGNOSIS = 0.3        # chẩn đoán, kết luận

# Cross-intent
W_NAME_BOOST = 0.3       # Boost PL khi có tên thật
W_NAME_SUPPRESS_STRUCT = 0.5  # Suppress STRUCT khi có tên
W_NAME_SUPPRESS_SEMAN = 0.3   # Suppress SEMANTIC khi có tên

# Thresholds
HYBRID_MIN_SCORE = 0.5   # Score tối thiểu để trigger HYBRID
HYBRID_MAX_GAP = 0.15    # Gap tối đa giữa 2 intent cho HYBRID
LOW_CONFIDENCE = 0.3     # Dưới ngưỡng này → SEMANTIC default
DEFAULT_SEMANTIC_SCORE = 0.3  # Score mặc định cho SEMANTIC fallback


# ============================================================
# Load vocab from config/vocab.json
# ============================================================

def _load_vocab() -> dict:
    """Load vocabulary từ config/vocab.json."""
    vocab_path = Path(__file__).parent.parent / "config" / "vocab.json"
    try:
        with open(vocab_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"[Router] vocab.json not found at {vocab_path}, using empty vocab")
        return {}


_VOCAB = _load_vocab()

# Frozen sets từ vocab
_VN_SURNAMES = frozenset(_VOCAB.get("vn_surnames", []))
_VN_MIDDLE_NAMES = frozenset(_VOCAB.get("vn_middle_names", []))
_VN_GIVEN_NAMES = frozenset(_VOCAB.get("vn_given_names", []))
_COUNTING_KW = frozenset(_VOCAB.get("counting_keywords", []))
_LISTING_KW = frozenset(_VOCAB.get("listing_keywords", []))
_STATS_KW = frozenset(_VOCAB.get("stats_keywords", []))
_STATUS_KW = frozenset(_VOCAB.get("status_keywords", []))
_MODALITY_TERMS = frozenset(_VOCAB.get("modality_terms", []))
_TIME_KW = frozenset(_VOCAB.get("time_keywords", []))
_MEDICAL_TERMS_VN = frozenset(_VOCAB.get("medical_terms_vn", []))
_MEDICAL_TERMS_EN = frozenset(_VOCAB.get("medical_terms_en", []))
_ANATOMY_TERMS = frozenset(_VOCAB.get("anatomy_terms", []))
_SIMILAR_KW = frozenset(_VOCAB.get("similar_keywords", []))
ABBREV_MAP = _VOCAB.get("abbreviations", {})

logger.info(f"[Router] Loaded vocab: {len(_VN_SURNAMES)} surnames, "
            f"{len(_MEDICAL_TERMS_VN)} medical terms VN, "
            f"{len(_VN_GIVEN_NAMES)} given names")


# ============================================================
# Abbreviation expansion
# ============================================================

def _expand_abbrev(text: str) -> str:
    """Mở rộng viết tắt VN phổ biến.
    Chỉ expand cho scoring, KHÔNG dùng cho name detection."""
    words = text.lower().split()
    expanded = [ABBREV_MAP.get(w, w) for w in words]
    return ' '.join(expanded)


# ============================================================
# Feature: PATIENT_LOOKUP — Name detection
# ============================================================

# Prefix tìm kiếm BN
_NAME_PREFIXES = re.compile(
    r'^(?:tìm|tim|search|tra cứu|tra cuu|xem|kiểm tra|kiem tra|'
    r'tìm kiếm|tim kiem|hồ sơ|ho so|mở|check|gọi|truy xuất|'
    r'cần tìm|tôi muốn tìm|tìm giúp|cho tôi xem|thông tin chi tiết|'
    r'thông tin|lấy|tra thông tin|tra thong tin|'
    r'gọi cho|gọi tới|liên hệ|lien he|'
    r'địa chỉ của|địa chỉ|dia chi|'
    r'số điện thoại|sđt|sdt|'
    r'ngày sinh|ngày tháng năm sinh|'
    r'thông tin liên hệ|'
    r'lịch sử khám|lịch sử|'
    r'tìm kiếm ca chụp của|lấy số điện thoại)\s+',
    re.IGNORECASE
)

# BN prefix patterns
_BN_PREFIX = re.compile(
    r'(?:^|\s)(?:BN|B/N|B\.N|bn|b/n|b\.n|bệnh nhân|benh nhan|'
    r'Bênh nhân|patient)\s+',
    re.IGNORECASE
)

# Patient ID patterns
_PATIENT_ID = re.compile(
    r'(?:^|\s)(?:A\d{3,}|P\d{3,}|'
    r'(?:mã|ma|ID|id|mã số|ma so|patient.?id|patient.?ID|'
    r'mã bệnh nhân|mã BN|BN số|BN mã|mã số bn|'
    r'bệnh nhân|benh nhan|BN|bn|patient)\s*'
    r'[A-Za-z]?\d{3,})',
    re.IGNORECASE
)

# VN name initials: L.T.H, P.V.D
_NAME_INITIALS = re.compile(r'^(?:BN\s+|B/N\s+|B\.N\s+|bn\s+)?[A-Z]\.[A-Z](?:\.[A-Z])*$')

# Structured/generic words — dùng để loại trừ false positive name detection
_STRUCT_WORDS = frozenset({
    'ca', 'danh', 'sách', 'liệt', 'kê', 'tổng', 'số', 'lượng',
    'thống', 'báo', 'cáo', 'pending', 'verified', 'reported',
    'studies', 'hôm', 'nay', 'qua', 'tuần', 'tháng', 'nam', 'nữ',
    'bệnh', 'nhân', 'mấy', 'bao', 'nhiêu', 'tất', 'cả',
    'cho', 'xem', 'tôi', 'biết', 'đã', 'đến', 'khám',
    'show', 'list', 'all', 'the', 'hiển', 'thị', 'vui', 'lòng',
})

# Context keywords cần strip (dùng word boundary để tránh cắt nhầm tên)
_CONTEXT_STRIP = re.compile(
    r'\b(?:số điện thoại|sđt|ngày sinh|thông tin liên hệ|thông tin chi tiết|'
    r'lịch sử khám|lịch sử bệnh nhân|lịch sử ca chụp|'
    r'đã chụp|chụp gì|có bao nhiêu|có mấy|danh sách|trạng thái|'
    r'có ca|báo cáo|hôm nay|hôm qua|từ đầu năm|7 ngày qua|'
    r'chụp CT|chụp MR|chụp CR|chụp US|chụp DX|chụp MG|'
    r'ca pending|ca reported|ca verified|'
    r'khi nào)\b\s*',
    re.IGNORECASE
)

# Các từ đơn lẻ cần strip (dùng word boundary)
_SINGLE_WORD_STRIP = re.compile(
    r'\b(?:tháng|tuần|ngày|chưa|không|nào|gì|của)\b\s*',
    re.IGNORECASE
)

# Medical terms dùng loại trừ false positive capitalized names
_MEDICAL_EXCLUDE = frozenset({
    'viêm', 'tràn', 'gãy', 'sỏi', 'hẹp', 'xẹp',
    'nhồi máu', 'di căn', 'xuất huyết', 'tổn thương',
})


def _detect_vn_name(text: str) -> bool:
    """Kiểm tra text có chứa tên người Việt không.

    Hỗ trợ cả tên viết hoa và không viết hoa.
    """
    # Bỏ prefix tìm kiếm
    clean = _NAME_PREFIXES.sub('', text).strip()
    # Bỏ BN prefix
    clean = _BN_PREFIX.sub('', clean).strip()
    # Bỏ context keywords (dùng word boundary, tránh cắt nhầm tên)
    clean = _CONTEXT_STRIP.sub(' ', clean).strip()
    clean = _SINGLE_WORD_STRIP.sub(' ', clean).strip()
    clean = re.sub(r'\s+', ' ', clean).strip()

    parts = clean.split()
    if len(parts) < 2 or len(parts) > 6:
        return False

    # Loại trừ: toàn bộ là structured/generic keywords
    if all(p.lower() in _STRUCT_WORDS for p in parts):
        return False

    first = parts[0].lower()

    # Họ VN đứng đầu (có dấu hoặc không dấu)
    if first in _VN_SURNAMES:
        return True

    # Tên 2 từ: kiểm tra trong dictionary (KHÔNG bắt buộc viết hoa)
    if len(parts) == 2:
        p0 = parts[0].lower()
        p1 = parts[1].lower()
        if (p0 in _VN_MIDDLE_NAMES and p1 in _VN_GIVEN_NAMES) or \
           (p0 in _VN_GIVEN_NAMES and p1 in _VN_GIVEN_NAMES):
            return True

    # 3+ từ viết hoa (Nguyen Van A pattern) — vẫn cần viết hoa cho 3+ từ lạ
    if len(parts) >= 3 and all(p[0].isupper() for p in parts if p):
        medical_check = clean.lower()
        if any(m in medical_check for m in _MEDICAL_EXCLUDE):
            return False
        return True

    return False


# ============================================================
# Doctor reference
# ============================================================

_DOCTOR_KW = re.compile(
    r'(?:bác sĩ|bac si|doctor|dr\.?)\s+\w+',
    re.IGNORECASE
)


# ============================================================
# Step 1: extract_query_features()
# ============================================================

def extract_query_features(query: str) -> Dict[str, object]:
    """Trích xuất features từ query cho intent scoring.

    Pattern từ RAGCHATBOTV2 query_features.py
    """
    q = (query or "").strip()
    q_lower = q.lower()
    q_expanded = _expand_abbrev(q_lower)

    features = {}

    # ── PATIENT_LOOKUP features ──────────────────────
    features["has_vn_name"] = _detect_vn_name(q)
    features["has_patient_id"] = bool(_PATIENT_ID.search(q))
    # BN prefix: chỉ count nếu có tên sau nó (không standalone "bệnh nhân")
    bn_match = _BN_PREFIX.search(q)
    if bn_match:
        after_bn = q[bn_match.end():].strip()
        features["has_bn_prefix"] = len(after_bn) > 0 and not after_bn[0].isdigit()
    else:
        features["has_bn_prefix"] = False
    features["has_name_initials"] = bool(_NAME_INITIALS.search(q.strip()))

    # ── STRUCTURED features ──────────────────────────
    features["has_counting_kw"] = any(kw in q_expanded for kw in _COUNTING_KW)
    features["has_listing_kw"] = any(kw in q_expanded for kw in _LISTING_KW)
    features["has_stats_kw"] = any(kw in q_expanded for kw in _STATS_KW)
    features["has_status_kw"] = any(kw in q_expanded for kw in _STATUS_KW)
    features["has_time_kw"] = any(kw in q_expanded for kw in _TIME_KW) or bool(re.search(r'\d{1,2}/\d{1,2}', q))
    features["has_modality_kw"] = any(m in q.upper().split() for m in _MODALITY_TERMS) or any(m.lower() in q_lower for m in _MODALITY_TERMS if len(m) > 2)
    features["has_doctor_ref"] = bool(_DOCTOR_KW.search(q_expanded))
    # Ca cụ thể: ca số 123, ca 456, study ID
    features["has_case_ref"] = bool(re.search(r'(?:ca|ca số|study|ca chụp)\s+(?:số\s+)?\d+', q_lower)) or \
                                bool(re.search(r'(?:chi tiết|thông tin|trạng thái|status|kết quả)\s+ca\b', q_lower))

    # ── SEMANTIC features ────────────────────────────
    features["has_medical_term"] = any(t in q_lower for t in _MEDICAL_TERMS_VN)
    features["has_medical_en"] = any(t in q_lower for t in _MEDICAL_TERMS_EN)
    features["has_similar_kw"] = any(kw in q_lower for kw in _SIMILAR_KW)
    features["has_anatomy_term"] = any(t in q_lower for t in _ANATOMY_TERMS)
    features["has_diagnosis_kw"] = any(kw in q_lower for kw in {'chẩn đoán', 'kết luận', 'findings', 'conclusion', 'impression'})

    # ── Meta features ────────────────────────────────
    features["query_length"] = len(q)
    features["word_count"] = len(q.split())
    features["is_short_query"] = len(q) < 15
    features["is_long_query"] = len(q) > 60

    return features


# ============================================================
# Step 2: compute_intent_scores()
# ============================================================

def compute_intent_scores(features: Dict[str, object]) -> Dict[str, float]:
    """Tính điểm cho mỗi intent dựa trên features.

    Additive scoring — pattern từ RAGCHATBOTV2 strategy_router.py.
    Weights = named constants, không dùng magic numbers.
    """
    scores = {"PATIENT_LOOKUP": 0.0, "STRUCTURED": 0.0, "SEMANTIC": 0.0}

    # ── PATIENT_LOOKUP boosters ──────────────────────
    if features.get("has_vn_name"):
        scores["PATIENT_LOOKUP"] += W_VN_NAME
    if features.get("has_patient_id"):
        scores["PATIENT_LOOKUP"] += W_PATIENT_ID
    if features.get("has_bn_prefix"):
        scores["PATIENT_LOOKUP"] += W_BN_PREFIX
    if features.get("has_name_initials"):
        scores["PATIENT_LOOKUP"] += W_NAME_INITIALS

    # ── STRUCTURED boosters ──────────────────────────
    if features.get("has_counting_kw"):
        scores["STRUCTURED"] += W_COUNTING
    if features.get("has_listing_kw"):
        scores["STRUCTURED"] += W_LISTING
    if features.get("has_stats_kw"):
        scores["STRUCTURED"] += W_STATS
    if features.get("has_status_kw"):
        scores["STRUCTURED"] += W_STATUS
    if features.get("has_time_kw"):
        scores["STRUCTURED"] += W_TIME
    if features.get("has_modality_kw") and not features.get("has_medical_term"):
        scores["STRUCTURED"] += W_MODALITY
    if features.get("has_doctor_ref"):
        scores["STRUCTURED"] += W_DOCTOR
    if features.get("has_case_ref"):
        scores["STRUCTURED"] += W_CASE_REF

    # ── SEMANTIC boosters ────────────────────────────
    if features.get("has_medical_term"):
        scores["SEMANTIC"] += W_MEDICAL_VN
    if features.get("has_medical_en"):
        scores["SEMANTIC"] += W_MEDICAL_EN
    if features.get("has_similar_kw"):
        scores["SEMANTIC"] += W_SIMILAR
    if features.get("has_anatomy_term"):
        scores["SEMANTIC"] += W_ANATOMY
    if features.get("has_diagnosis_kw"):
        scores["SEMANTIC"] += W_DIAGNOSIS

    # ── Cross-intent interactions ────────────────────

    # Tên người thật (has_vn_name) + bất kỳ context → vẫn PATIENT_LOOKUP
    if features.get("has_vn_name"):
        scores["PATIENT_LOOKUP"] += W_NAME_BOOST
        scores["STRUCTURED"] = max(0, scores["STRUCTURED"] - W_NAME_SUPPRESS_STRUCT)
        scores["SEMANTIC"] = max(0, scores["SEMANTIC"] - W_NAME_SUPPRESS_SEMAN)

    # Modality + medical → SEMANTIC (VD: "CT phổi" = tìm ca CT về phổi)
    if features.get("has_modality_kw") and features.get("has_medical_term"):
        scores["SEMANTIC"] += W_MODALITY

    # Stats/counting + modality (không có medical) → STRUCTURED
    if (features.get("has_counting_kw") or features.get("has_stats_kw")) and features.get("has_modality_kw"):
        if not features.get("has_medical_term"):
            scores["STRUCTURED"] += W_MODALITY

    # ── Default fallback: SEMANTIC (core use case) ───
    if all(v == 0.0 for v in scores.values()):
        scores["SEMANTIC"] = DEFAULT_SEMANTIC_SCORE

    logger.debug(f"Intent scores: {scores} | features: {features}")
    return scores


# ============================================================
# Step 3: select_intent()
# ============================================================

def select_intent(
    scores: Dict[str, float],
    features: Dict[str, object],
) -> Tuple[str, float, dict]:
    """Chọn intent dựa trên scores.

    Pattern từ RAGCHATBOTV2 select_strategies()
    """
    # Sort by score descending
    sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_intent = sorted_intents[0][0]
    best_score = sorted_intents[0][1]
    second_score = sorted_intents[1][1] if len(sorted_intents) > 1 else 0.0
    gap = best_score - second_score

    debug_info = {
        "scores": {k: round(v, 4) for k, v in scores.items()},
        "gap": round(gap, 4),
        "features": {k: v for k, v in features.items() if v and k != "query_length" and k != "word_count"},
        "method": "multi_signal_scoring",
    }

    # HYBRID: chỉ khi 2 intent cao VÀ gap rất nhỏ (không phải PATIENT_LOOKUP)
    if best_intent != "PATIENT_LOOKUP" and \
       best_score > HYBRID_MIN_SCORE and \
       second_score > HYBRID_MIN_SCORE and \
       gap < HYBRID_MAX_GAP:
        if sorted_intents[1][0] != "PATIENT_LOOKUP":
            logger.info(
                f"[Router] HYBRID triggered: {sorted_intents[0]} vs {sorted_intents[1]} (gap={gap:.2f})"
            )
            return "HYBRID", best_score, debug_info

    # Default fallback khi score quá thấp → SEMANTIC (core use case)
    if best_score < LOW_CONFIDENCE:
        logger.info(f"[Router] Low confidence ({best_score:.2f}) → default SEMANTIC")
        return "SEMANTIC", DEFAULT_SEMANTIC_SCORE, debug_info

    logger.info(
        f"[Router] → {best_intent} (score={best_score:.2f}, gap={gap:.2f})"
    )
    return best_intent, best_score, debug_info


# ============================================================
# classify() — public API (giữ nguyên interface)
# ============================================================

def classify(question: str) -> Tuple[str, float, dict]:
    """
    Phân loại câu hỏi bằng multi-signal scoring.

    Args:
        question: câu hỏi từ user

    Returns:
        (intent_type, confidence, debug_info)
    """
    features = extract_query_features(question)
    scores = compute_intent_scores(features)
    return select_intent(scores, features)
