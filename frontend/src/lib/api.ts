const DEFAULT_LOCAL_API_BASE = "http://localhost:8000/api";

function normalizeApiBase(url: string): string {
  return url.replace(/\/+$/, "");
}

function resolveApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (configured) {
    return normalizeApiBase(configured);
  }

  if (typeof window !== "undefined") {
    const { origin, hostname } = window.location;
    const isLocal = hostname === "localhost" || hostname === "127.0.0.1";
    if (!isLocal) {
      return `${origin}/api`;
    }
  }

  return DEFAULT_LOCAL_API_BASE;
}

// API request timeout constants (milliseconds)
const TIMEOUT_DEFAULT = 15_000;     // standard API calls
const TIMEOUT_TECHNICALS = 20_000;  // Deriv WS history + computation
const TIMEOUT_ANALYSIS = 25_000;    // pattern analysis + LLM nudge
const TIMEOUT_LLM = 30_000;        // LLM reasoning / sentiment
const TIMEOUT_BRIEF = 45_000;      // parallel Deriv WS + LLM summary
const TIMEOUT_PIPELINE = 90_000;   // full 5-agent pipeline (Monitor→Analyst→Advisor→Sentinel→Content)

interface ApiOptions {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
  token?: string;
  requiresAuth?: boolean;
  /** Request timeout in ms. Defaults to TIMEOUT_DEFAULT (15s). */
  timeoutMs?: number;
}

class ApiClient {
  private baseUrl?: string;

