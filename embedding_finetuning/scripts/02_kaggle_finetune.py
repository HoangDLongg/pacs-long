"""
02_kaggle_finetune.py — LoRA Fine-tune BGE-M3 cho PACS++
Chạy trên Kaggle GPU T4 (16GB VRAM)

Setup:
  1. Kaggle → New Notebook → GPU T4 x2
  2. Cell đầu tiên:
     !pip install -q sentence-transformers datasets peft
  3. Paste code này → Run All (~15-20 phút)
"""

# ============================================================
# !pip install -q sentence-transformers datasets peft
# ============================================================

import json
import time
import random
import numpy as np
from datasets import load_dataset
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

random.seed(42)

# ============================================================
# CONFIG
# ============================================================
BASE_MODEL = "BAAI/bge-m3"          # Best multilingual embedding
BATCH_SIZE = 32                      # T4 handles 32 easily with LoRA
EPOCHS = 3
WARMUP_RATIO = 0.1
LORA_R = 16                         # LoRA rank
LORA_ALPHA = 32                     # LoRA alpha
LORA_DROPOUT = 0.1
OUTPUT_PATH = "/kaggle/working/bge-m3-medical-lora"

# ============================================================
# STEP 1: Download Vietnamese Medical QA
# ============================================================
print("=" * 60)
print("  STEP 1: Download data (hungnm/vietnamese-medical-qa)")
print("=" * 60)

ds = load_dataset("hungnm/vietnamese-medical-qa", split="train")
print(f"Downloaded: {len(ds)} QA pairs")

# Collect raw QA pairs
raw_pairs = []
for item in ds:
    q = item["question"].strip()
    a = item["answer"].strip()
    if 10 < len(q) < 500 and 20 < len(a) < 1000:
        raw_pairs.append((q, a[:500]))

print(f"Valid QA pairs: {len(raw_pairs)}")

# Build ContrastiveLoss data: positive (label=1) + negative (label=0)
train_examples = []

# Positive pairs: question → correct answer (label=1)
for q, a in raw_pairs:
    train_examples.append(InputExample(texts=[q, a], label=1.0))

# Negative pairs: question → WRONG answer (label=0)
all_answers = [a for _, a in raw_pairs]
for q, correct_a in raw_pairs:
    wrong_a = random.choice(all_answers)
    while wrong_a == correct_a:
        wrong_a = random.choice(all_answers)
    train_examples.append(InputExample(texts=[q, wrong_a], label=0.0))

random.shuffle(train_examples)
print(f"Total pairs: {len(train_examples)} (50% positive, 50% negative)")

split_idx = int(len(train_examples) * 0.9)
train_data = train_examples[:split_idx]
eval_data = train_examples[split_idx:]
print(f"Train: {len(train_data)}, Eval: {len(eval_data)}")

# ============================================================
# STEP 2: Load model + Benchmark BEFORE
# ============================================================
print(f"\n{'=' * 60}")
print(f"  STEP 2: Load {BASE_MODEL} + Benchmark BEFORE")
print("=" * 60)

model = SentenceTransformer(BASE_MODEL)
print(f"Model: {BASE_MODEL}")
print(f"Embedding dim: {model.get_sentence_embedding_dimension()}")

# Medical benchmark queries
BENCH = [
    ("tổn thương phổi kẽ", "Phổi hai bên kém sáng mờ kính rải rác. Hình ảnh nghĩ nhiều đến tổn thương phổi kẽ."),
    ("bóng tim to trên phim ngực", "Bóng mờ tim to các cung tim rộng. Hình ảnh bóng tim to."),
    ("vôi hóa động mạch chủ", "Vôi hóa thành quai động mạch chủ. Phổi hai bên sáng đều."),
    ("ung thư gan HCC xơ gan", "Nốt giảm tỉ trọng thùy phải 35x30mm bắt thuốc mạnh. Nốt gan phải nghi HCC."),
    ("sỏi thận ứ nước", "Sỏi bể thận 18mm giãn đài bể thận. Sỏi bể thận phải kèm ứ nước độ II."),
    ("thoát vị đĩa đệm chèn ép rễ", "Thoát vị đĩa đệm L5-S1 chèn ép rễ S1 trái."),
    ("gãy lún đốt sống", "Giảm chiều cao thân đốt sống L1 gãy lún 40%."),
    ("u vú BI-RADS 5 ác tính", "Khối đặc bờ không đều 25x18mm. BI-RADS 5 rất nghi ngờ ác tính."),
    ("vi vôi hóa vú nghi ngờ", "Vi vôi hóa dạng đa hình. BI-RADS 4B nghi ngờ ác tính."),
    ("nang thận lành tính", "Nang đơn thuần thận trái 22mm. Bosniak I."),
    ("tràn dịch màng phổi", "Mờ tù góc sườn hoành phải. Tràn dịch màng phổi phải."),
    ("sỏi túi mật viêm mạn", "Sỏi túi mật 12mm thành dày. Sỏi túi mật kèm viêm mạn."),
]

NEGS = [
    "Gan bình thường nhu mô đồng nhất không bất thường.",
    "Phổi hai bên sáng đều bóng tim không to.",
    "Cong vẹo cột sống gai xương đa tầng.",
]


def benchmark(m):
    """Tính cosine similarity: positive vs negative"""
    pos, neg = [], []
    for q, p in BENCH:
        qe = m.encode([q], normalize_embeddings=True)[0]
        pe = m.encode([p], normalize_embeddings=True)[0]
        pos.append(float(np.dot(qe, pe)))
        for n in NEGS:
            ne = m.encode([n], normalize_embeddings=True)[0]
            neg.append(float(np.dot(qe, ne)))
    return {
        "pos": round(np.mean(pos), 4),
        "neg": round(np.mean(neg), 4),
        "margin": round(np.mean(pos) - np.mean(neg), 4),
        "details": [round(s, 4) for s in pos],
    }


