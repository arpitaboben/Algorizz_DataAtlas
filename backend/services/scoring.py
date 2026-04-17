"""
Dataset Quality Scoring System — Enhanced.
Scores datasets on a 0–100 scale based on data quality metrics.
Returns a score, explanation, AND a detailed breakdown of sub-scores.
"""
from __future__ import annotations
from models.schemas import DatasetMetrics, ScoreBreakdown, ScoreComponent


def score_dataset(metrics: DatasetMetrics) -> tuple[float, str, ScoreBreakdown]:
    """
    Score a dataset 0–100 based on quality indicators.

    Weights:
      - Missing values %: 30 points
      - Duplicate rows %: 20 points
      - Dataset size:     25 points
      - Column balance:   25 points

    Returns: (score, explanation_string, score_breakdown)
    """
    reasons: list[str] = []
    total = 0.0
    components: list[ScoreComponent] = []

    # ── 1. Missing values (30 pts) ──────────────────────────────
    missing_pct = metrics.missingPercent
    if missing_pct <= 1:
        missing_score = 30.0
    elif missing_pct <= 5:
        missing_score = 25.0
    elif missing_pct <= 15:
        missing_score = 18.0
    elif missing_pct <= 30:
        missing_score = 10.0
    else:
        missing_score = 3.0

    total += missing_score
    if missing_pct > 15:
        missing_label = "Poor"
        missing_desc = f"High missing values ({missing_pct:.1f}%) reduce usability. Consider imputation or column removal."
        reasons.append(f"High missing values ({missing_pct:.1f}%) reduce usability")
    elif missing_pct <= 1:
        missing_label = "Excellent"
        missing_desc = f"Very low missing values ({missing_pct:.1f}%) — excellent data completeness."
        reasons.append("Very low missing values — excellent data completeness")
    elif missing_pct <= 5:
        missing_label = "Good"
        missing_desc = f"Low missing values ({missing_pct:.1f}%) — minor imputation may be needed."
    else:
        missing_label = "Fair"
        missing_desc = f"Moderate missing values ({missing_pct:.1f}%) — imputation strategies recommended."

    components.append(ScoreComponent(
        name="completeness",
        score=missing_score,
        maxScore=30.0,
        label=missing_label,
        description=missing_desc,
    ))

    # ── 2. Duplicate rows (20 pts) ──────────────────────────────
    dup_pct = metrics.duplicatePercent
    if dup_pct <= 0.5:
        dup_score = 20.0
    elif dup_pct <= 2:
        dup_score = 16.0
    elif dup_pct <= 5:
        dup_score = 10.0
    elif dup_pct <= 15:
        dup_score = 5.0
    else:
        dup_score = 1.0

    total += dup_score
    if dup_pct > 5:
        dup_label = "Poor"
        dup_desc = f"Significant duplicate rows ({dup_pct:.1f}%) — may bias model training results."
        reasons.append(f"Significant duplicate rows ({dup_pct:.1f}%) — may bias results")
    elif dup_pct <= 0.5:
        dup_label = "Excellent"
        dup_desc = f"Minimal duplicates ({dup_pct:.1f}%) — clean dataset."
        reasons.append("Minimal duplicates — clean dataset")
    elif dup_pct <= 2:
        dup_label = "Good"
        dup_desc = f"Low duplicates ({dup_pct:.1f}%) — acceptable."
    else:
        dup_label = "Fair"
        dup_desc = f"Moderate duplicates ({dup_pct:.1f}%) — review recommended."

    components.append(ScoreComponent(
        name="uniqueness",
        score=dup_score,
        maxScore=20.0,
        label=dup_label,
        description=dup_desc,
    ))

    # ── 3. Dataset size (25 pts) ────────────────────────────────
    rows = metrics.rows
    cols = metrics.columns
    if rows >= 1000 and cols >= 3:
        size_score = 25.0
    elif rows >= 500 and cols >= 2:
        size_score = 20.0
    elif rows >= 100:
        size_score = 15.0
    elif rows >= 50:
        size_score = 10.0
    else:
        size_score = 5.0

    total += size_score
    if rows < 100:
        size_label = "Poor"
        size_desc = f"Small dataset ({rows:,} rows) — may not generalize well for complex models."
        reasons.append(f"Small dataset ({rows} rows) — may not generalize well")
    elif rows >= 10000:
        size_label = "Excellent"
        size_desc = f"Large dataset ({rows:,} rows, {cols} columns) — excellent for ML."
        reasons.append(f"Good dataset size ({rows:,} rows, {cols} columns)")
    elif rows >= 1000:
        size_label = "Good"
        size_desc = f"Good dataset size ({rows:,} rows, {cols} columns) — supports most ML models."
    else:
        size_label = "Fair"
        size_desc = f"Moderate size ({rows:,} rows, {cols} columns) — suitable for simpler models."

    components.append(ScoreComponent(
        name="size",
        score=size_score,
        maxScore=25.0,
        label=size_label,
        description=size_desc,
    ))

    # ── 4. Column balance / variety (25 pts) ────────────────────
    col_types = metrics.columnTypes
    if not col_types:
        balance_score = 12.0
        balance_label = "Unknown"
        balance_desc = "No column type information available."
    else:
        type_counts: dict[str, int] = {}
        for c in col_types:
            type_counts[c.type] = type_counts.get(c.type, 0) + 1

        n_types = len(type_counts)
        has_numeric = "number" in type_counts
        has_categorical = "string" in type_counts

        if n_types >= 3 and has_numeric and has_categorical:
            balance_score = 25.0
            balance_label = "Excellent"
            balance_desc = f"Diverse column types: {', '.join(f'{v} {k}' for k, v in type_counts.items())}. Good mix for modeling."
            reasons.append("Good mix of numeric and categorical columns")
        elif n_types >= 2:
            balance_score = 20.0
            balance_label = "Good"
            balance_desc = f"Column types: {', '.join(f'{v} {k}' for k, v in type_counts.items())}."
        elif has_numeric or has_categorical:
            balance_score = 15.0
            balance_label = "Fair"
            balance_desc = f"Limited column type variety ({', '.join(f'{v} {k}' for k, v in type_counts.items())}). Consider feature engineering."
        else:
            balance_score = 10.0
            balance_label = "Poor"
            balance_desc = "Limited column type variety — feature engineering strongly recommended."
            reasons.append("Limited column type variety")

    total += balance_score

    components.append(ScoreComponent(
        name="diversity",
        score=balance_score,
        maxScore=25.0,
        label=balance_label,
        description=balance_desc,
    ))

    # Build final result
    total = round(min(100, max(0, total)), 1)
    if not reasons:
        reasons.append("Reasonable data quality overall")

    explanation = "; ".join(reasons) + f". Overall quality score: {total}/100."

    breakdown = ScoreBreakdown(
        overall=total,
        components=components,
    )

    return total, explanation, breakdown
