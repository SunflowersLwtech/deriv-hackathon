"use client";

import { useState, useEffect, useRef } from "react";
import { TradeIQWebSocket, type NarrationData } from "@/lib/websocket";

export interface NarrationEntry extends NarrationData {
  id: number;
}

export interface UseNarratorReturn {
  currentNarration: string | null;
  narrationHistory: NarrationEntry[];
  isActive: boolean;
}

let _id = 0;

export function useNarrator(userId?: string): UseNarratorReturn {
  const [currentNarration, setCurrentNarration] = useState<string | null>(null);
  const [narrationHistory, setNarrationHistory] = useState<NarrationEntry[]>([]);
  const [isActive, setIsActive] = useState(false);
  const wsRef = useRef<TradeIQWebSocket | null>(null);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const ws = new TradeIQWebSocket("/chat/", userId);
    wsRef.current = ws;

    ws.onNarration((narr: NarrationData) => {
      setIsActive(true);
      setCurrentNarration(narr.text);
      const entry: NarrationEntry = { ...narr, id: ++_id };
      setNarrationHistory((prev) => [entry, ...prev].slice(0, 20));

      // Clear after 5 seconds
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        setCurrentNarration(null);
        setIsActive(false);
      }, 5000);
    });

    ws.connect();
    return () => {
      ws.disconnect();
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [userId]);

  return { currentNarration, narrationHistory, isActive };
}
