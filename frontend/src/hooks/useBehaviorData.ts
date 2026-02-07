"use client";

import { useCallback } from "react";
import { useApiWithFallback } from "./useApiWithFallback";
import api from "@/lib/api";

// ── Frontend display types ──
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

// ── Mock data ──
const MOCK_TRADES: TradeDisplay[] = [
  { id: "1", time: "14:22:30", instrument: "EUR/USD", direction: "SELL", amount: "$500", pnl: "-$23.50", pnlValue: -23.50 },
  { id: "2", time: "14:20:15", instrument: "EUR/USD", direction: "BUY", amount: "$400", pnl: "-$18.20", pnlValue: -18.20 },
  { id: "3", time: "14:18:45", instrument: "GBP/USD", direction: "SELL", amount: "$300", pnl: "+$12.30", pnlValue: 12.30 },
  { id: "4", time: "14:15:00", instrument: "EUR/USD", direction: "BUY", amount: "$200", pnl: "-$45.00", pnlValue: -45.00 },
  { id: "5", time: "14:12:30", instrument: "BTC/USD", direction: "BUY", amount: "$150", pnl: "+$8.50", pnlValue: 8.50 },
  { id: "6", time: "14:08:00", instrument: "EUR/USD", direction: "SELL", amount: "$100", pnl: "-$12.00", pnlValue: -12.00 },
];

const MOCK_PATTERNS: BehaviorPattern[] = [
  {
    id: "1", type: "overtrading", severity: "high",
    description: "You've executed 18 trades in the last 2 hours, significantly above your normal baseline of 4-6 trades per session.",
    nudge: "Take a 15-minute break. Review your last 5 trades \u2014 were they all planned?",
    detectedAt: "14:23:45",
    metrics: [
      { label: "TRADES/HR", value: 9, threshold: 3, status: "danger" },
      { label: "WIN RATE", value: "33%", threshold: "55%", status: "danger" },
      { label: "AVG HOLD", value: "2.3m", threshold: "15m", status: "warning" },
    ],
  },
  {
    id: "2", type: "loss_chasing", severity: "critical",
    description: "Position sizes have increased 3x after consecutive losses. Classic revenge trading pattern.",
    nudge: "STOP. You're doubling down after losses. Set a daily loss limit and honor it.",
    detectedAt: "14:18:12",
    metrics: [
      { label: "SIZE INCREASE", value: "3.2x", threshold: "1.5x", status: "danger" },
      { label: "CONSECUTIVE L", value: 4, threshold: 2, status: "danger" },
      { label: "DAILY P&L", value: "-$456", status: "danger" },
    ],
  },
];

const MOCK_SESSION_STATS: SessionStats = {
  sessionScore: 45,
  tradesToday: 18,
  winRate: 38,
  avgHoldTime: "2.3m",
  riskLevel: "HIGH",
  riskScore: 72,
};

// ── Hooks ──
export function useTrades() {
  const fetchTrades = useCallback(async () => {
    const response = await api.getTrades();
    // Handle both paginated and array responses
    const trades = Array.isArray(response) ? response : response.results || [];
    return trades.map((t): TradeDisplay => {
      const pnlNum = typeof t.pnl === 'string' ? parseFloat(t.pnl) : (t.pnl || 0);
      const opened = t.opened_at ? new Date(t.opened_at) : t.created_at ? new Date(t.created_at) : new Date();
      return {
        id: t.id,
        time: opened.toLocaleTimeString("en-US", { hour12: false, hour: "2-digit", minute: "2-digit", second: "2-digit" }),
        instrument: t.instrument,
        direction: (t.direction?.toUpperCase() === "SELL" ? "SELL" : "BUY") as "BUY" | "SELL",
        amount: `$${Math.abs(pnlNum * 10).toFixed(0)}`,
        pnl: `${pnlNum >= 0 ? "+" : ""}$${pnlNum.toFixed(2)}`,
        pnlValue: pnlNum,
      };
    });
  }, []);

  return useApiWithFallback<TradeDisplay[]>({
    fetcher: fetchTrades,
    fallbackData: MOCK_TRADES,
    pollInterval: 10000,
  });
}

