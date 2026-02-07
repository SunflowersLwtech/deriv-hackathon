# TradeIQ Final Best Practice Implementation Plan

- Document Path: `/Users/sunfl/Documents/study/deriv hackathon/dev/docs/FINAL_BEST_PRACTICE_PLAN.md`
- Applicable Codebase: `/Users/sunfl/Documents/study/deriv hackathon`
- Version: v1.0
- Date: 2026-02-07

## 1. Goals and Scope

This plan is for implementing the complete TradeIQ system, covering:
1. Django backend intelligent agents (DeepSeek function calling, market tools, behavioral coaching, Bluesky content).
2. Next.js 14 frontend (Dashboard, Market, Behavior, Content, chat panel).
3. Supabase Auth Google login (frontend-backend integration).

Strict Constraints:
1. Use DeepSeek API only (use OpenRouter only when absolutely necessary).
2. Use conda environment `tradeiq`.
3. Read configuration uniformly from project root `.env`.
4. Supabase Google Provider is already configured in console, code only needs to integrate.

## 2. Current Baseline and Key Gaps

The current repository has reusable foundations but has not formed a demonstrable closed loop. Main gaps:
1. Frontend directory missing, Phase 6/7 not started.
2. Multiple key APIs not implemented (`market/brief`, `market/ask`, `market/price`, `chat/ask`, `content/generate`, `demo/seed`, `demo/wow-moment`).
3. Demo fixtures for overtrading/loss-chasing/healthy have no trade data, behavioral detection chain cannot trigger.
4. DeepSeek routing and tool contracts not fully aligned with target interfaces.
5. Supabase JWT authentication middleware and protected permissions not implemented.
6. `DATABASE_URL` currently has wrong format causing fallback to sqlite, easily causing "false success".

## 3. Execution Principles (Best Practices)

1. Establish minimum closed loop first, then expand experience layer.
2. Interface first: fix API contract first, then write frontend/backend.
3. Strong naming constraints: tool function names, URLs, JSON fields strictly unified according to plan.
4. All external APIs (DeepSeek/Deriv/News/Finnhub/Bluesky) must have timeout, retry, fallback.
5. Don't hardcode secrets in code; `.env` only for local use, commit forbidden.
6. Each phase must have repeatable verification commands and clear DoD (Definition of Done).
7. Don't modify files you marked as non-modifiable; if conflicts with goals, record conflicts first and make minimal change decisions.

## 4. Conflicts and Decisions (Align First)

### 4.1 Identified Conflicts

1. You require "don't modify `tradeiq/settings.py`", but Supabase JWT middleware and DRF permissions need to integrate into settings by default.
2. You require "don't modify behavior/", but target tool naming needs `generate_behavioral_nudge` (currently `generate_behavioral_nudge_with_ai`).

### 4.2 Suggested Decisions

