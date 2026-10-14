"""
WitnessIQ Semantic Similarity Module

Uses sentence-transformers (all-MiniLM-L6-v2) to embed sentences and compute
cosine similarity.  Falls back to TF-IDF cosine similarity if the model cannot
be loaded.

IMPORTANT: Similarity scores indicate linguistic relatedness, NOT factual
consistency. Two sentences may be similar in meaning and still describe
different times or people.
"""
import logging
import math
import re
from collections import Counter
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)

# ─── Model loading (lazy, cached) ────────────────────────────────────────────

_sentence_model = None
_model_available = False
_model_checked = False
_model_name = "all-MiniLM-L6-v2"


def _load_sentence_model():
    global _sentence_model, _model_available, _model_checked
    if _model_checked:
        return _sentence_model, _model_available
    try:
        from sentence_transformers import SentenceTransformer
        _sentence_model = SentenceTransformer(_model_name)
        _model_available = True
        _model_checked = True
        logger.info("Sentence-transformer model '%s' loaded.", _model_name)
    except Exception as exc:
        logger.warning("Could not load sentence-transformer: %s. Using TF-IDF fallback.", exc)
        _sentence_model = None
        _model_available = False
        _model_checked = True
    return _sentence_model, _model_available


def get_model_status() -> Dict[str, Any]:
    _, available = _load_sentence_model()
    return {
        "sentence_transformer": {
            "available": available,
            "model_name": _model_name if available else None,
            "fallback": "TF-IDF cosine similarity" if not available else None,
            "threshold": 0.50 if available else 0.25,
        }
    }


# ─── Embedding ────────────────────────────────────────────────────────────────

def _embed_sentences_transformer(sentences: List[str]) -> List[List[float]]:
    model, _ = _load_sentence_model()
    vectors = model.encode(sentences, convert_to_numpy=True, show_progress_bar=False)
    return vectors.tolist()


def _embed_sentences_tfidf(sentences: List[str]) -> List[List[float]]:
    """Build lightweight TF-IDF vectors without native numerical dependencies."""
    tokenized = [
        re.findall(r"\b[a-z0-9']+\b", sentence.lower())
        for sentence in sentences
    ]
    stop_words = {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
        "had", "has", "have", "he", "her", "his", "i", "in", "into", "is",
        "it", "me", "my", "of", "on", "or", "our", "she", "that", "the",
        "their", "them", "there", "they", "this", "to", "was", "we", "were",
        "when", "while", "with", "you",
    }
    tokenized = [[word for word in words if word not in stop_words] for words in tokenized]
    documents = [
        words + [f"{words[i]} {words[i + 1]}" for i in range(len(words) - 1)]
        for words in tokenized
    ]
    document_frequency = Counter(
        term for document in documents for term in set(document)
    )
    vocabulary = sorted(document_frequency)
    if not vocabulary:
        return [[] for _ in sentences]

    vectors = []
    document_count = len(documents)
    for document in documents:
        term_frequency = Counter(document)
        vectors.append([
            (1 + math.log(term_frequency[term]))
            * (math.log((1 + document_count) / (1 + document_frequency[term])) + 1)
            if term_frequency[term]
            else 0.0
            for term in vocabulary
        ])
    return vectors


def embed_sentences(sentences: List[str]) -> Tuple[List[List[float]], str]:
    """
    Returns (embedding_matrix, method_used).
    Shape: (n_sentences, embedding_dim)
    """
    _, available = _load_sentence_model()
    if available:
        embeddings = _embed_sentences_transformer(sentences)
        return embeddings, "sentence_transformer"
    else:
        embeddings = _embed_sentences_tfidf(sentences)
        return embeddings, "tfidf_cosine"


# ─── Cosine similarity ────────────────────────────────────────────────────────

def cosine_similarity_matrix(
    a: List[List[float]],
    b: List[List[float]],
) -> List[List[float]]:
    """Compute pairwise cosine similarity between two vector collections."""
    similarities = []
    for vector_a in a:
        row = []
        for vector_b in b:
            dot_product = sum(x * y for x, y in zip(vector_a, vector_b))
            norm_a = math.sqrt(sum(x * x for x in vector_a))
            norm_b = math.sqrt(sum(y * y for y in vector_b))
            row.append(dot_product / (norm_a * norm_b) if norm_a and norm_b else 0.0)
        similarities.append(row)
    return similarities


# ─── Find semantically similar sentence pairs ─────────────────────────────────

def find_similar_pairs(
    sentences_a: List[str],
    sentences_b: List[str],
    threshold: float = 0.55,
) -> List[Dict[str, Any]]:
    """
    Returns a list of sentence pairs with similarity >= threshold.
    Each pair has indices into sentences_a and sentences_b plus the score.

    NOTE: similarity >= threshold only suggests the sentences may be topically
    related. It does not mean they are factually consistent.
    """
    if not sentences_a or not sentences_b:
        return []

    all_sentences = sentences_a + sentences_b
    embeddings, method = embed_sentences(all_sentences)

    emb_a = embeddings[: len(sentences_a)]
    emb_b = embeddings[len(sentences_a) :]

    sim_matrix = cosine_similarity_matrix(emb_a, emb_b)

    pairs = []
    for i, row in enumerate(sim_matrix):
        for j, score in enumerate(row):
            if float(score) >= threshold:
                pairs.append({
                    "index_a": i,
                    "index_b": j,
                    "sentence_a": sentences_a[i],
                    "sentence_b": sentences_b[j],
                    "similarity_score": round(float(score), 4),
                    "method": method,
                })

    # Sort by similarity descending
    pairs.sort(key=lambda p: p["similarity_score"], reverse=True)
    return pairs