  // In-flight request deduplication: prevents the same endpoint from being
  // called multiple times simultaneously (e.g., getUserProfiles from 3+ hooks)
  private _inflight = new Map<string, Promise<unknown>>();
  // TTL cache: avoid re-fetching the same data when multiple hooks with
  // different polling intervals hit the same endpoint seconds apart.
  private _cache = new Map<string, { data: unknown; expiresAt: number }>();

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl?.trim() ? normalizeApiBase(baseUrl) : undefined;
  }

  /** Read stale cached data (even if expired) for instant mount display. */
  getCached<T>(key: string): T | undefined {
    const entry = this._cache.get(key.toLowerCase().trim());
    return entry ? (entry.data as T) : undefined;
  }

  /** Deduplicate concurrent requests AND cache results for `ttl` ms. */
  private dedup<T>(key: string, fn: () => Promise<T>, ttl = 5000): Promise<T> {
    const normalized = key.toLowerCase().trim();

    // Return cached result if still fresh
    const cached = this._cache.get(normalized);
    if (cached && Date.now() < cached.expiresAt) {
      return Promise.resolve(cached.data as T);
    }

    // Return in-flight promise if one exists
    const existing = this._inflight.get(normalized);
    if (existing) return existing as Promise<T>;

    const promise = fn()
      .then((data) => {
        this._cache.set(normalized, { data, expiresAt: Date.now() + ttl });
        return data;
      })
      .finally(() => this._inflight.delete(normalized));
    this._inflight.set(normalized, promise);
    return promise;
  }

  private getBaseUrl(): string {
    const resolved = resolveApiBase();
    if (!this.baseUrl || this.baseUrl !== resolved) {
      this.baseUrl = resolved;
    }
    return this.baseUrl;
  }

  private async getAccessToken(): Promise<string | undefined> {
    if (typeof window === "undefined") {
      return undefined;
    }

    try {
      const { createClient } = await import("@/lib/supabase/client");
      const supabase = createClient();
      const { data } = await supabase.auth.getSession();
      return data.session?.access_token;
    } catch {
      return undefined;
    }
  }

  private async request<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
    const { method = "GET", body, headers = {}, token, requiresAuth = false, timeoutMs = TIMEOUT_DEFAULT } = options;

    const requestHeaders: Record<string, string> = {
      "Content-Type": "application/json",
      ...headers,
    };

    const accessToken = token || (requiresAuth ? await this.getAccessToken() : undefined);
    if (accessToken) {
      requestHeaders["Authorization"] = `Bearer ${accessToken}`;
    } else if (requiresAuth) {
      throw new ApiError(401, "Authentication required. Please sign in and try again.");
    }

    const response = await fetch(`${this.getBaseUrl()}${endpoint}`, {
      method,
      headers: requestHeaders,
      body: body ? JSON.stringify(body) : undefined,
      signal: AbortSignal.timeout(timeoutMs),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }));
      throw new ApiError(response.status, error.detail || error.error || "Request failed");
    }

    return response.json();
  }

  // Market endpoints
  async getMarketInsights() {
    return this.dedup("insights", () =>
      this.request<MarketInsightsResponse>("/market/insights/")
    , 10000);
  }

  // Safe to dedup: getMarketBrief is a read-only query despite using POST (body params).
  // Normalize: empty array is semantically identical to undefined on the backend,
  // so we collapse both to the same dedup key and request body.
  async getMarketBrief(instruments?: string[]) {
    const normalized = instruments?.length ? [...new Set(instruments)] : undefined;
    const key = `brief:${normalized ? [...normalized].sort().join(",") : ""}`;
    return this.dedup(key, () =>
      this.request<MarketBrief>("/market/brief/", {
        method: "POST",
        body: { instruments: normalized },
        timeoutMs: TIMEOUT_BRIEF,
      })
    , 8000);
  }

  async askMarketAnalyst(question: string) {
    return this.request<MarketAnalysis>("/market/ask/", {
      method: "POST",
      body: { question },
      timeoutMs: TIMEOUT_LLM,
    });
  }

  async getLivePrice(instrument: string) {
    return this.request<LivePrice>("/market/price/", {
      method: "POST",
      body: { instrument },
    });
  }

  async getMarketHistory(instrument: string, timeframe: string = "1h", count: number = 120) {
    return this.request<MarketHistory>("/market/history/", {
      method: "POST",
      body: { instrument, timeframe, count },
      timeoutMs: TIMEOUT_TECHNICALS,
    });
  }

  async getMarketTechnicals(instrument: string, timeframe: string = "1h") {
    return this.request<MarketTechnicals>("/market/technicals/", {
      method: "POST",
      body: { instrument, timeframe },
      timeoutMs: TIMEOUT_TECHNICALS,
    });
  }

  async getMarketSentiment(instrument: string) {
    return this.request<MarketSentiment>("/market/sentiment/", {
      method: "POST",
      body: { instrument },
      timeoutMs: TIMEOUT_LLM,
    });
  }

  // Behavior endpoints (deduplicated — these are called by multiple hooks on mount)
  async getUserProfiles() {
    return this.dedup("profiles", () =>
      this.request<PaginatedResponse<UserProfile>>("/behavior/profiles/")
    , 8000);
  }

  async getTrades(userId?: string) {
    const query = userId ? `?user_id=${userId}` : "";
    return this.dedup(`trades:${userId ?? ""}`, () =>
      this.request<PaginatedResponse<Trade>>(`/behavior/trades/${query}`)
    , 8000);
  }

  async getBehavioralMetrics(userId?: string) {
    const query = userId ? `?user_id=${userId}` : "";
    return this.dedup(`metrics:${userId ?? ""}`, () =>
      this.request<PaginatedResponse<BehavioralMetric>>(`/behavior/metrics/${query}`)
    , 8000);
  }

  async analyzeBatch(userId: string, hours: number = 24) {
    return this.dedup(`analyze:${userId}:${hours}`, () =>
      this.request<BatchAnalysis>("/behavior/trades/analyze_batch/", {
        method: "POST",
        body: { user_id: userId, hours },
        requiresAuth: false,
        timeoutMs: TIMEOUT_ANALYSIS,
      })
    , 10000);
  }

  // Demo scenario endpoints
  async analyzeScenario(scenario: string) {
    return this.request<ScenarioAnalysis>("/demo/analyze/", {
      method: "POST",
      body: { scenario },
      timeoutMs: TIMEOUT_LLM,
    });
  }

  async listScenarios() {
    return this.request<ScenariosListResponse>("/demo/scenarios/");
  }

  // Content endpoints
  async getPersonas() {
    return this.dedup("personas", () =>
      this.request<PaginatedResponse<AIPersona>>("/content/personas/")
    , 10000);
  }

  async getPosts() {
    return this.dedup("posts", () =>
      this.request<PaginatedResponse<SocialPost>>("/content/posts/")
    , 10000);
  }

  async generateContent(data: GenerateContentRequest) {
    return this.request<GenerateContentResponse>("/content/generate/", {
      method: "POST",
      body: data,
      timeoutMs: TIMEOUT_LLM,
    });
  }

  async publishToBluesky(content: string, postType: string = "single") {
    return this.request<PublishResponse>("/content/publish-bluesky/", {
      method: "POST",
      body: { content, type: postType },
      timeoutMs: TIMEOUT_LLM,
    });
  }

  // Chat endpoint (REST fallback)
  async chatAsk(message: string, conversationHistory?: ChatMessage[]) {
    return this.request<ChatResponse>("/chat/ask/", {
      method: "POST",
      body: { message, conversation_history: conversationHistory },
      timeoutMs: TIMEOUT_LLM,
    });
  }

  // Demo endpoints
  async seedDemo() {
    return this.request<DemoResponse>("/demo/seed/", { method: "POST" });
  }

  async loadScenario(scenario: string) {
    return this.request<LoadScenarioResponse>("/demo/load-scenario/", {
      method: "POST",
      body: { scenario },
      timeoutMs: TIMEOUT_LLM,
    });
  }

  async wowMoment(userId: string, instrument: string) {
    return this.request<WowMomentResponse>("/demo/wow-moment/", {
      method: "POST",
      body: { user_id: userId, instrument },
      timeoutMs: TIMEOUT_PIPELINE,
    });
  }

  // Agent Team Pipeline endpoints
  async runPipeline(params: PipelineRequest = {}) {
    return this.request<PipelineResponse>("/agents/pipeline/", {
      method: "POST",
      body: params,
      timeoutMs: TIMEOUT_PIPELINE,
    });
  }

  async runMonitor(instruments?: string[], customEvent?: CustomEvent) {
    return this.request<MonitorResponse>("/agents/monitor/", {
      method: "POST",
      body: { instruments, custom_event: customEvent },
      timeoutMs: TIMEOUT_LLM,
    });
  }

  async runAnalyst(event: VolatilityEventInput) {
    return this.request<AnalysisReportResponse>("/agents/analyst/", {
      method: "POST",
      body: event,
      timeoutMs: TIMEOUT_LLM,
    });
  }

  async runAdvisor(analysisReport: AnalysisReportResponse, userPortfolio?: PortfolioPosition[]) {
    return this.request<PersonalizedInsightResponse>("/agents/advisor/", {
      method: "POST",
      body: { analysis_report: analysisReport, user_portfolio: userPortfolio },
      timeoutMs: TIMEOUT_LLM,
    });
  }

  async runContentGen(analysisReport: AnalysisReportResponse, personalizedInsight?: PersonalizedInsightResponse) {
    return this.request<MarketCommentaryResponse>("/agents/content-gen/", {
      method: "POST",
      body: { analysis_report: analysisReport, personalized_insight: personalizedInsight },
      timeoutMs: TIMEOUT_LLM,
    });
  }

  // Sentinel endpoint
  async runSentinel(params: SentinelRequest) {
    return this.request<BehavioralSentinelResponse>("/agents/sentinel/", {
      method: "POST",
      body: params,
      timeoutMs: TIMEOUT_LLM,
    });
  }

  // Deriv trade sync
  async syncDerivTrades(userId?: string, daysBack?: number) {
    return this.request<DerivSyncResponse>("/behavior/trades/sync_deriv/", {
      method: "POST",
      body: { user_id: userId, days_back: daysBack },
      timeoutMs: TIMEOUT_LLM,
    });
  }

  // ─── New API Endpoints (Phase 3-6) ──────────────────────────────

  // Deriv portfolio & balance
  async getPortfolio() {
    return this.request<DerivPortfolioResponse>("/behavior/portfolio/");
  }

  async getBalance() {
    return this.request<DerivBalanceResponse>("/behavior/balance/");
  }

  async getRealityCheck() {
    return this.request<DerivRealityCheckResponse>("/behavior/reality-check/");
  }

  // Finnhub economic calendar
  async getEconomicCalendar() {
    return this.dedup("calendar", () =>
      this.request<EconomicCalendarResponse>("/market/calendar/")
    , 60000);
  }

  // Finnhub pattern recognition
  async getPatternRecognition(instrument: string) {
    return this.request<PatternRecognitionResponse>("/market/patterns/", {
      method: "POST",
      body: { instrument },
    });
  }

  // NewsAPI top headlines
  async getTopHeadlines(limit: number = 10) {
    return this.dedup(`headlines:${limit}`, () =>
      this.request<TopHeadlinesResponse>(`/market/headlines/?limit=${limit}`)
    , 30000);
  }

  // Deriv active symbols
  async getActiveSymbols(market?: string) {
    const query = market ? `?market=${market}` : "";
    return this.request<ActiveSymbolsResponse>(`/market/instruments/${query}`);
  }

  // Bluesky social search
  async searchBluesky(query: string, limit: number = 10) {
    return this.request<BlueskySearchResponse>(`/content/bluesky-search/?q=${encodeURIComponent(query)}&limit=${limit}`);
  }

  // Chat with history
  async chatWithHistory(message: string, agentType: string = "auto", history?: Array<{role: string; content: string}>, userId?: string) {
    return this.request<ChatResponse>("/agents/chat/", {
      method: "POST",
      timeoutMs: TIMEOUT_LLM,
      body: { message, agent_type: agentType, history, user_id: userId },
    });
  }

  // ─── Copy Trading endpoints ───────────────────────────────────────
  async getCopyTraders(limit: number = 10) {
    return this.request<CopyTradingListResponse>("/agents/copytrading/", {
      method: "POST",
      body: { action: "list", limit },
    });
  }

  async getTraderStats(traderId: string) {
    return this.request<TraderStatsResponse>("/agents/copytrading/", {
      method: "POST",
      body: { action: "stats", trader_id: traderId },
    });
  }

  async getTraderRecommendation(userId: string) {
    return this.request<TraderRecommendationResponse>("/agents/copytrading/", {
      method: "POST",
      body: { action: "recommend", user_id: userId },
      timeoutMs: TIMEOUT_LLM,
    });
  }

  async startCopyTrading(traderId: string, apiToken: string) {
    return this.request<CopyTradeActionResponse>("/agents/copytrading/", {
      method: "POST",
      body: { action: "start", trader_id: traderId, api_token: apiToken },
    });
  }

  async stopCopyTrading(traderId: string, apiToken: string) {
    return this.request<CopyTradeActionResponse>("/agents/copytrading/", {
      method: "POST",
      body: { action: "stop", trader_id: traderId, api_token: apiToken },
    });
  }

  // ─── Trading endpoints ────────────────────────────────────────────
  async getContractQuote(instrument: string, contractType: string = "CALL", amount: number = 10, duration: number = 5, durationUnit: string = "t") {
    return this.request<ContractQuoteResponse>("/agents/trading/", {
      method: "POST",
      body: { action: "quote", instrument, contract_type: contractType, amount, duration, duration_unit: durationUnit },
    });
  }

  async executeDemoTrade(instrument: string, contractType: string, amount: number, duration: number, durationUnit: string) {
    return this.request<DemoTradeResponse>("/agents/trading/", {
      method: "POST",
      body: { action: "buy", instrument, contract_type: contractType, amount, duration, duration_unit: durationUnit },
    });
  }

  async closeDemoPosition(contractId: number) {
    return this.request<ClosePositionResponse>("/agents/trading/", {
      method: "POST",
      body: { action: "sell", contract_id: contractId },
    });
  }

  async getOpenPositions() {
    return this.request<OpenPositionsResponse>("/agents/trading/", {
      method: "POST",
      body: { action: "positions" },
    });
  }

  // ─── Trading Twin endpoint ──────────────────────────────────────────

  async getTradingTwin(userId?: string, days = 30, startingEquity = 10000) {
    return this.request<TradingTwinResult>("/behavior/trading-twin/", {
      method: "POST",
      body: { user_id: userId, days, starting_equity: startingEquity },
      timeoutMs: TIMEOUT_LLM,
    });
  }

  // ─── Multi-Persona Content endpoint ────────────────────────────────

  async getMultiPersonaContent(event: Record<string, unknown>) {
    return this.request<MultiPersonaContentResult>("/content/multi-persona/", {
      method: "POST",
      body: { event },
      timeoutMs: TIMEOUT_LLM,
    });
  }

  // ─── Demo trigger + health endpoints ───────────────────────────────

  async triggerDemoEvent(instrument = "BTC/USD", changePct = -3.2) {
    return this.request<{ status: string; instrument: string; change_pct: number; message: string }>(
      "/demo/trigger-event/",
      {
        method: "POST",
        body: { instrument, change_pct: changePct },
      }
    );
  }

  async getDemoHealth() {
    return this.request<{ ready: boolean; checks: Record<string, unknown>; warnings: string[] }>(
      "/demo/health/"
    );
  }

  async runDemoScriptV2(name = "championship_run") {
    return this.request<DemoRunResult>("/demo/run-script-v2/", {
      method: "POST",
      body: { script_name: name },
      timeoutMs: TIMEOUT_PIPELINE,
    });
  }

  // ─── Demo script endpoints ────────────────────────────────────────
  async getDemoScripts() {
    return this.request<DemoScriptsResponse>("/demo/scripts/");
  }

  async getDemoScript(name: string) {
    return this.request<DemoScript>(`/demo/scripts/${name}/`);
  }

  async runDemoScript(name: string, instrument?: string, userId?: string) {
    return this.request<DemoRunResult>("/demo/run-script/", {
      method: "POST",
      body: { script_name: name, instrument, user_id: userId },
      timeoutMs: TIMEOUT_PIPELINE,
    });
  }
}

