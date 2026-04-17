# Data Atlas — AI-Powered Dataset Discovery & Intelligence Platform

An intelligent platform that helps data scientists and ML engineers **discover, evaluate, and understand datasets** across multiple sources using AI-powered semantic search and automated analysis.

## 🎯 What It Does

| Feature | Description |
|---|---|
| **AI Semantic Search** | Natural language queries matched via sentence-transformers embeddings + cosine similarity |
| **Multi-Source Discovery** | Searches Kaggle, HuggingFace, and GitHub simultaneously |
| **Auto-Analysis** | Click any dataset → auto-downloads CSV → runs full EDA pipeline |
| **Quality Scoring** | 0–100 score based on missing values, duplicates, size, column variance |
| **Smart Insights** | Rule-based engine generates human-readable data quality findings |
| **ML Recommendations** | Detects target column type and recommends ML task + models |

## 🏗️ Architecture

```
┌─────────────────────┐     HTTP/JSON      ┌─────────────────────────┐
│   Next.js Frontend  │ ◄────────────────► │   FastAPI Backend       │
│   (Port 3000)       │                    │   (Port 8000)           │
│                     │                    │                         │
│  Dashboard          │                    │  /api/search            │
│  Dataset Detail     │                    │  /api/dataset/{id}      │
│  Login / Signup     │                    │  /api/analyze           │
│  Landing Page       │                    │  /api/health            │
└─────────────────────┘                    └────────┬────────────────┘
                                                    │
                                           ┌────────┴────────────────┐
                                           │     Service Layer       │
                                           │                         │
                                           │  Query Processor        │
                                           │  ├─ Normalize           │
                                           │  ├─ Keywords            │
                                           │  └─ Embeddings          │
                                           │                         │
                                           │  Fetchers               │
                                           │  ├─ Kaggle (SDK)        │
                                           │  ├─ HuggingFace (API)   │
                                           │  └─ GitHub (API)        │
                                           │                         │
                                           │  Search Engine          │
                                           │  ├─ Cosine Similarity   │
                                           │  └─ Ranking + Filters   │
                                           │                         │
                                           │  Analysis Pipeline      │
                                           │  ├─ EDA Engine           │
                                           │  ├─ Scoring (0-100)     │
                                           │  ├─ Insight Generator    │
                                           │  └─ ML Recommender      │
                                           └─────────────────────────┘
```

## 📂 Project Structure

```
DataAtlas/
├── Backend/                    # FastAPI backend
│   ├── main.py                 # App entry point + CORS + model loading
│   ├── config.py               # Environment configuration
│   ├── requirements.txt        # Python dependencies
│   ├── models/schemas.py       # Pydantic data models
│   ├── services/               # Business logic
│   │   ├── query_processor.py  # NLP query processing + embeddings
│   │   ├── search_engine.py    # Semantic search + ranking
│   │   ├── scoring.py          # Quality scoring (0-100)
│   │   ├── eda_engine.py       # CSV download + Pandas EDA
│   │   ├── insight_generator.py# Rule-based insights
│   │   ├── ml_recommender.py   # ML task/model recommendation
│   │   └── fetchers/           # Data source integrations
│   │       ├── kaggle_fetcher.py
│   │       ├── huggingface_fetcher.py
│   │       └── github_fetcher.py
│   └── routers/                # API endpoints
│       ├── search.py           # POST /api/search
│       ├── datasets.py         # GET/POST /api/dataset, /api/analyze
│       └── health.py           # GET /api/health
├── DataAtlas/                  # Next.js frontend
│   ├── app/                    # Pages (dashboard, dataset, login, etc.)
│   ├── components/             # UI components
│   └── lib/                    # API client, types, utilities
├── .env                        # API keys (gitignored)
├── README.md                   # This file
└── GUIDE.md                    # Full run guide
```

## 🔌 Data Source APIs

| Source | Auth Required? | How It Works |
|---|---|---|
| **Kaggle** | ✅ API key needed | Uses official Kaggle Python SDK. Get key at [kaggle.com/settings](https://www.kaggle.com/settings) |
| **HuggingFace** | ❌ Public API | Hits `https://huggingface.co/api/datasets?search=...` — no auth needed. Token optional for higher rate limits |
| **GitHub** | ❌ Public API | Uses GitHub Search API (`api.github.com/search/repositories`) — 60 req/hr unauthenticated, 30 req/min with token |

## 🚀 Current Status (MVP)

**What works now:**
- Full search pipeline across all 3 sources with AI ranking
- Auto-download and analysis of Kaggle CSV datasets
- Quality scoring, EDA, insights, and ML recommendations
- Beautiful Next.js frontend with real data

**Roadmap to Full Product:**

1. **Database**: Add PostgreSQL to persist users, search history, cached analyses
2. **Authentication**: Implement real JWT auth (currently mock)
3. **Async Processing**: Add Celery + Redis for background EDA tasks
4. **More Formats**: Support Parquet, JSON, Excel (currently CSV only)
5. **User Accounts**: Real Kaggle/GitHub/HuggingFace OAuth connections
6. **Advanced EDA**: Feature importance, outlier detection, auto-visualization
7. **Deployment**: Docker Compose for one-command startup, CI/CD pipeline
8. **Rate Limiting**: API rate limiting and caching layer
9. **Search History**: Save and revisit previous searches
10. **Dataset Comparison**: Compare multiple datasets side-by-side

## 📄 License

MIT
