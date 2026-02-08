"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useApiWithFallback } from "./useApiWithFallback";
import api from "@/lib/api";
import type { EconomicEvent, EconomicCalendarResponse, TopHeadlinesResponse } from "@/lib/api";

export interface TickerItem {
  symbol: string;
  price: number;
  change: number;
  icon: string;
}

export interface MarketOverviewItem {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: string;
  icon: string;
}

export interface InsightItem {
  id: string;
  instrument: string;
  type: string;
  content: string;
  sentiment: number | null;
  time: string;
}

const FALLBACK_TICKERS: TickerItem[] = [];
const FALLBACK_MARKET_DATA: MarketOverviewItem[] = [];
const FALLBACK_INSIGHTS: InsightItem[] = [];

const ICON_MAP: Record<string, string> = {
  "EUR/USD": "💶",
  "GBP/USD": "💷",
  "USD/JPY": "💴",
  "BTC/USD": "₿",
  "ETH/USD": "Ξ",
  GOLD: "🥇",
  "Volatility 75": "📊",
  "Volatility 100": "📈",
};

const NAME_MAP: Record<string, string> = {
  "EUR/USD": "Euro / US Dollar",
  "GBP/USD": "British Pound / US Dollar",
  "USD/JPY": "US Dollar / Japanese Yen",
  "BTC/USD": "Bitcoin / US Dollar",
  "ETH/USD": "Ethereum / US Dollar",
  GOLD: "Gold Spot",
  "Volatility 75": "Volatility 75 Index",
  "Volatility 100": "Volatility 100 Index",
};


export function useTickerData(updateInterval = 10000) {
  const [tickers, setTickers] = useState<TickerItem[]>(FALLBACK_TICKERS);
  const [isUsingMock, setIsUsingMock] = useState(true);
  const previousPricesRef = useRef<Record<string, number>>({});

  // Use the market brief endpoint (1 request) instead of N individual
  // getLivePrice calls. The brief already fetches all instrument prices
  // in parallel on the backend. Watchlist personalization is preserved —
  // generate_market_brief(instruments=None) discovers instruments from
  // user watchlists and recent trades server-side.
  const fetchTickers = useCallback(async () => {
    const brief = await api.getMarketBrief();
    const instruments = brief.instruments || [];

    const live = instruments
      .filter((item) => item.price != null)
      .map((item) => {
        const prev = previousPricesRef.current[item.symbol];
        const next = item.price as number;
        const pct = item.change_percent ?? (prev && prev !== 0 ? ((next - prev) / prev) * 100 : 0);
        previousPricesRef.current[item.symbol] = next;

        return {
          symbol: item.symbol,
          price: next,
          change: pct,
          icon: ICON_MAP[item.symbol] || "📊",
        };
      });

    if (live.length === 0) {
      throw new Error("No live ticker data available");
    }

    setTickers(live);
    setIsUsingMock(false);
  }, []);

  useEffect(() => {
    let cancelled = false;

    const run = async () => {
      try {
        await fetchTickers();
      } catch {
        if (!cancelled) {
          setTickers(FALLBACK_TICKERS);
          setIsUsingMock(true);
        }
      }
    };

    run();
    const interval = setInterval(run, updateInterval);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [fetchTickers, updateInterval]);

  return { tickers, isUsingMock };
}

export function useMarketOverview() {
  const fetchOverview = useCallback(async () => {
    const brief = await api.getMarketBrief();
    const instruments = brief.instruments || [];

    return instruments.map((item) => ({
      symbol: item.symbol,
      name: NAME_MAP[item.symbol] || item.symbol,
      price: item.price ?? 0,
      change: item.change ?? 0,
      changePercent: item.change_percent ?? 0,
      volume: "N/A",
      icon: ICON_MAP[item.symbol] || "📊",
    }));
  }, []);

  return useApiWithFallback<MarketOverviewItem[]>({
    fetcher: fetchOverview,
    fallbackData: FALLBACK_MARKET_DATA,
    pollInterval: 15000,
  });
}

export function useMarketInsights() {
  const fetchInsights = useCallback(async () => {
    const response = await api.getMarketInsights();
    const raw = Array.isArray(response) ? response : response.results || [];

    return raw.map((item) => ({
      id: item.id,
      instrument: item.instrument,
      type: item.insight_type,
      content: item.content,
      sentiment: item.sentiment_score ?? item.confidence ?? null,
      time: new Date(item.generated_at || item.created_at || Date.now()).toLocaleTimeString(),
    }));
  }, []);

  return useApiWithFallback<InsightItem[]>({
    fetcher: fetchInsights,
    fallbackData: FALLBACK_INSIGHTS,
    pollInterval: 30000,
  });
}

export function useInstrumentUniverse() {
  const fetchInstruments = useCallback(async () => {
    const brief = await api.getMarketBrief();
    const symbols = (brief.instruments || []).map((item) => item.symbol).filter(Boolean);
    return Array.from(new Set(symbols));
  }, []);

  return useApiWithFallback<string[]>({
    fetcher: fetchInstruments,
    fallbackData: [],
    pollInterval: 60000,
  });
}

// ─── Finnhub / Deriv / NewsAPI hooks ────────────────────────────────

export function useEconomicCalendar() {
  const fetchCalendar = useCallback(async () => {
    const data: EconomicCalendarResponse = await api.getEconomicCalendar();
    return data.events || [];
  }, []);

  return useApiWithFallback<EconomicEvent[]>({
    fetcher: fetchCalendar,
    fallbackData: [],
    pollInterval: 300000, // 5 minutes
  });
}

export function useTopHeadlines(limit = 8) {
  const fetchHeadlines = useCallback(async () => {
    const data: TopHeadlinesResponse = await api.getTopHeadlines(limit);
    return data.headlines || [];
  }, [limit]);

  return useApiWithFallback<Array<{ title: string; description: string; url: string; publishedAt: string; source: string }>>({
    fetcher: fetchHeadlines,
    fallbackData: [],
    pollInterval: 120000, // 2 minutes
  });
}
