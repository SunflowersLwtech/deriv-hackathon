"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { cn } from "@/lib/utils";
import ChatMessage from "./ChatMessage";
import LoadingDots from "@/components/ui/LoadingDots";
import type { ChatMessage as ChatMessageType } from "@/lib/api";
import api from "@/lib/api";

const WELCOME_MESSAGE: ChatMessageType = {
  role: "assistant",
  content:
    "Welcome to TradeIQ. I'm your AI trading analyst. I can help you with:\n\n• Market analysis and insights\n• Technical indicator explanations\n• Behavioral pattern feedback\n• Content generation for social media\n\nWhat would you like to explore?",
  timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
  type: "normal",
};

export default function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessageType[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: ChatMessageType = {
      role: "user",
      content: input.trim(),
      timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await api.chatAsk(input.trim(), messages);

      const aiMessage: ChatMessageType = {
        role: "assistant",
        content: response.reply,
        timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
        type: "normal",
      };
      setMessages((prev) => [...prev, aiMessage]);

      if (response.nudge) {
        const nudgeMessage: ChatMessageType = {
          role: "assistant",
          content: response.nudge,
          timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
          type: "nudge",
        };
        setMessages((prev) => [...prev, nudgeMessage]);
      }

      if (response.disclaimer) {
        const disclaimerMessage: ChatMessageType = {
          role: "assistant",
          content: response.disclaimer,
          type: "disclaimer",
        };
        setMessages((prev) => [...prev, disclaimerMessage]);
      }
    } catch {
      const errorMessage: ChatMessageType = {
        role: "assistant",
        content: "I'm having trouble connecting to the analysis engine. Please try again in a moment.",
        timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
        type: "normal",
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        <div className="divide-y divide-border/30">
          {messages.map((msg, i) => (
            <ChatMessage key={i} message={msg} />
          ))}
        </div>

        {isLoading && (
          <div className="px-3 py-3 bg-surface/50">
            <div className="flex items-center gap-2 mb-1.5">
              <div className="w-5 h-5 rounded-sm bg-profit/20 flex items-center justify-center">
                <span className="text-[9px] text-profit mono-data font-bold">AI</span>
              </div>
              <span className="text-[9px] font-semibold tracking-wider mono-data text-profit">
                TRADEIQ
              </span>
            </div>
            <div className="pl-7">
              <LoadingDots />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-border p-3 shrink-0">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about markets, behavior, or content..."
            rows={1}
            className={cn(
              "flex-1 bg-surface border border-border rounded-sm px-3 py-2",
              "text-[11px] text-white placeholder:text-muted-foreground mono-data",
              "focus:outline-none focus:border-muted resize-none",
              "transition-colors"
            )}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            className={cn(
              "px-3 py-2 rounded-sm text-[10px] font-semibold tracking-wider mono-data",
              "transition-all duration-200",
              input.trim() && !isLoading
                ? "bg-white text-black hover:bg-gray-200"
                : "bg-border text-muted-foreground cursor-not-allowed"
            )}
          >
            SEND
          </button>
        </div>
        <p className="text-[8px] text-muted-foreground/40 mt-1.5 mono-data text-center">
          ⚠ AI analysis only. Not financial advice. DYOR.
        </p>
      </div>
    </div>
  );
}
