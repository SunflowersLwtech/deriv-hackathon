"use client";

import { cn } from "@/lib/utils";

interface DataSourceBadgeProps {
  isUsingMock: boolean;
  isBackendOnline?: boolean;
  className?: string;
}

/**
 * Small indicator showing whether data comes from live backend or fallback state.
 */
export default function DataSourceBadge({ isUsingMock, isBackendOnline, className }: DataSourceBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2 py-1 rounded-sm text-[10px] mono-data tracking-wider border",
        isUsingMock
          ? "border-warning/30 text-warning/70 bg-warning/5"
          : "border-profit/30 text-profit/70 bg-profit/5",
        className
      )}
      title={isUsingMock ? "Using fallback state (backend unavailable or empty)" : "Connected to live backend"}
    >
      <span className={cn(
        "w-1.5 h-1.5 rounded-full",
        isUsingMock ? "bg-warning" : "bg-profit",
        !isUsingMock && "animate-pulse"
      )} />
      {isUsingMock ? "FALLBACK" : "LIVE"}
      {isBackendOnline !== undefined && !isBackendOnline && isUsingMock && (
        <span className="text-muted-foreground"> · OFFLINE</span>
      )}
    </span>
  );
}
