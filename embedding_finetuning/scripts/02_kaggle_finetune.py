"""
02_kaggle_finetune.py — Fine-tune e5-large trên Kaggle GPU T4
Copy toàn bộ code này vào 1 Kaggle notebook cell

Setup Kaggle:
  1. New Notebook → Settings → Accelerator → GPU T4 x2
  2. Thêm cell đầu: !pip install -q sentence-transformers datasets
  3. Paste code này → Run All (~30 phút)
"""

# ============================================================
# INSTALL (chạy trong cell riêng trên Kaggle)
# ============================================================
# !pip install -q sentence-transformers datasets

import json
import time
import numpy as np
from datasets import load_dataset
from sentence_transformers import SentenceTransformer, InputExample, losses
from torch.utils.data import DataLoader

# ============================================================
# STEP 1: Download data
# ============================================================
print("=" * 60)
print("  STEP 1: Download Vietnamese Medical QA (7506 pairs)")
print("=" * 60)

ds = load_dataset("hungnm/vietnamese-medical-qa", split="train")
print(f"Downloaded: {len(ds)} QA pairs")

train_examples = []
for item in ds:
    q = item["question"].strip()
    a = item["answer"].strip()
    if 10 < len(q) < 500 and 20 < len(a) < 1000:
        train_examples.append(InputExample(texts=[q, a[:500]]))

split_idx = int(len(train_examples) * 0.9)
train_data = train_examples[:split_idx]
eval_data = train_examples[split_idx:]
print(f"Train: {len(train_data)}, Eval: {len(eval_data)}")

# ============================================================
# STEP 2: Load model + benchmark BEFORE
# ============================================================
print(f"\n{'=' * 60}")
print("  STEP 2: Benchmark BEFORE fine-tune")
print("=" * 60)

BASE_MODEL = "intfloat/multilingual-e5-large"
model = SentenceTransformer(BASE_MODEL)
print(f"Model: {BASE_MODEL} ({model.get_sentence_embedding_dimension()}d)")

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
    pos, neg = [], []
    for q, p in BENCH:
        qe = m.encode([f"query: {q}"], normalize_embeddings=True)[0]
        pe = m.encode([f"passage: {p}"], normalize_embeddings=True)[0]
        pos.append(float(np.dot(qe, pe)))
        for n in NEGS:
            ne = m.encode([f"passage: {n}"], normalize_embeddings=True)[0]
            neg.append(float(np.dot(qe, ne)))
    return {"pos": round(np.mean(pos), 4), "neg": round(np.mean(neg), 4),
            "margin": round(np.mean(pos) - np.mean(neg), 4), "details": [round(s, 4) for s in pos]}


before = benchmark(model)
print(f"  Positive sim: {before['pos']}")
print(f"  Negative sim: {before['neg']}")
print(f"  Margin:       {before['margin']}")

# ============================================================
# STEP 3: Fine-tune
# ============================================================
print(f"\n{'=' * 60}")
print("  STEP 3: Fine-tuning ({} pairs, 3 epochs)")
print("=" * 60)

BATCH_SIZE = 32
EPOCHS = 3
OUTPUT = "/kaggle/working/e5-large-medical-finetuned"

loader = DataLoader(train_data, shuffle=True, batch_size=BATCH_SIZE)
loss_fn = losses.MultipleNegativesRankingLoss(model=model)
warmup = int(len(loader) * EPOCHS * 0.1)

print(f"  Batches: {len(loader)}, Warmup: {warmup}")

t0 = time.time()
model.fit(
    train_objectives=[(loader, loss_fn)],
    epochs=EPOCHS,
    warmup_steps=warmup,
    output_path=OUTPUT,
    save_best_model=True,
    show_progress_bar=True,
    use_amp=True,
)
train_min = (time.time() - t0) / 60
print(f"\n  Done in {train_min:.1f} minutes")

# ============================================================
# STEP 4: Benchmark AFTER
# ============================================================
print(f"\n{'=' * 60}")
print("  STEP 4: Benchmark AFTER fine-tune")
print("=" * 60)

model_ft = SentenceTransformer(OUTPUT)
after = benchmark(model_ft)
print(f"  Positive sim: {after['pos']}")
print(f"  Negative sim: {after['neg']}")
print(f"  Margin:       {after['margin']}")

# ============================================================
# STEP 5: Comparison
# ============================================================
print(f"\n{'=' * 60}")
print("  RESULTS: Before vs After")
print("=" * 60)
print(f"{'Metric':<25} {'Before':>8} {'After':>8} {'Change':>8}")
print("-" * 50)
print(f"{'Positive Similarity':<25} {before['pos']:>8.4f} {after['pos']:>8.4f} {after['pos']-before['pos']:>+8.4f}")
print(f"{'Negative Similarity':<25} {before['neg']:>8.4f} {after['neg']:>8.4f} {after['neg']-before['neg']:>+8.4f}")
print(f"{'Margin':<25} {before['margin']:>8.4f} {after['margin']:>8.4f} {after['margin']-before['margin']:>+8.4f}")
print(f"{'Training Time':<25} {'':>8} {train_min:>7.1f}m")

print(f"\nPer-query:")
print(f"{'Query':<40} {'Before':>8} {'After':>8}")
print("-" * 58)
for i, (q, _) in enumerate(BENCH):
    print(f"{q[:39]:<40} {before['details'][i]:>8.4f} {after['details'][i]:>8.4f}")

# Save
results = {"before": before, "after": after, "train_min": round(train_min, 1),
           "train_pairs": len(train_data), "model": BASE_MODEL}
with open("/kaggle/working/finetune_results.json", "w") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\n{'=' * 60}")
print("  Download model từ Output panel bên phải Kaggle")
print("=" * 60)
