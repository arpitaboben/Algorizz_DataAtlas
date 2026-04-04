"""
Insight Generation Layer.
Converts EDA results into meaningful, human-readable insights.
Uses ONLY rule-based logic (no ML).
"""
from __future__ import annotations
from models.schemas import DatasetMetrics, Correlation, Distribution


def generate_insights(
    metrics: DatasetMetrics,
    correlations: list[Correlation],
    distributions: list[Distribution],
) -> list[str]:
    """
    Analyze EDA results and produce a list of plain-language insights.
    """
    insights: list[str] = []

    # ── Missing values insights ──────────────────────────────────
    if metrics.missingPercent == 0:
        insights.append("✅ No missing values — dataset is fully complete")
    elif metrics.missingPercent <= 2:
        insights.append(f"✅ Very low missing values ({metrics.missingPercent}%) — minimal imputation needed")
    elif metrics.missingPercent <= 10:
        insights.append(f"⚠️ Moderate missing values ({metrics.missingPercent}%) — consider imputation strategies")
    else:
        insights.append(f"🔴 High missing values ({metrics.missingPercent}%) — significant data cleaning required")

    # Per-column missing value alerts
    for col in metrics.columnTypes:
        if col.nullCount > 0 and metrics.rows > 0:
            pct = round(col.nullCount / metrics.rows * 100, 1)
            if pct > 30:
                insights.append(
                    f"🔴 Column '{col.name}' has {pct}% missing values — consider dropping or imputing"
                )
            elif pct > 10:
                insights.append(
                    f"⚠️ Column '{col.name}' has {pct}% missing values"
                )

    # ── Duplicate insights ───────────────────────────────────────
    if metrics.duplicatePercent == 0:
        insights.append("✅ No duplicate rows detected")
    elif metrics.duplicatePercent <= 1:
        insights.append(f"✅ Minimal duplicates ({metrics.duplicatePercent}%)")
    elif metrics.duplicatePercent <= 5:
        insights.append(
            f"⚠️ {metrics.duplicatePercent}% duplicate rows — review for unintentional data replication"
        )
    else:
        insights.append(
            f"🔴 {metrics.duplicatePercent}% duplicate rows — high duplication may bias model training"
        )

    # ── Size insights ────────────────────────────────────────────
    if metrics.rows < 100:
        insights.append(f"⚠️ Small dataset ({metrics.rows} rows) — may not support complex models")
    elif metrics.rows < 1000:
        insights.append(f"ℹ️ Moderate dataset size ({metrics.rows:,} rows) — suitable for simpler models")
    else:
        insights.append(f"✅ Good dataset size ({metrics.rows:,} rows, {metrics.columns} columns)")

    # ── Low-variance / low-cardinality columns ───────────────────
    for col in metrics.columnTypes:
        if col.uniqueCount == 1:
            insights.append(
                f"🔴 Column '{col.name}' has only 1 unique value — provides no information, consider dropping"
            )
        elif col.uniqueCount == 2 and col.type != "boolean":
            insights.append(
                f"ℹ️ Column '{col.name}' has only 2 unique values — potential binary feature"
            )
        elif col.type == "number" and col.uniqueCount <= 5:
            insights.append(
                f"ℹ️ Numeric column '{col.name}' has very low cardinality ({col.uniqueCount} values) — may be categorical"
            )

    # ── High-cardinality categorical columns ─────────────────────
    for col in metrics.columnTypes:
        if col.type == "string" and metrics.rows > 0:
            cardinality_ratio = col.uniqueCount / metrics.rows
            if cardinality_ratio > 0.9:
                insights.append(
                    f"ℹ️ Column '{col.name}' has very high cardinality ({col.uniqueCount:,} unique values)"
                    f" — likely an identifier, not useful as a feature"
                )

    # ── Correlation insights ─────────────────────────────────────
    for corr in correlations:
        abs_val = abs(corr.value)
        if abs_val >= 0.9:
            direction = "positive" if corr.value > 0 else "negative"
            insights.append(
                f"🔴 Very strong {direction} correlation between '{corr.column1}' and "
                f"'{corr.column2}' (r={corr.value:.2f}) — potential multicollinearity, consider removing one"
            )
        elif abs_val >= 0.7:
            direction = "positive" if corr.value > 0 else "negative"
            insights.append(
                f"⚠️ Strong {direction} correlation between '{corr.column1}' and "
                f"'{corr.column2}' (r={corr.value:.2f})"
            )
        elif abs_val >= 0.5:
            direction = "positive" if corr.value > 0 else "negative"
            insights.append(
                f"ℹ️ Moderate {direction} correlation between '{corr.column1}' and "
                f"'{corr.column2}' (r={corr.value:.2f})"
            )

    # ── Distribution insights ────────────────────────────────────
    for dist in distributions:
        if len(dist.bins) >= 2:
            counts = [b.get("count", 0) if isinstance(b, dict) else 0 for b in dist.bins]
            if counts:
                max_count = max(counts)
                min_count = min(counts)
                if max_count > 0 and min_count / max_count < 0.1:
                    insights.append(
                        f"⚠️ Column '{dist.column}' has a highly skewed distribution — consider log transform"
                    )

    return insights
