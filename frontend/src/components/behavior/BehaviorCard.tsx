"use client";

import { cn } from "@/lib/utils";
import StatusBadge from "@/components/ui/StatusBadge";
import CollapsibleSection from "@/components/ui/CollapsibleSection";

interface BehaviorPattern {
  id: string;
  type: string;
  severity: "low" | "medium" | "high" | "critical";
  description: string;
  nudge: string;
  detectedAt: string;
  metrics: {
    label: string;
    value: string | number;
    threshold?: string | number;
    status: "ok" | "warning" | "danger";
  }[];
}

interface BehaviorCardProps {
  pattern: BehaviorPattern;
  className?: string;
}

export default function BehaviorCard({ pattern, className }: BehaviorCardProps) {
  const severityMap = {
    low: { status: "info" as const, label: "LOW" },
    medium: { status: "warning" as const, label: "MEDIUM" },
    high: { status: "danger" as const, label: "HIGH" },
    critical: { status: "danger" as const, label: "CRITICAL" },
  };

  const { status, label } = severityMap[pattern.severity];

  return (
    <div className={cn("bg-card border border-border rounded-md overflow-hidden", className)}>
      {/* Header */}
      <div className="px-5 py-3.5 border-b border-border flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div
            className={cn(
              "w-2.5 h-2.5 rounded-full",
              pattern.severity === "critical" && "bg-loss animate-pulse",
              pattern.severity === "high" && "bg-loss",
              pattern.severity === "medium" && "bg-warning",
              pattern.severity === "low" && "bg-accent"
            )}
          />
          <span className="text-sm text-white font-semibold mono-data uppercase tracking-wider">
            {pattern.type.replace(/_/g, " ")}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <StatusBadge status={status} label={label} pulse={pattern.severity === "critical"} />
          <span className="text-xs text-muted-foreground mono-data">{pattern.detectedAt}</span>
        </div>
      </div>

      {/* Description */}
      <div className="px-5 py-4">
        <p className="text-sm text-muted leading-relaxed">{pattern.description}</p>
      </div>

      {/* Metrics */}
      <div className="px-5 pb-4">
        <div className="grid grid-cols-3 gap-3">
          {pattern.metrics.map((metric, i) => (
            <div key={i} className="bg-surface rounded-md p-3.5">
              <div className="text-xs text-muted-foreground mono-data tracking-wider mb-1.5">
                {metric.label}
              </div>
              <div className="flex items-baseline gap-1.5">
                <span
                  className={cn(
                    "text-base font-bold mono-data",
                    metric.status === "ok" && "text-profit",
                    metric.status === "warning" && "text-warning",
                    metric.status === "danger" && "text-loss"
                  )}
                >
                  {metric.value}
                </span>
                {metric.threshold && (
                  <span className="text-[10px] text-muted-foreground mono-data">
                    / {metric.threshold}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* AI Nudge */}
      <CollapsibleSection title="AI BEHAVIORAL NUDGE" defaultOpen={pattern.severity === "critical" || pattern.severity === "high"}>
        <div className="px-5 py-4 bg-warning/5">
          <div className="flex gap-3">
            <span className="text-warning text-base shrink-0">💡</span>
            <p className="text-sm text-warning/80 leading-relaxed italic">
              &ldquo;{pattern.nudge}&rdquo;
            </p>
          </div>
        </div>
      </CollapsibleSection>
    </div>
  );
}
