"""
Data Augmentation Service.
Triggers only when dataset is small or imbalanced.
Implements:
  - SMOTE for classification (class imbalance)
  - Bootstrap + noise injection for regression (small dataset)
Returns before/after comparison stats and saves the augmented CSV.
"""
from __future__ import annotations
import logging
import uuid
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


def augment_dataset(
    csv_path: str,
    target_column: str,
    task_type: str = "classification",
    method: str = "auto",
) -> dict[str, Any]:
    """
    Augment a dataset based on the detected task type.

    Args:
        csv_path: Path to the CSV file.
        target_column: Name of the target column.
        task_type: 'classification' or 'regression'.
        method: 'smote', 'bootstrap', or 'auto' (auto-detect best).

    Returns:
        {
            "success": bool,
            "method_used": str,
            "before": {"rows": int, "class_distribution": dict | None},
            "after": {"rows": int, "class_distribution": dict | None},
            "rows_added": int,
            "download_filename": str,
            "summary": str,
        }
    """
    try:
        df = pd.read_csv(csv_path, nrows=500_000)
    except Exception as e:
        logger.error(f"Failed to read CSV for augmentation: {e}")
        return {"success": False, "summary": f"Could not read dataset: {e}"}

    if target_column not in df.columns:
        return {"success": False, "summary": f"Target column '{target_column}' not found in dataset."}

    original_rows = len(df)

    # Auto-detect method
    if method == "auto":
        if task_type == "classification":
            method = "smote"
        else:
            method = "bootstrap"

    if method == "smote":
        return _apply_smote(df, target_column, original_rows, csv_path)
    elif method == "bootstrap":
        return _apply_bootstrap(df, target_column, original_rows, csv_path)
    else:
        return {"success": False, "summary": f"Unknown augmentation method: {method}"}


def _apply_smote(
    df: pd.DataFrame,
    target_column: str,
    original_rows: int,
    csv_path: str,
) -> dict[str, Any]:
    """Apply SMOTE oversampling for imbalanced classification datasets."""
    try:
        from imblearn.over_sampling import SMOTE
    except ImportError:
        logger.warning("imbalanced-learn not installed — falling back to bootstrap")
        return _apply_bootstrap(df, target_column, original_rows, csv_path)

    # Separate features and target
    feature_cols = [c for c in df.columns if c != target_column]
    numeric_features = df[feature_cols].select_dtypes(include=[np.number]).columns.tolist()

    if len(numeric_features) < 2:
        return {
            "success": False,
            "summary": "SMOTE requires at least 2 numeric feature columns. Try bootstrap augmentation instead.",
        }

    # Prepare data — handle non-numeric features
    X = df[numeric_features].fillna(df[numeric_features].median())
    y = df[target_column]

    # Drop rows where target is NaN
    mask = y.notna()
    X = X[mask]
    y = y[mask]

    if y.nunique() < 2:
        return {"success": False, "summary": "Target column has fewer than 2 classes. SMOTE requires at least 2."}

    # Get before distribution
    before_dist = y.value_counts().to_dict()
    before_dist = {str(k): int(v) for k, v in before_dist.items()}

    # Check minimum samples per class for SMOTE
    min_samples = y.value_counts().min()
    k_neighbors = min(5, min_samples - 1)
    if k_neighbors < 1:
        k_neighbors = 1

    try:
        smote = SMOTE(k_neighbors=k_neighbors, random_state=42)
        X_resampled, y_resampled = smote.fit_resample(X, y)
    except Exception as e:
        logger.error(f"SMOTE failed: {e}")
        return {"success": False, "summary": f"SMOTE augmentation failed: {e}. Try bootstrap method."}

    # Reconstruct full DataFrame
    augmented_df = pd.DataFrame(X_resampled, columns=numeric_features)
    augmented_df[target_column] = y_resampled

    # Add back non-numeric columns from original (repeat last rows for new samples)
    non_numeric_cols = [c for c in df.columns if c not in numeric_features and c != target_column]
    if non_numeric_cols:
        # For the original rows, keep original values; for new rows, fill with mode
        original_non_numeric = df[non_numeric_cols].iloc[:len(X)]
        extra_rows = len(augmented_df) - len(original_non_numeric)
        if extra_rows > 0:
            fill_values = {col: df[col].mode().iloc[0] if not df[col].mode().empty else "Unknown"
                          for col in non_numeric_cols}
            extra_df = pd.DataFrame([fill_values] * extra_rows)
            combined_non_numeric = pd.concat([original_non_numeric.reset_index(drop=True), extra_df], ignore_index=True)
        else:
            combined_non_numeric = original_non_numeric.reset_index(drop=True)

        for col in non_numeric_cols:
            augmented_df[col] = combined_non_numeric[col].values[:len(augmented_df)]

    # Reorder columns to match original
    augmented_df = augmented_df[[c for c in df.columns if c in augmented_df.columns]]

    # After distribution
    after_dist = augmented_df[target_column].value_counts().to_dict()
    after_dist = {str(k): int(v) for k, v in after_dist.items()}

    # Save augmented CSV
    filename = _save_augmented(augmented_df, csv_path)

    rows_added = len(augmented_df) - original_rows
    return {
        "success": True,
        "method_used": "SMOTE",
        "before": {"rows": original_rows, "class_distribution": before_dist},
        "after": {"rows": len(augmented_df), "class_distribution": after_dist},
        "rows_added": rows_added,
        "download_filename": filename,
        "summary": f"SMOTE augmentation added {rows_added:,} synthetic samples. All classes are now balanced.",
    }


