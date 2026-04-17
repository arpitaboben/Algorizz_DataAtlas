"""
Data Bias Detection Engine.
Detects class imbalance, feature skewness, feature dominance,
outlier concentration, and low-variance features.
Returns structured BiasWarning items.
"""
from __future__ import annotations
import logging
import pandas as pd
import numpy as np
from models.schemas import BiasWarning, DatasetMetrics

logger = logging.getLogger(__name__)


def detect_bias(csv_path: str, metrics: DatasetMetrics, target_column: str | None = None) -> list[BiasWarning]:
    """
    Analyze a dataset for potential bias and fairness issues.
    Returns a list of BiasWarning items.
    """
    warnings: list[BiasWarning] = []

    try:
        df = pd.read_csv(csv_path, nrows=100_000)
    except Exception as e:
        logger.error(f"Failed to read CSV for bias detection: {e}")
        return warnings

    # ── 1. Class Imbalance Detection ─────────────────────────────
    if target_column and target_column in df.columns:
        w = _check_class_imbalance(df, target_column)
        if w:
            warnings.append(w)

    # ── 2. Feature Skewness ──────────────────────────────────────
    skew_warnings = _check_skewness(df)
    warnings.extend(skew_warnings)

    # ── 3. Feature Dominance ─────────────────────────────────────
    dom_warning = _check_feature_dominance(df)
    if dom_warning:
        warnings.append(dom_warning)

    # ── 4. Outlier Heavy Columns ─────────────────────────────────
    outlier_warnings = _check_outliers(df)
    warnings.extend(outlier_warnings)

    # ── 5. Low Variance Features ─────────────────────────────────
    lv_warning = _check_low_variance(df)
    if lv_warning:
        warnings.append(lv_warning)

    # ── 6. Potential Proxy Variable Detection ────────────────────
    proxy_warning = _check_proxy_variables(df)
    if proxy_warning:
        warnings.append(proxy_warning)

    return warnings


def _check_class_imbalance(df: pd.DataFrame, target: str) -> BiasWarning | None:
    """Detect class imbalance in the target column."""
    try:
        value_counts = df[target].value_counts(normalize=True)
        if len(value_counts) < 2:
            return None

        dominant_pct = value_counts.iloc[0] * 100
        minority_pct = value_counts.iloc[-1] * 100
        ratio = dominant_pct / max(minority_pct, 0.01)

        if dominant_pct >= 90:
            severity = "high"
            title = f"Severe Class Imbalance in '{target}'"
        elif dominant_pct >= 80:
            severity = "high"
            title = f"Significant Class Imbalance in '{target}'"
        elif dominant_pct >= 70:
            severity = "medium"
            title = f"Moderate Class Imbalance in '{target}'"
        else:
            return None  # Balanced enough

        dominant_class = value_counts.index[0]
        minority_class = value_counts.index[-1]

        return BiasWarning(
            type="class_imbalance",
            severity=severity,
            title=title,
            description=(
                f"Class '{dominant_class}' dominates at {dominant_pct:.1f}% while "
                f"class '{minority_class}' has only {minority_pct:.1f}%. "
                f"Imbalance ratio: {ratio:.1f}:1."
            ),
            affected_columns=[target],
            suggestion=(
                "Apply SMOTE oversampling, class weights in the model, "
                "or stratified sampling. Use F1-score/AUC instead of accuracy for evaluation."
            ),
        )
    except Exception as e:
        logger.warning(f"Class imbalance check failed: {e}")
        return None


def _check_skewness(df: pd.DataFrame) -> list[BiasWarning]:
    """Detect heavily skewed numeric features."""
    warnings: list[BiasWarning] = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    high_skew_cols = []
    moderate_skew_cols = []

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 20:
            continue
        skew = series.skew()
        if abs(skew) > 3:
            high_skew_cols.append((col, round(skew, 2)))
        elif abs(skew) > 2:
            moderate_skew_cols.append((col, round(skew, 2)))

    if high_skew_cols:
        cols_desc = ", ".join(f"'{c[0]}' (skew={c[1]})" for c in high_skew_cols[:4])
        warnings.append(BiasWarning(
            type="feature_skewness",
            severity="high",
            title=f"Heavily Skewed Features ({len(high_skew_cols)})",
            description=f"These features have extreme skewness: {cols_desc}. This can bias linear models and distance-based algorithms.",
            affected_columns=[c[0] for c in high_skew_cols],
            suggestion="Apply Yeo-Johnson or log transform. Consider robust scaling (median/IQR) instead of standard scaling.",
        ))

    if moderate_skew_cols:
        cols_desc = ", ".join(f"'{c[0]}' (skew={c[1]})" for c in moderate_skew_cols[:4])
        warnings.append(BiasWarning(
            type="feature_skewness",
            severity="medium",
            title=f"Moderately Skewed Features ({len(moderate_skew_cols)})",
            description=f"These features show notable skewness: {cols_desc}.",
            affected_columns=[c[0] for c in moderate_skew_cols],
            suggestion="Power transforms or log transforms can improve normality. Tree-based models are less affected.",
        ))

    return warnings


