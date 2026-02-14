"use client";

import { useState, useCallback } from "react";
import AppShell from "@/components/layout/AppShell";
import { cn } from "@/lib/utils";
import api, {
  type PipelineResponse,
  type CustomEvent,
  type PortfolioPosition,
} from "@/lib/api";

type StageStatus = "idle" | "running" | "done" | "error";

interface StageState {
  monitor: StageStatus;
  analyst: StageStatus;
  advisor: StageStatus;
  sentinel: StageStatus;
  content: StageStatus;
}

const DEMO_USER_ID = "d1000000-0000-0000-0000-000000000001";

const DEMO_EVENTS: { label: string; event: CustomEvent }[] = [
  { label: "BTC +5.2%", event: { instrument: "BTC/USD", price: 97500, change_pct: 5.2 } },
  { label: "ETH -4.1%", event: { instrument: "ETH/USD", price: 3100, change_pct: -4.1 } },
  { label: "V75 +2.3%", event: { instrument: "Volatility 75", price: 900000, change_pct: 2.3 } },
  { label: "V100 -1.8%", event: { instrument: "Volatility 100", price: 1500000, change_pct: -1.8 } },
];

const DEMO_PORTFOLIO: PortfolioPosition[] = [
  { instrument: "BTC/USD", direction: "long", size: 0.1, entry_price: 95000, pnl: 250.0 },
  { instrument: "ETH/USD", direction: "long", size: 0.5, entry_price: 3200, pnl: -50.0 },
  { instrument: "Volatility 75", direction: "long", size: 1.0, entry_price: 900000, pnl: 120.0 },
  { instrument: "Volatility 100", direction: "short", size: 0.5, entry_price: 1500000, pnl: -35.0 },
];