def _apply_bootstrap(
    df: pd.DataFrame,
    target_column: str,
    original_rows: int,
    csv_path: str,
) -> dict[str, Any]:
    """Apply bootstrap sampling + noise injection for small regression datasets."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Determine how many rows to add (target: at least 2x original, max 5x)
    target_rows = max(original_rows * 2, 1000)
    rows_to_add = min(target_rows - original_rows, original_rows * 4)

    if rows_to_add <= 0:
        return {
            "success": False,
            "summary": "Dataset is already large enough. Augmentation not needed.",
        }

    # Bootstrap: sample with replacement from original
    bootstrap_indices = np.random.choice(len(df), size=rows_to_add, replace=True)
    augmented_rows = df.iloc[bootstrap_indices].copy().reset_index(drop=True)

    # Add Gaussian noise to numeric columns (5% of std dev)
    for col in numeric_cols:
        std = df[col].std()
        if std > 0 and not np.isnan(std):
            noise = np.random.normal(0, std * 0.05, size=len(augmented_rows))
            augmented_rows[col] = augmented_rows[col] + noise

    # Combine original + augmented
    augmented_df = pd.concat([df, augmented_rows], ignore_index=True)

    # Save
    filename = _save_augmented(augmented_df, csv_path)

    return {
        "success": True,
        "method_used": "Bootstrap + Noise",
        "before": {"rows": original_rows, "class_distribution": None},
        "after": {"rows": len(augmented_df), "class_distribution": None},
        "rows_added": rows_to_add,
        "download_filename": filename,
        "summary": (
            f"Bootstrap augmentation added {rows_to_add:,} synthetic samples "
            f"with 5% Gaussian noise injection. Dataset grew from {original_rows:,} to {len(augmented_df):,} rows."
        ),
    }


def _save_augmented(df: pd.DataFrame, original_csv_path: str) -> str:
    """Save augmented DataFrame to disk and return the filename."""
    aug_dir = Path(settings.DOWNLOAD_DIR) / "augmented"
    aug_dir.mkdir(parents=True, exist_ok=True)

    original_name = Path(original_csv_path).stem
    filename = f"{original_name}_augmented_{uuid.uuid4().hex[:8]}.csv"
    save_path = aug_dir / filename
    df.to_csv(str(save_path), index=False)

    logger.info(f"Saved augmented dataset: {save_path} ({len(df)} rows)")
    return filename
