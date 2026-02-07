"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import BehaviorCard from "@/components/behavior/BehaviorCard";
import DataCard from "@/components/ui/DataCard";
import DisclaimerBadge from "@/components/ui/DisclaimerBadge";
import StatusBadge from "@/components/ui/StatusBadge";
import DataSourceBadge from "@/components/ui/DataSourceBadge";
import { cn } from "@/lib/utils";
import { useTrades, useBehaviorPatterns, useSessionStats } from "@/hooks/useBehaviorData";
import api from "@/lib/api";
import type { ScenarioAnalysis } from "@/lib/api";

// ── Helpers to extract display values from nested ScenarioAnalysis ──
function getRiskLevel(sa: ScenarioAnalysis): string {
  return sa.nudge?.severity || "low";
}

function getNudgeText(sa: ScenarioAnalysis): string {
  return sa.nudge?.message || sa.analysis?.summary || "No specific nudge generated.";
}

function getAnalysisText(sa: ScenarioAnalysis): string {
  const parts: string[] = [];
  if (sa.analysis?.summary) parts.push(sa.analysis.summary);
  if (sa.nudge?.suggested_action) parts.push(`Suggested action: ${sa.nudge.suggested_action}`);
  if (sa.expected_nudge) parts.push(`Expected: ${sa.expected_nudge}`);
  return parts.join("\n\n") || "Analysis complete.";
}

function getDetectedPatterns(sa: ScenarioAnalysis): string[] {
  if (!sa.analysis?.patterns) return [];
  const patterns = sa.analysis.patterns as Record<string, { detected?: boolean }>;
  return Object.entries(patterns)
    .filter(([key, v]) => v?.detected && key !== "has_any_pattern" && key !== "highest_severity")
    .map(([k]) => k.replace(/_/g, " "));
}

type DemoScenario = {
  id: string;
  label: string;
  icon: string;
};

function scenarioIcon(name: string): string {
  if (name.includes("over")) return "⚡";
  if (name.includes("revenge")) return "🔥";
  if (name.includes("loss")) return "📉";
  if (name.includes("healthy")) return "✅";
  return "🧪";
}

