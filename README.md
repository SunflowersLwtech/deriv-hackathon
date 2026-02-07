# TradeIQ - Intelligent Trading Analyst

An AI-powered trading analytics platform built for the **Deriv AI Hackathon 2026**. TradeIQ combines real-time market analysis, behavioral coaching, and social content generation into a unified intelligent trading assistant.

## Three Pillars

| Pillar | Description |
|--------|-------------|
| **Market Analysis** | Real-time price feeds, technical indicators, sentiment analysis, economic calendar, and AI-powered market Q&A via Deriv WebSocket API |
| **Behavioral Coaching** | Trade pattern detection (revenge trading, overtrading, tilt), personalized nudges, and risk scoring based on user trading history |
| **Social Content Engine** | AI-generated market commentary with multiple personas, one-click publish to Bluesky via AT Protocol |

> **Note**: TradeIQ provides educational analysis only. It does not provide trading signals, predictions, or financial advice.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TailwindCSS 4, TradingView Lightweight Charts, Recharts, Framer Motion |
| Backend | Django 5, Django REST Framework, Django Channels (Daphne ASGI), WebSocket |
| AI/LLM | DeepSeek API / OpenRouter (OpenAI-compatible), Multi-agent pipeline |
| Database | Supabase PostgreSQL, Upstash Redis (channel layer) |
| Auth | Supabase Auth (Google OAuth, JWT) |
| External APIs | Deriv WebSocket API, NewsAPI, Finnhub, Bluesky AT Protocol |
| Deployment | Docker Compose, Vercel (frontend), Railway/Render (backend) |

---

## Quick Start

### Docker (Recommended)

```bash
git clone <repo-url> && cd "deriv hackathon"
cp .env.example .env        # Edit .env with your API keys
docker compose up --build    # Frontend: :3000, Backend: :8000
```

### Without Docker

```bash
conda create -n tradeiq python=3.11 -y && conda activate tradeiq
pip install -r backend/requirements.txt
cd frontend && npm ci && cd ..
cp .env.example .env && cp frontend/.env.example frontend/.env.local
# Edit both .env files with your API keys
cd backend && python manage.py migrate && cd ..
./scripts/start_prod.sh
```

See [DEPLOY.md](./DEPLOY.md) for detailed deployment instructions including Vercel, Railway, and Render.

---

## Project Structure

```
deriv hackathon/
├── frontend/                  # Next.js 16 (React 19)
│   ├── src/
│   │   ├── app/               # App Router pages
│   │   │   ├── page.tsx       # Dashboard (Overview)
│   │   │   ├── market/        # Market Analysis page
│   │   │   ├── behavior/      # Behavioral Coaching page
│   │   │   ├── content/       # Content Generation page
│   │   │   ├── pipeline/      # Agent Team Pipeline demo
│   │   │   ├── login/         # Login page
│   │   │   └── auth/callback/ # OAuth callback handler
│   │   ├── components/        # React components (layout, market, behavior, chat, ui)
│   │   ├── hooks/             # Custom React hooks (useMarketData, useBehaviorData, etc.)
│   │   └── lib/
│   │       ├── api.ts         # REST API client (all endpoints)
│   │       ├── websocket.ts   # WebSocket client (auto-reconnect)
│   │       └── supabase/      # Supabase browser client
│   ├── vercel.json            # Vercel deployment config
│   └── Dockerfile             # Docker build (multi-stage standalone)
│
├── backend/                   # Django 5 + DRF + Channels
│   ├── tradeiq/               # Project config
│   │   ├── settings.py        # Django settings (DB, auth, CORS, channels)
│   │   ├── asgi.py            # ASGI application (HTTP + WebSocket routing)
│   │   ├── urls.py            # Root URL routing (/api/*)
│   │   └── middleware/        # Supabase JWT authentication backend
│   ├── market/                # Market Analysis app (views, models, tools)
│   ├── behavior/              # Behavioral Coaching app (detection, deriv_client)
│   ├── content/               # Content Engine app (personas, bluesky client)
│   ├── agents/                # AI Agent Team (router, agent_team, tools_registry)
│   ├── chat/                  # WebSocket chat consumer
│   ├── demo/                  # Demo scenarios & data seeding
│   ├── railway.toml           # Railway deployment config
│   └── Dockerfile             # Docker build (multi-stage)
│
├── scripts/                   # Start & verification scripts
│   ├── start_prod.sh          # One-click production start
│   ├── start_backend.sh       # Backend development server
│   ├── start_frontend.sh      # Frontend development server
│   ├── verify_env.py          # Environment variable checker
│   └── test_all_features.py   # Comprehensive feature test suite
│
├── docker-compose.yml         # One-click local deployment
├── render.yaml                # Render blueprint (one-click cloud)
├── .env.example               # Environment variables template
├── DEPLOY.md                  # Deployment guide (4 methods)
└── DESIGN_DOCUMENT.md         # Architecture design document
```

