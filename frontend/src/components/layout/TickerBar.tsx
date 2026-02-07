"use client";

import { cn } from "@/lib/utils";
import { useTickerData } from "@/hooks/useMarketData";
import DataSourceBadge from "@/components/ui/DataSourceBadge";

export default function TickerBar() {
  const { tickers, isUsingMock } = useTickerData(2000);
  const renderTickers = [...tickers, ...tickers]; // Duplicate for seamless scroll

  return (
    <div className="bg-card border-b border-border overflow-hidden h-9 flex items-center relative">
      <div className="animate-ticker flex items-center gap-0 whitespace-nowrap">
        {renderTickers.map((ticker, i) => (
          <div
            key={`${ticker.symbol}-${i}`}
            className="flex items-center gap-3 px-4 transition-colors duration-300"
          >
            <span className="text-xs">{ticker.icon}</span>
            <span className="text-[11px] text-muted font-medium tracking-wide">
              {ticker.symbol}
            </span>
            <span className="mono-data font-medium text-white text-[11px]">
              ${ticker.price.toLocaleString("en-US", {
                minimumFractionDigits: 2,
                maximumFractionDigits: ticker.price < 10 ? 4 : 2,
              })}
            </span>
            <span
              className={cn(
                "text-[10px] mono-data font-medium",
                ticker.change >= 0 ? "text-profit" : "text-loss"
              )}
            >
              {ticker.change >= 0 ? "▲" : "▼"} {Math.abs(ticker.change).toFixed(2)}%
            </span>
            {i < renderTickers.length - 1 && (
              <span className="text-border/50 ml-3">•</span>
            )}
          </div>
        ))}
      </div>
      {/* Data source indicator - positioned absolute right */}
      <div className="absolute right-2 top-1/2 -translate-y-1/2 z-10">
        <DataSourceBadge isUsingMock={isUsingMock} />
      </div>
    </div>
  );
}
