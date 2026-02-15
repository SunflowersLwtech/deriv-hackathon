"use client";

import { Fragment, useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { cn } from "@/lib/utils";
import {
  usePipelineContext,
  DEMO_EVENTS,
  type StageStatus,
} from "@/providers/PipelineProvider";

const STAGE_DEFS = [
  { key: "monitor" as const, title: "1. MONITOR", desc: "Detect volatility via Redis", icon: "📡" },
  { key: "analyst" as const, title: "2. ANALYST", desc: "Root cause analysis", icon: "🔍" },
  { key: "advisor" as const, title: "3. ADVISOR", desc: "Portfolio interpretation", icon: "📊" },
  { key: "sentinel" as const, title: "4. SENTINEL", desc: "Behavior + market fusion", icon: "🧠" },
  { key: "content" as const, title: "5. CONTENT", desc: "Bluesky commentary", icon: "🦋" },
];

export default function PipelinePage() {
  const { stages, result, isRunning, error, mode, setMode, runPipeline, runAutoScan } =
    usePipelineContext();

  // Local elapsed timer — purely presentational
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (!isRunning) return;
    setElapsed(0);
    const start = Date.now();
    const interval = setInterval(() => setElapsed(Math.floor((Date.now() - start) / 1000)), 1000);
    return () => clearInterval(interval);
  }, [isRunning]);

  const completedCount = Object.values(stages).filter((s) => s === "done").length;

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

        {/* Pipeline Stages Visualisation */}
        <div className="bg-card border border-border rounded-md p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <h3 className="text-sm font-semibold tracking-wider text-muted uppercase mono-data">
                PIPELINE STATUS
              </h3>
              {isRunning && (
                <div className="flex items-center gap-2">
                  <div className="live-dot" />
                  <span className="text-[11px] text-profit mono-data">PROCESSING</span>
                  <span className="text-[11px] text-muted-foreground mono-data">{elapsed}s</span>
                </div>
              )}
            </div>
            {(isRunning || completedCount > 0) && (
              <span className="text-[11px] text-muted-foreground mono-data">
                {completedCount}/5 STAGES
              </span>
            )}
          </div>

          {/* Desktop: flex layout with SVG connectors */}
          <div className="hidden md:flex items-stretch gap-0">
            {STAGE_DEFS.map((stage, i) => (
              <Fragment key={stage.key}>
                <div className="flex-1 min-w-0">
                  <StageCard
                    title={stage.title}
                    description={stage.desc}
                    status={stages[stage.key]}
                    icon={stage.icon}
                  />
                </div>
                {i < 4 && (
                  <StageConnector
                    fromStatus={stages[STAGE_DEFS[i].key]}
                    toStatus={stages[STAGE_DEFS[i + 1].key]}
                  />
                )}
              </Fragment>
            ))}
          </div>

          {/* Mobile: vertical stack with connectors */}
          <div className="md:hidden space-y-2">
            {STAGE_DEFS.map((stage, i) => (
              <Fragment key={stage.key}>
                <StageCard
                  title={stage.title}
                  description={stage.desc}
                  status={stages[stage.key]}
                  icon={stage.icon}
                />
                {i < 4 && (
                  <div className="flex justify-center py-0.5">
                    <svg width="16" height="18" viewBox="0 0 16 18">
                      <line
                        x1="8" y1="0" x2="8" y2="12"
                        strokeWidth="2"
                        strokeDasharray="4 3"
                        className={cn(
                          "transition-colors duration-500",
                          stages[STAGE_DEFS[i].key] === "done" ? "stroke-profit" : "stroke-border"
                        )}
                      />
                      <polygon
                        points="4,12 12,12 8,18"
                        className={cn(
                          "transition-colors duration-500",
                          stages[STAGE_DEFS[i].key] === "done" ? "fill-profit" : "fill-border"
                        )}
                      />
                    </svg>
                  </div>
                )}
              </Fragment>
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

        {/* Results — staggered reveal animation */}
        {result && (
          <div className="space-y-5">
            {/* Stage 1 Result: Volatility Event */}
            {result.volatility_event && (
              <div className="result-card-reveal" style={{ animationDelay: "0ms" }}>
                <ResultCard title="VOLATILITY EVENT DETECTED" icon="📡" borderColor="border-cyan/30">
                  {result.volatility_event.demo_mode && (
                    <div className="mb-4 flex items-center gap-2 bg-yellow-500/10 border border-yellow-500/30 rounded-sm px-3 py-2">
                      <span className="text-yellow-400 text-xs">&#x26A0;</span>
                      <span className="text-[11px] text-yellow-400 mono-data tracking-wider">
                        DEMO MODE — No real volatility detected. Showing simulated analysis.
                      </span>
                    </div>
                  )}
                  {/* Multi-timeframe price row */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
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
                      label="1h Change"
                      value={`${Number(result.volatility_event.raw_data?.change_1h ?? 0) > 0 ? "+" : ""}${Number(result.volatility_event.raw_data?.change_1h ?? 0).toFixed(2)}%`}
                      color={Number(result.volatility_event.raw_data?.change_1h ?? 0) > 0 ? "text-profit" : Number(result.volatility_event.raw_data?.change_1h ?? 0) < 0 ? "text-loss" : "text-white"}
                    />
                    <MiniStat
                      label="24h Change"
                      value={`${result.volatility_event.price_change_pct > 0 ? "+" : ""}${result.volatility_event.price_change_pct}%`}
                      color={result.volatility_event.price_change_pct > 0 ? "text-profit" : "text-loss"}
                    />
                    <MiniStat
                      label="7d Change"
                      value={`${Number(result.volatility_event.raw_data?.change_7d ?? 0) > 0 ? "+" : ""}${Number(result.volatility_event.raw_data?.change_7d ?? 0).toFixed(2)}%`}
                      color={Number(result.volatility_event.raw_data?.change_7d ?? 0) > 0 ? "text-profit" : Number(result.volatility_event.raw_data?.change_7d ?? 0) < 0 ? "text-loss" : "text-white"}
                    />
                  </div>

                  {/* Market context row */}
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-4">
                    <MiniStat
                      label="Magnitude"
                      value={result.volatility_event.magnitude.toUpperCase()}
                      color={
                        result.volatility_event.magnitude === "high"
                          ? "text-loss"
                          : result.volatility_event.magnitude === "medium"
                            ? "text-yellow-400"
                            : "text-muted-foreground"
                      }
                    />
                    <MiniStat
                      label="ATR Ratio"
                      value={`${Number(result.volatility_event.raw_data?.atr_ratio ?? 0).toFixed(1)}x`}
                      color={
                        Number(result.volatility_event.raw_data?.atr_ratio ?? 0) >= 2.0
                          ? "text-loss"
                          : Number(result.volatility_event.raw_data?.atr_ratio ?? 0) >= 1.0
                            ? "text-yellow-400"
                            : "text-muted-foreground"
                      }
                    />
                    <MiniStat
                      label="RSI(14)"
                      value={String(Number(result.volatility_event.raw_data?.rsi_14 ?? 50).toFixed(1))}
                      color={
                        Number(result.volatility_event.raw_data?.rsi_14 ?? 50) < 30
                          ? "text-profit"
                          : Number(result.volatility_event.raw_data?.rsi_14 ?? 50) > 70
                            ? "text-loss"
                            : "text-white"
                      }
                    />
                    <div className="md:col-span-2 md:text-right">
                      <MiniStat
                        label="Trend"
                        value={String(result.volatility_event.raw_data?.trend ?? "neutral").toUpperCase()}
                        color={
                          result.volatility_event.raw_data?.trend === "bullish"
                            ? "text-profit"
                            : result.volatility_event.raw_data?.trend === "bearish"
                              ? "text-loss"
                              : "text-white"
                        }
                      />
                    </div>
                  </div>
                </ResultCard>
              </div>
            )}

            {/* Stage 2 Result: Analysis Report */}
            {result.analysis_report && (
              <div className="result-card-reveal" style={{ animationDelay: "150ms" }}>
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
              </div>
            )}

            {/* Stage 3 Result: Personalized Insight */}
            {result.personalized_insight && (
              <div className="result-card-reveal" style={{ animationDelay: "300ms" }}>
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
              </div>
            )}

            {/* Stage 4 Result: Behavioral Sentinel */}
            {result.sentinel_insight && (
              <div className="result-card-reveal" style={{ animationDelay: "450ms" }}>
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
                    <div className="mt-4 pt-3 border-t border-border">
                      <h4 className="text-[11px] text-muted-foreground uppercase tracking-wider mb-3 mono-data">
                        TRADING STATS (LAST {Number(result.sentinel_insight.user_stats_snapshot?.period_days ?? 30)} DAYS)
                      </h4>
                      <div className="flex flex-wrap gap-4">
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
                    </div>
                  )}
                </ResultCard>
              </div>
            )}

            {/* Stage 5 Result: Bluesky Market Commentary */}
            {result.market_commentary && (
              <div className="result-card-reveal" style={{ animationDelay: "600ms" }}>
                <ResultCard title="BLUESKY MARKET COMMENTARY" icon="🦋" borderColor="border-cyan/30">
                  <PostPreview content={result.market_commentary.post} />

                  {/* Image Preview */}
                  {result.market_commentary.image_url && (
                    <div className="mt-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs text-muted-foreground uppercase tracking-wider mono-data">
                          ATTACHED IMAGE
                        </span>
                        {result.market_commentary.image_type && (
                          <span className="text-[10px] text-cyan bg-cyan/10 px-2 py-0.5 rounded-sm mono-data">
                            {result.market_commentary.image_type}
                          </span>
                        )}
                      </div>
                      <img
                        src={result.market_commentary.image_url}
                        alt="Market commentary image"
                        className="w-full rounded-md border border-border object-cover max-h-96"
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = "none";
                        }}
                      />
                    </div>
                  )}

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
              </div>
            )}

            {/* Pipeline Summary */}
            {result.status && (
              <div className="result-card-reveal bg-card border border-border rounded-sm p-5" style={{ animationDelay: "750ms" }}>
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
                  <div className="flex items-center gap-4">
                    {result.pipeline_started_at && result.pipeline_finished_at && (
                      <span className="text-[10px] text-muted-foreground mono-data">
                        Duration: {Math.max(1, Math.ceil((new Date(result.pipeline_finished_at).getTime() - new Date(result.pipeline_started_at).getTime()) / 1000))}s
                      </span>
                    )}
                    {result.pipeline_started_at && (
                      <span className="text-[10px] text-muted-foreground mono-data">
                        {new Date(result.pipeline_started_at).toLocaleTimeString()}
                      </span>
                    )}
                  </div>
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

        {/* Empty state — engaging placeholder */}
        {!result && !isRunning && !error && (
          <div className="bg-card border border-border rounded-md p-10 text-center">
            {/* Mini pipeline diagram */}
            <div className="flex items-center justify-center gap-2 md:gap-3 mb-6">
              {STAGE_DEFS.map((stage, i) => (
                <Fragment key={stage.key}>
                  <div
                    className="w-9 h-9 md:w-11 md:h-11 rounded-lg bg-surface border border-border flex items-center justify-center text-base md:text-lg animate-fade-in"
                    style={{ animationDelay: `${i * 100}ms` }}
                  >
                    {stage.icon}
                  </div>
                  {i < 4 && (
                    <svg width="20" height="12" viewBox="0 0 20 12" className="shrink-0 animate-fade-in" style={{ animationDelay: `${i * 100 + 50}ms` }}>
                      <line x1="0" y1="6" x2="12" y2="6" stroke="currentColor" strokeWidth="1.5" strokeDasharray="3 2" className="text-border" />
                      <polygon points="12,3 20,6 12,9" className="fill-border" />
                    </svg>
                  )}
                </Fragment>
              ))}
            </div>

            <h3 className="text-base font-semibold text-white tracking-wider mono-data mb-2">
              READY TO ANALYZE
            </h3>
            <p className="text-sm text-muted-foreground max-w-lg mx-auto">
              Select a volatility event above or run auto scan to activate the 5-agent pipeline.
            </p>
            <p className="text-xs text-muted-foreground mt-2 max-w-md mx-auto">
              Each agent collaborates in sequence: detect anomalies, analyze root causes,
              personalize insights, fuse behavioral context, and generate social content.
            </p>
          </div>
        )}

        {/* Running state skeleton — show when running but no result yet */}
        {isRunning && !result && (
          <div className="space-y-4">
            {[0, 1, 2].map((i) => (
              <div key={i} className="bg-card border border-border rounded-md p-6 animate-shimmer" style={{ animationDelay: `${i * 200}ms` }}>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-6 h-6 rounded bg-surface" />
                  <div className="h-4 w-40 rounded bg-surface" />
                </div>
                <div className="space-y-2">
                  <div className="h-3 w-full rounded bg-surface" />
                  <div className="h-3 w-3/4 rounded bg-surface" />
                  <div className="h-3 w-1/2 rounded bg-surface" />
                </div>
              </div>
            ))}
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
        status === "running" && "border-cyan/50 pipeline-stage-running",
        status === "done" && "border-profit/50",
        status === "error" && "border-loss/50"
      )}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-lg">{icon}</span>
        <StatusBadge status={status} />
      </div>
      <h4 className="text-sm font-semibold text-white tracking-wider mono-data">{title}</h4>
      <p className="text-xs text-muted-foreground mt-1.5">{description}</p>
    </div>
  );
}

function StatusBadge({ status }: { status: StageStatus }) {
  const config: Record<StageStatus, { label: string; color: string }> = {
    idle: { label: "IDLE", color: "text-muted-foreground bg-muted/10" },
    running: { label: "RUNNING", color: "text-cyan bg-cyan/10" },
    done: { label: "DONE", color: "text-profit bg-profit/10" },
    error: { label: "ERROR", color: "text-loss bg-loss/10" },
  };
  const { label, color } = config[status];
  return (
    <div className="flex items-center gap-1.5">
      <StatusDot status={status} />
      <span className={cn("text-[9px] font-bold tracking-wider px-1.5 py-0.5 rounded-sm mono-data", color)}>
        {label}
      </span>
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

function StageConnector({
  fromStatus,
  toStatus,
}: {
  fromStatus: StageStatus;
  toStatus: StageStatus;
}) {
  const isDone = fromStatus === "done" && (toStatus === "done" || toStatus === "error");
  const isFlowing = fromStatus === "done" && toStatus === "running";

  return (
    <div className="flex items-center justify-center w-8 shrink-0">
      <svg width="24" height="16" viewBox="0 0 24 16" className="overflow-visible">
        <line
          x1="0" y1="8" x2="16" y2="8"
          strokeWidth="2"
          strokeDasharray={isDone ? "none" : "6 3"}
          className={cn(
            "transition-colors duration-500",
            isDone ? "stroke-profit" : isFlowing ? "stroke-cyan" : "stroke-border"
          )}
          style={isFlowing ? { animation: "pipeline-flow 0.6s linear infinite" } : undefined}
        />
        <polygon
          points="16,4 24,8 16,12"
          className={cn(
            "transition-colors duration-500",
            isDone ? "fill-profit" : isFlowing ? "fill-cyan" : "fill-border"
          )}
        />
      </svg>
    </div>
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
      <div className="grid grid-cols-[1.5rem,1fr] gap-x-3 gap-y-5">
        <div className="flex h-6 w-6 items-center justify-center text-lg leading-none">
          {icon}
        </div>
        <h3 className="self-center text-sm font-semibold tracking-wider text-muted uppercase mono-data">
          {title}
        </h3>
        <div className="col-start-2">{children}</div>
      </div>
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

function PostPreview({ content }: { content: string }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-5">
      {/* Bluesky-style header */}
      <div className="flex items-center gap-3 mb-3">
        <div className="w-10 h-10 rounded-full bg-cyan/20 flex items-center justify-center shrink-0">
          <span className="text-cyan text-xs font-bold mono-data">TIQ</span>
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-white">TradeIQ</span>
            <span className="text-[11px] text-cyan mono-data truncate">@tradeiq.bsky.social</span>
          </div>
          <span className="text-[11px] text-muted-foreground mono-data">just now</span>
        </div>
      </div>
      {/* Post content */}
      <p className="text-sm text-white leading-relaxed">{content}</p>
      {/* Character count */}
      <div className="flex justify-end mt-3 pt-3 border-t border-border">
        <span className="text-[11px] text-muted-foreground mono-data">{content.length}/300</span>
      </div>
    </div>
  );
}
