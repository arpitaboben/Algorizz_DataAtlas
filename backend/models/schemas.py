"""
Pydantic schemas matching the frontend TypeScript types exactly.
These are the API contracts between FastAPI backend and Next.js frontend.
"""
from __future__ import annotations
from typing import Optional, Any
from pydantic import BaseModel, Field


# ── Dataset Types ──────────────────────────────────────────────

class ColumnType(BaseModel):
    name: str
    type: str  # 'string' | 'number' | 'boolean' | 'date' | 'object'
    nullCount: int = 0
    uniqueCount: int = 0


class DatasetMetrics(BaseModel):
    rows: int = 0
    columns: int = 0
    missingPercent: float = 0.0
    duplicatePercent: float = 0.0
    columnTypes: list[ColumnType] = []
    sampleData: list[dict[str, Any]] = []


class Correlation(BaseModel):
    column1: str
    column2: str
    value: float


class Distribution(BaseModel):
    column: str
    bins: list[dict[str, Any]] = []  # {label: str, count: int}


class MLRecommendation(BaseModel):
    task: str  # 'classification' | 'regression' | 'clustering' | 'time-series'
    confidence: int = 0
    suggestedModels: list[str] = []
    targetColumn: Optional[str] = None
    reasoning: str = ""
    useCases: list[str] = []


# ── Insight Types (Enhanced — Feature 2) ──────────────────────

class InsightItem(BaseModel):
    """Structured insight with title, description, context, and action."""
    title: str
    description: str
    why_it_matters: str
    suggested_action: str
    severity: str = "info"      # 'info' | 'warning' | 'critical'
    category: str = "general"   # 'missing' | 'duplicates' | 'correlation' | 'distribution' | 'size' | 'column'


# ── Score Breakdown (Feature 3) ───────────────────────────────

class ScoreComponent(BaseModel):
    """A single sub-score within the quality breakdown."""
    name: str
    score: float
    maxScore: float
    label: str
    description: str


class ScoreBreakdown(BaseModel):
    """Full breakdown of the quality score."""
    overall: float = 0.0
    components: list[ScoreComponent] = []


# ── Bias Detection (Feature 7) ────────────────────────────────

class BiasWarning(BaseModel):
    """A detected data bias or fairness issue."""
    type: str          # 'class_imbalance' | 'feature_skewness' | 'feature_dominance' | 'low_variance' | 'outlier_heavy'
    severity: str      # 'low' | 'medium' | 'high'
    title: str
    description: str
    affected_columns: list[str] = []
    suggestion: str = ""


# ── Next Steps (Feature 5) ────────────────────────────────────

class NextStep(BaseModel):
    """An actionable next step recommendation."""
    order: int
    title: str
    description: str
    action_type: str = "info"    # 'preprocess' | 'analyze' | 'model' | 'info'
    action_key: Optional[str] = None   # e.g. 'handle_missing', 'remove_duplicates'
    is_critical: bool = False


# ── Main Dataset Model ────────────────────────────────────────

class Dataset(BaseModel):
    id: str
    title: str
    description: str = ""
    source: str  # 'kaggle' | 'github' | 'huggingface'
    format: str = "csv"  # 'csv' | 'json' | 'parquet' | 'excel'
    size: str = "Unknown"
    sizeBytes: int = 0
    relevanceScore: float = 0.0
    qualityScore: str = "medium"  # 'high' | 'medium' | 'low'
    downloadUrl: str = ""
    previewUrl: Optional[str] = None
    tags: list[str] = []
    lastUpdated: str = ""
    author: str = ""
    license: str = "Unknown"


class DatasetDetails(Dataset):
    metrics: DatasetMetrics = Field(default_factory=DatasetMetrics)
    correlations: list[Correlation] = []
    distributions: list[Distribution] = []
    mlRecommendation: MLRecommendation = Field(
        default_factory=lambda: MLRecommendation(task="classification", reasoning="")
    )
    insights: list[InsightItem] = []
    score: Optional[float] = None
    scoreExplanation: Optional[str] = None
    scoreBreakdown: Optional[ScoreBreakdown] = None
    biasWarnings: list[BiasWarning] = []
    nextSteps: list[NextStep] = []
    warnings: list[str] = []  # CSV parsing / EDA warnings for the user


