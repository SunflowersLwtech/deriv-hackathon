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
    <nav className="glass sticky top-0 z-50 border-b border-border">
      <div className="flex items-center justify-between px-6 h-[60px]">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 shrink-0">
          <div className="relative">
            <Image
              src="/tradeiq_favicon.svg"
              alt="TradeIQ"
              width={36}
              height={36}
              className="rounded-md"
              priority
            />
            <div className="absolute -top-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-profit animate-pulse" />
          </div>
          <div className="flex flex-col">
            <span className="text-white font-bold text-base tracking-wider">TradeIQ</span>
            <span className="text-muted text-[10px] tracking-widest uppercase">AI Analyst</span>
          </div>
        </Link>

        {/* Desktop Nav Links */}
        <div className="hidden md:flex items-center gap-1">
          {navLinks.map((link, i) => (
            <div key={link.href} className="flex items-center">
              {i > 0 && <span className="text-border mx-1.5">|</span>}
              <Link
                href={link.href}
                className={cn(
                  "px-4 py-2 text-sm font-medium tracking-wider transition-colors mono-data rounded-sm",
                  pathname === link.href
                    ? "text-white bg-surface"
                    : "text-muted hover:text-white hover:bg-surface/50"
                )}
              >
                {link.label}
              </Link>
            </div>
          ))}
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2">
            <div className="live-dot" />
            <span className="text-xs text-profit tracking-wider mono-data">LIVE</span>
          </div>

          {isAuthLoading ? (
            <span className="px-4 py-2 text-xs font-medium tracking-wider text-muted border border-border rounded-md mono-data">
              AUTH...
            </span>
          ) : session ? (
            <div className="flex items-center gap-3">
              <span className="hidden lg:inline-block text-xs text-muted mono-data">
                {displayName}
              </span>
              <button
                onClick={handleSignOut}
                disabled={isSigningOut}
                className="px-4 py-2 text-xs font-medium tracking-wider text-white bg-surface hover:bg-surface-hover transition-colors rounded-md border border-border disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSigningOut ? "SIGNING OUT..." : "SIGN OUT"}
              </button>
            </div>
          ) : (
            <Link
              href="/login"
              className="px-4 py-2 text-xs font-medium tracking-wider text-black bg-white hover:bg-gray-200 transition-colors rounded-md flex items-center gap-1.5"
            >
              SIGN IN
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M7 17L17 7M17 7H7M17 7V17" />
              </svg>
            </Link>
          )}

          {/* Mobile menu button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 text-muted hover:text-white transition-colors"
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
        <div className="md:hidden border-t border-border animate-fade-in">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setIsMobileMenuOpen(false)}
              className={cn(
                "block px-5 py-3.5 text-sm font-medium tracking-wider mono-data border-b border-border/50",
                pathname === link.href
                  ? "text-white bg-surface"
                  : "text-muted hover:text-white hover:bg-surface"
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
