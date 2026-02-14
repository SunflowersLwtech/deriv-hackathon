"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import { usePageState } from "@/hooks/usePageState";
import DataCard from "@/components/ui/DataCard";
import DisclaimerBadge from "@/components/ui/DisclaimerBadge";
import LoadingDots from "@/components/ui/LoadingDots";
import { useDerivAuth } from "@/hooks/useDerivAuth";
import api, {
  type CopyTrader,
  type TraderStatsResponse,
  type TraderRecommendationResponse,
} from "@/lib/api";

export default function CopyTradingPage() {
  const { isConnected, defaultAccount, connect, isLoading: authLoading } = useDerivAuth();
  const isReal = isConnected && defaultAccount?.account_type === "real";

  const [traders, setTraders] = usePageState<CopyTrader[]>("copy:traders", []);
  const [shownCount, setShownCount] = usePageState("copy:shownCount", 0);
  const [totalCount, setTotalCount] = usePageState("copy:totalCount", 0);
  const [loading, setLoading] = useState(() => traders.length === 0);
  const [selectedTrader, setSelectedTrader] = usePageState<string | null>("copy:selectedTrader", null);
  const [traderStats, setTraderStats] = usePageState<TraderStatsResponse | null>("copy:traderStats", null);
  const [statsLoading, setStatsLoading] = useState(false);
  const [recommendation, setRecommendation] = usePageState<TraderRecommendationResponse | null>("copy:recommendation", null);
  const [recLoading, setRecLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dataSource, setDataSource] = usePageState<string>("copy:source", "");

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
        setDataSource(resp.source || "");
        if (resp.api_error) {
          setError(`Live data unavailable: ${resp.api_error}`);
        }
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
      // Backend auto-detects user from auth token; pass placeholder
      // that will be overridden server-side for authenticated users.
      const rec = await api.getTraderRecommendation("auto");
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
            {/* Account mode badge */}
            {!authLoading && (
              isReal ? (
                <span className="px-3 py-1 text-xs font-bold tracking-wider bg-profit/20 text-profit border border-profit/30 rounded-full">
                  REAL ACCOUNT
                </span>
              ) : isConnected ? (
                <span className="px-3 py-1 text-xs font-bold tracking-wider bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded-full">
                  DEMO ACCOUNT
                </span>
              ) : (
                <span className="px-3 py-1 text-xs font-bold tracking-wider bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 rounded-full">
                  DEMO ONLY
                </span>
              )
            )}
            <button
              onClick={handleGetRecommendation}
              disabled={recLoading}
              className="px-4 py-2 text-xs font-medium tracking-wider bg-surface hover:bg-surface-hover text-white border border-border rounded-md transition-colors disabled:opacity-50"
            >
              {recLoading ? "ANALYZING..." : "AI MATCH"}
            </button>
          </div>
        </div>

        {/* Connect CTA for unauthenticated users */}
        {!authLoading && !isConnected && (
          <div className="p-4 bg-surface border border-border rounded-lg flex items-center justify-between">
            <div>
              <p className="text-white text-sm font-medium">
                Connect your Deriv account to copy real traders
              </p>
              <p className="text-muted text-xs mt-1">
                Link your account to use your own token for live copy trading data and actions.
              </p>
            </div>
            <button
              onClick={connect}
              className="px-4 py-2 text-xs font-bold tracking-wider bg-profit/20 text-profit border border-profit/30 rounded-md hover:bg-profit/30 transition-colors whitespace-nowrap"
            >
              CONNECT DERIV
            </button>
          </div>
        )}

        {/* Real account warning */}
        {isReal && (
          <div className="p-3 bg-profit/5 border border-profit/20 rounded-md">
            <p className="text-profit text-xs font-medium">
              Real Account -- Real Copy Trading. Actions here use your real Deriv account.
              Start/stop copy trading will affect real funds.
            </p>
          </div>
        )}

        {/* Demo data source notice */}
        {dataSource === "demo_fallback" && isConnected && (
          <div className="p-3 bg-warning/5 border border-warning/20 rounded-md">
            <p className="text-warning text-xs font-medium">
              Showing demo traders. Your account is connected but live copy trading data is currently unavailable.
            </p>
          </div>
        )}

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
              <>
              {/* All stats in a single grid for perfect column alignment */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-x-4 gap-y-5">
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
                  <div className="text-xs text-muted uppercase">Performance</div>
                  <div className="text-lg font-bold mono-data text-profit">
                    {((traderStats.stats.performance_probability || 0) * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
              </>
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
          {isReal
            ? " You are using a Real account. Actions affect real funds."
            : " This is a Demo account feature for educational purposes only."
          }{" "}
          Not financial advice.
        </p>
      </div>
    </AppShell>
  );
}
