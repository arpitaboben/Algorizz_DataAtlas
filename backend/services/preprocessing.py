"""
Advanced No-Code Preprocessing Engine.
Provides production-grade data cleaning and transformation operations
using state-of-the-art techniques:
  - KNN Imputation, Iterative (MICE) Imputation
  - Yeo-Johnson / Box-Cox power transforms
  - Robust scaling, IQR-based outlier removal
  - Smart categorical encoding
  - Variance-based feature selection
"""
from __future__ import annotations
import logging
import os
import uuid
from pathlib import Path
from typing import Any
import pandas as pd
import numpy as np

from config import settings
from models.schemas import (
    DatasetMetrics, ColumnType, PreprocessStep, PreprocessResponse,
)
from services.eda_engine import run_eda

logger = logging.getLogger(__name__)


def apply_pipeline(
    csv_path: str,
    dataset_id: str,
    steps: list[PreprocessStep],
) -> PreprocessResponse:
    """
    Apply an ordered list of preprocessing steps to a dataset.
    Saves the cleaned CSV and returns before/after metrics.
    """
    # Read original
    try:
        df = pd.read_csv(csv_path, nrows=500_000)
    except Exception as e:
        logger.error(f"Failed to read CSV for preprocessing: {e}")
        return PreprocessResponse(
            dataset_id=dataset_id,
            success=False,
            summary=f"Failed to read dataset: {e}",
        )

    # Capture original metrics via EDA
    original_eda = run_eda(csv_path)
    original_metrics = original_eda.get("metrics", DatasetMetrics())
    original_rows, original_cols = df.shape

    applied_steps: list[str] = []
    summaries: list[str] = []

    # Apply each step in order
    for step in steps:
        try:
            action = step.action
            params = step.params or {}
            logger.info(f"Applying step: {action} with params: {params}")

            if action == "handle_missing":
                df, desc = _handle_missing(df, params)
            elif action == "remove_duplicates":
                df, desc = _remove_duplicates(df, params)
            elif action == "remove_correlated":
                df, desc = _remove_correlated(df, params)
            elif action == "handle_skewness":
                df, desc = _handle_skewness(df, params)
            elif action == "normalize":
                df, desc = _normalize(df, params)
            elif action == "remove_outliers":
                df, desc = _remove_outliers(df, params)
            elif action == "encode_categorical":
                df, desc = _encode_categorical(df, params)
            elif action == "drop_low_variance":
                df, desc = _drop_low_variance(df, params)
            else:
                desc = f"Unknown action: {action}"
                logger.warning(desc)
                continue

            applied_steps.append(action)
            summaries.append(desc)
            logger.info(f"Step '{action}' complete: {desc}")

        except Exception as e:
            logger.error(f"Preprocessing step '{step.action}' failed: {e}", exc_info=True)
            summaries.append(f"{step.action}: FAILED — {e}")

    # Save cleaned CSV
    clean_dir = Path(settings.DOWNLOAD_DIR) / "cleaned"
    clean_dir.mkdir(parents=True, exist_ok=True)
    clean_filename = f"{dataset_id}_cleaned_{uuid.uuid4().hex[:8]}.csv"
    clean_path = clean_dir / clean_filename
    df.to_csv(str(clean_path), index=False)
    logger.info(f"Saved cleaned dataset: {clean_path}")

    # Compute updated metrics
    updated_eda = run_eda(str(clean_path))
    updated_metrics = updated_eda.get("metrics", DatasetMetrics())

    final_rows, final_cols = df.shape
    rows_removed = original_rows - final_rows
    cols_removed = original_cols - final_cols
    cols_added = max(0, final_cols - original_cols)

    summary = "; ".join(summaries) if summaries else "No changes applied."

    return PreprocessResponse(
        dataset_id=dataset_id,
        success=True,
        original_metrics=original_metrics,
        updated_metrics=updated_metrics,
        applied_steps=applied_steps,
        rows_removed=rows_removed,
        columns_removed=max(0, cols_removed),
        columns_added=cols_added,
        download_filename=clean_filename,
        summary=summary,
    )


# ── Individual Preprocessing Operations ──────────────────────────

