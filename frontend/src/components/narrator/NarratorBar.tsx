"use client";

import { cn } from "@/lib/utils";

interface NarratorBarProps {
  narration: string | null;
  isActive: boolean;
}

export default function NarratorBar({ narration, isActive }: NarratorBarProps) {
  if (!narration) return null;

  return (
    <div
      className={cn(
        "fixed bottom-0 left-0 right-0 z-40",
        "bg-card/90 backdrop-blur-sm border-t border-border/50",
        "px-6 py-3 flex items-center gap-3",
        "animate-slide-in-up"
      )}
    >
      {/* Status dot */}
      <div
        className={cn(
          "w-2 h-2 rounded-full shrink-0",
          isActive ? "bg-profit animate-pulse" : "bg-muted"
        )}
      />

      {/* Narration text */}
      <p className="text-sm text-muted-foreground mono-data flex-1 truncate">
        {narration}
      </p>

      {/* AI badge */}
      <div className="shrink-0 px-2 py-0.5 rounded bg-surface border border-border">
        <span className="text-[10px] text-muted-foreground mono-data tracking-wider">
          AI NARRATOR
        </span>
      </div>
    </div>
  );
}
