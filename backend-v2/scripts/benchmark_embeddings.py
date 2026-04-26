"""
benchmark_embeddings.py — So sánh embedding models trên data báo cáo y tế tiếng Việt
Chạy trên Kaggle (GPU T4 16GB) hoặc local (GPU 4GB cho model nhỏ)

Models so sánh:
1. BGE-M3           (BAAI)      - 1024d
2. multilingual-e5-large (MS)   - 1024d
3. GTE-multilingual-base (Ali)  - 768d
4. MiniLM-L12       (MS)        - 384d
5. NV-Embed-v2      (NVIDIA)    - 4096d (cần GPU 16GB+)

Metrics:
- Precision@5, Precision@10
- MRR (Mean Reciprocal Rank)
- nDCG@10
- Thời gian encode trung bình

Output: bảng so sánh + biểu đồ cho luận văn

Usage (Kaggle notebook):
  !pip install FlagEmbedding sentence-transformers
  !python benchmark_embeddings.py

Usage (local 4GB GPU):
  python benchmark_embeddings.py --skip-large
"""

import time
import json
import os
import numpy as np
from typing import List, Dict

# ========== LOAD DATA từ reports_data.json ==========

def load_reports(json_path=None):
    """Load 75 báo cáo thật từ file JSON (export từ DB)"""
    if json_path is None:
        json_path = os.path.join(os.path.dirname(__file__), "reports_data.json")
    
    # Kaggle: thử nhiều path
    if not os.path.exists(json_path):
        alt_paths = [
            "/kaggle/input/pacs-reports/reports_data.json",
            "./reports_data.json",
        ]
        for p in alt_paths:
            if os.path.exists(p):
                json_path = p
                break
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print(f"  Loaded {len(data)} reports from {json_path}")
    return data


def build_ground_truth(reports):
    """
    Tự động tạo ground truth queries dựa trên nội dung 75 reports thật.
    Mỗi query: tìm reports có chứa keyword/concept tương ứng.
    """
    queries = []
    
    # Helper: tìm report IDs chứa keyword trong findings/conclusion
    def find_ids(keyword):
        ids = []
        for r in reports:
            text = f"{r.get('findings','')} {r.get('conclusion','')}"
            if keyword.lower() in text.lower():
                ids.append(r["id"])
        return ids
    
    # Query 1: Tổn thương phổi kẽ (chiếm đa số chest reports)
    ids = find_ids("phổi kẽ")
    if ids:
        queries.append({"query": "tổn thương phổi dạng mờ kính rải rác", "expected_ids": ids[:10], "category": "chest"})
    
    # Query 2: Bóng tim to
    ids = find_ids("tim to")
    if ids:
        queries.append({"query": "bóng tim to trên X-quang ngực", "expected_ids": ids[:8], "category": "chest"})
    
    # Query 3: Vôi hóa động mạch chủ
    ids = find_ids("vôi hóa")
    if ids:
        queries.append({"query": "vôi hóa thành quai động mạch chủ", "expected_ids": ids[:8], "category": "chest"})
    
    # Query 4: Khối u vú nghi ác tính (BI-RADS 5)
    ids = find_ids("BI-RADS 5")
    if ids:
        queries.append({"query": "khối u vú nghi ngờ ác tính", "expected_ids": ids, "category": "breast"})
    
    # Query 5: Nốt đặc vú lành tính (BI-RADS 3)
    ids = find_ids("BI-RADS 3")
    if ids:
        queries.append({"query": "nốt đặc vú có thể lành tính cần theo dõi", "expected_ids": ids, "category": "breast"})
    
    # Query 6: HCC (ung thư gan)
    ids = find_ids("HCC")
    if ids:
        queries.append({"query": "nốt gan nghi ung thư biểu mô tế bào gan", "expected_ids": ids, "category": "abdomen"})
    
    # Query 7: Sỏi thận ứ nước
    ids = find_ids("sỏi")
    if ids:
        queries.append({"query": "sỏi thận gây giãn đài bể thận ứ nước", "expected_ids": ids, "category": "abdomen"})
    
    # Query 8: Thoát vị đĩa đệm
    ids = find_ids("thoát vị")
    if ids:
        queries.append({"query": "thoát vị đĩa đệm cột sống thắt lưng chèn ép rễ", "expected_ids": ids, "category": "spine"})
    
    # Query 9: Thoái hóa cột sống
    ids = find_ids("thoái hóa")
    if ids:
        queries.append({"query": "thoái hóa cột sống đa tầng gai xương", "expected_ids": ids, "category": "spine"})
    
    # Query 10: Dịch màng phổi
    ids = find_ids("dịch màng phổi") + find_ids("tràn dịch")
    ids = list(set(ids))
    if ids:
        queries.append({"query": "tràn dịch màng phổi", "expected_ids": ids, "category": "chest"})
    
    # Query 11: Vi vôi hóa vú (BI-RADS 4)
    ids = find_ids("BI-RADS 4")
    if ids:
        queries.append({"query": "vi vôi hóa nghi ngờ ác tính trên mammography", "expected_ids": ids, "category": "breast"})
    
    # Query 12: Nang thận
    ids = find_ids("nang") 
    kidney_ids = [i for i in ids if any("thận" in f"{r.get('findings','')} {r.get('conclusion','')}" for r in reports if r["id"] == i)]
    if kidney_ids:
        queries.append({"query": "nang đơn thuần thận Bosniak I", "expected_ids": kidney_ids, "category": "abdomen"})
    
    print(f"  Built {len(queries)} test queries with ground truth")
    for q in queries:
        print(f"    [{q['category']}] \"{q['query'][:50]}\" → {len(q['expected_ids'])} relevant docs")
    
    return queries


