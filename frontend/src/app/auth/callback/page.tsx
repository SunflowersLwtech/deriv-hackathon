"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const code = searchParams.get("code");
    const oauthError = searchParams.get("error");
    const oauthErrorDescription = searchParams.get("error_description");

    const redirectToLogin = (error: string, description?: string | null) => {
      const params = new URLSearchParams();
      params.set("error", error);
      if (description) {
        params.set("oauth_error_description", description);
      }
      router.replace(`/login?${params.toString()}`);
    };

    const handleCallback = async () => {
      if (oauthError) {
        redirectToLogin(oauthError, oauthErrorDescription);
        return;
      }

      if (!code) {
        redirectToLogin("missing_code");
        return;
      }

      try {
        const { createClient } = await import("@/lib/supabase/client");
        const supabase = createClient();

        const { data, error } = await supabase.auth.exchangeCodeForSession(code);
        if (error) {
          const { data: sessionData } = await supabase.auth.getSession();
          if (sessionData?.session) {
            router.replace("/");
            return;
          }

          console.error("Auth callback error:", error);
          redirectToLogin("callback_failed", error.message);
          return;
        }

        if (!data?.session) {
          const { data: sessionData } = await supabase.auth.getSession();
          if (!sessionData?.session) {
            redirectToLogin("callback_failed", "Session not found after code exchange");
            return;
          }
        }

        router.replace("/");
      } catch (error) {
        console.error("Callback processing error:", error);
        redirectToLogin(
          "callback_failed",
          error instanceof Error ? error.message : "unknown_error"
        );
      }
    };

    void handleCallback();
  }, [router]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <img
          src="/tradeiq_favicon.svg"
          alt="TradeIQ"
          width={48}
          height={48}
          className="rounded-sm mx-auto mb-4"
        />
        <div className="flex items-center gap-2 justify-center">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-2 h-2 rounded-full bg-profit animate-pulse"
              style={{ animationDelay: `${i * 200}ms` }}
            />
          ))}
        </div>
        <p className="text-[11px] text-muted mono-data mt-3">Completing sign in...</p>
      </div>
    </div>
  );
}
