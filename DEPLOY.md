# TradeIQ Deployment Guide

## System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────┐
│    Frontend      │────▶│     Backend      │────▶│   Supabase    │
│    Next.js 16    │     │  Django 5 + ASGI │     │  PostgreSQL   │
│    :3000         │     │  Daphne :8000    │     │  (Cloud)      │
│  (Vercel)        │     │  (Railway/Render)│     └───────────────┘
└─────────────────┘     └──────────────────┘
                              │
                        ┌─────┴──────────┐
                        │  LLM API       │  DeepSeek / OpenRouter
                        │  Deriv API     │  WebSocket (live prices)
                        │  NewsAPI       │  Headlines & sentiment
                        │  Finnhub       │  Technicals & patterns
                        │  Bluesky       │  AT Protocol (publish)
                        │  Upstash Redis │  Channel layer (WS)
                        └────────────────┘
```

> **Important**: The backend uses Django Channels (Daphne ASGI) for WebSocket
> support and cannot run on serverless platforms like Vercel. The frontend
> can be deployed to Vercel, but the backend requires a persistent server
> (Railway, Render, Docker, or bare metal).

---

## Method 1: Docker Compose (Recommended for Local / Demo)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed
- `.env` file configured (see Environment Variables below)

### Steps

```bash
# 1. Clone the repository
git clone <repo-url> && cd "deriv hackathon"

# 2. Configure environment variables
cp .env.example .env
# Edit .env and fill in all API keys and database connection

# 3. One-click start
docker compose up --build

# Run in background
docker compose up --build -d

# View logs
docker compose logs -f

# Stop
docker compose down
```

### Access
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **Pipeline Demo**: http://localhost:3000/pipeline
- **Django Admin**: http://localhost:8000/admin/

### Custom Ports
```bash
BACKEND_PORT=9000 FRONTEND_PORT=4000 docker compose up --build
```

---

## Method 2: Direct Deployment (No Docker)

### Prerequisites
- Python 3.11+ (conda recommended)
- Node.js 20+
- npm

### Steps

```bash
# 1. Create conda environment
conda create -n tradeiq python=3.11 -y
conda activate tradeiq

# 2. Install backend dependencies
pip install -r backend/requirements.txt

# 3. Install frontend dependencies
cd frontend && npm ci && cd ..

# 4. Configure environment variables
cp .env.example .env
# Edit .env and fill in all values

cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local (point to your backend URL)

# 5. Run database migrations
cd backend && python manage.py migrate && cd ..

# 6. One-click start (production mode)
chmod +x scripts/start_prod.sh
./scripts/start_prod.sh
```

### Or Start Separately (Development Mode)

```bash
# Terminal 1: Backend (Daphne ASGI server)
chmod +x scripts/start_backend.sh
./scripts/start_backend.sh

# Terminal 2: Frontend (Next.js dev server)
chmod +x scripts/start_frontend.sh
./scripts/start_frontend.sh
```

---

## Method 3: Vercel (Frontend) + Railway (Backend)

This is the recommended approach for cloud deployment.

### Step 1: Deploy Backend to Railway

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login and initialize
railway login
railway init

# Deploy backend (uses backend/railway.toml + Dockerfile)
cd backend
railway up

# Set environment variables in Railway dashboard
# (All variables from .env.example)

# Note the deployed URL (e.g., https://tradeiq-backend-production.up.railway.app)
```

### Step 2: Deploy Frontend to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy frontend
cd frontend
vercel

