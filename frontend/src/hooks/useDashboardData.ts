"use client";

import { useCallback } from "react";
import { useApiWithFallback } from "./useApiWithFallback";
import api, { getApiBase } from "@/lib/api";

export interface DashboardMetrics {
  portfolioValue: number;
  totalPnl: number;
  todayPnl: number;
  todayPnlPercent: number;
  riskScore: number;
  activePatterns: number;
  patternLabels: string[];
  /** "deriv_live" when using real Deriv account balance, "database" when computed from DB trades */
  dataSource: "deriv_live" | "database" | "fallback";
  /** Deriv account login ID (e.g. "CR12345") when live */
  derivLoginId?: string;
  /** Deriv account currency when live */
  derivCurrency?: string;
}

const EMPTY_DASHBOARD: DashboardMetrics = {
  portfolioValue: 0,
  totalPnl: 0,
  todayPnl: 0,
  todayPnlPercent: 0,
  riskScore: 0,
  activePatterns: 0,
  patternLabels: [],
  dataSource: "fallback",
};

export function useDashboardMetrics() {
  const fetchMetrics = useCallback(async () => {
    // Fetch DB data in parallel (always needed for risk/patterns)
    const [profilesResp, tradesResp, metricsResp] = await Promise.all([
      api.getUserProfiles(),
      api.getTrades(),
      api.getBehavioralMetrics(),
    ]);

    const profiles = Array.isArray(profilesResp) ? profilesResp : profilesResp.results || [];
    const trades = Array.isArray(tradesResp) ? tradesResp : tradesResp.results || [];
    const metrics = Array.isArray(metricsResp) ? metricsResp : metricsResp.results || [];

    // Risk score & active patterns from latest behavioral metric
    const latestMetric = metrics[0];
    const patternFlags = latestMetric?.pattern_flags || {};
    const activePatterns = Object.entries(patternFlags)
      .filter(([, detected]) => Boolean(detected))
      .map(([name]) => name.replace(/_/g, " ").toUpperCase());

    const riskScore = latestMetric?.risk_score ?? 0;
    const patternLabels = activePatterns.length > 0 ? activePatterns : ["NONE"];

    // ── Try real Deriv balance first ──
    // getBalance() sends the user's Supabase JWT → backend resolves
    // the linked Deriv account token → calls Deriv WebSocket {balance:1}
    try {
      const balanceResp = await api.getBalance();
      if (balanceResp && typeof balanceResp.balance === "number") {
        const liveBalance = balanceResp.balance;

        // Compute P&L from synced real trades in DB (is_mock=false preferred)
        const realTrades = trades.filter((t) => !t.is_mock);
        const allTrades = realTrades.length > 0 ? realTrades : trades;
        const totalPnl = allTrades.reduce((acc, t) => acc + parseFloat(String(t.pnl || 0)), 0);

        const today = new Date().toISOString().slice(0, 10);
        const todayTrades = allTrades.filter((trade) => {
          const opened = trade.opened_at || trade.created_at;
          return opened && opened.slice(0, 10) === today;
        });
        const todayPnl = todayTrades.reduce((acc, t) => acc + parseFloat(String(t.pnl || 0)), 0);
        const todayPnlPercent = liveBalance > 0 ? (todayPnl / liveBalance) * 100 : 0;

        return {
          portfolioValue: liveBalance,
          totalPnl,
          todayPnl,
          todayPnlPercent,
          riskScore,
          activePatterns: activePatterns.length,
          patternLabels,
          dataSource: "deriv_live" as const,
          derivLoginId: balanceResp.loginid,
          derivCurrency: balanceResp.currency,
        };
      }
    } catch {
      // Deriv balance unavailable (no token, backend error, network)
      // Fall through to database calculation
    }

    // ── Fallback: compute from DB trades ──
    const totalPnl = trades.reduce((acc, t) => acc + parseFloat(String(t.pnl || 0)), 0);
    const today = new Date().toISOString().slice(0, 10);
    const todayTrades = trades.filter((trade) => {
      const opened = trade.opened_at || trade.created_at;
      return opened && opened.slice(0, 10) === today;
    });
    const todayPnl = todayTrades.reduce((acc, t) => acc + parseFloat(String(t.pnl || 0)), 0);

    // Use user-configured initial balance, or default to 10,000 (demo starting equity)
    const DEFAULT_STARTING_BALANCE = 10_000;
    const initialBalance = Number(
      profiles[0]?.preferences?.initial_balance ?? DEFAULT_STARTING_BALANCE
    );
    const portfolioValue = initialBalance + totalPnl;
    const todayPnlPercent = initialBalance > 0 ? (todayPnl / initialBalance) * 100 : 0;

    return {
      portfolioValue,
      totalPnl,
      todayPnl,
      todayPnlPercent,
      riskScore,
      activePatterns: activePatterns.length,
      patternLabels,
      dataSource: "database" as const,
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
      `${getApiBase()}/behavior/profiles/`,
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
