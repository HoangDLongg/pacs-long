"""
core/query_router.py — Intent Classifier cho PACS++
Pattern từ 6805_intent_system: embedding-based classification

Thay vì regex đơn giản, dùng semantic similarity với example set
để phân loại câu hỏi → STRUCTURED (DDQ/SQL) hoặc SEMANTIC (RAG).

"Training data" = bộ examples được encode thành embeddings.
Khi query đến → encode → cosine similarity → intent có score cao nhất.
"""

import re
import numpy as np
import logging
from typing import Tuple

logger = logging.getLogger(__name__)


# ============================================================
# "Training" examples — giống 6805 examples_table
# Mỗi example gán vào 1 intent type
# ============================================================

INTENT_EXAMPLES = {
    "STRUCTURED": [
        # Đếm / thống kê
        "bao nhiêu ca CT hôm nay",
        "tổng số ca chụp tháng 3",
        "mấy ca chưa đọc",
        "thống kê theo modality",
        "tỷ lệ ca đã báo cáo",
        "đếm số bệnh nhân",
        "có bao nhiêu ca MR",
        "tổng cộng bao nhiều ca pending",
        # Danh sách / tra cứu
        "ca nào chưa đọc",
        "danh sách ca hôm nay",
        "liệt kê ca CT tuần này",
        "những ca chưa báo cáo",
        "cho tôi xem danh sách bệnh nhân",
        # Tra cứu entity (câu hỏi kèm tên)
        "bệnh nhân Nguyễn Văn A chụp gì",
        "ai chụp CT hôm qua",
        "bác sĩ Nam viết bao nhiêu báo cáo",
        "ca nào chụp ngày 15 tháng 3",
        # Status
        "ca số 123 trạng thái gì",
        "những ca đã verified",
        "ca reported hôm nay",
    ],
    "PATIENT_LOOKUP": [
        # Tên người (không có context y khoa — chỉ là tên)
        "Nguyen Van A",
        "Tran Thi Mai",
        "Le Hoang Minh",
        "Pham Thi Lan",
        "Ho Van Tai",
        "To Van Binh",
        "Cao Van Phuc",
        "Vu Thi Ha",
        "Ngo Van Thanh",
        "Duong Thi Lien",
        "Mai Thi Dung",
        "Luong Thi Yen",
        # Các pattern tìm kiếm theo tên
        "tìm bệnh nhân Nguyen Van A",
        "tra cứu bệnh nhân Tran Thi Mai",
        "tìm tên Pham Thi Lan",
        "bệnh nhân tên Le Hoang Minh",
        "hồ sơ bệnh nhân Ho Van Tai",
        "tìm hồ sơ Cao Van Phuc",
        # Mã bệnh nhân
        "bệnh nhân 10250",
        "mã bệnh nhân A000801",
        "patient ID 1781655154",
    ],
    "SEMANTIC": [
        # Triệu chứng / bệnh lý
        "tổn thương phổi dạng nốt đơn độc",
        "hình ảnh mờ kính rải rác hai phổi",
        "kết luận viêm phổi thùy dưới phải",
        "chẩn đoán u gan HCC",
        "dịch màng phổi hai bên",
        "vôi hóa thành quai động mạch chủ",
        "xẹp thùy dưới phổi trái",
        "gãy xương sườn bên phải",
        "thoát vị đĩa đệm cột sống thắt lưng",
        # Tìm ca tương tự
        "tìm báo cáo tương tự tổn thương phổi kẽ",
        "ca nào giống tràn dịch màng phổi",
        "trường hợp viêm phổi kèm bóng tim to",
        "tìm các ca có nốt mờ sát màng phổi",
        # Nội dung y khoa
        "BI-RADS 4 tuyến vú",
        "nhồi máu não cấp",
        "loãng xương cột sống",
        "hẹp động mạch vành",
        "di căn xương",
        "u phổi nghi ác tính",
        "COPD với tổn thương kẽ",
    ],
}


# ============================================================
# Embeddings cache — giống 6805 embeddings cache
# ============================================================

_router_cache = {
    "embeddings": None,    # np.array shape (N, 1024)
    "labels": None,        # list of intent types
    "examples": None,      # list of example texts
    "initialized": False,
    "version": 2,          # bump to force rebuild when examples change
}


def _build_cache():
    """Build embeddings cache cho examples (giống 6805 build_embeddings_cache)"""
    global _router_cache

    if _router_cache["initialized"]:
        return

    logger.info("[Router] Building intent examples cache...")

    from core.embeddings import EmbeddingModel

    all_texts = []
    all_labels = []

    for intent_type, examples in INTENT_EXAMPLES.items():
        for ex in examples:
            all_texts.append(ex)
            all_labels.append(intent_type)

    # Batch encode (giống 6805 model.encode batch)
    model = EmbeddingModel.get_model()
    # Dùng "query: " prefix vì đây là query examples
    prefixed = [f"query: {t}" for t in all_texts]
    embeddings = model.encode(prefixed, normalize_embeddings=True, batch_size=32)

    _router_cache["embeddings"] = np.array(embeddings)
    _router_cache["labels"] = all_labels
    _router_cache["examples"] = all_texts
    _router_cache["initialized"] = True

    logger.info(f"[Router] Cache built: {len(all_texts)} examples "
                f"(STRUCTURED={all_labels.count('STRUCTURED')}, SEMANTIC={all_labels.count('SEMANTIC')})")


