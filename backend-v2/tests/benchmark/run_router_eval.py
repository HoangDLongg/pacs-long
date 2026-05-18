"""
tests/benchmark/run_router_eval.py
==================================

Chạy query_router.classify() trên bộ gold dataset và in báo cáo:
  - Overall accuracy
  - Per-intent precision / recall (macro view)
  - Confusion matrix
  - Danh sách câu fail

Cách chạy độc lập:
    cd backend-v2
    python -m tests.benchmark.run_router_eval

Cách dùng trong pytest: xem tests/test_router_gold.py.

Output: dict thống kê (cho test/CI dùng).
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Cho phép chạy cả từ backend-v2/ và từ thư mục con
_HERE = Path(__file__).resolve()
_BACKEND_ROOT = _HERE.parents[2]
sys.path.insert(0, str(_BACKEND_ROOT))

from core.query_router import classify  # noqa: E402

GOLD_PATH = _BACKEND_ROOT / "tests" / "data" / "router_gold.jsonl"

INTENT_ORDER = ["PATIENT_LOOKUP", "STRUCTURED", "SEMANTIC", "HYBRID"]


def load_gold(path: Path = GOLD_PATH) -> list[dict[str, Any]]:
    """Đọc JSONL gold dataset."""
    items: list[dict[str, Any]] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            items.append(json.loads(line))
    return items


def evaluate(gold: list[dict[str, Any]]) -> dict[str, Any]:
    """Chạy classify() trên gold, trả về thống kê."""
    total = len(gold)
    correct = 0
    per_intent_total: dict[str, int] = defaultdict(int)
    per_intent_correct: dict[str, int] = defaultdict(int)
    confusion: dict[tuple[str, str], int] = defaultdict(int)
    mismatches: list[dict[str, Any]] = []

    for item in gold:
        q = item["question"]
        expected = item["expected_intent"]
        predicted, conf, _ = classify(q)

        per_intent_total[expected] += 1
        confusion[(expected, predicted)] += 1

        if predicted == expected:
            correct += 1
            per_intent_correct[expected] += 1
        else:
            mismatches.append({
                "id": item.get("id"),
                "question": q,
                "expected": expected,
                "predicted": predicted,
                "confidence": round(conf, 3),
                "tags": item.get("tags", []),
            })

    accuracy = correct / total if total else 0.0

    per_intent_accuracy = {
        intent: (per_intent_correct[intent] / per_intent_total[intent]
                 if per_intent_total[intent] else 0.0)
        for intent in INTENT_ORDER
    }

    return {
        "total": total,
        "correct": correct,
        "accuracy": accuracy,
        "per_intent_total": dict(per_intent_total),
        "per_intent_accuracy": per_intent_accuracy,
        "confusion": {f"{e}->{p}": n for (e, p), n in confusion.items()},
        "mismatches": mismatches,
    }


def format_report(stats: dict[str, Any]) -> str:
    """Format thống kê thành text in CI/console."""
    lines: list[str] = []
    lines.append("=" * 60)
    lines.append("ROUTER GOLD EVALUATION")
    lines.append("=" * 60)
    lines.append(f"Total questions: {stats['total']}")
    lines.append(f"Correct:         {stats['correct']}")
    lines.append(f"Accuracy:        {stats['accuracy'] * 100:.1f}%")
    lines.append("")
    lines.append("Per-intent accuracy:")
    for intent in INTENT_ORDER:
        n_total = stats["per_intent_total"].get(intent, 0)
        acc = stats["per_intent_accuracy"].get(intent, 0.0)
        lines.append(f"  {intent:<16} {acc * 100:5.1f}%  ({n_total} questions)")
    lines.append("")
    lines.append("Confusion (expected -> predicted, count):")
    for k, v in sorted(stats["confusion"].items(), key=lambda x: -x[1]):
        marker = "  " if k.split("->")[0] == k.split("->")[1] else "* "
        lines.append(f"  {marker}{k:<40} {v}")
    lines.append("")
    if stats["mismatches"]:
        lines.append(f"Mismatches ({len(stats['mismatches'])}):")
        for m in stats["mismatches"]:
            lines.append(
                f"  [{m['id']}] '{m['question']}'"
                f"  expected={m['expected']}  got={m['predicted']}  conf={m['confidence']}"
            )
    else:
        lines.append("No mismatches.")
    lines.append("=" * 60)
    return "\n".join(lines)


def main() -> int:
    # Windows console mặc định cp1252 — force UTF-8 cho stdout/stderr
    # để in được tiếng Việt (Linux CI đã sẵn UTF-8).
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass

    gold = load_gold()
    stats = evaluate(gold)
    print(format_report(stats))
    return 0


if __name__ == "__main__":
    sys.exit(main())
