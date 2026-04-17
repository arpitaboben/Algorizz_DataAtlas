"""
Comparison API Router.
POST /api/compare — compare 2 analyzed datasets side-by-side.
"""
from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException
from models.schemas import CompareRequest, ComparisonResult

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/compare", response_model=ComparisonResult)
async def compare_datasets_endpoint(request: CompareRequest):
    """
    Compare two previously-analyzed datasets.
    Both datasets must have been analyzed via /api/analyze first.
    """
    if len(request.dataset_ids) != 2:
        raise HTTPException(
            status_code=400,
            detail="Exactly 2 dataset IDs are required for comparison."
        )

    # Import the cache from datasets router
    from routers.datasets import _analysis_cache
    from services.comparison import compare_datasets

    # Look up both datasets
    missing_ids = [did for did in request.dataset_ids if did not in _analysis_cache]
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Dataset(s) not yet analyzed: {', '.join(missing_ids)}. "
                f"Please analyze both datasets first via /api/analyze."
            ),
        )

    dataset_a = _analysis_cache[request.dataset_ids[0]]
    dataset_b = _analysis_cache[request.dataset_ids[1]]

    try:
        result = compare_datasets(dataset_a, dataset_b)
        return result
    except Exception as e:
        logger.error(f"Comparison failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Comparison encountered an error. Please ensure both datasets have been analyzed."
        )