// Error class
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

// Paginated response from DRF
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// Types matching backend models
export interface MarketInsight {
  id: string;
  instrument: string;
  insight_type: string;
  content: string;
  sentiment_score?: number | null;
  generated_at?: string;
  // Backward-compatible fields for older payloads
  confidence?: number | null;
  created_at?: string;
}

export interface MarketInsightsResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: MarketInsight[];
}

export interface MarketBrief {
  summary: string;
  instruments: InstrumentData[];
  timestamp: string;
}

export interface InstrumentData {
  symbol: string;
  price: number | null;
  source?: string;
  change?: number;
  change_percent?: number;
  trend?: string;
}

export interface MarketAnalysis {
  answer: string;
  disclaimer: string;
  sources?: unknown[];
  tools_used?: string[];
}

export interface LivePrice {
  instrument: string;
  deriv_symbol?: string;
  price: number | null;
  bid?: number | null;
  ask?: number | null;
  timestamp: string;
  source: string;
  error?: string;
}

export interface MarketCandle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface MarketHistory {
  instrument: string;
  timeframe: string;
  candles: MarketCandle[];
  change: number;
  change_percent: number;
  source: string;
  error?: string;
}

export interface MarketTechnicals {
  instrument: string;
  timeframe: string;
  current_price?: number;
  trend?: "bullish" | "bearish" | "neutral";
  volatility?: "low" | "medium" | "high";
  key_levels?: {
    support: number;
    resistance: number;
  };
  indicators?: {
    sma20?: number;
    sma50?: number | null;
    rsi14?: number;
  };
  summary?: string;
  source?: string;
  error?: string;
}