# Set environment variables in Vercel dashboard:
# NEXT_PUBLIC_API_URL = https://your-railway-backend-url.up.railway.app/api
# NEXT_PUBLIC_WS_URL  = wss://your-railway-backend-url.up.railway.app/ws
# NEXT_PUBLIC_SUPABASE_URL = https://xxxxx.supabase.co
# NEXT_PUBLIC_SUPABASE_ANON_KEY = eyJxxxxx
# NEXT_PUBLIC_AUTH_CALLBACK_URL = https://your-vercel-url.vercel.app/auth/callback
```

### Step 3: Update CORS on Backend

Add your Vercel domain to `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` in
Railway environment variables:

```
ALLOWED_HOSTS=your-railway-url.up.railway.app,localhost
```

---

## Method 4: Render (Full-Stack)

Render supports the `render.yaml` blueprint for one-click deployment.

### Option A: Blueprint (Recommended)

1. Push code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click **New** -> **Blueprint**
4. Connect your GitHub repo (Render auto-detects `render.yaml`)
5. Fill in environment variables when prompted
6. Click **Apply**

### Option B: Manual Setup

1. Create **Backend** Web Service:
   - Root Directory: `backend`
   - Environment: Docker
   - Start Command: `daphne -b 0.0.0.0 -p $PORT tradeiq.asgi:application`

2. Create **Frontend** Web Service:
   - Root Directory: `frontend`
   - Environment: Docker
   - Add env var: `NEXT_OUTPUT=standalone`

3. Set all environment variables in each service dashboard

---

## Environment Variables Reference

### Backend Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | Supabase PostgreSQL connection string | Yes |
| `DJANGO_SECRET_KEY` | Django secret key (random 50+ char string) | Yes |
| `DEBUG` | Enable debug mode (`True`/`False`) | No (default: `True`) |
| `ALLOWED_HOSTS` | Comma-separated allowed hosts | No (default: `localhost,127.0.0.1`) |
| `SUPABASE_URL` | Supabase project URL | Yes |
| `SUPABASE_JWT_SECRET` | Supabase JWT secret (from dashboard) | Yes |
| `DEEPSEEK_API_KEY` | DeepSeek API key | Yes* |
| `OPENROUTER_API_KEY` | OpenRouter API key | Yes* |
| `DERIV_APP_ID` | Deriv API application ID | Yes |
| `DERIV_TOKEN` | Deriv API token | Yes |
| `NEWS_API_KEY` | NewsAPI.org API key | Yes |
| `FINNHUB_API_KEY` | Finnhub.io API key | Yes |
| `BLUESKY_HANDLE` | Bluesky account handle | Yes |
| `BLUESKY_APP_PASSWORD` | Bluesky app password | Yes |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Optional |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | Optional |
| `CALLBACK_URL` | OAuth callback URL | Optional |
| `REDIS_URL` | Upstash Redis URL (TLS) | Optional |

> *At least one of `DEEPSEEK_API_KEY` or `OPENROUTER_API_KEY` is required

### Frontend Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL | Yes |
| `NEXT_PUBLIC_WS_URL` | Backend WebSocket URL | Yes |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | Yes |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon/publishable key | Yes |
| `NEXT_PUBLIC_AUTH_CALLBACK_URL` | OAuth callback URL | Yes |

---

## Feature Verification

After deployment, verify all features are working:

```bash
# Check environment variables
conda run -n tradeiq python scripts/verify_env.py

# Run comprehensive feature tests
conda run --no-capture-output -n tradeiq python -u scripts/test_all_features.py
```

### Manual Verification Checklist

1. **Dashboard**: http://localhost:3000 - Shows real-time market data and KPIs
2. **Market Analysis**: http://localhost:3000/market - Ask analyst questions, view technicals
3. **Behavioral Coaching**: http://localhost:3000/behavior - Load demo scenarios, view patterns
4. **Content Engine**: http://localhost:3000/content - Generate and publish to Bluesky
5. **Agent Pipeline**: http://localhost:3000/pipeline - Run full 5-stage AI pipeline
6. **AI Chat**: Click sidebar chat icon, ask "Why did BTC spike today?"
7. **WebSocket**: Chat should show "connected" status badge

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Backend 502 / connection refused | Check `DATABASE_URL` is correct and Supabase project is active |
| LLM returns empty response | Verify `DEEPSEEK_API_KEY` or `OPENROUTER_API_KEY` has balance |
| Bluesky publish failed | Check `BLUESKY_HANDLE` and `BLUESKY_APP_PASSWORD` (Settings -> App Passwords) |
| Frontend shows FALLBACK mode | Ensure backend is running, check `NEXT_PUBLIC_API_URL` |
| Docker build failed | Run `docker compose build --no-cache` |
| WebSocket disconnected | Check `NEXT_PUBLIC_WS_URL`, ensure it uses `ws://` (local) or `wss://` (cloud) |
| DATABASE_URL parse error | URL-encode special chars in password: `@` -> `%40`, `#` -> `%23`, `:` -> `%3A` |
| Railway deploy fails | Check `railway.toml` is in `backend/` directory, ensure Dockerfile builds |
| Vercel build fails | Ensure `NEXT_OUTPUT` is NOT set (Vercel manages its own output) |
| CORS errors on cloud | Add frontend domain to `ALLOWED_HOSTS` env var on backend |

---

## Deployment File Reference

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Local Docker deployment (frontend + backend) |
| `backend/Dockerfile` | Backend Docker image (multi-stage, Daphne ASGI) |
| `frontend/Dockerfile` | Frontend Docker image (multi-stage, standalone Next.js) |
| `frontend/vercel.json` | Vercel deployment configuration |
| `backend/railway.toml` | Railway deployment configuration |
| `render.yaml` | Render blueprint (one-click full-stack deploy) |
| `.env.example` | Root environment variables template |
| `backend/.env.example` | Backend-specific env template |
| `frontend/.env.example` | Frontend-specific env template |
| `scripts/start_prod.sh` | One-click production start (no Docker) |
| `scripts/start_backend.sh` | Backend development server |
| `scripts/start_frontend.sh` | Frontend development server |
