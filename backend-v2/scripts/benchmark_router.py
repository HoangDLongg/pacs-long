"""
benchmark_router.py — Benchmark Query Router accuracy
Doc test cases tu scripts/test_queries.json
Chay: python scripts/benchmark_router.py
"""

import sys, os, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.query_router import classify

# Load test cases from JSON
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
JSON_PATH = os.path.join(SCRIPT_DIR, "..", "..", "dataset", "datatest.json")

def load_test_cases():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        groups = json.load(f)
    cases = []
    for group in groups:
        for c in group["cases"]:
            cases.append((c["query"], c["expected"], group["group"]))
    return cases

def run():
    test_cases = load_test_cases()
    print("=" * 70)
    print("BENCHMARK: Query Router Accuracy")
    print(f"Test file: {JSON_PATH}")
    print("=" * 70)
    print(f"Total test cases: {len(test_cases)}\n")

    correct = 0
    wrong = []
    results_by_intent = {}
    results_by_group = {}

    for query, expected, group in test_cases:
        predicted, confidence, debug = classify(query)

        is_correct = predicted == expected
        if is_correct:
            correct += 1
        else:
            wrong.append({
                "query": query,
                "expected": expected,
                "predicted": predicted,
                "confidence": round(confidence, 4),
                "group": group,
                "scores": debug.get("scores", {}),
            })

        # Per-intent
        if expected not in results_by_intent:
            results_by_intent[expected] = {"total": 0, "correct": 0}
        results_by_intent[expected]["total"] += 1
        if is_correct:
            results_by_intent[expected]["correct"] += 1

        # Per-group
        if group not in results_by_group:
            results_by_group[group] = {"total": 0, "correct": 0}
        results_by_group[group]["total"] += 1
        if is_correct:
            results_by_group[group]["correct"] += 1

        status = "OK" if is_correct else "XX"
        print(f"  {status} [{confidence:.2f}] {query[:50]:<50} -> {predicted:<16} (exp: {expected})")

    # Summary
    total = len(test_cases)
    accuracy = correct / total * 100

    print(f"\n{'='*70}")
    print(f"OVERALL ACCURACY: {correct}/{total} = {accuracy:.1f}%")
    print(f"{'='*70}")

    print("\nPer-intent accuracy:")
    for intent, stats in sorted(results_by_intent.items()):
        acc = stats["correct"] / stats["total"] * 100
        bar = "#" * int(acc / 5) + "." * (20 - int(acc / 5))
        print(f"  {intent:<20} {stats['correct']:>3}/{stats['total']:<3} = {acc:>5.1f}% [{bar}]")

    print(f"\nPer-group accuracy:")
    for group, stats in results_by_group.items():
        acc = stats["correct"] / stats["total"] * 100
        print(f"  {acc:>5.1f}% ({stats['correct']}/{stats['total']})  {group}")

    if wrong:
        print(f"\n{'='*70}")
        print(f"WRONG PREDICTIONS ({len(wrong)}):")
        print(f"{'='*70}")
        for w in wrong:
            print(f"\n  Query:     {w['query']}")
            print(f"  Group:     {w['group']}")
            print(f"  Expected:  {w['expected']}")
            print(f"  Predicted: {w['predicted']} (conf={w['confidence']})")
            scores = w['scores']
            print(f"  Scores:    {', '.join(f'{k}={v:.3f}' for k,v in sorted(scores.items(), key=lambda x:-x[1]))}")

    # Confusion matrix
    intents = sorted(set(e for _, e, _ in test_cases))
    all_predicted = intents + (["HYBRID"] if "HYBRID" not in intents else [])
    matrix = {e: {p: 0 for p in all_predicted} for e in intents}

    for query, expected, _ in test_cases:
        predicted, _, _ = classify(query)
        if predicted not in matrix[expected]:
            matrix[expected][predicted] = 0
        matrix[expected][predicted] += 1

    print(f"\n{'='*70}")
    print("CONFUSION MATRIX:")
    print(f"{'='*70}")
    header = f"{'Actual':<20}" + "".join(f"{p:<18}" for p in all_predicted)
    print(header)
    print("-" * len(header))
    for actual in intents:
        row = f"{actual:<20}" + "".join(f"{matrix[actual].get(p, 0):<18}" for p in all_predicted)
        print(row)

    print(f"\n{'='*70}")
    if accuracy >= 90:
        print(f"GOOD — Router accuracy {accuracy:.1f}% (>= 90%)")
    elif accuracy >= 75:
        print(f"WARNING — Router accuracy {accuracy:.1f}% (75-90%, can cai thien)")
    else:
        print(f"BAD — Router accuracy {accuracy:.1f}% (< 75%, can refactor)")

    return accuracy

if __name__ == "__main__":
    run()
