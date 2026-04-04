"""
Semantic Search & Ranking Engine.
- Fetches dataset metadata from Kaggle
- Embeds all fetched dataset descriptions
- Computes cosine similarity against user query embedding
- Ranks results by semantic relevance
- Applies frontend-compatible filters
"""
from __future__ import annotations
import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Optional

from services.query_processor import (
    normalize_query,
    extract_keywords,
    generate_embedding,
    build_structured_queries,
)
from services.fetchers.kaggle_fetcher import KaggleFetcher
from models.schemas import Dataset, SearchFilters

logger = logging.getLogger(__name__)

# Kaggle is the primary data source
_kaggle_fetcher = KaggleFetcher()


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


async def search_datasets(
    query: str,
    description: Optional[str] = None,
    filters: Optional[SearchFilters] = None,
    limit_per_source: int = 15,
) -> list[Dataset]:
    """
    Full pipeline: query processing → Kaggle fetch → semantic ranking.
    Returns datasets sorted by relevance score.
    """
    # 1. Process query
    normalized = normalize_query(query)
    keywords = extract_keywords(query)
    structured = build_structured_queries(normalized, keywords)

    # Combine query + description for embedding
    embed_text = query
    if description:
        embed_text = f"{query}. {description}"

    try:
        query_embedding = generate_embedding(embed_text)
    except RuntimeError:
        logger.warning("Model not loaded — falling back to keyword search only")
        query_embedding = None

    # 2. Fetch from Kaggle
    kaggle_query = structured.get("kaggle", normalized)

    try:
        datasets = await _kaggle_fetcher.fetch(kaggle_query, limit_per_source)
    except Exception as e:
        logger.error(f"Kaggle fetch error: {e}", exc_info=True)
        datasets = []

    if not datasets:
        return []

    # 3. Compute semantic relevance scores
    if query_embedding is not None:
        for ds in datasets:
            desc_text = f"{ds.title}. {ds.description}"
            try:
                desc_embedding = generate_embedding(desc_text)
                similarity = _cosine_similarity(query_embedding, desc_embedding)
                # Scale to 0-100
                ds.relevanceScore = round(max(0, min(100, similarity * 100)), 1)
            except Exception:
                ds.relevanceScore = 50.0  # Default score if embedding fails
    else:
        # Fallback: keyword matching score
        for ds in datasets:
            matches = sum(
                1 for kw in keywords
                if kw in ds.title.lower() or kw in ds.description.lower()
            )
            ds.relevanceScore = round(min(100, (matches / max(len(keywords), 1)) * 100), 1)

    # 4. Apply filters
    datasets = _apply_filters(datasets, filters)

    # 5. Assign quality scores based on available info
    for ds in datasets:
        if ds.relevanceScore >= 80:
            ds.qualityScore = "high"
        elif ds.relevanceScore >= 50:
            ds.qualityScore = "medium"
        else:
            ds.qualityScore = "low"

    # 6. Sort by relevance
    datasets.sort(key=lambda d: d.relevanceScore, reverse=True)

    return datasets


def _apply_filters(datasets: list[Dataset], filters: Optional[SearchFilters]) -> list[Dataset]:
    """Apply frontend-compatible filters to dataset list."""
    if not filters:
        return datasets

    result = datasets

    # Format filter
    if filters.format:
        result = [d for d in result if d.format in filters.format]

    # Quality filter
    if filters.quality:
        result = [d for d in result if d.qualityScore in filters.quality]

    # Size filter
    if filters.size and filters.size != "all":
        result = [d for d in result if _matches_size(d, filters.size)]

    # Freshness filter
    if filters.freshness and filters.freshness != "all":
        result = [d for d in result if _matches_freshness(d, filters.freshness)]

    return result


def _matches_size(dataset: Dataset, size_category: str) -> bool:
    """Check if dataset matches size category."""
    b = dataset.sizeBytes
    if b == 0:
        return True  # Unknown size, include
    if size_category == "small":
        return b < 10 * 1024 * 1024          # < 10MB
    elif size_category == "medium":
        return 10 * 1024 * 1024 <= b < 1024 * 1024 * 1024  # 10MB – 1GB
    elif size_category == "large":
        return b >= 1024 * 1024 * 1024        # >= 1GB
    return True


def _matches_freshness(dataset: Dataset, freshness: str) -> bool:
    """Check if dataset was updated within the freshness window."""
    if not dataset.lastUpdated:
        return True  # Unknown date, include

    try:
        # Try parsing ISO format
        updated = datetime.fromisoformat(dataset.lastUpdated.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_map = {"day": 1, "week": 7, "month": 30, "year": 365}
        max_days = days_map.get(freshness)
        if max_days is None:
            return True
        return (now - updated).days <= max_days
    except Exception:
        return True
