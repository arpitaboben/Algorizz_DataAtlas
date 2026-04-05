"""
Semantic Search & Ranking Engine.
- Fetches dataset metadata from ALL available sources (Kaggle, HuggingFace, GitHub)
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
from services.fetchers.huggingface_fetcher import HuggingFaceFetcher
from services.fetchers.github_fetcher import GitHubFetcher
from models.schemas import Dataset, SearchFilters

logger = logging.getLogger(__name__)

# All data source fetchers
_fetchers = [
    KaggleFetcher(),
    HuggingFaceFetcher(),
    GitHubFetcher(),
]


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


async def _fetch_from_source(fetcher, query: str, limit: int) -> list[Dataset]:
    """Fetch from a single source with error handling."""
    try:
        if not await fetcher.is_available():
            logger.info(f"{fetcher.source_name}: skipped (not available)")
            return []
        results = await fetcher.fetch(query, limit)
        logger.info(f"{fetcher.source_name}: returned {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"{fetcher.source_name}: fetch error: {e}")
        return []


async def search_datasets(
    query: str,
    description: Optional[str] = None,
    filters: Optional[SearchFilters] = None,
    limit_per_source: int = 15,
) -> list[Dataset]:
    """
    Full pipeline: query processing → multi-source fetch → semantic ranking.
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

    # 2. Fetch from ALL sources concurrently
    # Build source-specific queries
    source_queries = {
        "kaggle": structured.get("kaggle", normalized),
        "huggingface": structured.get("huggingface", query),
        "github": structured.get("github", normalized),
    }

    # Apply source filter if specified
    active_fetchers = _fetchers
    if filters and filters.source:
        active_fetchers = [f for f in _fetchers if f.source_name in filters.source]

    # Fetch concurrently from all active sources
    tasks = [
        _fetch_from_source(
            fetcher,
            source_queries.get(fetcher.source_name, normalized),
            limit_per_source,
        )
        for fetcher in active_fetchers
    ]

    results = await asyncio.gather(*tasks)

    # Merge all results
    all_datasets: list[Dataset] = []
    for source_results in results:
        all_datasets.extend(source_results)

    if not all_datasets:
        logger.warning("No datasets found from any source")
        return []

    # 3. Compute semantic relevance scores
    if query_embedding is not None:
        for ds in all_datasets:
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
        for ds in all_datasets:
            matches = sum(
                1 for kw in keywords
                if kw in ds.title.lower() or kw in ds.description.lower()
            )
            ds.relevanceScore = round(min(100, (matches / max(len(keywords), 1)) * 100), 1)

    # 4. Assign quality scores BEFORE filtering (Fix #6)
    for ds in all_datasets:
        if ds.relevanceScore >= 80:
            ds.qualityScore = "high"
        elif ds.relevanceScore >= 50:
            ds.qualityScore = "medium"
        else:
            ds.qualityScore = "low"

    # 5. Apply filters (quality filter now works correctly)
    all_datasets = _apply_filters(all_datasets, filters)

    # 6. Sort by relevance
    all_datasets.sort(key=lambda d: d.relevanceScore, reverse=True)

    return all_datasets


def _apply_filters(datasets: list[Dataset], filters: Optional[SearchFilters]) -> list[Dataset]:
    """Apply frontend-compatible filters to dataset list."""
    if not filters:
        return datasets

    result = datasets

    # Format filter
    if filters.format:
        result = [d for d in result if d.format in filters.format]

    # Quality filter (now works because quality is assigned before this)
    if filters.quality:
        result = [d for d in result if d.qualityScore in filters.quality]

    # Size filter
    if filters.size and filters.size != "all":
        result = [d for d in result if _matches_size(d, filters.size)]

    # Freshness filter
    if filters.freshness and filters.freshness != "all":
        result = [d for d in result if _matches_freshness(d, filters.freshness)]

    # Source filter is already handled above (active_fetchers), but
    # double-check here for safety
    if filters.source:
        result = [d for d in result if d.source in filters.source]

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
