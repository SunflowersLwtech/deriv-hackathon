"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";

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

let _anonCounter = 0;

/**
 * Hook that fetches data from backend API with automatic fallback state.
 * Powered by TanStack Query — data is cached across page navigations.
 * When backend is unavailable, seamlessly uses fallbackData.
 */
export function useApiWithFallback<T>({
  fetcher,
  fallbackData,
  pollInterval = 0,
  immediate = true,
  cacheKey,
}: UseApiWithFallbackOptions<T>): UseApiWithFallbackResult<T> {
  // Stable unique key for hooks that don't specify a cacheKey
  const [stableKey] = useState(() => cacheKey || `_anon_${++_anonCounter}`);

  const {
    data,
    isPending,
    isError,
    error,
    refetch,
    isPlaceholderData,
  } = useQuery({
    queryKey: [stableKey],
    queryFn: fetcher,
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    placeholderData: fallbackData as any,
    enabled: immediate,
    refetchInterval: pollInterval > 0 ? pollInterval : undefined,
  });

  // Stable refetch wrapper matching the original Promise<void> signature
  const wrappedRefetch = useCallback(async () => {
    await refetch();
  }, [refetch]);

  return {
    data: data ?? fallbackData,
    isLoading: isPending,
    error: isError ? (error instanceof Error ? error.message : "Backend unavailable") : null,
    isUsingMock: isPlaceholderData,
    refetch: wrappedRefetch,
    isBackendOnline: !isError,
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
