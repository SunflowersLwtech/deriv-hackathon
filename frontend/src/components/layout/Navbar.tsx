"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { useEffect, useMemo, useState } from "react";
import type { Session } from "@supabase/supabase-js";

const navLinks = [
  { href: "/", label: "LIVE" },
  { href: "/market", label: "MARKET" },
  { href: "/behavior", label: "BEHAVIOR" },
  { href: "/copytrading", label: "COPY" },
  { href: "/trading", label: "TRADE" },
  { href: "/content", label: "CONTENT" },
  { href: "/pipeline", label: "AGENTS" },
  { href: "/demo", label: "DEMO" },
];

export default function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [session, setSession] = useState<Session | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [isSigningOut, setIsSigningOut] = useState(false);

  useEffect(() => {
    let isMounted = true;
    let unsubscribe: (() => void) | undefined;

    const initAuth = async () => {
      try {
        const { createClient } = await import("@/lib/supabase/client");
        const supabase = createClient();

        const { data } = await supabase.auth.getSession();
        if (isMounted) {
          setSession(data.session ?? null);
          setIsAuthLoading(false);
        }

        const {
          data: { subscription },
        } = supabase.auth.onAuthStateChange((_event, nextSession) => {
          if (!isMounted) {
            return;
          }
          setSession(nextSession ?? null);
          setIsAuthLoading(false);
        });
        unsubscribe = () => subscription.unsubscribe();
      } catch (error) {
        console.error("Failed to initialize auth state in Navbar:", error);
        if (isMounted) {
          setSession(null);
          setIsAuthLoading(false);
        }
      }
    };

    void initAuth();

    return () => {
      isMounted = false;
      if (unsubscribe) {
        unsubscribe();
      }
    };
  }, []);

  const displayName = useMemo(() => {
    const email = session?.user?.email ?? "";
    if (!email) {
      return "ACCOUNT";
    }
    return email.split("@")[0].slice(0, 12).toUpperCase();
  }, [session?.user?.email]);

  const handleSignOut = async () => {
    setIsSigningOut(true);
    try {
      const { createClient } = await import("@/lib/supabase/client");
      const supabase = createClient();
      await supabase.auth.signOut();
      setSession(null);
      router.push("/login");
      router.refresh();
    } catch (error) {
      console.error("Sign out failed:", error);
    } finally {
      setIsSigningOut(false);
    }
  };

  return (
    <nav className="sticky top-0 z-50 bg-[#131722] border-b border-[#2a2e39]">
      <div className="flex items-center h-[60px] px-6 lg:px-10">
        {/* Left: Logo */}
        <Link href="/" className="flex items-center gap-3 shrink-0">
          <Image
            src="/tradeiq_favicon.svg"
            alt="TradeIQ"
            width={36}
            height={36}
            className="rounded-md"
            priority
          />
          <span className="text-white font-bold text-[20px] tracking-tight">
            TradeIQ
          </span>
        </Link>

        {/* Center: Desktop Nav Links */}
        <div className="hidden md:flex items-center justify-center flex-1 gap-8">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={cn(
                "px-4 py-1.5 text-[16px] transition-all duration-200 rounded-full",
                pathname === link.href
                  ? "text-[#4d8bff] font-semibold bg-[#4d8bff]/10"
                  : "text-white font-normal hover:text-[#4d8bff] hover:bg-[#4d8bff]/10"
              )}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Right: Live Status + Auth + Mobile Toggle */}
        <div className="flex items-center gap-4 shrink-0 ml-auto md:ml-0">
          <div className="hidden sm:flex items-center gap-1.5">
            <div className="live-dot" />
            <span className="text-[12px] text-[#26a69a] font-medium">
              LIVE
            </span>
          </div>

          {isAuthLoading ? (
            <span className="px-3 py-1.5 text-[13px] font-medium text-[#787b86]">
              ...
            </span>
          ) : session ? (
            <div className="flex items-center gap-3">
              <span className="hidden lg:inline-block text-[13px] text-[#787b86] font-medium">
                {displayName}
              </span>
              <button
                onClick={handleSignOut}
                disabled={isSigningOut}
                className="px-4 py-1.5 text-[13px] font-medium text-[#d1d4dc] hover:text-white border border-[#2a2e39] hover:border-[#363a45] transition-colors rounded disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSigningOut ? "Signing out..." : "Sign Out"}
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="px-5 py-[7px] text-[13px] font-semibold text-white bg-[#2962ff] hover:bg-[#1e53e5] transition-colors rounded flex items-center gap-1.5"
            >
              Get Started
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M7 17L17 7M17 7H7M17 7V17" />
              </svg>
            </Link>
          )}

          {/* Mobile menu button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-1.5 text-[#787b86] hover:text-white transition-colors"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {isMobileMenuOpen ? (
                <path d="M18 6L6 18M6 6L18 18" />
              ) : (
                <path d="M3 12h18M3 6h18M3 18h18" />
              )}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden border-t border-[#2a2e39] bg-[#1e222d] animate-fade-in">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setIsMobileMenuOpen(false)}
              className={cn(
                "block px-6 py-3 text-[14px] font-medium border-b border-[#2a2e39]/50 transition-colors",
                pathname === link.href
                  ? "text-[#4d8bff] bg-[#4d8bff]/10"
                  : "text-white hover:text-[#4d8bff] hover:bg-[#4d8bff]/10"
              )}
            >
              {link.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
