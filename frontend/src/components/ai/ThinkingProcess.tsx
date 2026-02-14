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
    <div className="px-4 py-4 bg-surface/50 animate-fade-in">
      {/* Agent badge */}
      <div className="flex items-center gap-2.5 mb-3">
        <div className="w-6 h-6 rounded-md bg-cyan/20 flex items-center justify-center">
          <span className="text-[10px] text-cyan mono-data font-bold">AI</span>
        </div>
        <span className="text-xs font-semibold tracking-wider mono-data text-cyan">
          {agentType ? agentType.toUpperCase() : "TRADEIQ"}
        </span>
      </div>

      {/* Thinking state */}
      {status === "thinking" && (
        <div className="pl-8 flex items-center gap-2">
          <div className="flex gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-cyan animate-pulse" style={{ animationDelay: "0ms" }} />
            <div className="w-1.5 h-1.5 rounded-full bg-cyan animate-pulse" style={{ animationDelay: "150ms" }} />
            <div className="w-1.5 h-1.5 rounded-full bg-cyan animate-pulse" style={{ animationDelay: "300ms" }} />
          </div>
          <span className="text-xs text-muted-foreground mono-data">Analyzing...</span>
        </div>
      )}

      {/* Tool call state */}
      {status === "tool_call" && toolCall && (
        <div className="pl-8 space-y-1.5">
          {toolCall.tools_used.map((tool, i) => (
            <div key={i} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full border border-cyan/50 flex items-center justify-center">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan animate-pulse" />
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
        <div className={cn(
          "pl-8 text-sm leading-relaxed text-muted",
          "border-l-2 border-cyan/30 pl-4 ml-8"
        )}>
          {streamingText.split("\n").map((line, i) => (
            <p key={i} className={cn(i > 0 && "mt-2")}>{line}</p>
          ))}
          <span className="inline-block w-0.5 h-4 bg-cyan animate-pulse ml-0.5 align-text-bottom" />
        </div>
      )}
    </div>
  );
}

function _toolLabel(tool: string): string {
  const labels: Record<string, string> = {
    fetch_price_data: "Fetching live price...",
    search_news: "Searching news...",
    analyze_technicals: "Running technical analysis...",
    get_sentiment: "Analyzing sentiment...",
    analyze_trade_patterns: "Detecting behavioral patterns...",
    get_recent_trades: "Loading trade history...",
    get_trading_statistics: "Computing statistics...",
    generate_draft: "Generating content...",
  };
  return labels[tool] || `Running ${tool}...`;
}
