"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";

export default function DerivOAuthCallbackPage() {
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const processCallback = async () => {
      try {
        const params = new URLSearchParams(window.location.search);

        // Parse acct1/token1/cur1, acct2/token2/cur2, ... from URL
        const accounts: Array<{ login_id: string; token: string; currency: string }> = [];
        for (let i = 1; ; i++) {
          const loginId = params.get(`acct${i}`);
          const token = params.get(`token${i}`);
          const currency = params.get(`cur${i}`) || "USD";

          if (!loginId || !token) break;

          accounts.push({
            login_id: loginId,
            token: token,
            currency: currency.toUpperCase(),
          });
        }

        if (accounts.length === 0) {
          setStatus("error");
          setErrorMessage("No Deriv accounts found in the callback URL.");
          return;
        }

        // Remove sensitive tokens from the address bar ASAP.
        try {
          window.history.replaceState({}, "", "/auth/deriv/callback");
        } catch {
          // ignore
        }

        await api.saveDerivOAuthTokens(accounts);
        setStatus("success");

        // Redirect to trading page after a brief success message
        setTimeout(() => {
          router.replace("/trading");
        }, 2000);
      } catch (err) {
        console.error("Deriv OAuth callback error:", err);
        setStatus("error");
        setErrorMessage(
          err instanceof Error ? err.message : "Failed to connect Deriv account."
        );
      }
    };

    void processCallback();
  }, [router]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center max-w-sm">
        <img
          src="/tradeiq_favicon.svg"
          alt="TradeIQ"
          width={48}
          height={48}
          className="rounded-sm mx-auto mb-4"
        />

        {status === "loading" && (
          <>
            <div className="flex items-center gap-2 justify-center">
              {[0, 1, 2].map((i) => (
                <div
                  key={i}
                  className="w-2 h-2 rounded-full bg-profit animate-pulse"
                  style={{ animationDelay: `${i * 200}ms` }}
                />
              ))}
            </div>
            <p className="text-[11px] text-muted mono-data mt-3">
              Connecting your Deriv account...
            </p>
          </>
        )}

        {status === "success" && (
          <>
            <div className="w-10 h-10 rounded-full bg-profit/20 flex items-center justify-center mx-auto mb-3">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-profit"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <p className="text-sm font-semibold text-white mb-1">
              Deriv Account Connected
            </p>
            <p className="text-[11px] text-muted mono-data">
              Redirecting to trading dashboard...
            </p>
          </>
        )}

        {status === "error" && (
          <>
            <div className="w-10 h-10 rounded-full bg-loss/20 flex items-center justify-center mx-auto mb-3">
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-loss"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </div>
            <p className="text-sm font-semibold text-white mb-1">
              Connection Failed
            </p>
            <p className="text-[11px] text-loss mono-data mb-4">{errorMessage}</p>
            <button
              onClick={() => router.replace("/login")}
              className="px-4 py-2 rounded-sm border border-border bg-surface text-white text-[11px] mono-data hover:bg-surface-hover transition-colors"
            >
              Back to Login
            </button>
          </>
        )}
      </div>
    </div>
  );
}