export interface MarketSentiment {
  instrument: string;
  sentiment: "bullish" | "bearish" | "neutral";
  score: number;
  key_points?: string[];
  confidence?: number;
  sources: string[];
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  preferences: Record<string, unknown>;
  watchlist: string[];
  created_at: string;
}

export interface Trade {
  id: string;
  user: string;
  instrument: string;
  direction: "buy" | "sell";
  entry_price: number | null;
  exit_price: number | null;
  pnl: number;
  duration_seconds: number | null;
  opened_at: string;
  closed_at: string | null;
  is_mock: boolean;
  created_at: string;
}

export interface BehavioralMetric {
  id: string;
  user: string;
  trading_date: string;
  total_trades: number;
  win_count: number;
  loss_count: number;
  avg_hold_time: number | null;
  risk_score: number | null;
  emotional_state: string;
  pattern_flags: Record<string, boolean>;
  created_at: string;
}

export interface BatchAnalysis {
  analysis: {
    patterns: Record<string, unknown>;
    summary: string;
    needs_nudge: boolean;
    trade_count: number;
    time_window: string;
  };
  nudge: {
    nudge_type: string;
    message: string;
    severity: string;
    suggested_action: string;
  } | null;
}

export interface ScenarioAnalysis {
  scenario: string;
  user_id: string;
  trades_created: number;
  analysis: {
    patterns: Record<string, unknown>;
    summary: string;
    needs_nudge: boolean;
    trade_count: number;
    time_window: string;
  };
  nudge: {
    nudge_type: string;
    message: string;
    severity: string;
    suggested_action: string;
  } | null;
  expected_detection: string;
  expected_nudge: string;
}

