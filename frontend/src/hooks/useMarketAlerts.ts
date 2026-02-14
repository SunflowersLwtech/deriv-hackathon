"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { TradeIQWebSocket, type MarketAlertData } from "@/lib/websocket";

export interface UseMarketAlertsReturn {
  alerts: MarketAlertData[];
  latestAlert: MarketAlertData | null;
  clearAlerts: () => void;
}

export function useMarketAlerts(userId?: string): UseMarketAlertsReturn {
  const [alerts, setAlerts] = useState<MarketAlertData[]>([]);
  const [latestAlert, setLatestAlert] = useState<MarketAlertData | null>(null);
  const wsRef = useRef<TradeIQWebSocket | null>(null);

  useEffect(() => {
    const ws = new TradeIQWebSocket("/chat/", userId);
    wsRef.current = ws;

    ws.onMarketAlert((alert) => {
      setAlerts((prev) => [alert, ...prev].slice(0, 50));
      setLatestAlert(alert);
    });

    ws.connect();
    return () => ws.disconnect();
  }, [userId]);

  const clearAlerts = useCallback(() => {
    setAlerts([]);
    setLatestAlert(null);
  }, []);

  return { alerts, latestAlert, clearAlerts };
}
