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
      <div style={{ padding: '24px 24px 56px' }} className="border-t border-white/10 bg-card/80 backdrop-blur-sm shrink-0">
        <div className="flex gap-3 items-stretch" style={{ height: '52px' }}>
          <button
            onClick={clearHistory}
            disabled={isProcessing || messages.length <= 1}
            title="Clear conversation"
            style={{ width: '52px', color: '#ffffff', borderColor: '#ffffff55' }}
            className={cn(
              "flex items-center justify-center rounded-xl transition-all duration-200 shrink-0 border",
              !isProcessing && messages.length > 1
                ? "hover:text-loss hover:bg-loss/10"
                : "cursor-not-allowed"
            )}
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 6h18" /><path d="M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2" /><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6" />
            </svg>
          </button>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder=""
            rows={1}
            disabled={isProcessing}
            style={{ fontSize: '18px', color: '#ffffff', borderColor: '#ffffff55', height: '52px', overflowY: 'auto' }}
            className={cn(
              "flex-1 bg-white/[0.08] border rounded-xl px-5",
              "placeholder:text-white",
              "focus:outline-none focus:border-accent/50 focus:ring-2 focus:ring-accent/20 resize-none",
              "transition-all duration-200",
              isProcessing && "opacity-50 cursor-not-allowed"
            )}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || isProcessing}
            style={{ fontSize: '16px', color: input.trim() && !isProcessing ? '#000000' : '#ffffff', backgroundColor: input.trim() && !isProcessing ? '#ffffff' : 'rgba(255,255,255,0.15)', borderColor: '#ffffff55' }}
            className={cn(
              "px-7 rounded-xl font-bold tracking-wider flex items-center justify-center border",
              "transition-all duration-200",
              input.trim() && !isProcessing
                ? "hover:bg-gray-200 active:scale-[0.97]"
                : "cursor-not-allowed"
            )}
          >
            {isProcessing ? "..." : "SEND"}
          </button>
        </div>
      </div>
    </div>
  );
}
