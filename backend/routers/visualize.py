"""
On-Demand Visualization Router.
POST /api/visualize — generate chart data for selected columns.
POST /api/visualize/suggest — get chart recommendations for the dataset.
Returns JSON data (frontend renders the charts).
Does NOT auto-render — only on user request.
"""
from __future__ import annotations
import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


class VisualizeRequest(BaseModel):
    dataset_id: str
    columns: list[str]                # 1 or 2+ columns
    chart_type: str = "histogram"     # 'histogram', 'scatter', 'boxplot', 'violin', 'pie', 'area', 'heatmap', 'line'
    bins: int = 0                     # 0 = auto-detect; 5-100 user selectable
    normalize: bool = False           # For histograms: show density instead of count


class ChartData(BaseModel):
    chart_type: str
    columns: list[str]
    data: list[dict[str, Any]] = []
    stats: dict[str, Any] = {}
    error: Optional[str] = None


class SuggestRequest(BaseModel):
    dataset_id: str


class ChartSuggestion(BaseModel):
    chart_type: str
    columns: list[str]
    reason: str
    priority: int = 0   # Higher = more interesting


class SuggestResponse(BaseModel):
    suggestions: list[ChartSuggestion] = []


@router.post("/visualize/suggest", response_model=SuggestResponse)
async def suggest_charts(request: SuggestRequest):
    """
    Suggest interesting charts based on dataset structure.
    Analyzes column types, distributions, and correlations to recommend
    the most insightful visualizations.
    """
    from routers.datasets import _analysis_cache

    if request.dataset_id not in _analysis_cache:
        raise HTTPException(status_code=404, detail="Dataset not yet analyzed.")

    cached = _analysis_cache[request.dataset_id]
    metrics = cached.metrics
    correlations = cached.correlations or []

    suggestions: list[ChartSuggestion] = []
    numeric_cols = [c.name for c in metrics.columnTypes if c.type == "number"]
    categorical_cols = [c.name for c in metrics.columnTypes if c.type == "string"]

    # 1. High-correlation scatter plots
    for corr in sorted(correlations, key=lambda c: abs(c.value), reverse=True)[:3]:
        if abs(corr.value) >= 0.4:
            strength = "Strong" if abs(corr.value) >= 0.7 else "Moderate"
            suggestions.append(ChartSuggestion(
                chart_type="scatter",
                columns=[corr.column1, corr.column2],
                reason=f"{strength} correlation ({corr.value:+.2f}) — scatter plot reveals the relationship",
                priority=int(abs(corr.value) * 100),
            ))

    # 2. Categorical pie charts (low cardinality)
    for col_info in metrics.columnTypes:
        if col_info.type == "string" and 2 <= col_info.uniqueCount <= 10:
            suggestions.append(ChartSuggestion(
                chart_type="pie",
                columns=[col_info.name],
                reason=f"{col_info.uniqueCount} categories — pie chart shows proportions",
                priority=60,
            ))

    # 3. Skewed numeric distributions — histogram
    for col_info in metrics.columnTypes:
        if col_info.type == "number":
            suggestions.append(ChartSuggestion(
                chart_type="histogram",
                columns=[col_info.name],
                reason=f"See distribution shape, outliers, and spread",
                priority=40,
            ))
            # Only suggest the first 3 numeric columns
            if len([s for s in suggestions if s.chart_type == "histogram"]) >= 3:
                break

    # 4. Boxplot for comparing multiple numerics
    if len(numeric_cols) >= 2:
        suggestions.append(ChartSuggestion(
            chart_type="boxplot",
            columns=numeric_cols[:4],
            reason=f"Compare distributions and spot outliers across {min(4, len(numeric_cols))} numeric columns",
            priority=50,
        ))

    # 5. Violin for the column with highest null count (interesting shape)
    high_null = sorted(
        [c for c in metrics.columnTypes if c.type == "number" and c.nullCount > 0],
        key=lambda c: c.nullCount, reverse=True
    )
    if high_null:
        suggestions.append(ChartSuggestion(
            chart_type="violin",
            columns=[high_null[0].name],
            reason=f"{high_null[0].nullCount} nulls — violin plot shows density distribution",
            priority=45,
        ))

    # 6. Heatmap if 4+ numeric columns
    if len(numeric_cols) >= 4:
        suggestions.append(ChartSuggestion(
            chart_type="heatmap",
            columns=numeric_cols[:8],
            reason=f"Correlation heatmap across {min(8, len(numeric_cols))} features",
            priority=70,
        ))

    # Sort by priority
    suggestions.sort(key=lambda s: s.priority, reverse=True)

    return SuggestResponse(suggestions=suggestions[:8])


