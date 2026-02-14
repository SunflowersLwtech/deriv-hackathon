<p align="center">
  <img src="frontend/public/tradeiq_favicon.svg" width="80" alt="TradeIQ Logo" />
</p>

<h1 align="center">TradeIQ</h1>

<p align="center">
  <strong>The Bloomberg Terminal for retail traders, the trading coach they never had, and the content team they always wanted.</strong>
</p>

<p align="center">
  <a href="https://deriv.com"><img src="https://img.shields.io/badge/Deriv_AI_Hackathon-2026-ff444f?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMMiAyMmgyMEwxMiAyeiIgZmlsbD0id2hpdGUiLz48L3N2Zz4=" alt="Deriv Hackathon 2026" /></a>
  <img src="https://img.shields.io/badge/Next.js-16-black?style=for-the-badge&logo=next.js" alt="Next.js" />
  <img src="https://img.shields.io/badge/Django-5-092E20?style=for-the-badge&logo=django" alt="Django" />
  <img src="https://img.shields.io/badge/DeepSeek-AI-4A90D9?style=for-the-badge" alt="DeepSeek" />
  <img src="https://img.shields.io/badge/Supabase-DB-3ECF8E?style=for-the-badge&logo=supabase" alt="Supabase" />
</p>

<p align="center">
  <a href="https://deepwiki.com/SunflowersLwtech/deriv-hackathon"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
</p>

---

## The Problem

Traders face two interconnected challenges: **understanding what's happening in markets** and **managing their own behaviour**. Professional traders have analyst teams for market insights and coaches for discipline. Retail traders have neither.

> *"I see the price dropped 5% but I don't know why. By the time I find the news, the move is over."*
>
> *"I didn't realise I was on a losing streak until I'd lost half my account. No one warned me."*
>
> *"I wish there was a trusted voice that explained what's happening in markets without the hype."*

**TradeIQ** bridges this gap with AI-powered intelligence across three pillars:

<table>
<tr>
<td width="33%" align="center">

**Market Analysis**

Real-time prices, streaming AI responses, proactive market alerts, technical indicators, sentiment analysis, and AI-powered market Q&A

</td>
<td width="33%" align="center">

**Behavioral Coaching**

Trade pattern detection, Trading Twin simulation (impulsive vs disciplined you), live narrator, proactive alerts, and risk scoring

</td>
<td width="33%" align="center">

**Social Content Engine**

Multi-persona AI content, few-shot style matching, community interaction, trending topic analysis, one-click publish to Bluesky

</td>
</tr>
</table>

> **Note**: TradeIQ provides educational analysis only. It does **not** provide trading signals, predictions, or financial advice.

---

## Killer Feature: Trading Twin

Your **Trading Twin** shows the cost of impulsive trading. It replays your trade history, splits it into two equity curves — your *actual* impulsive path vs a *disciplined* alternative that skips revenge trades and loss-chasing — and visualizes the gap with an animated dual-line chart.

```
Impulsive You:   $10,000 → $8,200  (-18.0%)  ████████░░░░
Disciplined You: $10,000 → $11,400 (+14.0%)  ████████████
                                    Gap: $3,200
```

AI-generated narrative explains *exactly* which behavior patterns cost you money, with pattern breakdown tags (Revenge Trading: 4 trades, Loss Chasing: 2 trades).

---

## Real-Time Architecture

```
                    ┌─────────────────────────────┐
                    │   Market Monitor (daemon)    │
                    │  Scans prices every 5s       │
                    │  Triggers on >1% volatility  │
                    └──────────┬──────────────────┘
                               │ event
                    ┌──────────▼──────────────────┐
                    │   5-Agent Pipeline           │
                    │  Monitor → Analyst → Advisor │
                    │  → Sentinel → Content        │
                    └──────────┬──────────────────┘
                               │ WebSocket push
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌────────────┐   ┌──────────────┐  ┌────────────┐
     │ Market     │   │ Live         │  │ Proactive  │
     │ Alert      │   │ Narrator     │  │ Behavioral │
     │ Toast      │   │ Bar          │  │ Nudges     │
     └────────────┘   └──────────────┘  └────────────┘
```

