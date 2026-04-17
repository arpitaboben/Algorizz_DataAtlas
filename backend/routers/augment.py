"""
Augmentation API Router.
POST /api/augment — augment an analyzed dataset (SMOTE or bootstrap).
GET  /api/augment/download/{filename} — download augmented CSV.
"""
from __future__ import annotations
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Any

from config import settings
from services.augmentation import augment_dataset

logger = logging.getLogger(__name__)
router = APIRouter()


class AugmentRequest(BaseModel):
    dataset_id: str
    target_column: str
    task_type: str = "classification"  # 'classification' or 'regression'
    method: str = "auto"               # 'smote', 'bootstrap', or 'auto'


class AugmentResponse(BaseModel):
    success: bool = True
    method_used: str = ""
    before: dict[str, Any] = {}
    after: dict[str, Any] = {}
    rows_added: int = 0
    download_filename: str = ""
    summary: str = ""


@router.post("/augment", response_model=AugmentResponse)
async def augment_dataset_endpoint(request: AugmentRequest):
    """
    Augment a previously-analyzed dataset.
    Supports SMOTE (classification) and bootstrap+noise (regression).
    """
    from routers.datasets import _analysis_cache

    if request.dataset_id not in _analysis_cache:
        raise HTTPException(
            status_code=404,
            detail="Dataset not yet analyzed. Please analyze it first.",
        )

    # Find the CSV path
    download_dir = Path(settings.DOWNLOAD_DIR) / request.dataset_id
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

    try:
        result = augment_dataset(
            csv_path=csv_path,
            target_column=request.target_column,
            task_type=request.task_type,
            method=request.method,
        )
        return AugmentResponse(**result)
    except Exception as e:
        logger.error(f"Augmentation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Augmentation encountered an error. Please try a different method or target column.",
        )


@router.get("/augment/download/{filename}")
async def download_augmented_dataset(filename: str):
    """Download an augmented CSV file."""
    aug_path = Path(settings.DOWNLOAD_DIR) / "augmented" / filename
    if not aug_path.exists():
        raise HTTPException(status_code=404, detail="Augmented file not found.")

    return FileResponse(
        path=str(aug_path),
        media_type="text/csv",
        filename=filename,
    )
