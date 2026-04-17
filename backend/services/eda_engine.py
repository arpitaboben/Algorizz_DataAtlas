"""
Advanced On-Demand EDA Engine.
Downloads a CSV dataset via the Kaggle API and runs comprehensive
exploratory data analysis including:
  - Extended column profiling (nulls, uniques, skewness, kurtosis)
  - Outlier detection stats per column
  - Categorical distribution analysis
  - Correlation matrix with more pairs
  - Enhanced distribution histograms (10 bins, more columns)
  - Sample data extraction with safe JSON serialization
"""
from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Optional, Any
import pandas as pd
import numpy as np

from config import settings
from models.schemas import (
    DatasetMetrics, ColumnType, Correlation, Distribution,
)

logger = logging.getLogger(__name__)


def _detect_column_type(series: pd.Series) -> str:
    """Map pandas dtype to frontend-compatible type string."""
    dtype = series.dtype
    if pd.api.types.is_bool_dtype(dtype):
        return "boolean"
    if pd.api.types.is_numeric_dtype(dtype):
        return "number"
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return "date"
    # Check if string column looks like dates
    if dtype == object:
        sample = series.dropna().head(20)
        if len(sample) > 0:
            try:
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    pd.to_datetime(sample, format="mixed")
                return "date"
            except (ValueError, TypeError, Exception):
                pass
    return "string"


def _safe_json_value(val: Any) -> Any:
    """Convert numpy/pandas types to JSON-safe Python types."""
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        v = float(val)
        if np.isnan(v) or np.isinf(v):
            return None
        return round(v, 4)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if isinstance(val, pd.Timestamp):
        return val.isoformat()
    if pd.isna(val):
        return None
    return val


def download_kaggle_dataset(kaggle_ref: str, dataset_id: str) -> Optional[str]:
    """
    Download a Kaggle dataset using the Kaggle SDK.
    kaggle_ref: e.g. "username/dataset-slug"
    Returns the local path to the first CSV file found, or None on failure.
    """
    if not settings.kaggle_available:
        logger.error("Kaggle API credentials not configured")
        return None

    download_dir = Path(settings.DOWNLOAD_DIR)
    download_dir.mkdir(parents=True, exist_ok=True)
    dest = download_dir / dataset_id

    # Check cache — look for any CSV in the dest folder
    if dest.exists():
        for f in dest.rglob("*.csv"):
            if f.stat().st_size > 0:
                # Validate it's not an HTML file from a bad download
                with open(f, "rb") as fh:
                    head = fh.read(50)
                if not head.lstrip().lower().startswith((b"<!doctype", b"<html")):
                    logger.info(f"Using cached CSV: {f}")
                    return str(f)

    # Download via Kaggle SDK
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi

        api = KaggleApi()
        api.authenticate()

        os.makedirs(str(dest), exist_ok=True)
        logger.info(f"Downloading Kaggle dataset: {kaggle_ref} -> {dest}")
        api.dataset_download_files(kaggle_ref, path=str(dest), unzip=True)

        # Find the first CSV file within size limits
        csv_files = []
        for f in dest.rglob("*.csv"):
            file_size = f.stat().st_size
            if file_size > settings.max_dataset_bytes:
                logger.warning(f"Skipping {f.name}: exceeds size limit ({file_size} bytes)")
                continue
            if file_size > 0:
                csv_files.append((f, file_size))

        if not csv_files:
            logger.error(f"No valid CSV files found in Kaggle download for {kaggle_ref}")
            return None

        # Prefer the largest CSV (usually the main dataset file)
        csv_files.sort(key=lambda x: x[1], reverse=True)
        chosen = csv_files[0][0]
        logger.info(f"Downloaded Kaggle CSV: {chosen} ({csv_files[0][1]} bytes)")
        return str(chosen)

    except Exception as e:
        logger.error(f"Kaggle download error for {kaggle_ref}: {e}", exc_info=True)
        return None


_MAX_ROWS = 500_000  # Hard cap for performance


