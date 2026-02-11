"use client";

import { useState, useEffect, useCallback, useRef } from "react";

interface UseApiWithFallbackOptions<T> {
  /** Async function that calls the real API */
  fetcher: () => Promise<T>;
  /** Fallback state to use when API is unavailable */
  fallbackData: T;
  /** Polling interval in ms (0 = no polling) */
  pollInterval?: number;
  /** Whether to start fetching immediately */
  immediate?: boolean;
}

interface UseApiWithFallbackResult<T> {
  data: T;
  isLoading: boolean;
  error: string | null;
  isUsingMock: boolean;
  refetch: () => Promise<void>;
  /** Whether backend is reachable */
  isBackendOnline: boolean;
}

/**
 * Hook that fetches data from backend API with automatic fallback state.
 * When backend is unavailable, seamlessly uses fallbackData.
 * Periodically retries the backend to detect when it comes back online.
 */
export function useApiWithFallback<T>({
  fetcher,
  fallbackData,
  pollInterval = 0,
  immediate = true,
}: UseApiWithFallbackOptions<T>): UseApiWithFallbackResult<T> {
  const [data, setData] = useState<T>(fallbackData);
  const [isLoading, setIsLoading] = useState(immediate);
  const [error, setError] = useState<string | null>(null);
  const [isUsingMock, setIsUsingMock] = useState(true);
  const [isBackendOnline, setIsBackendOnline] = useState(false);
  const mountedRef = useRef(true);
  // Store fallbackData in a ref so it doesn't cause fetchData to be
  // recreated on every render (callers often pass inline [] or {}).
  const fallbackRef = useRef(fallbackData);
  fallbackRef.current = fallbackData;

  const fetchData = useCallback(async () => {
    try {
      const result = await fetcher();
      if (mountedRef.current) {
        setData(result);
        setIsUsingMock(false);
        setIsBackendOnline(true);
        setError(null);
      }
    } catch (err) {
      if (mountedRef.current) {
        // Keep existing real data if we had it before, otherwise use fallback
        setIsUsingMock((prev) => {
          if (!prev) {
            // We had real data before, keep it but mark the error
            return false;
          }
          // Never had real data, use fallback
          setData(fallbackRef.current);
          return true;
        });
        setIsBackendOnline(false);
        setError(err instanceof Error ? err.message : "Backend unavailable");
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [fetcher]);

  // Initial fetch
  useEffect(() => {
    mountedRef.current = true;
    if (immediate) {
      fetchData();
    }
    return () => {
      mountedRef.current = false;
    };
  }, [fetchData, immediate]);

  // Polling
  useEffect(() => {
    if (pollInterval <= 0) return;

    const interval = setInterval(fetchData, pollInterval);
    return () => clearInterval(interval);
  }, [fetchData, pollInterval]);

  return {
    data,
    isLoading,
    error,
    isUsingMock,
    refetch: fetchData,
    isBackendOnline,
  };
}

/**
 * Simplified helper for one-shot API calls with fallback
 */
export function useApiFetch<T>(
  fetcher: () => Promise<T>,
  fallbackData: T
): UseApiWithFallbackResult<T> {
  return useApiWithFallback({ fetcher, fallbackData });
}