before = benchmark(model)
print(f"  Positive sim: {before['pos']}")
print(f"  Negative sim: {before['neg']}")
print(f"  Margin:       {before['margin']}")

# ============================================================
# STEP 3: Setup LoRA
# ============================================================
print(f"\n{'=' * 60}")
print(f"  STEP 3: Setup LoRA (r={LORA_R}, alpha={LORA_ALPHA})")
print("=" * 60)

from peft import LoraConfig, get_peft_model, TaskType
import torch

# Get the transformer model inside SentenceTransformer
transformer = model[0]  # First module is the transformer
base_model = transformer.auto_model

# Count params before LoRA
total_params = sum(p.numel() for p in base_model.parameters())
print(f"  Base model params: {total_params:,}")

# Apply LoRA
lora_config = LoraConfig(
    task_type=TaskType.FEATURE_EXTRACTION,
    r=LORA_R,
    lora_alpha=LORA_ALPHA,
    lora_dropout=LORA_DROPOUT,
    target_modules=["query", "key", "value", "dense"],  # attention layers
    inference_mode=False,
)

base_model = get_peft_model(base_model, lora_config)
transformer.auto_model = base_model

trainable_params = sum(p.numel() for p in base_model.parameters() if p.requires_grad)
print(f"  Trainable params: {trainable_params:,} ({trainable_params/total_params*100:.2f}%)")
print(f"  Reduction: {total_params/trainable_params:.0f}x fewer params")

# ============================================================
# STEP 4: Fine-tune with LoRA
# ============================================================
print(f"\n{'=' * 60}")
print(f"  STEP 4: LoRA Fine-tuning ({len(train_data)} pairs, {EPOCHS} epochs)")
print("=" * 60)

loader = DataLoader(train_data, shuffle=True, batch_size=BATCH_SIZE)
loss_fn = losses.ContrastiveLoss(model=model)
warmup = int(len(loader) * EPOCHS * WARMUP_RATIO)

print(f"  Batches/epoch: {len(loader)}")
print(f"  Total steps: {len(loader) * EPOCHS}")
print(f"  Warmup: {warmup}")

t0 = time.time()
model.fit(
    train_objectives=[(loader, loss_fn)],
    epochs=EPOCHS,
    warmup_steps=warmup,
    output_path=OUTPUT_PATH,
    save_best_model=True,
    show_progress_bar=True,
    use_amp=True,
)
train_min = (time.time() - t0) / 60
print(f"\n  LoRA training done in {train_min:.1f} minutes")

# ============================================================
# STEP 5: Benchmark AFTER
# ============================================================
print(f"\n{'=' * 60}")
print("  STEP 5: Benchmark AFTER LoRA fine-tune")
print("=" * 60)

# Save and reload to test
model.save(OUTPUT_PATH)
model_ft = SentenceTransformer(OUTPUT_PATH)

after = benchmark(model_ft)
print(f"  Positive sim: {after['pos']}")
print(f"  Negative sim: {after['neg']}")
print(f"  Margin:       {after['margin']}")

# ============================================================
# STEP 6: Results
# ============================================================
print(f"\n{'=' * 60}")
print("  RESULTS: Before vs After LoRA Fine-tune")
print("=" * 60)
print(f"  Model: {BASE_MODEL}")
print(f"  LoRA: r={LORA_R}, alpha={LORA_ALPHA}")
print(f"  Data: {len(train_data)} medical QA pairs (Vietnamese)")
print(f"  Trainable: {trainable_params:,} / {total_params:,} params ({trainable_params/total_params*100:.2f}%)")
print()
print(f"{'Metric':<25} {'Before':>8} {'After':>8} {'Change':>8}")
print("-" * 50)
print(f"{'Positive Similarity':<25} {before['pos']:>8.4f} {after['pos']:>8.4f} {after['pos']-before['pos']:>+8.4f}")
print(f"{'Negative Similarity':<25} {before['neg']:>8.4f} {after['neg']:>8.4f} {after['neg']-before['neg']:>+8.4f}")
print(f"{'Margin':<25} {before['margin']:>8.4f} {after['margin']:>8.4f} {after['margin']-before['margin']:>+8.4f}")
print(f"{'Training Time':<25} {'':>8} {train_min:>7.1f}m")

print(f"\nPer-query positive similarity:")
print(f"{'Query':<40} {'Before':>8} {'After':>8} {'Δ':>8}")
print("-" * 65)
for i, (q, _) in enumerate(BENCH):
    b = before['details'][i]
    a = after['details'][i]
    marker = "↑" if a > b else ("↓" if a < b else "=")
    print(f"{q[:39]:<40} {b:>8.4f} {a:>8.4f} {a-b:>+7.4f} {marker}")

# Save results
results = {
    "base_model": BASE_MODEL,
    "method": "LoRA",
    "lora_r": LORA_R,
    "lora_alpha": LORA_ALPHA,
    "trainable_params": trainable_params,
    "total_params": total_params,
    "train_pairs": len(train_data),
    "epochs": EPOCHS,
    "train_min": round(train_min, 1),
    "before": before,
    "after": after,
    "improvement": {
        "pos": round(after['pos'] - before['pos'], 4),
        "neg": round(after['neg'] - before['neg'], 4),
        "margin": round(after['margin'] - before['margin'], 4),
    }
}

with open("/kaggle/working/finetune_results.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n{'=' * 60}")
print("  Model saved: /kaggle/working/bge-m3-medical-lora/")
print("  Results: /kaggle/working/finetune_results.json")
print("  → Download từ Output panel bên phải Kaggle")
print("=" * 60)
