"use client";

import { useState, useCallback } from "react";
import api, { type TradingTwinResult } from "@/lib/api";

export interface UseTradingTwinReturn {
  twinData: TradingTwinResult | null;
  isLoading: boolean;
  error: string | null;
  generateTwin: (days?: number, startingEquity?: number) => Promise<void>;
}

export function useTradingTwin(userId?: string): UseTradingTwinReturn {
  const [twinData, setTwinData] = useState<TradingTwinResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateTwin = useCallback(
    async (days = 30, startingEquity = 10000) => {
      setIsLoading(true);
      setError(null);
      try {
        // Backend auto-detects authenticated user's profile ID;
        // pass userId prop if provided, otherwise let backend resolve.
        const result = await api.getTradingTwin(
          userId,
          days,
          startingEquity
        );
        setTwinData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to generate Trading Twin");
      } finally {
        setIsLoading(false);
      }
    },
    [userId]
  );

  return { twinData, isLoading, error, generateTwin };
}
