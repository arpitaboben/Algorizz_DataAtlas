"""
Search API Router.
POST /api/search — full pipeline: query processing → multi-source fetch → semantic rank.
"""
from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException
from models.schemas import SearchRequest, SearchResponse
from services.search_engine import search_datasets

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Search datasets across all available sources (Kaggle, HuggingFace, GitHub).

    Accepts a natural language query, optional description for semantic boost,
    and filters. Returns datasets ranked by semantic relevance.
    """
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Please enter a search query.")

    try:
        datasets = await search_datasets(
            query=request.query,
            description=request.description,
            filters=request.filters,
            limit_per_source=request.limit,
        )

        # Paginate
        total = len(datasets)
        total_pages = max(1, -(-total // request.limit))  # ceil division
        start = (request.page - 1) * request.limit
        end = start + request.limit
        page_datasets = datasets[start:end]

        return SearchResponse(
            datasets=page_datasets,
            total=total,
            page=request.page,
            totalPages=total_pages,
        )

    except Exception as e:
        logger.error(f"Search error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Search encountered an error. Please try a different query or check that the backend services are running.",
        )
