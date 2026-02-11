"use client";

import { useState, useEffect, useCallback, useRef } from "react";

// Module-level cache persists across page navigations (component unmount/remount).
// This gives stale-while-revalidate behavior: show old data instantly, refresh in background.
const _hookCache = new Map<string, unknown>();

interface UseApiWithFallbackOptions<T> {
  /** Async function that calls the real API */
  fetcher: () => Promise<T>;
  /** Fallback state to use when API is unavailable */
  fallbackData: T;
  /** Polling interval in ms (0 = no polling) */
  pollInterval?: number;
  /** Whether to start fetching immediately */
  immediate?: boolean;
  /** Cache key for persisting data across page navigations */
  cacheKey?: string;
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
  cacheKey,
}: UseApiWithFallbackOptions<T>): UseApiWithFallbackResult<T> {
  // Initialize from module cache if available (survives page navigation)
  const cached = cacheKey ? (_hookCache.get(cacheKey) as T | undefined) : undefined;
  const hasCache = cached !== undefined;

  const [data, setData] = useState<T>(hasCache ? cached : fallbackData);
  const [isLoading, setIsLoading] = useState(!hasCache && immediate);
  const [error, setError] = useState<string | null>(null);
  const [isUsingMock, setIsUsingMock] = useState(!hasCache);
  const [isBackendOnline, setIsBackendOnline] = useState(hasCache);
  const mountedRef = useRef(true);
  const fallbackRef = useRef(fallbackData);
  fallbackRef.current = fallbackData;
  const cacheKeyRef = useRef(cacheKey);
  cacheKeyRef.current = cacheKey;

  const fetchData = useCallback(async () => {
    try {
      const result = await fetcher();
      if (mountedRef.current) {
        setData(result);
        setIsUsingMock(false);
        setIsBackendOnline(true);
        setError(null);
        if (cacheKeyRef.current) {
          _hookCache.set(cacheKeyRef.current, result);
        }
      }
    } catch (err) {
      if (mountedRef.current) {
        setIsUsingMock((prev) => {
          if (!prev) {
            return false;
          }
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
