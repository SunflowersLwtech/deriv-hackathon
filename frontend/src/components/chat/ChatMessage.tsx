"use client";

import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/lib/api";

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";
  const isNudge = message.type === "nudge";
  const isDisclaimer = message.type === "disclaimer";

  if (isDisclaimer) {
    return (
      <div className="px-4 py-3 animate-fade-in">
        <p className="text-[11px] text-muted-foreground/50 mono-data leading-relaxed text-center">
          ⚠ {message.content}
        </p>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "px-4 py-3.5 animate-fade-in",
        isUser ? "bg-transparent" : "bg-surface/50"
      )}
    >
      {/* Header */}
      <div className="flex items-center gap-2.5 mb-2">
        {isUser ? (
          <div className="w-6 h-6 rounded-md bg-accent/20 flex items-center justify-center">
            <span className="text-[10px] text-accent mono-data font-bold">U</span>
          </div>
        ) : (
          <div className={cn(
            "w-6 h-6 rounded-md flex items-center justify-center",
            isNudge ? "bg-warning/20" : "bg-profit/20"
          )}>
            <span className={cn(
              "text-[10px] mono-data font-bold",
              isNudge ? "text-warning" : "text-profit"
            )}>
              {isNudge ? "!" : "AI"}
            </span>
          </div>
        )}
        <span className={cn(
          "text-xs font-semibold tracking-wider mono-data",
          isUser ? "text-accent" : isNudge ? "text-warning" : "text-profit"
        )}>
          {isUser ? "YOU" : isNudge ? "BEHAVIORAL NUDGE" : "TRADEIQ"}
        </span>
        {message.timestamp && (
          <span className="text-[11px] text-muted-foreground mono-data ml-auto">
            {message.timestamp}
          </span>
        )}
      </div>

      {/* Content */}
      <div className={cn(
        "text-sm leading-relaxed pl-8",
        isUser ? "text-white" : "text-muted",
        isNudge && "border-l-2 border-warning/50 pl-4 ml-8",
        !isUser && !isNudge && "border-l-2 border-profit/30 pl-4 ml-8"
      )}>
        {message.content.split("\n").map((line, i) => (
          <p key={i} className={cn(i > 0 && "mt-2")}>
            {line}
          </p>
        ))}
      </div>
    </div>
  );
}
