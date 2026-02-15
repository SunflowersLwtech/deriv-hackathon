"use client";

import { createContext, useContext, useState, useCallback, useEffect, useMemo } from "react";
import api, {
  type PipelineResponse,
  type CustomEvent,
  type PortfolioPosition,
} from "@/lib/api";

// ─── Types ───────────────────────────────────────────────────────────
export type StageStatus = "idle" | "running" | "done" | "error";

export interface StageState {
  monitor: StageStatus;
  analyst: StageStatus;
  advisor: StageStatus;
  sentinel: StageStatus;
  content: StageStatus;
}

export const IDLE_STAGES: StageState = {
  monitor: "idle",
  analyst: "idle",
  advisor: "idle",
  sentinel: "idle",
  content: "idle",
};

export const DEMO_EVENTS: { label: string; event: CustomEvent }[] = [
  { label: "BTC +5.2%", event: { instrument: "BTC/USD", price: 97500, change_pct: 5.2 } },
  { label: "ETH -4.1%", event: { instrument: "ETH/USD", price: 3100, change_pct: -4.1 } },
  { label: "V75 +2.3%", event: { instrument: "Volatility 75", price: 900000, change_pct: 2.3 } },
  { label: "V100 -1.8%", event: { instrument: "Volatility 100", price: 1500000, change_pct: -1.8 } },
];

export const DEMO_PORTFOLIO: PortfolioPosition[] = [
  { instrument: "BTC/USD", direction: "long", size: 0.1, entry_price: 95000, pnl: 250.0 },
  { instrument: "ETH/USD", direction: "long", size: 0.5, entry_price: 3200, pnl: -50.0 },
  { instrument: "Volatility 75", direction: "long", size: 1.0, entry_price: 900000, pnl: 120.0 },
  { instrument: "Volatility 100", direction: "short", size: 0.5, entry_price: 1500000, pnl: -35.0 },
];

// ─── Demo fallback generator ────────────────────────────────────────
// Generates a complete PipelineResponse from client-side demo data
// when the backend is unreachable / times out.

const DEMO_FALLBACK_POOL = [
  {
    instrument: "BTC/USD",
    price: 97500,
    change: 5.2,
    direction: "spike" as const,
    magnitude: "high" as const,
    sentiment: "Bullish — institutional accumulation detected amid ETF inflows.",
    causes: [
      "Spot Bitcoin ETF net inflows exceeded $500M in 24 hours",
      "Short liquidation cascade triggered above $95K resistance",
      "Macro risk-off rotation into digital assets ahead of CPI data",
    ],
    impact: "Your BTC/USD long position benefits from this spike. Unrealised P&L improved by ~$250. Consider scaling out partial profits at resistance.",
    commentary: "BTC surged past $97K as ETF inflows surged and shorts got liquidated. Momentum is strong but resistance at $100K looms large. Stay disciplined.",
    insight: "Historically, 5%+ daily BTC moves see a 60% retracement within 48h. Consider protecting profits with a trailing stop.",
    sentinelWarning: "Your trading history shows a tendency to add to winning positions during spikes. While BTC looks strong, 5%+ moves often retrace 60% within 48h.",
    sentinelContext: "Based on your last 30 days, you show a bias toward momentum chasing during volatile periods. This can lead to overexposure at local tops.",
    sentinelPattern: "In similar BTC spike events (>5% daily), your past trades show a 40% win rate when entering immediately vs. 65% when waiting for confirmation.",
  },
  {
    instrument: "ETH/USD",
    price: 3100,
    change: -4.1,
    direction: "drop" as const,
    magnitude: "high" as const,
    sentiment: "Bearish — whale sell-off and DeFi liquidations pressuring price.",
    causes: [
      "Large whale transferred 50K ETH to exchange wallets",
      "DeFi protocol liquidations cascading across Aave and Compound",
      "ETH/BTC ratio declining as capital rotates to Bitcoin",
    ],
    impact: "Your ETH/USD long position is under pressure. Unrealised P&L dropped by ~$50. Monitor the $3,000 support level closely.",
    commentary: "ETH dropped below $3,100 as whale selling and DeFi liquidations compounded. The ETH/BTC ratio continues to weaken. Key support at $3,000.",
    insight: "When ETH drops >4% while BTC rises, the divergence typically resolves within a week. Avoid adding to ETH longs until BTC stabilises.",
    sentinelWarning: "You tend to average down on losing positions. ETH is under pressure from whale activity. Averaging down here increases risk of larger drawdown.",
    sentinelContext: "Your last 30 days show 3 instances of adding to losers, resulting in 2 larger losses. The instinct to 'buy the dip' can be costly during structural selling.",
    sentinelPattern: "When ETH drops >4% while BTC rises, traders who averaged down had a 35% win rate vs. 58% for those who waited for stabilization.",
  },
  {
    instrument: "Volatility 75",
    price: 900000,
    change: 2.3,
    direction: "spike" as const,
    magnitude: "medium" as const,
    sentiment: "Neutral — synthetic index showing elevated but normal volatility.",
    causes: [
      "Algorithmic volatility expansion during high-activity session",
      "Mean-reversion patterns forming after sustained low-volatility period",
      "Increased retail trading volume during overlap hours",
    ],
    impact: "Your V75 long position gained ~$120. Synthetic indices are independent of macro events, so position sizing remains the key risk factor.",
    commentary: "V75 saw a 2.3% spike driven by algorithmic expansion. Synthetic indices follow statistical patterns — watch for mean-reversion signals.",
    insight: "V75 spikes of this magnitude typically revert within 2-4 hours. Consider tightening stops rather than adding to winners.",
    sentinelWarning: "You frequently hold V75 positions through volatile spikes without adjusting stops. This pattern has led to 3 unnecessary stop-outs in the last month.",
    sentinelContext: "Your synthetic index trading shows good entry timing but poor exit discipline. 60% of your V75 losses came from not tightening stops during spikes.",
    sentinelPattern: "V75 spikes of this magnitude historically revert within 2-4 hours. Traders who tighten stops see 25% fewer drawdowns on winning trades.",
  },
];

