"use client";

import { useCallback } from "react";
import { useApiWithFallback } from "./useApiWithFallback";
import api from "@/lib/api";

export interface TradeDisplay {
  id: string;
  time: string;
  instrument: string;
  direction: "BUY" | "SELL";
  amount: string;
  pnl: string;
  pnlValue: number;
}

export interface BehaviorPattern {
  id: string;
  type: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  nudge: string;
  detectedAt: string;
  metrics: {
    label: string;
    value: string | number;
    threshold?: string | number;
    status: "ok" | "warning" | "danger";
  }[];
}

export interface SessionStats {
  sessionScore: number;
  tradesToday: number;
  winRate: number;
  avgHoldTime: string;
  riskLevel: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  riskScore: number;
}

const EMPTY_TRADES: TradeDisplay[] = [];
const EMPTY_PATTERNS: BehaviorPattern[] = [];
const EMPTY_SESSION_STATS: SessionStats = {
  sessionScore: 100,
  tradesToday: 0,
  winRate: 0,
  avgHoldTime: "0s",
  riskLevel: "LOW",
  riskScore: 0,
};

async function getPrimaryUserId(): Promise<string | null> {
  const profilesResp = await api.getUserProfiles();
  const profiles = Array.isArray(profilesResp) ? profilesResp : profilesResp.results || [];
  return profiles[0]?.id || null;
}

function severityToCard(severity: string): BehaviorPattern["severity"] {
  if (severity === "high") return "critical";
  if (severity === "medium") return "high";
  if (severity === "low") return "medium";
  return "low";
}

export function useTrades() {
  const fetchTrades = useCallback(async () => {
    const userId = await getPrimaryUserId();
    const tradesResp = await api.getTrades(userId || undefined);
    const trades = Array.isArray(tradesResp) ? tradesResp : tradesResp.results || [];

    return trades.map((trade): TradeDisplay => {
      const pnlNum = parseFloat(String(trade.pnl || 0));
      const opened = trade.opened_at ? new Date(trade.opened_at) : new Date(trade.created_at || Date.now());
      const notional = trade.entry_price ? Math.abs(Number(trade.entry_price)) : Math.abs(pnlNum);

      return {
        id: trade.id,
        time: opened.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" }),
        instrument: trade.instrument,
        direction: trade.direction?.toUpperCase() === "SELL" ? "SELL" : "BUY",
        amount: `$${notional.toFixed(2)}`,
        pnl: `${pnlNum >= 0 ? "+" : ""}$${pnlNum.toFixed(2)}`,
        pnlValue: pnlNum,
      };
    });
  }, []);

  return useApiWithFallback<TradeDisplay[]>({
    fetcher: fetchTrades,
    fallbackData: EMPTY_TRADES,
    pollInterval: 10000,
    cacheKey: "trades",
  });
}

export function useBehaviorPatterns() {
  const fetchPatterns = useCallback(async () => {
    const userId = await getPrimaryUserId();
    if (!userId) return [];

    const batch = await api.analyzeBatch(userId, 24);
    const patternsRaw = batch.analysis?.patterns || {};
    const nudgeText = batch.nudge?.message || "Monitor your recent behavior and maintain your process.";

    return Object.entries(patternsRaw)
      .filter(([key, value]) => {
        if (key === "has_any_pattern" || key === "highest_severity") return false;
        if (!value || typeof value !== "object") return false;
        return Boolean((value as { detected?: boolean }).detected);
      })
      .map(([patternName, value], index): BehaviorPattern => {
        const pattern = value as {
          severity?: string;
          details?: string;
          trade_count?: number;
          ratio?: number;
          consecutive_losses?: number;
          size_increase?: number;
        };

        const severity = severityToCard(pattern.severity || "low");
        const metrics = [
          pattern.trade_count != null
            ? {
                label: "TRADES",
                value: pattern.trade_count,
                status: (severity === "critical" ? "danger" : "warning") as "danger" | "warning",
              }
            : null,
          pattern.ratio != null
            ? { label: "RATIO", value: `${pattern.ratio.toFixed(2)}x`, status: "danger" as const }
            : null,
          pattern.consecutive_losses != null
            ? { label: "LOSSES", value: pattern.consecutive_losses, status: "danger" as const }
            : null,
          pattern.size_increase != null
            ? { label: "SIZE +", value: `${Number(pattern.size_increase).toFixed(1)}%`, status: "warning" as const }
            : null,
        ].filter((item): item is NonNullable<typeof item> => Boolean(item));

        return {
          id: `${patternName}-${index}`,
          type: patternName,
          severity,
          description: pattern.details || `${patternName.replace(/_/g, " ")} detected from recent trades.`,
          nudge: nudgeText,
          detectedAt: new Date().toLocaleTimeString("en-US", { hour12: false }),
          metrics,
        };
      });
  }, []);

  return useApiWithFallback<BehaviorPattern[]>({
    fetcher: fetchPatterns,
    fallbackData: EMPTY_PATTERNS,
    pollInterval: 15000,
    cacheKey: "behavior-patterns",
  });
}

export function useSessionStats() {
  const fetchStats = useCallback(async () => {
    const userId = await getPrimaryUserId();
    if (!userId) return EMPTY_SESSION_STATS;

    const [tradesResp, batch] = await Promise.all([
      api.getTrades(userId),
      api.analyzeBatch(userId, 24),
    ]);

    const trades = Array.isArray(tradesResp) ? tradesResp : tradesResp.results || [];
    const totalTrades = trades.length;
    const wins = trades.filter((trade) => parseFloat(String(trade.pnl || 0)) > 0).length;
    const winRate = totalTrades > 0 ? Math.round((wins / totalTrades) * 100) : 0;

    const avgDuration = trades.reduce((acc, trade) => acc + (trade.duration_seconds || 0), 0) / (totalTrades || 1);
    const avgHoldTime = avgDuration < 60
      ? `${Math.round(avgDuration)}s`
      : avgDuration < 3600
        ? `${(avgDuration / 60).toFixed(1)}m`
        : `${(avgDuration / 3600).toFixed(1)}h`;

    const highestSeverity = batch.analysis?.patterns?.highest_severity || "none";
    const riskMap = { none: 0, low: 25, medium: 55, high: 85 } as const;
    const riskScore = riskMap[highestSeverity as keyof typeof riskMap] ?? 0;

    const riskLevel: SessionStats["riskLevel"] =
      riskScore >= 80 ? "CRITICAL" :
      riskScore >= 50 ? "HIGH" :
      riskScore >= 25 ? "MEDIUM" :
      "LOW";

    const today = new Date().toISOString().slice(0, 10);
    const tradesToday = trades.filter((trade) => {
      const opened = trade.opened_at || trade.created_at;
      return opened && opened.slice(0, 10) === today;
    }).length;

    return {
      sessionScore: Math.max(0, 100 - riskScore),
      tradesToday,
      winRate,
      avgHoldTime,
      riskLevel,
      riskScore,
    };
  }, []);

  return useApiWithFallback<SessionStats>({
    fetcher: fetchStats,
    fallbackData: EMPTY_SESSION_STATS,
    pollInterval: 15000,
    cacheKey: "session-stats",
  });
}
