"""
Query Processing Engine.
- Normalizes natural language queries
- Extracts keywords
- Generates semantic embeddings via sentence-transformers
- Builds platform-specific structured queries
"""
from __future__ import annotations
import re
import numpy as np
from typing import Optional

# Lazy-loaded model reference (loaded once by lifespan handler in main.py)
_model = None
_STOP_WORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "because", "but", "and", "or", "if", "while", "about",
    "i", "me", "my", "we", "our", "you", "your", "he", "him", "his",
    "she", "her", "it", "its", "they", "them", "their", "what", "which",
    "who", "whom", "this", "that", "these", "those", "am", "dataset",
    "data", "find", "search", "looking", "want", "get", "show", "give",
}


def set_model(model) -> None:
    """Set the shared sentence-transformer model (called from main.py lifespan)."""
    global _model
    _model = model


def get_model():
    """Return the loaded model, raising if not initialized."""
    if _model is None:
        raise RuntimeError("Embedding model not loaded yet. Wait for server startup.")
    return _model


def normalize_query(query: str) -> str:
    """Lowercase, strip special chars, collapse whitespace."""
    text = query.lower().strip()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_keywords(query: str) -> list[str]:
    """Extract meaningful keywords by removing stop words."""
    normalized = normalize_query(query)
    words = normalized.split()
    keywords = [w for w in words if w not in _STOP_WORDS and len(w) > 1]
    return keywords if keywords else words[:5]  # fallback to first 5 words


def generate_embedding(text: str) -> np.ndarray:
    """Generate a semantic embedding vector for the given text."""
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding


def build_structured_queries(query: str, keywords: list[str]) -> dict[str, str]:
    """
    Build platform-specific search strings.
    Each platform has slightly different optimal query formats.
    """
    keyword_str = " ".join(keywords)

    return {
        "kaggle": keyword_str,  # Kaggle search works well with keywords
        "huggingface": query,   # HuggingFace handles natural language well
        "github": f"{keyword_str} dataset csv",  # GitHub needs explicit pointers
    }