export default function PipelinePage() {
  const [stages, setStages] = useState<StageState>({
    monitor: "idle",
    analyst: "idle",
    advisor: "idle",
    sentinel: "idle",
    content: "idle",
  });
  const [result, setResult] = useState<PipelineResponse | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<"auto" | "manual">("manual");

  const resetState = useCallback(() => {
    setStages({ monitor: "idle", analyst: "idle", advisor: "idle", sentinel: "idle", content: "idle" });
    setResult(null);
    setError(null);
  }, []);

  const runPipeline = useCallback(
    async (customEvent?: CustomEvent) => {
      resetState();
      setIsRunning(true);

      // Animate stages sequentially
      setStages((s) => ({ ...s, monitor: "running" }));

      try {
        const response = await api.runPipeline({
          custom_event: customEvent,
          user_portfolio: DEMO_PORTFOLIO,
          user_id: DEMO_USER_ID,
        });

        // Animate stage completion based on response
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
          setStages((s) => ({ ...s, sentinel: response.sentinel_insight === null ? "done" : "error", content: "running" }));
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
        setStages({ monitor: "error", analyst: "error", advisor: "error", sentinel: "error", content: "error" });
      } finally {
        setIsRunning(false);
      }
    },
    [resetState]
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
    <AppShell>
      <div className="p-6 md:p-10 space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-wider mono-data">
              AGENT TEAM PIPELINE
            </h1>
            <p className="text-sm text-muted-foreground mt-2">
              5-agent collaboration: Monitor &rarr; Analyst &rarr; Advisor &rarr; Sentinel &rarr; Content
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMode("manual")}
              className={cn(
                "px-5 py-2.5 text-sm font-medium tracking-wider rounded-md transition-colors mono-data",
                mode === "manual"
                  ? "bg-white text-black"
                  : "bg-surface text-muted hover:text-white border border-border"
              )}
            >
              MANUAL
            </button>
            <button
              onClick={() => setMode("auto")}
              className={cn(
                "px-5 py-2.5 text-sm font-medium tracking-wider rounded-md transition-colors mono-data",
                mode === "auto"
                  ? "bg-white text-black"
                  : "bg-surface text-muted hover:text-white border border-border"
              )}
            >
              AUTO SCAN
            </button>
          </div>
        </div>

        {/* Pipeline Stages Visualisation — 5 columns */}
        <div className="bg-card border border-border rounded-md p-6">
          <div className="flex items-center gap-3 mb-6">
            <h3 className="text-sm font-semibold tracking-wider text-muted uppercase mono-data">
              PIPELINE STATUS
            </h3>
            {isRunning && (
              <div className="flex items-center gap-2">
                <div className="live-dot" />
                <span className="text-[11px] text-profit mono-data">PROCESSING</span>
              </div>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-5">
            <StageCard
              title="1. MONITOR"
              description="Detect volatility (Redis)"
              status={stages.monitor}
              icon="📡"
            />
            <StageCard
              title="2. ANALYST"
              description="Root cause analysis"
              status={stages.analyst}
              icon="🔍"
            />
            <StageCard
              title="3. ADVISOR"
              description="Portfolio interpretation"
              status={stages.advisor}
              icon="📊"
            />
            <StageCard
              title="4. SENTINEL"
              description="Behavior + market fusion"
              status={stages.sentinel}
              icon="🧠"
            />
            <StageCard
              title="5. CONTENT"
              description="Bluesky commentary"
              status={stages.content}
              icon="🦋"
            />
          </div>

          {/* Connector arrows (desktop only) */}
          <div className="hidden md:flex items-center justify-between px-10 -mt-8 mb-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="flex-1 flex justify-center">
                <span className="text-muted text-lg">&rarr;</span>
              </div>
            ))}
          </div>
        </div>

        {/* Trigger Controls */}
        <div className="bg-card border border-border rounded-md p-6">
          <h3 className="text-sm font-semibold tracking-wider text-muted uppercase mono-data mb-5">
            {mode === "manual" ? "MANUAL TRIGGER" : "AUTO SCAN"}
          </h3>

          {mode === "manual" ? (
            <div className="flex flex-wrap gap-3">
              {DEMO_EVENTS.map((demo) => (
                <button
                  key={demo.label}
                  onClick={() => runPipeline(demo.event)}
                  disabled={isRunning}
                  className={cn(
                    "px-5 py-3 text-sm font-medium tracking-wider rounded-md transition-all mono-data",
                    "border border-border hover:border-profit/50 hover:bg-surface",
                    demo.event.change_pct > 0 ? "text-profit" : "text-loss",
                    isRunning && "opacity-50 cursor-not-allowed"
                  )}
                >
                  {demo.event.instrument} {demo.event.change_pct > 0 ? "+" : ""}
                  {demo.event.change_pct}%
                </button>
              ))}
            </div>
          ) : (
            <button
              onClick={runAutoScan}
              disabled={isRunning}
              className={cn(
                "px-8 py-3.5 text-sm font-bold tracking-wider rounded-md transition-all mono-data",
                "bg-profit text-black hover:bg-profit/80",
                isRunning && "opacity-50 cursor-not-allowed"
              )}
            >
              {isRunning ? "SCANNING..." : "SCAN ALL MARKETS"}
            </button>
          )}
        </div>

        {/* Error Display */}
        {error && (
          <div className="bg-loss/10 border border-loss/30 rounded-sm p-4">
            <p className="text-xs text-loss mono-data">{error}</p>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-5">
            {/* Stage 1 Result: Volatility Event */}
            {result.volatility_event && (
              <ResultCard title="VOLATILITY EVENT DETECTED" icon="📡" borderColor="border-cyan/30">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <MiniStat label="Instrument" value={result.volatility_event.instrument} />
                  <MiniStat
                    label="Price"
                    value={
                      result.volatility_event.current_price?.toLocaleString("en-US", {
                        minimumFractionDigits: 2,
                      }) || "N/A"
                    }
                  />
                  <MiniStat
                    label="Change"
                    value={`${result.volatility_event.price_change_pct > 0 ? "+" : ""}${result.volatility_event.price_change_pct}%`}
                    color={result.volatility_event.price_change_pct > 0 ? "text-profit" : "text-loss"}
                  />
                  <MiniStat
                    label="Magnitude"
                    value={result.volatility_event.magnitude.toUpperCase()}
                    color={result.volatility_event.magnitude === "high" ? "text-loss" : "text-yellow-400"}
                  />
                </div>
              </ResultCard>
            )}

            {/* Stage 2 Result: Analysis Report */}
            {result.analysis_report && (
              <ResultCard title="ANALYSIS REPORT" icon="🔍" borderColor="border-profit/30">
                <p className="text-sm text-white mb-3">{result.analysis_report.event_summary}</p>

                <div className="mb-3">
                  <h4 className="text-[11px] text-muted-foreground uppercase tracking-wider mb-2 mono-data">
                    ROOT CAUSES
                  </h4>
                  <ul className="space-y-1">
                    {result.analysis_report.root_causes.map((cause, i) => (
                      <li key={i} className="text-xs text-white/80 flex items-start gap-2">
                        <span className="text-profit mt-0.5">&bull;</span>
                        {cause}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="flex flex-wrap gap-4">
                  <MiniStat label="Sentiment" value={result.analysis_report.sentiment.toUpperCase()} />
                  <MiniStat
                    label="Score"
                    value={result.analysis_report.sentiment_score.toFixed(2)}
                    color={result.analysis_report.sentiment_score > 0 ? "text-profit" : "text-loss"}
                  />
                </div>

                {result.analysis_report.news_sources.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-[11px] text-muted-foreground uppercase tracking-wider mb-2 mono-data">
                      SOURCES
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {result.analysis_report.news_sources.map((src, i) => (
                        <span
                          key={i}
                          className="text-[10px] text-muted-foreground bg-surface px-2 py-1 rounded-sm mono-data"
                        >
                          {src.source || src.title?.slice(0, 30)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </ResultCard>
            )}

            {/* Stage 3 Result: Personalized Insight */}
            {result.personalized_insight && (
              <ResultCard title="PERSONALIZED INSIGHT" icon="📊" borderColor="border-yellow-500/30">
                <p className="text-sm text-white mb-3">
                  {result.personalized_insight.impact_summary}
                </p>

                <div className="flex flex-wrap gap-4 mb-3">
                  <MiniStat
                    label="Risk"
                    value={result.personalized_insight.risk_assessment.toUpperCase()}
                    color={
                      result.personalized_insight.risk_assessment === "high"
                        ? "text-loss"
                        : result.personalized_insight.risk_assessment === "medium"
                          ? "text-yellow-400"
                          : "text-profit"
                    }
                  />
                  <MiniStat
                    label="Affected Positions"
                    value={String(result.personalized_insight.affected_positions.length)}
                  />
                </div>

                {result.personalized_insight.suggestions.length > 0 && (
                  <div>
                    <h4 className="text-[11px] text-muted-foreground uppercase tracking-wider mb-2 mono-data">
                      SUGGESTIONS
                    </h4>
                    <ul className="space-y-1">
                      {result.personalized_insight.suggestions.map((s, i) => (
                        <li key={i} className="text-xs text-white/80 flex items-start gap-2">
                          <span className="text-yellow-400 mt-0.5">&#x25B8;</span>
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </ResultCard>
            )}

            {/* Stage 3.5 Result: Behavioral Sentinel */}
            {result.sentinel_insight && (
              <ResultCard title="BEHAVIORAL SENTINEL" icon="🧠" borderColor="border-purple-500/30">
                <div className={cn(
                  "p-4 rounded-sm border-l-2 mb-4",
                  result.sentinel_insight.risk_level === "high"
                    ? "bg-loss/10 border-loss"
                    : result.sentinel_insight.risk_level === "medium"
                    ? "bg-yellow-500/10 border-yellow-500"
                    : "bg-profit/10 border-profit"
                )}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[10px] font-semibold tracking-wider mono-data text-white uppercase">
                      PERSONALIZED WARNING
                    </span>
                    <span className={cn(
                      "text-[9px] font-bold tracking-wider px-2 py-0.5 rounded-sm mono-data",
                      result.sentinel_insight.risk_level === "high"
                        ? "bg-loss/20 text-loss"
                        : result.sentinel_insight.risk_level === "medium"
                        ? "bg-yellow-500/20 text-yellow-400"
                        : "bg-profit/20 text-profit"
                    )}>
                      {result.sentinel_insight.risk_level.toUpperCase()} RISK
                    </span>
                  </div>
                  <p className="text-xs text-white leading-relaxed">
                    {result.sentinel_insight.personalized_warning}
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-[11px] text-muted-foreground uppercase tracking-wider mb-2 mono-data">
                      BEHAVIORAL CONTEXT
                    </h4>
                    <p className="text-xs text-white/80 leading-relaxed">
                      {result.sentinel_insight.behavioral_context}
                    </p>
                  </div>
                  <div>
                    <h4 className="text-[11px] text-muted-foreground uppercase tracking-wider mb-2 mono-data">
                      PATTERN MATCH
                    </h4>
                    <p className="text-xs text-white/80 leading-relaxed">
                      {result.sentinel_insight.historical_pattern_match}
                    </p>
                  </div>
                </div>

                {result.sentinel_insight.user_stats_snapshot && (
                  <div className="mt-4 pt-3 border-t border-border flex flex-wrap gap-4">
                    <MiniStat
                      label="Total Trades"
                      value={String(result.sentinel_insight.user_stats_snapshot?.total_trades || 0)}
                    />
                    <MiniStat
                      label="Win Rate"
                      value={`${Number(result.sentinel_insight.user_stats_snapshot?.win_rate || 0).toFixed(1)}%`}
                      color={Number(result.sentinel_insight.user_stats_snapshot?.win_rate || 0) >= 50 ? "text-profit" : "text-loss"}
                    />
                    <MiniStat
                      label="Total P&L"
                      value={`$${Number(result.sentinel_insight.user_stats_snapshot?.total_pnl || 0).toFixed(2)}`}
                      color={Number(result.sentinel_insight.user_stats_snapshot?.total_pnl || 0) >= 0 ? "text-profit" : "text-loss"}
                    />
                  </div>
                )}
              </ResultCard>
            )}

            {/* Stage 4 Result: Bluesky Market Commentary */}
            {result.market_commentary && (
              <ResultCard title="BLUESKY MARKET COMMENTARY" icon="🦋" borderColor="border-cyan/30">
                <PostPreview
                  label="BLUESKY POST"
                  content={result.market_commentary.post}
                />

                <div className="flex flex-wrap gap-2 mt-4">
                  {result.market_commentary.hashtags.map((tag, i) => (
                    <span
                      key={i}
                      className="text-[11px] text-cyan bg-cyan/10 px-2 py-1 rounded-sm mono-data"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                {result.market_commentary.data_points.length > 0 && (
                  <div className="mt-3">
                    <h4 className="text-[11px] text-muted-foreground uppercase tracking-wider mb-2 mono-data">
                      DATA POINTS
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {result.market_commentary.data_points.map((dp, i) => (
                        <span
                          key={i}
                          className="text-[10px] text-muted-foreground bg-surface px-2 py-1 rounded-sm mono-data"
                        >
                          {dp}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Publish Status */}
                <div className="mt-4 pt-4 border-t border-border">
                  {result.market_commentary.published ? (
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-profit" />
                        <span className="text-xs text-profit font-semibold tracking-wider mono-data">
                          PUBLISHED TO BLUESKY
                        </span>
                      </div>
                      {result.market_commentary.bluesky_url && (
                        <a
                          href={result.market_commentary.bluesky_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[11px] text-cyan hover:underline mono-data"
                        >
                          View on Bluesky
                        </a>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-yellow-400" />
                      <span className="text-xs text-yellow-400 tracking-wider mono-data">
                        DRAFT &mdash; NOT PUBLISHED
                      </span>
                    </div>
                  )}
                </div>
              </ResultCard>
            )}

            {/* Pipeline Summary */}
            {result.status && (
              <div className="bg-card border border-border rounded-sm p-5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span
                      className={cn(
                        "text-xs font-bold tracking-wider mono-data",
                        result.status === "success" && "text-profit",
                        result.status === "partial" && "text-yellow-400",
                        result.status === "error" && "text-loss",
                        result.status === "no_event" && "text-muted"
                      )}
                    >
                      STATUS: {result.status.toUpperCase()}
                    </span>
                    {result.errors.length > 0 && (
                      <span className="text-[10px] text-muted-foreground mono-data">
                        ({result.errors.length} warning{result.errors.length > 1 ? "s" : ""})
                      </span>
                    )}
                  </div>
                  <span className="text-[10px] text-muted-foreground mono-data">
                    {result.pipeline_started_at &&
                      `Started: ${new Date(result.pipeline_started_at).toLocaleTimeString()}`}
                  </span>
                </div>
                {result.errors.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {result.errors.map((err, i) => (
                      <p key={i} className="text-[11px] text-yellow-400/80 mono-data">
                        {err}
                      </p>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* No result yet placeholder */}
        {!result && !isRunning && !error && (
          <div className="bg-card border border-border rounded-sm p-8 text-center">
            <p className="text-sm text-muted-foreground">
              Select a volatility event above or run auto scan to start the pipeline.
            </p>
            <p className="text-xs text-muted-foreground mt-2">
              The 5 agents will collaborate to detect, analyze, personalize, fuse behavioral context, and create content.
            </p>
          </div>
        )}
      </div>
    </AppShell>
  );
}

// ─── Sub-components ──────────────────────────────────────────────────

function StageCard({
  title,
  description,
  status,
  icon,
}: {
  title: string;
  description: string;
  status: StageStatus;
  icon: string;
}) {
  return (
    <div
      className={cn(
        "bg-surface border rounded-md p-5 transition-all duration-300",
        status === "idle" && "border-border",
        status === "running" && "border-cyan/50 shadow-[0_0_15px_rgba(0,212,255,0.1)]",
        status === "done" && "border-profit/50",
        status === "error" && "border-loss/50"
      )}
    >
      <div className="flex items-center gap-2.5 mb-3">
        <span className="text-lg">{icon}</span>
        <StatusDot status={status} />
      </div>
      <h4 className="text-sm font-semibold text-white tracking-wider mono-data">{title}</h4>
      <p className="text-xs text-muted-foreground mt-1.5">{description}</p>
    </div>
  );
}

function StatusDot({ status }: { status: StageStatus }) {
  return (
    <div
      className={cn(
        "w-2 h-2 rounded-full transition-all",
        status === "idle" && "bg-muted",
        status === "running" && "bg-cyan animate-pulse",
        status === "done" && "bg-profit",
        status === "error" && "bg-loss"
      )}
    />
  );
}

function ResultCard({
  title,
  icon,
  borderColor,
  children,
}: {
  title: string;
  icon: string;
  borderColor: string;
  children: React.ReactNode;
}) {
  return (
    <div className={cn("bg-card border rounded-md p-6", borderColor)}>
      <div className="flex items-center gap-2.5 mb-5">
        <span className="text-lg">{icon}</span>
        <h3 className="text-sm font-semibold tracking-wider text-muted uppercase mono-data">
          {title}
        </h3>
      </div>
      {children}
    </div>
  );
}

function MiniStat({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div>
      <span className="text-xs text-muted-foreground uppercase tracking-wider mono-data block mb-1">
        {label}
      </span>
      <span className={cn("text-base font-bold mono-data", color || "text-white")}>{value}</span>
    </div>
  );
}

function PostPreview({
  label,
  content,
}: {
  label: string;
  content: string;
}) {
  return (
    <div className="bg-surface border border-border rounded-md p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs text-muted-foreground uppercase tracking-wider mono-data">
          {label}
        </span>
        <span className="text-xs text-muted-foreground mono-data">
          {content.length}/300
        </span>
      </div>
      <p className="text-sm text-white leading-relaxed">
        {content}
      </p>
    </div>
  );
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
