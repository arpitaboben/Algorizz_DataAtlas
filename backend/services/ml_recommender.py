"""
ML Recommendation Engine.
Analyzes a dataset to recommend the best ML task, models, and target column.
"""
from __future__ import annotations
import logging
import pandas as pd
import numpy as np
from models.schemas import MLRecommendation, DatasetMetrics

logger = logging.getLogger(__name__)


def recommend_ml(csv_path: str, metrics: DatasetMetrics) -> MLRecommendation:
    """
    Analyze the dataset and return ML task + model recommendations.
    
    Detection logic:
      1. Time column present → time-series
      2. Text column present → NLP (classification)
      3. Categorical target → classification
      4. Numeric target → regression
    """
    try:
        df = pd.read_csv(csv_path, nrows=10_000)  # Sample for speed
    except Exception as e:
        logger.error(f"Failed to read CSV for ML recommendation: {e}")
        return MLRecommendation(
            task="classification",
            confidence=30,
            suggestedModels=["Random Forest", "Logistic Regression"],
            reasoning=f"Could not analyze dataset: {e}",
        )

    col_analysis = _analyze_columns(df)

    # ── 1. Check for time series ────────────────────────────────
    if col_analysis["datetime_cols"]:
        numeric_targets = [c for c in col_analysis["numeric_cols"] if c not in col_analysis["datetime_cols"]]
        target = _pick_best_target(df, numeric_targets) if numeric_targets else None
        return MLRecommendation(
            task="time-series",
            confidence=85,
            suggestedModels=["ARIMA", "Prophet", "LSTM", "XGBoost"],
            targetColumn=target,
            reasoning=(
                f"Detected temporal column(s): {', '.join(col_analysis['datetime_cols'])}. "
                f"Time series forecasting is recommended for predicting trends over time."
                + (f" Suggested target: '{target}'." if target else "")
            ),
        )

    # ── 2. Check for NLP / text-heavy columns ──────────────────
    if col_analysis["text_cols"]:
        # If there's a short categorical column, use it as target
        cat_cols = col_analysis["low_cardinality_cols"]
        target = cat_cols[0] if cat_cols else None
        return MLRecommendation(
            task="classification",
            confidence=78,
            suggestedModels=["TF-IDF + Logistic Regression", "BERT", "Naive Bayes", "DistilBERT"],
            targetColumn=target,
            reasoning=(
                f"Detected text column(s): {', '.join(col_analysis['text_cols'][:3])}. "
                "NLP-based text classification is recommended."
                + (f" Suggested target: '{target}'." if target else "")
            ),
        )

    # ── 3. Pick the best target column ──────────────────────────
    # Look for common target column names first
    target, is_categorical = _detect_target(df, col_analysis)

    if target and is_categorical:
        n_classes = df[target].nunique()
        return MLRecommendation(
            task="classification",
            confidence=88,
            suggestedModels=_classification_models(n_classes),
            targetColumn=target,
            reasoning=(
                f"Target column '{target}' is categorical with {n_classes} classes. "
                "Classification is the most appropriate task."
            ),
        )

    if target and not is_categorical:
        return MLRecommendation(
            task="regression",
            confidence=85,
            suggestedModels=["XGBoost", "Random Forest", "Linear Regression", "LightGBM", "Ridge Regression"],
            targetColumn=target,
            reasoning=(
                f"Target column '{target}' is numeric with {df[target].nunique()} unique values. "
                "Regression is the most appropriate task."
            ),
        )

    # ── 4. Fallback: clustering ─────────────────────────────────
    if len(col_analysis["numeric_cols"]) >= 3:
        return MLRecommendation(
            task="clustering",
            confidence=60,
            suggestedModels=["K-Means", "DBSCAN", "Gaussian Mixture", "Hierarchical Clustering"],
            reasoning=(
                "No clear target column detected. With multiple numeric features, "
                "unsupervised clustering may help discover hidden patterns."
            ),
        )

    return MLRecommendation(
        task="classification",
        confidence=40,
        suggestedModels=["Random Forest", "XGBoost", "Logistic Regression"],
        reasoning="Unable to auto-detect the best task. Please specify a target column for better recommendations.",
    )


