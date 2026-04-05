"""
Data Atlas — FastAPI Backend Entry Point.

Starts the server, loads the sentence-transformer model,
and registers all API routers.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("data_atlas")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler: load the sentence-transformer model at startup,
    clean up at shutdown.
    """
    logger.info("🚀 Starting Data Atlas Backend...")

    # Load embedding model
    try:
        from sentence_transformers import SentenceTransformer
        from services.query_processor import set_model

        logger.info("Loading embedding model (all-MiniLM-L6-v2)...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        set_model(model)
        logger.info("✅ Embedding model loaded successfully")
    except Exception as e:
        logger.warning(f"⚠️ Could not load embedding model: {e}")
        logger.warning("   Semantic search will fall back to keyword matching")

    # Log available data sources
    from config import settings
    sources = []
    if settings.kaggle_available:
        sources.append(f"Kaggle (user: {settings.KAGGLE_USERNAME})")
    else:
        logger.warning("⚠️ Kaggle API NOT configured — set KAGGLE_USERNAME and KAGGLE_KEY in .env")
    sources.append("HuggingFace (public API)")
    sources.append("GitHub (public API)")
    logger.info(f"📡 Available data sources: {', '.join(sources)}")

    yield  # ← Server is running

    logger.info("Shutting down Data Atlas Backend...")


# Create the app
app = FastAPI(
    title="Data Atlas API",
    description="AI-powered dataset discovery and intelligence platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from routers.health import router as health_router
from routers.search import router as search_router
from routers.datasets import router as datasets_router

app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(search_router, prefix="/api", tags=["Search"])
app.include_router(datasets_router, prefix="/api", tags=["Datasets"])


@app.get("/")
async def root():
    return {
        "name": "Data Atlas API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
