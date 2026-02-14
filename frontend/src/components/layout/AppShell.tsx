"use client";

import Navbar from "./Navbar";
import TickerBar from "./TickerBar";
import Sidebar from "./Sidebar";
import MarketAlertToast from "@/components/alerts/MarketAlertToast";
import NarratorBar from "@/components/narrator/NarratorBar";
import { useMarketAlerts } from "@/hooks/useMarketAlerts";
import { useNarrator } from "@/hooks/useNarrator";

interface AppShellProps {
  children: React.ReactNode;
  showSidebar?: boolean;
  showTicker?: boolean;
}

export default function AppShell({
  children,
  showSidebar = true,
  showTicker = true,
}: AppShellProps) {
  const { latestAlert, clearAlerts } = useMarketAlerts();
  const { currentNarration, isActive } = useNarrator();

  return (
    <div className="h-screen bg-background flex flex-col overflow-hidden">
      <Navbar />
      {showTicker && <TickerBar />}

      <div className="flex flex-1 overflow-hidden">
        {/* Main Content */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>

        {/* Right Sidebar */}
        {showSidebar && <Sidebar />}
      </div>

      {/* Global overlays */}
      <MarketAlertToast alert={latestAlert} onDismiss={clearAlerts} />
      <NarratorBar narration={currentNarration} isActive={isActive} />
    </div>
  );
}