def make_text(report):
    return f"{report['findings']} {report['conclusion']}"


def cosine_similarity(a, b):
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def compute_metrics(rankings: List[int], expected_ids: List[int], k_values=[5, 10]):
    """Tính Precision@K, MRR, nDCG@K"""
    results = {}

    # Precision@K
    for k in k_values:
        top_k = rankings[:k]
        relevant = len([r for r in top_k if r in expected_ids])
        results[f"P@{k}"] = relevant / min(k, len(expected_ids))

    # MRR
    for i, rid in enumerate(rankings):
        if rid in expected_ids:
            results["MRR"] = 1.0 / (i + 1)
            break
    else:
        results["MRR"] = 0.0

    # nDCG@10
    dcg = 0.0
    for i, rid in enumerate(rankings[:10]):
        if rid in expected_ids:
            dcg += 1.0 / np.log2(i + 2)
    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(10, len(expected_ids))))
    results["nDCG@10"] = dcg / idcg if idcg > 0 else 0.0

    return results


def benchmark_model(model_name: str, encode_fn, reports, queries):
    """Benchmark 1 model: encode reports + queries, tính metrics"""
    print(f"\n{'='*60}")
    print(f"  Model: {model_name}")
    print(f"{'='*60}")

    # 1. Encode all reports
    report_texts = [make_text(r) for r in reports]
    t0 = time.time()
    report_vecs = encode_fn(report_texts)
    encode_time = (time.time() - t0) / len(report_texts)
    dim = len(report_vecs[0])
    print(f"  Dimension: {dim}")
    print(f"  Encode time: {encode_time:.3f}s/report")

    # 2. Test queries
    all_metrics = []
    for q in queries:
        t0 = time.time()
        q_vec = encode_fn([q["query"]])[0]
        query_time = time.time() - t0

        # Rank reports by cosine similarity
        scores = [(r["id"], cosine_similarity(q_vec, rv))
                   for r, rv in zip(reports, report_vecs)]
        scores.sort(key=lambda x: x[1], reverse=True)
        rankings = [s[0] for s in scores]

        metrics = compute_metrics(rankings, q["expected_ids"])
        metrics["query_time"] = query_time
        all_metrics.append(metrics)

        print(f"  Q: \"{q['query'][:40]}...\" → Top3: {rankings[:3]} "
              f"(expect: {q['expected_ids']}) MRR={metrics['MRR']:.2f}")

    # 3. Average metrics
    avg = {}
    for key in all_metrics[0]:
        avg[key] = np.mean([m[key] for m in all_metrics])

    print(f"\n  --- Average Metrics ---")
    print(f"  P@5:      {avg['P@5']:.3f}")
    print(f"  P@10:     {avg['P@10']:.3f}")
    print(f"  MRR:      {avg['MRR']:.3f}")
    print(f"  nDCG@10:  {avg['nDCG@10']:.3f}")
    print(f"  Avg query time: {avg['query_time']:.3f}s")
    print(f"  Encode time:    {encode_time:.3f}s/report")

    return {
        "model": model_name,
        "dim": dim,
        "P@5": round(avg["P@5"], 3),
        "P@10": round(avg["P@10"], 3),
        "MRR": round(avg["MRR"], 3),
        "nDCG@10": round(avg["nDCG@10"], 3),
        "query_time_ms": round(avg["query_time"] * 1000, 1),
        "encode_time_ms": round(encode_time * 1000, 1),
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-large", action="store_true",
                        help="Bo qua NV-Embed-v2 (can GPU 16GB+)")
    parser.add_argument("--data", type=str, default=None,
                        help="Path to reports_data.json")
    args = parser.parse_args()

    # Load data
    print("\n[1/3] Loading data...")
    REPORTS = load_reports(args.data)
    QUERIES = build_ground_truth(REPORTS)

    results = []

    # --- Model 1: BGE-M3 ---
    try:
        from FlagEmbedding import BGEM3FlagModel
        model = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True)
        def encode_bge(texts):
            out = model.encode(texts, batch_size=8, max_length=512)
            return [v.tolist() for v in out["dense_vecs"]]
        results.append(benchmark_model("BGE-M3 (1024d)", encode_bge, REPORTS, QUERIES))
    except Exception as e:
        print(f"[SKIP] BGE-M3: {e}")

    # --- Model 2: multilingual-e5-large ---
    try:
        from sentence_transformers import SentenceTransformer
        model_e5 = SentenceTransformer("intfloat/multilingual-e5-large")
        def encode_e5(texts):
            prefixed = [f"query: {t}" for t in texts]
            return model_e5.encode(prefixed).tolist()
        results.append(benchmark_model("multilingual-e5-large (1024d)", encode_e5, REPORTS, QUERIES))
    except Exception as e:
        print(f"[SKIP] e5-large: {e}")

    # --- Model 3: GTE-multilingual-base ---
    try:
        from sentence_transformers import SentenceTransformer
        model_gte = SentenceTransformer("Alibaba-NLP/gte-multilingual-base")
        def encode_gte(texts):
            return model_gte.encode(texts).tolist()
        results.append(benchmark_model("GTE-multilingual-base (768d)", encode_gte, REPORTS, QUERIES))
    except Exception as e:
        print(f"[SKIP] GTE: {e}")

    # --- Model 4: MiniLM-L12 ---
    try:
        from sentence_transformers import SentenceTransformer
        model_mini = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        def encode_mini(texts):
            return model_mini.encode(texts).tolist()
        results.append(benchmark_model("MiniLM-L12 (384d)", encode_mini, REPORTS, QUERIES))
    except Exception as e:
        print(f"[SKIP] MiniLM: {e}")

    # --- Model 5: NV-Embed-v2 (large, cần GPU 16GB+) ---
    if not args.skip_large:
        try:
            from sentence_transformers import SentenceTransformer
            model_nv = SentenceTransformer("nvidia/NV-Embed-v2", trust_remote_code=True)
            def encode_nv(texts):
                return model_nv.encode(texts).tolist()
            results.append(benchmark_model("NV-Embed-v2 (4096d)", encode_nv, REPORTS, QUERIES))
        except Exception as e:
            print(f"[SKIP] NV-Embed-v2: {e}")
    else:
        print("\n[SKIP] NV-Embed-v2 (--skip-large)")

    # --- Summary ---
    print("\n" + "=" * 80)
    print(f"  KET QUA SO SANH EMBEDDING MODELS")
    print(f"  Data: {len(REPORTS)} bao cao y te tieng Viet, {len(QUERIES)} truy van test")
    print("=" * 80)
    print(f"{'Model':<35} {'Dim':>5} {'P@5':>6} {'MRR':>6} {'nDCG@10':>8} {'Query(ms)':>10} {'Encode(ms)':>11}")
    print("-" * 80)
    for r in results:
        print(f"{r['model']:<35} {r['dim']:>5} {r['P@5']:>6.3f} {r['MRR']:>6.3f} {r['nDCG@10']:>8.3f} {r['query_time_ms']:>10.1f} {r['encode_time_ms']:>11.1f}")

    # Save JSON
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\n[SAVED] benchmark_results.json")


if __name__ == "__main__":
    main()
