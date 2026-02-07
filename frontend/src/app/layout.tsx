import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TradeIQ | AI Trading Analyst",
  description:
    "The Bloomberg Terminal for retail traders. AI-powered market analysis, behavioral coaching, and social content generation.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