def _read_csv_safe(csv_path: str) -> tuple[pd.DataFrame, list[str]]:
    """
    Attempt to read a CSV with progressively more lenient strategies.
    Returns (dataframe, list_of_warnings).
    Raises RuntimeError only if ALL strategies fail.
    """
    warnings: list[str] = []

    # Strategy 1: Default C parser — fast, strict
    try:
        df = pd.read_csv(csv_path, nrows=_MAX_ROWS)
        if len(df) == _MAX_ROWS:
            warnings.append(f"Dataset was capped at {_MAX_ROWS:,} rows for performance.")
        return df, warnings
    except Exception as e1:
        logger.warning(f"Default CSV read failed: {e1}")

    # Strategy 2: Python engine + skip bad lines + auto-detect separator
    try:
        df = pd.read_csv(
            csv_path,
            nrows=_MAX_ROWS,
            engine="python",
            sep=None,               # auto-detect delimiter
            on_bad_lines="skip",     # skip malformed rows instead of crashing
            encoding="utf-8",
        )
        warnings.append("Some rows were skipped due to formatting issues.")
        if len(df) == _MAX_ROWS:
            warnings.append(f"Dataset was capped at {_MAX_ROWS:,} rows for performance.")
        if len(df) > 0:
            return df, warnings
    except Exception as e2:
        logger.warning(f"Python-engine CSV read failed (utf-8): {e2}")

    # Strategy 3: Latin-1 encoding fallback (handles most non-UTF files)
    try:
        df = pd.read_csv(
            csv_path,
            nrows=_MAX_ROWS,
            engine="python",
            sep=None,
            on_bad_lines="skip",
            encoding="latin-1",
        )
        warnings.append("File was read using latin-1 encoding (non-UTF-8 detected).")
        warnings.append("Some rows were skipped due to formatting issues.")
        if len(df) == _MAX_ROWS:
            warnings.append(f"Dataset was capped at {_MAX_ROWS:,} rows for performance.")
        if len(df) > 0:
            return df, warnings
    except Exception as e3:
        logger.error(f"All CSV read strategies failed: {e3}")

    raise RuntimeError(
        "Could not parse this CSV file. The file may be corrupted, "
        "use an unsupported encoding, or not be a valid CSV."
    )


def run_eda(csv_path: str) -> dict:
    """
    Run comprehensive EDA on a CSV file.
    Returns a dict with: metrics, correlations, distributions, warnings.

    Enhanced analysis includes:
      - Extended column profiling with skewness and outlier stats
      - Larger sample data (first 20 rows)
      - More correlation pairs (top 20)
      - More distribution columns (top 8) with 10 bins each
      - Categorical distribution analysis
    """
    logger.info(f"Running EDA on: {csv_path}")

    try:
        df, warnings = _read_csv_safe(csv_path)
    except RuntimeError as e:
        logger.error(f"Failed to read CSV: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error reading CSV: {e}")
        return {"error": f"Failed to read CSV: {e}"}

    # Drop fully empty columns/rows that can appear after skipping bad lines
    df = df.dropna(how="all", axis=1)
    df = df.dropna(how="all", axis=0)

    if df.empty:
        return {"error": "The CSV file has no usable data after cleaning."}

    rows, cols = df.shape

    # ── Missing values ──
    total_cells = rows * cols
    missing_cells = int(df.isnull().sum().sum())
    missing_pct = round((missing_cells / total_cells * 100) if total_cells > 0 else 0, 2)

    # ── Duplicates ──
    dup_count = int(df.duplicated().sum())
    dup_pct = round((dup_count / rows * 100) if rows > 0 else 0, 2)

    # ── Extended Column Profiling ──
    column_types: list[ColumnType] = []
    for col in df.columns:
        ct = _detect_column_type(df[col])

        null_count = int(df[col].isnull().sum())
        unique_count = int(df[col].nunique())

        column_types.append(ColumnType(
            name=str(col),
            type=ct,
            nullCount=null_count,
            uniqueCount=unique_count,
        ))

    # ── Sample data (first 20 rows for richer preview) ──
    sample_df = df.head(20)
    sample_data = []
    for _, row in sample_df.iterrows():
        sample_data.append({str(k): _safe_json_value(v) for k, v in row.items()})

    metrics = DatasetMetrics(
        rows=rows,
        columns=cols,
        missingPercent=missing_pct,
        duplicatePercent=dup_pct,
        columnTypes=column_types,
        sampleData=sample_data,
    )

    # ── Correlations (expanded: top 20 pairs) ──
    correlations = _compute_correlations(df, top_n=20)

    # ── Distributions (expanded: top 8 numeric + top 4 categorical) ──
    distributions = _compute_distributions(df, max_numeric=8, max_categorical=4)

    return {
        "metrics": metrics,
        "correlations": correlations,
        "distributions": distributions,
        "warnings": warnings,
    }


