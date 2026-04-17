"""
Advanced Semantic Search & Ranking Engine.
Multi-layer ranking system:
  Layer 1: Concurrent multi-source fetch with query expansion
  Layer 2: Batch semantic embedding + cosine similarity
  Layer 3: Keyword match boosting (title/tags/description)
  Layer 4: Metadata quality scoring (size, recency, format)
  Layer 5: Cross-source deduplication
  Layer 6: Filter application + final sort
"""
from __future__ import annotations
import asyncio
import logging
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Optional

from services.query_processor import (
    normalize_query,
    sanitize_query,
    extract_keywords,
    expand_query,
    detect_intent,
    generate_embedding,
    generate_batch_embeddings,
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


def _batch_cosine_similarity(query_vec: np.ndarray, doc_vecs: np.ndarray) -> np.ndarray:
    """Vectorized cosine similarity — much faster than per-item loop."""
    query_norm = np.linalg.norm(query_vec)
    if query_norm == 0:
        return np.zeros(len(doc_vecs))
    doc_norms = np.linalg.norm(doc_vecs, axis=1)
    doc_norms[doc_norms == 0] = 1.0  # Avoid division by zero
    dots = doc_vecs @ query_vec
    return dots / (doc_norms * query_norm)


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
    Full advanced pipeline:
      1. Query processing — normalize, expand, detect intent
      2. Multi-source concurrent fetch with expanded queries
      3. Cross-source deduplication
      4. Batch semantic embedding + cosine similarity
      5. Multi-factor scoring (semantic + keyword + metadata)
      6. Filter + sort by composite score
    """
    # ─── Layer 1: Query Processing ──────────────────────────────
    normalized = normalize_query(query)
    sanitized = sanitize_query(query)  # Strip domain noise ("dataset", "data", etc.)
    keywords = extract_keywords(query)
    intent = detect_intent(query)
    expanded = expand_query(sanitized, keywords)  # Use sanitized for expansion
    structured = build_structured_queries(normalized, keywords)

    # Build the text to embed: sanitized query + description + expanded terms
    # Using sanitized query gives better semantic embeddings by removing noise
    embed_text = sanitized if sanitized else query
    if description:
        embed_text = f"{embed_text}. {description}"
    if expanded != sanitized:
        embed_text = f"{embed_text}. {expanded}"

    logger.info(f"Search: query='{query}' sanitized='{sanitized}' keywords={keywords} intent={intent}")
    if expanded != sanitized:
        logger.info(f"  Expanded query: '{expanded}'")

    try:
        query_embedding = generate_embedding(embed_text)
    except RuntimeError:
        logger.warning("Model not loaded — falling back to keyword search only")
        query_embedding = None

    # ─── Layer 2: Multi-Source Concurrent Fetch ─────────────────
    # Apply source filter if specified
    active_fetchers = _fetchers
    if filters and filters.source:
        active_fetchers = [f for f in _fetchers if f.source_name in filters.source]

    # Fetch concurrently from all active sources
    source_queries = {
        "kaggle": structured.get("kaggle", normalized),
        "huggingface": structured.get("huggingface", query),
        "github": structured.get("github", normalized),
    }

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

    logger.info(f"Fetched {len(all_datasets)} total datasets before dedup")

    # ─── Layer 3: Cross-Source Deduplication ─────────────────────
    all_datasets = _deduplicate(all_datasets)
    logger.info(f"After dedup: {len(all_datasets)} datasets")

    # ─── Layer 4: Semantic Scoring (Batch) ──────────────────────
    if query_embedding is not None:
        # Build description texts for batch embedding
        desc_texts = [
            f"{ds.title}. {ds.description}" for ds in all_datasets
        ]

        try:
            # Batch embed — much faster than one-by-one
            desc_embeddings = generate_batch_embeddings(desc_texts)
            semantic_scores = _batch_cosine_similarity(query_embedding, desc_embeddings)
        except Exception as e:
            logger.warning(f"Batch embedding failed, falling back to per-item: {e}")
            semantic_scores = np.array([
                _safe_embedding_score(query_embedding, ds) for ds in all_datasets
            ])
    else:
        semantic_scores = np.zeros(len(all_datasets))

    # ─── Layer 5: Multi-Factor Composite Scoring ─────────────────
    for i, ds in enumerate(all_datasets):
        # Semantic similarity score (0-100), weight = 50%
        semantic_score = max(0, min(100, float(semantic_scores[i]) * 100))

        # Keyword match score (0-100), weight = 25%
        keyword_score = _compute_keyword_score(ds, keywords, query)

        # Metadata quality score (0-100), weight = 15%
        metadata_score = _compute_metadata_score(ds)

        # Intent match bonus (0-100), weight = 10%
        intent_score = _compute_intent_score(ds, intent) if intent else 0

        # Weighted composite score
        composite = (
            semantic_score * 0.50
            + keyword_score * 0.25
            + metadata_score * 0.15
            + intent_score * 0.10
        )

        # ── Minimum relevance floor ──
        # These datasets were already returned by source-specific search APIs,
        # so they have SOME relevance. Showing 0% is misleading.

        # Floor 1: Every result gets at least 12% (source API thought it was relevant)
        if composite < 12:
            composite = 12.0

        # Floor 2: If any keyword matches title/tags/desc, at least 20%
        if keyword_score > 0 and composite < 20:
            composite = 20.0

        # Floor 3: If the original query appears in the title, at least 35%
        if query.lower().strip() in ds.title.lower() and composite < 35:
            composite = 35.0

        ds.relevanceScore = round(max(0, min(100, composite)), 1)

    # ─── Layer 6: Quality Score Assignment ──────────────────────
    for ds in all_datasets:
        if ds.relevanceScore >= 75:
            ds.qualityScore = "high"
        elif ds.relevanceScore >= 45:
            ds.qualityScore = "medium"
        else:
            ds.qualityScore = "low"

    # ─── Layer 7: Filter + Sort ─────────────────────────────────
    all_datasets = _apply_filters(all_datasets, filters)
    all_datasets.sort(key=lambda d: d.relevanceScore, reverse=True)

    return all_datasets


# ── Scoring Helpers ─────────────────────────────────────────────

def _safe_embedding_score(query_emb: np.ndarray, ds: Dataset) -> float:
    """Compute embedding score with error handling."""
    try:
        desc_emb = generate_embedding(f"{ds.title}. {ds.description}")
        return _cosine_similarity(query_emb, desc_emb)
    except Exception:
        return 0.5


def _compute_keyword_score(ds: Dataset, keywords: list[str], original_query: str) -> float:
    """
    Multi-level keyword matching:
      - Exact title match: highest boost
      - Title keyword match: high boost
      - Tag match: medium boost
      - Description match: lower boost
    """
    if not keywords:
        return 50.0

    score = 0.0
    title_lower = ds.title.lower()
    desc_lower = ds.description.lower()
    tags_lower = " ".join(t.lower() for t in (ds.tags or []))

    # Exact query in title → huge boost
    if original_query.lower() in title_lower:
        score += 40.0

    # Per-keyword matching
    for kw in keywords:
        kw_lower = kw.lower()
        # Title keyword match (highest value)
        if kw_lower in title_lower:
            score += 15.0
        # Tag match (high value — tags are curated)
        if kw_lower in tags_lower:
            score += 12.0
        # Description match (moderate)
        if kw_lower in desc_lower:
            score += 5.0

    # Normalize by number of keywords
    max_possible = 40 + len(keywords) * 32  # max per keyword = 15+12+5
    normalized = (score / max_possible) * 100 if max_possible > 0 else 0

    return min(100, normalized)


def _compute_metadata_score(ds: Dataset) -> float:
    """
    Score based on metadata quality indicators:
      - Has description: +20
      - Has tags: +20
      - Has known size: +15
      - Has author: +10
      - Has license: +10
      - Recency bonus: up to +25
    """
    score = 0.0

    if ds.description and len(ds.description) > 20:
        score += 20
    if ds.tags and len(ds.tags) >= 2:
        score += 20
    if ds.sizeBytes > 0:
        score += 15
    if ds.author and ds.author != "Unknown":
        score += 10
    if ds.license and ds.license != "Unknown":
        score += 10

    # Recency bonus (up to 25 pts)
    if ds.lastUpdated:
        try:
            updated = datetime.fromisoformat(ds.lastUpdated.replace("Z", "+00:00"))
            days_old = (datetime.now(timezone.utc) - updated).days
            if days_old <= 30:
                score += 25
            elif days_old <= 90:
                score += 20
            elif days_old <= 365:
                score += 10
            else:
                score += 5
        except (ValueError, TypeError):
            score += 5

    return score


def _compute_intent_score(ds: Dataset, intent: str) -> float:
    """Score how well the dataset matches the detected search intent."""
    text = f"{ds.title} {ds.description} {' '.join(ds.tags or [])}".lower()

    # Direct intent word match
    if intent.lower() in text:
        return 80.0

    # Partial / related match
    intent_related = {
        "prediction": ["predict", "forecast", "estimate", "regression"],
        "classification": ["classify", "class", "label", "category", "binary"],
        "detection": ["detect", "anomaly", "fraud", "intrusion", "spam"],
        "forecasting": ["forecast", "time series", "trend", "seasonal", "temporal"],
        "segmentation": ["segment", "cluster", "group", "partition"],
        "recommendation": ["recommend", "collaborative", "preference", "rating"],
        "clustering": ["cluster", "unsupervised", "group", "segment"],
        "analysis": ["analyze", "exploration", "insight", "statistics"],
        "comparison": ["compare", "benchmark", "versus", "contrast"],
    }

    related = intent_related.get(intent, [])
    matches = sum(1 for r in related if r in text)
    if matches > 0:
        return min(100, matches * 25)

    return 0.0


# ── Deduplication ───────────────────────────────────────────────

def _deduplicate(datasets: list[Dataset]) -> list[Dataset]:
    """
    Remove duplicate datasets across sources.
    Uses normalized title similarity as the key.
    Keeps the version with the highest relevance score or more metadata.
    """
    seen: dict[str, Dataset] = {}

    for ds in datasets:
        # Create a dedup key from normalized title
        key = _normalize_for_dedup(ds.title)

        if key in seen:
            existing = seen[key]
            # Keep the one with more metadata
            existing_meta = _metadata_richness(existing)
            new_meta = _metadata_richness(ds)
            if new_meta > existing_meta:
                seen[key] = ds
        else:
            seen[key] = ds

    return list(seen.values())


def _normalize_for_dedup(title: str) -> str:
    """Normalize title for deduplication comparison."""
    import re
    text = title.lower().strip()
    # Remove common suffixes like "dataset", "data", "(kaggle)", etc.
    text = re.sub(r"\b(dataset|data|csv|kaggle|huggingface|github)\b", "", text)
    text = re.sub(r"[^a-z0-9]", "", text)
    return text


def _metadata_richness(ds: Dataset) -> int:
    """Score how much metadata a dataset entry has."""
    score = 0
    if ds.description and len(ds.description) > 20:
        score += 2
    if ds.tags and len(ds.tags) > 0:
        score += 1
    if ds.sizeBytes > 0:
        score += 1
    if ds.author and ds.author != "Unknown":
        score += 1
    if ds.source == "kaggle":
        score += 1  # Prefer Kaggle (downloadable)
    return score


# ── Filters ─────────────────────────────────────────────────────

def _apply_filters(datasets: list[Dataset], filters: Optional[SearchFilters]) -> list[Dataset]:
    """Apply frontend-compatible filters to dataset list."""
    if not filters:
        return datasets

    result = datasets

    # Format filter
    if filters.format:
        result = [d for d in result if d.format in filters.format]

    # Quality filter (assigned before this step)
    if filters.quality:
        result = [d for d in result if d.qualityScore in filters.quality]

    # Size filter
    if filters.size and filters.size != "all":
        result = [d for d in result if _matches_size(d, filters.size)]

    # Freshness filter
    if filters.freshness and filters.freshness != "all":
        result = [d for d in result if _matches_freshness(d, filters.freshness)]

    # Source filter (already handled by active_fetchers, but belt+suspenders)
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
        updated = datetime.fromisoformat(dataset.lastUpdated.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        days_map = {"day": 1, "week": 7, "month": 30, "year": 365}
        max_days = days_map.get(freshness)
        if max_days is None:
            return True
        return (now - updated).days <= max_days
    except Exception:
        return True
