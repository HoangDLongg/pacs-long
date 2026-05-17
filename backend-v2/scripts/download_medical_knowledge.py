"""
scripts/download_medical_knowledge.py
Download tài liệu y tế tiếng Việt từ HuggingFace để làm RAG Knowledge Base.

Datasets:
  1. urnus11/Vietnamese-Healthcare  — Bài viết Vinmec (bệnh, thuốc)
  2. VietAI/vi_pubmed              — 20M abstracts PubMed (Việt hóa)
  3. tmnam20/ViMedAQA               — Passages về bệnh/thuốc/cơ thể
  4. PB3002/ViMedical_Disease       — 12K+ triệu chứng bệnh

Output: dataset/medical_knowledge/<source>/*.jsonl
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Output directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent / "dataset" / "medical_knowledge"


def save_jsonl(records: list, filepath: Path):
    """Save records to JSONL file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    size_mb = filepath.stat().st_size / (1024 * 1024)
    logger.info(f"  ✅ Saved {len(records)} records → {filepath} ({size_mb:.1f} MB)")


# ============================================================
# 1. Vietnamese-Healthcare (Vinmec articles)
# ============================================================
def download_vietnamese_healthcare():
    """
    Download bài viết y tế từ Vinmec.
    Subsets: vinmec_article_content, vinmec_article_main, vinmec_article_subtitle
    ⚠️ Gated dataset — cần HuggingFace login (huggingface-cli login)
    """
    from datasets import load_dataset

    out_dir = BASE_DIR / "vinmec_articles"
    logger.info("=" * 60)
    logger.info("📥 [1/4] Downloading urnus11/Vietnamese-Healthcare...")
    logger.info("=" * 60)

    subsets = ["vinmec_article_content", "vinmec_article_main", "vinmec_article_subtitle"]
    total = 0

    for subset_name in subsets:
        logger.info(f"\n  📂 Loading subset: {subset_name}...")
        try:
            ds = load_dataset("urnus11/Vietnamese-Healthcare", subset_name, trust_remote_code=True)

            records = []
            for split_name, split_data in ds.items():
                for row in split_data:
                    record = {
                        "source": "vinmec",
                        "subset": subset_name,
                        "split": split_name,
                    }
                    # Preserve all columns
                    for col in row:
                        record[col] = row[col]
                    records.append(record)

            save_jsonl(records, out_dir / f"{subset_name}.jsonl")
            total += len(records)

        except Exception as e:
            logger.warning(f"  ⚠️ Failed to load {subset_name}: {e}")
            logger.warning("  → Có thể cần: huggingface-cli login (gated dataset)")

    logger.info(f"\n  📊 Vietnamese-Healthcare total: {total} documents")
    return total


# ============================================================
# 2. vi_pubmed (PubMed abstracts in Vietnamese)
# ============================================================
def download_vi_pubmed(max_records: int = 200_000):
    """
    Download abstracts y sinh PubMed đã dịch sang tiếng Việt.
    Dataset gốc: 20M rows, 23GB → chỉ lấy max_records đầu.
    """
    from datasets import load_dataset

    out_dir = BASE_DIR / "vi_pubmed"
    logger.info("=" * 60)
    logger.info(f"📥 [2/4] Downloading VietAI/vi_pubmed (top {max_records:,} records)...")
    logger.info("=" * 60)

    try:
        # Stream để không tải hết 23GB
        ds = load_dataset("VietAI/vi_pubmed", streaming=True)

        records = []
        count = 0
        batch_size = 50_000

        for split_name, split_data in ds.items():
            logger.info(f"  📂 Streaming split: {split_name}...")
            for row in split_data:
                # Lấy text tiếng Việt
                vi_text = row.get("vi", "") or row.get("text", "")
                en_text = row.get("en", "")

                if not vi_text or len(vi_text.strip()) < 50:
                    continue

                records.append({
                    "source": "vi_pubmed",
                    "split": split_name,
                    "text_vi": vi_text.strip(),
                    "text_en": en_text.strip() if en_text else "",
                })
                count += 1

                if count % batch_size == 0:
                    logger.info(f"    ... {count:,} records loaded")

                if count >= max_records:
                    break

            if count >= max_records:
                break

        # Split into multiple files (50K each) to avoid huge files
        chunk_size = 50_000
        for i in range(0, len(records), chunk_size):
            chunk = records[i:i + chunk_size]
            chunk_idx = i // chunk_size + 1
            save_jsonl(chunk, out_dir / f"vi_pubmed_chunk_{chunk_idx:03d}.jsonl")

        logger.info(f"\n  📊 vi_pubmed total: {len(records)} abstracts")
        return len(records)

    except Exception as e:
        logger.error(f"  ❌ Failed: {e}")
        return 0