@router.post("/visualize", response_model=ChartData)
async def generate_visualization(request: VisualizeRequest):
    """
    Generate chart data for selected columns.
    Supports: histogram, scatter, boxplot, violin, pie, area, heatmap, line
    """
    from routers.datasets import _analysis_cache

    if request.dataset_id not in _analysis_cache:
        raise HTTPException(
            status_code=404,
            detail="Dataset not yet analyzed. Please analyze it first.",
        )

    # Find CSV
    download_dir = Path(settings.DOWNLOAD_DIR) / request.dataset_id
    csv_path = None
    if download_dir.exists():
        for f in download_dir.rglob("*.csv"):
            if f.stat().st_size > 0:
                csv_path = str(f)
                break

    if csv_path is None:
        raise HTTPException(status_code=404, detail="CSV file not found.")

    try:
        df = pd.read_csv(csv_path, nrows=100_000)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not read dataset: {e}")

    # Validate columns exist
    missing_cols = [c for c in request.columns if c not in df.columns]
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Column(s) not found: {', '.join(missing_cols)}",
        )

    chart_type = request.chart_type.lower()
    bins = request.bins if request.bins >= 5 else 0  # 0 = auto

    try:
        if chart_type == "histogram":
            return _generate_histogram(df, request.columns[0], bins, request.normalize)
        elif chart_type == "scatter":
            if len(request.columns) < 2:
                raise HTTPException(status_code=400, detail="Scatter plot requires exactly 2 columns.")
            return _generate_scatter(df, request.columns[0], request.columns[1])
        elif chart_type == "boxplot":
            return _generate_boxplot(df, request.columns)
        elif chart_type == "violin":
            return _generate_violin(df, request.columns[0], bins)
        elif chart_type == "pie":
            return _generate_pie(df, request.columns[0])
        elif chart_type == "area":
            return _generate_area(df, request.columns[0], bins)
        elif chart_type == "heatmap":
            return _generate_heatmap(df, request.columns)
        elif chart_type == "line":
            if len(request.columns) < 2:
                raise HTTPException(status_code=400, detail="Line chart requires at least 2 columns (x, y).")
            return _generate_line(df, request.columns[0], request.columns[1])
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown chart type: {chart_type}. "
                       f"Use: histogram, scatter, boxplot, violin, pie, area, heatmap, line.",
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Visualization error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not generate visualization.")


# ─── Chart Generators ────────────────────────────────────────────

def _generate_histogram(df: pd.DataFrame, column: str, bins: int = 0, normalize: bool = False) -> ChartData:
    """Generate histogram bin data for a single column."""
    series = df[column].dropna()

    if pd.api.types.is_numeric_dtype(series):
        if bins <= 0:
            bins = min(30, max(6, int(np.log2(len(series)) + 1)))
        bins = max(5, min(100, bins))

        counts, edges = np.histogram(series, bins=bins, density=normalize)
        data = []
        for i in range(len(counts)):
            lo, hi = float(edges[i]), float(edges[i + 1])
            label = f"{lo:.2f} – {hi:.2f}" if abs(hi) < 1000 else f"{lo:.0f} – {hi:.0f}"
            data.append({"label": label, "count": round(float(counts[i]), 6) if normalize else int(counts[i])})

        stats = {
            "mean": round(float(series.mean()), 4),
            "median": round(float(series.median()), 4),
            "std": round(float(series.std()), 4),
            "min": round(float(series.min()), 4),
            "max": round(float(series.max()), 4),
            "skewness": round(float(series.skew()), 4),
            "bins": bins,
        }
    else:
        value_counts = series.value_counts().head(25)
        data = [{"label": str(val)[:30], "count": int(count)} for val, count in value_counts.items()]
        total = len(series)
        shown = sum(d["count"] for d in data)
        if total > shown:
            data.append({"label": "Other", "count": total - shown})

        stats = {
            "unique_values": int(series.nunique()),
            "most_common": str(series.mode().iloc[0]) if not series.mode().empty else "N/A",
            "most_common_pct": round(float(series.value_counts(normalize=True).iloc[0] * 100), 1),
        }

    return ChartData(chart_type="histogram", columns=[column], data=data, stats=stats)


