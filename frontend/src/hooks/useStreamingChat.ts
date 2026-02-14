"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { TradeIQWebSocket, type StreamStatus, type WebSocketMessage } from "@/lib/websocket";
import type { ChatMessage } from "@/lib/api";

export type StreamState = "idle" | "thinking" | "tool_call" | "streaming" | "done";

export interface ToolCallInfo {
  tools_used: string[];
  description: string;
}

export interface UseStreamingChatReturn {
  messages: ChatMessage[];
  streamingMessage: string;
  streamStatus: StreamState;
  currentToolCall: ToolCallInfo | null;
  sendMessage: (text: string, agentType?: string) => void;
  clearHistory: () => void;
}

const WELCOME: ChatMessage = {
  role: "assistant",
  content:
    "Welcome to TradeIQ. I'm your AI trading analyst. Ask me about markets, your trading patterns, or content creation.",
  timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
  type: "normal",
};

export function useStreamingChat(userId?: string): UseStreamingChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [streamingMessage, setStreamingMessage] = useState("");
  const [streamStatus, setStreamStatus] = useState<StreamState>("idle");
  const [currentToolCall, setCurrentToolCall] = useState<ToolCallInfo | null>(null);
  const wsRef = useRef<TradeIQWebSocket | null>(null);
  const streamBufferRef = useRef("");

  useEffect(() => {
    const ws = new TradeIQWebSocket("/chat/", userId);
    wsRef.current = ws;

    ws.onStreamStatus((status: StreamStatus) => {
      if (status.status === "thinking") {
        setStreamStatus("thinking");
        setCurrentToolCall(null);
        streamBufferRef.current = "";
        setStreamingMessage("");
      } else if (status.status === "tool_call") {
        setStreamStatus("tool_call");
        setCurrentToolCall({
          tools_used: status.tools_used || [],
          description: status.description || "",
        });
      }
    });

    ws.onStreamChunk((chunk: string) => {
      setStreamStatus("streaming");
      streamBufferRef.current += chunk;
      setStreamingMessage(streamBufferRef.current);
    });

    ws.onStreamDone((fullContent: string, meta) => {
      setStreamStatus("done");
      setStreamingMessage("");
      streamBufferRef.current = "";
      setCurrentToolCall(null);
      const aiMsg: ChatMessage = {
        role: "assistant",
        content: fullContent,
        timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
        type: "normal",
      };
      setMessages((prev) => [...prev, aiMsg]);
      // Reset after short delay
      setTimeout(() => setStreamStatus("idle"), 300);
    });

    // Handle legacy non-stream replies
    ws.onMessage((data: WebSocketMessage) => {
      if (data.type === "reply") {
        const content = (data.message as string) || (data.content as string) || "";
        const aiMsg: ChatMessage = {
          role: "assistant",
          content,
          timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
          type: "normal",
        };
        setMessages((prev) => [...prev, aiMsg]);
        setStreamStatus("idle");
      }
    });

    ws.connect();
    return () => ws.disconnect();
  }, [userId]);

  const sendMessage = useCallback((text: string, agentType: string = "auto") => {
    if (!text.trim()) return;
    const userMsg: ChatMessage = {
      role: "user",
      content: text.trim(),
      timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
      type: "normal",
    };
    setMessages((prev) => [...prev, userMsg]);
    wsRef.current?.sendMessage(text.trim(), agentType);
  }, []);

  const clearHistory = useCallback(() => {
    setMessages([WELCOME]);
    setStreamingMessage("");
    setStreamStatus("idle");
  }, []);

  return { messages, streamingMessage, streamStatus, currentToolCall, sendMessage, clearHistory };
}