- **Streaming AI**: Token-by-token LLM responses via WebSocket (`stream_status` → `stream_chunk` → `stream_done`)
- **Proactive Alerts**: 5 rules (overtrading, consecutive losses, bad time, long session, weekly drawdown) — push to client without user action
- **Live Narrator**: One-liner trade commentary auto-clears after 5 seconds
- **Market Monitor**: Background daemon scanning Deriv prices, triggers full pipeline on volatility

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/SunflowersLwtech/deriv-hackathon.git
cd "deriv hackathon"
cp .env.example .env          # Fill in your API keys

# Backend
conda create -n tradeiq python=3.11 -y && conda activate tradeiq
pip install -r backend/requirements.txt
cd backend && python manage.py migrate && python manage.py runserver

# Frontend (new terminal)
cd frontend && npm ci && npm run dev
```

Open **http://localhost:3000** (frontend) and **http://localhost:8000/api/** (backend).

### After Pulling Latest Code

```bash
git pull origin <your-branch>

# Frontend — install any new packages (e.g. katex, framer-motion)
cd frontend && npm install && cd ..

# Backend — install any new Python packages
pip install -r backend/requirements.txt

# Run migrations if models changed
cd backend && python manage.py migrate && cd ..
```

---

## Deploy on Render (Recommended for Demo)

### One-Click Blueprint

1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com) → **New** → **Blueprint**
3. Connect your repo — Render auto-detects `render.yaml`
4. Fill in the environment variables when prompted (see below)
5. Click **Apply** — both backend and frontend deploy automatically

### Manual Setup

If you prefer to set up services manually:

**Backend (Web Service)**

| Setting | Value |
|---------|-------|
| Runtime | Docker |
| Dockerfile Path | `./backend/Dockerfile` |
| Docker Context | `./backend` |
| Health Check Path | `/healthz/` |
| Plan | Free (or Starter for demo) |

**Frontend (Web Service)**

| Setting | Value |
|---------|-------|
| Runtime | Docker |
| Dockerfile Path | `./frontend/Dockerfile` |
| Docker Context | `./frontend` |
| Plan | Free (or Starter for demo) |

### Required Environment Variables

**Backend** — set in Render Dashboard → Environment:

```bash
DATABASE_URL=postgresql://...              # Supabase connection string
DJANGO_SECRET_KEY=<auto-generated>
DEBUG=False
ALLOWED_HOSTS=*
CORS_ALLOWED_ORIGINS=https://<your-frontend>.onrender.com

# LLM (at least one)
DEEPSEEK_API_KEY=sk-xxxxx
OPENROUTER_API_KEY=sk-or-xxxxx

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret

# External APIs
DERIV_APP_ID=123456
DERIV_TOKEN=your-deriv-token
NEWS_API_KEY=your-newsapi-key
FINNHUB_API_KEY=your-finnhub-key

# Bluesky
BLUESKY_HANDLE=tradeiq-analyst.bsky.social
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx

# Redis (Upstash free tier — needed for WebSocket + alerts)
REDIS_URL=rediss://default:xxxxx@xxxxx.upstash.io:6379

# Real-time features
RUN_MONITOR=true                           # Start market monitor daemon
```

**Frontend** — set in Render Dashboard → Environment:

```bash
NEXT_PUBLIC_API_URL=https://<your-backend>.onrender.com/api
NEXT_PUBLIC_WS_URL=wss://<your-backend>.onrender.com/ws
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxxxx
NEXT_PUBLIC_AUTH_CALLBACK_URL=https://<your-frontend>.onrender.com/auth/callback
NEXT_OUTPUT=standalone
```

### Post-Deploy: Seed Demo Data

After deployment, seed demo data so all features work out of the box:

```bash
# Seed demo trades for Trading Twin + behavioral detection
curl -X POST https://<your-backend>.onrender.com/api/demo/seed/ \
  -H "Content-Type: application/json"