def _generate_scatter(df: pd.DataFrame, col_x: str, col_y: str) -> ChartData:
    """Generate scatter plot data for two numeric columns."""
    for col in [col_x, col_y]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            return ChartData(
                chart_type="scatter",
                columns=[col_x, col_y],
                error=f"Column '{col}' is not numeric. Scatter plots require numeric columns.",
            )

    clean_df = df[[col_x, col_y]].dropna()

    if len(clean_df) > 2000:
        clean_df = clean_df.sample(2000, random_state=42)

    data = [
        {"x": round(float(row[col_x]), 4), "y": round(float(row[col_y]), 4)}
        for _, row in clean_df.iterrows()
    ]

    corr = float(clean_df[col_x].corr(clean_df[col_y]))

    stats = {
        "correlation": round(corr, 4),
        "points": len(data),
        "x_range": [round(float(clean_df[col_x].min()), 4), round(float(clean_df[col_x].max()), 4)],
        "y_range": [round(float(clean_df[col_y].min()), 4), round(float(clean_df[col_y].max()), 4)],
    }

    return ChartData(chart_type="scatter", columns=[col_x, col_y], data=data, stats=stats)


def _generate_boxplot(df: pd.DataFrame, columns: list[str]) -> ChartData:
    """Generate boxplot statistics for one or more numeric columns."""
    data = []

    for col in columns[:5]:
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue

        series = df[col].dropna()
        if len(series) < 5:
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        whisker_low = float(series[series >= q1 - 1.5 * iqr].min())
        whisker_high = float(series[series <= q3 + 1.5 * iqr].max())
        outliers = series[(series < whisker_low) | (series > whisker_high)]

        data.append({
            "column": col,
            "min": round(whisker_low, 4),
            "q1": round(q1, 4),
            "median": round(float(series.median()), 4),
            "q3": round(q3, 4),
            "max": round(whisker_high, 4),
            "outliers": [round(float(v), 4) for v in outliers.head(50)],
            "outlier_count": int(len(outliers)),
        })

    if not data:
        return ChartData(chart_type="boxplot", columns=columns, error="No numeric columns suitable for boxplot.")

    return ChartData(chart_type="boxplot", columns=columns, data=data)


def _generate_violin(df: pd.DataFrame, column: str, bins: int = 0) -> ChartData:
    """Generate KDE density curve data for violin-style visualization."""
    if not pd.api.types.is_numeric_dtype(df[column]):
        return ChartData(chart_type="violin", columns=[column], error=f"'{column}' is not numeric.")

    series = df[column].dropna()
    if len(series) < 10:
        return ChartData(chart_type="violin", columns=[column], error="Too few data points for violin plot.")

    # Build KDE approximation using histogram with many bins
    n_bins = bins if bins >= 10 else 50
    counts, edges = np.histogram(series, bins=n_bins, density=True)

    # Smooth with running average
    kernel = np.ones(3) / 3
    smoothed = np.convolve(counts, kernel, mode='same')

    data = []
    max_density = float(smoothed.max()) if smoothed.max() > 0 else 1.0
    for i in range(len(smoothed)):
        mid = float((edges[i] + edges[i + 1]) / 2)
        density = float(smoothed[i])
        data.append({
            "value": round(mid, 4),
            "density": round(density, 6),
            "density_pct": round(density / max_density * 100, 1),
        })

    stats = {
        "mean": round(float(series.mean()), 4),
        "median": round(float(series.median()), 4),
        "std": round(float(series.std()), 4),
        "skewness": round(float(series.skew()), 4),
        "kurtosis": round(float(series.kurtosis()), 4),
        "n": len(series),
    }

    return ChartData(chart_type="violin", columns=[column], data=data, stats=stats)


def _generate_pie(df: pd.DataFrame, column: str) -> ChartData:
    """Generate pie chart data for a categorical column."""
    series = df[column].dropna()
    value_counts = series.value_counts().head(10)
    total = len(series)

    data = []
    for val, count in value_counts.items():
        data.append({
            "label": str(val)[:30],
            "count": int(count),
            "percentage": round(float(count / total * 100), 1),
        })

    # "Other" slice
    shown = sum(d["count"] for d in data)
    if total > shown:
        data.append({
            "label": "Other",
            "count": total - shown,
            "percentage": round(float((total - shown) / total * 100), 1),
        })

    stats = {
        "total_values": total,
        "unique_categories": int(series.nunique()),
        "top_category": str(value_counts.index[0]) if len(value_counts) > 0 else "N/A",
        "top_pct": round(float(value_counts.iloc[0] / total * 100), 1) if len(value_counts) > 0 else 0,
    }

    return ChartData(chart_type="pie", columns=[column], data=data, stats=stats)


