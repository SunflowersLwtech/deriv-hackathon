"use client";

import { useState } from "react";
import AppShell from "@/components/layout/AppShell";
import PnLChart from "@/components/market/PnLChart";
import MarketOverview from "@/components/market/MarketOverview";
import DataCard from "@/components/ui/DataCard";
import DisclaimerBadge from "@/components/ui/DisclaimerBadge";
import CollapsibleSection from "@/components/ui/CollapsibleSection";
import LoadingDots from "@/components/ui/LoadingDots";
import { cn } from "@/lib/utils";
import api from "@/lib/api";

const instruments = [
  { symbol: "EUR/USD", icon: "💶" },
  { symbol: "GBP/USD", icon: "💷" },
  { symbol: "USD/JPY", icon: "💴" },
  { symbol: "BTC/USD", icon: "₿" },
  { symbol: "ETH/USD", icon: "Ξ" },
  { symbol: "Volatility 75", icon: "📊" },
  { symbol: "GOLD", icon: "🥇" },
];

export default function MarketPage() {
  const [selectedInstrument, setSelectedInstrument] = useState("EUR/USD");
  const [question, setQuestion] = useState("");
  const [analysis, setAnalysis] = useState<string>("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const handleAskAnalyst = async () => {
    if (!question.trim()) return;
    setIsAnalyzing(true);
    setAnalysis("");

    try {
      const response = await api.askMarketAnalyst(question.trim());
      setAnalysis(response.answer + (response.disclaimer ? `\n\n⚠️ ${response.disclaimer}` : ""));
    } catch {
      setAnalysis(
        "I'm currently unable to connect to the analysis engine. Here's what I can tell you based on general market knowledge:\n\n" +
        "The market you're asking about is influenced by multiple factors including macroeconomic conditions, central bank policies, and market sentiment. " +
        "For the most up-to-date analysis, please ensure the backend service is running.\n\n" +
        "⚠️ This is AI-generated educational content, not financial advice."
      );
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <AppShell>
      <div className="p-4 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-white tracking-tight">Market Analysis</h1>
            <p className="text-[11px] text-muted mono-data mt-0.5">
              AI-powered market intelligence and technical analysis
            </p>
          </div>
          <DisclaimerBadge variant="banner" text="Educational analysis only. Not trading signals." className="max-w-xs" />
        </div>

        {/* Instrument Selector */}
        <div className="flex items-center gap-0 border border-border rounded-sm overflow-hidden w-fit flex-wrap">
          {instruments.map((inst) => (
            <button
              key={inst.symbol}
              onClick={() => setSelectedInstrument(inst.symbol)}
              className={cn(
                "px-3 py-2 text-[10px] font-medium tracking-wider mono-data transition-colors border-r border-border last:border-r-0 flex items-center gap-1.5",
                selectedInstrument === inst.symbol
                  ? "bg-white text-black"
                  : "bg-transparent text-muted hover:text-white hover:bg-surface"
              )}
            >
              <span className="text-xs">{inst.icon}</span>
              {inst.symbol}
            </button>
          ))}
        </div>

        {/* Chart + Technical Analysis */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            <PnLChart title={`${selectedInstrument} PRICE CHART`} height={320} />
          </div>

          {/* Technical Indicators */}
          <div className="space-y-3">
            <div className="bg-card border border-border rounded-sm p-4">
              <h3 className="text-[10px] font-semibold tracking-wider text-muted uppercase mono-data mb-3">
                TECHNICAL INDICATORS
              </h3>
              <div className="space-y-3">
                <TechnicalIndicator label="RSI (14)" value="42.3" status="neutral" description="Neutral zone" />
                <TechnicalIndicator label="SMA 20" value="1.0835" status="below" description="Price above" />
                <TechnicalIndicator label="SMA 50" value="1.0798" status="above" description="Price above" />
                <TechnicalIndicator label="MACD" value="-0.0012" status="bearish" description="Bearish crossover" />
                <TechnicalIndicator label="Bollinger" value="1.0780-1.0900" status="neutral" description="Within bands" />
              </div>
            </div>

            <DataCard title="TREND" value="BEARISH" trend="down" glow>
              <p className="text-[10px] text-muted mt-1">Short-term bearish, long-term neutral. Watch 1.0820 support.</p>
            </DataCard>

            <DataCard title="SENTIMENT" value="38/100" subtitle="Slightly bearish" trend="down">
              <div className="w-full bg-surface rounded-full h-1.5 mt-2">
                <div className="bg-loss h-1.5 rounded-full transition-all duration-500" style={{ width: "38%" }} />
              </div>
            </DataCard>
          </div>
        </div>

        {/* Ask the Analyst */}
        <div className="bg-card border border-border rounded-sm p-4">
          <h3 className="text-[10px] font-semibold tracking-wider text-muted uppercase mono-data mb-3">
            ASK THE AI ANALYST
          </h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAskAnalyst()}
              placeholder={`Ask about ${selectedInstrument}... e.g., "What's driving the recent move?"`}
              className={cn(
                "flex-1 bg-surface border border-border rounded-sm px-3 py-2.5",
                "text-[11px] text-white placeholder:text-muted-foreground mono-data",
                "focus:outline-none focus:border-muted transition-colors"
              )}
            />
            <button
              onClick={handleAskAnalyst}
              disabled={!question.trim() || isAnalyzing}
              className={cn(
                "px-4 py-2.5 rounded-sm text-[10px] font-semibold tracking-wider mono-data transition-all",
                question.trim() && !isAnalyzing
                  ? "bg-white text-black hover:bg-gray-200"
                  : "bg-border text-muted-foreground cursor-not-allowed"
              )}
            >
              {isAnalyzing ? "ANALYZING..." : "ASK"}
            </button>
          </div>

          {/* Analysis Result */}
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
                    <div className="text-[11px] text-muted leading-relaxed mono-data whitespace-pre-wrap">
                      {analysis}
                    </div>
                  )}
                </div>
              </CollapsibleSection>
            </div>
          )}

          {/* Quick Questions */}
          <div className="flex flex-wrap gap-2 mt-3">
            {[
              `What's happening with ${selectedInstrument}?`,
              `Key support/resistance for ${selectedInstrument}`,
              `News affecting ${selectedInstrument} today`,
              "Should I be cautious right now?",
            ].map((q) => (
              <button
                key={q}
                onClick={() => {
                  setQuestion(q);
                }}
                className="px-2 py-1 rounded-sm text-[9px] mono-data text-muted border border-border/50 hover:border-muted hover:text-white transition-colors"
              >
                {q}
              </button>
            ))}
          </div>
        </div>

        {/* Market Overview */}
        <MarketOverview />

        <DisclaimerBadge variant="footer" />
      </div>
    </AppShell>
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
    <div className="flex items-center justify-between">
      <div>
        <span className="text-[10px] text-muted-foreground mono-data">{label}</span>
        <span className="text-[9px] text-muted-foreground/50 ml-1">({description})</span>
      </div>
      <span className={cn("text-[11px] font-medium mono-data", statusColors[status] || "text-white")}>
        {value}
      </span>
    </div>
  );
}