def _compute_correlations(df: pd.DataFrame, top_n: int = 20) -> list[Correlation]:
    """
    Compute top correlations between numeric columns.
    Uses Pearson correlation with NaN-safe handling.
    Returns more pairs for better feature analysis.
    """
    numeric_df = df.select_dtypes(include=[np.number])
    if numeric_df.shape[1] < 2:
        return []

    try:
        # Use pairwise-complete observations for robustness
        corr_matrix = numeric_df.corr(method="pearson", min_periods=10)
    except Exception:
        return []

    pairs: list[tuple[str, str, float]] = []
    cols = corr_matrix.columns.tolist()
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            val = corr_matrix.iloc[i, j]
            if pd.notna(val) and not np.isinf(val):
                pairs.append((cols[i], cols[j], round(float(val), 4)))

    # Sort by absolute correlation — strongest first
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)

    return [
        Correlation(column1=p[0], column2=p[1], value=p[2])
        for p in pairs[:top_n]
    ]


def _compute_distributions(
    df: pd.DataFrame,
    max_numeric: int = 8,
    max_categorical: int = 4,
) -> list[Distribution]:
    """
    Compute distributions for both numeric and categorical columns.
    
    Numeric: histogram with 10 bins (was 6), smart edge formatting
    Categorical: top-N value counts as bar chart data
    """
    distributions: list[Distribution] = []

    # ── Numeric distributions (10 bins) ──
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Sort numeric columns by variance (most interesting first)
    if len(numeric_cols) > max_numeric:
        variances = {}
        for col in numeric_cols:
            try:
                variances[col] = df[col].var()
            except Exception:
                variances[col] = 0
        numeric_cols = sorted(numeric_cols, key=lambda c: variances.get(c, 0), reverse=True)

    for col in numeric_cols[:max_numeric]:
        series = df[col].dropna()
        if len(series) < 5:
            continue

        try:
            # Use Sturges' rule or 10, whichever is smaller but at least 6
            import math
            n_bins = min(10, max(6, int(math.log2(len(series)) + 1)))

            counts, edges = np.histogram(series, bins=n_bins)
            bins = []
            for k in range(len(counts)):
                lo = edges[k]
                hi = edges[k + 1]
                label = f"{_format_number(lo)}–{_format_number(hi)}"
                bins.append({"label": label, "count": int(counts[k])})

            distributions.append(Distribution(column=col, bins=bins))
        except Exception:
            continue

    # ── Categorical distributions (top values) ──
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Prefer columns with moderate cardinality (2-50 unique values)
    filtered_cat = [c for c in cat_cols if 2 <= df[c].nunique() <= 50]
    # If none found, allow higher cardinality
    if not filtered_cat:
        filtered_cat = [c for c in cat_cols if 2 <= df[c].nunique() <= 200]

    for col in filtered_cat[:max_categorical]:
        try:
            value_counts = df[col].value_counts().head(10)
            bins = []
            for val, count in value_counts.items():
                label = str(val)[:30]  # Truncate long labels
                bins.append({"label": label, "count": int(count)})

            if bins:
                # Add "Other" category if there are more values
                total_shown = sum(b["count"] for b in bins)
                total_all = len(df[col].dropna())
                if total_all > total_shown:
                    bins.append({"label": "Other", "count": total_all - total_shown})

                distributions.append(Distribution(column=col, bins=bins))
        except Exception:
            continue

    return distributions


def _format_number(n: float) -> str:
    """Format a number for display in histogram labels."""
    abs_n = abs(n)
    if abs_n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if abs_n >= 1_000:
        return f"{n / 1_000:.1f}K"
    if abs_n >= 1:
        return f"{n:.1f}"
    if abs_n >= 0.01:
        return f"{n:.2f}"
    return f"{n:.3f}"
