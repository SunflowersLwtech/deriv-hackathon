import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import QueryProvider from "@/providers/QueryProvider";
import ChatProvider from "@/providers/ChatProvider";
import PipelineProvider from "@/providers/PipelineProvider";
import "@/lib/pageCache";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-jetbrains",
});

export const metadata: Metadata = {
  title: "TradeIQ | AI Trading Analyst",
  description:
    "The Bloomberg Terminal for retail traders. AI-powered market analysis, behavioral coaching, and social content generation.",
  icons: {
    icon: "/tradeiq_favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${jetbrainsMono.variable}`}>
      <body className="antialiased">
        <QueryProvider>
          <ChatProvider>
            <PipelineProvider>
              {children}
            </PipelineProvider>
          </ChatProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
