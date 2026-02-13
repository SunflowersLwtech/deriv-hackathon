"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import DataCard from "@/components/ui/DataCard";
import DisclaimerBadge from "@/components/ui/DisclaimerBadge";
import LoadingDots from "@/components/ui/LoadingDots";
import api, {
  type CopyTrader,
  type TraderStatsResponse,
  type TraderRecommendationResponse,
} from "@/lib/api";

export default function CopyTradingPage() {
  const [traders, setTraders] = useState<CopyTrader[]>([]);
  const [shownCount, setShownCount] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedTrader, setSelectedTrader] = useState<string | null>(null);
  const [traderStats, setTraderStats] = useState<TraderStatsResponse | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);
  const [recommendation, setRecommendation] = useState<TraderRecommendationResponse | null>(null);
  const [recLoading, setRecLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTraders = async () => {
      try {
        const resp = await api.getCopyTraders(10);
        const nextTraders = resp.traders || [];
        const nextCount = resp.count ?? nextTraders.length;
        const nextTotalCount = resp.total_count ?? nextCount;
        setTraders(nextTraders);
        setShownCount(nextCount);
        setTotalCount(nextTotalCount);
      } catch (err) {
        setTraders([]);
        setShownCount(0);
        setTotalCount(0);
        setError(err instanceof Error ? err.message : "Failed to load traders");
      } finally {
        setLoading(false);
      }
    };
    loadTraders();
  }, []);

  const handleSelectTrader = async (traderId: string) => {
    setSelectedTrader(traderId);
    setStatsLoading(true);
    try {
      const stats = await api.getTraderStats(traderId);
      setTraderStats(stats);
    } catch {
      setTraderStats(null);
    } finally {
      setStatsLoading(false);
    }
  };

  const handleGetRecommendation = async () => {
    setRecLoading(true);
    try {
      const rec = await api.getTraderRecommendation("d1000000-0000-0000-0000-000000000001");
      setRecommendation(rec);
    } catch {
      setRecommendation(null);
    } finally {
      setRecLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white tracking-wide">COPY TRADING</h1>
            <p className="text-muted text-sm mt-1">
              Explore top traders and learn how copy trading works on Deriv
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 text-xs font-bold tracking-wider bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 rounded-full">
              DEMO ONLY
            </span>
            <button
              onClick={handleGetRecommendation}
              disabled={recLoading}
              className="px-4 py-2 text-xs font-medium tracking-wider bg-surface hover:bg-surface-hover text-white border border-border rounded-md transition-colors disabled:opacity-50"
            >
              {recLoading ? "ANALYZING..." : "AI MATCH"}
            </button>
          </div>
        </div>

        {/* AI Recommendation Panel */}
        {recommendation && (
          <DataCard title="AI Compatibility Match">
            <div className="space-y-3">
              {recommendation.recommendations?.map((rec, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-surface rounded-md border border-border">
                  <div>
                    <span className="text-white font-mono text-sm">{rec.trader?.loginid || "Unknown"}</span>
                    <div className="text-xs text-muted mt-1">
                      {rec.reasons?.slice(0, 2).join(" · ") || "No details"}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-profit font-bold mono-data">
                      {((rec.compatibility_score || 0) * 100).toFixed(0)}%
                    </div>
                    <div className="text-xs text-muted">match</div>
                  </div>
                </div>
              ))}
              <p className="text-xs text-muted">{recommendation.disclaimer}</p>
            </div>
          </DataCard>
        )}

        {/* Error */}
        {error && (
          <div className="p-4 bg-loss/10 border border-loss/30 rounded-md text-loss text-sm">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <LoadingDots />
          </div>
        )}

        {/* Trader Grid */}
        {!loading && (
          <div className="space-y-3">
            <p className="text-xs text-muted mono-data">
              Showing {shownCount} of {totalCount} traders
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {traders.map((trader) => (
                <button
                  key={trader.loginid}
                  onClick={() => handleSelectTrader(trader.loginid)}
                  className={`text-left p-4 bg-card border rounded-lg transition-all hover:border-white/30 ${
                    selectedTrader === trader.loginid
                      ? "border-profit ring-1 ring-profit/20"
                      : "border-border"
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-white font-mono text-sm font-bold">{trader.loginid}</span>
                    <span className="text-xs text-muted">{trader.copiers || 0} copiers</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <div className="text-xs text-muted uppercase tracking-wider">Performance</div>
                      <div className={`text-sm font-bold mono-data ${
                        (trader.performance_probability || 0) >= 0.5 ? "text-profit" : "text-loss"
                      }`}>
                        {((trader.performance_probability || 0) * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted uppercase tracking-wider">Avg Profit</div>
                      <div className={`text-sm font-bold mono-data ${
                        (trader.avg_profit || 0) >= 0 ? "text-profit" : "text-loss"
                      }`}>
                        ${(trader.avg_profit || 0).toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-muted uppercase tracking-wider">Total Trades</div>
                      <div className="text-sm font-bold mono-data text-white">{trader.total_trades || 0}</div>
                    </div>
                    <div>
                      <div className="text-xs text-muted uppercase tracking-wider">Min Stake</div>
                      <div className="text-sm font-bold mono-data text-white">
                        ${(trader.min_trade_stake || 0).toFixed(2)}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Trader Details Panel */}
        {selectedTrader && (
          <DataCard title={`Trader: ${selectedTrader}`}>
            {statsLoading ? (
              <LoadingDots />
            ) : traderStats?.stats ? (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <div className="text-xs text-muted uppercase">Total Trades</div>
                  <div className="text-lg font-bold mono-data text-white">{traderStats.stats.total_trades}</div>
                </div>
                <div>
                  <div className="text-xs text-muted uppercase">Avg Profit</div>
                  <div className={`text-lg font-bold mono-data ${traderStats.stats.avg_profit >= 0 ? "text-profit" : "text-loss"}`}>
                    ${traderStats.stats.avg_profit.toFixed(2)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-muted uppercase">Copiers</div>
                  <div className="text-lg font-bold mono-data text-white">{traderStats.stats.copiers}</div>
                </div>
                <div>
                  <div className="text-xs text-muted uppercase">Monthly Profitable</div>
                  <div className="text-lg font-bold mono-data text-profit">{traderStats.stats.monthly_profitable_trades}</div>
                </div>
                <div>
                  <div className="text-xs text-muted uppercase">Active Since</div>
                  <div className="text-sm font-bold mono-data text-white">{traderStats.stats.active_since || "N/A"}</div>
                </div>
                <div>
                  <div className="text-xs text-muted uppercase">Performance</div>
                  <div className="text-lg font-bold mono-data text-profit">
                    {((traderStats.stats.performance_probability || 0) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-muted text-sm">No stats available.</p>
            )}
          </DataCard>
        )}

        {/* Disclaimer */}
        <div className="flex justify-center pt-4">
          <DisclaimerBadge />
        </div>
        <p className="text-center text-xs text-muted max-w-2xl mx-auto">
          Past performance does not guarantee future results. Copy trading involves risk.
          This is a Demo account feature for educational purposes only. Not financial advice.
        </p>
      </div>
    </AppShell>
  );
}
