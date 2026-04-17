"""
ML Recommendation Engine — Enhanced with Use Case Detection.
Analyzes dataset structure and column semantics to recommend:
  1. ML task type (classification, regression, clustering, time-series)
  2. Suggested models
  3. Practical use cases the dataset could serve
"""
from __future__ import annotations
import logging
import pandas as pd
import numpy as np
from models.schemas import MLRecommendation, DatasetMetrics

logger = logging.getLogger(__name__)


# ── Use Case Knowledge Base ─────────────────────────────────────

_USE_CASE_PATTERNS = {
    "classification": {
        "health": ["disease prediction", "patient diagnosis", "medical risk assessment"],
        "finance": ["fraud detection", "credit scoring", "loan default prediction"],
        "customer": ["churn prediction", "customer segmentation", "lead scoring"],
        "text": ["spam detection", "sentiment analysis", "document classification"],
        "image": ["object recognition", "defect detection", "medical imaging"],
        "security": ["intrusion detection", "malware classification", "anomaly detection"],
        "marketing": ["conversion prediction", "campaign targeting", "A/B test analysis"],
        "general": ["binary classification", "multi-class prediction", "label assignment"],
    },
    "regression": {
        "price": ["price prediction", "real estate valuation", "product pricing"],
        "demand": ["demand forecasting", "inventory optimization", "sales prediction"],
        "finance": ["stock price prediction", "revenue forecasting", "risk quantification"],
        "science": ["measurement prediction", "experiment outcome estimation"],
        "energy": ["energy consumption prediction", "load forecasting"],
        "general": ["continuous value prediction", "trend estimation", "quantity forecasting"],
    },
    "clustering": {
        "customer": ["customer segmentation", "market basket analysis", "persona discovery"],
        "science": ["pattern discovery", "taxonomy generation", "anomaly detection"],
        "general": ["data grouping", "similarity analysis", "unsupervised pattern mining"],
    },
    "time-series": {
        "finance": ["stock forecasting", "revenue projection", "volatility modeling"],
        "demand": ["demand planning", "capacity planning", "seasonal trend analysis"],
        "iot": ["sensor data analysis", "predictive maintenance", "anomaly detection"],
        "general": ["time-series forecasting", "trend analysis", "seasonal decomposition"],
    },
}

# Column name patterns that suggest specific domains
_DOMAIN_PATTERNS = {
    "health": ["patient", "diagnosis", "symptom", "disease", "medical", "health", "blood", "heart",
               "bmi", "glucose", "insulin", "cholesterol", "hospital", "clinical"],
    "finance": ["price", "cost", "revenue", "profit", "salary", "income", "credit", "loan",
                "interest", "transaction", "payment", "balance", "stock", "market", "fund"],
    "customer": ["customer", "user", "churn", "retention", "satisfaction", "feedback",
                 "subscriber", "member", "account", "loyalty"],
    "text": ["text", "review", "comment", "message", "tweet", "post", "content", "title",
             "description", "body", "subject", "email"],
    "marketing": ["campaign", "conversion", "click", "impression", "ad", "marketing",
                  "channel", "engagement", "bounce"],
    "energy": ["energy", "power", "electricity", "consumption", "kwh", "solar", "wind"],
    "security": ["attack", "intrusion", "malware", "threat", "vulnerability", "security"],
    "demand": ["demand", "quantity", "order", "inventory", "supply", "sales", "volume"],
    "iot": ["sensor", "temperature", "humidity", "pressure", "device", "reading"],
    "science": ["measurement", "experiment", "sample", "observation", "species", "specimen"],
    "image": ["pixel", "image", "width", "height", "channel", "resolution"],
}


def recommend_ml(csv_path: str, metrics: DatasetMetrics) -> MLRecommendation:
    """
    Analyze the dataset and return ML task + model recommendations + use cases.

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
            useCases=["general classification"],
        )

    col_analysis = _analyze_columns(df)
    domain = _detect_domain(df)

    # ── 1. Check for time series ────────────────────────────────
    if col_analysis["datetime_cols"]:
        numeric_targets = [c for c in col_analysis["numeric_cols"] if c not in col_analysis["datetime_cols"]]
        target = _pick_best_target(df, numeric_targets) if numeric_targets else None
        use_cases = _get_use_cases("time-series", domain)
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
            useCases=use_cases,
        )

    # ── 2. Check for NLP / text-heavy columns ──────────────────
    if col_analysis["text_cols"]:
        cat_cols = col_analysis["low_cardinality_cols"]
        target = cat_cols[0] if cat_cols else None
        use_cases = _get_use_cases("classification", "text" if not domain else domain)
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
            useCases=use_cases,
        )

    # ── 3. Pick the best target column ──────────────────────────
    target, is_categorical = _detect_target(df, col_analysis)

    if target and is_categorical:
        n_classes = df[target].nunique()
        use_cases = _get_use_cases("classification", domain)
        return MLRecommendation(
            task="classification",
            confidence=88,
            suggestedModels=_classification_models(n_classes),
            targetColumn=target,
            reasoning=(
                f"Target column '{target}' is categorical with {n_classes} classes. "
                "Classification is the most appropriate task."
            ),
            useCases=use_cases,
        )

    if target and not is_categorical:
        use_cases = _get_use_cases("regression", domain)
        return MLRecommendation(
            task="regression",
            confidence=85,
            suggestedModels=["XGBoost", "Random Forest", "Linear Regression", "LightGBM", "Ridge Regression"],
            targetColumn=target,
            reasoning=(
                f"Target column '{target}' is numeric with {df[target].nunique()} unique values. "
                "Regression is the most appropriate task."
            ),
            useCases=use_cases,
        )

    # ── 4. Fallback: clustering ─────────────────────────────────
    if len(col_analysis["numeric_cols"]) >= 3:
        use_cases = _get_use_cases("clustering", domain)
        return MLRecommendation(
            task="clustering",
            confidence=60,
            suggestedModels=["K-Means", "DBSCAN", "Gaussian Mixture", "Hierarchical Clustering"],
            reasoning=(
                "No clear target column detected. With multiple numeric features, "
                "unsupervised clustering may help discover hidden patterns."
            ),
            useCases=use_cases,
        )

    return MLRecommendation(
        task="classification",
        confidence=40,
        suggestedModels=["Random Forest", "XGBoost", "Logistic Regression"],
        reasoning="Unable to auto-detect the best task. Please specify a target column for better recommendations.",
        useCases=["general classification", "exploratory analysis"],
    )


def _detect_domain(df: pd.DataFrame) -> str:
    """Detect the domain of the dataset based on column names."""
    all_cols_lower = " ".join(df.columns.str.lower())

    scores: dict[str, int] = {}
    for domain, patterns in _DOMAIN_PATTERNS.items():
        score = sum(1 for p in patterns if p in all_cols_lower)
        if score > 0:
            scores[domain] = score

    if not scores:
        return ""

    # Return the domain with the most pattern matches
    return max(scores, key=scores.get)


def _get_use_cases(task: str, domain: str) -> list[str]:
    """Get relevant use cases for a given task and domain."""
    task_cases = _USE_CASE_PATTERNS.get(task, {})

    use_cases = []
    if domain and domain in task_cases:
        use_cases.extend(task_cases[domain])

    # Always add general use cases
    general = task_cases.get("general", [])
    for uc in general:
        if uc not in use_cases:
            use_cases.append(uc)

    return use_cases[:5]  # Limit to 5 use cases


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