export interface ScenariosListResponse {
  scenarios: {
    name: string;
    description: string;
    expected_detection: string;
    expected_nudge: string;
  }[];
}

export interface LoadScenarioResponse {
  status: string;
  scenario: string;
  user_id: string;
  trades_created: number;
  expected_detection: string;
  expected_nudge: string;
}

export interface AIPersona {
  id: string;
  name: string;
  personality_type?: string;
  system_prompt?: string;
  created_at?: string;
}

export interface SocialPost {
  id: string;
  persona: string;
  persona_name?: string;
  platform: string;
  content: string;
  status: "draft" | "published" | "scheduled";
  engagement_metrics?: Record<string, unknown>;
  published_at?: string | null;
  scheduled_at?: string | null;
  created_at: string;
}

export interface GenerateContentRequest {
  insight: string;
  platform: "bluesky_post" | "bluesky_thread";
  persona_id?: string;
}

export interface GenerateContentResponse {
  content: string;
  platform: string;
  persona: string;
  disclaimer: string;
  status?: string;
}

export interface PublishResponse {
  success: boolean;
  status?: string;
  platform?: string;
  uri?: string;
  results?: Array<{ uri?: string; url?: string; index?: number }>;
  error?: string;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: string;
  type?: "normal" | "nudge" | "disclaimer";
}

