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

---

## 8. Deployment Roadmap

This is the lowest-friction path for the current codebase:

1. Keep the Next.js frontend on Vercel.
2. Deploy the FastAPI backend to a free web service such as Render.
3. Point the Vercel frontend at the backend with `BACKEND_URL`.
4. Use only free, public data-source APIs where possible.
5. Accept the current MVP limits: in-memory cache, mock auth, and ephemeral downloads.

Why this path works for this repository:

- The frontend already proxies dataset actions through `/api/*` route handlers.
- Those route handlers call `BACKEND_URL` on the server side, so the browser does not need direct backend access.
- Kaggle, HuggingFace, and GitHub can all be reached from the backend without any paid infrastructure.
- The backend only needs temporary writable storage for downloaded CSVs.

Recommended rollout order:

1. Deploy backend first and confirm `/api/health`.
2. Set `BACKEND_URL` in Vercel.
3. Verify search and dataset analysis end to end.
4. Only after that, consider adding persistence, real auth, and background jobs.

---

## 9. Free Deployment Guide

### Recommended Free Stack

- Frontend: Vercel, already deployed at https://dataatlas-virid.vercel.app
- Backend: Render free web service
- Storage: none required for the MVP beyond temporary filesystem space
- Database: not required for the current MVP

This keeps the deployment fully free while matching the current architecture.

### Backend Deployment On Render

1. Push the repository to GitHub if it is not already there.
2. In Render, create a new Web Service from the repo.
3. Set the root directory to `Backend`.
4. Use the build command:

```bash
pip install -r requirements.txt
```

5. Use the start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

6. Add these environment variables in Render:

```env
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key
HUGGINGFACE_TOKEN=
GITHUB_TOKEN=
MAX_DATASET_SIZE_MB=200
DOWNLOAD_DIR=/tmp/data-atlas-downloads
```

7. Deploy and wait for the first boot to finish. The sentence-transformer model is loaded at startup, so the first boot will be slower than later requests.
8. Open `https://<your-render-app>.onrender.com/api/health` and confirm the backend is healthy.

### Frontend Configuration On Vercel

1. Open the Vercel project for the existing frontend deployment.
2. Add a production environment variable:

```env
BACKEND_URL=https://<your-render-app>.onrender.com
```

3. Redeploy the Vercel project.
4. Confirm the app still opens at `https://dataatlas-virid.vercel.app`.

### End-To-End Smoke Test

1. Open the homepage and log in with the MVP mock auth flow.
2. Go to the dashboard and run a dataset search.
3. Open a dataset result and verify the analysis page loads.
4. Trigger a dataset analysis on a public Kaggle dataset.
5. Confirm the backend returns analysis data and the frontend renders the score, metrics, and charts.

### Deployment Notes And Limits

- The current auth flow is mock-only and uses session storage, so it is fine for a demo but not for real users.
- The analysis cache is in memory, so it resets when the backend restarts.
- Downloads are written to local temp storage, so they are ephemeral on a free host.
- Free hosts may sleep after inactivity, which can make the first request slower.
- If you ever expose the backend directly to the browser, add `https://dataatlas-virid.vercel.app` to the backend CORS allowlist.

### Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| Frontend returns 502 from `/api/search` | `BACKEND_URL` is missing or wrong | Set `BACKEND_URL` in Vercel to the Render URL |
| Backend returns no Kaggle results | Kaggle credentials are missing or invalid | Recheck `KAGGLE_USERNAME` and `KAGGLE_KEY` |
| Analysis fails on startup | Free host ran out of memory or timed out during model load | Redeploy on a larger free-capable host or defer model loading |
| Dataset analysis fails for a file | Dataset does not contain a valid CSV or exceeds the size limit | Pick a different dataset or lower `MAX_DATASET_SIZE_MB` |
| Results disappear after a restart | Cache is in memory only | Add a database later if persistence is required |

### What To Improve Next

If you want to move beyond a demo, the next upgrades should be:

1. Add PostgreSQL for search history, saved datasets, and analysis cache.
2. Replace mock auth with real JWT or session-based auth.
3. Move dataset analysis to a background worker such as Celery or RQ.
4. Add durable object storage if you want to retain downloaded files.
5. Add a small rate-limit layer and request caching for the public APIs.
