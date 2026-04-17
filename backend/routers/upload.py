"""
Upload API Router.
POST /api/upload — upload a CSV or Excel file and run full analysis pipeline.
Reuses the existing EDA, scoring, insights, ML recommendation, bias detection,
and next steps services — no duplicate logic.
"""
from __future__ import annotations
import logging
import uuid
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException, UploadFile, File
from config import settings
from models.schemas import DatasetDetails, DatasetMetrics
from services.eda_engine import run_eda, run_eda_from_dataframe
from services.scoring import score_dataset
from services.insight_generator import generate_insights
from services.ml_recommender import recommend_ml
from services.bias_detector import detect_bias
from services.next_steps import generate_next_steps

logger = logging.getLogger(__name__)
router = APIRouter()

# Max upload size: 200 MB
MAX_UPLOAD_BYTES = 200 * 1024 * 1024

# Allowed extensions
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}


@router.post("/upload", response_model=DatasetDetails)
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload a CSV or Excel file and run the full analysis pipeline.
    Returns the same DatasetDetails format as /api/analyze.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Please upload a CSV (.csv) or Excel (.xlsx, .xls) file.",
        )

    # Read file contents
    try:
        contents = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise HTTPException(status_code=400, detail="Could not read the uploaded file.")

    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {MAX_UPLOAD_BYTES // (1024*1024)} MB.",
        )

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")

    # Generate a unique dataset ID for this upload
    dataset_id = f"upload-{uuid.uuid4().hex[:12]}"
    safe_name = file.filename.replace(" ", "_").replace("/", "_")

    # Save the file to disk
    upload_dir = Path(settings.DOWNLOAD_DIR) / dataset_id
    upload_dir.mkdir(parents=True, exist_ok=True)

    if ext == ".csv":
        csv_path = upload_dir / safe_name
        csv_path.write_bytes(contents)
        csv_path_str = str(csv_path)
    else:
        # Excel: save as xlsx, then convert to CSV for the pipeline
        xlsx_path = upload_dir / safe_name
        xlsx_path.write_bytes(contents)
        try:
            df = pd.read_excel(xlsx_path, nrows=500_000)
            csv_name = safe_name.rsplit(".", 1)[0] + ".csv"
            csv_path = upload_dir / csv_name
            df.to_csv(str(csv_path), index=False)
            csv_path_str = str(csv_path)
            logger.info(f"Converted Excel to CSV: {csv_path_str}")
        except Exception as e:
            logger.error(f"Failed to read Excel file: {e}")
            raise HTTPException(
                status_code=400,
                detail="Could not parse the Excel file. Please ensure it contains valid data.",
            )

    # --- Run the full analysis pipeline (same as /api/analyze) ---

    # 1. EDA
    eda_result = run_eda(csv_path_str)
    if "error" in eda_result:
        raise HTTPException(
            status_code=500,
            detail=f"Could not analyze this file: {eda_result['error']}",
        )

    metrics: DatasetMetrics = eda_result["metrics"]
    correlations = eda_result["correlations"]
    distributions = eda_result["distributions"]
    eda_warnings: list[str] = eda_result.get("warnings", [])

    # 2. Score quality
    quality_score, score_explanation, score_breakdown = score_dataset(metrics)

    # 3. Generate insights
    insights = generate_insights(metrics, correlations, distributions)

    # 4. ML recommendation
    ml_recommendation = recommend_ml(csv_path_str, metrics)

    # 5. Detect bias
    target_col = ml_recommendation.targetColumn if ml_recommendation else None
    bias_warnings = detect_bias(csv_path_str, metrics, target_column=target_col)

    # 6. Generate next steps
    next_steps = generate_next_steps(
        metrics=metrics,
        insights=insights,
        ml_recommendation=ml_recommendation,
        bias_warnings=bias_warnings,
        score_breakdown=score_breakdown,
        quality_score=quality_score,
    )

    # Quality label
    if quality_score >= 70:
        quality_label = "high"
    elif quality_score >= 40:
        quality_label = "medium"
    else:
        quality_label = "low"

    # Build and cache the response
    details = DatasetDetails(
        id=dataset_id,
        title=file.filename or "Uploaded Dataset",
        source="upload",
        format=ext.lstrip("."),
        qualityScore=quality_label,
        metrics=metrics,
        correlations=correlations,
        distributions=distributions,
        mlRecommendation=ml_recommendation,
        insights=insights,
        score=quality_score,
        scoreExplanation=score_explanation,
        scoreBreakdown=score_breakdown,
        biasWarnings=bias_warnings,
        nextSteps=next_steps,
        warnings=eda_warnings,
        size=f"{len(contents) / 1024:.1f} KB" if len(contents) < 1024 * 1024 else f"{len(contents) / (1024*1024):.1f} MB",
        sizeBytes=len(contents),
    )

    # Cache so preprocessing/compare can access it
    from routers.datasets import _analysis_cache
    _analysis_cache[dataset_id] = details

    logger.info(f"Upload analysis complete for '{file.filename}': id={dataset_id}, score={quality_score}")

    return details