export interface ChatResponse {
  message?: string;
  reply?: string;
  agent_type?: string;
  tools_used?: string[];
  source?: string;
  disclaimer?: string;
  nudge?: string;
}

export interface DemoResponse {
  success: boolean;
  message: string;
  user_id?: string;
}

export interface WowMomentResponse {
  market_analysis: string;
  behavior_insight: string;
  content_preview: string;
  disclaimer: string;
}

// ─── Agent Team Pipeline types ───

export interface CustomEvent {
  instrument: string;
  price?: number;
  change_pct: number;
}

export interface PipelineRequest {
  instruments?: string[];
  custom_event?: CustomEvent;
  user_portfolio?: PortfolioPosition[];
  skip_content?: boolean;
  user_id?: string;
}

export interface PortfolioPosition {
  instrument: string;
  direction: "long" | "short";
  size: number;
  entry_price: number;
  pnl: number;
}

export interface VolatilityEventData {
  instrument: string;
  current_price: number | null;
  price_change_pct: number;
  direction: "spike" | "drop";
  magnitude: "high" | "medium";
  detected_at: string;
  raw_data: Record<string, unknown>;
}

export interface VolatilityEventInput {
  instrument: string;
  current_price?: number;
  price_change_pct: number;
  direction: "spike" | "drop";
  magnitude: "high" | "medium";
}

export interface AnalysisReportResponse {
  instrument: string;
  event_summary: string;
  root_causes: string[];
  news_sources: { title: string; url: string; source?: string }[];
  sentiment: string;
  sentiment_score: number;
  key_data_points: string[];
  generated_at: string;
}

export interface PersonalizedInsightResponse {
  instrument: string;
  impact_summary: string;
  affected_positions: PortfolioPosition[];
  risk_assessment: "high" | "medium" | "low";
  suggestions: string[];
  generated_at: string;
}

