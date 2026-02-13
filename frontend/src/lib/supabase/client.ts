"use client";

import { createBrowserClient } from "@supabase/ssr";

function requirePublicEnv(name: string, value: string | undefined): string {
  const normalized = (value ?? "").trim();
  if (!normalized) {
    throw new Error(`Missing required env var: ${name}`);
  }
  return normalized;
}

export function createClient() {
  const supabaseUrl = requirePublicEnv(
    "NEXT_PUBLIC_SUPABASE_URL",
    process.env.NEXT_PUBLIC_SUPABASE_URL
  );
  const supabaseAnonKey = requirePublicEnv(
    "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
  );

  const lowerKey = supabaseAnonKey.toLowerCase();
  if (
    lowerKey === "your-supabase-anon-key" ||
    lowerKey === "your_anon_key_here" ||
    (lowerKey.includes("your") && lowerKey.includes("key") && !lowerKey.startsWith("ey"))
  ) {
    throw new Error(
      "NEXT_PUBLIC_SUPABASE_ANON_KEY is still a placeholder. Set a real Supabase anon/publishable key."
    );
  }

  return createBrowserClient(
    supabaseUrl,
    supabaseAnonKey,
    {
      auth: {
        // Callback page does an explicit exchangeCodeForSession(code),
        // so disable automatic URL detection to avoid duplicate exchanges.
        detectSessionInUrl: false,
      },
    }
  );
}