export function useBehaviorPatterns() {
  const fetchPatterns = useCallback(async () => {
    const response = await api.getBehavioralMetrics();
    const metrics = Array.isArray(response) ? response : response.results || [];
    if (!metrics || metrics.length === 0) throw new Error("No metrics");

    return metrics.map((m): BehaviorPattern => {
      const flags = m.pattern_flags || {};
      const detectedPatterns = Object.entries(flags).filter(([, v]) => v);
      const mainPattern = detectedPatterns[0]?.[0] || "normal_session";
      const riskScore = m.risk_score ?? 0;

      let severity: BehaviorPattern["severity"] = "low";
      if (riskScore >= 70) severity = "critical";
      else if (riskScore >= 50) severity = "high";
      else if (riskScore >= 30) severity = "medium";

      return {
        id: m.id,
        type: mainPattern,
        severity,
        description: `Pattern detected with risk score ${riskScore}. ${detectedPatterns.length} pattern(s) flagged.`,
        nudge: "Consider reviewing your recent trading decisions.",
        detectedAt: new Date(m.created_at).toLocaleTimeString("en-US", { hour12: false }),
        metrics: [
          { label: "RISK SCORE", value: riskScore, threshold: 50, status: riskScore > 50 ? "danger" : riskScore > 30 ? "warning" : "ok" },
          { label: "PATTERNS", value: detectedPatterns.length, status: detectedPatterns.length > 1 ? "danger" : detectedPatterns.length > 0 ? "warning" : "ok" },
          { label: "STATE", value: m.emotional_state || "unknown", status: m.emotional_state === "distressed" ? "danger" : "ok" },
        ],
      };
    });
  }, []);

  return useApiWithFallback<BehaviorPattern[]>({
    fetcher: fetchPatterns,
    fallbackData: MOCK_PATTERNS,
    pollInterval: 15000,
  });
}

export function useSessionStats() {
  const fetchStats = useCallback(async () => {
    const profilesResp = await api.getUserProfiles();
    const profiles = Array.isArray(profilesResp) ? profilesResp : profilesResp.results || [];
    if (!profiles || profiles.length === 0) throw new Error("No profiles");

    const profile = profiles[0];
    const tradesResp = await api.getTrades(profile.id);
    const trades = Array.isArray(tradesResp) ? tradesResp : tradesResp.results || [];
    const metricsResp = await api.getBehavioralMetrics(profile.id);
    const metrics = Array.isArray(metricsResp) ? metricsResp : metricsResp.results || [];

    const totalTrades = trades.length;
    const wins = trades.filter((t) => parseFloat(String(t.pnl)) > 0).length;
    const winRate = totalTrades > 0 ? Math.round((wins / totalTrades) * 100) : 0;

    const latestMetric = metrics[0];
    const riskScore = latestMetric?.risk_score ?? 50;

    let riskLevel: SessionStats["riskLevel"] = "LOW";
    if (riskScore >= 70) riskLevel = "CRITICAL";
    else if (riskScore >= 50) riskLevel = "HIGH";
    else if (riskScore >= 30) riskLevel = "MEDIUM";

    const avgDuration = trades.reduce((acc, t) => {
      return acc + (t.duration_seconds || 0);
    }, 0) / (totalTrades || 1);

    const holdTimeStr = avgDuration < 60 ? `${Math.round(avgDuration)}s`
      : avgDuration < 3600 ? `${(avgDuration / 60).toFixed(1)}m`
      : `${(avgDuration / 3600).toFixed(1)}h`;

    return {
      sessionScore: Math.max(0, 100 - riskScore),
      tradesToday: totalTrades,
      winRate,
      avgHoldTime: holdTimeStr,
      riskLevel,
      riskScore,
    };
  }, []);

  return useApiWithFallback<SessionStats>({
    fetcher: fetchStats,
    fallbackData: MOCK_SESSION_STATS,
    pollInterval: 15000,
  });
}
