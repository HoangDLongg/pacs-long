"""Debug: dump scores + features cho từng case HYBRID trong gold."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from core.query_router import (
    extract_query_features,
    compute_intent_scores,
    select_intent,
    HYBRID_MIN_SCORE,
    HYBRID_MAX_GAP,
)

GOLD = Path(__file__).resolve().parents[1] / "data" / "router_gold.jsonl"

print(f"HYBRID rule: best > {HYBRID_MIN_SCORE} AND second > {HYBRID_MIN_SCORE} AND gap < {HYBRID_MAX_GAP}\n")
print(f"{'ID':<6}{'Query':<55}{'Got':<14}{'PL':>5}{'STR':>6}{'SEM':>6}{'gap':>6}  why_fail")
print("-" * 130)

with open(GOLD, encoding="utf-8") as f:
    for line in f:
        item = json.loads(line)
        if item["expected_intent"] != "HYBRID":
            continue
        q = item["question"]
        feats = extract_query_features(q)
        scores = compute_intent_scores(feats)
        got, conf, dbg = select_intent(scores, feats)
        pl = scores["PATIENT_LOOKUP"]
        st = scores["STRUCTURED"]
        sm = scores["SEMANTIC"]
        sorted_s = sorted(scores.values(), reverse=True)
        gap = sorted_s[0] - sorted_s[1]

        why = []
        if sorted_s[0] <= HYBRID_MIN_SCORE:
            why.append(f"best({sorted_s[0]:.2f})<={HYBRID_MIN_SCORE}")
        if sorted_s[1] <= HYBRID_MIN_SCORE:
            why.append(f"second({sorted_s[1]:.2f})<={HYBRID_MIN_SCORE}")
        if gap >= HYBRID_MAX_GAP:
            why.append(f"gap({gap:.2f})>={HYBRID_MAX_GAP}")
        why_str = ", ".join(why) if got != "HYBRID" else "OK"

        flag = "✓" if got == "HYBRID" else "✗"
        print(f"{item['id']:<6}{q[:53]:<55}{got+' '+flag:<14}{pl:>5.2f}{st:>6.2f}{sm:>6.2f}{gap:>6.2f}  {why_str}")
