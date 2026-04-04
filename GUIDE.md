# Data Atlas — Complete Run Guide

Step-by-step instructions to run the entire platform and use every feature.

---

## Prerequisites

- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
- **Node.js 18+** — [nodejs.org](https://nodejs.org/)
- **Git** — [git-scm.com](https://git-scm.com/)

---

## 1. Configure Environment Variables

Create or update the `.env` file in the project root (`Data Atlas/.env`):

```env
# Required for Kaggle search (get at https://www.kaggle.com/settings)
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key

# Optional (public API works without these)
HUGGINGFACE_TOKEN=
GITHUB_TOKEN=
```

> **Note on Public APIs:**
> - **HuggingFace**: The Datasets API (`huggingface.co/api/datasets`) is completely public. No token needed. Adding a token only increases rate limits.
> - **GitHub**: The Search API allows 60 requests/hour without a token. A personal access token raises this to 30 requests/minute. Get one at [github.com/settings/tokens](https://github.com/settings/tokens).

---

## 2. Start the Backend (FastAPI)

Open a terminal:

```bash
cd "Data Atlas/Backend"

# Create virtual environment (first time only)
python -m venv venv

# Activate it
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

You should see:
```
🚀 Starting Data Atlas Backend...
Loading embedding model (all-MiniLM-L6-v2)...
✅ Embedding model loaded successfully
📡 Available data sources: Kaggle, HuggingFace (public API), GitHub (public API)
```

> The first startup downloads the AI model (~90MB). Subsequent starts are instant.

**Verify:** Open http://localhost:8000/api/health — should return available sources.

**API Docs:** Open http://localhost:8000/docs for interactive Swagger UI.

---

## 3. Start the Frontend (Next.js)

In a **separate terminal**:

```bash
cd "Data Atlas/DataAtlas"

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

Opens at: **http://localhost:3000**

---

## 4. Using the Platform

### 4.1 — Login
1. Open http://localhost:3000
2. Click "Get Started" or go to `/login`
3. Enter any email and password (mock auth for MVP)

### 4.2 — Search for Datasets
1. Navigate to the **Dashboard** (`/dashboard`)
2. Enter a search query, e.g.:
   - `"house prices prediction"`
   - `"sentiment analysis twitter"`
   - `"medical imaging cancer detection"`
3. Optionally add a description for better semantic matching
4. Apply filters (format, size, source, quality)
5. Click **Search**

**What happens behind the scenes:**
- Query is normalized and keywords extracted
- Sentence-transformer generates a semantic embedding
- All available sources (Kaggle, HuggingFace, GitHub) are searched concurrently
- Dataset descriptions are embedded and ranked by cosine similarity
- Results are returned sorted by AI relevance score

### 4.3 — Analyze a Dataset
1. Click **"View & Analyze Dataset"** on any search result
2. The system automatically:
   - Downloads the CSV file in the background
   - Runs Pandas-based EDA (stats, missing values, duplicates, correlations)
   - Computes a quality score (0–100)
   - Generates human-readable insights
   - Recommends ML tasks and models
3. View complete analysis on the dataset detail page:
   - **Quality Score** with explanation
   - **AI Insights** (e.g., "High missing values in column X")
   - **Dataset Metrics** (rows, columns, missing %, duplicates %)
   - **Column Information** (types, unique values, nulls)
   - **Data Preview** (first 10 rows)
   - **Distribution Charts** (histograms for numeric columns)
   - **Correlation Charts** (top correlated pairs)
   - **ML Recommendation** (suggested task, models, reasoning)

### 4.4 — Generate Starter Code
1. On the dataset detail page, click **"Generate Starter Code"**
2. A Python script with Pandas + sklearn boilerplate is copied to clipboard
3. Paste into your notebook and start training!

---

## 5. API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | System health + available sources |
| `/api/search` | POST | Search datasets across all sources |
| `/api/analyze` | POST | Download CSV + run full EDA pipeline |
| `/api/dataset/{id}` | GET | Get cached analysis results |
| `/docs` | GET | Interactive Swagger documentation |

### Example: Search Request

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "house prices", "limit": 10}'
```

### Example: Analyze Request

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "kaggle-abc123",
    "download_url": "https://www.kaggle.com/datasets/user/house-prices",
    "title": "House Prices",
    "source": "kaggle"
  }'
```

---

## 6. Troubleshooting

| Problem | Solution |
|---|---|
| "Failed to connect to backend" in frontend | Make sure FastAPI is running on port 8000 |
| "Kaggle API not configured" | Add `KAGGLE_USERNAME` and `KAGGLE_KEY` to `.env` |
| First search is slow | The AI model needs ~10s to load on first request |
| "Non-CSV format" error on analyze | Only CSV files are supported. Some datasets may not have CSV files |
| "File too large" error | Default max is 200MB. Change `MAX_DATASET_SIZE_MB` in `.env` |
| GitHub rate limit | Add `GITHUB_TOKEN` to `.env` for higher limits |

---

## 7. Project Configuration

All settings are in `.env`:

```env
KAGGLE_USERNAME=your_username    # Required for Kaggle
KAGGLE_KEY=your_key              # Required for Kaggle
HUGGINGFACE_TOKEN=               # Optional (public API)
GITHUB_TOKEN=                    # Optional (60 req/hr without)
MAX_DATASET_SIZE_MB=200          # Max CSV download size
DOWNLOAD_DIR=./downloads         # Where CSVs are saved
```
