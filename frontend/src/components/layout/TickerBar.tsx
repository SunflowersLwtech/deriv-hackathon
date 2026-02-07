"use client";

import { cn } from "@/lib/utils";
import { useTickerData } from "@/hooks/useMarketData";
import DataSourceBadge from "@/components/ui/DataSourceBadge";

export default function TickerBar() {
  const { tickers, isUsingMock } = useTickerData(10000);
  const renderTickers = [...tickers, ...tickers]; // Duplicate for seamless scroll

  return (
    <div className="bg-card border-b border-border overflow-hidden h-12 flex items-center relative">
      {renderTickers.length > 0 ? (
        <div className="animate-ticker flex items-center gap-0 whitespace-nowrap">
        {renderTickers.map((ticker, i) => (
          <div
            key={`${ticker.symbol}-${i}`}
            className="flex items-center gap-3.5 px-5 transition-colors duration-300"
          >
            <span className="text-sm">{ticker.icon}</span>
            <span className="text-sm text-muted font-medium tracking-wide">
              {ticker.symbol}
            </span>
            <span className="mono-data font-medium text-white text-sm">
              ${ticker.price.toLocaleString("en-US", {
                minimumFractionDigits: 2,
                maximumFractionDigits: ticker.price < 10 ? 4 : 2,
              })}
            </span>
            <span
              className={cn(
                "text-xs mono-data font-medium",
                ticker.change >= 0 ? "text-profit" : "text-loss"
              )}
            >
              {ticker.change >= 0 ? "▲" : "▼"} {Math.abs(ticker.change).toFixed(2)}%
            </span>
            {i < renderTickers.length - 1 && (
              <span className="text-border/50 ml-4">•</span>
            )}
          </div>
        ))}
        </div>
      ) : (
        <div className="px-4 text-sm text-muted mono-data">No live ticker data available.</div>
      )}
      {/* Data source indicator - positioned absolute right */}
      <div className="absolute right-2 top-1/2 -translate-y-1/2 z-10">
        <DataSourceBadge isUsingMock={isUsingMock} />
      </div>
    </div>
  );
}
