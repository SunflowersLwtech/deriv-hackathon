"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useRouter } from "next/navigation";
import AppShell from "@/components/layout/AppShell";
import DataCard from "@/components/ui/DataCard";
import DisclaimerBadge from "@/components/ui/DisclaimerBadge";
import CollapsibleSection from "@/components/ui/CollapsibleSection";
import StatusBadge from "@/components/ui/StatusBadge";
import DataSourceBadge from "@/components/ui/DataSourceBadge";
import { cn } from "@/lib/utils";
import { useDashboardMetrics } from "@/hooks/useDashboardData";
import { useMarketInsights } from "@/hooks/useMarketData";
import { useApiWithFallback } from "@/hooks/useApiWithFallback";
import api from "@/lib/api";
import type { Trade } from "@/lib/api";
import { useCallback } from "react";

const PnLChart = dynamic(() => import("@/components/market/PnLChart"), {
  loading: () => <div className="bg-card border border-border rounded-md p-6 h-[400px] animate-shimmer" />,
  ssr: false,
});

const MarketOverview = dynamic(() => import("@/components/market/MarketOverview"), {
  loading: () => <div className="bg-card border border-border rounded-md h-[300px] animate-shimmer" />,
  ssr: false,
});

const tabs = [
  { id: "overview", label: "Overview" },
  { id: "market", label: "Market Analysis" },
  { id: "positions", label: "Positions" },
  { id: "signals", label: "AI Signals" },
];

function useTrades() {
  const fetchTrades = useCallback(async () => {
    const resp = await api.getTrades();
    const trades = Array.isArray(resp) ? resp : resp.results || [];
    return trades;
  }, []);

  return useApiWithFallback<Trade[]>({
    fetcher: fetchTrades,
    fallbackData: [],
    pollInterval: 15000,
    cacheKey: "trades",
  });
}