def _generate_area(df: pd.DataFrame, column: str, bins: int = 0) -> ChartData:
    """Generate cumulative area chart (CDF) for a numeric column."""
    if not pd.api.types.is_numeric_dtype(df[column]):
        return ChartData(chart_type="area", columns=[column], error=f"'{column}' is not numeric.")

    series = df[column].dropna().sort_values()

    # Sample down if too many points
    if len(series) > 500:
        indices = np.linspace(0, len(series) - 1, 200, dtype=int)
        series = series.iloc[indices]

    data = []
    n = len(series)
    for i, val in enumerate(series):
        data.append({
            "value": round(float(val), 4),
            "cumulative_pct": round((i + 1) / n * 100, 2),
        })

    # Percentile stats
    full_series = df[column].dropna()
    stats = {
        "p10": round(float(full_series.quantile(0.10)), 4),
        "p25": round(float(full_series.quantile(0.25)), 4),
        "p50": round(float(full_series.quantile(0.50)), 4),
        "p75": round(float(full_series.quantile(0.75)), 4),
        "p90": round(float(full_series.quantile(0.90)), 4),
        "p99": round(float(full_series.quantile(0.99)), 4),
    }

    return ChartData(chart_type="area", columns=[column], data=data, stats=stats)


def _generate_heatmap(df: pd.DataFrame, columns: list[str]) -> ChartData:
    """Generate a correlation heatmap for selected numeric columns."""
    numeric_cols = [c for c in columns if pd.api.types.is_numeric_dtype(df[c])]

    if len(numeric_cols) < 2:
        return ChartData(chart_type="heatmap", columns=columns, error="Heatmap requires at least 2 numeric columns.")

    # Limit to 12 columns for readability
    numeric_cols = numeric_cols[:12]
    corr_matrix = df[numeric_cols].corr()

    data = []
    for row_col in numeric_cols:
        for col_col in numeric_cols:
            val = float(corr_matrix.loc[row_col, col_col])
            if np.isnan(val):
                val = 0.0
            data.append({
                "row": row_col,
                "col": col_col,
                "value": round(val, 4),
            })

    stats = {
        "columns": numeric_cols,
        "size": len(numeric_cols),
        "strongest_positive": None,
        "strongest_negative": None,
    }

    # Find strongest correlations (excluding diagonal)
    off_diag = [(r, c, corr_matrix.loc[r, c]) for r in numeric_cols for c in numeric_cols if r != c]
    if off_diag:
        max_corr = max(off_diag, key=lambda x: x[2])
        min_corr = min(off_diag, key=lambda x: x[2])
        stats["strongest_positive"] = f"{max_corr[0]} ↔ {max_corr[1]} ({max_corr[2]:+.3f})"
        stats["strongest_negative"] = f"{min_corr[0]} ↔ {min_corr[1]} ({min_corr[2]:+.3f})"

    return ChartData(chart_type="heatmap", columns=numeric_cols, data=data, stats=stats)


def _generate_line(df: pd.DataFrame, col_x: str, col_y: str) -> ChartData:
    """Generate line chart data for two columns (X as index, Y as values)."""
    if not pd.api.types.is_numeric_dtype(df[col_y]):
        return ChartData(chart_type="line", columns=[col_x, col_y], error=f"'{col_y}' must be numeric for Y axis.")

    clean_df = df[[col_x, col_y]].dropna()

    # Sort by X
    if pd.api.types.is_numeric_dtype(clean_df[col_x]):
        clean_df = clean_df.sort_values(col_x)

    # Sample down
    if len(clean_df) > 500:
        indices = np.linspace(0, len(clean_df) - 1, 300, dtype=int)
        clean_df = clean_df.iloc[indices]

    data = [
        {"x": (round(float(row[col_x]), 4) if pd.api.types.is_numeric_dtype(df[col_x]) else str(row[col_x])[:20]),
         "y": round(float(row[col_y]), 4)}
        for _, row in clean_df.iterrows()
    ]

    stats = {
        "points": len(data),
        "y_mean": round(float(df[col_y].mean()), 4),
        "y_trend": "increasing" if len(data) > 1 and data[-1]["y"] > data[0]["y"] else "decreasing",
    }

    return ChartData(chart_type="line", columns=[col_x, col_y], data=data, stats=stats)
