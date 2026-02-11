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

const EMPTY_DASHBOARD: DashboardMetrics = {
  portfolioValue: 0,
  todayPnl: 0,
  todayPnlPercent: 0,
  riskScore: 0,
  activePatterns: 0,
  patternLabels: [],
};

export function useDashboardMetrics() {
  const fetchMetrics = useCallback(async () => {
    const [profilesResp, tradesResp, metricsResp] = await Promise.all([
      api.getUserProfiles(),
      api.getTrades(),
      api.getBehavioralMetrics(),
    ]);

    const profiles = Array.isArray(profilesResp) ? profilesResp : profilesResp.results || [];
    const trades = Array.isArray(tradesResp) ? tradesResp : tradesResp.results || [];
    const metrics = Array.isArray(metricsResp) ? metricsResp : metricsResp.results || [];

    const totalPnl = trades.reduce((acc, t) => acc + parseFloat(String(t.pnl || 0)), 0);
    const today = new Date().toISOString().slice(0, 10);
    const todayTrades = trades.filter((trade) => {
      const opened = trade.opened_at || trade.created_at;
      return opened && opened.slice(0, 10) === today;
    });
    const todayPnl = todayTrades.reduce((acc, t) => acc + parseFloat(String(t.pnl || 0)), 0);

    const initialBalance = Number(profiles[0]?.preferences?.initial_balance ?? 0);
    const portfolioValue = initialBalance + totalPnl;
    const todayPnlPercent = initialBalance > 0 ? (todayPnl / initialBalance) * 100 : 0;

    const latestMetric = metrics[0];
    const patternFlags = latestMetric?.pattern_flags || {};
    const activePatterns = Object.entries(patternFlags)
      .filter(([, detected]) => Boolean(detected))
      .map(([name]) => name.replace(/_/g, " ").toUpperCase());

    return {
      portfolioValue,
      todayPnl,
      todayPnlPercent,
      riskScore: latestMetric?.risk_score ?? 0,
      activePatterns: activePatterns.length,
      patternLabels: activePatterns.length > 0 ? activePatterns : ["NONE"],
    };
  }, []);

  return useApiWithFallback<DashboardMetrics>({
    fetcher: fetchMetrics,
    fallbackData: EMPTY_DASHBOARD,
    pollInterval: 15000,
    cacheKey: "dashboard-metrics",
  });
}

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
