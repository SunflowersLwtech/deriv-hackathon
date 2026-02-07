"use client";

import { useCallback } from "react";
import { useApiWithFallback } from "./useApiWithFallback";
import api from "@/lib/api";

export interface DashboardMetrics {
  portfolioValue: number;
  todayPnl: number;
  todayPnlPercent: number;
  riskScore: number;
  activePatterns: number;
  patternLabels: string[];
}

const MOCK_DASHBOARD: DashboardMetrics = {
  portfolioValue: 10234.56,
  todayPnl: 234.56,
  todayPnlPercent: 2.34,
  riskScore: 72,
  activePatterns: 2,
  patternLabels: ["OVERTRADING", "STREAK"],
};

export function useDashboardMetrics() {
  const fetchMetrics = useCallback(async () => {
    // Aggregate from multiple endpoints
    const [profilesResp, tradesResp, metricsResp] = await Promise.all([
      api.getUserProfiles().catch(() => ({ results: [] })),
      api.getTrades().catch(() => ({ results: [] })),
      api.getBehavioralMetrics().catch(() => ({ results: [] })),
    ]);

    const profiles = Array.isArray(profilesResp) ? profilesResp : profilesResp.results || [];
    const trades = Array.isArray(tradesResp) ? tradesResp : tradesResp.results || [];
    const metrics = Array.isArray(metricsResp) ? metricsResp : metricsResp.results || [];

    if (!profiles.length && !trades.length) throw new Error("No data");

    const totalPnl = trades.reduce((acc, t) => acc + parseFloat(String(t.pnl)), 0);
    const baseValue = 10000;

    // Extract patterns from latest metric
    const latestMetric = metrics[0];
    const patternFlags = latestMetric?.pattern_flags || {};
    const activePatterns = Object.entries(patternFlags)
      .filter(([, v]) => v)
      .map(([k]) => k.replace(/_/g, " ").toUpperCase());

    const riskScore = latestMetric?.risk_score ?? 50;

    return {
      portfolioValue: baseValue + totalPnl,
      todayPnl: totalPnl,
      todayPnlPercent: baseValue > 0 ? (totalPnl / baseValue) * 100 : 0,
      riskScore,
      activePatterns: activePatterns.length,
      patternLabels: activePatterns.length > 0 ? activePatterns : ["NONE"],
    };
  }, []);

  return useApiWithFallback<DashboardMetrics>({
    fetcher: fetchMetrics,
    fallbackData: MOCK_DASHBOARD,
    pollInterval: 15000,
  });
}

// ── Backend health check ──
export function useBackendHealth() {
  const checkHealth = useCallback(async () => {
    const res = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/behavior/profiles/`,
      { method: "GET", signal: AbortSignal.timeout(3000) }
    );
    if (!res.ok) throw new Error("Backend unhealthy");
    return { online: true, latency: 0 };
  }, []);

  return useApiWithFallback({
    fetcher: checkHealth,
    fallbackData: { online: false, latency: -1 },
    pollInterval: 30000,
  });
}