function generateDemoFallback(customEvent?: CustomEvent): PipelineResponse {
  const now = new Date().toISOString();

  // Pick a demo scenario — either matching the custom event or random
  let demo = DEMO_FALLBACK_POOL[Math.floor(Math.random() * DEMO_FALLBACK_POOL.length)];
  if (customEvent?.instrument) {
    const match = DEMO_FALLBACK_POOL.find(
      (d) => d.instrument.toLowerCase() === customEvent.instrument.toLowerCase()
    );
    if (match) demo = match;
  }

  const changePct = customEvent?.change_pct ?? demo.change;
  const price = customEvent?.price ?? demo.price;

  return {
    status: "success",
    volatility_event: {
      instrument: customEvent?.instrument ?? demo.instrument,
      current_price: price,
      price_change_pct: changePct,
      direction: changePct > 0 ? "spike" : "drop",
      magnitude: Math.abs(changePct) >= 3 ? "high" : Math.abs(changePct) >= 1.5 ? "medium" : "low",
      detected_at: now,
      raw_data: { source: "demo_fallback", note: "Backend unavailable — using client-side demo data" },
      demo_mode: true,
    },
    analysis_report: {
      instrument: customEvent?.instrument ?? demo.instrument,
      event_summary: `${demo.instrument} ${changePct > 0 ? "surged" : "dropped"} ${Math.abs(changePct).toFixed(1)}% to $${price.toLocaleString()}. ${demo.sentiment}`,
      root_causes: demo.causes,
      news_sources: [
        { title: "Demo data — connect backend for live analysis", url: "#", source: "TradeIQ Demo" },
      ],
      sentiment: changePct > 0 ? "bullish" : "bearish",
      sentiment_score: changePct > 0 ? 0.72 : -0.65,
      key_data_points: [
        `Price: $${price.toLocaleString()}`,
        `24h Change: ${changePct > 0 ? "+" : ""}${changePct.toFixed(1)}%`,
        `Magnitude: ${Math.abs(changePct) >= 3 ? "HIGH" : "MEDIUM"}`,
      ],
      generated_at: now,
    },
    personalized_insight: {
      instrument: customEvent?.instrument ?? demo.instrument,
      impact_summary: demo.impact,
      affected_positions: DEMO_PORTFOLIO.filter(
        (p) => p.instrument.toLowerCase() === (customEvent?.instrument ?? demo.instrument).toLowerCase()
      ),
      risk_assessment: Math.abs(changePct) >= 3 ? "high" : "medium",
      suggestions: [
        "Review position sizing relative to current volatility",
        "Consider setting tighter stop-losses during high-volatility periods",
        "Avoid impulsive trades — wait for confirmation before adding to positions",
      ],
      generated_at: now,
    },
    sentinel_insight: {
      instrument: customEvent?.instrument ?? demo.instrument,
      market_event_summary: `${demo.instrument} ${changePct > 0 ? "spike" : "drop"} of ${Math.abs(changePct).toFixed(1)}%`,
      behavioral_context: demo.sentinelContext,
      risk_level: Math.abs(changePct) >= 3 ? "high" as const : "medium" as const,
      personalized_warning: demo.sentinelWarning,
      historical_pattern_match: demo.sentinelPattern,
      user_stats_snapshot: {
        total_trades: 47,
        win_rate: 52.3,
        total_pnl: 185.50,
        period_days: 30,
      },
      generated_at: now,
    },
    market_commentary: {
      post: demo.commentary,
      hashtags: ["#TradeIQ", "#MarketAlert", `#${(customEvent?.instrument ?? demo.instrument).replace(/[/ ]/g, "")}`],
      data_points: [
        `${customEvent?.instrument ?? demo.instrument} ${changePct > 0 ? "+" : ""}${changePct.toFixed(1)}%`,
        `Price: $${price.toLocaleString()}`,
      ],
      platform: "demo",
      published: false,
      bluesky_uri: "",
      bluesky_url: "",
      generated_at: now,
    },
    errors: ["Backend unavailable — showing demo data. Results will be live when the server is reachable."],
    pipeline_started_at: now,
    pipeline_finished_at: now,
  };
}

