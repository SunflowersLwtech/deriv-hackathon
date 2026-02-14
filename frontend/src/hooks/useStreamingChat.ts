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

const CHAT_STORAGE_KEY = "tradeiq-chat-messages";

// ─── sessionStorage persistence ──────────────────────────────────────
// Survives Next.js chunk re-evaluation on page navigation.

function loadMessages(): ChatMessage[] {
  if (typeof window === "undefined") return [WELCOME];
  try {
    const raw = sessionStorage.getItem(CHAT_STORAGE_KEY);
    if (raw) {
      const parsed: ChatMessage[] = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }
  } catch { /* ignore parse errors */ }
  return [WELCOME];
}

function saveMessages(messages: ChatMessage[]) {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
  } catch { /* quota exceeded — silently ignore */ }
}

export function useStreamingChat(userId?: string): UseStreamingChatReturn {
  const [messages, setMessagesRaw] = useState<ChatMessage[]>(() => loadMessages());
  const [streamingMessage, setStreamingMessage] = useState("");
  const [streamStatus, setStreamStatus] = useState<StreamState>("idle");
  const [currentToolCall, setCurrentToolCall] = useState<ToolCallInfo | null>(null);
  const wsRef = useRef<TradeIQWebSocket | null>(null);
  const streamBufferRef = useRef("");
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Wrapper: every state update also syncs to sessionStorage
  const setMessages = useCallback((action: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => {
    setMessagesRaw((prev) => {
      const next = typeof action === "function" ? action(prev) : action;
      saveMessages(next);
      return next;
    });
  }, []);

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
  }, [clearStreamTimeout, setMessages]);

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

    ws.onStreamDone((fullContent: string) => {
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
      setTimeout(() => setStreamStatus("idle"), 300);
    });

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
  }, [userId, clearStreamTimeout, setMessages]);

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
  }, [startStreamTimeout, setMessages]);

  const clearHistory = useCallback(() => {
    clearStreamTimeout();
    setMessages([WELCOME]);
    setStreamingMessage("");
    setStreamStatus("idle");
  }, [clearStreamTimeout, setMessages]);

  return { messages, streamingMessage, streamStatus, currentToolCall, sendMessage, clearHistory };
}
