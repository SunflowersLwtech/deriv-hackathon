"use client";

import { useEffect, useState, useRef } from "react";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/lib/api";

interface ChatMessageProps {
  message: ChatMessageType;
  /** When true, renders streamingContent with a blinking cursor */
  isStreaming?: boolean;
  /** Partial text being streamed in */
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

  // Typewriter effect for newly completed assistant messages
  const [displayedText, setDisplayedText] = useState("");
  const [showCursor, setShowCursor] = useState(false);
  const hasAnimatedRef = useRef(false);
  const isAssistant = !isUser && !isNudge && !isDisclaimer;

  useEffect(() => {
    // Only animate new assistant messages that haven't been animated yet
    if (!isAssistant || hasAnimatedRef.current || isStreaming) {
      if (!hasAnimatedRef.current && !isStreaming) {
        setDisplayedText(message.content);
      }
      return;
    }

    hasAnimatedRef.current = true;
    setShowCursor(true);

    const text = message.content;
    let idx = 0;
    // Reveal in chunks of 3 chars for speed
    const chunkSize = 3;
    const interval = setInterval(() => {
      idx = Math.min(idx + chunkSize, text.length);
      setDisplayedText(text.slice(0, idx));
      if (idx >= text.length) {
        clearInterval(interval);
        setShowCursor(false);
      }
    }, 12);

    return () => clearInterval(interval);
  }, [message.content, isAssistant, isStreaming]);

  // For non-assistant messages, always show full content
  useEffect(() => {
    if (!isAssistant) {
      setDisplayedText(message.content);
    }
  }, [isAssistant, message.content]);

  if (isDisclaimer) {
    return (
      <div className="px-4 py-3 animate-fade-in">
        <p className="text-[11px] text-muted-foreground/50 mono-data leading-relaxed text-center">
          {message.content}
        </p>
      </div>
    );
  }

  // Determine which text to render
  const textToRender = isStreaming ? (streamingContent || "") : displayedText;
  const cursorVisible = isStreaming || showCursor;

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
        {isStreaming && (
          <span className="text-[10px] text-cyan mono-data ml-2 animate-pulse">
            STREAMING
          </span>
        )}
      </div>

      {/* Content */}
      <div className={cn(
        "text-sm leading-relaxed pl-8",
        isUser ? "text-white" : "text-muted",
        isNudge && "border-l-2 border-warning/50 pl-4 ml-8",
        !isUser && !isNudge && "border-l-2 border-profit/30 pl-4 ml-8",
        isStreaming && "border-l-2 border-cyan/50 pl-4 ml-8"
      )}>
        {textToRender.split("\n").map((line, i) => (
          <p key={i} className={cn(i > 0 && "mt-2")}>
            {line}
          </p>
        ))}
        {cursorVisible && (
          <span className="inline-block w-0.5 h-4 bg-cyan animate-pulse ml-0.5 align-text-bottom" />
        )}
      </div>
    </div>
  );
}
