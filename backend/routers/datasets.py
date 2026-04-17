"""
Dataset API Router.
- POST /api/analyze — downloads CSV (Kaggle/HuggingFace/GitHub), runs EDA + scoring + insights + ML
- GET  /api/dataset/{dataset_id} — returns cached analysis results
"""
from __future__ import annotations
import logging
import re
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from models.schemas import AnalyzeRequest, DatasetDetails, DatasetMetrics
from services.eda_engine import download_kaggle_dataset, run_eda
from services.scoring import score_dataset
from services.insight_generator import generate_insights
from services.ml_recommender import recommend_ml
from services.bias_detector import detect_bias
from services.next_steps import generate_next_steps
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory cache for analyzed datasets (MVP — replace with DB/Redis in production)
_analysis_cache: dict[str, DatasetDetails] = {}


async def _download_from_url(url: str, dataset_id: str, source: str) -> Optional[str]:
    """
    Download a CSV file from a URL (HuggingFace, GitHub, or any direct link).
    Returns the local path to the downloaded CSV, or None if download fails.
    """
    download_dir = Path(settings.DOWNLOAD_DIR) / dataset_id
    download_dir.mkdir(parents=True, exist_ok=True)

    # For HuggingFace dataset pages, try to construct a direct CSV download URL
    if source == "huggingface" and "huggingface.co/datasets/" in url:
        # Extract dataset name: https://huggingface.co/datasets/username/dataset-name
        match = re.search(r"huggingface\.co/datasets/([^/]+/[^/]+)", url)
        if match:
            hf_name = match.group(1)
            # Try HuggingFace datasets API for CSV files
            try_urls = [
                f"https://huggingface.co/datasets/{hf_name}/resolve/main/data/train.csv",
                f"https://huggingface.co/datasets/{hf_name}/resolve/main/train.csv",
                f"https://huggingface.co/datasets/{hf_name}/resolve/main/data.csv",
                f"https://huggingface.co/datasets/{hf_name}/resolve/main/dataset.csv",
            ]
            for try_url in try_urls:
                result = await _try_download(try_url, download_dir, dataset_id)
                if result:
                    return result

    # For GitHub repos, try to find CSV files
    if source == "github" and "github.com" in url:
        match = re.search(r"github\.com/([^/]+/[^/]+)", url)
        if match:
            repo_name = match.group(1)
            # Use GitHub API to list files in the repo root
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    headers = {"Accept": "application/vnd.github.v3+json"}
                    resp = await client.get(
                        f"https://api.github.com/repos/{repo_name}/contents",
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        files = resp.json()
                        csv_files = [f for f in files if isinstance(f, dict) and f.get("name", "").endswith(".csv")]
                        for csv_file in csv_files[:3]:  # Try first 3 CSV files
                            raw_url = csv_file.get("download_url", "")
                            if raw_url:
                                result = await _try_download(raw_url, download_dir, dataset_id)
                                if result:
                                    return result
            except Exception as e:
                logger.warning(f"GitHub contents API failed: {e}")

    # Direct URL download (for any http CSV link)
    if url.startswith("http"):
        result = await _try_download(url, download_dir, dataset_id)
        if result:
            return result

    return None


async def _try_download(url: str, download_dir: Path, dataset_id: str) -> Optional[str]:
    """Try to download a single file from a URL. Returns local path or None."""
    try:
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                content_type = resp.headers.get("content-type", "")
                # Accept CSV-like content types
                if "csv" in content_type or "text" in content_type or "octet-stream" in content_type or url.endswith(".csv"):
                    # Extract filename from URL
                    filename = url.split("/")[-1].split("?")[0]
                    if not filename.endswith(".csv"):
                        filename = f"{dataset_id}.csv"
                    save_path = download_dir / filename
                    save_path.write_bytes(resp.content)
                    logger.info(f"Downloaded {len(resp.content)} bytes from {url} to {save_path}")
                    return str(save_path)
    except Exception as e:
        logger.warning(f"Download failed for {url}: {e}")
    return None


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

    # 1. Download CSV — Multi-source support
    download_url = request.download_url
    source = request.source or "kaggle"
    logger.info(f"Starting analysis for dataset: {dataset_id} (source: {source}, ref: {download_url})")

    csv_path = None

    if source == "kaggle":
        # Kaggle SDK download
        csv_path = download_kaggle_dataset(
            kaggle_ref=download_url,
            dataset_id=dataset_id,
        )
    elif source in ("huggingface", "github") or download_url.startswith("http"):
        # Try direct HTTP download for HuggingFace/GitHub/any URL
        csv_path = await _download_from_url(download_url, dataset_id, source)

    if csv_path is None:
        source_msg = {
            "kaggle": "Kaggle API credentials are set correctly in .env",
            "huggingface": "the HuggingFace dataset contains downloadable CSV files",
            "github": "the GitHub repository contains CSV files",
        }.get(source, "the dataset URL is accessible")

        raise HTTPException(
            status_code=400,
            detail=(
                f"Could not download this dataset from {source}. "
                f"Please verify: (1) {source_msg}, "
                "(2) The dataset exists and is publicly accessible, "
                "(3) The dataset contains CSV files. "
                "Alternatively, download the file manually and use the Upload feature."
            ),
        )

    # 2. Run EDA
    eda_result = run_eda(csv_path)
    if "error" in eda_result:
        raise HTTPException(
            status_code=500,
            detail=f"Could not analyze this dataset: {eda_result['error']}",
        )

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
        # Store the source URL for the "View Source" button
        downloadUrl=download_url if download_url.startswith("http") else f"https://www.kaggle.com/datasets/{download_url}",
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
