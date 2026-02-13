"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";

function buildUiErrorMessage(
  errorCode: string,
  expectedGoogleRedirectUri: string,
  errorDescription?: string | null
): string {
  const normalizedError = errorCode.toLowerCase();
  const normalizedDescription = (errorDescription ?? "").toLowerCase();

  if (normalizedError.includes("redirect_uri_mismatch")) {
    return `Google OAuth redirect URI mismatch. In Google Cloud Console, add this exact URI: ${expectedGoogleRedirectUri}`;
  }
  if (normalizedError.includes("callback_failed")) {
    if (
      normalizedDescription.includes("code verifier") ||
      normalizedDescription.includes("invalid flow state")
    ) {
      return "OAuth callback failed: PKCE code verifier mismatch. Please access and complete login on the same host (use localhost only, not mixed with 127.0.0.1).";
    }
    return "OAuth callback failed while exchanging the auth code. Please try signing in again.";
  }
  if (normalizedError.includes("missing_code")) {
    return "Missing OAuth code in callback URL. Please restart Google sign-in from the login page.";
  }
  if (normalizedError.includes("auth_failed")) {
    return "Authentication failed. Please retry Google sign-in.";
  }
  if (normalizedError.includes("oauth_url_missing")) {
    return "Supabase did not return an OAuth redirect URL. Check Supabase Auth provider setup.";
  }
  return errorCode;
}

export default function LoginPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);
  const [queryError, setQueryError] = useState<string | null>(null);
  const [queryErrorDescription, setQueryErrorDescription] = useState<string | null>(null);

  useEffect(() => {
    const searchParams = new URLSearchParams(window.location.search);
    const nextQueryError =
      searchParams.get("error") ??
      searchParams.get("oauth_error") ??
      searchParams.get("oauth_error_description");
    const nextErrorDescription = searchParams.get("oauth_error_description");
    setQueryError(nextQueryError);
    setQueryErrorDescription(nextErrorDescription);
  }, []);

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    setLocalError(null);
    try {
      const sameOriginCallback = `${window.location.origin}/auth/callback`;
      const configuredCallback = process.env.NEXT_PUBLIC_AUTH_CALLBACK_URL?.trim();
      let redirectTo = sameOriginCallback;

      if (configuredCallback) {
        try {
          const parsed = new URL(configuredCallback);
          if (parsed.origin === window.location.origin) {
            redirectTo = parsed.toString();
          } else {
            console.warn(
              "NEXT_PUBLIC_AUTH_CALLBACK_URL origin differs from current origin. Falling back to same-origin callback.",
              {
                configuredOrigin: parsed.origin,
                currentOrigin: window.location.origin,
              }
            );
          }
        } catch {
          console.warn(
            "NEXT_PUBLIC_AUTH_CALLBACK_URL is invalid. Falling back to same-origin callback."
          );
        }
      }

      // Supabase Google OAuth
      const { createClient } = await import("@/lib/supabase/client");
      const supabase = createClient();
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: "google",
        options: {
          redirectTo,
          skipBrowserRedirect: true,
        },
      });

      if (error) {
        setLocalError(error.message);
        setIsLoading(false);
        return;
      }

      if (data?.url) {
        window.location.assign(data.url);
        return;
      }

      setLocalError("oauth_url_missing");
      setIsLoading(false);
    } catch (error) {
      console.error("Login failed:", error);
      setLocalError(error instanceof Error ? error.message : "oauth_start_failed");
      setIsLoading(false);
    }
  };

  const expectedGoogleRedirectUri = process.env.NEXT_PUBLIC_SUPABASE_URL
    ? `${process.env.NEXT_PUBLIC_SUPABASE_URL.replace(/\/$/, "")}/auth/v1/callback`
    : "https://<your-project-ref>.supabase.co/auth/v1/callback";
  const errorMessage = localError ?? queryError;
  const uiErrorMessage = errorMessage
    ? buildUiErrorMessage(errorMessage, expectedGoogleRedirectUri, queryErrorDescription)
    : null;

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      {/* Hero video background */}
      <div className="fixed inset-0 overflow-hidden">
        <video
          autoPlay
          muted
          loop
          playsInline
          className="absolute inset-0 w-full h-full object-cover"
        >
          <source src="/videos/hero-reveal.mp4" type="video/mp4" />
        </video>
        <div className="absolute inset-0 bg-black/40" />
      </div>

      <div className="relative z-10 w-full max-w-sm">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-block">
            <div className="flex items-center justify-center gap-3">
              <div className="relative">
                <img
                  src="/tradeiq_favicon.svg"
                  alt="TradeIQ"
                  width={48}
                  height={48}
                  className="rounded-sm"
                />
                <div className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-profit animate-pulse" />
              </div>
              <div className="text-left">
                <div className="text-xl font-bold text-white tracking-wider">TradeIQ</div>
                <div className="text-[10px] text-muted tracking-widest uppercase">AI Trading Analyst</div>
              </div>
            </div>
          </Link>
        </div>

        {/* Login Card */}
        <div className="bg-card/80 backdrop-blur-xl border border-border rounded-sm p-6">
          <h2 className="text-sm font-semibold text-white text-center mb-1 tracking-wide">
            Welcome to TradeIQ
          </h2>
          <p className="text-[11px] text-muted text-center mb-6">
            Sign in to access your AI trading dashboard
          </p>

          {uiErrorMessage && (
            <div className="mb-4 rounded-sm border border-loss/40 bg-loss/10 p-3">
              <p className="text-[10px] leading-relaxed text-loss">{uiErrorMessage}</p>
            </div>
          )}

          {/* Google Sign In */}
          <button
            onClick={handleGoogleLogin}
            disabled={isLoading}
            className={cn(
              "w-full flex items-center justify-center gap-3 px-4 py-3 rounded-sm border border-border",
              "bg-white text-black font-medium text-[12px] tracking-wide",
              "hover:bg-gray-100 transition-all duration-200",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            <svg width="18" height="18" viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
            {isLoading ? "Signing in..." : "Continue with Google"}
          </button>

          {/* Divider */}
          <div className="flex items-center gap-3 my-5">
            <div className="flex-1 h-px bg-border" />
            <span className="text-[9px] text-muted-foreground mono-data tracking-wider">OR</span>
            <div className="flex-1 h-px bg-border" />
          </div>

          {/* Demo Access */}
          <Link
            href="/"
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-sm border border-border bg-surface text-white font-medium text-[12px] tracking-wide hover:bg-surface-hover transition-all duration-200"
          >
            <span className="text-profit">⚡</span>
            Try Demo Mode
          </Link>

          <p className="text-[9px] text-muted-foreground text-center mt-4 mono-data leading-relaxed">
            By signing in, you agree to our Terms of Service.
            <br />
            TradeIQ provides AI analysis for educational purposes only.
          </p>
        </div>

        {/* Footer */}
        <div className="text-center mt-6">
          <p className="text-[9px] text-muted-foreground/50 mono-data">
            Deriv AI Hackathon 2026 &middot; TradeIQ v1.0
          </p>
        </div>
      </div>
    </div>
  );
}