1. `tradeiq/settings.py` allows minimal necessary changes (only add middleware/REST auth config, don't change other behavior).
2. behavior logic remains unchanged, create adapter layer in `agents/tools_registry.py` (alias mapping) to satisfy tool naming contract.

## 5. Phased Implementation Plan (Recommended Order)

## Phase A: Stabilization and Security Prerequisites (Half Day)

Goal: Avoid "false green" in subsequent integration.

Tasks:
1. Fix `.env` `DATABASE_URL` to valid Supabase URI (password URL encoded).
2. Sync dependencies: `backend/requirements.txt` and `scripts/environment.yml` both add `finnhub-python`, `websockets`, `textblob`.
3. Unified read from root `.env` (scripts and services consistent).
4. Clean hardcoded credentials (especially `scripts/deriv_test.py`).
5. Add `.gitignore` to prevent `__pycache__`, temp file pollution.

DoD:
1. `conda activate tradeiq && cd backend && python manage.py check` no errors and no DB parse fallback.
2. `python scripts/verify_env.py` passes.
3. Repository has no new sensitive information leaks.

## Phase 0: Infrastructure (0.5 Day)

Goal: Complete infrastructure implementation.

Tasks:
1. Update `backend/requirements.txt` (five packages).
2. Create `market_insights` Supabase table (structure aligned with `market/models.py`).
3. Install dependencies in `tradeiq` environment and verify.

DoD:
1. `market_insights` table exists, fields consistent with Django model.
2. `pip install -r backend/requirements.txt` succeeds.
3. `python manage.py showmigrations`, `python manage.py check` both pass.

## Phase 1: Agent Core (1 Day)

Goal: Build unified AI routing brain.

Tasks:
1. `agents/llm_client.py`
   - `get_client()` singleton.
   - `chat_completion()` generic wrapper.
   - `chat_completion_with_tools()` complete tool loop (supports multi-round tool calls).
   - Exponential backoff retry and error classification.
2. `agents/prompts.py`
   - Write complete `MASTER_COMPLIANCE_RULES`.
   - Complete `SYSTEM_PROMPT_MARKET/BEHAVIOR/CONTENT/ROUTER`.
3. `agents/tools_registry.py`
   - Define 9 tools (names strictly consistent).
   - `TOOL_DISPATCH_MAP` bound to real functions.
4. `agents/router.py`
   - `route_query(query, user_id=None, conversation_history=None)`.
   - Integrate compliance check and disclaimer concatenation.
   - Add `generate_market_brief(instruments)`.

DoD:
1. Any market/behavior/content question can go through unified routing.
2. Tool call supports multiple rounds until final text.
3. Output contains no prediction/signal statements, and includes disclaimer.

## Phase 2: Market Analysis Tools (1 Day)

Goal: Provide real market analysis capabilities.

Tasks:
1. `market/tools.py`
   - `fetch_price_data(instrument, timeframe)` connect Deriv WS (including symbol map).
   - `search_news(instrument, hours)` aggregate NewsAPI + Finnhub.
   - `analyze_technicals(instrument)` pure Python implementation SMA20/50, RSI, trend.
   - `get_sentiment(instrument)` use TextBlob to aggregate news sentiment.
2. `market/views.py`
   - `MarketBriefView`.
   - `AskAnalystView`.
   - `LivePriceView`.
3. `market/urls.py`
   - Add `brief/`, `ask/`, `price/`.

DoD:
1. Three market APIs can return structured JSON.
2. When Deriv unavailable, have explainable fallback return (not 500 crash).
3. Technical indicator calculation results are repeatable and unit-testable.

## Phase 3: Content Generation Tools (0.5-1 Day)

Goal: Complete Bluesky content production closed loop.

Tasks:
1. `content/tools.py`
   - `generate_social_content`.
   - `format_bluesky_post` (within 300 characters, mandatory disclaimer).
   - `compose_bluesky_thread` (3-5 posts).
   - `apply_persona_voice`.
2. `content/personas.py`
   - Complete persona config: `system_prompt`, `voice_config`, `example_posts`, `banned_phrases`.
3. `content/views.py`
   - Add `GenerateContentView`.
4. `content/urls.py`
   - Add `generate/`.

DoD:
1. Input insight can produce post/thread.
2. Overlong text automatically truncated while preserving compliance footer.
3. Persona switch shows obvious style change without breaking compliance rules.

## Phase 4: WebSocket Chat Integration (0.5 Day)

Goal: Chat end-to-end connectivity.

Tasks:
1. `chat/consumers.py`
   - Each connection maintains conversation history.
   - Use `asyncio.to_thread()` to call `route_query()`.
   - Support normal reply + behavioral nudge.
2. Create `chat/views.py`, `chat/urls.py`
   - `POST /api/chat/ask/` as REST fallback.
3. `tradeiq/urls.py`
   - Include `api/chat/`.
4. Group isolation
   - Don't use global fixed group, isolate by user/session, avoid cross-user message leaks.

DoD:
1. Both WS and REST can return AI results.
2. Behavior nudge only goes to target user connection.

## Phase 5: Demo System (0.5 Day)

Goal: Demo scenarios one-click reproducible.

Tasks:
1. Complete fixtures:
   - `demo_overtrading.json` at least 18 trades.
   - `demo_loss_chasing.json` at least 6 trades with increasing position size.
   - `demo_healthy_session.json` at least 6 healthy samples.
2. Create `demo_all_in_one.json` (demo user + 3 personas).
3. `demo/views.py`
   - `SeedDemoDataView`.
   - `WowMomentView`.
4. `demo/urls.py`
   - Add `seed/`, `wow-moment/`.

DoD:
1. After seed, can directly run complete demo chain.
2. wow-moment one call returns market + behavior + content combined results.

## Phase 6: Supabase Auth (Google Sign-In) (1 Day)

Goal: Unified authentication chain.

Tasks (Frontend):
1. Install `@supabase/supabase-js`, `@supabase/ssr`.
2. Create `src/lib/supabase/client.ts`, `server.ts`, `middleware.ts`.
3. Create `/login`, `/auth/callback`, global `middleware.ts`.
4. Add sign-out to navigation bar.

Tasks (Backend):
1. Create `tradeiq/middleware/supabase_auth.py`.
2. Verify `Authorization: Bearer <jwt>`, map/auto-create `users` table records.
3. Enable permission control for protected interfaces.

DoD:
1. Unauthenticated access to protected pages redirects to `/login`.
2. After Google login, can access frontend/backend protected interfaces.
3. Backend returns 401 when JWT invalid.

## Phase 7: Frontend Next.js (nof1.ai style) (1.5-2 Days)

Goal: Build demonstrable frontend experience.

Tasks: (Completely replicate https://nof1.ai/ frontend including colors, elements, any visual effects, interactions can be more natural)
1. Initialize Next.js 14 + Tailwind + ESLint + TS.
2. Create API/WebSocket clients: `src/lib/api.ts`, `src/lib/websocket.ts`.
3. Build base shell: Sidebar, TickerBar, ChatPanel, DisclaimerBadge, DataCard, AppShell.
4. Page implementation:
   - `/` Dashboard
   - `/market`
   - `/behavior`
   - `/content`
5. Complete dark high-density visuals and responsive.

DoD:
1. All four pages can load and fetch backend data.
2. Chat panel can send/receive.
3. Content workbench can generate and preview Bluesky content.

## Phase 8: Integration, Quality Gates and Rehearsal (0.5-1 Day)

Goal: Ensure Demo Day stability.

Tasks:
1. Full chain regression: market -> behavior -> content.
2. Exception injection: DeepSeek timeout, Deriv disconnection, News API rate limit.
3. Add cache and timeout fallback, control P95 response time.
4. Solidify demo script (narration + API trigger order + fallback script).

DoD:
1. Key flows run 3 times consecutively without interruption.
2. Any external API failure doesn't cause overall 500.

## 6. Milestones and Suggested Schedule

1. Day 1: Phase A + 0 + 1.
2. Day 2: Phase 2 + 3 + 4.
3. Day 3: Phase 5 + 6.
4. Day 4: Phase 7 + 8 + Demo rehearsal.

## 7. Acceptance Command Checklist (Final)

```bash
# Backend
cd backend
python manage.py runserver

curl -X POST http://localhost:8000/api/demo/seed/
curl -X POST http://localhost:8000/api/demo/load-scenario/ -H "Content-Type: application/json" -d '{"scenario":"revenge_trading"}'
curl -X POST http://localhost:8000/api/market/ask/ -H "Content-Type: application/json" -d '{"question":"What is happening with EUR/USD?"}'
curl -X POST http://localhost:8000/api/chat/ask/ -H "Content-Type: application/json" -d '{"message":"Why did EUR/USD spike?"}'
curl -X POST http://localhost:8000/api/content/generate/ -H "Content-Type: application/json" -d '{"insight":"EUR/USD dropped 1.2%","platform":"bluesky_post"}'
curl -X POST http://localhost:8000/api/demo/wow-moment/ -H "Content-Type: application/json" -d '{"user_id":"aaaaaaaa-0000-4000-8000-000000000001","instrument":"EUR/USD"}'

# Frontend
cd ../frontend
npm run dev
```

## 8. Quality Gates (Must All Be Satisfied)

1. Function gate: All above acceptance commands succeed.
2. Compliance gate: Output contains no prediction/signal statements, disclaimer coverage complete.
3. Security gate: Codebase has no hardcoded keys, all invalid JWT requests rejected.
4. Performance gate: Key APIs acceptable under normal network (recommend P95 < 3s, fallback when external API exceptions).
5. Demo gate: Wow flow triggers successfully once.

## 9. Risks and Rollback Strategy

1. DeepSeek timeout/failure.
   - Strategy: Retry + fallback template + cache last available analysis.
2. Deriv WS unstable.
   - Strategy: Disconnect reconnect + recent price cache + clear "data temporarily unavailable" state.
3. NewsAPI/Finnhub rate limit.
   - Strategy: Dual-source aggregation + deduplication + failed parts can be empty.
4. Supabase Auth callback failure.
   - Strategy: Independent callback diagnostic logs + login retry entry.
5. Demo site network fluctuations.
   - Strategy: Pre-configured mock fallback and cached data.

## 10. File-Level Execution Checklist (Final)

New:
1. `backend/chat/views.py`
2. `backend/chat/urls.py`
3. `backend/fixtures/demo_all_in_one.json`
4. `backend/tradeiq/middleware/supabase_auth.py`
5. `frontend/` entire directory and files

Modify:
1. `backend/requirements.txt`
2. `backend/agents/prompts.py`
3. `backend/agents/tools_registry.py`
4. `backend/agents/router.py`
5. `backend/market/tools.py`
6. `backend/market/views.py`
7. `backend/market/urls.py`
8. `backend/content/tools.py`
9. `backend/content/personas.py`
10. `backend/content/views.py`
11. `backend/content/urls.py`
12. `backend/chat/consumers.py`
13. `backend/demo/views.py`
14. `backend/demo/urls.py`
15. `backend/tradeiq/urls.py`
16. `backend/fixtures/demo_overtrading.json`
17. `backend/fixtures/demo_loss_chasing.json`
18. `backend/fixtures/demo_healthy_session.json`

Keep Unchanged (as you requested):
1. `backend/behavior/` all
2. `backend/content/models.py`
3. `backend/content/bluesky.py`
4. `backend/market/models.py`
5. `backend/agents/compliance.py`
6. All migrations
7. `backend/fixtures/demo_revenge_trading.json`
8. `backend/fixtures/demo_personas.json`

## 11. Final Demo Key Flow (Only Main Line)

Market event -> AI explains -> Detects user pattern -> Nudge appears -> Content generated -> Published to Bluesky

This main line is the only high-priority acceptance path for Demo success. All tasks prioritize ensuring this chain's stability as the first goal.
