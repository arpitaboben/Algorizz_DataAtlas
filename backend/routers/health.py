"""
Health check router.
"""
from fastapi import APIRouter
from config import settings
from services import query_processor

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return system health status and available data sources."""
    sources = []

    if settings.kaggle_available:
        sources.append("kaggle")

    # HuggingFace and GitHub public APIs are always available
    sources.append("huggingface")
    sources.append("github")

    return {
        "status": "healthy",
        "available_sources": sources,
        "embedding_model_loaded": query_processor._model is not None,
        "download_dir": settings.DOWNLOAD_DIR,
    }
