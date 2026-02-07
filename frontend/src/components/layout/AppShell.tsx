"use client";

import Navbar from "./Navbar";
import TickerBar from "./TickerBar";
import Sidebar from "./Sidebar";

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
  return (
    <div className="min-h-screen bg-background flex flex-col">
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
    </div>
  );
}
