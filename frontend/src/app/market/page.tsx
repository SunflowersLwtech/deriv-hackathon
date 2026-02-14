"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import AppShell from "@/components/layout/AppShell";
import DataCard from "@/components/ui/DataCard";
import DisclaimerBadge from "@/components/ui/DisclaimerBadge";
import CollapsibleSection from "@/components/ui/CollapsibleSection";
import LoadingDots from "@/components/ui/LoadingDots";
import { cn } from "@/lib/utils";
import api, { type MarketSentiment, type MarketTechnicals } from "@/lib/api";
import { useInstrumentUniverse, useEconomicCalendar, useTopHeadlines } from "@/hooks/useMarketData";

const PnLChart = dynamic(() => import("@/components/market/PnLChart"), {
  loading: () => <div className="bg-card border border-border rounded-md p-6 h-[400px] animate-shimmer" />,
  ssr: false,
});

const MarketOverview = dynamic(() => import("@/components/market/MarketOverview"), {
  loading: () => <div className="bg-card border border-border rounded-md h-[300px] animate-shimmer" />,
  ssr: false,
});

const INSTRUMENT_ICONS: Record<string, string> = {
  "BTC/USD": "₿",
  "ETH/USD": "Ξ",
  "Volatility 75": "📊",
  "Volatility 100": "📈",
  "Volatility 10": "📉",
  "EUR/USD": "💶",
  "GBP/USD": "💷",
  "USD/JPY": "💴",
  GOLD: "🥇",
};

type TimelineOption = "1H" | "6H" | "1D" | "3D" | "1W" | "2W" | "1M" | "3M" | "6M" | "1Y";

interface TimelineConfig {
  label: string;
  timeframe: string;
  candles: number;
}

const TIMELINE_OPTIONS: Record<TimelineOption, TimelineConfig> = {
  "1H": { label: "1H", timeframe: "1h", candles: 12 },
  "6H": { label: "6H", timeframe: "1h", candles: 24 },
  "1D": { label: "1D", timeframe: "1h", candles: 36 },
  "3D": { label: "3D", timeframe: "1h", candles: 72 },
  "1W": { label: "1W", timeframe: "1d", candles: 7 },
  "2W": { label: "2W", timeframe: "1d", candles: 14 },
  "1M": { label: "1M", timeframe: "1d", candles: 30 },
  "3M": { label: "3M", timeframe: "1d", candles: 90 },
  "6M": { label: "6M", timeframe: "1d", candles: 180 },
  "1Y": { label: "1Y", timeframe: "1d", candles: 365 },
};

const TIMELINE_ORDER: TimelineOption[] = ["1H", "6H", "1D", "3D", "1W", "2W", "1M", "3M", "6M", "1Y"];

