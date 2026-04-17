"""
Dataset API Router.
- POST /api/analyze — downloads CSV via Kaggle SDK, runs EDA + scoring + insights + ML recommendation
- GET  /api/dataset/{dataset_id} — returns cached analysis results
"""
from __future__ import annotations
import logging
from fastapi import APIRouter, HTTPException
from models.schemas import AnalyzeRequest, DatasetDetails, DatasetMetrics
from services.eda_engine import download_kaggle_dataset, run_eda
from services.scoring import score_dataset
from services.insight_generator import generate_insights
from services.ml_recommender import recommend_ml
from services.bias_detector import detect_bias
from services.next_steps import generate_next_steps

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory cache for analyzed datasets (MVP — replace with DB/Redis in production)
_analysis_cache: dict[str, DatasetDetails] = {}


@router.post("/analyze", response_model=DatasetDetails)
async def analyze_dataset(request: AnalyzeRequest):
    """
    Full analysis pipeline triggered when user clicks on a dataset:
    1. Download the CSV file via Kaggle API
    2. Run EDA (stats, missing, duplicates, correlations, distributions)
    3. Score dataset quality (0-100) with breakdown
    4. Generate structured, actionable insights
    5. Recommend ML task, models, and use cases
    6. Detect data bias and fairness issues
    7. Generate prioritized next steps
    """
    dataset_id = request.dataset_id

    # Check cache first
    if dataset_id in _analysis_cache:
        logger.info(f"Returning cached analysis for {dataset_id}")
        return _analysis_cache[dataset_id]

    # 1. Download CSV via Kaggle SDK
    # download_url contains the Kaggle ref (e.g. "username/dataset-slug")
    kaggle_ref = request.download_url
    logger.info(f"Starting analysis for dataset: {dataset_id} (ref: {kaggle_ref})")

    csv_path = download_kaggle_dataset(
        kaggle_ref=kaggle_ref,
        dataset_id=dataset_id,
    )

    if csv_path is None:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not download this Kaggle dataset. "
                "Please verify: (1) Your Kaggle API credentials are set correctly in .env, "
                "(2) The dataset exists and is publicly accessible, "
                "(3) The dataset contains CSV files."
            ),
        )

    # 2. Run EDA
    eda_result = run_eda(csv_path)
    if "error" in eda_result:
        raise HTTPException(status_code=500, detail=f"EDA failed: {eda_result['error']}")

    metrics: DatasetMetrics = eda_result["metrics"]
    correlations = eda_result["correlations"]
    distributions = eda_result["distributions"]
    eda_warnings: list[str] = eda_result.get("warnings", [])

    # 3. Score dataset (now returns breakdown)
    quality_score, score_explanation, score_breakdown = score_dataset(metrics)

    # 4. Generate structured insights
    insights = generate_insights(metrics, correlations, distributions)

    # 5. ML recommendation (now includes use cases)
    ml_recommendation = recommend_ml(csv_path, metrics)

    # 6. Detect bias
    target_col = ml_recommendation.targetColumn if ml_recommendation else None
    bias_warnings = detect_bias(csv_path, metrics, target_column=target_col)

    # 7. Generate next steps
    next_steps = generate_next_steps(
        metrics=metrics,
        insights=insights,
        ml_recommendation=ml_recommendation,
        bias_warnings=bias_warnings,
        score_breakdown=score_breakdown,
        quality_score=quality_score,
    )

    # Determine quality label
    if quality_score >= 70:
        quality_label = "high"
    elif quality_score >= 40:
        quality_label = "medium"
    else:
        quality_label = "low"

    # Build response
    details = DatasetDetails(
        id=dataset_id,
        title=request.title or dataset_id,
        source=request.source or "kaggle",
        format="csv",
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
        # Store the Kaggle URL for the "View Source" button
        downloadUrl=f"https://www.kaggle.com/datasets/{kaggle_ref}",
    )

    # Cache the result
    _analysis_cache[dataset_id] = details
    logger.info(f"Analysis complete for {dataset_id}: score={quality_score}")

    return details


@router.get("/dataset/{dataset_id}", response_model=DatasetDetails)
async def get_dataset(dataset_id: str):
    """
    Retrieve cached analysis results for a previously analyzed dataset.
    If the dataset hasn't been analyzed yet, returns 404.
    """
    if dataset_id not in _analysis_cache:
        raise HTTPException(
            status_code=404,
            detail="Dataset not found. Please trigger analysis first via /api/analyze.",
        )
    return _analysis_cache[dataset_id]
