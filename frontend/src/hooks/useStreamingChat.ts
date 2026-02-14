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
  skipAnimation: true,
};

/** Timeout for stream responses (45 seconds) */
const STREAM_TIMEOUT_MS = 45_000;

export function useStreamingChat(userId?: string): UseStreamingChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME]);
  const [streamingMessage, setStreamingMessage] = useState("");
  const [streamStatus, setStreamStatus] = useState<StreamState>("idle");
  const [currentToolCall, setCurrentToolCall] = useState<ToolCallInfo | null>(null);
  const wsRef = useRef<TradeIQWebSocket | null>(null);
  const streamBufferRef = useRef("");
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  /** Clear any pending timeout */
  const clearStreamTimeout = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  /** Reset stream state back to idle, adding an error message if provided */
  const resetStream = useCallback((errorContent?: string) => {
    clearStreamTimeout();
    setStreamStatus("idle");
    setStreamingMessage("");
    streamBufferRef.current = "";
    setCurrentToolCall(null);
    if (errorContent) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: errorContent,
          timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
          type: "normal",
          skipAnimation: true,
        },
      ]);
    }
  }, [clearStreamTimeout]);

  /** Start a timeout that auto-resets if stream_done never arrives */
  const startStreamTimeout = useCallback(() => {
    clearStreamTimeout();
    timeoutRef.current = setTimeout(() => {
      resetStream("Request timed out. Please try again.");
    }, STREAM_TIMEOUT_MS);
  }, [clearStreamTimeout, resetStream]);

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
      clearStreamTimeout();
      setStreamStatus("done");
      setStreamingMessage("");
      streamBufferRef.current = "";
      setCurrentToolCall(null);
      const aiMsg: ChatMessage = {
        role: "assistant",
        content: fullContent,
        timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
        type: "normal",
        skipAnimation: true,
      };
      setMessages((prev) => [...prev, aiMsg]);
      // Reset after short delay
      setTimeout(() => setStreamStatus("idle"), 300);
    });

    // Handle legacy non-stream replies
    ws.onMessage((data: WebSocketMessage) => {
      if (data.type === "reply") {
        clearStreamTimeout();
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
    return () => {
      clearStreamTimeout();
      ws.disconnect();
    };
  }, [userId, clearStreamTimeout]);

  const sendMessage = useCallback((text: string, agentType: string = "auto") => {
    if (!text.trim()) return;
    const userMsg: ChatMessage = {
      role: "user",
      content: text.trim(),
      timestamp: new Date().toLocaleTimeString("en-US", { hour12: false }),
      type: "normal",
    };
    setMessages((prev) => [...prev, userMsg]);
    startStreamTimeout();
    wsRef.current?.sendMessage(text.trim(), agentType);
  }, [startStreamTimeout]);

  const clearHistory = useCallback(() => {
    clearStreamTimeout();
    setMessages([WELCOME]);
    setStreamingMessage("");
    setStreamStatus("idle");
  }, [clearStreamTimeout]);

  return { messages, streamingMessage, streamStatus, currentToolCall, sendMessage, clearHistory };
}