export interface MarketCommentaryResponse {
  post: string;
  hashtags: string[];
  data_points: string[];
  platform: string;
  published: boolean;
  bluesky_uri: string;
  bluesky_url: string;
  generated_at: string;
}

export interface BehavioralSentinelResponse {
  instrument: string;
  market_event_summary: string;
  behavioral_context: string;
  risk_level: "high" | "medium" | "low";
  personalized_warning: string;
  historical_pattern_match: string;
  user_stats_snapshot: Record<string, unknown>;
  generated_at: string;
}

export interface SentinelRequest {
  instrument: string;
  price_change_pct: number;
  direction: "spike" | "drop";
  event_summary?: string;
  user_id?: string;
  current_price?: number;
  sentiment?: string;
  sentiment_score?: number;
  root_causes?: string[];
}

export interface DerivSyncResponse {
  status: string;
  user_id: string;
  trades_synced: number;
  trades_updated: number;
  total_trades: number;
  analysis_summary: Record<string, unknown> | null;
}

export interface PipelineResponse {
  status: "success" | "partial" | "no_event" | "error";
  volatility_event: VolatilityEventData | null;
  analysis_report: AnalysisReportResponse | null;
  personalized_insight: PersonalizedInsightResponse | null;
  sentinel_insight: BehavioralSentinelResponse | null;
  market_commentary: MarketCommentaryResponse | null;
  errors: string[];
  pipeline_started_at: string;
  pipeline_finished_at: string;
}

export interface MonitorResponse {
  status: "detected" | "no_event";
  event?: VolatilityEventData;
  message?: string;
}

// ─── New API Types (Phase 3-6) ──────────────────────────────────

export interface DerivPortfolioResponse {
  contracts?: Array<{
    symbol: string;
    contract_id: number;
    contract_type: string;
    buy_price: number;
    payout: number;
    date_start: number;
    date_expiry?: number;
    longcode: string;
  }>;
}

export interface DerivBalanceResponse {
  balance: number;
  currency: string;
  id?: string;
  loginid?: string;
}

export interface DerivRealityCheckResponse {
  buy_amount?: number;
  buy_count?: number;
  currency?: string;
  open_contract_count?: number;
  potential_profit?: number;
  sell_amount?: number;
  sell_count?: number;
  start_time?: number;
}

export interface EconomicEvent {
  country: string;
  event: string;
  impact: string;
  date: string;
  time: string;
  actual: number | null;
  estimate: number | null;
  prev: number | null;
  unit: string;
}

export interface EconomicCalendarResponse {
  events: EconomicEvent[];
  from_date: string;
  to_date: string;
  count: number;
  source: string;
}

export interface PatternRecognitionResponse {
  instrument: string;
  patterns: Array<Record<string, unknown>>;
  count: number;
  source: string;
}

export interface TopHeadlinesResponse {
  headlines: Array<{
    title: string;
    description: string;
    url: string;
    publishedAt: string;
    source: string;
  }>;
}

export interface ActiveSymbolsResponse {
  instruments: Array<{
    symbol: string;
    display_name: string;
    market: string;
    market_display_name: string;
    submarket: string;
    submarket_display_name: string;
    is_trading_suspended: number;
    pip: number;
  }>;
  count: number;
}

export interface BlueskyPost {
  text: string;
  author: string;
  author_name: string;
  like_count: number;
  repost_count: number;
  uri: string;
  url: string;
  created_at: string;
}

export interface BlueskySearchResponse {
  query: string;
  posts: BlueskyPost[];
  count: number;
}

export interface WowMomentResponse {
  market_analysis: string;
  behavior_insight: string;
  sentinel_fusion?: {
    personalized_warning: string;
    behavioral_context: string;
    risk_level: string;
    historical_pattern_match: string;
  } | string;
  content_preview: string;
  economic_calendar?: {
    high_impact_events: EconomicEvent[];
    total_events: number;
  } | string;
  social_sentiment?: {
    platform: string;
    query: string;
    posts: BlueskyPost[];
    total_found: number;
  } | string;
  disclaimer: string;
}

// ─── Trading Twin types ─────────────────────────────────────────────

