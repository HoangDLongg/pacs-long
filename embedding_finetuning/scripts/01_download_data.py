"""
01_download_data.py — Tải Vietnamese Medical QA từ HuggingFace
Output: data/training_pairs_medical.json (≥7000 pairs)

Usage:
  python scripts/01_download_data.py
"""

import json
import os
import random
from datasets import load_dataset

random.seed(42)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

print("=" * 60)
print("  Download Vietnamese Medical QA from HuggingFace")
print("=" * 60)

ds = load_dataset("hungnm/vietnamese-medical-qa", split="train")
print(f"Downloaded: {len(ds)} QA pairs")

# Filter và convert
pairs = []
for item in ds:
    q = item["question"].strip()
    a = item["answer"].strip()
    if 10 < len(q) < 500 and 20 < len(a) < 1000:
        pairs.append({"text1": q, "text2": a[:500]})

random.shuffle(pairs)
print(f"After filter: {len(pairs)} pairs")

# Save
output = os.path.join(DATA_DIR, "training_pairs_medical.json")
with open(output, "w", encoding="utf-8") as f:
    json.dump(pairs, f, ensure_ascii=False, indent=2)

print(f"SAVED: {output}")
print(f"Size: {os.path.getsize(output) / 1024 / 1024:.1f} MB")
