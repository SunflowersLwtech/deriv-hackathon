"use client";

import { cn } from "@/lib/utils";
import { useTickerData } from "@/hooks/useMarketData";
import DataSourceBadge from "@/components/ui/DataSourceBadge";

export default function TickerBar() {
  const { tickers, isUsingMock } = useTickerData(10000);
  const renderTickers = [...tickers, ...tickers]; // Duplicate for seamless scroll

  return (
    <div className="bg-[#1e222d] border-b border-[#2a2e39] overflow-hidden h-10 flex items-center relative">
      {renderTickers.length > 0 ? (
        <div className="animate-ticker flex items-center gap-0 whitespace-nowrap">
        {renderTickers.map((ticker, i) => (
          <div
            key={`${ticker.symbol}-${i}`}
            className="flex items-center gap-3.5 px-5 transition-colors duration-300"
          >
            <span className="text-[12px]">{ticker.icon}</span>
            <span className="text-[12px] text-[#787b86] font-medium tracking-wide">
              {ticker.symbol}
            </span>
            <span className="mono-data font-medium text-[#d1d4dc] text-[12px]">
              ${ticker.price.toLocaleString("en-US", {
                minimumFractionDigits: 2,
                maximumFractionDigits: ticker.price < 10 ? 4 : 2,
              })}
            </span>
            <span
              className={cn(
                "text-[11px] mono-data font-medium",
                ticker.change >= 0 ? "text-profit" : "text-loss"
              )}
            >
              {ticker.change >= 0 ? "▲" : "▼"} {Math.abs(ticker.change).toFixed(2)}%
            </span>
            {i < renderTickers.length - 1 && (
              <span className="text-[#2a2e39] ml-3">|</span>
            )}
          </div>
        ))}
        </div>
      ) : (
        <div className="px-4 text-[12px] text-[#787b86] mono-data">No live ticker data available.</div>
      )}
      {/* Data source indicator - positioned absolute right */}
      <div className="absolute right-2 top-1/2 -translate-y-1/2 z-10">
        <DataSourceBadge isUsingMock={isUsingMock} />
      </div>
    </div>
  );
}