# Warm demo cache (pre-computes Trading Twin, multi-persona content)
curl -X POST https://<your-backend>.onrender.com/api/demo/run-script-v2/ \
  -H "Content-Type: application/json" \
  -d '{"script": "championship_run", "step_index": 0}'

# Check deployment health
curl https://<your-backend>.onrender.com/api/demo/health/
```

### WebSocket on Render

Render supports WebSocket natively on all web services. The backend runs **Daphne (ASGI)** which handles both HTTP and WebSocket on the same port. No extra configuration needed.

**Important**: Use `wss://` (not `ws://`) for the frontend WebSocket URL since Render enforces HTTPS.

### Demo Day Tips

- Use **Starter plan** ($7/mo) instead of Free to avoid cold starts during the pitch
- Run `POST /api/demo/health/` before going on stage to verify all dependencies
- If live markets are calm, use `POST /api/demo/trigger-event/` to simulate a volatility event
- The championship demo script runs 7 steps in ~120 seconds — perfect for a pitch

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 16, React 19, Tailwind CSS 4, Recharts, Framer Motion |
| **Backend** | Django 5, DRF, Django Channels (Daphne ASGI), WebSocket |
| **AI/LLM** | DeepSeek V3 via OpenRouter (streaming + function calling + multi-agent pipeline) |
| **Database** | Supabase PostgreSQL, Upstash Redis (channel layer + cache) |
| **Auth** | Supabase Auth (Google OAuth, JWT) |
| **External APIs** | Deriv WebSocket, NewsAPI, Finnhub, Bluesky AT Protocol |
| **Deployment** | Docker multi-stage builds, Render Blueprint, Railway support |

---

## 5-Agent Pipeline

```
[1] Market Monitor ──> [2] Event Analyst ──> [3] Portfolio Advisor
      (Deriv API)          (News + LLM)          (User positions)
       │ daemon                                        │
       │ pushes alerts                                 │
       ▼                                               ▼
  [WebSocket]         [4] Behavioral Sentinel <────────┘
  (real-time)              (Trade history + Trading Twin)
       │                          │
       ▼                          ▼
  Browser push          [5] Content Creator
  (toasts, narrator)        (Multi-persona Bluesky posts)
```

Each agent receives structured input from the previous stage, runs DeepSeek function calling with specialized tools, and passes results forward. The pipeline produces a complete analysis from raw market event to published Bluesky post — all streamed to the browser in real-time.

---

<details>
<summary><h2>External APIs & Integration Details</h2></summary>

### Deriv WebSocket API
- **Live prices** (`ticks`) and **OHLC candles** (`ticks_history`)
- **Trade history** (`profit_table`) for behavioral analysis
- **Portfolio** and **balance** for real-time account data
- **Active symbols** for dynamic instrument listing
- **Reality check** for official session health data
- Connection: `wss://ws.derivws.com/websockets/v3?app_id=YOUR_APP_ID`

### Finnhub API
- **Economic calendar** (`/calendar/economic`) — explains "why did EUR/USD drop?"
- **Chart pattern recognition** (`/scan/pattern`) — head-and-shoulders, triangles, etc.
- **Real-time quotes** (`/quote`) — fallback for Deriv coverage gaps
- **Market news** (`/news`) — aggregated with NewsAPI

### NewsAPI
- **Top headlines** (`/v2/top-headlines?category=business`) — dashboard news feed
- **Keyword search** (`/v2/everything`) — instrument-specific news for sentiment
- Domain filtering for authoritative sources (Reuters, Bloomberg, CNBC)

### Bluesky AT Protocol
- **Post publishing** with auto-hashtag facets (`#TradeIQ #trading`)
- **Thread publishing** for multi-part analysis
- **Link card embeds** for news source references
- **Post search** for social sentiment analysis and trending topics
- **Community engagement** — AI-drafted replies to trending posts
- Authentication via app password (not OAuth)

</details>

---