def _handle_missing(df: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, str]:
    """
    Handle missing values with multiple strategies:
    - drop_rows: Remove rows with any missing values
    - drop_cols: Remove columns with >50% missing
    - mean: Fill numeric with mean
    - median: Fill numeric with median
    - mode: Fill categorical with mode
    - knn: KNN Imputation (advanced)
    - iterative: Iterative/MICE Imputation (advanced)
    - smart: Auto-select best strategy per column
    """
    strategy = params.get("strategy", "smart")
    original_missing = df.isnull().sum().sum()

    if strategy == "drop_rows":
        before = len(df)
        df = df.dropna()
        return df, f"Dropped {before - len(df):,} rows with missing values"

    elif strategy == "drop_cols":
        threshold = params.get("threshold", 0.5)
        cols_before = df.shape[1]
        missing_ratios = df.isnull().mean()
        cols_to_drop = missing_ratios[missing_ratios > threshold].index.tolist()
        df = df.drop(columns=cols_to_drop)
        return df, f"Dropped {cols_before - df.shape[1]} columns with >{threshold*100:.0f}% missing"

    elif strategy == "mean":
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
        cat_cols = df.select_dtypes(include=["object", "category"]).columns
        for col in cat_cols:
            df[col] = df[col].fillna(df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown")
        filled = original_missing - df.isnull().sum().sum()
        return df, f"Filled {filled:,} missing values (mean for numeric, mode for categorical)"

    elif strategy == "median":
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
        cat_cols = df.select_dtypes(include=["object", "category"]).columns
        for col in cat_cols:
            df[col] = df[col].fillna(df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown")
        filled = original_missing - df.isnull().sum().sum()
        return df, f"Filled {filled:,} missing values (median for numeric, mode for categorical)"

    elif strategy == "mode":
        for col in df.columns:
            mode_val = df[col].mode()
            if not mode_val.empty:
                df[col] = df[col].fillna(mode_val.iloc[0])
        filled = original_missing - df.isnull().sum().sum()
        return df, f"Filled {filled:,} missing values using mode imputation"

    elif strategy == "knn":
        return _knn_impute(df, params)

    elif strategy == "iterative":
        return _iterative_impute(df, params)

    else:  # "smart" — auto-select best strategy per column
        return _smart_impute(df)


def _knn_impute(df: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, str]:
    """KNN Imputation — uses k-nearest neighbors to impute missing values."""
    try:
        from sklearn.impute import KNNImputer

        n_neighbors = params.get("n_neighbors", 5)

        # Separate numeric and categorical
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

        # KNN on numeric columns
        if numeric_cols:
            imputer = KNNImputer(n_neighbors=min(n_neighbors, len(df) - 1))
            df[numeric_cols] = imputer.fit_transform(df[numeric_cols])

        # Mode for categorical
        for col in cat_cols:
            mode_val = df[col].mode()
            if not mode_val.empty:
                df[col] = df[col].fillna(mode_val.iloc[0])

        remaining = df.isnull().sum().sum()
        return df, f"KNN imputation applied (k={n_neighbors}). {remaining} values still missing."

    except ImportError:
        logger.warning("scikit-learn not available for KNN imputation, falling back to median")
        return _handle_missing(df, {"strategy": "median"})


def _iterative_impute(df: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, str]:
    """Iterative (MICE) Imputation — multivariate imputation using chained equations."""
    try:
        from sklearn.experimental import enable_iterative_imputer  # noqa
        from sklearn.impute import IterativeImputer

        max_iter = params.get("max_iter", 10)

        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

        if numeric_cols:
            imputer = IterativeImputer(max_iter=max_iter, random_state=42)
            df[numeric_cols] = imputer.fit_transform(df[numeric_cols])

        for col in cat_cols:
            mode_val = df[col].mode()
            if not mode_val.empty:
                df[col] = df[col].fillna(mode_val.iloc[0])

        remaining = df.isnull().sum().sum()
        return df, f"Iterative (MICE) imputation applied ({max_iter} iterations). {remaining} values still missing."

    except ImportError:
        logger.warning("scikit-learn not available for iterative imputation, falling back to median")
        return _handle_missing(df, {"strategy": "median"})


def _smart_impute(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """
    Smart imputation — auto-select the best strategy per column:
    - <5% missing → median/mode
    - 5-30% missing → KNN
    - >30% missing → drop column
    """
    cols_dropped = []
    cols_knn = []
    cols_simple = []

    for col in df.columns:
        pct_missing = df[col].isnull().mean()
        if pct_missing == 0:
            continue
        elif pct_missing > 0.5:
            cols_dropped.append(col)
        elif pct_missing > 0.05:
            cols_knn.append(col)
        else:
            cols_simple.append(col)

    # Drop columns with >50% missing
    if cols_dropped:
        df = df.drop(columns=cols_dropped)

    # KNN on moderate missing columns (if sklearn available)
    if cols_knn:
        numeric_knn = [c for c in cols_knn if c in df.select_dtypes(include=[np.number]).columns]
        cat_knn = [c for c in cols_knn if c in df.select_dtypes(include=["object", "category"]).columns]

        if numeric_knn:
            try:
                from sklearn.impute import KNNImputer
                imputer = KNNImputer(n_neighbors=5)
                df[numeric_knn] = imputer.fit_transform(df[numeric_knn])
            except ImportError:
                df[numeric_knn] = df[numeric_knn].fillna(df[numeric_knn].median())

        for col in cat_knn:
            mode_val = df[col].mode()
            if not mode_val.empty:
                df[col] = df[col].fillna(mode_val.iloc[0])

    # Simple imputation for low-missing columns
    for col in cols_simple:
        if col not in df.columns:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            df[col] = df[col].fillna(df[col].median())
        else:
            mode_val = df[col].mode()
            if not mode_val.empty:
                df[col] = df[col].fillna(mode_val.iloc[0])

    parts = []
    if cols_dropped:
        parts.append(f"dropped {len(cols_dropped)} cols (>50% missing)")
    if cols_knn:
        parts.append(f"KNN imputed {len(cols_knn)} cols")
    if cols_simple:
        parts.append(f"median/mode filled {len(cols_simple)} cols")

    if parts:
        return df, f"Smart imputation: {', '.join(parts)}"
    return df, "No missing values to handle"


def _remove_duplicates(df: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, str]:
    """Remove duplicate rows."""
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    return df, f"Removed {removed:,} duplicate rows"


def _remove_correlated(df: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, str]:
    """
    Remove one column from each highly correlated pair.
    Keeps the column that appears first (leftmost).
    """
    threshold = params.get("threshold", 0.9)
    numeric_df = df.select_dtypes(include=[np.number])

    if numeric_df.shape[1] < 2:
        return df, "Not enough numeric columns for correlation analysis"

    corr_matrix = numeric_df.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))

    to_drop = set()
    for col in upper.columns:
        correlated = upper[col][upper[col] > threshold].index.tolist()
        to_drop.update(correlated)

    if to_drop:
        df = df.drop(columns=list(to_drop))
        return df, f"Removed {len(to_drop)} highly correlated columns (threshold={threshold}): {', '.join(sorted(to_drop)[:5])}"

    return df, f"No column pairs found with correlation > {threshold}"


def _handle_skewness(df: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, str]:
    """
    Apply power transforms to reduce skewness.
    Methods: log, sqrt, box_cox, yeo_johnson (default)
    """
    method = params.get("method", "yeo_johnson")
    target_cols = params.get("columns", None)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if target_cols:
        numeric_cols = [c for c in target_cols if c in numeric_cols]

    # Find skewed columns (|skewness| > 1)
    skewed_cols = []
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 10:
            continue
        skew = series.skew()
        if abs(skew) > 1:
            skewed_cols.append(col)

    if not skewed_cols:
        return df, "No significantly skewed columns detected"

    transformed = []
    for col in skewed_cols:
        try:
            if method == "log":
                # Only for strictly positive values
                if (df[col].dropna() > 0).all():
                    df[col] = np.log1p(df[col])
                    transformed.append(col)
            elif method == "sqrt":
                if (df[col].dropna() >= 0).all():
                    df[col] = np.sqrt(df[col])
                    transformed.append(col)
            elif method == "box_cox":
                from scipy import stats  # type: ignore
                series = df[col].dropna()
                if (series > 0).all():
                    df.loc[df[col].notna(), col], _ = stats.boxcox(series)
                    transformed.append(col)
            elif method == "yeo_johnson":
                from sklearn.preprocessing import PowerTransformer
                pt = PowerTransformer(method="yeo-johnson")
                mask = df[col].notna()
                if mask.sum() > 1:
                    df.loc[mask, col] = pt.fit_transform(df.loc[mask, [col]]).flatten()
                    transformed.append(col)
        except Exception as e:
            logger.warning(f"Skewness transform failed for '{col}': {e}")

    return df, f"Applied {method} transform to {len(transformed)} skewed columns: {', '.join(transformed[:5])}"


def _normalize(df: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, str]:
    """
    Normalize numeric columns.
    Methods: minmax (0-1), zscore (standard), robust (median/IQR)
    """
    method = params.get("method", "robust")
    target_cols = params.get("columns", None)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if target_cols:
        numeric_cols = [c for c in target_cols if c in numeric_cols]

    if not numeric_cols:
        return df, "No numeric columns to normalize"

    if method == "minmax":
        from sklearn.preprocessing import MinMaxScaler
        scaler = MinMaxScaler()
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        return df, f"Min-Max normalized {len(numeric_cols)} columns to [0, 1] range"

    elif method == "zscore":
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        return df, f"Z-score standardized {len(numeric_cols)} columns (mean=0, std=1)"

    elif method == "robust":
        from sklearn.preprocessing import RobustScaler
        scaler = RobustScaler()
        df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
        return df, f"Robust-scaled {len(numeric_cols)} columns (using median and IQR — outlier-resistant)"

    return df, f"Unknown normalization method: {method}"


def _remove_outliers(df: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, str]:
    """
    Remove outliers using IQR or Z-score method.
    """
    method = params.get("method", "iqr")
    threshold = params.get("threshold", 1.5)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    before = len(df)

    if method == "iqr":
        for col in numeric_cols:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            if IQR > 0:
                lower = Q1 - threshold * IQR
                upper = Q3 + threshold * IQR
                df = df[(df[col] >= lower) & (df[col] <= upper) | df[col].isna()]
    elif method == "zscore":
        from scipy import stats  # type: ignore
        for col in numeric_cols:
            z_scores = np.abs(stats.zscore(df[col].dropna()))
            mask = df[col].isna() | (pd.Series(np.abs(stats.zscore(df[col].fillna(df[col].median()))), index=df.index) < threshold)
            df = df[mask]

    removed = before - len(df)
    return df, f"Removed {removed:,} outlier rows using {method.upper()} method (threshold={threshold})"


def _encode_categorical(df: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, str]:
    """
    Encode categorical columns.
    Methods: onehot (for low cardinality), label (ordinal encoding)
    """
    method = params.get("method", "onehot")
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    if not cat_cols:
        return df, "No categorical columns to encode"

    if method == "onehot":
        # Only one-hot encode columns with ≤20 unique values
        ohe_cols = [c for c in cat_cols if df[c].nunique() <= 20]
        label_cols = [c for c in cat_cols if df[c].nunique() > 20]

        if ohe_cols:
            df = pd.get_dummies(df, columns=ohe_cols, drop_first=True, dtype=int)

        if label_cols:
            from sklearn.preprocessing import LabelEncoder
            for col in label_cols:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))

        return df, (
            f"One-hot encoded {len(ohe_cols)} columns (≤20 categories), "
            f"label encoded {len(label_cols)} high-cardinality columns"
        )

    elif method == "label":
        from sklearn.preprocessing import LabelEncoder
        for col in cat_cols:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
        return df, f"Label encoded {len(cat_cols)} categorical columns"

    return df, f"Unknown encoding method: {method}"