def _analyze_columns(df: pd.DataFrame) -> dict:
    """Categorize all columns by their data characteristics."""
    datetime_cols: list[str] = []
    numeric_cols: list[str] = []
    text_cols: list[str] = []
    low_cardinality_cols: list[str] = []
    boolean_cols: list[str] = []

    for col in df.columns:
        series = df[col]
        dtype = series.dtype

        # Boolean
        if pd.api.types.is_bool_dtype(dtype):
            boolean_cols.append(col)
            continue

        # Numeric
        if pd.api.types.is_numeric_dtype(dtype):
            numeric_cols.append(col)
            continue

        # Datetime
        if pd.api.types.is_datetime64_any_dtype(dtype):
            datetime_cols.append(col)
            continue

        # String columns
        if dtype == object:
            sample = series.dropna().head(50)
            # Check if it's a datetime
            try:
                pd.to_datetime(sample)
                datetime_cols.append(col)
                continue
            except (ValueError, TypeError):
                pass

            # Check if it's text (long strings)
            avg_len = sample.astype(str).str.len().mean() if len(sample) > 0 else 0
            n_unique = series.nunique()

            if avg_len > 50:
                text_cols.append(col)
            elif n_unique <= 20:
                low_cardinality_cols.append(col)
            elif n_unique <= 50 and n_unique / len(df) < 0.1:
                low_cardinality_cols.append(col)

    return {
        "datetime_cols": datetime_cols,
        "numeric_cols": numeric_cols,
        "text_cols": text_cols,
        "low_cardinality_cols": low_cardinality_cols,
        "boolean_cols": boolean_cols,
    }


def _detect_target(df: pd.DataFrame, col_analysis: dict) -> tuple:
    """
    Try to detect the target column.
    Returns (column_name, is_categorical) or (None, None).
    """
    # Common target column name patterns
    TARGET_PATTERNS = [
        "target", "label", "class", "y", "output", "result",
        "price", "salary", "amount", "revenue", "sales",
        "status", "category", "type", "is_", "has_",
        "survived", "diagnosis", "sentiment", "rating",
    ]

    # Check categorical columns first
    for col in col_analysis["low_cardinality_cols"]:
        col_lower = col.lower()
        for pattern in TARGET_PATTERNS:
            if pattern in col_lower:
                return col, True

    # Check numeric columns
    for col in col_analysis["numeric_cols"]:
        col_lower = col.lower()
        for pattern in TARGET_PATTERNS:
            if pattern in col_lower:
                is_cat = df[col].nunique() <= 10
                return col, is_cat

    # Fallback: last column is often the target
    last_col = df.columns[-1]
    if last_col in col_analysis["low_cardinality_cols"]:
        return last_col, True
    if last_col in col_analysis["numeric_cols"]:
        return last_col, df[last_col].nunique() <= 10

    return None, None


def _pick_best_target(df: pd.DataFrame, candidates: list[str]) -> str | None:
    """Pick the best numeric target from a list of candidates."""
    if not candidates:
        return None
    # Prefer the column furthest to the right (common convention)
    col_positions = [(df.columns.get_loc(c), c) for c in candidates]
    col_positions.sort(reverse=True)
    return col_positions[0][1]


def _classification_models(n_classes: int) -> list[str]:
    """Return suggested classification models based on number of classes."""
    if n_classes == 2:
        return ["Logistic Regression", "XGBoost", "Random Forest", "SVM", "LightGBM"]
    elif n_classes <= 10:
        return ["Random Forest", "XGBoost", "LightGBM", "Gradient Boosting", "Neural Network"]
    else:
        return ["XGBoost", "LightGBM", "Neural Network", "Random Forest"]
