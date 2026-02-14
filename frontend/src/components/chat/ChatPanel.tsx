"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import ChatMessage from "./ChatMessage";
import ThinkingProcess from "@/components/ai/ThinkingProcess";
import { useStreamingChat } from "@/hooks/useStreamingChat";

export default function ChatPanel() {
  const {
    messages,
    streamingMessage,
    streamStatus,
    currentToolCall,
    sendMessage,
  } = useStreamingChat();

  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage, scrollToBottom]);

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
        <div className="divide-y divide-border/30">
          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}
        </div>

        {/* Thinking / Tool call phase */}
        {isProcessing && (streamStatus === "thinking" || streamStatus === "tool_call") && (
          <ThinkingProcess
            status={streamStatus}
            toolCall={currentToolCall}
            streamingText=""
          />
        )}

        {/* Streaming phase — render as a ChatMessage with typewriter cursor */}
        {streamStatus === "streaming" && streamingMessage && (
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
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-border p-4 shrink-0">
        <div className="flex gap-2.5">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about markets, behavior, or content..."
            rows={1}
            className={cn(
              "flex-1 bg-surface border border-border rounded-md px-4 py-2.5",
              "text-sm text-white placeholder:text-muted-foreground mono-data",
              "focus:outline-none focus:border-muted resize-none",
              "transition-colors"
            )}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isProcessing}
            className={cn(
              "px-4 py-2.5 rounded-md text-xs font-semibold tracking-wider mono-data",
              "transition-all duration-200",
              input.trim() && !isProcessing
                ? "bg-white text-black hover:bg-gray-200"
                : "bg-border text-muted-foreground cursor-not-allowed"
            )}
          >
            SEND
          </button>
        </div>
        <p className="text-[10px] text-muted-foreground/50 mt-2 mono-data text-center">
          AI analysis only. Not financial advice. DYOR.
        </p>
      </div>
    </div>
  );
}