def _check_feature_dominance(df: pd.DataFrame) -> BiasWarning | None:
    """Detect if one feature has disproportionately high variance."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) < 3:
        return None

    try:
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        scaled = pd.DataFrame(
            scaler.fit_transform(df[numeric_cols].fillna(0)),
            columns=numeric_cols,
        )
        variances = scaled.var()
        mean_var = variances.mean()

        if mean_var > 0:
            dominant = variances[variances > 3 * mean_var]
            if len(dominant) > 0 and len(dominant) <= 3:
                cols = dominant.index.tolist()
                return BiasWarning(
                    type="feature_dominance",
                    severity="medium",
                    title=f"Feature Dominance Detected",
                    description=(
                        f"Column(s) {', '.join(repr(c) for c in cols)} have disproportionately high "
                        f"variance compared to other features. They may dominate distance-based models."
                    ),
                    affected_columns=cols,
                    suggestion="Apply normalization (min-max or robust scaling) to equalize feature influence.",
                )
    except Exception as e:
        logger.warning(f"Feature dominance check failed: {e}")

    return None


def _check_outliers(df: pd.DataFrame) -> list[BiasWarning]:
    """Detect columns with heavy outlier concentration."""
    warnings: list[BiasWarning] = []
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    outlier_heavy_cols = []

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 20:
            continue

        Q1 = series.quantile(0.25)
        Q3 = series.quantile(0.75)
        IQR = Q3 - Q1

        if IQR == 0:
            continue

        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR
        outlier_pct = ((series < lower) | (series > upper)).mean() * 100

        if outlier_pct > 10:
            outlier_heavy_cols.append((col, round(outlier_pct, 1)))

    if outlier_heavy_cols:
        cols_desc = ", ".join(f"'{c[0]}' ({c[1]}%)" for c in outlier_heavy_cols[:4])
        warnings.append(BiasWarning(
            type="outlier_heavy",
            severity="medium" if len(outlier_heavy_cols) <= 3 else "high",
            title=f"Outlier-Heavy Columns ({len(outlier_heavy_cols)})",
            description=f"These columns have significant outlier percentages: {cols_desc}.",
            affected_columns=[c[0] for c in outlier_heavy_cols],
            suggestion="Use IQR-based outlier removal or winsorization. Robust models (tree-based) are less affected.",
        ))

    return warnings


def _check_low_variance(df: pd.DataFrame) -> BiasWarning | None:
    """Detect near-constant features that add noise without signal."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    low_var_cols = []

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 10:
            continue

        # Check if >95% of values are the same
        most_common_pct = series.value_counts(normalize=True).iloc[0] if len(series) > 0 else 0
        if most_common_pct > 0.95:
            low_var_cols.append((col, round(most_common_pct * 100, 1)))

    if low_var_cols:
        cols_desc = ", ".join(f"'{c[0]}' ({c[1]}% same value)" for c in low_var_cols[:4])
        return BiasWarning(
            type="low_variance",
            severity="medium",
            title=f"Near-Constant Features ({len(low_var_cols)})",
            description=f"These features have almost no variation: {cols_desc}.",
            affected_columns=[c[0] for c in low_var_cols],
            suggestion="Drop these features — they provide almost no information and may add noise to models.",
        )

    return None


def _check_proxy_variables(df: pd.DataFrame) -> BiasWarning | None:
    """
    Detect potential proxy variables for sensitive attributes.
    Checks if column names suggest demographic / protected attributes.
    """
    sensitive_patterns = [
        "gender", "sex", "race", "ethnicity", "age", "religion",
        "nationality", "zip", "postal", "zipcode", "zip_code",
        "marital", "disability", "veteran",
    ]

    found = []
    for col in df.columns:
        col_lower = col.lower().replace("_", "").replace("-", "")
        for pattern in sensitive_patterns:
            if pattern in col_lower:
                found.append(col)
                break

    if found:
        return BiasWarning(
            type="proxy_variable",
            severity="medium",
            title=f"Potential Sensitive Attributes ({len(found)})",
            description=f"Columns that may contain sensitive/protected information: {', '.join(repr(c) for c in found)}.",
            affected_columns=found,
            suggestion="Review these columns for fairness implications. Consider if they should be included in modeling or if they introduce discriminatory bias.",
        )

    return None