---

## API Reference

All backend endpoints are served under `/api/`. Authentication uses Supabase JWT tokens passed as `Authorization: Bearer <token>`.

### Market Analysis API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/market/insights/` | List market insights (paginated) |
| `POST` | `/api/market/ask/` | Ask the AI market analyst a free-form question |
| `POST` | `/api/market/brief/` | Get market summary for specific instruments |
| `POST` | `/api/market/price/` | Get live price for an instrument (via Deriv API) |
| `POST` | `/api/market/history/` | Get historical OHLC candle data |
| `POST` | `/api/market/technicals/` | Get technical indicators (SMA, RSI, support/resistance) |
| `POST` | `/api/market/sentiment/` | Get AI-powered sentiment analysis |
| `GET` | `/api/market/calendar/` | Get economic calendar events (Finnhub) |
| `GET` | `/api/market/headlines/` | Get top financial news headlines (NewsAPI) |
| `GET` | `/api/market/instruments/` | List active tradeable symbols (Deriv) |
| `POST` | `/api/market/patterns/` | Get chart pattern recognition (Finnhub) |

#### Example: Ask Market Analyst

```bash
curl -X POST http://localhost:8000/api/market/ask/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is driving BTC/USD volatility today?"}'
```

```json
{
  "answer": "BTC/USD is experiencing heightened volatility driven by...",
  "disclaimer": "This is educational analysis, not financial advice.",
  "tools_used": ["deriv_live_price", "news_search", "sentiment_analysis"]
}
```

#### Example: Get Technical Indicators

```bash
curl -X POST http://localhost:8000/api/market/technicals/ \
  -H "Content-Type: application/json" \
  -d '{"instrument": "BTC/USD", "timeframe": "1h"}'
```

```json
{
  "instrument": "BTC/USD",
  "timeframe": "1h",
  "current_price": 67234.50,
  "trend": "bullish",
  "volatility": "high",
  "key_levels": { "support": 65800.0, "resistance": 68500.0 },
  "indicators": { "sma20": 66890.30, "sma50": 65420.15, "rsi14": 62.5 },
  "summary": "BTC/USD is in a bullish trend above both SMAs...",
  "source": "deriv_api"
}
```

#### Example: Get Live Price

```bash
curl -X POST http://localhost:8000/api/market/price/ \
  -H "Content-Type: application/json" \
  -d '{"instrument": "EUR/USD"}'
```

```json
{
  "instrument": "EUR/USD",
  "deriv_symbol": "frxEURUSD",
  "price": 1.08234,
  "bid": 1.08230,
  "ask": 1.08238,
  "timestamp": "2026-02-08T10:30:00Z",
  "source": "deriv_api"
}
```

### Behavioral Coaching API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/behavior/profiles/` | List user profiles |
| `GET` | `/api/behavior/trades/` | List user trades (paginated) |
| `GET` | `/api/behavior/metrics/` | Get behavioral metrics (daily aggregates) |
| `POST` | `/api/behavior/trades/analyze_batch/` | Analyze recent trades for patterns (auth required) |
| `POST` | `/api/behavior/trades/sync_deriv/` | Sync trades from Deriv account |
| `GET` | `/api/behavior/portfolio/` | Get Deriv portfolio positions |
| `GET` | `/api/behavior/balance/` | Get Deriv account balance |
| `GET` | `/api/behavior/reality-check/` | Get Deriv reality check data |

#### Example: Analyze Trading Patterns

```bash
curl -X POST http://localhost:8000/api/behavior/trades/analyze_batch/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <jwt_token>" \
  -d '{"user_id": "user-uuid", "hours": 24}'
```

```json
{
  "analysis": {
    "patterns": { "revenge_trading": true, "overtrading": false, "tilt": false },
    "summary": "3 rapid trades detected after a significant loss...",
    "needs_nudge": true,
    "trade_count": 8,
    "time_window": "24h"
  },
  "nudge": {
    "nudge_type": "revenge_trading",
    "message": "You have made 3 trades in quick succession after a loss. Consider taking a break.",
    "severity": "warning",
    "suggested_action": "Take a 30-minute break before your next trade."
  }
}
```