export default function MarketPage() {
  const { data: availableInstruments } = useInstrumentUniverse();
  const [selectedInstrument, setSelectedInstrument] = useState("");
  const [selectedTimeline, setSelectedTimeline] = useState<TimelineOption>("1D");
  const [question, setQuestion] = useState("");
  const [analysis, setAnalysis] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const [technicals, setTechnicals] = useState<MarketTechnicals | null>(null);
  const [sentiment, setSentiment] = useState<MarketSentiment | null>(null);
  const [isMetricsLoading, setIsMetricsLoading] = useState(false);
  const [isChartLoading, setIsChartLoading] = useState(false);

  useEffect(() => {
    if (!selectedInstrument && availableInstruments.length > 0) {
      setSelectedInstrument(availableInstruments[0]);
    }
  }, [availableInstruments, selectedInstrument]);

  useEffect(() => {
    if (!selectedInstrument) return;
    let cancelled = false;

    const loadMarketMetrics = async () => {
      setIsMetricsLoading(true);
      try {
        const [techResp, sentResp] = await Promise.all([
          api.getMarketTechnicals(selectedInstrument, "1h"),
          api.getMarketSentiment(selectedInstrument),
        ]);
        if (!cancelled) {
          setTechnicals(techResp);
          setSentiment(sentResp);
        }
      } catch {
        if (!cancelled) {
          setTechnicals(null);
          setSentiment(null);
        }
      } finally {
        if (!cancelled) {
          setIsMetricsLoading(false);
        }
      }
    };

    loadMarketMetrics();
    const interval = setInterval(loadMarketMetrics, 20000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [selectedInstrument]);

  const handleAskAnalyst = async () => {
    if (!question.trim() || !selectedInstrument) return;
    setIsAnalyzing(true);
    setAnalysis("");

    try {
      const prompt = question.includes(selectedInstrument)
        ? question.trim()
        : `${selectedInstrument}: ${question.trim()}`;
      const response = await api.askMarketAnalyst(prompt);
      setAnalysis(response.answer + (response.disclaimer ? `\n\n⚠️ ${response.disclaimer}` : ""));
    } catch {
      setAnalysis("Unable to retrieve AI analysis right now. Please verify backend and API availability.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  const sentimentPercent = useMemo(() => {
    const score = sentiment?.score ?? 0;
    return Math.max(0, Math.min(100, ((score + 1) / 2) * 100));
  }, [sentiment]);

  return (
    <AppShell>
      <div className="p-6 md:p-10 space-y-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Market Analysis</h1>
            <p className="text-sm text-muted mono-data mt-2">AI-powered market intelligence and technical analysis</p>
          </div>
          <DisclaimerBadge variant="banner" text="Educational analysis only. Not trading signals." className="max-w-xs" />
        </div>

        <div className="flex items-center gap-3">
          <label htmlFor="instrument-select" className="text-sm font-medium text-muted mono-data tracking-wider">
            INSTRUMENT:
          </label>
          <div className="relative">
            <select
              id="instrument-select"
              value={selectedInstrument}
              onChange={(e) => setSelectedInstrument(e.target.value)}
              disabled={availableInstruments.length === 0}
              className={cn(
                "appearance-none bg-card border border-border rounded-md pl-4 pr-10 py-3",
                "text-sm font-medium tracking-wider mono-data text-white",
                "focus:outline-none focus:border-white focus:ring-1 focus:ring-white",
                "transition-all cursor-pointer hover:border-muted",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "min-w-[200px]"
              )}
            >
              {availableInstruments.length === 0 ? (
                <option value="">No instruments available</option>
              ) : (
                availableInstruments.map((symbol) => (
                  <option key={symbol} value={symbol} className="bg-surface text-white">
                    {INSTRUMENT_ICONS[symbol] || "📊"} {symbol}
                  </option>
                ))
              )}
            </select>
            <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-muted">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </div>
          {selectedInstrument && (
            <div className="flex items-center gap-2 px-4 py-2 bg-surface border border-border rounded-md">
              <span className="text-xl">{INSTRUMENT_ICONS[selectedInstrument] || "📊"}</span>
              <span className="text-sm font-semibold text-white mono-data tracking-wider">{selectedInstrument}</span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="min-h-[460px]">
              <PnLChart
                key={`${selectedInstrument}-${selectedTimeline}`}
                title={`${selectedInstrument || "MARKET"} PRICE CHART`}
                height={380}
                instrument={selectedInstrument || undefined}
                timeframe={TIMELINE_OPTIONS[selectedTimeline].timeframe}
                candles={TIMELINE_OPTIONS[selectedTimeline].candles}
                timeline={selectedTimeline}
                onLoadingChange={setIsChartLoading}
              />
            </div>

            {/* Timeline Controls */}
            <div className="flex items-center justify-center gap-3 flex-wrap">
              {TIMELINE_ORDER.map((timeline) => (
                <button
                  key={timeline}
                  onClick={() => setSelectedTimeline(timeline)}
                  disabled={isChartLoading}
                  className={cn(
                    "px-6 py-3 rounded-lg text-sm font-bold tracking-widest mono-data transition-all duration-200",
                    selectedTimeline === timeline
                      ? "bg-white text-black shadow-lg scale-110 border-2 border-white"
                      : "bg-card text-muted-foreground border-2 border-border hover:text-white hover:border-white/40 hover:bg-surface hover:scale-105 shadow-md",
                    isChartLoading && "opacity-40 cursor-not-allowed pointer-events-none"
                  )}
                >
                  {TIMELINE_OPTIONS[timeline].label}
                  {isChartLoading && selectedTimeline === timeline && (
                    <span className="ml-2 inline-block w-3 h-3 border-2 border-black border-t-transparent rounded-full animate-spin" />
                  )}
                </button>
              ))}
            </div>
          </div>

          <div className="flex flex-col gap-5 lg:max-h-[540px]">
            <div className="bg-card border border-border rounded-md p-6 shrink-0">
              <h3 className="text-sm font-semibold tracking-wider text-muted uppercase mono-data mb-5">TECHNICAL INDICATORS</h3>
              {isMetricsLoading ? (
                <div className="flex items-center gap-2 text-xs text-muted mono-data"><LoadingDots /> Loading indicators...</div>
              ) : (
                <div className="space-y-3.5">
                  <TechnicalIndicator
                    label="RSI (14)"
                    value={technicals?.indicators?.rsi14 != null ? String(technicals.indicators.rsi14) : "N/A"}
                    status={technicals?.indicators?.rsi14 != null && technicals.indicators.rsi14 > 70 ? "bearish" : technicals?.indicators?.rsi14 != null && technicals.indicators.rsi14 < 30 ? "bullish" : "neutral"}
                    description="Momentum"
                  />
                  <TechnicalIndicator
                    label="SMA 20"
                    value={technicals?.indicators?.sma20 != null ? String(technicals.indicators.sma20.toFixed(4)) : "N/A"}
                    status="neutral"
                    description="Short trend"
                  />
                  <TechnicalIndicator
                    label="SMA 50"
                    value={technicals?.indicators?.sma50 != null ? String(technicals.indicators.sma50.toFixed(4)) : "N/A"}
                    status="neutral"
                    description="Mid trend"
                  />
                  <TechnicalIndicator
                    label="Support"
                    value={technicals?.key_levels?.support != null ? String(technicals.key_levels.support.toFixed(4)) : "N/A"}
                    status="below"
                    description="Recent low"
                  />
                  <TechnicalIndicator
                    label="Resistance"
                    value={technicals?.key_levels?.resistance != null ? String(technicals.key_levels.resistance.toFixed(4)) : "N/A"}
                    status="above"
                    description="Recent high"
                  />
                </div>
              )}
            </div>

            {/* Trend Card — fixed box, scrollable insights */}
            <div
              className={cn(
                "bg-card border rounded-md p-6 transition-all duration-200 flex flex-col flex-1 min-h-0 overflow-hidden",
                technicals?.trend === "bullish" ? "border-profit/30" : technicals?.trend === "bearish" ? "border-loss/30" : "border-border"
              )}
            >
              <div className="flex items-center justify-between mb-2.5 shrink-0">
                <h3 className="text-xs font-semibold tracking-wider text-muted uppercase mono-data">TREND</h3>
                <span
                  className={cn(
                    "text-xs mono-data font-semibold",
                    technicals?.trend === "bullish" && "text-profit",
                    technicals?.trend === "bearish" && "text-loss",
                    (!technicals?.trend || technicals.trend === "neutral") && "text-muted"
                  )}
                >
                  {technicals?.trend === "bullish" ? "▲" : technicals?.trend === "bearish" ? "▼" : "—"}
                </span>
              </div>
              <div
                className={cn(
                  "text-3xl font-bold mono-data tracking-tight shrink-0",
                  technicals?.trend === "bullish" && "text-profit",
                  technicals?.trend === "bearish" && "text-loss",
                  (!technicals?.trend || technicals.trend === "neutral") && "text-white"
                )}
              >
                {(technicals?.trend || "neutral").toUpperCase()}
              </div>
              <p className="text-[10px] text-muted mt-1 shrink-0">{technicals?.summary || "No technical summary available."}</p>

              {/* Scrollable insights */}
              {technicals?.insights && technicals.insights.length > 0 && (
                <div className="mt-3 border-t border-border pt-3 flex-1 min-h-0 flex flex-col overflow-hidden">
                  <h4 className="text-[10px] font-semibold tracking-wider text-muted uppercase mono-data mb-2 shrink-0">WHY {(technicals?.trend || "neutral").toUpperCase()}?</h4>
                  <div className="overflow-y-auto pr-1 space-y-2.5 flex-1 min-h-0">
                    {technicals.insights.map((insight, i) => (
                      <div key={i} className="flex gap-2">
                        <span className={cn(
                          "mt-1 w-1.5 h-1.5 rounded-full shrink-0",
                          technicals.trend === "bullish" ? "bg-profit" : technicals.trend === "bearish" ? "bg-loss" : "bg-muted"
                        )} />
                        <p className="text-[11px] text-muted-foreground leading-relaxed mono-data">{insight}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <DataCard title="SENTIMENT" value={`${Math.round(sentimentPercent)}/100`} subtitle={sentiment?.sentiment || "neutral"} trend={sentimentPercent >= 50 ? "up" : "down"} className="shrink-0">
              <div className="w-full bg-surface rounded-full h-1.5 mt-2">
                <div
                  className={cn("h-1.5 rounded-full transition-all duration-500", sentimentPercent >= 50 ? "bg-profit" : "bg-loss")}
                  style={{ width: `${sentimentPercent}%` }}
                />
              </div>
            </DataCard>
          </div>
        </div>

        <div className="bg-card border border-border rounded-md p-6">
          <h3 className="text-sm font-semibold tracking-wider text-muted uppercase mono-data mb-5">ASK THE AI ANALYST</h3>
          <div className="flex gap-3">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAskAnalyst()}
              placeholder={`Ask about ${selectedInstrument || "the selected instrument"}...`}
              className={cn(
                "flex-1 bg-surface border border-border rounded-md px-5 py-3.5",
                "text-sm text-white placeholder:text-muted-foreground mono-data",
                "focus:outline-none focus:border-muted transition-colors"
              )}
            />
            <button
              onClick={handleAskAnalyst}
              disabled={!question.trim() || isAnalyzing || !selectedInstrument}
              className={cn(
                "px-6 py-3.5 rounded-md text-sm font-semibold tracking-wider mono-data transition-all",
                question.trim() && !isAnalyzing && selectedInstrument
                  ? "bg-white text-black hover:bg-gray-200"
                  : "bg-border text-muted-foreground cursor-not-allowed"
              )}
            >
              {isAnalyzing ? "ANALYZING..." : "ASK"}
            </button>
          </div>

          {(analysis || isAnalyzing) && (
            <div className="mt-3 animate-fade-in">
              <CollapsibleSection title="AI ANALYSIS" defaultOpen>
                <div className="p-4 bg-surface/50">
                  {isAnalyzing ? (
                    <div className="flex items-center gap-2">
                      <LoadingDots />
                      <span className="text-[10px] text-muted mono-data">Analyzing market data...</span>
                    </div>
                  ) : (
                    <div className="text-[11px] text-muted leading-relaxed mono-data whitespace-pre-wrap">{analysis}</div>
                  )}
                </div>
              </CollapsibleSection>
            </div>
          )}

          <div className="flex flex-wrap gap-3 mt-5">
            {[
              `What's happening with ${selectedInstrument || "this instrument"}?`,
              `Key support/resistance for ${selectedInstrument || "this instrument"}`,
              `News affecting ${selectedInstrument || "this instrument"} today`,
              "What does current sentiment imply historically?",
            ].map((q) => (
              <button
                key={q}
                onClick={() => setQuestion(q)}
                className="px-4 py-2 rounded-md text-xs mono-data text-muted border border-border/50 hover:border-muted hover:text-white transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        <MarketOverview />

        {/* Economic Calendar */}
        <EconomicCalendarPanel />

        {/* Top Headlines */}
        <TopHeadlinesPanel />

        <DisclaimerBadge variant="footer" />
      </div>
    </AppShell>
  );
}

function EconomicCalendarPanel() {
  const { data: events, isLoading } = useEconomicCalendar();

  if (isLoading) return null;
  if (!events || events.length === 0) return null;

  const impactColor: Record<string, string> = {
    high: "text-loss", "3": "text-loss",
    medium: "text-warning", "2": "text-warning",
    low: "text-muted", "1": "text-muted",
  };

  return (
    <div className="bg-card border border-border rounded-md overflow-hidden">
      <div className="px-5 py-3.5 border-b border-border flex items-center justify-between">
        <h3 className="text-xs font-semibold tracking-widest mono-data text-muted">ECONOMIC CALENDAR</h3>
        <span className="text-[11px] text-muted-foreground mono-data">FINNHUB</span>
      </div>
      <div className="divide-y divide-border/30 max-h-[300px] overflow-y-auto">
        {events.slice(0, 12).map((ev, i) => (
          <div key={i} className="px-5 py-3 flex items-center justify-between text-sm mono-data">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              <span className="text-muted-foreground w-6 shrink-0">{ev.country}</span>
              <span className={cn("w-1.5 h-1.5 rounded-full shrink-0", ev.impact === "high" || ev.impact === "3" ? "bg-loss" : ev.impact === "medium" || ev.impact === "2" ? "bg-warning" : "bg-muted")} />
              <span className="text-white truncate">{ev.event}</span>
            </div>
            <div className="flex items-center gap-4 shrink-0 ml-2">
              <span className="text-muted-foreground text-[10px]">{ev.date} {ev.time}</span>
              {ev.actual !== null && <span className={cn("font-medium", impactColor[ev.impact] || "text-white")}>{ev.actual}{ev.unit}</span>}
              {ev.actual === null && ev.estimate !== null && <span className="text-muted-foreground">est: {ev.estimate}{ev.unit}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TopHeadlinesPanel() {
  const { data: headlines, isLoading } = useTopHeadlines();

  if (isLoading) return null;
  if (!headlines || headlines.length === 0) return null;

  return (
    <div className="bg-card border border-border rounded-sm overflow-hidden">
      <div className="px-4 py-2.5 border-b border-border flex items-center justify-between">
        <h3 className="text-[10px] font-semibold tracking-widest mono-data text-muted">TOP HEADLINES</h3>
        <span className="text-[9px] text-muted-foreground mono-data">NEWSAPI</span>
      </div>
      <div className="divide-y divide-border/30 max-h-[200px] overflow-y-auto">
        {headlines.slice(0, 8).map((h, i) => (
          <a
            key={i}
            href={h.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block px-4 py-2.5 hover:bg-surface/50 transition-colors"
          >
            <div className="text-[11px] text-white mono-data leading-snug line-clamp-2">{h.title}</div>
            <div className="text-[9px] text-muted-foreground mt-1 mono-data">{h.source} &middot; {new Date(h.publishedAt).toLocaleTimeString()}</div>
          </a>
        ))}
      </div>
    </div>
  );
}

function TechnicalIndicator({
  label,
  value,
  status,
  description,
}: {
  label: string;
  value: string;
  status: string;
  description: string;
}) {
  const statusColors: Record<string, string> = {
    bullish: "text-profit",
    above: "text-profit",
    bearish: "text-loss",
    below: "text-loss",
    neutral: "text-warning",
  };

  return (
    <div className="flex items-center justify-between py-1.5">
      <div>
        <span className="text-sm text-muted-foreground mono-data">{label}</span>
        <span className="text-xs text-muted-foreground/50 ml-2">({description})</span>
      </div>
      <span className={cn("text-base font-medium mono-data", statusColors[status] || "text-white")}>{value}</span>
    </div>
  );
}