export default function DashboardPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("overview");
  const [isRefreshingInsights, setIsRefreshingInsights] = useState(false);
  const { data: metrics, isUsingMock: metricsIsMock, isBackendOnline } = useDashboardMetrics();
  const { data: insights, isUsingMock: insightsIsMock, refetch: refetchInsights } = useMarketInsights();
  const { data: trades, isUsingMock: tradesIsMock } = useTrades();

  const handleRefreshInsights = useCallback(async () => {
    setIsRefreshingInsights(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/market/insights/refresh/`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ limit: 8, max_insights: 5 }),
        }
      );
      if (response.ok) {
        await refetchInsights();
      }
    } catch (error) {
      console.error("Failed to refresh insights:", error);
    } finally {
      setIsRefreshingInsights(false);
    }
  }, [refetchInsights]);

  return (
    <AppShell>
      <div className="p-6 md:p-8 space-y-6">
        {/* Tab Navigation */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-0 border border-border rounded-sm overflow-hidden w-fit">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "px-5 py-2.5 text-xs font-medium tracking-wider mono-data transition-colors border-r border-border last:border-r-0",
                  activeTab === tab.id
                    ? "bg-white text-black"
                    : "bg-transparent text-muted hover:text-white hover:bg-surface"
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>
          <DataSourceBadge isUsingMock={metricsIsMock} isBackendOnline={isBackendOnline} />
        </div>

        {/* ── Tab Content Area ── */}
        <div className="min-h-[400px]">

          {/* ── Overview Tab ── */}
          {activeTab === "overview" && (
            <div className="space-y-6">
              <p className="text-xs text-muted mono-data">
                Real-time AI-powered trading intelligence dashboard. All analysis is educational — not financial advice.
              </p>

              {/* Key Metrics Row */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
                <DataCard
                  title="Portfolio Value"
                  value={`$${metrics.portfolioValue.toLocaleString("en-US", { minimumFractionDigits: 2 })}`}
                  subtitle="Updated just now"
                  trend={metrics.todayPnl >= 0 ? "up" : "down"}
                  glow
                />
                <DataCard
                  title="Today's P&L"
                  value={`${metrics.todayPnl >= 0 ? "+" : ""}$${metrics.todayPnl.toFixed(2)}`}
                  subtitle={`${metrics.todayPnlPercent >= 0 ? "+" : ""}${metrics.todayPnlPercent.toFixed(2)}%`}
                  trend={metrics.todayPnl >= 0 ? "up" : "down"}
                  glow
                />
                <DataCard
                  title="Risk Score"
                  value={`${metrics.riskScore}/100`}
                  subtitle={metrics.riskScore > 70 ? "High" : metrics.riskScore > 40 ? "Moderate" : "Low"}
                  trend={metrics.riskScore > 50 ? "down" : "neutral"}
                >
                  <div className="w-full bg-surface rounded-full h-1.5 mt-1">
                    <div
                      className={cn(
                        "h-1.5 rounded-full transition-all duration-500",
                        metrics.riskScore > 70 ? "bg-loss" : metrics.riskScore > 40 ? "bg-warning" : "bg-profit"
                      )}
                      style={{ width: `${metrics.riskScore}%` }}
                    />
                  </div>
                </DataCard>
                <DataCard
                  title="Active Patterns"
                  value={String(metrics.activePatterns)}
                  subtitle={metrics.patternLabels.join(", ").toLowerCase()}
                  trend={metrics.activePatterns > 0 ? "down" : "up"}
                >
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {metrics.patternLabels.map((label) => (
                      <StatusBadge
                        key={label}
                        status={label === "NONE" ? "success" : "warning"}
                        label={label}
                      />
                    ))}
                  </div>
                </DataCard>
              </div>

              {/* Main Content Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <PnLChart height={340} />
                </div>

                <div className="space-y-5">
                  <div className="bg-card border border-border rounded-md p-6">
                    <h3 className="text-sm font-semibold tracking-wider text-muted uppercase mono-data mb-5">
                      QUICK ACTIONS
                    </h3>
                    <div className="space-y-3">
                      <QuickActionButton label="RUN MARKET BRIEF" description="AI analysis of tracked instruments" icon="📊" onClick={() => router.push("/market")} />
                      <QuickActionButton label="CHECK BEHAVIOR" description="Scan current trading patterns" icon="🧠" onClick={() => router.push("/behavior")} />
                      <QuickActionButton label="GENERATE CONTENT" description="Create Bluesky post from insights" icon="✍️" onClick={() => router.push("/content")} />
                      <QuickActionButton label="WOW MOMENT" description="Full pipeline: Market → Behavior → Content" icon="⚡" highlight onClick={() => router.push("/behavior")} />
                    </div>
                  </div>

                  <CollapsibleSection
                    title="RECENT AI INSIGHTS"
                    defaultOpen
                    badge={
                      <div className="flex items-center gap-2">
                        <DataSourceBadge isUsingMock={insightsIsMock} />
                        <button
                          onClick={(e) => { e.stopPropagation(); handleRefreshInsights(); }}
                          disabled={isRefreshingInsights}
                          className={cn(
                            "px-2 py-0.5 text-[10px] font-medium tracking-wider mono-data rounded-sm transition-colors",
                            "border border-accent/30 text-accent hover:bg-accent/10",
                            isRefreshingInsights && "opacity-50 cursor-not-allowed"
                          )}
                        >
                          {isRefreshingInsights ? "..." : "REFRESH"}
                        </button>
                      </div>
                    }
                  >
                    <div className="max-h-[320px] overflow-y-auto p-5 space-y-4">
                      {insights.length === 0 ? (
                        <p className="text-sm text-muted mono-data text-center py-4">
                          No insights available. Click REFRESH to generate from latest news.
                        </p>
                      ) : null}
                      {insights.map((insight) => {
                        const typeMap: Record<string, "market" | "behavior" | "content"> = {
                          technical: "market", news: "market", sentiment: "market",
                          behavior: "behavior", content: "content",
                        };
                        return (
                          <InsightItem
                            key={insight.id}
                            type={typeMap[insight.type] || "market"}
                            text={insight.content}
                            time={insight.time}
                          />
                        );
                      })}
                    </div>
                  </CollapsibleSection>
                </div>
              </div>

              <MarketOverview />
            </div>
          )}

          {/* ── Market Analysis Tab ── */}
          {activeTab === "market" && (
            <div className="space-y-6">
              <MarketOverview />

              <CollapsibleSection
                title="MARKET INSIGHTS"
                defaultOpen
                badge={
                  <div className="flex items-center gap-2">
                    <DataSourceBadge isUsingMock={insightsIsMock} />
                    <button
                      onClick={(e) => { e.stopPropagation(); handleRefreshInsights(); }}
                      disabled={isRefreshingInsights}
                      className={cn(
                        "px-2 py-0.5 text-[10px] font-medium tracking-wider mono-data rounded-sm transition-colors",
                        "border border-accent/30 text-accent hover:bg-accent/10",
                        isRefreshingInsights && "opacity-50 cursor-not-allowed"
                      )}
                    >
                      {isRefreshingInsights ? "..." : "REFRESH"}
                    </button>
                  </div>
                }
              >
                <div className="max-h-[480px] overflow-y-auto p-5 space-y-4">
                  {insights.length === 0 && (
                    <p className="text-sm text-muted mono-data text-center py-6">
                      No market insights available. Click REFRESH to generate from latest news.
                    </p>
                  )}
                  {insights.map((insight) => {
                    const typeMap: Record<string, "market" | "behavior" | "content"> = {
                      technical: "market", news: "market", sentiment: "market",
                      behavior: "behavior", content: "content",
                    };
                    return (
                      <InsightItem
                        key={insight.id}
                        type={typeMap[insight.type] || "market"}
                        text={insight.content}
                        time={insight.time}
                      />
                    );
                  })}
                </div>
              </CollapsibleSection>

              <div className="flex justify-center pt-2">
                <button
                  onClick={() => router.push("/market")}
                  className="px-6 py-3 text-xs font-medium tracking-wider mono-data border border-border rounded-sm hover:bg-surface transition-colors text-muted hover:text-white"
                >
                  OPEN FULL MARKET ANALYSIS
                </button>
              </div>
            </div>
          )}

          {/* ── Positions Tab ── */}
          {activeTab === "positions" && (
            <div className="space-y-6">
              {/* Positions summary cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
                <DataCard
                  title="Total Trades"
                  value={String(trades.length)}
                  subtitle={`${trades.filter((t) => !t.closed_at).length} open`}
                  trend="neutral"
                />
                <DataCard
                  title="Total P&L"
                  value={`${trades.reduce((s, t) => s + Number(t.pnl), 0) >= 0 ? "+" : ""}$${trades.reduce((s, t) => s + Number(t.pnl), 0).toFixed(2)}`}
                  subtitle="All trades"
                  trend={trades.reduce((s, t) => s + Number(t.pnl), 0) >= 0 ? "up" : "down"}
                  glow
                />
                <DataCard
                  title="Winning"
                  value={String(trades.filter((t) => Number(t.pnl) > 0).length)}
                  subtitle={trades.length > 0 ? `${((trades.filter((t) => Number(t.pnl) > 0).length / trades.length) * 100).toFixed(0)}% win rate` : "—"}
                  trend="up"
                />
                <DataCard
                  title="Losing"
                  value={String(trades.filter((t) => Number(t.pnl) < 0).length)}
                  subtitle={trades.length > 0 ? `${((trades.filter((t) => Number(t.pnl) < 0).length / trades.length) * 100).toFixed(0)}% loss rate` : "—"}
                  trend="down"
                />
              </div>

              {/* Positions table */}
              <div className="bg-card border border-border rounded-md">
                <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                  <div className="flex items-center gap-3">
                    <h3 className="text-sm font-semibold tracking-wider text-muted uppercase mono-data">TRADE HISTORY</h3>
                    <DataSourceBadge isUsingMock={tradesIsMock} isBackendOnline={isBackendOnline} />
                  </div>
                  <span className="text-xs text-muted mono-data">{trades.length} TRADE{trades.length !== 1 ? "S" : ""}</span>
                </div>

                {trades.length === 0 ? (
                  <div className="px-6 py-16 text-center">
                    <p className="text-sm text-muted mono-data">No positions found.</p>
                    <p className="text-xs text-muted-foreground mt-2">Trades will appear here once recorded.</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <div className="min-w-[640px]">
                      <div className="grid grid-cols-12 gap-3 px-6 py-3 border-b border-border/50 text-xs text-muted-foreground mono-data tracking-wider">
                        <div className="col-span-3">INSTRUMENT</div>
                        <div className="col-span-2">DIRECTION</div>
                        <div className="col-span-2 text-right">ENTRY</div>
                        <div className="col-span-2 text-right">EXIT</div>
                        <div className="col-span-2 text-right">P&L</div>
                        <div className="col-span-1 text-right">STATUS</div>
                      </div>
                      <div className="divide-y divide-border/30 max-h-[480px] overflow-y-auto">
                        {trades.map((trade) => (
                          <div key={trade.id} className="grid grid-cols-12 gap-3 px-6 py-3.5 items-center transition-all duration-300 card-hover">
                            <div className="col-span-3">
                              <span className="text-sm text-white font-medium mono-data">{trade.instrument}</span>
                            </div>
                            <div className="col-span-2">
                              <span className={cn(
                                "text-xs font-bold mono-data tracking-wider px-2 py-1 border rounded-md",
                                trade.direction === "buy"
                                  ? "text-profit border-profit/30"
                                  : "text-loss border-loss/30"
                              )}>
                                {trade.direction.toUpperCase()}
                              </span>
                            </div>
                            <div className="col-span-2 text-right">
                              <span className="text-sm text-white mono-data">
                                {trade.entry_price != null ? `$${Number(trade.entry_price).toFixed(2)}` : "—"}
                              </span>
                            </div>
                            <div className="col-span-2 text-right">
                              <span className="text-sm text-muted mono-data">
                                {trade.exit_price != null ? `$${Number(trade.exit_price).toFixed(2)}` : "—"}
                              </span>
                            </div>
                            <div className="col-span-2 text-right">
                              <span className={cn(
                                "text-sm mono-data font-medium",
                                Number(trade.pnl) >= 0 ? "text-profit" : "text-loss"
                              )}>
                                {Number(trade.pnl) >= 0 ? "+" : ""}${Number(trade.pnl).toFixed(2)}
                              </span>
                            </div>
                            <div className="col-span-1 text-right">
                              <StatusBadge
                                status={trade.closed_at ? "neutral" : "success"}
                                label={trade.closed_at ? "CLOSED" : "OPEN"}
                              />
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ── AI Signals Tab ── */}
          {activeTab === "signals" && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-5">
                <DataCard
                  title="Total Signals"
                  value={String(insights.length)}
                  subtitle="Active AI insights"
                  trend="neutral"
                />
                <DataCard
                  title="Bullish Signals"
                  value={String(insights.filter((i) => i.sentiment != null && i.sentiment > 0).length)}
                  subtitle="Positive sentiment"
                  trend="up"
                />
                <DataCard
                  title="Bearish Signals"
                  value={String(insights.filter((i) => i.sentiment != null && i.sentiment < 0).length)}
                  subtitle="Negative sentiment"
                  trend="down"
                />
              </div>

              <div className="bg-card border border-border rounded-md">
                <div className="flex items-center justify-between px-6 py-4 border-b border-border">
                  <div className="flex items-center gap-3">
                    <h3 className="text-sm font-semibold tracking-wider text-muted uppercase mono-data">AI SIGNALS</h3>
                    <DataSourceBadge isUsingMock={insightsIsMock} isBackendOnline={isBackendOnline} />
                  </div>
                </div>
                <div className="divide-y divide-border/30 max-h-[480px] overflow-y-auto">
                  {insights.length === 0 && (
                    <div className="px-6 py-16 text-center">
                      <p className="text-sm text-muted mono-data">No AI signals available.</p>
                      <p className="text-xs text-muted-foreground mt-2">Signals will appear as the AI analyzes market data.</p>
                    </div>
                  )}
                  {insights.map((insight) => (
                    <div key={insight.id} className="px-6 py-4 flex gap-4 items-start card-hover transition-all duration-300">
                      <div className="shrink-0 mt-0.5">
                        <span className={cn(
                          "text-[11px] font-bold mono-data tracking-wider px-2 py-1 border rounded-md",
                          insight.sentiment != null && insight.sentiment > 0
                            ? "text-profit border-profit/30"
                            : insight.sentiment != null && insight.sentiment < 0
                              ? "text-loss border-loss/30"
                              : "text-muted border-border"
                        )}>
                          {insight.type.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white/90 leading-relaxed">{insight.content}</p>
                        <div className="flex items-center gap-3 mt-2">
                          <span className="text-xs text-muted-foreground mono-data">{insight.instrument}</span>
                          <span className="text-xs text-muted-foreground mono-data">{insight.time}</span>
                          {insight.sentiment != null && (
                            <span className={cn(
                              "text-xs mono-data font-medium",
                              insight.sentiment > 0 ? "text-profit" : insight.sentiment < 0 ? "text-loss" : "text-muted"
                            )}>
                              Sentiment: {insight.sentiment > 0 ? "+" : ""}{(insight.sentiment * 100).toFixed(0)}%
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

        </div>

        <DisclaimerBadge variant="footer" />
      </div>
    </AppShell>
  );
}

function QuickActionButton({ label, description, icon, highlight, onClick }: { label: string; description: string; icon: string; highlight?: boolean; onClick?: () => void }) {
  return (
    <button onClick={onClick} className={cn(
      "w-full flex items-center gap-4 p-4 rounded-md border transition-all text-left group",
      highlight
        ? "border-profit/30 bg-profit/5 hover:bg-profit/10 hover:border-profit/50"
        : "border-border bg-surface hover:bg-surface-hover hover:border-muted"
    )}>
      <span className="text-2xl">{icon}</span>
      <div>
        <span className={cn("text-sm font-semibold tracking-wider mono-data block", highlight ? "text-profit" : "text-white")}>{label}</span>
        <span className="text-xs text-muted-foreground mt-1 block">{description}</span>
      </div>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="ml-auto text-muted-foreground group-hover:text-white transition-colors">
        <path d="M9 18l6-6-6-6" />
      </svg>
    </button>
  );
}

function InsightItem({ type, text, time }: { type: "market" | "behavior" | "content"; text: string; time: string }) {
  const colorMap = { market: "text-accent border-accent/30", behavior: "text-warning border-warning/30", content: "text-cyan border-cyan/30" };
  const labelMap = { market: "MKT", behavior: "BHV", content: "CTN" };
  return (
    <div className="flex gap-3.5 items-start">
      <span className={cn("text-[11px] font-bold mono-data tracking-wider mt-0.5 px-2 py-1 border rounded-md shrink-0", colorMap[type])}>{labelMap[type]}</span>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-muted leading-relaxed">{text}</p>
        <span className="text-xs text-muted-foreground mono-data mt-1 block">{time}</span>
      </div>
    </div>
  );
}
