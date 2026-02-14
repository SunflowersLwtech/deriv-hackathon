"use client";

type MessageHandler = (data: WebSocketMessage) => void;
type StatusHandler = (status: ConnectionStatus) => void;
type MarketAlertHandler = (alert: MarketAlertData) => void;
type StreamStatusHandler = (status: StreamStatus) => void;
type StreamChunkHandler = (chunk: string) => void;
type StreamDoneHandler = (fullContent: string, meta: StreamDoneMeta) => void;
type NarrationHandler = (narration: NarrationData) => void;

export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

export interface WebSocketMessage {
  type: string;
  content?: string;
  description?: string;
  data?: Record<string, unknown>;
  timestamp?: string;
  // Stream fields
  status?: string;
  full_content?: string;
  agent_type?: string;
  tools_used?: string[];
  // Narration
  text?: string;
  event_type?: string;
  instrument?: string;
  // Legacy
  message?: string;
}

export interface MarketAlertData {
  instrument: string;
  price: number;
  change_pct: number;
  direction: "spike" | "drop";
  magnitude: "medium" | "high";
  timestamp: string;
  analysis_summary: string;
  behavioral_warning: string;
  content_draft: string;
}

export interface StreamStatus {
  status: "thinking" | "tool_call" | "streaming" | "done";
  agent_type?: string;
  tools_used?: string[];
  description?: string;
}

export interface StreamDoneMeta {
  agent_type?: string;
  tools_used?: string[];
}

export interface NarrationData {
  text: string;
  event_type: string;
  instrument: string;
  timestamp: string;
}

export class TradeIQWebSocket {
  private ws: WebSocket | null = null;
  private url: string;
  private messageHandlers: Set<MessageHandler> = new Set();
  private statusHandlers: Set<StatusHandler> = new Set();
  private marketAlertHandlers: Set<MarketAlertHandler> = new Set();
  private streamStatusHandlers: Set<StreamStatusHandler> = new Set();
  private streamChunkHandlers: Set<StreamChunkHandler> = new Set();
  private streamDoneHandlers: Set<StreamDoneHandler> = new Set();
  private narrationHandlers: Set<NarrationHandler> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private status: ConnectionStatus = "disconnected";

  constructor(path: string = "/chat/", userId?: string) {
    const wsBase = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws";
    const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
    this.url = `${wsBase}${path}${query}`;
  }

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;
    this.setStatus("connecting");

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.setStatus("connected");
      };

      this.ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          this._dispatch(parsed);
        } catch {
          console.error("Failed to parse WebSocket message");
        }
      };

      this.ws.onclose = () => {
        this.setStatus("disconnected");
        this.attemptReconnect();
      };

      this.ws.onerror = () => {
        this.setStatus("error");
      };
    } catch {
      this.setStatus("error");
      this.attemptReconnect();
    }
  }

  private _dispatch(parsed: WebSocketMessage): void {
    const msgType = parsed.type;

    // Market alerts from MonitorEngine
    if (msgType === "market_alert") {
      const alertData = (parsed.data || parsed) as unknown as MarketAlertData;
      this.marketAlertHandlers.forEach((h) => h(alertData));
      return;
    }

    // Streaming protocol
    if (msgType === "stream_status") {
      const ss: StreamStatus = {
        status: (parsed.status as StreamStatus["status"]) || "thinking",
        agent_type: parsed.agent_type,
        tools_used: parsed.tools_used,
        description: parsed.description || parsed.content,
      };
      this.streamStatusHandlers.forEach((h) => h(ss));
      return;
    }
    if (msgType === "stream_chunk") {
      this.streamChunkHandlers.forEach((h) => h(parsed.content || ""));
      return;
    }
    if (msgType === "stream_done") {
      const meta: StreamDoneMeta = {
        agent_type: parsed.agent_type,
        tools_used: parsed.tools_used,
      };
      this.streamDoneHandlers.forEach((h) => h(parsed.full_content || "", meta));
      return;
    }

    // Narration from Live Narrator
    if (msgType === "narration") {
      const narr: NarrationData = {
        text: parsed.text || "",
        event_type: parsed.event_type || "",
        instrument: parsed.instrument || "",
        timestamp: parsed.timestamp || "",
      };
      this.narrationHandlers.forEach((h) => h(narr));
      return;
    }

    // Generic messages (system, reply, thinking, nudge, etc.)
    this.messageHandlers.forEach((handler) => handler(parsed));
  }

  disconnect(): void {
    this.reconnectAttempts = this.maxReconnectAttempts;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.setStatus("disconnected");
  }

  send(message: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  sendMessage(content: string, agentType: string = "auto"): void {
    this.send({ type: "chat.message", message: content, agent_type: agentType, stream: true });
  }

  // ── Listener registration ──

  onMessage(handler: MessageHandler): () => void {
    this.messageHandlers.add(handler);
    return () => this.messageHandlers.delete(handler);
  }

  onStatusChange(handler: StatusHandler): () => void {
    this.statusHandlers.add(handler);
    return () => this.statusHandlers.delete(handler);
  }

  onMarketAlert(handler: MarketAlertHandler): () => void {
    this.marketAlertHandlers.add(handler);
    return () => this.marketAlertHandlers.delete(handler);
  }

  onStreamStatus(handler: StreamStatusHandler): () => void {
    this.streamStatusHandlers.add(handler);
    return () => this.streamStatusHandlers.delete(handler);
  }

  onStreamChunk(handler: StreamChunkHandler): () => void {
    this.streamChunkHandlers.add(handler);
    return () => this.streamChunkHandlers.delete(handler);
  }

  onStreamDone(handler: StreamDoneHandler): () => void {
    this.streamDoneHandlers.add(handler);
    return () => this.streamDoneHandlers.delete(handler);
  }

  onNarration(handler: NarrationHandler): () => void {
    this.narrationHandlers.add(handler);
    return () => this.narrationHandlers.delete(handler);
  }

  getStatus(): ConnectionStatus {
    return this.status;
  }

  private setStatus(status: ConnectionStatus): void {
    this.status = status;
    this.statusHandlers.forEach((handler) => handler(status));
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) return;
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    setTimeout(() => this.connect(), delay);
  }
}
