"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import ChatMessage from "./ChatMessage";
import ThinkingProcess from "@/components/ai/ThinkingProcess";
import { useChatContext } from "@/providers/ChatProvider";

export default function ChatPanel() {
  const {
    messages,
    streamingMessage,
    streamStatus,
    currentToolCall,
    sendMessage,
    clearHistory,
  } = useChatContext();

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage, scrollToBottom]);

  // Auto-resize textarea to fit content (max 5 rows)
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = Math.min(ta.scrollHeight, 120) + "px"; // 120px ≈ 5 rows
  }, [input]);

  const handleSend = () => {
    if (!input.trim() || streamStatus !== "idle") return;
    sendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isProcessing = streamStatus !== "idle";

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="divide-y divide-border/20">
          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}
        </div>

        {/* Thinking / Tool call phase */}
        {isProcessing && (streamStatus === "thinking" || streamStatus === "tool_call") && (
          <div className="border-t border-border/20">
            <ThinkingProcess
              status={streamStatus}
              toolCall={currentToolCall}
              streamingText=""
            />
          </div>
        )}

        {/* Streaming phase */}
        {streamStatus === "streaming" && streamingMessage && (
          <div className="border-t border-border/20">
            <ChatMessage
              message={{
                role: "assistant",
                content: "",
                timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
                type: "normal",
              }}
              isStreaming
              streamingContent={streamingMessage}
            />
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-border bg-card/50 p-4 shrink-0">
        <div className="flex gap-2.5 items-end">
          <button
            onClick={clearHistory}
            disabled={isProcessing || messages.length <= 1}
            title="Clear conversation"
            className={cn(
              "p-2.5 rounded-lg transition-all duration-200 shrink-0",
              !isProcessing && messages.length > 1
                ? "text-muted-foreground hover:text-loss hover:bg-loss/10"
                : "text-muted-foreground/30 cursor-not-allowed"
            )}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 6h18" /><path d="M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2" /><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
            </svg>
          </button>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isProcessing ? "Waiting for response..." : "Ask about markets, behavior, or content..."}
            rows={1}
            disabled={isProcessing}
            className={cn(
              "flex-1 bg-surface border border-border rounded-lg px-4 py-2.5",
              "text-sm text-white placeholder:text-muted-foreground/50 mono-data",
              "focus:outline-none focus:border-accent/40 focus:ring-1 focus:ring-accent/20 resize-none",
              "transition-all duration-200",
              isProcessing && "opacity-50 cursor-not-allowed"
            )}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isProcessing}
            className={cn(
              "px-4 py-2.5 rounded-lg text-xs font-semibold tracking-wider mono-data",
              "transition-all duration-200",
              input.trim() && !isProcessing
                ? "bg-white text-black hover:bg-gray-200 active:scale-[0.97]"
                : "bg-border/50 text-muted-foreground/50 cursor-not-allowed"
            )}
          >
            {isProcessing ? "..." : "SEND"}
          </button>
        </div>
        <p className="text-[10px] text-muted-foreground/30 mt-2 mono-data text-center">
          AI analysis only &middot; Not financial advice &middot; DYOR
        </p>
      </div>
    </div>
  );
}
