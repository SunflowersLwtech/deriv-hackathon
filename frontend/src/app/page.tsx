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

export default function DashboardPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("overview");
  const [isRefreshingInsights, setIsRefreshingInsights] = useState(false);
  const { data: metrics, isUsingMock: metricsIsMock, isBackendOnline } = useDashboardMetrics();
  const { data: insights, isUsingMock: insightsIsMock, refetch: refetchInsights } = useMarketInsights();

  const handleRefreshInsights = async () => {
    setIsRefreshingInsights(true);
    try {
      // Call the refresh endpoint to generate new insights
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/market/insights/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ limit: 8, max_insights: 5 }),
      });

      if (response.ok) {
        // Refetch the insights list
        await refetchInsights?.();
      }
    } catch (error) {
      console.error('Failed to refresh insights:', error);
    } finally {
      setIsRefreshingInsights(false);
    }
  };

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

            <div className="bg-card border border-border rounded-md overflow-hidden h-fit">
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-border">
                <h3 className="text-xs font-semibold tracking-wider text-muted uppercase mono-data">
                  RECENT AI INSIGHTS
                </h3>
                <div className="flex items-center gap-2">
                  <DataSourceBadge isUsingMock={insightsIsMock} />
                  <button
                    onClick={handleRefreshInsights}
                    disabled={isRefreshingInsights}
                    className={cn(
                      "px-2 py-1 text-[10px] font-medium tracking-wider mono-data rounded-sm transition-colors",
                      "border border-accent/30 text-accent hover:bg-accent/10",
                      isRefreshingInsights && "opacity-50 cursor-not-allowed"
                    )}
                    title="Generate fresh insights from latest news"
                  >
                    {isRefreshingInsights ? "REFRESHING..." : "REFRESH"}
                  </button>
                </div>
              </div>
              <div className="h-[200px] overflow-y-auto scrollbar-thin scrollbar-thumb-border scrollbar-track-surface">
                <div className="p-3 space-y-2.5">
                  {insights.length === 0 ? (
                    <div className="text-sm text-muted text-center py-4">
                      No insights available. Click REFRESH to generate insights from latest news.
                    </div>
                  ) : (
                    insights.map((insight) => {
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
                    })
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        <MarketOverview />
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
