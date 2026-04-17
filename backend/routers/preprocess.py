"""
Preprocessing API Router.
POST /api/preprocess — apply preprocessing pipeline to an analyzed dataset.
GET  /api/preprocess/download/{filename} — download a cleaned CSV file.
"""
from __future__ import annotations
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from models.schemas import PreprocessRequest, PreprocessResponse
from services.preprocessing import apply_pipeline, get_cleaned_csv_path
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/preprocess", response_model=PreprocessResponse)
async def preprocess_dataset(request: PreprocessRequest):
    """
    Apply preprocessing steps to a previously-analyzed dataset.
    The dataset must have been analyzed via /api/analyze first.
    """
    from routers.datasets import _analysis_cache

    dataset_id = request.dataset_id

    if dataset_id not in _analysis_cache:
        raise HTTPException(
            status_code=404,
            detail="Dataset not yet analyzed. Please analyze it first via /api/analyze.",
        )

    dataset = _analysis_cache[dataset_id]

    # Find the original CSV path
    # The CSV was downloaded to downloads/{dataset_id}/
    download_dir = Path(settings.DOWNLOAD_DIR) / dataset_id
    csv_path = None

    if download_dir.exists():
        for f in download_dir.rglob("*.csv"):
            if f.stat().st_size > 0:
                csv_path = str(f)
                break

    if csv_path is None:
        raise HTTPException(
            status_code=404,
            detail="Original CSV file not found. Please re-analyze the dataset.",
        )

    if not request.steps:
        raise HTTPException(
            status_code=400,
            detail="At least one preprocessing step is required.",
        )

    try:
        result = apply_pipeline(csv_path, dataset_id, request.steps)
        return result
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Preprocessing encountered an error. Please try different settings or re-analyze the dataset.",
        )


@router.get("/preprocess/download/{filename}")
async def download_cleaned_dataset(filename: str):
    """Download a cleaned CSV file."""
    clean_path = get_cleaned_csv_path("", filename)

    if clean_path is None:
        # Try direct lookup
        direct_path = Path(settings.DOWNLOAD_DIR) / "cleaned" / filename
        if direct_path.exists():
            clean_path = str(direct_path)
        else:
            raise HTTPException(
                status_code=404,
                detail="Cleaned file not found.",
            )

    return FileResponse(
        path=clean_path,
        media_type="text/csv",
        filename=filename,
    )
