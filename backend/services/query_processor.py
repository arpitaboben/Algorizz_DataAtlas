"""
Advanced Query Processing Engine.
- Normalizes natural language queries
- Expands queries with synonyms and domain terms
- Extracts keywords with TF-IDF-like weighting
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

# Domain synonym expansion map — query expansion for better recall
_QUERY_EXPANSIONS = {
    # ML/AI terms
    "classification": ["classifier", "labeled", "categories", "classes", "predict label"],
    "regression": ["prediction", "continuous", "numeric", "forecast", "estimate value"],
    "clustering": ["unsupervised", "grouping", "segmentation", "cluster analysis"],
    "nlp": ["text", "natural language", "sentiment", "language model", "tokenization"],
    "computer vision": ["image", "object detection", "cnn", "visual recognition"],
    "time series": ["temporal", "sequential", "forecast", "time-series", "trend analysis"],
    # Domain terms
    "healthcare": ["medical", "clinical", "patient", "hospital", "disease", "health"],
    "medical": ["healthcare", "clinical", "patient", "diagnosis", "treatment"],
    "finance": ["financial", "stock", "market", "trading", "banking", "economic"],
    "stock": ["financial", "market", "trading", "equity", "shares", "stock price"],
    "weather": ["climate", "meteorological", "temperature", "atmospheric", "forecast"],
    "climate": ["weather", "environmental", "temperature", "greenhouse", "emissions"],
    "sales": ["revenue", "commerce", "retail", "ecommerce", "transactions", "marketing"],
    "housing": ["real estate", "property", "home", "residential", "house price"],
    "fraud": ["anomaly detection", "suspicious", "financial crime", "identity theft"],
    "spam": ["email", "text classification", "phishing", "unwanted messages"],
    "sentiment": ["opinion", "review", "emotion", "polarity", "text analysis"],
    "recommendation": ["collaborative filtering", "content-based", "user preferences"],
    "sports": ["athletics", "game", "player", "team", "competition", "score"],
    "education": ["academic", "student", "school", "learning", "curriculum"],
    "agriculture": ["farming", "crop", "soil", "yield", "agricultural"],
    "energy": ["power", "electricity", "renewable", "solar", "wind", "consumption"],
    "iot": ["sensor", "device", "smart", "connected", "telemetry", "internet of things"],
    "autonomous": ["self-driving", "vehicle", "robotics", "navigation"],
    "cybersecurity": ["security", "threat", "attack", "vulnerability", "intrusion"],
    # Data format hints
    "tabular": ["csv", "structured", "table", "spreadsheet", "rows and columns"],
    "image": ["images", "pictures", "photos", "visual", "pixel"],
    "text": ["nlp", "corpus", "documents", "articles", "reviews"],
}

# Intent detection patterns — understand what user wants
_INTENT_PATTERNS = {
    "predict": "prediction",
    "forecast": "forecasting",
    "classify": "classification",
    "detect": "detection",
    "segment": "segmentation",
    "recommend": "recommendation",
    "cluster": "clustering",
    "analyze": "analysis",
    "compare": "comparison",
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


def expand_query(query: str, keywords: list[str]) -> str:
    """
    Expand the query with domain synonyms and related terms.
    This improves recall by matching datasets that use different terminology.
    """
    expanded_terms = set()
    query_lower = query.lower()

    for term, synonyms in _QUERY_EXPANSIONS.items():
        if term in query_lower or any(kw == term for kw in keywords):
            # Add top 2 synonyms to avoid over-expansion
            expanded_terms.update(synonyms[:2])

    if expanded_terms:
        # Remove terms already in the query
        new_terms = [t for t in expanded_terms if t.lower() not in query_lower]
        if new_terms:
            return f"{query} {' '.join(new_terms[:4])}"

    return query


def detect_intent(query: str) -> str | None:
    """Detect the user's intent from the query to boost relevance."""
    query_lower = query.lower()
    for pattern, intent in _INTENT_PATTERNS.items():
        if pattern in query_lower:
            return intent
    return None


def generate_embedding(text: str) -> np.ndarray:
    """Generate a semantic embedding vector for the given text."""
    model = get_model()
    embedding = model.encode(text, convert_to_numpy=True)
    return embedding


def generate_batch_embeddings(texts: list[str]) -> np.ndarray:
    """
    Generate embeddings for multiple texts at once — much faster than one-by-one.
    Returns a 2D array of shape (len(texts), embedding_dim).
    """
    model = get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, batch_size=32, show_progress_bar=False)
    return embeddings


def build_structured_queries(query: str, keywords: list[str]) -> dict[str, str]:
    """
    Build platform-specific search strings.
    Each platform has slightly different optimal query formats.
    """
    keyword_str = " ".join(keywords)
    intent = detect_intent(query)

    # Build enhanced Kaggle query
    kaggle_query = keyword_str
    if intent:
        kaggle_query = f"{keyword_str} {intent}"

    return {
        "kaggle": kaggle_query,
        "huggingface": query,   # HuggingFace handles natural language well
        "github": f"{keyword_str} dataset csv",  # GitHub needs explicit pointers
    }