def _drop_low_variance(df: pd.DataFrame, params: dict) -> tuple[pd.DataFrame, str]:
    """Drop columns with very low variance (near-constant)."""
    threshold = params.get("threshold", 0.01)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    if not numeric_cols:
        return df, "No numeric columns for variance analysis"

    from sklearn.preprocessing import StandardScaler
    scaler = StandardScaler()
    scaled = pd.DataFrame(
        scaler.fit_transform(df[numeric_cols].fillna(0)),
        columns=numeric_cols,
    )
    variances = scaled.var()
    low_var_cols = variances[variances < threshold].index.tolist()

    # Also find columns with only 1 unique value
    single_val_cols = [c for c in df.columns if df[c].nunique() <= 1]
    all_drop = list(set(low_var_cols + single_val_cols))

    if all_drop:
        df = df.drop(columns=all_drop)
        return df, f"Dropped {len(all_drop)} low-variance/constant columns: {', '.join(all_drop[:5])}"

    return df, "No low-variance columns found"


def get_cleaned_csv_path(dataset_id: str, filename: str) -> str | None:
    """Return the path to a cleaned CSV file, or None if not found."""
    clean_path = Path(settings.DOWNLOAD_DIR) / "cleaned" / filename
    if clean_path.exists():
        return str(clean_path)
    return None
