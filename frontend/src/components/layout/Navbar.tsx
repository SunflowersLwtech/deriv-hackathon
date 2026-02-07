"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useState } from "react";

const navLinks = [
  { href: "/", label: "LIVE" },
  { href: "/market", label: "MARKET" },
  { href: "/behavior", label: "BEHAVIOR" },
  { href: "/content", label: "CONTENT" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <nav className="glass sticky top-0 z-50 border-b border-border">
      <div className="flex items-center justify-between px-4 h-14">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <div className="relative">
            <div className="w-8 h-8 bg-gradient-to-br from-profit to-cyan rounded-sm flex items-center justify-center">
              <span className="text-black font-bold text-sm mono-data">TQ</span>
            </div>
            <div className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-profit animate-pulse" />
          </div>
          <div className="flex flex-col">
            <span className="text-white font-bold text-sm tracking-wider">TradeIQ</span>
            <span className="text-muted text-[9px] tracking-widest uppercase">AI Analyst</span>
          </div>
        </Link>

        {/* Desktop Nav Links */}
        <div className="hidden md:flex items-center gap-0">
          {navLinks.map((link, i) => (
            <div key={link.href} className="flex items-center">
              {i > 0 && <span className="text-border mx-1">|</span>}
              <Link
                href={link.href}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium tracking-wider transition-colors mono-data",
                  pathname === link.href
                    ? "text-white"
                    : "text-muted hover:text-white"
                )}
              >
                {link.label}
              </Link>
            </div>
          ))}
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2">
            <div className="live-dot" />
            <span className="text-[10px] text-profit tracking-wider mono-data">LIVE</span>
          </div>

          <Link
            href="/login"
            className="px-3 py-1.5 text-[10px] font-medium tracking-wider text-black bg-white hover:bg-gray-200 transition-colors rounded-sm flex items-center gap-1"
          >
            SIGN IN
            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M7 17L17 7M17 7H7M17 7V17" />
            </svg>
          </Link>

          {/* Mobile menu button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-1.5 text-muted hover:text-white transition-colors"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
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
                "block px-4 py-3 text-xs font-medium tracking-wider mono-data border-b border-border/50",
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
