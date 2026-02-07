"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const { createClient } = await import("@/lib/supabase/client");
        const supabase = createClient();

        const { error } = await supabase.auth.getSession();
        if (error) {
          console.error("Auth callback error:", error);
          router.push("/login?error=auth_failed");
          return;
        }

        router.push("/");
      } catch (error) {
        console.error("Callback processing error:", error);
        router.push("/login?error=callback_failed");
      }
    };

    handleCallback();
  }, [router]);

  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <div className="w-12 h-12 bg-gradient-to-br from-profit to-cyan rounded-sm flex items-center justify-center mx-auto mb-4">
          <span className="text-black font-bold text-lg mono-data">TQ</span>
        </div>
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
