"""
benchmark_search_methods.py — So sánh Keyword vs Dense vs Hybrid Search
Chạy OFFLINE — không cần database, chỉ cần reports_data.json + model

Output: bảng so sánh P@5, MRR, nDCG@5 cho luận văn

Usage:
  cd backend-v2
  python scripts/benchmark_search_methods.py
"""

import time
import json
import os
import sys
import numpy as np
from collections import defaultdict

# ============================================================
# Load data
# ============================================================

def load_reports():
    path = os.path.join(os.path.dirname(__file__), "reports_data.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} reports")
    return data


def make_text(r):
    return f"{r.get('findings', '')} {r.get('conclusion', '')}"


# ============================================================
# Search methods (offline — no DB needed)
# ============================================================

def keyword_search_offline(query, reports, top_k=5):
    """ILIKE simulation — exact substring match"""
    q = query.lower()
    results = []
    for r in reports:
        text = make_text(r).lower()
        if q in text:
            results.append({**r, "score": 1.0, "method": "keyword"})
    return results[:top_k]


def dense_search_offline(query, reports, report_vecs, model, top_k=5):
    """Dense search — cosine similarity with e5-large"""
    q_vec = model.encode([f"query: {query}"], normalize_embeddings=True)[0]
    scores = np.dot(report_vecs, q_vec)
    top_indices = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in top_indices:
        r = reports[idx]
        results.append({**r, "score": float(scores[idx]), "method": "dense"})
    return results


def bm25_search_offline(query, reports, bm25_model, top_k=5):
    """BM25 sparse search"""
    tokens = query.lower().split()
    scores = bm25_model.get_scores(tokens)
    top_indices = np.argsort(scores)[::-1][:top_k]
    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            results.append({**reports[idx], "score": float(scores[idx]), "method": "bm25"})
    return results[:top_k]


def hybrid_search_offline(query, reports, report_vecs, model, bm25_model, top_k=5, rrf_k=60):
    """Hybrid search — Dense + BM25 + RRF fusion"""
    # Dense
    q_vec = model.encode([f"query: {query}"], normalize_embeddings=True)[0]
    dense_scores = np.dot(report_vecs, q_vec)
    dense_ranking = np.argsort(dense_scores)[::-1]

    # BM25
    tokens = query.lower().split()
    bm25_scores = bm25_model.get_scores(tokens)
    bm25_ranking = np.argsort(bm25_scores)[::-1]

    # RRF fusion
    rrf_scores = defaultdict(float)
    for rank, idx in enumerate(dense_ranking):
        rrf_scores[idx] += 1.0 / (rrf_k + rank + 1)
    for rank, idx in enumerate(bm25_ranking):
        rrf_scores[idx] += 1.0 / (rrf_k + rank + 1)

    sorted_indices = sorted(rrf_scores, key=rrf_scores.get, reverse=True)[:top_k]
    results = []
    for idx in sorted_indices:
        r = reports[idx]
        results.append({
            **r,
            "score": float(rrf_scores[idx]),
            "dense_score": float(dense_scores[idx]),
            "sparse_score": float(bm25_scores[idx]),
            "method": "hybrid",
        })
    return results


# ============================================================
# Test queries + ground truth
# ============================================================

QUERIES = [
    {"query": "tổn thương phổi kẽ", "keywords": ["phổi kẽ"], "cat": "chest"},
    {"query": "mờ kính rải rác hai phổi", "keywords": ["mờ kính", "phổi"], "cat": "chest"},
    {"query": "bóng tim to trên phim", "keywords": ["tim to"], "cat": "chest"},
    {"query": "vôi hóa thành quai động mạch chủ", "keywords": ["vôi hóa"], "cat": "chest"},
    {"query": "tràn dịch màng phổi", "keywords": ["tràn dịch", "dịch màng phổi"], "cat": "chest"},
    {"query": "khối u gan nghi HCC ác tính", "keywords": ["HCC", "ung thư"], "cat": "abdomen"},
    {"query": "sỏi túi mật viêm mạn", "keywords": ["sỏi túi mật"], "cat": "abdomen"},
    {"query": "sỏi thận ứ nước giãn đài bể thận", "keywords": ["sỏi", "thận"], "cat": "abdomen"},
    {"query": "thoát vị đĩa đệm chèn ép rễ thần kinh", "keywords": ["thoát vị", "đĩa đệm"], "cat": "spine"},
    {"query": "gãy lún đốt sống thắt lưng", "keywords": ["gãy lún", "đốt sống"], "cat": "spine"},
    {"query": "u vú BI-RADS 5 nghi ác tính hạch nách", "keywords": ["BI-RADS 5", "ác tính"], "cat": "breast"},
    {"query": "vi vôi hóa dạng đa hình tuyến vú", "keywords": ["vi vôi hóa", "vú"], "cat": "breast"},
]


def is_relevant(result, keywords):
    text = make_text(result).lower()
    return any(kw.lower() in text for kw in keywords)


