/**
 * Module-level Map that persists across page navigations.
 * Imported by layout.tsx to guarantee the module stays in memory.
 */
export const _pageCache = new Map<string, unknown>();
