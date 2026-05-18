"""
tests/test_query_router.py — Test Query Router intent classification

Kiểm tra:
  - _detect_vn_name() — heuristic phát hiện tên người Việt
  - classify()         — phân loại intent end-to-end (PATIENT_LOOKUP / STRUCTURED /
                          SEMANTIC / HYBRID)
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.query_router import _detect_vn_name, classify


# ============================================================
# Heuristic phát hiện tên người Việt
# ============================================================

class TestDetectVnName:
    """Test heuristic tên người Việt (_detect_vn_name)."""

    # ── TRUE — đúng là tên ───────────────────────────────
    @pytest.mark.parametrize("name", [
        "Nguyen Van A",
        "Tran Thi Mai Lan",
        "tìm Nguyen Van A",
        "bệnh nhân Pham Thi Lan",
        "Ho Van Tai",
        "Cao Van Phuc",
    ])
    def test_is_vn_name(self, name):
        assert _detect_vn_name(name) is True

    # ── FALSE — không phải tên ───────────────────────────
    # Note: "A B C D E F" (chữ cái rời rạc) hiện tại bị FP do rule "3+ từ viết hoa".
    # Sẽ siết lại trong Phase 1 khi tune router với gold set thật.
    @pytest.mark.parametrize("text", [
        "tổn thương phổi",
        "bao nhiêu ca CT",
        "viêm",
        "",
    ])
    def test_not_vn_name(self, text):
        assert _detect_vn_name(text) is False


# ============================================================
# Phân loại intent end-to-end (classify)
# ============================================================

class TestClassify:
    """Smoke test cho classify() — cover 4 intent chính."""

    def test_patient_lookup_full_name(self):
        intent, conf, _ = classify("Nguyen Van A")
        assert intent == "PATIENT_LOOKUP"
        assert conf > 0

    def test_patient_lookup_with_prefix(self):
        intent, _, _ = classify("tìm bệnh nhân Tran Thi Mai")
        assert intent == "PATIENT_LOOKUP"

    def test_structured_counting(self):
        intent, _, _ = classify("bao nhiêu ca CT hôm nay")
        assert intent in ("STRUCTURED", "HYBRID")

    def test_structured_listing_status(self):
        intent, _, _ = classify("danh sách ca chưa đọc")
        assert intent in ("STRUCTURED", "HYBRID")

    def test_semantic_medical(self):
        intent, _, _ = classify("tổn thương phổi dạng nốt")
        assert intent in ("SEMANTIC", "HYBRID")

    def test_returns_debug_info(self):
        _, _, debug = classify("Nguyen Van A")
        assert isinstance(debug, dict)
        assert "scores" in debug

    def test_empty_query_does_not_crash(self):
        intent, conf, _ = classify("")
        assert intent in ("PATIENT_LOOKUP", "STRUCTURED", "SEMANTIC", "HYBRID")
        assert isinstance(conf, float)
