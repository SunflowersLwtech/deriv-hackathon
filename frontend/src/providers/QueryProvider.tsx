"use client";

import { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

export default function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60_000,            // 1 min — data stays fresh, skip refetch on re-mount
            gcTime: 30 * 60_000,          // 30 min — keep unused data in cache
            retry: 1,
            refetchOnWindowFocus: false,  // polling handles freshness
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