<details>
<summary><h2>API Reference</h2></summary>

All endpoints served under `/api/`. Auth via `Authorization: Bearer <supabase_jwt>` (most endpoints work without auth for demo).

### Market Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/market/ask/` | Ask AI market analyst a question |
| `POST` | `/api/market/brief/` | Market summary for instruments |
| `POST` | `/api/market/price/` | Live price (Deriv WebSocket) |
| `POST` | `/api/market/history/` | OHLC candles |
| `POST` | `/api/market/technicals/` | SMA, RSI, support/resistance |
| `POST` | `/api/market/sentiment/` | AI sentiment analysis |
| `GET` | `/api/market/calendar/` | Economic calendar (Finnhub) |
| `GET` | `/api/market/headlines/` | Top headlines (NewsAPI) |
| `GET` | `/api/market/instruments/` | Active symbols (Deriv) |
| `POST` | `/api/market/patterns/` | Chart patterns (Finnhub) |

### Behavioral Coaching

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/behavior/trades/` | Trade history |
| `POST` | `/api/behavior/trades/analyze_batch/` | Pattern detection |
| `POST` | `/api/behavior/trades/sync_deriv/` | Sync from Deriv account |
| `POST` | `/api/behavior/trading-twin/` | Trading Twin simulation |
| `GET` | `/api/behavior/portfolio/` | Deriv portfolio |
| `GET` | `/api/behavior/balance/` | Deriv balance |
| `GET` | `/api/behavior/reality-check/` | Deriv reality check |

### Content Engine

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/content/generate/` | Generate social content (few-shot enhanced) |
| `POST` | `/api/content/publish-bluesky/` | Publish to Bluesky |
| `GET` | `/api/content/bluesky-search/` | Search Bluesky posts |
| `GET` | `/api/content/personas/` | List AI personas |
| `POST` | `/api/content/community/` | Trending topics + reply drafts |
| `POST` | `/api/content/multi-persona/` | 3-persona simultaneous content |

### Agent Pipeline

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/agents/pipeline/` | Full 5-stage pipeline |
| `POST` | `/api/agents/monitor/` | Stage 1: Market Monitor |
| `POST` | `/api/agents/analyst/` | Stage 2: Event Analyst |
| `POST` | `/api/agents/advisor/` | Stage 3: Portfolio Advisor |
| `POST` | `/api/agents/sentinel/` | Stage 4: Behavioral Sentinel |
| `POST` | `/api/agents/content-gen/` | Stage 5: Content Creator |
| `POST` | `/api/agents/chat/` | Auto-routed chat |

### Demo & Presentation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/demo/seed/` | Initialize demo data |
| `POST` | `/api/demo/analyze/` | Load scenario + analyze |
| `POST` | `/api/demo/wow-moment/` | Three-pillar combined demo |
| `POST` | `/api/demo/trigger-event/` | Simulate volatility event for demo |
| `GET` | `/api/demo/health/` | 6-point dependency health check |
| `POST` | `/api/demo/run-script-v2/` | Championship demo script (7 steps, 4 acts) |
| `GET` | `/api/demo/scripts/` | List available demo scripts |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://host/ws/chat/<user_id>/` | Streaming AI chat + pipeline results |
| Messages: `stream_status`, `stream_chunk`, `stream_done` | Token-by-token LLM streaming |
| Messages: `market_alert`, `narrator` | Proactive push notifications |

</details>

---

<details>
<summary><h2>Behavioral Detection Algorithms</h2></summary>

### Revenge Trading
- **Trigger**: 3+ trades within 10 minutes after a loss
- **Severity**: Low (3 trades), Medium (4), High (5+)
- **Nudge**: "I notice you've made several trades quickly after a loss. Consider taking a breath."

### Overtrading
- **Trigger**: Daily trade count > 2x historical average
- **Severity**: Low (2-2.5x), Medium (2.5-3x), High (3x+)
- **Nudge**: "You're at X trades today, which is Y times your average. Quality over quantity."

