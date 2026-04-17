# Data Atlas — Deployment Guide

Complete guide for deploying Data Atlas to production.

---

.
## Table of Contents
1. [Local Development](#1:local-development)
2. [VPS Deployment](#2:vps-deployment)
3. [Vercel + Railway](#3:vercel--railway)
4. [Environment Variables](#4:environment-variables)
5. [Architecture Overview](#5:architecture-overview)
6. [Health Checks & Monitoring](#6:health-checks--monitoring)
7. [Troubleshooting](#7:troubleshooting)

---

## 1. Local Development

### Prerequisites
- Python 3.10+
- Node.js 18+
- Kaggle API key (get at https://www.kaggle.com/settings)

### Step 1: Configure Environment
```bash
# In the project root (Data Atlas/)
cp Backend/.env.example .env
# Edit .env with your API keys
```

### Step 2: Start Backend
```bash
cd Backend

# Create virtual environment
python -m venv venv

# Activate
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server (auto-reload for dev)
uvicorn main:app --reload --port 8000
```

First startup downloads the AI model (~90MB). Subsequent starts are instant.

### Step 3: Start Frontend
```bash
cd DataAtlas
npm install
npm run dev
```

Open http://localhost:3000

---

## 2. VPS Deployment

For DigitalOcean, AWS EC2, Hetzner, etc.

### System Requirements
- **RAM:** 2GB minimum (4GB recommended for AI model)
- **Disk:** 10GB + space for downloaded datasets
- **CPU:** 2 cores minimum

### Setup Steps

```bash
# 1. Install system dependencies
sudo apt update && sudo apt install -y python3.11 python3.11-venv nodejs npm nginx

# 2. Clone your repo
git clone https://github.com/your-repo/data-atlas.git /opt/data-atlas
cd /opt/data-atlas

# 3. Configure environment
cp Backend/.env.example .env
nano .env  # Add your API keys

# 4. Setup Backend
cd Backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Pre-download AI model so first request is fast
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
deactivate

# 5. Setup Frontend
cd ../DataAtlas
npm ci
npm run build
```

### Systemd Service — Backend

Create `/etc/systemd/system/data-atlas-backend.service`:

```ini
[Unit]
Description=Data Atlas FastAPI Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/data-atlas/Backend
Environment="PATH=/opt/data-atlas/Backend/venv/bin"
EnvironmentFile=/opt/data-atlas/.env
ExecStart=/opt/data-atlas/Backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8000 --workers 1
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> **Note:** Use `--workers 1` because the sentence-transformers model is loaded in-memory. Multiple workers would each load a separate copy (~200MB each).

### Systemd Service — Frontend

Create `/etc/systemd/system/data-atlas-frontend.service`:

```ini
[Unit]
Description=Data Atlas Next.js Frontend
After=data-atlas-backend.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/data-atlas/DataAtlas
Environment="BACKEND_URL=http://127.0.0.1:8000"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Nginx Reverse Proxy

Create `/etc/nginx/sites-available/data-atlas`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API (direct access if needed)
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 120s;  # Analysis can take time
    }
}
```

### Enable & Start

```bash
# Enable nginx site
sudo ln -s /etc/nginx/sites-available/data-atlas /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx

# Start services
sudo systemctl enable --now data-atlas-backend data-atlas-frontend

# Add SSL with Certbot
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

## 3. Vercel + Railway

### Frontend on Vercel
1. Push `DataAtlas/` to a GitHub repo
2. Import to Vercel at https://vercel.com/new
3. Set environment variable:
   ```
   BACKEND_URL=https://your-backend.railway.app
   ```
4. Deploy

### Backend on Railway
1. Push `Backend/` to a GitHub repo
2. Import to Railway at https://railway.app/new
3. Set environment variables from `.env`
4. Add a `Procfile` in `Backend/`:
   ```
   web: uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
   ```

> **⚠️ Important:** Railway free tier has 512MB RAM. The sentence-transformers model needs ~400MB. Use a paid plan ($5/mo) for reliability.

---

## 4. Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `KAGGLE_USERNAME` | Yes (for Kaggle) | `""` | Kaggle API username |
| `KAGGLE_KEY` | Yes (for Kaggle) | `""` | Kaggle API key |
| `HUGGINGFACE_TOKEN` | No | `""` | HuggingFace token (higher rate limits) |
| `GITHUB_TOKEN` | No | `""` | GitHub token (higher rate limits) |
| `MAX_DATASET_SIZE_MB` | No | `200` | Max CSV file size to download |
| `DOWNLOAD_DIR` | No | `Backend/downloads/` | Where CSVs are saved |
| `BACKEND_URL` | No (frontend) | `http://localhost:8000` | Backend URL for Next.js proxy |

---

## 5. Architecture Overview

```
Internet
    │
    ▼
┌─────────────┐
│   Nginx /   │    Port 80/443
│   Vercel    │
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
   ▼       ▼
┌──────┐ ┌──────────┐
│Next.js│ │ FastAPI  │
│:3000  │ │ :8000    │
└──────┘ └────┬─────┘
              │
     ┌────────┼────────┐
     ▼        ▼        ▼
  Kaggle  HuggingFace GitHub
  (SDK)   (Public API) (Public API)
              │
              ▼
        ./downloads/
        (CSV cache)
```

### Download Location
Downloaded CSV files are stored in `Backend/downloads/<dataset-id>/`.
Configurable via the `DOWNLOAD_DIR` environment variable.

---

## 6. Health Checks & Monitoring

### Health Endpoint
```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "healthy",
  "available_sources": ["kaggle", "huggingface", "github"],
  "embedding_model_loaded": true,
  "download_dir": "/path/to/Backend/downloads"
}
```

### Key Metrics to Monitor
- **`/api/search` response time:** 2-10s normal, 10-30s on first search (model loading)
- **`/api/analyze` response time:** 10-60s depending on dataset size
- **Disk usage** of `downloads/` directory (datasets accumulate)
- **Memory usage:** ~400MB for model + variable for pandas analysis

### Cleanup
Periodically clean old downloads:
```bash
# Delete downloads older than 7 days
find /opt/data-atlas/Backend/downloads -type f -mtime +7 -delete
```

---

## 7. Troubleshooting

| Problem | Solution |
|---|---|
| Server crashes on startup | Check `routers/search.py` exists. Run `pip install -r requirements.txt` |
| "Failed to connect to backend" | Ensure FastAPI runs on port 8000. Check CORS in `main.py` |
| "Kaggle API not configured" | Set `KAGGLE_USERNAME` and `KAGGLE_KEY` in `.env` |
| First search is very slow | AI model downloads on first use (~90MB). Pre-download with the setup command |
| "No datasets found" | API rate limit or network issue. HuggingFace/GitHub should still work |
| Analysis fails with "Non-CSV" | Only CSV datasets supported. Some Kaggle datasets don't contain CSV files |
| Out of memory | AI model needs ~400MB RAM. Use 2GB+ for reliable operation |
| Downloads folder growing | Set up a cron job to clean downloads older than N days |
| `pydantic-settings` import error | Run `pip install pydantic-settings` — separate package from `pydantic` |
