"""
Dataset Comparison Service.
Compares 2 analyzed datasets side-by-side on all key metrics.
Returns structured comparison with winner determination.
"""
from __future__ import annotations
import logging
from models.schemas import (
    DatasetDetails, DatasetSummary, ComparisonResult,
)

logger = logging.getLogger(__name__)


def compare_datasets(
    dataset_a: DatasetDetails,
    dataset_b: DatasetDetails,
) -> ComparisonResult:
    """
    Compare two datasets and determine which is better for ML.
    Returns a ComparisonResult with per-metric breakdown and overall winner.
    """

    # Build summaries
    summary_a = _build_summary(dataset_a)
    summary_b = _build_summary(dataset_b)

    # Per-metric comparison
    comparisons = []
    score_a = 0
    score_b = 0

    # 1. Rows
    winner = "tie"
    if summary_a.rows > summary_b.rows * 1.1:
        winner = summary_a.id
        score_a += 1
    elif summary_b.rows > summary_a.rows * 1.1:
        winner = summary_b.id
        score_b += 1
    comparisons.append({
        "metric": "Rows",
        "dataset1_value": f"{summary_a.rows:,}",
        "dataset2_value": f"{summary_b.rows:,}",
        "winner": winner,
        "explanation": "More rows means more training data.",
    })

    # 2. Columns
    winner = "tie"
    if summary_a.columns > summary_b.columns:
        winner = summary_a.id
        score_a += 1
    elif summary_b.columns > summary_a.columns:
        winner = summary_b.id
        score_b += 1
    comparisons.append({
        "metric": "Columns",
        "dataset1_value": str(summary_a.columns),
        "dataset2_value": str(summary_b.columns),
        "winner": winner,
        "explanation": "More columns means more potential features.",
    })

    # 3. Missing %
    winner = "tie"
    if summary_a.missingPercent < summary_b.missingPercent - 0.5:
        winner = summary_a.id
        score_a += 2  # Missing is heavily weighted
    elif summary_b.missingPercent < summary_a.missingPercent - 0.5:
        winner = summary_b.id
        score_b += 2
    comparisons.append({
        "metric": "Missing Data",
        "dataset1_value": f"{summary_a.missingPercent}%",
        "dataset2_value": f"{summary_b.missingPercent}%",
        "winner": winner,
        "explanation": "Lower missing data means less imputation needed.",
    })

    # 4. Duplicate %
    winner = "tie"
    if summary_a.duplicatePercent < summary_b.duplicatePercent - 0.5:
        winner = summary_a.id
        score_a += 1
    elif summary_b.duplicatePercent < summary_a.duplicatePercent - 0.5:
        winner = summary_b.id
        score_b += 1
    comparisons.append({
        "metric": "Duplicates",
        "dataset1_value": f"{summary_a.duplicatePercent}%",
        "dataset2_value": f"{summary_b.duplicatePercent}%",
        "winner": winner,
        "explanation": "Fewer duplicates means cleaner data.",
    })

    # 5. Quality Score
    winner = "tie"
    if summary_a.qualityScore > summary_b.qualityScore + 3:
        winner = summary_a.id
        score_a += 2
    elif summary_b.qualityScore > summary_a.qualityScore + 3:
        winner = summary_b.id
        score_b += 2
    comparisons.append({
        "metric": "Quality Score",
        "dataset1_value": f"{summary_a.qualityScore}/100",
        "dataset2_value": f"{summary_b.qualityScore}/100",
        "winner": winner,
        "explanation": "Higher quality score means better overall data quality.",
    })

    # 6. Feature Balance (numeric vs categorical)
    a_balance = _feature_balance_score(summary_a)
    b_balance = _feature_balance_score(summary_b)
    winner = "tie"
    if a_balance > b_balance:
        winner = summary_a.id
        score_a += 1
    elif b_balance > a_balance:
        winner = summary_b.id
        score_b += 1
    comparisons.append({
        "metric": "Feature Balance",
        "dataset1_value": f"{summary_a.numericColumnCount} numeric, {summary_a.categoricalColumnCount} categorical",
        "dataset2_value": f"{summary_b.numericColumnCount} numeric, {summary_b.categoricalColumnCount} categorical",
        "winner": winner,
        "explanation": "A good mix of numeric and categorical features is ideal.",
    })

    # 7. ML Task (informational)
    comparisons.append({
        "metric": "ML Task",
        "dataset1_value": summary_a.mlTask or "Unknown",
        "dataset2_value": summary_b.mlTask or "Unknown",
        "winner": "tie",
        "explanation": "The recommended ML task for each dataset.",
    })

    # Determine overall winner
    if score_a > score_b:
        best_id = summary_a.id
        explanation = _build_explanation(summary_a, summary_b, score_a, score_b)
    elif score_b > score_a:
        best_id = summary_b.id
        explanation = _build_explanation(summary_b, summary_a, score_b, score_a)
    else:
        best_id = summary_a.id if summary_a.qualityScore >= summary_b.qualityScore else summary_b.id
        explanation = (
            f"Both datasets are very similar in quality. "
            f"'{summary_a.title}' has a quality score of {summary_a.qualityScore}/100, "
            f"while '{summary_b.title}' scores {summary_b.qualityScore}/100. "
            f"Choose based on your specific ML task requirements."
        )

    return ComparisonResult(
        datasets=[summary_a, summary_b],
        bestDatasetId=best_id,
        explanation=explanation,
        metricComparisons=comparisons,
    )


