"""
tests/test_router_gold.py — Regression test trên router_gold.jsonl

Mục đích:
  - Bắt regression khi đụng vào query_router.py.
  - Threshold đặt theo baseline 2026-05-19 trừ buffer.
  - HYBRID hiện yếu (~10%) → có threshold riêng, sẽ siết khi tune
    router ở Phase 1.2–1.5.

Cách xem chi tiết mismatch:
    cd backend-v2
    python -m tests.benchmark.run_router_eval
"""

import pytest

from tests.benchmark.run_router_eval import evaluate, format_report, load_gold

# ============================================================
# Thresholds — phải >= mức này để CI xanh.
# Baseline đo 2026-05-19 (phase-1-intelligence, 74 câu).
# ============================================================
MIN_OVERALL_ACCURACY = 0.75
MIN_PER_INTENT = {
    "PATIENT_LOOKUP": 0.85,
    "STRUCTURED": 0.75,
    "SEMANTIC": 0.90,
    # HYBRID: chưa đặt threshold cứng — còn yếu, sẽ tune cùng 1.2-1.5.
}


@pytest.fixture(scope="module")
def stats():
    return evaluate(load_gold())


def test_overall_accuracy_above_threshold(stats):
    assert stats["accuracy"] >= MIN_OVERALL_ACCURACY, (
        f"Router accuracy {stats['accuracy'] * 100:.1f}% < "
        f"threshold {MIN_OVERALL_ACCURACY * 100:.0f}%.\n\n"
        + format_report(stats)
    )


@pytest.mark.parametrize("intent,threshold", list(MIN_PER_INTENT.items()))
def test_per_intent_accuracy(stats, intent, threshold):
    acc = stats["per_intent_accuracy"].get(intent, 0.0)
    assert acc >= threshold, (
        f"{intent} accuracy {acc * 100:.1f}% < threshold {threshold * 100:.0f}%"
    )


def test_dataset_loaded(stats):
    """Sanity check: gold dataset không bị rỗng / parse hỏng."""
    assert stats["total"] >= 50, "Gold set quá nhỏ — kiểm tra router_gold.jsonl"
    for intent in ["PATIENT_LOOKUP", "STRUCTURED", "SEMANTIC", "HYBRID"]:
        assert stats["per_intent_total"].get(intent, 0) > 0, (
            f"Gold set thiếu câu intent {intent}"
        )
