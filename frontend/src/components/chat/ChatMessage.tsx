"use client";

import { useEffect, useState, useRef } from "react";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/lib/api";
import { renderBlocks } from "@/components/ui/MarkdownRenderer";

/* ────────────────────────────────────────────────────────
   ChatMessage component
   ──────────────────────────────────────────────────────── */

interface ChatMessageProps {
  message: ChatMessageType;
  isStreaming?: boolean;
  streamingContent?: string;
}

export default function ChatMessage({
  message,
  isStreaming = false,
  streamingContent,
}: ChatMessageProps) {
  const isUser = message.role === "user";
  const isNudge = message.type === "nudge";
  const isDisclaimer = message.type === "disclaimer";
  const isAssistant = !isUser && !isNudge && !isDisclaimer;

  /* ── typewriter state ── */
  const shouldAnimate = isAssistant && !isStreaming && !message.skipAnimation;
  const [displayedText, setDisplayedText] = useState(() => (shouldAnimate ? "" : message.content));
  const [showCursor, setShowCursor] = useState(() => shouldAnimate);
  const hasAnimatedRef = useRef(false);

  useEffect(() => {
    if (!shouldAnimate || hasAnimatedRef.current) return;
    hasAnimatedRef.current = true;
    const text = message.content;
    let idx = 0;
    const interval = setInterval(() => {
      idx = Math.min(idx + 3, text.length);
      setDisplayedText(text.slice(0, idx));
      if (idx >= text.length) { clearInterval(interval); setShowCursor(false); }
    }, 12);
    return () => clearInterval(interval);
  }, [message.content, shouldAnimate]);

  /* ── disclaimer type ── */
  if (isDisclaimer) {
    return (
      <div className="px-5 py-2.5">
        <p className="text-[11px] text-muted-foreground/40 mono-data leading-relaxed text-center italic">
          {message.content}
        </p>
      </div>
    );
  }

  const textToRender = isStreaming ? (streamingContent || "") : (shouldAnimate ? displayedText : message.content);
  const cursorVisible = isStreaming || (shouldAnimate && showCursor);

  /* ── user message ── */
  if (isUser) {
    return (
      <div className="px-5 py-4 animate-fade-in">
        <div className="flex items-start gap-3">
          <div className="w-7 h-7 rounded-lg bg-accent/15 border border-accent/20 flex items-center justify-center shrink-0 mt-0.5">
            <span className="text-[10px] text-accent font-bold">U</span>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[11px] font-semibold tracking-wider text-accent/80 mono-data">YOU</span>
              {message.timestamp && (
                <span className="text-[10px] text-muted-foreground/50 mono-data">{message.timestamp}</span>
              )}
            </div>
            <p className="text-[14px] text-white leading-relaxed">{textToRender}</p>
          </div>
        </div>
      </div>
    );
  }

  /* ── nudge message ── */
  if (isNudge) {
    return (
      <div className="px-5 py-4 animate-fade-in">
        <div className="rounded-lg border border-warning/20 bg-warning/[0.04] p-3.5">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-5 h-5 rounded bg-warning/20 flex items-center justify-center">
              <span className="text-[9px] text-warning font-bold">!</span>
            </div>
            <span className="text-[11px] font-semibold tracking-wider text-warning/80 mono-data">BEHAVIORAL NUDGE</span>
          </div>
          <div className="text-sm text-warning/70 leading-relaxed pl-7">
            {renderBlocks(textToRender)}
          </div>
        </div>
      </div>
    );
  }

  /* ── AI assistant message ── */
  return (
    <div className={cn("px-5 py-4 animate-fade-in", isStreaming && "bg-cyan/[0.02]")}>
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div className={cn(
          "w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 border",
          isStreaming
            ? "bg-cyan/15 border-cyan/25"
            : "bg-profit/10 border-profit/20"
        )}>
          <span className={cn(
            "text-[9px] font-bold mono-data",
            isStreaming ? "text-cyan" : "text-profit"
          )}>AI</span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-1.5">
            <span className={cn(
              "text-[11px] font-semibold tracking-wider mono-data",
              isStreaming ? "text-cyan/80" : "text-profit/80"
            )}>TRADEIQ</span>
            {message.timestamp && (
              <span className="text-[10px] text-muted-foreground/50 mono-data">{message.timestamp}</span>
            )}
            {isStreaming && (
              <span className="flex items-center gap-1.5 ml-1">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan animate-pulse" />
                <span className="text-[10px] text-cyan/60 mono-data">LIVE</span>
              </span>
            )}
          </div>

          {/* Rich body */}
          <div className="text-muted leading-relaxed">
            {renderBlocks(textToRender)}
            {cursorVisible && (
              <span className="inline-block w-[2px] h-[14px] bg-cyan animate-pulse ml-0.5 -mb-[2px] rounded-full" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