export interface TwinPoint {
  timestamp: string;
  impulsive_equity: number;
  disciplined_equity: number;
  trade_id?: string;
  is_impulsive: boolean;
  pattern?: string;
}

export interface TradingTwinResult {
  equity_curve: TwinPoint[];
  impulsive_final_equity: number;
  disciplined_final_equity: number;
  equity_difference: number;
  equity_difference_pct: number;
  total_trades: number;
  impulsive_trades: number;
  disciplined_trades: number;
  impulsive_loss: number;
  disciplined_gain: number;
  pattern_breakdown: Record<string, number>;
  narrative: string;
  key_insight: string;
  analysis_period_days: number;
  generated_at: string;
}

// ─── Multi-Persona Content types ────────────────────────────────────

export interface MultiPersonaContentResult {
  event_summary: string;
  calm_analyst_post: string;
  data_nerd_post: string;
  trading_coach_post: string;
  generated_at: string;
}

// ─── Copy Trading types ─────────────────────────────────────────────

export interface CopyTrader {
  loginid: string;
  token: string;
  avg_profit: number;
  total_trades: number;
  copiers: number;
  performance_probability: number;
  min_trade_stake?: number | null;
  trade_types?: string[];
  balance?: number | null;
  currency?: string;
  win_rate?: number;
  avg_loss?: number;
  active_since?: string | null;
  _demo?: boolean;
}

export interface TraderStatsResponse {
  trader_id: string;
  stats: {
    avg_profit: number;
    total_trades: number;
    copiers: number;
    performance_probability: number;
    monthly_profitable_trades: number;
    active_since: string;
  };
  error?: string;
}

export interface TraderRecommendationResponse {
  recommendations: Array<{
    trader: CopyTrader;
    compatibility_score: number;
    reasons: string[];
  }>;
  disclaimer: string;
  error?: string;
}

export interface CopyTradingListResponse {
  traders: CopyTrader[];
  count: number;
  total_count: number;
  source?: string;
  disclaimer?: string;
  error?: string;
}

export interface CopyTradeActionResponse {
  success: boolean;
  message: string;
  disclaimer?: string;
  error?: string;
}

// ─── Trading types ──────────────────────────────────────────────────

export interface ContractQuoteResponse {
  proposal_id: string;
  instrument: string;
  contract_type: string;
  ask_price: number;
  payout: number;
  spot: number;
  longcode: string;
  duration: number;
  duration_unit: string;
  disclaimer: string;
  error?: string;
}

export interface DemoTradeResponse {
  contract_id: number;
  buy_price: number;
  balance_after: number;
  longcode: string;
  start_time: string;
  disclaimer: string;
  error?: string;
}

export interface ClosePositionResponse {
  contract_id: number;
  sold_for: number;
  profit: number;
  error?: string;
}

export interface OpenPosition {
  contract_id: number;
  instrument: string;
  contract_type: string;
  buy_price: number;
  current_spot: number;
  profit: number;
  is_valid_to_sell: boolean;
  longcode: string;
}

export interface OpenPositionsResponse {
  positions: OpenPosition[];
  count: number;
  error?: string;
}

// ─── Demo script types ──────────────────────────────────────────────

export interface DemoStep {
  step_number: number;
  title: string;
  narration: string;
  api_endpoint: string;
  api_params: Record<string, unknown>;
  expected_duration_sec: number;
  wow_factor: string;
}

export interface DemoScript {
  name: string;
  total_duration_sec: number;
  opening_line: string;
  closing_line: string;
  steps: DemoStep[];
}

export interface DemoScriptsResponse {
  scripts: Array<{ name: string; description: string; total_duration_sec: number; step_count: number }>;
}

export interface DemoStepResult {
  step_number: number;
  title: string;
  status: "success" | "error";
  result: Record<string, unknown>;
  duration_ms: number;
  narration?: string;
  wow_factor?: string;
}

export interface DemoRunResult {
  script_name: string;
  status: "success" | "partial" | "error";
  steps: DemoStepResult[];
  total_duration_ms: number;
}

// Singleton instance
export const api = new ApiClient(process.env.NEXT_PUBLIC_API_URL);
export default api;
