"use client";

import { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { useTradingTwin } from "@/hooks/useTradingTwin";
import type { TradingTwinResult, TwinPoint } from "@/lib/api";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
  ReferenceDot,
} from "recharts";

interface TradingTwinChartProps {
  userId?: string;
  compact?: boolean;
}

export default function TradingTwinChart({
  userId,
  compact = false,
}: TradingTwinChartProps) {
  const { twinData, isLoading, error, generateTwin } = useTradingTwin(userId);
  const [days, setDays] = useState(30);
  const [animatedDiff, setAnimatedDiff] = useState(0);
  const animRef = useRef<ReturnType<typeof requestAnimationFrame>>();

  // Count-up animation for difference
  useEffect(() => {
    if (!twinData) return;
    const target = Math.abs(twinData.equity_difference);
    const duration = 2000;
    const start = performance.now();

    const tick = (now: number) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedDiff(Math.round(target * eased * 100) / 100);
      if (progress < 1) {
        animRef.current = requestAnimationFrame(tick);
      }
    };

    animRef.current = requestAnimationFrame(tick);
    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
    };
  }, [twinData]);

  // Prepare chart data
  const chartData = twinData?.equity_curve.map((pt, i) => ({
    index: i,
    time: new Date(pt.timestamp).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
    }),
    impulsive: pt.impulsive_equity,
    disciplined: pt.disciplined_equity,
    isImpulsive: pt.is_impulsive,
    pattern: pt.pattern,
  })) ?? [];

  const dayOptions = [7, 14, 30, 90];

  if (error) {
    return (
      <div className="rounded-lg border border-loss/30 bg-loss/5 p-4">
        <p className="text-sm text-loss mono-data">{error}</p>
        <button
          onClick={() => generateTwin(days)}
          className="mt-2 text-xs text-muted-foreground underline"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!twinData && !isLoading) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6 text-center">
        <div className="mb-3">
          <span className="text-2xl">🔮</span>
        </div>
        <h3 className="text-sm font-bold text-white mb-1 mono-data tracking-wider">
          TRADING TWIN
        </h3>
        <p className="text-xs text-muted-foreground mb-4">
          See what discipline looks like — your impulsive self vs your
          disciplined self.
        </p>

        <div className="flex justify-center gap-2 mb-4">
          {dayOptions.map((d) => (
            <button
              key={d}
              onClick={() => setDays(d)}
              className={cn(
                "px-3 py-1 rounded text-xs mono-data",
                d === days
                  ? "bg-cyan/20 text-cyan border border-cyan/30"
                  : "bg-surface border border-border text-muted-foreground hover:text-white"
              )}
            >
              {d}D
            </button>
          ))}
        </div>

        <button
          onClick={() => generateTwin(days)}
          className="px-6 py-2.5 rounded-md bg-white text-black text-xs font-bold tracking-wider hover:bg-gray-200 transition-all"
        >
          GENERATE YOUR TRADING TWIN
        </button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6 text-center animate-pulse">
        <div className="flex justify-center gap-1 mb-3">
          <div className="w-2 h-2 rounded-full bg-cyan animate-pulse" style={{ animationDelay: "0ms" }} />
          <div className="w-2 h-2 rounded-full bg-cyan animate-pulse" style={{ animationDelay: "150ms" }} />
          <div className="w-2 h-2 rounded-full bg-cyan animate-pulse" style={{ animationDelay: "300ms" }} />
        </div>
        <p className="text-xs text-muted-foreground mono-data">
          Analyzing {days} days of trades...
        </p>
      </div>
    );
  }

  if (twinData && twinData.total_trades < 5) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6 text-center">
        <p className="text-sm text-muted-foreground mb-2">
          {twinData.narrative}
        </p>
        <p className="text-xs text-cyan mono-data">{twinData.key_insight}</p>
      </div>
    );
  }

  const isPositive = twinData!.equity_difference > 0;

  if (compact) {
    return (
      <div className="rounded-lg border border-border bg-surface p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-bold tracking-wider mono-data text-white">
            TRADING TWIN
          </span>
          <span className={cn(
            "text-sm font-bold mono-data",
            isPositive ? "text-profit" : "text-loss"
          )}>
            {isPositive ? "+" : "-"}${animatedDiff.toLocaleString()}
          </span>
        </div>
        <div className="flex gap-4 text-xs text-muted-foreground mono-data">
          <span>
            Actual:{" "}
            <span className="text-white">
              ${twinData!.impulsive_final_equity.toLocaleString()}
            </span>
          </span>
          <span>
            Disciplined:{" "}
            <span className="text-profit">
              ${twinData!.disciplined_final_equity.toLocaleString()}
            </span>
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-surface overflow-hidden">
      {/* Header Stats */}
      <div className="p-4 border-b border-border/50">
        <div className="flex items-center gap-2 mb-3">
          <span className="text-xs font-bold tracking-wider mono-data text-white">
            TRADING TWIN
          </span>
          <span className="text-[10px] text-muted-foreground mono-data">
            {twinData!.analysis_period_days}D ANALYSIS
          </span>
        </div>

        <div className="grid grid-cols-3 gap-4">
          {/* Impulsive Path */}
          <div>
            <p className="text-[10px] text-muted-foreground mono-data mb-1">
              YOUR ACTUAL PATH
            </p>
            <p className="text-lg font-bold text-loss mono-data">
              ${twinData!.impulsive_final_equity.toLocaleString()}
            </p>
            <p className="text-[10px] text-loss mono-data">
              {((twinData!.impulsive_final_equity - 10000) / 100).toFixed(1)}%
            </p>
          </div>

          {/* Difference */}
          <div className="text-center">
            <p className="text-[10px] text-muted-foreground mono-data mb-1">
              DIFFERENCE
            </p>
            <p className={cn(
              "text-2xl font-bold mono-data",
              isPositive ? "text-profit" : "text-loss"
            )}>
              {isPositive ? "+" : "-"}${animatedDiff.toLocaleString()}
            </p>
            <p className={cn(
              "text-[10px] mono-data",
              isPositive ? "text-profit" : "text-loss"
            )}>
              {isPositive ? "+" : ""}{twinData!.equity_difference_pct.toFixed(1)}%
            </p>
          </div>

          {/* Disciplined Path */}
          <div className="text-right">
            <p className="text-[10px] text-muted-foreground mono-data mb-1">
              DISCIPLINED PATH
            </p>
            <p className="text-lg font-bold text-profit mono-data">
              ${twinData!.disciplined_final_equity.toLocaleString()}
            </p>
            <p className="text-[10px] text-profit mono-data">
              {((twinData!.disciplined_final_equity - 10000) / 100).toFixed(1)}%
            </p>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="p-4" style={{ height: 300 }}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData}>
            <defs>
              <linearGradient id="gapFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#22c55e" stopOpacity={0.15} />
                <stop offset="100%" stopColor="#22c55e" stopOpacity={0.02} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" />
            <XAxis
              dataKey="time"
              tick={{ fill: "#666", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tick={{ fill: "#666", fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v: number) => `$${(v / 1000).toFixed(1)}k`}
              domain={["auto", "auto"]}
            />
            <Tooltip
              contentStyle={{
                background: "#1a1a2e",
                border: "1px solid #333",
                borderRadius: 8,
                fontSize: 11,
              }}
              formatter={(value: number, name: string) => [
                `$${value.toLocaleString()}`,
                name === "disciplined" ? "Disciplined You" : "Impulsive You",
              ]}
            />
            <Area
              type="monotone"
              dataKey="disciplined"
              stroke="#22c55e"
              strokeWidth={2}
              fill="url(#gapFill)"
              dot={false}
              animationDuration={1500}
            />
            <Area
              type="monotone"
              dataKey="impulsive"
              stroke="#ef4444"
              strokeWidth={2}
              fill="transparent"
              dot={(props: Record<string, unknown>) => {
                const { cx, cy, payload } = props as {
                  cx: number;
                  cy: number;
                  payload: { isImpulsive: boolean };
                };
                if (payload?.isImpulsive) {
                  return (
                    <circle
                      cx={cx}
                      cy={cy}
                      r={4}
                      fill="#ef4444"
                      stroke="#ef444480"
                      strokeWidth={2}
                    />
                  );
                }
                return <></>;
              }}
              animationDuration={1500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="px-4 pb-2 flex items-center gap-4 text-[10px] text-muted-foreground mono-data">
        <div className="flex items-center gap-1">
          <div className="w-3 h-0.5 bg-[#ef4444] rounded" />
          <span>Impulsive You</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-3 h-0.5 bg-[#22c55e] rounded" />
          <span>Disciplined You</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-2 h-2 rounded-full bg-[#ef4444]" />
          <span>Impulse Trade</span>
        </div>
      </div>

      {/* Pattern Breakdown */}
      {Object.keys(twinData!.pattern_breakdown).length > 0 && (
        <div className="px-4 py-3 border-t border-border/30">
          <p className="text-[10px] text-muted-foreground mono-data mb-2 tracking-wider">
            BEHAVIOR PATTERNS DETECTED
          </p>
          <div className="flex flex-wrap gap-2">
            {Object.entries(twinData!.pattern_breakdown).map(([pattern, count]) => (
              <span
                key={pattern}
                className="px-2 py-1 rounded bg-loss/10 border border-loss/20 text-[10px] text-loss mono-data"
              >
                {_formatPattern(pattern)}: {count} trades
              </span>
            ))}
            <span className="px-2 py-1 rounded bg-surface border border-border text-[10px] text-muted-foreground mono-data">
              {twinData!.impulsive_trades} / {twinData!.total_trades} impulsive
            </span>
          </div>
        </div>
      )}

      {/* AI Narrative */}
      <div className="px-4 py-4 border-t border-border/30 bg-surface/50">
        <p className="text-sm text-muted leading-relaxed mb-2">
          {twinData!.narrative}
        </p>
        <p className="text-xs text-cyan mono-data font-medium">
          {twinData!.key_insight}
        </p>
      </div>

      {/* Regenerate */}
      <div className="px-4 py-3 border-t border-border/30 flex items-center justify-between">
        <div className="flex gap-1.5">
          {dayOptions.map((d) => (
            <button
              key={d}
              onClick={() => { setDays(d); generateTwin(d); }}
              className={cn(
                "px-2.5 py-1 rounded text-[10px] mono-data transition-colors",
                d === days
                  ? "bg-cyan/20 text-cyan border border-cyan/30"
                  : "bg-surface border border-border text-muted-foreground hover:text-white"
              )}
            >
              {d}D
            </button>
          ))}
        </div>
        <p className="text-[10px] text-muted-foreground/50 mono-data">
          Not financial advice
        </p>
      </div>
    </div>
  );
}

function _formatPattern(pattern: string): string {
  const labels: Record<string, string> = {
    revenge_trading: "Revenge Trading",
    loss_chasing: "Loss Chasing",
    overtrading: "Overtrading",
    unknown: "Unknown Pattern",
  };
  return labels[pattern] || pattern.replace(/_/g, " ");
}
