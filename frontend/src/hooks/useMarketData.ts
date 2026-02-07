"use client";

import { useCallback, useState, useEffect } from "react";
import { useApiWithFallback } from "./useApiWithFallback";
import api from "@/lib/api";

// ── Ticker data with simulated live updates ──
export interface TickerItem {
  symbol: string;
  price: number;
  change: number;
  icon: string;
}

const MOCK_TICKERS: TickerItem[] = [
  { symbol: "EUR/USD", price: 1.0842, change: 0.12, icon: "\ud83d\udcb6" },
  { symbol: "GBP/USD", price: 1.2645, change: -0.08, icon: "\ud83d\udcb7" },
  { symbol: "USD/JPY", price: 149.32, change: 0.24, icon: "\ud83d\udcb4" },
  { symbol: "BTC/USD", price: 97523.45, change: 2.34, icon: "\u20bf" },
  { symbol: "ETH/USD", price: 3245.67, change: -1.12, icon: "\u039e" },
  { symbol: "Volatility 75", price: 452891.23, change: 0.56, icon: "\ud83d\udcca" },
  { symbol: "Volatility 100", price: 1823.45, change: -0.34, icon: "\ud83d\udcc8" },
  { symbol: "GOLD", price: 2845.30, change: 0.89, icon: "\ud83e\udd47" },
];

/** Simulates small random price movements */
function simulatePriceUpdate(tickers: TickerItem[]): TickerItem[] {
  return tickers.map((t) => {
    const variance = t.price * 0.0002;
    const delta = (Math.random() - 0.5) * 2 * variance;
    return {
      ...t,
      price: Math.max(0, t.price + delta),
      change: t.change + (Math.random() - 0.5) * 0.02,
    };
  });
}

export function useTickerData(updateInterval = 2000) {
  const [tickers, setTickers] = useState<TickerItem[]>(MOCK_TICKERS);
  const [isUsingMock, setIsUsingMock] = useState(true);

  // Try to fetch from backend on mount
  useEffect(() => {
    let cancelled = false;
    async function tryFetchPrices() {
      try {
        const instruments = ["EUR/USD", "GBP/USD", "USD/JPY", "BTC/USD", "ETH/USD"];
        const pricePromises = instruments.map((inst) =>
          api.getLivePrice(inst).catch(() => null)
        );
        const results = await Promise.all(pricePromises);
        const valid = results.filter((r) => r && r.price !== null);
        if (!cancelled && valid.length > 0) {
          const iconMap: Record<string, string> = {
            "EUR/USD": "\ud83d\udcb6", "GBP/USD": "\ud83d\udcb7", "USD/JPY": "\ud83d\udcb4",
            "BTC/USD": "\u20bf", "ETH/USD": "\u039e",
          };
          const liveTickers = valid.map((p) => ({
            symbol: p!.instrument,
            price: p!.price!,
            change: 0, // Deriv single tick doesn't include change
            icon: iconMap[p!.instrument] || "\ud83d\udcca",
          }));
          // Merge live tickers with remaining mock ones
          const liveSymbols = new Set(liveTickers.map((t) => t.symbol));
          const remaining = MOCK_TICKERS.filter((t) => !liveSymbols.has(t.symbol));
          setTickers([...liveTickers, ...remaining]);
          setIsUsingMock(false);
        }
      } catch {
        // Keep mock data
      }
    }
    tryFetchPrices();
    return () => { cancelled = true; };
  }, []);

  // Simulate updates (works for both mock and real data as continuous feed)
  useEffect(() => {
    const interval = setInterval(() => {
      setTickers((prev) => simulatePriceUpdate(prev));
    }, updateInterval);
    return () => clearInterval(interval);
  }, [updateInterval]);

  return { tickers, isUsingMock };
}

// ── Market Overview data ──
export interface MarketOverviewItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: string;
  icon: string;
}

const MOCK_MARKET_DATA: MarketOverviewItem[] = [
  { symbol: "EUR/USD", name: "Euro / US Dollar", price: 1.0842, change: 0.0012, changePercent: 0.11, volume: "5.2B", icon: "\ud83d\udcb6" },
  { symbol: "GBP/USD", name: "British Pound / US Dollar", price: 1.2645, change: -0.0008, changePercent: -0.06, volume: "3.1B", icon: "\ud83d\udcb7" },
  { symbol: "USD/JPY", name: "US Dollar / Japanese Yen", price: 149.32, change: 0.45, changePercent: 0.30, volume: "4.8B", icon: "\ud83d\udcb4" },
  { symbol: "BTC/USD", name: "Bitcoin / US Dollar", price: 97523.45, change: 2345.67, changePercent: 2.46, volume: "28.4B", icon: "\u20bf" },
  { symbol: "ETH/USD", name: "Ethereum / US Dollar", price: 3245.67, change: -45.23, changePercent: -1.37, volume: "12.1B", icon: "\u039e" },
  { symbol: "V75", name: "Volatility 75 Index", price: 452891.23, change: 1234.56, changePercent: 0.27, volume: "N/A", icon: "\ud83d\udcca" },
  { symbol: "GOLD", name: "Gold Spot", price: 2845.30, change: 12.45, changePercent: 0.44, volume: "182B", icon: "\ud83e\udd47" },
  { symbol: "V100", name: "Volatility 100 Index", price: 1823.45, change: -5.67, changePercent: -0.31, volume: "N/A", icon: "\ud83d\udcc8" },
];

export function useMarketOverview() {
  const fetchInsights = useCallback(async () => {
    const response = await api.getMarketInsights();
    const insights = Array.isArray(response) ? response : response.results || [];
    if (insights && insights.length > 0) {
      return insights.map((insight) => ({
        symbol: insight.instrument,
        name: insight.instrument,
        price: 0,
        change: 0,
        changePercent: insight.confidence ? (insight.confidence - 0.5) * 10 : 0,
        volume: "N/A",
        icon: "\ud83d\udcca",
      }));
    }
    throw new Error("No insights available");
  }, []);

  return useApiWithFallback<MarketOverviewItem[]>({
    fetcher: fetchInsights,
    fallbackData: MOCK_MARKET_DATA,
    pollInterval: 30000,
  });
}

// ── Market Insights (AI analysis) ──
export interface InsightItem {
  id: string;
  instrument: string;
  type: string;
  content: string;
  sentiment: number | null;
  time: string;
}

const MOCK_INSIGHTS: InsightItem[] = [
  { id: "1", instrument: "EUR/USD", type: "technical", content: "EUR/USD showing bearish divergence on 4H RSI. Support at 1.0820.", time: "2m ago", sentiment: -0.3 },
  { id: "2", instrument: "BTC/USD", type: "news", content: "BTC/USD crossed above 50-day SMA. Volume increasing.", time: "8m ago", sentiment: 0.6 },
  { id: "3", instrument: "GOLD", type: "sentiment", content: "Gold sentiment turning bullish amid geopolitical uncertainty.", time: "15m ago", sentiment: 0.4 },
];

export function useMarketInsights() {
  const fetchInsights = useCallback(async () => {
    const response = await api.getMarketInsights();
    const raw = Array.isArray(response) ? response : response.results || [];
    return raw.map((r) => ({
      id: r.id,
      instrument: r.instrument,
      type: r.insight_type,
      content: r.content,
      sentiment: r.confidence ?? null,
      time: new Date(r.created_at).toLocaleTimeString(),
    }));
  }, []);

  return useApiWithFallback<InsightItem[]>({
    fetcher: fetchInsights,
    fallbackData: MOCK_INSIGHTS,
    pollInterval: 60000,
  });
}
