"use client";

import { useState, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import { useMarketOverview, type MarketOverviewItem } from "@/hooks/useMarketData";
import DataSourceBadge from "@/components/ui/DataSourceBadge";

export default function MarketOverview({ className }: { className?: string }) {
  const { data: initialData, isUsingMock, isBackendOnline } = useMarketOverview();
  const [data, setData] = useState<MarketOverviewItem[]>(initialData);
  const [flashMap, setFlashMap] = useState<Record<string, "up" | "down">>({});

  // Sync when API data changes
  useEffect(() => {
    setData(initialData);
  }, [initialData]);

  // Simulate price movement on top of real or mock data
  const updatePrices = useCallback(() => {
    setData((prev) =>
      prev.map((item) => {
        const variance = item.price * 0.0003;
        const delta = (Math.random() - 0.5) * 2 * variance;
        const newPrice = Math.max(0, item.price + delta);
        const newChange = item.change + delta;
        const newChangePercent = (newChange / (newPrice - newChange)) * 100;

        if (Math.abs(delta) > variance * 0.3) {
          setFlashMap((prev) => ({ ...prev, [item.symbol]: delta > 0 ? "up" : "down" }));
          setTimeout(() => {
            setFlashMap((prev) => {
              const updated = { ...prev };
              delete updated[item.symbol];
              return updated;
            });
          }, 600);
        }

        return { ...item, price: newPrice, change: newChange, changePercent: newChangePercent };
      })
    );
  }, []);

  useEffect(() => {
    const interval = setInterval(updatePrices, 2500);
    return () => clearInterval(interval);
  }, [updatePrices]);

  return (
    <div className={cn("bg-card border border-border rounded-sm", className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <h3 className="text-[10px] font-semibold tracking-wider text-muted uppercase mono-data">
            MARKET OVERVIEW
          </h3>
          <DataSourceBadge isUsingMock={isUsingMock} isBackendOnline={isBackendOnline} />
        </div>
        <div className="flex items-center gap-2">
          <div className="live-dot" />
          <span className="text-[9px] text-profit mono-data">STREAMING</span>
        </div>
      </div>

      {/* Table Header */}
      <div className="grid grid-cols-12 gap-2 px-4 py-2 border-b border-border/50 text-[9px] text-muted-foreground mono-data tracking-wider">
        <div className="col-span-4">INSTRUMENT</div>
        <div className="col-span-3 text-right">PRICE</div>
        <div className="col-span-3 text-right">CHANGE</div>
        <div className="col-span-2 text-right">VOL</div>
      </div>

      {/* Table Body */}
      <div className="divide-y divide-border/30">
        {data.map((item) => (
          <div
            key={item.symbol}
            className={cn(
              "grid grid-cols-12 gap-2 px-4 py-2.5 items-center transition-all duration-300 card-hover cursor-pointer",
              flashMap[item.symbol] === "up" && "animate-flash-green",
              flashMap[item.symbol] === "down" && "animate-flash-red"
            )}
          >
            <div className="col-span-4 flex items-center gap-2">
              <span className="text-sm">{item.icon}</span>
              <div>
                <span className="text-[11px] text-white font-medium mono-data">{item.symbol}</span>
                <span className="text-[9px] text-muted-foreground block">{item.name}</span>
              </div>
            </div>
            <div className="col-span-3 text-right">
              <span className="text-[11px] text-white mono-data font-medium">
                {item.price < 10
                  ? item.price.toFixed(4)
                  : item.price < 1000
                  ? item.price.toFixed(2)
                  : item.price.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            </div>
            <div className="col-span-3 text-right">
              <span className={cn("text-[11px] mono-data font-medium", item.changePercent >= 0 ? "text-profit" : "text-loss")}>
                {item.changePercent >= 0 ? "+" : ""}{item.changePercent.toFixed(2)}%
              </span>
            </div>
            <div className="col-span-2 text-right">
              <span className="text-[10px] text-muted-foreground mono-data">{item.volume}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
