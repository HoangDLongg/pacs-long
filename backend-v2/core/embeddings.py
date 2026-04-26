"""
core/embeddings.py — multilingual-e5-large Embedding Singleton
Spec: 03_backend L22, TECHNICAL 2.1
UC18: Tự động tạo embedding khi lưu báo cáo

Model: intfloat/multilingual-e5-large (1024d, đa ngôn ngữ, MIT license)
Benchmark: nDCG@10=0.904, MRR=0.944 trên 75 báo cáo y tế tiếng Việt

Pattern adapted from project 6803_RAG (hybrid_retriever.py)
"""

import logging
import re
from typing import List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# BM25 cho Sparse Search (copy from 6803 hybrid_retriever.py)
# ============================================================
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("[Embedding] rank-bm25 not available, sparse search disabled")

# Vietnamese stopwords (from 6803_rag)
STOPWORDS = {
    'là', 'của', 'và', 'có', 'được', 'trong', 'những',
    'gì', 'bao', 'gồm', 'như', 'thế', 'nào', 'cho', 'này',
    'đó', 'với', 'các', 'một', 'để', 'theo', 'khi', 'từ',
    'không', 'bên', 'hai', 'phải', 'trái', 'bình', 'thường',
}


def tokenize_vietnamese(text: str) -> List[str]:
    """
    Simple Vietnamese tokenizer cho BM25.
    Copy from 6803_rag/core/rag/hybrid_retriever.py:_tokenize_vietnamese
    """
    text = (text or "").lower()
    # Remove punctuation but keep Vietnamese characters
    text = re.sub(
        r'[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]',
        ' ', text
    )
    tokens = text.split()
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    return tokens


# ============================================================
# Embedding Model Singleton (e5-large thay BGE-M3)
# ============================================================

class EmbeddingModel:
    """Singleton wrapper cho multilingual-e5-large model"""

    _instance = None
    _model = None

    @classmethod
    def get_model(cls):
        """Lazy-load model lần đầu tiên"""
        if cls._model is None:
            logger.info("[Embedding] Loading multilingual-e5-large (lần đầu, mất ~30s)...")
            try:
                from sentence_transformers import SentenceTransformer
                cls._model = SentenceTransformer(
                    "intfloat/multilingual-e5-large",
                )
                logger.info("[Embedding] multilingual-e5-large loaded OK")
            except Exception as e:
                logger.error(f"[Embedding] Không thể load e5-large: {e}")
                raise
        return cls._model

    @classmethod
    def encode(cls, text: str) -> Optional[list]:
        """
        Encode text → dense vector 1024 chiều
        e5-large cần prefix "passage: " cho documents, "query: " cho queries
        Spec UC18 step 2-3: findings + " " + conclusion → vector float32
        """
        if not text or not text.strip():
            return None

        model = cls.get_model()
        # Prefix "passage: " cho document embedding (theo e5 spec)
        # normalize_embeddings=True → cosine similarity = dot product (pattern 6805)
        prefixed = f"passage: {text}"
        vector = model.encode([prefixed], normalize_embeddings=True)[0].tolist()
        return vector

    @classmethod
    def encode_query(cls, text: str) -> Optional[list]:
        """
        Encode query → dense vector 1024 chiều
        e5-large cần prefix "query: " cho search queries
        """
        if not text or not text.strip():
            return None

        model = cls.get_model()
        prefixed = f"query: {text}"
        vector = model.encode([prefixed], normalize_embeddings=True)[0].tolist()
        return vector

    @classmethod
    def encode_batch(cls, texts: list) -> list:
        """Encode nhiều documents cùng lúc (nhanh hơn encode từng cái)"""
        if not texts:
            return []

        model = cls.get_model()
        # Prefix "passage: " cho tất cả documents
        prefixed = [f"passage: {t}" for t in texts]
        vectors = model.encode(prefixed, batch_size=8, normalize_embeddings=True)
        return [vec.tolist() for vec in vectors]

    @classmethod
    def make_report_text(cls, findings: str, conclusion: str) -> str:
        """
        Ghép text báo cáo cho embedding
        Spec UC18 step 2: findings + " " + conclusion
        """
        parts = []
        if findings and findings.strip():
            parts.append(findings.strip())
        if conclusion and conclusion.strip():
            parts.append(conclusion.strip())
        return " ".join(parts)
