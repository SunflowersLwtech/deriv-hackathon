"use client";

import { memo, useEffect, useRef } from "react";

// ── Symbol mapping: display names → TradingView format ──────────
const TV_SYMBOL_MAP: Record<string, string> = {
  "BTC/USD": "BINANCE:BTCUSDT",
  "ETH/USD": "BINANCE:ETHUSDT",
  "EUR/USD": "FX:EURUSD",
  "GBP/USD": "FX:GBPUSD",
  "USD/JPY": "FX:USDJPY",
  "AUD/USD": "FX:AUDUSD",
  GOLD: "TVC:GOLD",
  "XAU/USD": "TVC:GOLD",
};

// ── Interval mapping: timeline codes → TradingView intervals ────
const TV_INTERVAL_MAP: Record<string, string> = {
  "1H": "60",
  "6H": "360",
  "1D": "D",
  "3D": "D",
  "1W": "W",
  "2W": "W",
  "1M": "M",
  "3M": "M",
  "6M": "M",
  "1Y": "M",
};

export function hasTradingViewSymbol(instrument: string): boolean {
  return instrument in TV_SYMBOL_MAP;
}

interface TradingViewWidgetProps {
  symbol: string;
  interval?: string;
  height?: number;
  className?: string;
}

function TradingViewWidgetInner({
  symbol,
  interval = "1D",
  height = 400,
  className,
}: TradingViewWidgetProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Clear previous widget
    container.innerHTML = "";

    const tvSymbol = TV_SYMBOL_MAP[symbol] || symbol;
    const tvInterval = TV_INTERVAL_MAP[interval] || "D";

    const script = document.createElement("script");
    script.src = "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = JSON.stringify({
      autosize: true,
      symbol: tvSymbol,
      interval: tvInterval,
      timezone: "Etc/UTC",
      theme: "dark",
      style: "1",
      locale: "en",
      backgroundColor: "#0a0a0a",
      gridColor: "rgba(39,39,42,0.4)",
      hide_top_toolbar: false,
      hide_legend: false,
      allow_symbol_change: false,
      save_image: false,
      calendar: false,
      hide_volume: true,
      support_host: "https://www.tradingview.com",
      studies: ["RSI@tv-basicstudies", "MASimple@tv-basicstudies"],
    });

    const wrapper = document.createElement("div");
    wrapper.className = "tradingview-widget-container__widget";
    wrapper.style.height = "100%";
    wrapper.style.width = "100%";

    container.appendChild(wrapper);
    container.appendChild(script);

    return () => {
      container.innerHTML = "";
    };
  }, [symbol, interval]);

  return (
    <div className={className}>
      <div
        ref={containerRef}
        className="tradingview-widget-container"
        style={{ height: `${height}px`, width: "100%" }}
      />
      <div className="text-center mt-1">
        <a
          href="https://www.tradingview.com/"
          target="_blank"
          rel="noopener noreferrer"
          className="text-[9px] text-muted-foreground/50 hover:text-muted-foreground transition-colors mono-data"
        >
          Chart by TradingView
        </a>
      </div>
    </div>
  );
}

const TradingViewWidget = memo(TradingViewWidgetInner);
export default TradingViewWidget;
