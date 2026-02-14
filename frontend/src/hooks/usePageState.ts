"use client";

import { useState, useCallback, useRef } from "react";
import type { Dispatch, SetStateAction } from "react";
import { _pageCache } from "@/lib/pageCache";

/**
 * Drop-in replacement for useState that persists values in a module-level Map.
 * The Map lives in pageCache.ts (imported by layout.tsx → always in memory).
 *
 * Works even after component unmount: setValue updates the Map directly,
 * so background async functions can still persist their results.
 * On remount, useState initializer reads the cached value from the Map.
 */
export function usePageState<T>(key: string, initial: T): [T, Dispatch<SetStateAction<T>>] {
  const initialRef = useRef(initial);

  const [value, setValueRaw] = useState<T>(() =>
    _pageCache.has(key) ? (_pageCache.get(key) as T) : initial,
  );

  const setValue: Dispatch<SetStateAction<T>> = useCallback(
    (action: SetStateAction<T>) => {
      const prev = (_pageCache.has(key) ? _pageCache.get(key) : initialRef.current) as T;
      const next = typeof action === "function" ? (action as (prev: T) => T)(prev) : action;
      _pageCache.set(key, next);
      setValueRaw(next); // no-op after unmount, but Map is updated
    },
    [key],
  );

  return [value, setValue];
}
