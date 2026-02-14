"use client";

import { createContext, useContext, useState, useCallback, useEffect } from "react";
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

const DEMO_USER_ID = "d1000000-0000-0000-0000-000000000001";

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

// ─── Provider ────────────────────────────────────────────────────────
function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

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
          user_id: DEMO_USER_ID,
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
      } catch (err) {
        setError(err instanceof Error ? err.message : "Pipeline failed");
        setStages({
          monitor: "error",
          analyst: "error",
          advisor: "error",
          sentinel: "error",
          content: "error",
        });
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
        user_id: DEMO_USER_ID,
      });

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
      if (response.sentinel_insight !== undefined) {
        setStages((s) => ({ ...s, sentinel: "done", content: "running" }));
        await sleep(400);
      }
      if (response.market_commentary) {
        setStages((s) => ({ ...s, content: "done" }));
      }

      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Auto scan failed");
    } finally {
      setIsRunning(false);
    }
  }, [resetState]);

  return (
    <PipelineContext.Provider
      value={{ stages, result, isRunning, error, mode, setMode, runPipeline, runAutoScan }}
    >
      {children}
    </PipelineContext.Provider>
  );
}
