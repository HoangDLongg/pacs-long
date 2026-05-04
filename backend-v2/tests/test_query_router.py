"""
tests/test_query_router.py — Test Query Router intent classification
Kiểm tra phân loại câu hỏi → đúng intent
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.query_router import _looks_like_name


class TestLooksLikeName:
    """Test heuristic tên người Việt"""

    # ==================== TRUE — Tên người Việt ====================
    def test_simple_name(self):
        assert _looks_like_name("Nguyen Van A") is True

    def test_full_name(self):
        assert _looks_like_name("Tran Thi Mai Lan") is True

    def test_two_parts(self):
        assert _looks_like_name("Le Minh") is True

    def test_with_prefix_tim(self):
        assert _looks_like_name("tìm Nguyen Van A") is True

    def test_with_prefix_benh_nhan(self):
        assert _looks_like_name("bệnh nhân Pham Thi Lan") is True

    def test_surname_ho(self):
        assert _looks_like_name("Ho Van Tai") is True

    def test_surname_cao(self):
        assert _looks_like_name("Cao Van Phuc") is True

    # ==================== FALSE — Không phải tên ====================
    def test_medical_term(self):
        assert _looks_like_name("tổn thương phổi") is False

    def test_question_count(self):
        assert _looks_like_name("bao nhiêu ca CT") is False

    def test_single_word(self):
        assert _looks_like_name("viêm") is False

    def test_too_many_parts(self):
        assert _looks_like_name("A B C D E F") is False

    def test_lowercase(self):
        assert _looks_like_name("nguyen van a b c d") is False

    def test_empty(self):
        assert _looks_like_name("") is False
