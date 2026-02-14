"use client";

import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import type { MarketAlertData } from "@/lib/websocket";

interface MarketAlertToastProps {
  alert: MarketAlertData | null;
  onDismiss?: () => void;
}

export default function MarketAlertToast({ alert, onDismiss }: MarketAlertToastProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (alert) {
      setVisible(true);
      const timer = setTimeout(() => {
        setVisible(false);
        onDismiss?.();
      }, 8000);
      return () => clearTimeout(timer);
    }
  }, [alert, onDismiss]);

  if (!alert || !visible) return null;

  const isUp = alert.direction === "spike";
  const color = isUp ? "text-profit" : "text-loss";
  const borderColor = isUp ? "border-profit/50" : "border-loss/50";
  const bgColor = isUp ? "bg-profit/5" : "bg-loss/5";
  const arrow = isUp ? "▲" : "▼";

  return (
    <div
      className={cn(
        "fixed top-16 right-4 z-50 w-80 rounded-lg border p-4 shadow-2xl",
        "backdrop-blur-sm animate-slide-in-right",
        borderColor,
        bgColor,
        "bg-card/95"
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className={cn("w-2 h-2 rounded-full animate-pulse", isUp ? "bg-profit" : "bg-loss")} />
          <span className="text-xs font-bold tracking-wider mono-data text-white uppercase">
            Market Alert
          </span>
        </div>
        <button
          onClick={() => { setVisible(false); onDismiss?.(); }}
          className="text-muted-foreground hover:text-white text-xs"
        >
          x
        </button>
      </div>

      {/* Instrument + Change */}
      <div className="flex items-baseline gap-2 mb-2">
        <span className="text-sm font-bold text-white">{alert.instrument}</span>
        <span className={cn("text-lg font-bold mono-data", color)}>
          {arrow} {Math.abs(alert.change_pct).toFixed(2)}%
        </span>
      </div>

      {/* Price */}
      <div className="text-xs text-muted-foreground mono-data mb-2">
        Price: ${alert.price.toLocaleString()}
      </div>

      {/* AI Summary */}
      {alert.analysis_summary && (
        <p className="text-xs text-muted leading-relaxed border-t border-border/30 pt-2 mt-2">
          {alert.analysis_summary.slice(0, 150)}
          {alert.analysis_summary.length > 150 ? "..." : ""}
        </p>
      )}

      {/* Behavioral Warning */}
      {alert.behavioral_warning && (
        <div className="mt-2 px-2 py-1.5 rounded bg-warning/10 border border-warning/30">
          <p className="text-[11px] text-warning mono-data">
            {alert.behavioral_warning.slice(0, 120)}
          </p>
        </div>
      )}
    </div>
  );
}
