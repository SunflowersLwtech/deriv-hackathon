"use client";

import { useEffect, useState, useCallback } from "react";
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

interface DataPoint {
  time: string;
  value: number;
}

function generateMockData(points = 50): DataPoint[] {
  const data: DataPoint[] = [];
  let value = 10000;
  const now = new Date();

  for (let i = points; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 3600000);
    value += (Math.random() - 0.48) * 50;
    data.push({
      time: time.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }),
      value: Math.round(value * 100) / 100,
    });
  }

  return data;
}

interface PnLChartProps {
  className?: string;
  title?: string;
  height?: number;
}

export default function PnLChart({ className, title = "PORTFOLIO PnL", height = 300 }: PnLChartProps) {
  const [data, setData] = useState<DataPoint[]>(() => generateMockData());
  const [hoveredValue, setHoveredValue] = useState<number | null>(null);

  const addDataPoint = useCallback(() => {
    setData((prev) => {
      if (prev.length === 0) return prev;
      const lastValue = prev[prev.length - 1].value;
      const newValue = lastValue + (Math.random() - 0.48) * 20;
      const newPoint = {
        time: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false }),
        value: Math.round(newValue * 100) / 100,
      };
      return [...prev.slice(1), newPoint];
    });
  }, []);

  useEffect(() => {
    const interval = setInterval(addDataPoint, 3000);
    return () => clearInterval(interval);
  }, [addDataPoint]);

  if (data.length === 0) return null;

  const currentValue = hoveredValue ?? data[data.length - 1]?.value ?? 0;
  const startValue = data[0]?.value ?? 0;
  const pnl = currentValue - startValue;
  const pnlPercent = startValue > 0 ? (pnl / startValue) * 100 : 0;
  const isPositive = pnl >= 0;
  const chartColor = isPositive ? "#4ade80" : "#f87171";

  return (
    <div className={cn("bg-card border border-border rounded-sm p-4", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-[10px] font-semibold tracking-wider text-muted uppercase mono-data">
            {title}
          </h3>
          <div className="flex items-baseline gap-3 mt-1">
            <span className="text-2xl font-bold mono-data text-white">
              ${currentValue.toLocaleString("en-US", { minimumFractionDigits: 2 })}
            </span>
            <span
              className={cn(
                "text-sm mono-data font-semibold",
                isPositive ? "text-profit glow-green" : "text-loss glow-red"
              )}
            >
              {isPositive ? "+" : ""}
              {pnl.toFixed(2)} ({pnlPercent.toFixed(2)}%)
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className={cn("w-2 h-2 rounded-full", isPositive ? "bg-profit" : "bg-loss")} />
          <span className="text-[9px] text-muted mono-data">LIVE</span>
        </div>
      </div>

      {/* Chart */}
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
            tick={{ fontSize: 9, fill: "#71717a", fontFamily: "JetBrains Mono, monospace" }}
            axisLine={{ stroke: "#27272a" }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fontSize: 9, fill: "#71717a", fontFamily: "JetBrains Mono, monospace" }}
            axisLine={false}
            tickLine={false}
            domain={["auto", "auto"]}
            tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
          />
          <Tooltip
            contentStyle={{
              background: "#0a0a0a",
              border: "1px solid #27272a",
              borderRadius: "2px",
              fontSize: "10px",
              fontFamily: "JetBrains Mono, monospace",
              color: "#ffffff",
            }}
            formatter={(value: number | undefined) => [`$${(value ?? 0).toFixed(2)}`, "Value"]}
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
    </div>
  );
}
