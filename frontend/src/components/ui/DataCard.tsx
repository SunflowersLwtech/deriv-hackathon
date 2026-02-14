"use client";

import { cn } from "@/lib/utils";

interface DataCardProps {
  title: string;
  value?: string | number;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
  icon?: React.ReactNode;
  children?: React.ReactNode;
  className?: string;
  onClick?: () => void;
  glow?: boolean;
}

export default function DataCard({
  title,
  value,
  subtitle,
  trend,
  icon,
  children,
  className,
  onClick,
  glow,
}: DataCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "bg-card border border-border rounded-md p-6 transition-all duration-200 overflow-hidden",
        onClick && "cursor-pointer card-hover",
        glow && trend === "up" && "border-profit/30",
        glow && trend === "down" && "border-loss/30",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-2">
          {icon && <span className="text-base">{icon}</span>}
          <h3 className="text-xs font-semibold tracking-wider text-muted-foreground uppercase mono-data">
            {title}
          </h3>
        </div>
        {trend && (
          <span
            className={cn(
              "text-xs mono-data font-semibold",
              trend === "up" && "text-profit",
              trend === "down" && "text-loss",
              trend === "neutral" && "text-muted"
            )}
          >
            {trend === "up" ? "▲" : trend === "down" ? "▼" : "—"}
          </span>
        )}
      </div>

      {/* Value */}
      {value !== undefined && (
        <div
          className={cn(
            "font-bold mono-data tracking-tight truncate",
            String(value).length > 10 ? "text-xl" : "text-3xl",
            trend === "up" && "text-profit",
            trend === "down" && "text-loss",
            (trend === "neutral" || !trend) && "text-white"
          )}
          title={String(value)}
        >
          {value}
        </div>
      )}

      {/* Subtitle */}
      {subtitle && (
        <p className={cn(
          "text-xs mt-2 mono-data truncate",
          trend === "up" ? "text-profit" : trend === "down" ? "text-loss" : "text-white"
        )} title={subtitle}>{subtitle}</p>
      )}

      {/* Custom children */}
      {children && <div className="mt-4">{children}</div>}
    </div>
  );
}