# ── Search Types ───────────────────────────────────────────────

class SearchFilters(BaseModel):
    format: Optional[list[str]] = None
    size: Optional[str] = None        # 'small' | 'medium' | 'large' | 'all'
    freshness: Optional[str] = None   # 'day' | 'week' | 'month' | 'year' | 'all'
    source: Optional[list[str]] = None
    quality: Optional[list[str]] = None


class SearchRequest(BaseModel):
    query: str
    description: Optional[str] = None
    filters: Optional[SearchFilters] = None
    page: int = 1
    limit: int = 20


class SearchResponse(BaseModel):
    datasets: list[Dataset] = []
    total: int = 0
    page: int = 1
    totalPages: int = 1


# ── Analysis Types ─────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    dataset_id: str
    download_url: str
    title: str = ""
    source: str = ""


class AnalyzeResponse(BaseModel):
    dataset_id: str
    metrics: DatasetMetrics = Field(default_factory=DatasetMetrics)
    correlations: list[Correlation] = []
    distributions: list[Distribution] = []
    mlRecommendation: MLRecommendation = Field(
        default_factory=lambda: MLRecommendation(task="classification", reasoning="")
    )
    insights: list[InsightItem] = []
    score: float = 0.0
    scoreExplanation: str = ""
    scoreBreakdown: Optional[ScoreBreakdown] = None
    biasWarnings: list[BiasWarning] = []
    nextSteps: list[NextStep] = []


# ── Comparison Types (Feature 1) ──────────────────────────────

class CompareRequest(BaseModel):
    dataset_ids: list[str]   # exactly 2


class DatasetSummary(BaseModel):
    """Lightweight summary used in comparison table."""
    id: str
    title: str
    source: str = ""
    rows: int = 0
    columns: int = 0
    missingPercent: float = 0.0
    duplicatePercent: float = 0.0
    qualityScore: float = 0.0
    qualityLabel: str = "medium"
    mlTask: str = ""
    targetColumn: Optional[str] = None
    numericColumnCount: int = 0
    categoricalColumnCount: int = 0
    avgNullsPerColumn: float = 0.0
    correlationStrength: str = "unknown"  # 'none' | 'weak' | 'moderate' | 'strong'
    sizeBytes: int = 0


class ComparisonResult(BaseModel):
    datasets: list[DatasetSummary] = []
    bestDatasetId: str = ""
    explanation: str = ""
    metricComparisons: list[dict[str, Any]] = []  # [{metric, dataset1_value, dataset2_value, winner}]


# ── Preprocessing Types (Feature 4) ──────────────────────────

class PreprocessStep(BaseModel):
    """A single preprocessing operation to apply."""
    action: str    # 'handle_missing' | 'remove_duplicates' | 'remove_correlated' | 'handle_skewness' | 'normalize' | 'remove_outliers' | 'encode_categorical' | 'drop_low_variance'
    params: dict[str, Any] = {}
    # Example params:
    #   handle_missing: {strategy: 'mean'|'median'|'mode'|'knn'|'iterative'|'drop_rows'|'drop_cols'}
    #   remove_correlated: {threshold: 0.9}
    #   handle_skewness: {method: 'log'|'sqrt'|'box_cox'|'yeo_johnson', columns: [...]}
    #   normalize: {method: 'minmax'|'zscore'|'robust', columns: [...]}
    #   remove_outliers: {method: 'iqr'|'zscore', threshold: 1.5}
    #   encode_categorical: {method: 'onehot'|'label'|'ordinal'}
    #   drop_low_variance: {threshold: 0.01}


class PreprocessRequest(BaseModel):
    dataset_id: str
    steps: list[PreprocessStep]


class PreprocessResponse(BaseModel):
    dataset_id: str
    success: bool = True
    original_metrics: DatasetMetrics = Field(default_factory=DatasetMetrics)
    updated_metrics: DatasetMetrics = Field(default_factory=DatasetMetrics)
    applied_steps: list[str] = []
    rows_removed: int = 0
    columns_removed: int = 0
    columns_added: int = 0
    download_filename: str = ""
    summary: str = ""


# ── Health ─────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "healthy"
    available_sources: list[str] = []
    embedding_model_loaded: bool = False
