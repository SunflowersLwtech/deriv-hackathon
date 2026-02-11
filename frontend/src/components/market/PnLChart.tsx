"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
} from "recharts";
import { cn } from "@/lib/utils";
import api from "@/lib/api";

interface DataPoint {
  time: string;
  value: number;
}

interface PnLChartProps {
  className?: string;
  title?: string;
  height?: number;
  instrument?: string;
  timeframe?: string;
}

function formatTimeLabel(isoOrDate: string | Date): string {
  const date = typeof isoOrDate === "string" ? new Date(isoOrDate) : isoOrDate;
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export default function PnLChart({
  className,
  title = "PORTFOLIO PnL",
  height = 300,
  instrument,
  timeframe = "1h",
}: PnLChartProps) {
  const [data, setData] = useState<DataPoint[]>([]);
  const [hoveredValue, setHoveredValue] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function fetchPriceChart(symbol: string, tf: string): Promise<DataPoint[]> {
      const history = await api.getMarketHistory(symbol, tf, 120);
      return (history.candles || []).map((candle) => ({
        time: formatTimeLabel(candle.time),
        value: Number(candle.close || 0),
      }));
    }

    const fetchData = async () => {
      setIsLoading(true);
      try {
        if (instrument) {
          const chartData = await fetchPriceChart(instrument, timeframe);
          if (!cancelled && chartData.length > 0) {
            setData(chartData);
          }
        } else {
          // Try loading cumulative PnL from trades
          let hasTrades = false;
          try {
            const tradesResp = await api.getTrades();
            const trades = Array.isArray(tradesResp) ? tradesResp : tradesResp.results || [];
            if (trades.length > 0) {
              hasTrades = true;
              const sorted = [...trades].sort((a, b) => {
                const at = new Date(a.opened_at || a.created_at || Date.now()).getTime();
                const bt = new Date(b.opened_at || b.created_at || Date.now()).getTime();
                return at - bt;
              });
              let cumulative = 0;
              const points = sorted.map((trade) => {
                cumulative += Number(trade.pnl || 0);
                const timestamp = trade.opened_at || trade.created_at || new Date().toISOString();
                return {
                  time: formatTimeLabel(timestamp),
                  value: Number(cumulative.toFixed(2)),
                };
              });
              if (!cancelled) setData(points);
            }
          } catch {
            // getTrades failed (backend cold start, timeout, etc.) — fall through to price chart
          }

          // No trades or getTrades failed → show EUR/USD price chart
          if (!hasTrades && !cancelled) {
            try {
              const chartData = await fetchPriceChart("frxEURUSD", "1h");
              if (!cancelled && chartData.length > 0) {
                setData(chartData);
              }
            } catch {
              // getMarketHistory also failed — keep existing data (don't overwrite with [])
            }
          }
        }
      } catch {
        // Inner try/catches handle individual failures — nothing else to do here
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    };

    fetchData();
    const interval = setInterval(fetchData, instrument ? 15000 : 30000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [instrument, timeframe]);

  const currentValue = hoveredValue ?? data[data.length - 1]?.value ?? 0;
  const startValue = data[0]?.value ?? 0;
  const pnl = currentValue - startValue;
  const pnlPercent = startValue !== 0 ? (pnl / Math.abs(startValue)) * 100 : 0;
  const isPositive = pnl >= 0;
  const chartColor = isPositive ? "#4ade80" : "#f87171";

  const chartBody = useMemo(() => {
    if (isLoading) {
      return <div className="text-xs text-muted mono-data py-16 text-center">Loading live chart data...</div>;
    }
    if (data.length === 0) {
      return <div className="text-xs text-muted mono-data py-16 text-center">No chart data available.</div>;
    }

    return (
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart
          data={data}
          onMouseMove={(e: Record<string, unknown>) => {
            const payload = e?.activePayload as Array<{ value: number }> | undefined;
            if (payload?.[0]) {
              setHoveredValue(payload[0].value);
            }
          }}
          onMouseLeave={() => setHoveredValue(null)}
        >
          <defs>
            <linearGradient id="pnlGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={chartColor} stopOpacity={0.3} />
              <stop offset="100%" stopColor={chartColor} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
          <XAxis
            dataKey="time"
            tick={{ fontSize: 11, fill: "#71717a", fontFamily: "JetBrains Mono, monospace" }}
            axisLine={{ stroke: "#27272a" }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#71717a", fontFamily: "JetBrains Mono, monospace" }}
            axisLine={false}
            tickLine={false}
            domain={["auto", "auto"]}
            tickFormatter={(v) => Number(v).toFixed(2)}
          />
          <Tooltip
            contentStyle={{
              background: "#0a0a0a",
              border: "1px solid #27272a",
              borderRadius: "6px",
              fontSize: "12px",
              fontFamily: "JetBrains Mono, monospace",
              color: "#ffffff",
              padding: "8px 12px",
            }}
            formatter={(value: number | undefined) => [Number(value ?? 0).toFixed(2), "Value"]}
          />
          <Area
            type="monotone"
            dataKey="value"
            stroke={chartColor}
            strokeWidth={1.5}
            fill="url(#pnlGradient)"
            dot={false}
            activeDot={{
              r: 3,
              stroke: chartColor,
              strokeWidth: 2,
              fill: "#000000",
            }}
          />
        </AreaChart>
      </ResponsiveContainer>
    );
  }, [isLoading, data, height, chartColor]);

  return (
    <div className={cn("bg-card border border-border rounded-md p-6", className)}>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h3 className="text-xs font-semibold tracking-wider text-muted uppercase mono-data">{title}</h3>
          <div className="flex items-baseline gap-3 mt-2">
            <span className="text-3xl font-bold mono-data text-white">
              {currentValue.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 4 })}
            </span>
            <span
              className={cn(
                "text-base mono-data font-semibold",
                isPositive ? "text-profit glow-green" : "text-loss glow-red"
              )}
            >
              {isPositive ? "+" : ""}
              {pnl.toFixed(2)} ({pnlPercent.toFixed(2)}%)
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className={cn("w-2.5 h-2.5 rounded-full", isPositive ? "bg-profit" : "bg-loss")} />
          <span className="text-xs text-muted mono-data">LIVE</span>
        </div>
      </div>

      {chartBody}
    </div>
  );
}
