"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { cn } from "@/lib/utils";

const ChatPanel = dynamic(() => import("@/components/chat/ChatPanel"), {
  loading: () => (
    <div className="flex items-center justify-center h-full">
      <span className="text-xs text-muted mono-data">Loading chat...</span>
    </div>
  ),
  ssr: false,
});

interface SidebarProps {
  defaultOpen?: boolean;
}

export default function Sidebar({ defaultOpen = true }: SidebarProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [activeTab, setActiveTab] = useState<"chat" | "activity">("chat");

  return (
    <>
      {/* Toggle button when closed */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed right-0 top-1/2 -translate-y-1/2 z-40 bg-card border border-border border-r-0 rounded-l-md px-1.5 py-6 hover:bg-surface transition-colors group"
          title="Open sidebar"
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-muted group-hover:text-white transition-colors"
          >
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "h-full border-l border-border bg-card transition-all duration-300 flex flex-col shrink-0",
          isOpen ? "w-[420px] xl:w-[460px]" : "w-0 overflow-hidden"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border shrink-0">
          <button
            onClick={() => setIsOpen(false)}
            className="p-3 text-muted hover:text-white transition-colors"
            title="Collapse sidebar"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 18l6-6-6-6" />
            </svg>
          </button>

          {/* Tabs */}
          <div className="flex">
            <button
              onClick={() => setActiveTab("chat")}
              className={cn(
                "px-5 py-3 text-xs font-semibold tracking-wider mono-data transition-colors",
                activeTab === "chat"
                  ? "text-white border-b-2 border-white"
                  : "text-muted hover:text-white"
              )}
            >
              AI CHAT
            </button>
            <button
              onClick={() => setActiveTab("activity")}
              className={cn(
                "px-5 py-3 text-xs font-semibold tracking-wider mono-data transition-colors",
                activeTab === "activity"
                  ? "text-white border-b-2 border-white"
                  : "text-muted hover:text-white"
              )}
            >
              ACTIVITY
            </button>
          </div>

          <div className="w-10" /> {/* Spacer for alignment */}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === "chat" ? (
            <ChatPanel />
          ) : (
            <ActivityFeed />
          )}
        </div>
      </aside>
    </>
  );
}

function ActivityFeed() {
  const activities = [
    {
      type: "market" as const,
      message: "EUR/USD showing bearish divergence on RSI",
      time: "2m ago",
    },
    {
      type: "behavior" as const,
      message: "Pattern detected: Potential overtrading (12 trades in 1h)",
      time: "5m ago",
    },
    {
      type: "content" as const,
      message: "New Bluesky post drafted: 'Market Update: EUR/USD...'",
      time: "12m ago",
    },
    {
      type: "market" as const,
      message: "BTC/USD crossed above 50-day SMA",
      time: "18m ago",
    },
    {
      type: "behavior" as const,
      message: "Trading session score: 78/100 (Good)",
      time: "25m ago",
    },
  ];

  const typeColors: Record<string, string> = {
    market: "text-accent",
    behavior: "text-warning",
    content: "text-cyan",
  };

  const typeLabels: Record<string, string> = {
    market: "MARKET",
    behavior: "BEHAVIOR",
    content: "CONTENT",
  };

  return (
    <div className="p-4 space-y-2 overflow-y-auto h-full">
      {activities.map((activity, i) => (
        <div
          key={i}
          className="p-4 border border-border/50 rounded-md hover:bg-surface transition-colors animate-fade-in"
          style={{ animationDelay: `${i * 50}ms` }}
        >
          <div className="flex items-center justify-between mb-2">
            <span className={cn("text-xs font-semibold tracking-wider mono-data", typeColors[activity.type])}>
              {typeLabels[activity.type]}
            </span>
            <span className="text-[11px] text-muted-foreground mono-data">{activity.time}</span>
          </div>
          <p className="text-sm text-muted leading-relaxed">{activity.message}</p>
        </div>
      ))}
    </div>
  );
}
