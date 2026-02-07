"use client";

import { cn } from "@/lib/utils";

interface DisclaimerBadgeProps {
  text?: string;
  variant?: "inline" | "banner" | "footer";
  className?: string;
}

export default function DisclaimerBadge({
  text = "AI-generated analysis. Not financial advice. Always do your own research.",
  variant = "inline",
  className,
}: DisclaimerBadgeProps) {
  if (variant === "banner") {
    return (
      <div className={cn("bg-warning/10 border border-warning/20 px-4 py-2.5 rounded-md", className)}>
        <div className="flex items-center gap-2.5">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-warning shrink-0">
            <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <p className="text-xs text-warning/80 mono-data leading-relaxed">{text}</p>
        </div>
      </div>
    );
  }

  if (variant === "footer") {
    return (
      <div className={cn("border-t border-border pt-4 mt-6", className)}>
        <p className="text-xs text-muted-foreground/60 mono-data text-center leading-relaxed">
          ⚠ {text}
        </p>
      </div>
    );
  }

  return (
    <span className={cn("inline-flex items-center gap-1.5 text-[11px] text-muted-foreground/50 mono-data", className)}>
      <span>⚠</span>
      <span>{text}</span>
    </span>
  );
}