# ============================================================
# classify() — semantic similarity (giống 6805 compute_similarity_with_cache)
# ============================================================

# ============================================================
# Regex-based name detector (fast pre-check)
# ============================================================

# Pattern: 2-4 Vietnamese name parts, mỗi từ bắt đầu bằng chữ hoa
# VD: "Nguyen Van A", "To Van Binh", "Pham Thi Lan"
_NAME_PATTERN = re.compile(
    r'^(?:tìm\s+)?(?:bệnh nhân\s+)?(?:tên\s+)?(?:hồ sơ\s+)?'
    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,4})\s*$',
    re.IGNORECASE
)

# Họ Việt Nam phổ biến (không dấu)
_VN_SURNAMES = {
    'nguyen', 'tran', 'le', 'pham', 'huynh', 'hoang', 'phan', 'vu',
    'vo', 'dang', 'bui', 'do', 'ho', 'ngo', 'duong', 'ly', 'cao',
    'luong', 'trinh', 'to', 'dinh', 'mai', 'truong', 'lam', 'ta',
    'dam', 'ha', 'la', 'tong', 'doan', 'van',
}


def _looks_like_name(text: str) -> bool:
    """Heuristic: kiểm tra xem text có giống tên người Việt không"""
    text = text.strip()
    # Bỏ prefix "tìm", "bệnh nhân", "tên", "hồ sơ"
    clean = re.sub(r'^(?:tìm|tim|benh nhan|bệnh nhân|tên|ten|hồ sơ|ho so)\s+', '', text, flags=re.IGNORECASE).strip()

    parts = clean.split()
    if len(parts) < 2 or len(parts) > 5:
        return False

    # Kiểm tra từ đầu tiên có phải họ Việt?
    first = parts[0].lower()
    if first in _VN_SURNAMES:
        return True

    # Kiểm tra pattern: mỗi từ bắt đầu bằng chữ hoa
    if all(p[0].isupper() for p in parts if p):
        return True

    return False


def classify(question: str) -> Tuple[str, float, dict]:
    """
    Phân loại câu hỏi bằng semantic similarity + heuristic.
    
    Intents:
        PATIENT_LOOKUP: tìm kiếm theo tên bệnh nhân
        STRUCTURED: câu hỏi thống kê, đếm, tra cứu → SQL
        SEMANTIC: tìm kiếm nội dung y khoa → RAG
        HYBRID: mập mờ giữa STRUCTURED và SEMANTIC → chạy cả 2

    Args:
        question: câu hỏi từ user

    Returns:
        (intent_type, confidence, debug_info)
    """
    # === Fast-path: regex name detection ===
    if _looks_like_name(question):
        logger.info(f"[Router] '{question[:40]}' → PATIENT_LOOKUP (name detected by heuristic)")
        return "PATIENT_LOOKUP", 0.95, {
            "scores": {"PATIENT_LOOKUP": 0.95},
            "method": "heuristic_name_detection",
            "gap": 0,
            "best_example": question,
            "top_match_score": 0.95,
            "top_match_idx": 0,
            "top_match_text": question,
        }

    # === Semantic similarity classification ===
    _build_cache()

    from core.embeddings import EmbeddingModel

    # Encode query (giống 6805 encode_query)
    model = EmbeddingModel.get_model()
    query_emb = model.encode(
        [f"query: {question}"],
        normalize_embeddings=True
    )[0]

    # Cosine similarity = dot product (vì normalized)
    scores = np.dot(_router_cache["embeddings"], query_emb)

    # Group by intent type, lấy MAX score
    intent_scores = {}
    best_examples = {}

    for i, (label, score) in enumerate(zip(_router_cache["labels"], scores)):
        if label not in intent_scores or score > intent_scores[label]:
            intent_scores[label] = float(score)
            best_examples[label] = _router_cache["examples"][i]

    # Winner
    best_intent = max(intent_scores, key=intent_scores.get)
    confidence = intent_scores[best_intent]

    # Nếu confidence quá thấp → khó phân loại
    if confidence < 0.5:
        best_intent = "PATIENT_LOOKUP"  # default fallback → tìm tên
        confidence = 0.3

    # Safety: nếu gap giữa STRUCTURED và SEMANTIC < 0.1 → HYBRID
    s_score = intent_scores.get("STRUCTURED", 0)
    r_score = intent_scores.get("SEMANTIC", 0)
    p_score = intent_scores.get("PATIENT_LOOKUP", 0)
    gap = abs(s_score - r_score)

    if best_intent not in ("PATIENT_LOOKUP",) and gap < 0.10:
        best_intent = "HYBRID"
        confidence = max(s_score, r_score)

    debug_info = {
        "scores": {k: round(v, 4) for k, v in intent_scores.items()},
        "gap": round(gap, 4),
        "best_example": best_examples.get(best_intent, best_examples.get(max(intent_scores, key=intent_scores.get), "")),
        "top_match_score": round(float(np.max(scores)), 4),
        "top_match_idx": int(np.argmax(scores)),
        "top_match_text": _router_cache["examples"][int(np.argmax(scores))],
    }

    logger.info(
        f"[Router] '{question[:40]}' → {best_intent} "
        f"(conf={confidence:.2f}, S={s_score:.2f}, R={r_score:.2f}, P={p_score:.2f}, gap={gap:.2f})"
    )

    return best_intent, confidence, debug_info