def compute_metrics(results, keywords, k=5):
    relevant = [is_relevant(r, keywords) for r in results[:k]]
    precision = sum(relevant) / k if k > 0 else 0
    mrr = 0.0
    for i, rel in enumerate(relevant):
        if rel:
            mrr = 1.0 / (i + 1)
            break
    dcg = sum((1.0 / np.log2(i + 2)) for i, rel in enumerate(relevant) if rel)
    total_rel = sum(1 for r in results if is_relevant(r, keywords))
    idcg = sum(1.0 / np.log2(i + 2) for i in range(min(k, max(total_rel, 1))))
    ndcg = dcg / idcg if idcg > 0 else 0
    return {"P@5": round(precision, 3), "MRR": round(mrr, 3), "nDCG@5": round(ndcg, 3), "hits": sum(relevant)}


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 80)
    print("  BENCHMARK: Keyword vs Dense vs Hybrid Search")
    print("  Data: 75 báo cáo y tế (VinDr) | Model: multilingual-e5-large")
    print("=" * 80)

    # Load data
    reports = load_reports()
    texts = [make_text(r) for r in reports]

    # Load embedding model
    print("\nLoading multilingual-e5-large...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("intfloat/multilingual-e5-large")

    # Encode all reports
    print("Encoding 75 reports...")
    t0 = time.time()
    prefixed = [f"passage: {t}" for t in texts]
    report_vecs = model.encode(prefixed, normalize_embeddings=True, batch_size=16, show_progress_bar=True)
    encode_time = time.time() - t0
    print(f"Encoded in {encode_time:.1f}s ({encode_time/len(reports)*1000:.0f}ms/report)")

    # Build BM25
    print("Building BM25 index...")
    from rank_bm25 import BM25Okapi
    tokenized = [t.lower().split() for t in texts]
    bm25 = BM25Okapi(tokenized)

    # Run benchmark
    methods = {
        "Keyword": lambda q: keyword_search_offline(q, reports),
        "Dense": lambda q: dense_search_offline(q, reports, report_vecs, model),
        "BM25": lambda q: bm25_search_offline(q, reports, bm25),
        "Hybrid": lambda q: hybrid_search_offline(q, reports, report_vecs, model, bm25),
    }

    all_metrics = {m: [] for m in methods}
    all_times = {m: [] for m in methods}
    details = []

    for q in QUERIES:
        for method_name, search_fn in methods.items():
            t0 = time.time()
            results = search_fn(q["query"])
            elapsed = time.time() - t0

            m = compute_metrics(results, q["keywords"])
            all_metrics[method_name].append(m)
            all_times[method_name].append(elapsed)

            details.append({"method": method_name, "query": q["query"], "cat": q["cat"], **m, "time_ms": round(elapsed*1000, 1)})

    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "=" * 80)
    print("  KẾT QUẢ SO SÁNH 4 PHƯƠNG PHÁP TÌM KIẾM")
    print(f"  {len(QUERIES)} test queries × {len(reports)} reports")
    print("=" * 80)
    print(f"{'Method':<12} {'P@5':>8} {'MRR':>8} {'nDCG@5':>8} {'Hits/60':>8} {'Avg ms':>8}")
    print("-" * 55)

    for method in methods:
        avg_p = np.mean([m["P@5"] for m in all_metrics[method]])
        avg_mrr = np.mean([m["MRR"] for m in all_metrics[method]])
        avg_ndcg = np.mean([m["nDCG@5"] for m in all_metrics[method]])
        total_hits = sum(m["hits"] for m in all_metrics[method])
        avg_time = np.mean(all_times[method]) * 1000
        print(f"{method:<12} {avg_p:>8.3f} {avg_mrr:>8.3f} {avg_ndcg:>8.3f} {total_hits:>5}/60 {avg_time:>7.1f}")

    # Per category
    print("\n" + "-" * 55)
    print("  MRR per category:")
    categories = sorted(set(q["cat"] for q in QUERIES))
    print(f"{'Category':<12}", end="")
    for method in methods:
        print(f" {method:>10}", end="")
    print()
    for cat in categories:
        print(f"{cat:<12}", end="")
        for method in methods:
            cat_m = [d["MRR"] for d in details if d["method"] == method and d["cat"] == cat]
            print(f" {np.mean(cat_m):>10.3f}", end="")
        print()

    # Per query detail
    print("\n" + "-" * 55)
    print("  Detail per query (MRR):")
    print(f"{'Query':<45}", end="")
    for method in methods:
        print(f" {method[:3]:>5}", end="")
    print()
    for q in QUERIES:
        print(f"{q['query'][:44]:<45}", end="")
        for method in methods:
            d = [x for x in details if x["method"] == method and x["query"] == q["query"]][0]
            mrr = d["MRR"]
            marker = "  ✓" if mrr >= 1.0 else (" ~" if mrr > 0 else "  ✗")
            print(f" {mrr:>4.2f}{'' if mrr == 0 else ''}", end="")
        print()

    # Save
    output = {
        "summary": {},
        "details": details,
    }
    for method in methods:
        output["summary"][method] = {
            "P@5": round(np.mean([m["P@5"] for m in all_metrics[method]]), 3),
            "MRR": round(np.mean([m["MRR"] for m in all_metrics[method]]), 3),
            "nDCG@5": round(np.mean([m["nDCG@5"] for m in all_metrics[method]]), 3),
        }

    path = os.path.join(os.path.dirname(__file__), "benchmark_search_results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] {path}")


if __name__ == "__main__":
    main()