### Loss Chasing
- **Trigger**: 2+ consecutive losses with 20%+ position size increase
- **Severity**: Based on consecutive count and size escalation
- **Nudge**: "I see increasing position sizes after losses. Classic loss-chasing pattern."

### Time-Based Patterns
- **Trigger**: Win rate < 35% during specific hours (min 3 trades/hour)
- **Output**: Identifies worst-performing trading hours

All nudges are **supportive, not restrictive** — they inform and suggest, never block or judge.

</details>

---

<details>
<summary><h2>Project Structure</h2></summary>

```
TradeIQ/
├── frontend/                  # Next.js 16 (React 19)
│   ├── src/app/               # App Router pages (dashboard, market, behavior, content, pipeline)
│   ├── src/components/        # 30+ React components
│   │   ├── layout/            # AppShell (sidebar, alerts, narrator)
│   │   ├── market/            # MarketDashboard, PriceCard, CandlestickChart
│   │   ├── behavior/          # TradingTwinChart, BehavioralDashboard
│   │   ├── chat/              # ChatPanel (streaming), ThinkingProcess
│   │   ├── alerts/            # MarketAlertToast (proactive push)
│   │   ├── narrator/          # NarratorBar (live commentary)
│   │   └── ui/                # Shared UI primitives
│   ├── src/hooks/             # useMarketData, useTradingTwin, useNarrator, useMarketAlerts, useStreamingChat
│   └── src/lib/               # API client (70+ types), WebSocket client, Supabase client
│
├── backend/                   # Django 5 + DRF + Channels
│   ├── agents/                # AI Agent Team (router, agent_team, tools_registry, compliance)
│   ├── market/                # Market Analysis (Deriv WebSocket, Finnhub, NewsAPI, MarketMonitor daemon)
│   ├── behavior/              # Behavioral Coach (detection, Trading Twin engine, Deriv client)
│   ├── content/               # Content Engine (personas, few-shot examples, community, multi-persona, Bluesky)
│   ├── chat/                  # WebSocket consumer (streaming, auto-routing)
│   ├── demo/                  # Demo system (V2 script, fallback cache, health check, scenarios)
│   └── tradeiq/               # Django config (settings, ASGI, JWT auth middleware)
│
├── render.yaml                # Render Blueprint (one-click deploy)
├── docker-compose.yml         # Local Docker deployment
├── .env.example               # Environment variables template
├── scripts/                   # Setup, start, and verification scripts
└── dev/                       # Architecture diagrams and design docs
```

</details>

---

<details>
<summary><h2>Environment Variables</h2></summary>

```bash
# Database
DATABASE_URL=postgresql://...          # Supabase connection string

# Django
DJANGO_SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# LLM (need at least one)
DEEPSEEK_API_KEY=...                   # Direct DeepSeek
OPENROUTER_API_KEY=...                 # OpenRouter (recommended)

# Deriv API (free at api.deriv.com)
DERIV_APP_ID=...                       # App registration ID
DERIV_TOKEN=...                        # API token (read + trade scope)

# News & Data
NEWS_API_KEY=...                       # newsapi.org
FINNHUB_API_KEY=...                    # finnhub.io

# Social
BLUESKY_HANDLE=...                     # your-handle.bsky.social
BLUESKY_APP_PASSWORD=...               # App password (not main password)

# Auth
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_JWT_SECRET=...
GOOGLE_CLIENT_ID=...                   # For Google OAuth

# Redis (needed for WebSocket + real-time alerts)
REDIS_URL=rediss://...                 # Upstash free tier

# Real-time features
RUN_MONITOR=true                       # Start market monitor daemon on boot

# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
```

All API keys work on **free tiers** for hackathon demo purposes.

</details>

---

<details>
<summary><h2>Demo Scenarios</h2></summary>

### Classic Scenarios

Pre-configured behavioral patterns for live demo:

