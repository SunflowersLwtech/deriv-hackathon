"use client";

import { useState } from "react";
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

const scenarios = [
  { id: "overtrading", label: "Overtrading", icon: "⚡" },
  { id: "revenge_trading", label: "Revenge Trading", icon: "🔥" },
  { id: "loss_chasing", label: "Loss Chasing", icon: "📉" },
  { id: "healthy_session", label: "Healthy Session", icon: "✅" },
];

export default function BehaviorPage() {
  const [activeScenario, setActiveScenario] = useState<string | null>(null);
  const [isLoadingScenario, setIsLoadingScenario] = useState(false);
  const [scenarioAnalysis, setScenarioAnalysis] = useState<ScenarioAnalysis | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const { data: trades, isUsingMock: tradesIsMock, isBackendOnline, refetch: refetchTrades } = useTrades();
  const { data: patterns, isUsingMock: patternsIsMock, refetch: refetchPatterns } = useBehaviorPatterns();
  const { data: stats, isUsingMock: statsIsMock, refetch: refetchStats } = useSessionStats();

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
      // Scenario load failed — keep mock data
    }
    // Also run AI analysis on the scenario
    try {
      const analysis = await api.analyzeScenario(scenario);
      setScenarioAnalysis(analysis);
    } catch {
      setAnalysisError("AI analysis unavailable. Showing pattern data from backend.");
    }
    setIsLoadingScenario(false);
  };

  const isAnyMock = tradesIsMock || patternsIsMock || statsIsMock;

  return (
    <AppShell>
      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">Behavioral Coach</h1>
            <p className="text-[11px] text-muted mono-data mt-0.5">
              AI-powered trading behavior analysis and pattern detection
            </p>
          </div>
          <DataSourceBadge isUsingMock={isAnyMock} isBackendOnline={isBackendOnline} />
        </div>

        {/* Session Health Overview */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
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
        <div className="bg-card border border-border rounded-sm p-4">
          <h3 className="text-[10px] font-semibold tracking-wider text-muted uppercase mono-data mb-3">
            LOAD DEMO SCENARIO
          </h3>
          <div className="flex flex-wrap gap-2">
            {scenarios.map((s) => (
              <button
                key={s.id}
                onClick={() => handleLoadScenario(s.id)}
                disabled={isLoadingScenario}
                className={cn(
                  "flex items-center gap-2 px-3 py-2 rounded-sm border text-left transition-all",
                  activeScenario === s.id
                    ? "border-accent bg-accent/10 text-white"
                    : "border-border bg-surface text-muted hover:text-white hover:border-muted",
                  isLoadingScenario && "opacity-50 cursor-not-allowed"
                )}
              >
                <span>{s.icon}</span>
                <span className="text-[10px] font-medium mono-data tracking-wider">{s.label}</span>
              </button>
            ))}
          </div>
          {isLoadingScenario && (
            <div className="mt-2 text-[10px] text-muted mono-data animate-pulse">Loading scenario from backend...</div>
          )}
        </div>

        {/* AI Scenario Analysis Results */}
        {(scenarioAnalysis || analysisError) && (
          <div className="bg-card border border-border rounded-sm p-4 animate-fade-in">
            <h3 className="text-[10px] font-semibold tracking-wider text-muted uppercase mono-data mb-3">
              AI SCENARIO ANALYSIS
            </h3>
            {analysisError ? (
              <div className="text-[10px] text-warning mono-data">{analysisError}</div>
            ) : scenarioAnalysis && (() => {
              const riskLevel = getRiskLevel(scenarioAnalysis);
              const nudgeText = getNudgeText(scenarioAnalysis);
              const analysisText = getAnalysisText(scenarioAnalysis);
              const detectedPatterns = getDetectedPatterns(scenarioAnalysis);
              return (
              <div className="space-y-4">
                {/* Nudge Message - Prominent */}
                <div className={cn(
                  "p-3 rounded-sm border-l-2",
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
        <div className="bg-card border border-border rounded-sm p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <h3 className="text-[10px] font-semibold tracking-wider text-muted uppercase mono-data">
                PATTERN DETECTION TIMELINE
              </h3>
              <DataSourceBadge isUsingMock={patternsIsMock} />
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-loss animate-pulse" /><span className="text-[9px] text-muted mono-data">Critical</span></div>
              <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-warning" /><span className="text-[9px] text-muted mono-data">Warning</span></div>
              <div className="flex items-center gap-1"><div className="w-2 h-2 rounded-full bg-profit" /><span className="text-[9px] text-muted mono-data">Healthy</span></div>
            </div>
          </div>

          <div className="relative">
            <div className="absolute left-[7px] top-0 bottom-0 w-px bg-border" />
            <div className="space-y-4">
              {patterns.map((pattern, i) => (
                <div key={pattern.id} className="relative pl-6 animate-fade-in" style={{ animationDelay: `${i * 100}ms` }}>
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
            </div>
          </div>
        </div>

        {/* Trade Log */}
        <div className="bg-card border border-border rounded-sm">
          <div className="px-4 py-3 border-b border-border flex items-center justify-between">
            <h3 className="text-[10px] font-semibold tracking-wider text-muted uppercase mono-data">
              RECENT TRADES
            </h3>
            <DataSourceBadge isUsingMock={tradesIsMock} />
          </div>
          <div className="divide-y divide-border/30">
            {trades.map((trade) => (
              <div key={trade.id} className="grid grid-cols-12 gap-2 px-4 py-2.5 items-center text-[10px] mono-data">
                <div className="col-span-2 text-muted-foreground">{trade.time}</div>
                <div className="col-span-3 text-white">{trade.instrument}</div>
                <div className={cn("col-span-2", trade.direction === "BUY" ? "text-profit" : "text-loss")}>{trade.direction}</div>
                <div className="col-span-2 text-muted">{trade.amount}</div>
                <div className={cn("col-span-3 text-right font-medium", trade.pnlValue >= 0 ? "text-profit" : "text-loss")}>{trade.pnl}</div>
              </div>
            ))}
            {trades.length === 0 && (
              <div className="px-4 py-8 text-center text-[10px] text-muted-foreground mono-data">
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
