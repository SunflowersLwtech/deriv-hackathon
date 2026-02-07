"use client";

import { cn } from "@/lib/utils";

interface StatusBadgeProps {
  status: "success" | "warning" | "danger" | "info" | "neutral";
  label: string;
  pulse?: boolean;
  className?: string;
}

export default function StatusBadge({ status, label, pulse, className }: StatusBadgeProps) {
  const colorMap = {
    success: "bg-profit/20 text-profit border-profit/30",
    warning: "bg-warning/20 text-warning border-warning/30",
    danger: "bg-loss/20 text-loss border-loss/30",
    info: "bg-accent/20 text-accent border-accent/30",
    neutral: "bg-muted/20 text-muted border-muted/30",
  };

  const dotColorMap = {
    success: "bg-profit",
    warning: "bg-warning",
    danger: "bg-loss",
    info: "bg-accent",
    neutral: "bg-muted",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-sm text-[11px] font-semibold tracking-wider mono-data border",
        colorMap[status],
        className
      )}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", dotColorMap[status], pulse && "animate-pulse")} />
      {label}
    </span>
  );
}
