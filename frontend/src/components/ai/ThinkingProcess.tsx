"use client";

import { cn } from "@/lib/utils";
import type { StreamState, ToolCallInfo } from "@/hooks/useStreamingChat";

interface ThinkingProcessProps {
  status: StreamState;
  toolCall: ToolCallInfo | null;
  streamingText: string;
  agentType?: string;
}

export default function ThinkingProcess({
  status,
  toolCall,
  streamingText,
  agentType,
}: ThinkingProcessProps) {
  if (status === "idle" || status === "done") return null;

  return (
    <div className="px-5 py-4 animate-fade-in">
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className="w-7 h-7 rounded-lg bg-cyan/15 border border-cyan/25 flex items-center justify-center shrink-0 mt-0.5">
          <span className="text-[9px] text-cyan mono-data font-bold">AI</span>
        </div>

        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-2">
            <span className="text-[11px] font-semibold tracking-wider mono-data text-cyan/80">
              {agentType ? agentType.toUpperCase() : "TRADEIQ"}
            </span>
          </div>

          {/* Thinking state */}
          {status === "thinking" && (
            <div className="flex items-center gap-3">
              <div className="flex gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan/70 animate-bounce" style={{ animationDelay: "0ms", animationDuration: "0.8s" }} />
                <div className="w-1.5 h-1.5 rounded-full bg-cyan/70 animate-bounce" style={{ animationDelay: "150ms", animationDuration: "0.8s" }} />
                <div className="w-1.5 h-1.5 rounded-full bg-cyan/70 animate-bounce" style={{ animationDelay: "300ms", animationDuration: "0.8s" }} />
              </div>
              <span className="text-xs text-muted-foreground/70 mono-data">Analyzing your query...</span>
            </div>
          )}

          {/* Tool call state */}
          {status === "tool_call" && toolCall && (
            <div className="space-y-1.5">
              {toolCall.tools_used.map((tool, i) => (
                <div key={i} className="flex items-center gap-2.5 py-0.5">
                  <div className="relative w-4 h-4 shrink-0">
                    <div className="absolute inset-0 rounded-full border border-cyan/30" />
                    <div className="absolute inset-[3px] rounded-full bg-cyan/60 animate-ping" />
                    <div className="absolute inset-[3px] rounded-full bg-cyan/80" />
                  </div>
                  <span className="text-xs text-muted-foreground mono-data">
                    {_toolLabel(tool)}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Streaming text */}
          {status === "streaming" && streamingText && (
            <div className="text-sm leading-relaxed text-muted">
              {streamingText.split("\n").map((line, i) => (
                <p key={i} className={cn(i > 0 && "mt-1.5")}>{line}</p>
              ))}
              <span className="inline-block w-[2px] h-[14px] bg-cyan animate-pulse ml-0.5 -mb-[2px] rounded-full" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function _toolLabel(tool: string): string {
  const labels: Record<string, string> = {
    fetch_price_data: "Fetching live price data...",
    search_news: "Searching latest news...",
    analyze_technicals: "Running technical analysis...",
    get_sentiment: "Analyzing market sentiment...",
    analyze_trade_patterns: "Detecting behavioral patterns...",
    get_recent_trades: "Loading trade history...",
    get_trading_statistics: "Computing statistics...",
    generate_draft: "Generating content...",
    get_leaderboard: "Fetching leaderboard...",
    get_trader_profile: "Loading trader profile...",
    get_copiers: "Loading copier data...",
  };
  return labels[tool] || `Running ${tool}...`;
}