| Scenario | Trades | Pattern | Expected Detection |
|----------|--------|---------|-------------------|
| `revenge_trading` | 5 trades in 8 min after -$200 loss | Rapid trading post-loss | Revenge trading (high) |
| `overtrading` | 22 trades in 80 min (2.75x avg) | Excessive frequency | Overtrading (medium) |
| `loss_chasing` | 4 consecutive losses, 1.5x size increase | Position size escalation | Loss chasing (high) |
| `healthy_session` | 6 trades, 60% win rate | Disciplined trading | No patterns (healthy) |

### Championship Demo Script (V2)

A 7-step, 4-act, ~120-second championship demo designed for hackathon pitches:

| Act | Step | What Happens | Wow Factor |
|-----|------|-------------|------------|
| 1 - Hook | 1. Market Alert | Simulated volatility event triggers real-time push | Toast appears without user action |
| 1 - Hook | 2. Streaming Analysis | AI analyzes the event token-by-token | Visible thinking process |
| 2 - Core | 3. Trading Twin | Generate dual equity curve | Animated gap visualization |
| 2 - Core | 4. Behavioral Detection | Pattern detection on demo trades | Real-time nudge push |
| 3 - Scale | 5. Multi-Persona Content | 3 AI personas write about same event | Side-by-side comparison |
| 3 - Scale | 6. Community Engagement | Discover trending topics + draft reply | AI community interaction |
| 4 - Close | 7. Health Dashboard | Show all systems operational | 6-point dependency check |

```bash
# Run the full championship demo
curl -X POST http://localhost:8000/api/demo/run-script-v2/ \
  -H "Content-Type: application/json" \
  -d '{"script": "championship_run", "step_index": 0}'

# Simulate a market event (when markets are calm)
curl -X POST http://localhost:8000/api/demo/trigger-event/ \
  -H "Content-Type: application/json" \
  -d '{"instrument": "frxEURUSD", "change_pct": 1.5}'

# Check all systems before demo
curl http://localhost:8000/api/demo/health/
```

</details>

---

<details>
<summary><h2>Design Decisions</h2></summary>

| Decision | Rationale |
|----------|-----------|
| **No predictions/signals** | Hackathon requirement: educational analysis only, brand-safe |
| **Supportive coaching** | Nudges inform and suggest, never block trades or judge |
| **Streaming-first** | Token-by-token LLM output via WebSocket — feels alive, not static |
| **Trading Twin as killer feature** | Visual proof that impulsive trading costs money — emotional impact |
| **Proactive, not reactive** | Market monitor pushes alerts without user action — "it's watching for you" |
| **Graceful degradation** | Frontend works with mock data when backend is offline; demo fallback cache |
| **LLM fallback chain** | DeepSeek direct -> OpenRouter with automatic failover |
| **WebSocket + REST** | Chat uses WebSocket with REST fallback for reliability |
| **Function calling** | DeepSeek native tool use instead of LangGraph for simplicity |
| **Multi-persona content** | Different AI voices (Calm Analyst, Data Nerd, Trading Coach) |
| **Few-shot style matching** | Per-persona example library ensures consistent voice without fine-tuning |
| **Compliance-first** | Every LLM output filtered for blocklisted terms + disclaimer injection |
| **Demo-perfected** | Pre-cached data, fallback system, health checks — nothing fails on stage |

</details>

---

<details>
<summary><h2>Compliance System</h2></summary>

All AI outputs pass through a compliance filter before reaching users:

**Blocklist**: `guaranteed`, `moon`, `easy money`, `get rich`, `sure thing`

**Prediction detection**: Regex matching `will hit`, `price will`, `going to`

**Auto-disclaimer**: Every response includes `"This is analysis, not financial advice."`

**System prompts**: All agents have master compliance rules embedded:
- Never predict future prices
- Always use past/present tense
- Frame everything as educational
- Reference specific data sources

</details>

---

## License

Built for the [Deriv AI Hackathon 2026](https://deriv.com).

<p align="center">
  <img src="frontend/public/tradeiq_favicon.svg" width="40" alt="TradeIQ" />
  <br />
  <sub>TradeIQ - Making trading intelligent</sub>
</p>