### Content Engine API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/content/personas/` | List AI personas (Market Maven, Data Sage, etc.) |
| `GET` | `/api/content/posts/` | List social posts (draft/published) |
| `POST` | `/api/content/generate/` | Generate social content from market insight |
| `POST` | `/api/content/publish-bluesky/` | Publish content to Bluesky |
| `GET` | `/api/content/bluesky-search/` | Search Bluesky for market discussions |

#### Example: Generate Content

```bash
curl -X POST http://localhost:8000/api/content/generate/ \
  -H "Content-Type: application/json" \
  -d '{
    "insight": "BTC/USD broke above 68K resistance with strong volume",
    "platform": "bluesky_post"
  }'
```

```json
{
  "content": "BTC just cleared the 68K resistance level with conviction...",
  "platform": "bluesky_post",
  "persona": "Market Maven",
  "disclaimer": "For educational purposes only. Not financial advice."
}
```

#### Example: Publish to Bluesky

```bash
curl -X POST http://localhost:8000/api/content/publish-bluesky/ \
  -H "Content-Type: application/json" \
  -d '{"content": "Market update: BTC holding above 68K support.", "type": "single"}'
```

```json
{
  "success": true,
  "status": "published",
  "platform": "bluesky",
  "uri": "at://did:plc:xxx/app.bsky.feed.post/xxx"
}
```

### AI Agent Team API

The agent team runs five specialized agents in a pipeline.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/agents/pipeline/` | Run full 5-stage pipeline |
| `POST` | `/api/agents/monitor/` | Stage 1: Volatility Monitor (Deriv price scan) |
| `POST` | `/api/agents/analyst/` | Stage 2: Event Analyst (news + LLM analysis) |
| `POST` | `/api/agents/advisor/` | Stage 3: Portfolio Advisor (personalized impact) |
| `POST` | `/api/agents/sentinel/` | Stage 4: Behavioral Sentinel (trading pattern check) |
| `POST` | `/api/agents/content-gen/` | Stage 5: Content Generator (Bluesky publish) |
| `POST` | `/api/agents/chat/` | General chat with automatic agent routing |

#### Pipeline Flow

```
[1] Volatility Monitor ──> [2] Event Analyst ──> [3] Portfolio Advisor
         (Deriv)               (News+LLM)            (Portfolio)
                                                          │
[5] Content Generator <── [4] Behavioral Sentinel <───────┘
       (Bluesky)              (Trade History)
```

#### Example: Run Full Pipeline

```bash
curl -X POST http://localhost:8000/api/agents/pipeline/ \
  -H "Content-Type: application/json" \
  -d '{
    "custom_event": { "instrument": "BTC/USD", "change_pct": 5.2 },
    "user_portfolio": [
      {"instrument": "BTC/USD", "direction": "long", "size": 0.5, "entry_price": 64000, "pnl": 1617}
    ]
  }'
```

```json
{
  "status": "success",
  "volatility_event": {
    "instrument": "BTC/USD",
    "price_change_pct": 5.2,
    "direction": "spike",
    "magnitude": "high"
  },
  "analysis_report": {
    "event_summary": "BTC/USD surged 5.2% in the last hour...",
    "root_causes": ["Institutional buying pressure", "Short squeeze"],
    "sentiment": "bullish",
    "sentiment_score": 0.78
  },
  "personalized_insight": {
    "impact_summary": "Your long BTC position is up $1,617...",
    "risk_assessment": "medium",
    "suggestions": ["Consider taking partial profits", "Move stop-loss to breakeven"]
  },
  "sentinel_insight": {
    "personalized_warning": "Your recent win streak may lead to overconfidence...",
    "risk_level": "medium"
  },
  "market_commentary": {
    "post": "BTC just ripped 5.2% in an hour...",
    "published": true,
    "bluesky_url": "https://bsky.app/profile/tradeiq-analyst.bsky.social/post/xxx"
  },
  "pipeline_started_at": "2026-02-08T10:00:00Z",
  "pipeline_finished_at": "2026-02-08T10:00:12Z"
}
```

### Chat API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat/ask/` | REST chat endpoint (fallback when WebSocket unavailable) |
| `WS` | `/ws/chat/` | WebSocket chat with real-time streaming |

#### WebSocket Chat

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/chat/?user_id=user-uuid");
ws.onopen = () => ws.send(JSON.stringify({ message: "Analyze EUR/USD trend" }));
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