# ============================================================
# 3. ViMedAQA (Medical passages)
# ============================================================
def download_vimedaqa():
    """
    Download passages y tế (bệnh, thuốc, cơ thể, y dược).
    Trích xuất phần context/passage làm knowledge documents.
    """
    from datasets import load_dataset

    out_dir = BASE_DIR / "vimedaqa"
    logger.info("=" * 60)
    logger.info("📥 [3/4] Downloading tmnam20/ViMedAQA...")
    logger.info("=" * 60)

    try:
        ds = load_dataset("tmnam20/ViMedAQA", "all", trust_remote_code=True)

        records = []
        seen_texts = set()  # Dedup

        for split_name, split_data in ds.items():
            logger.info(f"  📂 Processing split: {split_name} ({len(split_data)} rows)...")
            for row in split_data:
                # Extract passage/context (the knowledge content)
                context = (
                    row.get("context", "")
                    or row.get("passage", "")
                    or row.get("answer", "")
                    or ""
                )
                question = row.get("question", "")

                if not context or len(context.strip()) < 30:
                    continue

                # Dedup by context
                ctx_key = context.strip()[:200]
                if ctx_key in seen_texts:
                    continue
                seen_texts.add(ctx_key)

                record = {
                    "source": "vimedaqa",
                    "split": split_name,
                    "text": context.strip(),
                }
                # Add question as metadata (useful for understanding context)
                if question:
                    record["related_question"] = question.strip()

                # Add any category/topic info
                for field in ["category", "topic", "type", "label"]:
                    if field in row and row[field]:
                        record[field] = row[field]

                records.append(record)

        save_jsonl(records, out_dir / "vimedaqa_passages.jsonl")
        logger.info(f"\n  📊 ViMedAQA total: {len(records)} unique passages")
        return len(records)

    except Exception as e:
        logger.error(f"  ❌ Failed: {e}")
        return 0


# ============================================================
# 4. ViMedical_Disease (Disease symptoms)
# ============================================================
def download_vimedical_disease():
    """
    Download triệu chứng bệnh phổ biến (12K+).
    Format: Disease + mô tả triệu chứng.
    """
    from datasets import load_dataset

    out_dir = BASE_DIR / "vimedical_disease"
    logger.info("=" * 60)
    logger.info("📥 [4/4] Downloading PB3002/ViMedical_Disease...")
    logger.info("=" * 60)

    try:
        ds = load_dataset("PB3002/ViMedical_Disease", trust_remote_code=True)

        records = []
        disease_map = {}  # Group by disease

        for split_name, split_data in ds.items():
            logger.info(f"  📂 Processing split: {split_name} ({len(split_data)} rows)...")
            for row in split_data:
                disease = row.get("Disease", "") or row.get("disease", "")
                question = row.get("Question", "") or row.get("question", "")

                if not disease or not question:
                    continue

                records.append({
                    "source": "vimedical_disease",
                    "split": split_name,
                    "disease": disease.strip(),
                    "symptoms_description": question.strip(),
                })

                # Track diseases
                disease_map.setdefault(disease.strip(), []).append(question.strip())

        save_jsonl(records, out_dir / "disease_symptoms.jsonl")

        # Also save grouped by disease (better for RAG)
        grouped_records = []
        for disease, descriptions in disease_map.items():
            # Combine all symptom descriptions for each disease
            combined_text = f"Bệnh: {disease}\n\nCác triệu chứng và mô tả:\n"
            for i, desc in enumerate(descriptions[:20], 1):  # Max 20 per disease
                combined_text += f"- {desc}\n"

            grouped_records.append({
                "source": "vimedical_disease",
                "disease": disease,
                "text": combined_text.strip(),
                "num_descriptions": len(descriptions),
            })

        save_jsonl(grouped_records, out_dir / "disease_grouped.jsonl")

        logger.info(f"\n  📊 ViMedical_Disease: {len(records)} symptom records, {len(disease_map)} unique diseases")
        return len(records)

    except Exception as e:
        logger.error(f"  ❌ Failed: {e}")
        return 0


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Download Vietnamese medical knowledge for RAG")
    parser.add_argument("--pubmed-limit", type=int, default=200_000,
                        help="Max PubMed abstracts to download (default: 200K)")
    parser.add_argument("--skip-pubmed", action="store_true",
                        help="Skip vi_pubmed (very large)")
    parser.add_argument("--skip-vinmec", action="store_true",
                        help="Skip Vietnamese-Healthcare (gated)")
    parser.add_argument("--only", type=str, default=None,
                        help="Download only one: vinmec|pubmed|vimedaqa|disease")
    args = parser.parse_args()

    logger.info("🏥 Vietnamese Medical Knowledge Downloader for RAG")
    logger.info(f"   Output directory: {BASE_DIR}")
    logger.info(f"   PubMed limit: {args.pubmed_limit:,}")
    logger.info(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    BASE_DIR.mkdir(parents=True, exist_ok=True)
    totals = {}

    # 1. Vietnamese-Healthcare
    if args.only in (None, "vinmec") and not args.skip_vinmec:
        totals["Vietnamese-Healthcare"] = download_vietnamese_healthcare()
    
    # 2. vi_pubmed
    if args.only in (None, "pubmed") and not args.skip_pubmed:
        totals["vi_pubmed"] = download_vi_pubmed(max_records=args.pubmed_limit)

    # 3. ViMedAQA
    if args.only in (None, "vimedaqa"):
        totals["ViMedAQA"] = download_vimedaqa()

    # 4. ViMedical_Disease
    if args.only in (None, "disease"):
        totals["ViMedical_Disease"] = download_vimedical_disease()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 DOWNLOAD SUMMARY")
    logger.info("=" * 60)
    grand_total = 0
    for name, count in totals.items():
        status = "✅" if count > 0 else "❌"
        logger.info(f"  {status} {name}: {count:,} documents")
        grand_total += count

    logger.info(f"\n  🎯 Grand Total: {grand_total:,} documents")
    logger.info(f"  📁 Location: {BASE_DIR}")

    # Save metadata
    meta = {
        "downloaded_at": datetime.now().isoformat(),
        "datasets": totals,
        "grand_total": grand_total,
        "pubmed_limit": args.pubmed_limit,
    }
    meta_path = BASE_DIR / "metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    logger.info(f"  📝 Metadata saved: {meta_path}")


if __name__ == "__main__":
    main()
