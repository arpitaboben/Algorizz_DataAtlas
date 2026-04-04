"""
Dataset Quality Scoring System.
Scores datasets on a 0–100 scale based on data quality metrics.
Returns a score and a human-readable explanation.
"""
from __future__ import annotations
from models.schemas import DatasetMetrics


def score_dataset(metrics: DatasetMetrics) -> tuple[float, str]:
    """
    Score a dataset 0–100 based on quality indicators.

    Weights:
      - Missing values %: 30 points
      - Duplicate rows %: 20 points
      - Dataset size:     25 points
      - Column balance:   25 points

    Returns: (score, explanation_string)
    """
    reasons: list[str] = []
    total = 0.0

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
        reasons.append(f"High missing values ({missing_pct:.1f}%) reduce usability")
    elif missing_pct <= 1:
        reasons.append("Very low missing values — excellent data completeness")

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
        reasons.append(f"Significant duplicate rows ({dup_pct:.1f}%) — may bias results")
    elif dup_pct <= 0.5:
        reasons.append("Minimal duplicates — clean dataset")

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
        reasons.append(f"Small dataset ({rows} rows) — may not generalize well")
    elif rows >= 10000:
        reasons.append(f"Good dataset size ({rows:,} rows, {cols} columns)")

    # ── 4. Column balance / variety (25 pts) ────────────────────
    col_types = metrics.columnTypes
    if not col_types:
        balance_score = 12.0
    else:
        type_counts: dict[str, int] = {}
        for c in col_types:
            type_counts[c.type] = type_counts.get(c.type, 0) + 1

        n_types = len(type_counts)
        has_numeric = "number" in type_counts
        has_categorical = "string" in type_counts

        if n_types >= 3 and has_numeric and has_categorical:
            balance_score = 25.0
            reasons.append("Good mix of numeric and categorical columns")
        elif n_types >= 2:
            balance_score = 20.0
        elif has_numeric or has_categorical:
            balance_score = 15.0
        else:
            balance_score = 10.0
            reasons.append("Limited column type variety")

    total += balance_score

    # Build final explanation
    total = round(min(100, max(0, total)), 1)
    if not reasons:
        reasons.append("Reasonable data quality overall")

    explanation = "; ".join(reasons) + f". Overall quality score: {total}/100."

    return total, explanation