def _build_summary(dataset: DatasetDetails) -> DatasetSummary:
    """Extract a lightweight summary from full dataset details."""
    metrics = dataset.metrics
    numeric_count = sum(1 for c in metrics.columnTypes if c.type == "number")
    categorical_count = sum(1 for c in metrics.columnTypes if c.type == "string")
    avg_nulls = 0.0
    if metrics.columnTypes:
        total_nulls = sum(c.nullCount for c in metrics.columnTypes)
        avg_nulls = round(total_nulls / len(metrics.columnTypes), 1)

    # Compute correlation strength
    corr_strength = "none"
    if dataset.correlations:
        max_corr = max(abs(c.value) for c in dataset.correlations)
        if max_corr >= 0.9:
            corr_strength = "strong"
        elif max_corr >= 0.7:
            corr_strength = "moderate"
        elif max_corr >= 0.4:
            corr_strength = "weak"

    return DatasetSummary(
        id=dataset.id,
        title=dataset.title,
        source=dataset.source,
        rows=metrics.rows,
        columns=metrics.columns,
        missingPercent=metrics.missingPercent,
        duplicatePercent=metrics.duplicatePercent,
        qualityScore=dataset.score or 0.0,
        qualityLabel=dataset.qualityScore,
        mlTask=dataset.mlRecommendation.task if dataset.mlRecommendation else "",
        targetColumn=dataset.mlRecommendation.targetColumn if dataset.mlRecommendation else None,
        numericColumnCount=numeric_count,
        categoricalColumnCount=categorical_count,
        avgNullsPerColumn=avg_nulls,
        correlationStrength=corr_strength,
        sizeBytes=dataset.sizeBytes,
    )


def _feature_balance_score(summary: DatasetSummary) -> float:
    """Score how well-balanced the feature types are (0-1)."""
    total = summary.numericColumnCount + summary.categoricalColumnCount
    if total == 0:
        return 0.0
    ratio = min(summary.numericColumnCount, summary.categoricalColumnCount) / max(
        summary.numericColumnCount, summary.categoricalColumnCount, 1
    )
    return ratio


def _build_explanation(winner: DatasetSummary, loser: DatasetSummary, w_score: int, l_score: int) -> str:
    """Build a human-readable explanation of why one dataset is better."""
    advantages = []
    if winner.qualityScore > loser.qualityScore:
        advantages.append(f"higher quality score ({winner.qualityScore} vs {loser.qualityScore})")
    if winner.rows > loser.rows:
        advantages.append(f"more data ({winner.rows:,} vs {loser.rows:,} rows)")
    if winner.missingPercent < loser.missingPercent:
        advantages.append(f"less missing data ({winner.missingPercent}% vs {loser.missingPercent}%)")
    if winner.duplicatePercent < loser.duplicatePercent:
        advantages.append(f"fewer duplicates ({winner.duplicatePercent}% vs {loser.duplicatePercent}%)")

    adv_text = ", ".join(advantages[:3]) if advantages else "slightly better metrics overall"
    return (
        f"'{winner.title}' is recommended with {adv_text}. "
        f"It won {w_score} out of {w_score + l_score} comparison metrics."
    )
