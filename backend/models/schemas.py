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
    insights: list[str] = []
    score: Optional[float] = None
    scoreExplanation: Optional[str] = None
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
    insights: list[str] = []
    score: float = 0.0
    scoreExplanation: str = ""


# ── Health ─────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "healthy"
    available_sources: list[str] = []
    embedding_model_loaded: bool = False
