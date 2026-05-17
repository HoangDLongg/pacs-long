"""Test router với 50 real-world cases."""
import sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, '.')

from core.query_router import classify

data = json.load(open('scripts/realworld_test.json', 'r', encoding='utf-8'))

correct = 0
errors = []
for c in data:
    intent, conf, debug = classify(c['query'])
    ok = intent == c['expected']
    if ok:
        correct += 1
    else:
        errors.append(c | {"predicted": intent, "conf": conf, "scores": debug["scores"]})

print(f"=== Real-world Test: {correct}/{len(data)} ({correct/len(data)*100:.1f}%) ===\n")

if errors:
    print(f"--- {len(errors)} errors ---")
    for e in errors:
        print(f"  [{e['predicted']}] '{e['query']}'")
        print(f"    Expected: {e['expected']} | Scores: {e['scores']}")
        print()
else:
    print("ALL PASSED!")
