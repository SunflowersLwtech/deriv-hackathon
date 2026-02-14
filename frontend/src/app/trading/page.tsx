"use client";

import { useEffect, useState, useCallback } from "react";
import AppShell from "@/components/layout/AppShell";
import DataCard from "@/components/ui/DataCard";
import DisclaimerBadge from "@/components/ui/DisclaimerBadge";
import LoadingDots from "@/components/ui/LoadingDots";
import api, {
  type ContractQuoteResponse,
  type OpenPosition,
} from "@/lib/api";

const INSTRUMENTS = [
  "Volatility 100 Index",
  "Volatility 75 Index",
  "Volatility 50 Index",
  "Volatility 25 Index",
  "BTC/USD",
  "ETH/USD",
  "EUR/USD",
  "GBP/USD",
];

export default function TradingPage() {
  const [instrument, setInstrument] = useState(INSTRUMENTS[0]);
  const [contractType, setContractType] = useState<"CALL" | "PUT">("CALL");
  const [amount, setAmount] = useState(10);
  const [duration, setDuration] = useState(5);
  const [durationUnit, setDurationUnit] = useState("t");

  const [quote, setQuote] = useState<ContractQuoteResponse | null>(null);
  const [quoteLoading, setQuoteLoading] = useState(false);
  const [tradeLoading, setTradeLoading] = useState(false);
  const [tradeResult, setTradeResult] = useState<string | null>(null);

  const [positions, setPositions] = useState<OpenPosition[]>([]);
  const [positionsLoading, setPositionsLoading] = useState(false);

  const [error, setError] = useState<string | null>(null);

  const loadPositions = useCallback(async () => {
    setPositionsLoading(true);
    try {
      const resp = await api.getOpenPositions();
      setPositions(resp.positions || []);
    } catch {
      // silent
    } finally {
      setPositionsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadPositions();
    const interval = setInterval(loadPositions, 10000);
    return () => clearInterval(interval);
  }, [loadPositions]);

  const handleGetQuote = async () => {
    setQuoteLoading(true);
    setError(null);
    setTradeResult(null);
    try {
      const resp = await api.getContractQuote(instrument, contractType, amount, duration, durationUnit);
      if (resp.error) {
        setError(resp.error);
        setQuote(null);
      } else {
        setQuote(resp);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to get quote");
      setQuote(null);
    } finally {
      setQuoteLoading(false);
    }
  };

  const handleExecuteTrade = async () => {
    if (!quote) return;
    setTradeLoading(true);
    setError(null);
    try {
      // Use quote_and_buy: send contract params so backend does proposal+buy in one WS session
      const resp = await api.executeDemoTrade(instrument, contractType, amount, duration, durationUnit);
      if (resp.error) {
        setError(resp.error);
      } else {
        setTradeResult(`Trade executed! Contract #${resp.contract_id} — Buy price: $${resp.buy_price.toFixed(2)}`);
        setQuote(null);
        loadPositions();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Trade execution failed");
    } finally {
      setTradeLoading(false);
    }
  };

  const handleClosePosition = async (contractId: number) => {
    try {
      const resp = await api.closeDemoPosition(contractId);
      if (resp.error) {
        setError(resp.error);
      } else {
        setTradeResult(`Closed #${contractId} — Sold for $${resp.sold_for.toFixed(2)}, Profit: $${resp.profit.toFixed(2)}`);
        loadPositions();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to close position");
    }
  };

  return (
    <AppShell>
      <div className="p-6 space-y-6 max-w-5xl mx-auto">
        {/* Demo Banner */}
        <div className="w-full p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg text-center">
          <span className="text-yellow-400 font-bold tracking-wider text-sm">
            DEMO ACCOUNT — Virtual money only. No real funds at risk.
          </span>
        </div>

        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide">DEMO TRADING</h1>
          <p className="text-muted text-sm mt-1">
            Learn how Deriv contracts work with virtual money
          </p>
        </div>

        {/* Contract Selector */}
        <DataCard title="Contract Setup">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Instrument */}
            <div>
              <label className="block text-xs text-muted uppercase tracking-wider mb-2">Instrument</label>
              <select
                value={instrument}
                onChange={(e) => setInstrument(e.target.value)}
                className="w-full bg-surface border border-border rounded-md px-3 py-2 text-white text-sm mono-data focus:outline-none focus:ring-1 focus:ring-white/20"
              >
                {INSTRUMENTS.map((inst) => (
                  <option key={inst} value={inst}>{inst}</option>
                ))}
              </select>
            </div>

            {/* Contract Type Toggle */}
            <div>
              <label className="block text-xs text-muted uppercase tracking-wider mb-2">Direction</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setContractType("CALL")}
                  className={`flex-1 py-2 text-sm font-bold tracking-wider rounded-md transition-colors ${
                    contractType === "CALL"
                      ? "bg-profit text-black"
                      : "bg-surface text-muted border border-border hover:text-white"
                  }`}
                >
                  CALL (Rise)
                </button>
                <button
                  onClick={() => setContractType("PUT")}
                  className={`flex-1 py-2 text-sm font-bold tracking-wider rounded-md transition-colors ${
                    contractType === "PUT"
                      ? "bg-loss text-white"
                      : "bg-surface text-muted border border-border hover:text-white"
                  }`}
                >
                  PUT (Fall)
                </button>
              </div>
            </div>

            {/* Stake */}
            <div>
              <label className="block text-xs text-muted uppercase tracking-wider mb-2">Stake (USD)</label>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(Number(e.target.value))}
                min={1}
                max={1000}
                className="w-full bg-surface border border-border rounded-md px-3 py-2 text-white text-sm mono-data focus:outline-none focus:ring-1 focus:ring-white/20"
              />
            </div>

            {/* Duration */}
            <div>
              <label className="block text-xs text-muted uppercase tracking-wider mb-2">Duration</label>
              <div className="flex gap-2">
                <input
                  type="number"
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                  min={1}
                  max={60}
                  className="flex-1 bg-surface border border-border rounded-md px-3 py-2 text-white text-sm mono-data focus:outline-none focus:ring-1 focus:ring-white/20"
                />
                <select
                  value={durationUnit}
                  onChange={(e) => setDurationUnit(e.target.value)}
                  className="bg-surface border border-border rounded-md px-3 py-2 text-white text-sm mono-data focus:outline-none focus:ring-1 focus:ring-white/20"
                >
                  <option value="t">Ticks</option>
                  <option value="s">Seconds</option>
                  <option value="m">Minutes</option>
                  <option value="h">Hours</option>
                </select>
              </div>
            </div>
          </div>

          {/* Get Quote Button */}
          <div className="mt-4">
            <button
              onClick={handleGetQuote}
              disabled={quoteLoading}
              className="w-full py-3 text-sm font-bold tracking-wider bg-white text-black rounded-md hover:bg-gray-200 transition-colors disabled:opacity-50"
            >
              {quoteLoading ? "GETTING QUOTE..." : "GET QUOTE"}
            </button>
          </div>
        </DataCard>

        {/* Error */}
        {error && (
          <div className="p-4 bg-loss/10 border border-loss/30 rounded-md text-loss text-sm">
            {error}
          </div>
        )}

        {/* Trade Result */}
        {tradeResult && (
          <div className="p-4 bg-profit/10 border border-profit/30 rounded-md text-profit text-sm">
            {tradeResult}
          </div>
        )}

        {/* Quote Display */}
        {quote && (
          <DataCard title="Contract Quote">
            <div className="space-y-4">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-xs text-muted uppercase">Ask Price</div>
                  <div className="text-xl font-bold mono-data text-white">${quote.ask_price.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-xs text-muted uppercase">Payout</div>
                  <div className="text-xl font-bold mono-data text-profit">${quote.payout.toFixed(2)}</div>
                </div>
                <div>
                  <div className="text-xs text-muted uppercase">Spot Price</div>
                  <div className="text-lg font-bold mono-data text-white">{quote.spot}</div>
                </div>
                <div>
                  <div className="text-xs text-muted uppercase">Contract</div>
                  <div className="text-sm mono-data text-muted">{quote.contract_type}</div>
                </div>
              </div>

              <p className="text-xs text-muted border-t border-border pt-3">{quote.longcode}</p>

              <button
                onClick={handleExecuteTrade}
                disabled={tradeLoading}
                className={`w-full py-3 text-sm font-bold tracking-wider rounded-md transition-colors disabled:opacity-50 ${
                  contractType === "CALL"
                    ? "bg-profit text-black hover:bg-profit/80"
                    : "bg-loss text-white hover:bg-loss/80"
                }`}
              >
                <span className="inline-flex items-center gap-2">
                  {tradeLoading ? "EXECUTING..." : "EXECUTE DEMO TRADE"}
                  <span className="px-2 py-0.5 text-[10px] bg-black/20 rounded">DEMO</span>
                </span>
              </button>
            </div>
          </DataCard>
        )}

        {/* Open Positions */}
        <DataCard title={`Open Positions (${positions.length})`}>
          {positionsLoading && positions.length === 0 ? (
            <LoadingDots />
          ) : positions.length === 0 ? (
            <p className="text-muted text-sm text-center py-4">No open positions.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-xs text-muted uppercase tracking-wider border-b border-border">
                    <th className="text-left py-2 px-2">ID</th>
                    <th className="text-left py-2 px-2">Instrument</th>
                    <th className="text-left py-2 px-2">Type</th>
                    <th className="text-right py-2 px-2">Buy</th>
                    <th className="text-right py-2 px-2">Current</th>
                    <th className="text-right py-2 px-2">P&L</th>
                    <th className="text-right py-2 px-2">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {positions.map((pos) => (
                    <tr key={pos.contract_id} className="border-b border-border/50 hover:bg-surface/50">
                      <td className="py-2 px-2 mono-data text-white">{pos.contract_id}</td>
                      <td className="py-2 px-2 text-muted">{pos.instrument}</td>
                      <td className="py-2 px-2">
                        <span className={`text-xs font-bold ${pos.contract_type === "CALL" ? "text-profit" : "text-loss"}`}>
                          {pos.contract_type}
                        </span>
                      </td>
                      <td className="py-2 px-2 text-right mono-data text-white">${pos.buy_price.toFixed(2)}</td>
                      <td className="py-2 px-2 text-right mono-data text-white">{pos.current_spot}</td>
                      <td className={`py-2 px-2 text-right mono-data font-bold ${pos.profit >= 0 ? "text-profit" : "text-loss"}`}>
                        ${pos.profit.toFixed(2)}
                      </td>
                      <td className="py-2 px-2 text-right">
                        {pos.is_valid_to_sell && (
                          <button
                            onClick={() => handleClosePosition(pos.contract_id)}
                            className="px-3 py-1 text-xs font-bold tracking-wider bg-surface hover:bg-surface-hover text-white border border-border rounded transition-colors"
                          >
                            CLOSE
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </DataCard>

        {/* Disclaimer */}
        <div className="flex justify-center pt-4">
          <DisclaimerBadge />
        </div>
        <p className="text-center text-xs text-muted max-w-2xl mx-auto">
          This is a Demo account using virtual money. No real funds are at risk.
          Trading involves risk. This is for educational purposes only. Not financial advice.
        </p>
      </div>
    </AppShell>
  );
}
