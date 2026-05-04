# Embedding Fine-tuning for PACS++

Fine-tune `multilingual-e5-large` trên dữ liệu y tế tiếng Việt để cải thiện RAG search.

## Structure

```
embedding_finetuning/
├── scripts/
│   ├── 01_download_data.py        # Tải data từ HuggingFace
│   ├── 02_kaggle_finetune.py      # Chạy trên Kaggle GPU T4
│   └── 03_benchmark_compare.py    # So sánh before/after
├── data/                          # Training data (auto-generated)
└── models/                        # Fine-tuned models (gitignored)
```

## Quick Start

### 1. Tải training data
```bash
python scripts/01_download_data.py
```

### 2. Fine-tune trên Kaggle
- Tạo notebook trên [kaggle.com](https://kaggle.com)
- Bật GPU T4
- Copy nội dung `scripts/02_kaggle_finetune.py`
- Run All (~30 phút)

### 3. Benchmark
```bash
python scripts/03_benchmark_compare.py --model-path models/finetuned/
```

## Data Source
- **hungnm/vietnamese-medical-qa** (HuggingFace): 9,335 QA pairs y tế tiếng Việt
- Source gốc: Vinmec + eDoctor
- License: Apache-2.0
