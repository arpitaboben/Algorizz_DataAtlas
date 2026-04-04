"""
Health check router.
"""
from fastapi import APIRouter
from config import settings
from services import query_processor
from services.fetchers.kaggle_fetcher import KaggleFetcher
from services.fetchers.huggingface_fetcher import HuggingFaceFetcher
from services.fetchers.github_fetcher import GitHubFetcher

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return system health status and available data sources."""
    sources = []

    kaggle = KaggleFetcher()
    if await kaggle.is_available():
        sources.append("kaggle")

    hf = HuggingFaceFetcher()
    if await hf.is_available():
        sources.append("huggingface")

    gh = GitHubFetcher()
    if await gh.is_available():
        sources.append("github")

    model_loaded = query_processor._model is not None

    return {
        "status": "healthy",
        "available_sources": sources,
        "embedding_model_loaded": model_loaded,
    }