export default function BehaviorPage() {
  const [activeScenario, setActiveScenario] = useState<string | null>(null);
  const [isLoadingScenario, setIsLoadingScenario] = useState(false);
  const [scenarioAnalysis, setScenarioAnalysis] = useState<ScenarioAnalysis | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [scenarios, setScenarios] = useState<DemoScenario[]>([]);
  const [isSyncingDeriv, setIsSyncingDeriv] = useState(false);
  const [derivSyncResult, setDerivSyncResult] = useState<{ trades_synced: number; total_trades: number } | null>(null);
  const [derivSyncError, setDerivSyncError] = useState<string | null>(null);

  const { data: trades, isUsingMock: tradesIsMock, isBackendOnline, refetch: refetchTrades } = useTrades();
  const { data: patterns, isUsingMock: patternsIsMock, refetch: refetchPatterns } = useBehaviorPatterns();
  const { data: stats, isUsingMock: statsIsMock, refetch: refetchStats } = useSessionStats();

  useEffect(() => {
    let cancelled = false;

    const loadScenarios = async () => {
      try {
        const resp = await api.listScenarios();
        if (cancelled) return;
        const mapped = (resp.scenarios || []).map((scenario) => ({
          id: scenario.name,
          label: scenario.description || scenario.name,
          icon: scenarioIcon(scenario.name.toLowerCase()),
        }));
        setScenarios(mapped);
      } catch {
        if (!cancelled) {
          setScenarios([]);
        }
      }
    };

    loadScenarios();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleLoadScenario = async (scenario: string) => {
    setIsLoadingScenario(true);
    setActiveScenario(scenario);
    setScenarioAnalysis(null);
    setAnalysisError(null);
    try {
      await api.loadScenario(scenario);
      // Refetch all data after loading scenario
      await Promise.all([refetchTrades(), refetchPatterns(), refetchStats()]);
    } catch {
      setAnalysisError("Scenario loading failed. Ensure demo_scenarios exists in Supabase.");
    }
    // Also run AI analysis on the scenario
    try {
      const analysis = await api.analyzeScenario(scenario);
      setScenarioAnalysis(analysis);
    } catch {
      setAnalysisError("AI analysis unavailable for this scenario.");
    }
    setIsLoadingScenario(false);
  };

  const handleSyncDeriv = async () => {
    setIsSyncingDeriv(true);
    setDerivSyncResult(null);
    setDerivSyncError(null);
    try {
      const result = await api.syncDerivTrades(undefined, 30);
      setDerivSyncResult({
        trades_synced: result.trades_synced,
        total_trades: result.total_trades,
      });
      // Refresh trade data
      await Promise.all([refetchTrades(), refetchPatterns(), refetchStats()]);
    } catch {
      setDerivSyncError("Deriv sync failed. Check DERIV_TOKEN in backend .env.");
    }
    setIsSyncingDeriv(false);
  };

  const isAnyMock = tradesIsMock || patternsIsMock || statsIsMock;

  return (
    <AppShell>
      <div className="p-6 md:p-10 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Behavioral Coach</h1>
            <p className="text-sm text-muted mono-data mt-2">
              AI-powered trading behavior analysis and pattern detection
            </p>
          </div>
          <DataSourceBadge isUsingMock={isAnyMock} isBackendOnline={isBackendOnline} />
        </div>

        {/* Session Health Overview */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-5">
          <DataCard title="Session Score" value={`${stats.sessionScore}/100`} subtitle={stats.sessionScore > 70 ? "Good" : stats.sessionScore > 40 ? "Needs improvement" : "Poor"} trend={stats.sessionScore > 50 ? "up" : "down"} glow />
          <DataCard title="Trades Today" value={String(stats.tradesToday)} subtitle={stats.tradesToday > 10 ? "Above average" : "Normal"} trend={stats.tradesToday > 10 ? "down" : "up"} />
          <DataCard title="Win Rate" value={`${stats.winRate}%`} subtitle={stats.winRate < 50 ? `Below baseline 55%` : "Above baseline"} trend={stats.winRate >= 50 ? "up" : "down"} />
          <DataCard title="Avg Hold Time" value={stats.avgHoldTime} subtitle="Per trade" trend="neutral" />
          <DataCard title="Risk Level" value={stats.riskLevel} trend={stats.riskLevel === "LOW" ? "up" : "down"} glow>
            <StatusBadge
              status={stats.riskLevel === "CRITICAL" || stats.riskLevel === "HIGH" ? "danger" : stats.riskLevel === "MEDIUM" ? "warning" : "success"}
              label={stats.riskLevel === "LOW" ? "NORMAL" : "ELEVATED"}
              pulse={stats.riskLevel === "CRITICAL"}
            />
          </DataCard>
        </div>

        {/* Demo Scenario Loader */}
        <div className="bg-card border border-border rounded-md p-6">
          <h3 className="text-sm font-semibold tracking-wider text-muted uppercase mono-data mb-5">
            LOAD DEMO SCENARIO
          </h3>
          <div className="flex flex-wrap gap-3">
            {scenarios.map((s) => (
              <button
                key={s.id}
                onClick={() => handleLoadScenario(s.id)}
                disabled={isLoadingScenario}
                className={cn(
                  "flex items-center gap-3 px-5 py-3 rounded-md border text-left transition-all",
                  activeScenario === s.id
                    ? "border-accent bg-accent/10 text-white"
                    : "border-border bg-surface text-muted hover:text-white hover:border-muted",
                  isLoadingScenario && "opacity-50 cursor-not-allowed"
                )}
              >
                <span className="text-xl">{s.icon}</span>
                <span className="text-sm font-medium mono-data tracking-wider">{s.label}</span>
              </button>
            ))}
            {scenarios.length === 0 && (
              <div className="text-xs text-muted mono-data">
                No scenarios available from demo_scenarios table.
              </div>
            )}
          </div>
          {isLoadingScenario && (
            <div className="mt-3 text-xs text-muted mono-data animate-pulse">Loading scenario from backend...</div>
          )}
        </div>

        {/* Deriv Real Trade Sync */}
        <div className="bg-card border border-border rounded-sm p-5">
          <h3 className="text-xs font-semibold tracking-wider text-muted uppercase mono-data mb-4">
            SYNC REAL TRADES FROM DERIV
          </h3>
          <div className="flex items-center gap-4">
            <button
              onClick={handleSyncDeriv}
              disabled={isSyncingDeriv}
              className={cn(
                "flex items-center gap-2 px-5 py-2.5 rounded-sm border text-left transition-all",
                "border-cyan/50 bg-cyan/10 text-white hover:bg-cyan/20",
                isSyncingDeriv && "opacity-50 cursor-not-allowed"
              )}
            >
              <span className="text-lg">🔗</span>
              <span className="text-xs font-medium mono-data tracking-wider">
                {isSyncingDeriv ? "SYNCING..." : "SYNC FROM DERIV API"}
              </span>
            </button>
            {derivSyncResult && (
              <span className="text-xs text-profit mono-data">
                {derivSyncResult.trades_synced} trades synced ({derivSyncResult.total_trades} total)
              </span>
            )}
            {derivSyncError && (
              <span className="text-xs text-loss mono-data">{derivSyncError}</span>
            )}
          </div>
          <p className="text-[10px] text-muted-foreground mt-2 mono-data">
            Pulls real trade history from your Deriv account using DERIV_TOKEN
          </p>
        </div>

        {/* AI Scenario Analysis Results */}
        {(scenarioAnalysis || analysisError) && (
          <div className="bg-card border border-border rounded-sm p-5 animate-fade-in">
            <h3 className="text-xs font-semibold tracking-wider text-muted uppercase mono-data mb-4">
              AI SCENARIO ANALYSIS
            </h3>
            {analysisError ? (
              <div className="text-xs text-warning mono-data">{analysisError}</div>
            ) : scenarioAnalysis && (() => {
              const riskLevel = getRiskLevel(scenarioAnalysis);
              const nudgeText = getNudgeText(scenarioAnalysis);
              const analysisText = getAnalysisText(scenarioAnalysis);
              const detectedPatterns = getDetectedPatterns(scenarioAnalysis);
              return (
              <div className="space-y-4">
                {/* Nudge Message - Prominent */}
                <div className={cn(
                  "p-4 rounded-sm border-l-2",
                  riskLevel === "critical" || riskLevel === "high"
                    ? "bg-loss/10 border-loss"
                    : riskLevel === "medium"
                    ? "bg-warning/10 border-warning"
                    : "bg-profit/10 border-profit"
                )}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-[10px] font-semibold tracking-wider mono-data text-white uppercase">
                      AI NUDGE
                    </span>
                    <StatusBadge
                      status={
                        riskLevel === "critical" || riskLevel === "high"
                          ? "danger"
                          : riskLevel === "medium"
                          ? "warning"
                          : "success"
                      }
                      label={riskLevel.toUpperCase()}
                      pulse={riskLevel === "critical"}
                    />
                  </div>
                  <p className="text-[11px] text-white leading-relaxed mono-data font-medium">
                    {nudgeText}
                  </p>
                </div>

                {/* Analysis Text */}
                <div>
                  <span className="text-[9px] text-muted-foreground mono-data tracking-wider uppercase block mb-1">ANALYSIS</span>
                  <p className="text-[10px] text-muted leading-relaxed mono-data whitespace-pre-wrap">
                    {analysisText}
                  </p>
                </div>

                {/* Detected Patterns */}
                {detectedPatterns.length > 0 && (
                  <div>
                    <span className="text-[9px] text-muted-foreground mono-data tracking-wider uppercase block mb-2">DETECTED PATTERNS</span>
                    <div className="flex flex-wrap gap-1.5">
                      {detectedPatterns.map((pattern, i) => (
                        <span
                          key={i}
                          className="px-2 py-1 rounded-sm text-[9px] mono-data font-medium bg-accent/10 text-accent border border-accent/30"
                        >
                          {pattern}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Suggested Action */}
                {scenarioAnalysis.nudge?.suggested_action && (
                  <div>
                    <span className="text-[9px] text-muted-foreground mono-data tracking-wider uppercase block mb-2">RECOMMENDED ACTION</span>
                    <div className="text-[10px] text-muted mono-data flex items-start gap-2">
                      <span className="text-profit mt-0.5">&#x2022;</span>
                      <span>{scenarioAnalysis.nudge.suggested_action}</span>
                    </div>
                  </div>
                )}
              </div>
              );
            })()}
          </div>
        )}

        {/* Pattern Detection Timeline */}
        <div className="bg-card border border-border rounded-md p-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <h3 className="text-sm font-semibold tracking-wider text-muted uppercase mono-data">
                PATTERN DETECTION TIMELINE
              </h3>
              <DataSourceBadge isUsingMock={patternsIsMock} />
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-loss animate-pulse" /><span className="text-[11px] text-muted mono-data">Critical</span></div>
              <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-warning" /><span className="text-[11px] text-muted mono-data">Warning</span></div>
              <div className="flex items-center gap-1.5"><div className="w-2.5 h-2.5 rounded-full bg-profit" /><span className="text-[11px] text-muted mono-data">Healthy</span></div>
            </div>
          </div>

          <div className="relative">
            <div className="absolute left-[7px] top-0 bottom-0 w-px bg-border" />
            <div className="space-y-6">
              {patterns.map((pattern, i) => (
                <div key={pattern.id} className="relative pl-8 animate-fade-in" style={{ animationDelay: `${i * 100}ms` }}>
                  <div className={cn(
                    "absolute left-0 top-2 w-4 h-4 rounded-full border-2 bg-card z-10",
                    pattern.severity === "critical" && "border-loss",
                    pattern.severity === "high" && "border-loss",
                    pattern.severity === "medium" && "border-warning",
                    pattern.severity === "low" && "border-profit"
                  )}>
                    <div className={cn(
                      "w-2 h-2 rounded-full m-auto mt-[3px]",
                      pattern.severity === "critical" && "bg-loss animate-pulse",
                      pattern.severity === "high" && "bg-loss",
                      pattern.severity === "medium" && "bg-warning",
                      pattern.severity === "low" && "bg-profit"
                    )} />
                  </div>
                  <BehaviorCard pattern={pattern} />
                </div>
              ))}
              {patterns.length === 0 && (
                <div className="pl-7 text-[11px] text-muted mono-data">
                  No elevated behavioral patterns detected from recent trade data.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Trade Log */}
        <div className="bg-card border border-border rounded-md">
          <div className="px-6 py-4 border-b border-border flex items-center justify-between">
            <h3 className="text-sm font-semibold tracking-wider text-muted uppercase mono-data">
              RECENT TRADES
            </h3>
            <DataSourceBadge isUsingMock={tradesIsMock} />
          </div>
          <div className="divide-y divide-border/30">
            {trades.map((trade) => (
              <div key={trade.id} className="grid grid-cols-12 gap-3 px-6 py-3.5 items-center text-sm mono-data">
                <div className="col-span-2 text-muted-foreground">{trade.time}</div>
                <div className="col-span-3 text-white">{trade.instrument}</div>
                <div className={cn("col-span-2", trade.direction === "BUY" ? "text-profit" : "text-loss")}>{trade.direction}</div>
                <div className="col-span-2 text-muted">{trade.amount}</div>
                <div className={cn("col-span-3 text-right font-medium", trade.pnlValue >= 0 ? "text-profit" : "text-loss")}>{trade.pnl}</div>
              </div>
            ))}
            {trades.length === 0 && (
              <div className="px-5 py-10 text-center text-xs text-muted-foreground mono-data">
                No trades yet. Load a demo scenario to see trade data.
              </div>
            )}
          </div>
        </div>

        <DisclaimerBadge variant="footer" />
      </div>
    </AppShell>
  );
}
