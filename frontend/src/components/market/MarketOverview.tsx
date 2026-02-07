"use client";

import { cn } from "@/lib/utils";
import { useMarketOverview } from "@/hooks/useMarketData";
import DataSourceBadge from "@/components/ui/DataSourceBadge";

export default function MarketOverview({ className }: { className?: string }) {
  const { data: initialData, isUsingMock, isBackendOnline } = useMarketOverview();

  return (
    <div className={cn("bg-card border border-border rounded-md", className)}>
      <div className="flex items-center justify-between px-6 py-4 border-b border-border">
        <div className="flex items-center gap-3">
          <h3 className="text-sm font-semibold tracking-wider text-muted uppercase mono-data">MARKET OVERVIEW</h3>
          <DataSourceBadge isUsingMock={isUsingMock} isBackendOnline={isBackendOnline} />
        </div>
        <div className="flex items-center gap-2">
          <div className="live-dot" />
          <span className="text-xs text-profit mono-data">STREAMING</span>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-3 px-6 py-3 border-b border-border/50 text-xs text-muted-foreground mono-data tracking-wider">
        <div className="col-span-4">INSTRUMENT</div>
        <div className="col-span-3 text-right">PRICE</div>
        <div className="col-span-3 text-right">CHANGE</div>
        <div className="col-span-2 text-right">VOL</div>
      </div>

      <div className="divide-y divide-border/30">
        {initialData.map((item) => (
          <div
            key={item.symbol}
            className="grid grid-cols-12 gap-3 px-6 py-3.5 items-center transition-all duration-300 card-hover cursor-pointer"
          >
            <div className="col-span-4 flex items-center gap-3">
              <span className="text-base">{item.icon}</span>
              <div>
                <span className="text-sm text-white font-medium mono-data">{item.symbol}</span>
                <span className="text-xs text-muted-foreground block mt-0.5">{item.name}</span>
              </div>
            </div>
            <div className="col-span-3 text-right">
              <span className="text-sm text-white mono-data font-medium">
                {item.price < 10
                  ? item.price.toFixed(4)
                  : item.price < 1000
                    ? item.price.toFixed(2)
                    : item.price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
            <div className="col-span-3 text-right">
              <span className={cn("text-sm mono-data font-medium", item.changePercent >= 0 ? "text-profit" : "text-loss")}>
                {item.changePercent >= 0 ? "+" : ""}
                {item.changePercent.toFixed(2)}%
              </span>
            </div>
            <div className="col-span-2 text-right">
              <span className="text-xs text-muted-foreground mono-data">{item.volume}</span>
            </div>
          </div>
        ))}
        {initialData.length === 0 && (
          <div className="px-6 py-10 text-center text-sm text-muted mono-data">No live market overview data available.</div>
        )}
      </div>
    </div>
  );
}
