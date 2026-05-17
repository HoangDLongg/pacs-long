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
"""

import re
import logging
from typing import Tuple, Dict

logger = logging.getLogger(__name__)


# ============================================================
# Abbreviation expansion
# ============================================================

ABBREV_MAP = {
    'tk': 'thống kê', 'ds': 'danh sách', 'sl': 'số lượng',
    'bs': 'bác sĩ', 'bc': 'báo cáo', 'bn': 'bệnh nhân',
    'hn': 'hôm nay', 'hq': 'hôm qua',
}


def _expand_abbrev(text: str) -> str:
    """Mở rộng viết tắt VN phổ biến.
    Chỉ expand cho scoring, KHÔNG dùng cho name detection."""
    words = text.lower().split()
    expanded = [ABBREV_MAP.get(w, w) for w in words]
    return ' '.join(expanded)


# ============================================================
# Feature: PATIENT_LOOKUP
# ============================================================

# Họ Việt Nam phổ biến (không dấu + có dấu)
_VN_SURNAMES = frozenset({
    'nguyen', 'tran', 'le', 'pham', 'huynh', 'hoang', 'phan', 'vu',
    'vo', 'dang', 'bui', 'do', 'ho', 'ngo', 'duong', 'ly', 'cao',
    'luong', 'trinh', 'to', 'dinh', 'mai', 'truong', 'lam', 'ta',
    'dam', 'ha', 'la', 'tong', 'doan', 'van',
    # Có dấu
    'nguyễn', 'trần', 'lê', 'phạm', 'huỳnh', 'hoàng', 'phan', 'vũ',
    'võ', 'đặng', 'bùi', 'đỗ', 'hồ', 'ngô', 'dương', 'lý', 'cao',
    'lương', 'trịnh', 'tô', 'đinh', 'mai', 'trương', 'lâm', 'tạ',
    'đàm', 'hà', 'la', 'tống', 'đoàn', 'văn',
})

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

# VN name initials pattern: L.T.H, P.V.D, N.A
_NAME_INITIALS = re.compile(r'^(?:BN\s+|B/N\s+|B\.N\s+|bn\s+)?[A-Z]\.[A-Z](?:\.[A-Z])*$')


# Tên đệm / tên lót VN phổ biến (dùng để detect tên 2 từ không có họ)
_VN_MIDDLE_NAMES = frozenset({
    'văn', 'thị', 'hữu', 'đức', 'minh', 'quang', 'công', 'tiến',
    'xuân', 'thu', 'thanh', 'bá', 'tấn', 'thái', 'quốc', 'phúc',
    'bảo', 'ngọc', 'hoàng', 'đình', 'la', 'tất', 'lương', 'anh',
})

# Tên VN phổ biến (dùng khi chỉ có 2 từ)
_VN_GIVEN_NAMES = frozenset({
    'hải', 'trang', 'đạt', 'ngọc', 'phong', 'nghĩa', 'đức', 'linh',
    'sơn', 'mai', 'hương', 'thắng', 'thảo', 'hà', 'bích', 'nam',
    'trâm', 'long', 'hùng', 'dũng', 'lan', 'hoa', 'thủy', 'tuấn',
    'minh', 'anh', 'phương', 'thành', 'quân', 'khoa', 'hiếu',
    # Thêm từ round 3 errors
    'khang', 'trúc', 'nở', 'nguyệt', 'hậu', 'châu', 'phúc', 'hinh',
    'kiên', 'tâm', 'lộc', 'thịnh', 'cường', 'việt', 'hạnh', 'yến',
    'uyên', 'tuyết', 'xuân', 'thư', 'an', 'bình', 'cúc', 'dương',
    'giang', 'hưng', 'khánh', 'lâm', 'nhân', 'phát', 'quý',
    'thương', 'tiến', 'trọng', 'văn', 'viên', 'vũ', 'xâm',
})


def _detect_vn_name(text: str) -> bool:
    """Kiểm tra text có chứa tên người Việt không."""
    # Bỏ prefix tìm kiếm
    clean = _NAME_PREFIXES.sub('', text).strip()
    # Bỏ BN prefix
    clean = _BN_PREFIX.sub('', clean).strip()
    # Bỏ thêm context keywords (số điện thoại, ngày sinh, lịch sử, thông tin...)
    clean = re.sub(
        r'(?:số điện thoại|sđt|ngày sinh|thông tin liên hệ|thông tin chi tiết|'
        r'lịch sử khám|lịch sử bệnh nhân|lịch sử ca chụp|'
        r'đã chụp|chụp gì|có bao nhiêu|có mấy|danh sách|trạng thái|'
        r'có ca|báo cáo|tháng|tuần|hôm nay|hôm qua|ngày|từ đầu năm|7 ngày qua|'
        r'chụp CT|chụp MR|chụp CR|chụp US|chụp DX|chụp MG|'
        r'ca pending|ca reported|ca verified|'
        r'chưa|không|nào|gì|khi nào|của)\s*',
        ' ', clean, flags=re.IGNORECASE
    ).strip()
    clean = re.sub(r'\s+', ' ', clean).strip()

    parts = clean.split()
    if len(parts) < 2 or len(parts) > 6:
        return False

    # Loại trừ: nếu toàn bộ là structured/generic keywords
    struct_words = {'ca', 'danh', 'sách', 'liệt', 'kê', 'tổng', 'số', 'lượng',
                    'thống', 'báo', 'cáo', 'pending', 'verified', 'reported',
                    'studies', 'hôm', 'nay', 'qua', 'tuần', 'tháng', 'nam', 'nữ',
                    'bệnh', 'nhân', 'mấy', 'bao', 'nhiêu', 'tất', 'cả',
                    'cho', 'xem', 'tôi', 'biết', 'đã', 'đến', 'khám',
                    'show', 'list', 'all', 'the', 'hiển', 'thị', 'vui', 'lòng'}
    if all(p.lower() in struct_words for p in parts):
        return False

    first = parts[0].lower()

    # Họ VN đứng đầu
    if first in _VN_SURNAMES:
        return True

    # Tên 2 từ (không có họ): kiểm tra tên đệm + tên
    if len(parts) == 2:
        p0 = parts[0].lower()
        p1 = parts[1].lower()
        if (p0 in _VN_MIDDLE_NAMES and p1 in _VN_GIVEN_NAMES) or \
           (p0 in _VN_GIVEN_NAMES and p1 in _VN_GIVEN_NAMES):
            # Phải viết hoa
            if parts[0][0].isupper() and parts[1][0].isupper():
                return True

    # Mỗi từ viết hoa (Nguyen Van A pattern) - 3+ từ
    if len(parts) >= 3 and all(p[0].isupper() for p in parts if p):
        # Loại trừ nếu toàn bộ là medical terms
        medical_check = clean.lower()
        medical_exclude = {'viêm', 'tràn', 'gãy', 'u ', 'sỏi', 'hẹp', 'xẹp',
                          'nhồi máu', 'di căn', 'xuất huyết', 'tổn thương'}
        if any(m in medical_check for m in medical_exclude):
            return False
        return True

    return False


# ============================================================
# Feature: STRUCTURED keywords
# ============================================================

_COUNTING_KW = frozenset({
    'bao nhiêu', 'bao nhiu', 'mấy', 'may', 'đếm', 'dem', 'tổng', 'tong',
    'số lượng', 'so luong', 'count', 'how many', 'total',
    'tổng số', 'tong so', 'tổng cộng', 'tong cong',
})

_LISTING_KW = frozenset({
    'danh sách', 'danh sach', 'liệt kê', 'liet ke',
    'cho xem', 'cho tôi xem', 'show', 'list', 'hiển thị', 'hien thi',
    'ca nào', 'ca nao', 'những ca', 'nhung ca', 'các ca', 'cac ca',
})

_STATS_KW = frozenset({
    'thống kê', 'thong ke', 'tỷ lệ', 'ty le',
    'phân bố', 'phan bo', 'biểu đồ', 'bieu do',
    'so sánh', 'so sanh', 'phân tích', 'phan tich',
    'statistics', 'chart', 'graph',
})

_STATUS_KW = frozenset({
    'pending', 'reported', 'verified',
    'chưa đọc', 'chua doc', 'đã đọc', 'da doc',
    'đã báo cáo', 'da bao cao', 'đã xác nhận', 'da xac nhan',
    'chưa báo cáo', 'chua bao cao',
})

_MODALITY_TERMS = frozenset({'CT', 'MR', 'MRI', 'CR', 'US', 'DX', 'MG'})

_TIME_KW = frozenset({
    'hôm nay', 'hom nay', 'hôm qua', 'hom qua',
    'tuần này', 'tuan nay', 'tuần trước', 'tuan truoc',
    'tháng này', 'thang nay', 'tháng trước', 'thang truoc',
    'từ đầu năm', 'tu dau nam', '7 ngày qua', '7 ngay qua',
    'today', 'this week', 'this month', 'yesterday',
})

_DOCTOR_KW = re.compile(
    r'(?:bác sĩ|bac si|BS|bs|doctor|dr\.?)\s+\w+',
    re.IGNORECASE
)


# ============================================================
# Feature: SEMANTIC (medical terms)
# ============================================================

_MEDICAL_TERMS_VN = frozenset({
    # Phổi
    'viêm phổi', 'tràn dịch', 'tràn khí', 'xẹp phổi', 'u phổi',
    'nốt mờ', 'đông đặc', 'giãn phế quản', 'lao phổi', 'phù phổi',
    'khí phế thũng', 'xơ phổi', 'áp xe phổi', 'nấm phổi',
    'nhồi máu phổi', 'bụi phổi', 'nang phổi', 'kén khí',
    'viêm phế quản', 'hạch rốn phổi', 'COPD', 'ARDS',
    'tổn thương phổi', 'tổn thương kẽ', 'vôi hóa nhu mô',
    'dày màng phổi', 'tràn dịch màng phổi', 'tràn dịch rãnh',
    'dấu hiệu bóng mờ', 'dấu hiệu viền halo',
    'dấu hiệu lát đá', 'dấu hiệu cành cây',
    'nốt vôi hóa', 'mờ kính', 'kính mờ', 'kính chướng',
    # Tim mạch
    'vôi hóa', 'phình', 'hẹp van', 'suy tim', 'nhồi máu',
    'bóng tim to', 'tràn dịch màng tim', 'phình động mạch',
    'hẹp động mạch', 'hẹp eo', 'viêm cơ tim', 'ép tim',
    'giãn gốc', 'còn ống', 'tứ chứng', 'nhồi máu cơ tim',
    # Xương khớp
    'gãy xương', 'gãy cổ', 'gãy mâm', 'gãy đầu dưới',
    'thoát vị', 'loãng xương', 'thoái hóa', 'trật khớp',
    'viêm khớp', 'xẹp đốt sống', 'trượt đốt sống',
    'viêm cột sống', 'u xương', 'sarcoma', 'di căn xương',
    'viêm xương', 'nang xương', 'đứt dây chằng', 'rách sụn',
    'gãy xương đòn', 'hoại tử vô khuẩn', 'gout', 'gai xương',
    'hẹp ống sống', 'gãy xương chậu', 'vỡ xương sọ',
    'chấn thương cột sống', 'vẹo cột sống',
    # Gan / ổ bụng
    'u gan', 'HCC', 'sỏi túi mật', 'viêm tụy', 'gan nhiễm mỡ',
    'u nang', 'tắc ruột', 'áp xe gan', 'lách to', 'xơ gan',
    'u máu', 'đường mật', 'sỏi ống mật', 'viêm túi mật',
    'polyp túi mật', 'ung thư đường mật', 'di căn gan', 'nang gan',
    'cholangiocarcinoma', 'tràn dịch ổ bụng', 'lồng ruột',
    # Não / thần kinh
    'xuất huyết não', 'u não', 'teo não', 'phù não',
    'nhồi máu não', 'não úng thủy', 'u tuyến yên',
    'dị dạng mạch', 'viêm màng não', 'áp xe não',
    'máu tụ ngoài màng cứng', 'máu tụ dưới màng cứng',
    'tụ dịch dưới màng cứng', 'thoát vị não',
    # Vú / tuyến
    'BI-RADS', 'BIRADS', 'u xơ tuyến vú', 'u vú',
    'nang vú', 'vôi hóa vi thể', 'ung thư vú',
    'u xơ tử cung',
    # Thận / tiết niệu
    'sỏi thận', 'u bàng quang', 'ứ nước thận',
    'hẹp niệu quản', 'sỏi niệu quản', 'thận ứ nước',
    # Chung
    'tổn thương', 'di căn', 'ung thư', 'u ác tính',
    'u lành tính', 'viêm', 'áp xe', 'nang', 'sỏi',
    'xuất huyết', 'hoại tử',
})

_MEDICAL_TERMS_EN = frozenset({
    'pneumonia', 'pleural effusion', 'lung nodule', 'fracture',
    'hepatocellular carcinoma', 'brain tumor', 'stroke',
    'pulmonary embolism', 'aortic aneurysm', 'subdural hematoma',
    'breast cancer', 'kidney stone', 'appendicitis', 'liver cirrhosis',
    'pancreatitis', 'osteoporosis', 'disc herniation', 'hydrocephalus',
    'cholecystitis', 'ovarian cyst', 'tuberculosis',
})

_ANATOMY_TERMS = frozenset({
    'phổi', 'gan', 'não', 'tim', 'xương', 'thận', 'vú', 'tuyến',
    'mạch', 'ruột', 'tụy', 'lách', 'bàng quang', 'tử cung',
    'cột sống', 'khớp', 'đầu', 'ngực', 'bụng', 'chậu',
    'sọ', 'cổ', 'vai', 'háng', 'gối', 'mắt',
    'lung', 'liver', 'brain', 'heart', 'bone', 'kidney', 'breast',
})

_SIMILAR_KW = frozenset({
    'tương tự', 'tuong tu', 'giống', 'giong',
    'tìm ca', 'tim ca', 'ca nào giống', 'trường hợp tương tự',
    'ca tương tự', 'những ca giống', 'báo cáo tương tự',
    'báo cáo nào giống', 'trường hợp giống',
})


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

    Additive scoring — pattern từ RAGCHATBOTV2 strategy_router.py
    """
    scores = {"PATIENT_LOOKUP": 0.0, "STRUCTURED": 0.0, "SEMANTIC": 0.0}

    # ── PATIENT_LOOKUP boosters ──────────────────────
    if features.get("has_vn_name"):
        scores["PATIENT_LOOKUP"] += 0.8
    if features.get("has_patient_id"):
        scores["PATIENT_LOOKUP"] += 0.9
    if features.get("has_bn_prefix"):
        scores["PATIENT_LOOKUP"] += 0.6
    if features.get("has_name_initials"):
        scores["PATIENT_LOOKUP"] += 0.7

    # ── STRUCTURED boosters ──────────────────────────
    if features.get("has_counting_kw"):
        scores["STRUCTURED"] += 0.7
    if features.get("has_listing_kw"):
        scores["STRUCTURED"] += 0.6
    if features.get("has_stats_kw"):
        scores["STRUCTURED"] += 0.7
    if features.get("has_status_kw"):
        scores["STRUCTURED"] += 0.5
    if features.get("has_time_kw"):
        scores["STRUCTURED"] += 0.3
    if features.get("has_modality_kw") and not features.get("has_medical_term"):
        scores["STRUCTURED"] += 0.2
    if features.get("has_doctor_ref"):
        scores["STRUCTURED"] += 0.4
    if features.get("has_case_ref"):
        scores["STRUCTURED"] += 0.6

    # ── SEMANTIC boosters ────────────────────────────
    if features.get("has_medical_term"):
        scores["SEMANTIC"] += 0.7
    if features.get("has_medical_en"):
        scores["SEMANTIC"] += 0.6
    if features.get("has_similar_kw"):
        scores["SEMANTIC"] += 0.5
    if features.get("has_anatomy_term"):
        scores["SEMANTIC"] += 0.3
    if features.get("has_diagnosis_kw"):
        scores["SEMANTIC"] += 0.3

    # ── Cross-intent interactions ────────────────────

    # Tên người thật (has_vn_name) + bất kỳ context → vẫn PATIENT_LOOKUP
    # CHỈ khi has_vn_name=True (có tên thật), KHÔNG phải chỉ từ 'bệnh nhân' generic
    if features.get("has_vn_name"):
        scores["PATIENT_LOOKUP"] += 0.3
        scores["STRUCTURED"] = max(0, scores["STRUCTURED"] - 0.5)
        scores["SEMANTIC"] = max(0, scores["SEMANTIC"] - 0.3)

    # Modality + medical → SEMANTIC (VD: "CT phổi" = tìm ca CT về phổi)
    if features.get("has_modality_kw") and features.get("has_medical_term"):
        scores["SEMANTIC"] += 0.2

    # Stats/counting + modality (không có medical) → STRUCTURED
    if (features.get("has_counting_kw") or features.get("has_stats_kw")) and features.get("has_modality_kw"):
        if not features.get("has_medical_term"):
            scores["STRUCTURED"] += 0.2

    # ── Default fallback: SEMANTIC (core use case) ───
    if all(v == 0.0 for v in scores.values()):
        scores["SEMANTIC"] = 0.3

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
    if best_intent != "PATIENT_LOOKUP" and best_score > 0.5 and second_score > 0.5 and gap < 0.15:
        # Nhưng nếu PATIENT_LOOKUP là 1 trong 2 → không HYBRID
        if sorted_intents[1][0] != "PATIENT_LOOKUP":
            logger.info(
                f"[Router] HYBRID triggered: {sorted_intents[0]} vs {sorted_intents[1]} (gap={gap:.2f})"
            )
            return "HYBRID", best_score, debug_info

    # Default fallback khi score quá thấp → SEMANTIC (core use case)
    if best_score < 0.3:
        logger.info(f"[Router] Low confidence ({best_score:.2f}) → default SEMANTIC")
        return "SEMANTIC", 0.3, debug_info

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