// ─── Context ─────────────────────────────────────────────────────────
interface PipelineContextValue {
  stages: StageState;
  result: PipelineResponse | null;
  isRunning: boolean;
  error: string | null;
  mode: "auto" | "manual";
  setMode: (m: "auto" | "manual") => void;
  runPipeline: (customEvent?: CustomEvent) => Promise<void>;
  runAutoScan: () => Promise<void>;
}

const PipelineContext = createContext<PipelineContextValue | null>(null);

export function usePipelineContext(): PipelineContextValue {
  const ctx = useContext(PipelineContext);
  if (!ctx) throw new Error("usePipelineContext must be used within PipelineProvider");
  return ctx;
}

// ─── SessionStorage persistence ──────────────────────────────────────
const STORAGE_KEY = "tradeiq-pipeline-cache";
const CACHE_TTL = 30 * 60_000; // 30 minutes

interface PipelineCache {
  stages: StageState;
  result: PipelineResponse | null;
  mode: "auto" | "manual";
  savedAt: number;
}

function loadCache(): PipelineCache | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as PipelineCache;
    if (Date.now() - parsed.savedAt > CACHE_TTL) {
      sessionStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

function saveCache(stages: StageState, result: PipelineResponse | null, mode: "auto" | "manual") {
  try {
    const data: PipelineCache = { stages, result, mode, savedAt: Date.now() };
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch { /* quota exceeded — ignore */ }
}

// ─── Helpers ─────────────────────────────────────────────────────────
function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** Animate stage progression for a complete pipeline response. */
async function animateStages(
  response: PipelineResponse,
  setStages: React.Dispatch<React.SetStateAction<StageState>>,
) {
  if (response.volatility_event) {
    setStages((s) => ({ ...s, monitor: "done", analyst: "running" }));
    await sleep(400);
  }
  if (response.analysis_report) {
    setStages((s) => ({ ...s, analyst: "done", advisor: "running" }));
    await sleep(400);
  }
  if (response.personalized_insight) {
    setStages((s) => ({ ...s, advisor: "done", sentinel: "running" }));
    await sleep(400);
  }
  // sentinel may be null (no user_id) — still mark done
  setStages((s) => ({ ...s, sentinel: response.sentinel_insight ? "done" : "done", content: "running" }));
  await sleep(400);
  if (response.market_commentary) {
    setStages((s) => ({ ...s, content: "done" }));
  }
}

// ─── Provider ────────────────────────────────────────────────────────
export default function PipelineProvider({ children }: { children: React.ReactNode }) {
  const cached = loadCache();
  const [stages, setStages] = useState<StageState>(cached?.stages ?? { ...IDLE_STAGES });
  const [result, setResult] = useState<PipelineResponse | null>(cached?.result ?? null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"auto" | "manual">(cached?.mode ?? "manual");

  // Persist to sessionStorage on every state change
  useEffect(() => {
    saveCache(stages, result, mode);
  }, [stages, result, mode]);

  const resetState = useCallback(() => {
    setStages({ ...IDLE_STAGES });
    setResult(null);
    setError(null);
  }, []);

  const runPipeline = useCallback(
    async (customEvent?: CustomEvent) => {
      resetState();
      setIsRunning(true);
      setStages((s) => ({ ...s, monitor: "running" }));

      try {
        const response = await api.runPipeline({
          custom_event: customEvent,
          user_portfolio: DEMO_PORTFOLIO,
        });

        if (response.volatility_event) {
          setStages((s) => ({ ...s, monitor: "done", analyst: "running" }));
          await sleep(400);
        } else {
          setStages((s) => ({ ...s, monitor: "error" }));
          setResult(response);
          setIsRunning(false);
          return;
        }

        if (response.analysis_report) {
          setStages((s) => ({ ...s, analyst: "done", advisor: "running" }));
          await sleep(400);
        } else {
          setStages((s) => ({ ...s, analyst: "error" }));
        }

        if (response.personalized_insight) {
          setStages((s) => ({ ...s, advisor: "done", sentinel: "running" }));
          await sleep(400);
        } else {
          setStages((s) => ({ ...s, advisor: "error" }));
        }

        if (response.sentinel_insight) {
          setStages((s) => ({ ...s, sentinel: "done", content: "running" }));
          await sleep(500);
        } else {
          setStages((s) => ({
            ...s,
            sentinel: response.sentinel_insight === null ? "done" : "error",
            content: "running",
          }));
          await sleep(300);
        }

        if (response.market_commentary) {
          setStages((s) => ({ ...s, content: "done" }));
        } else {
          setStages((s) => ({ ...s, content: "error" }));
        }

        setResult(response);
      } catch (err: unknown) {
        // Differentiate error types for better UX
        const isNetwork =
          err instanceof TypeError && /fetch|network/i.test(err.message);
        const status = (err as { status?: number })?.status;

        let errorMsg: string;
        if (isNetwork) {
          errorMsg = "Backend unavailable — showing demo data";
        } else if (status === 401 || status === 403) {
          errorMsg = "Authentication error — showing demo data";
        } else if (status === 429) {
          errorMsg = "Rate limited — please wait a moment and try again";
        } else if (status && status >= 500) {
          errorMsg = "Server error — showing demo data";
        } else {
          errorMsg = "Unexpected error — showing demo data";
        }

        const fallback = generateDemoFallback(customEvent);
        await animateStages(fallback, setStages);
        setResult(fallback);
        setError(errorMsg);
      } finally {
        setIsRunning(false);
      }
    },
    [resetState],
  );

  const runAutoScan = useCallback(async () => {
    resetState();
    setIsRunning(true);
    setStages((s) => ({ ...s, monitor: "running" }));

    try {
      const response = await api.runPipeline({
        user_portfolio: DEMO_PORTFOLIO,
      });

      await animateStages(response, setStages);
      setResult(response);
    } catch (err: unknown) {
      const isNetwork =
        err instanceof TypeError && /fetch|network/i.test(err.message);
      const errorMsg = isNetwork
        ? "Backend unavailable — showing demo data"
        : "Unexpected error — showing demo data";

      const fallback = generateDemoFallback();
      await animateStages(fallback, setStages);
      setResult(fallback);
      setError(errorMsg);
    } finally {
      setIsRunning(false);
    }
  }, [resetState]);

  const contextValue = useMemo(
    () => ({ stages, result, isRunning, error, mode, setMode, runPipeline, runAutoScan }),
    [stages, result, isRunning, error, mode, setMode, runPipeline, runAutoScan],
  );

  return (
    <PipelineContext.Provider value={contextValue}>
      {children}
    </PipelineContext.Provider>
  );
}