### Demo API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/demo/scenarios/` | List available demo scenarios |
| `POST` | `/api/demo/seed/` | Seed demo data (creates test user + trades) |
| `POST` | `/api/demo/load-scenario/` | Load a specific demo scenario (revenge_trading, overtrading, etc.) |
| `POST` | `/api/demo/analyze/` | Analyze a demo scenario and return nudges |
| `POST` | `/api/demo/wow-moment/` | Trigger the full "wow moment" demo experience |

---

## External APIs Used

| API | Purpose | Protocol |
|-----|---------|----------|
| **Deriv API** | Live market prices, historical candles, portfolio, active symbols, reality check | WebSocket (`wss://ws.derivws.com/websockets/v3`) |
| **DeepSeek** | Primary LLM for market analysis, content generation, agent chat | REST (OpenAI-compatible) |
| **OpenRouter** | Fallback LLM provider (automatic failover) | REST (OpenAI-compatible) |
| **NewsAPI** | Financial news headlines and keyword search | REST (`https://newsapi.org/v2/`) |
| **Finnhub** | Economic calendar, chart pattern recognition | REST (`https://finnhub.io/api/v1/`) |
| **Bluesky** | Social content publishing, market discussion search | AT Protocol (`https://bsky.social/`) |
| **Supabase** | PostgreSQL database, JWT authentication, Google OAuth | REST + Realtime |
| **Upstash Redis** | Django Channels layer for WebSocket message pub/sub | Redis over TLS |

---

## Authentication

TradeIQ uses **Supabase Auth** with JWT tokens:

1. User signs in via Google OAuth on the frontend (`/login`)
2. Supabase issues a JWT access token stored in the browser
3. Frontend sends `Authorization: Bearer <token>` header on API calls
4. Backend `SupabaseJWTAuthentication` middleware validates the JWT (HS256)
5. First-time users get a `UserProfile` auto-created in the database

Most API endpoints work without authentication for demo purposes. Endpoints that require auth (like `analyze_batch`) will return `401 Unauthorized` without a valid token.

---

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Dashboard | `/` | Overview with portfolio KPIs, P&L chart, market insights, data source badge |
| Market Analysis | `/market` | Instrument selector, free-form analyst Q&A, technicals, sentiment, economic calendar, headlines |
| Behavioral Coaching | `/behavior` | Demo scenario loader, trade pattern visualization, nudge cards, Deriv sync |
| Content Engine | `/content` | Persona selector, content generator, Bluesky publish, post history |
| Agent Pipeline | `/pipeline` | Visual 5-stage pipeline demo with sequential animation and collapsible result cards |
| Login | `/login` | Google OAuth sign-in page |

---

## Development

### Prerequisites

- Python 3.11+ (conda recommended)
- Node.js 20+
- Supabase project (free tier works)
- At least one LLM API key (DeepSeek or OpenRouter)
- Deriv API app ID and token (free at [api.deriv.com](https://api.deriv.com))

### Running Tests

```bash
# Backend unit tests
cd backend && python manage.py test

# LLM resilience tests
cd backend && python -m pytest tests/test_llm_resilience.py -v

# Environment variable verification
python scripts/verify_env.py

# Full feature test suite (requires running backend)
python scripts/test_all_features.py
```

### Key Design Decisions

- **No trading signals or predictions** - Educational analysis only (hackathon brand-safe requirement)
- **Graceful degradation** - Frontend works with mock data when backend is offline (DataSourceBadge shows status)
- **LLM fallback chain** - Supports DeepSeek and OpenRouter with automatic failover
- **WebSocket + REST dual mode** - Chat uses WebSocket with REST fallback for reliability
- **Supportive coaching** - Behavioral nudges are encouraging and non-restrictive
- **Multi-persona content** - Different AI personas for varied social media voice

---

## Deployment Options

| Method | Frontend | Backend | Best For |
|--------|----------|---------|----------|
| Docker Compose | Container :3000 | Container :8000 | Local dev, hackathon demo |
| Vercel + Railway | Vercel (serverless) | Railway (persistent) | Production cloud |
| Render Blueprint | Render (Docker) | Render (Docker) | One-click cloud deploy |
| Direct (no Docker) | `npm start` | `daphne` | Development |

> **Important**: The backend requires a persistent server (not serverless) because it uses
> Django Channels with Daphne for WebSocket support. It cannot run on Vercel's serverless
> platform. The frontend can be deployed to Vercel without issues.

See [DEPLOY.md](./DEPLOY.md) for step-by-step instructions for all deployment methods.

---

## License

Built for the Deriv AI Hackathon 2026.
