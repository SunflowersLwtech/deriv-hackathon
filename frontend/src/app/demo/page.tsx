"use client";

import { useEffect, useState } from "react";
import AppShell from "@/components/layout/AppShell";
import DataCard from "@/components/ui/DataCard";
import LoadingDots from "@/components/ui/LoadingDots";
import { useDemoFlow } from "@/hooks/useDemoFlow";
import api from "@/lib/api";

interface ScriptInfo {
  name: string;
  description: string;
  total_duration_sec: number;
  step_count: number;
}

export default function DemoPage() {
  const [scripts, setScripts] = useState<ScriptInfo[]>([]);
  const [scriptsLoading, setScriptsLoading] = useState(true);
  const demo = useDemoFlow();

  useEffect(() => {
    const loadScripts = async () => {
      try {
        const resp = await api.getDemoScripts();
        setScripts(resp.scripts || []);
      } catch {
        // fallback
        setScripts([
          { name: "full_showcase", description: "Complete 5-agent pipeline", total_duration_sec: 300, step_count: 5 },
          { name: "behavioral_focus", description: "Behavioral coaching flow", total_duration_sec: 180, step_count: 3 },
        ]);
      } finally {
        setScriptsLoading(false);
      }
    };
    loadScripts();
  }, []);

  return (
    <AppShell showSidebar={false}>
      <div className="p-6 space-y-6 max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-white tracking-wider">DEMO COMMAND CENTER</h1>
          <p className="text-muted text-sm">TradeIQ Hackathon Demo — Select a script and run</p>
        </div>

        {/* Opening Line */}
        {demo.openingLine && (
          <div className="p-4 bg-surface border border-border rounded-lg text-center">
            <p className="text-white text-sm italic">&ldquo;{demo.openingLine}&rdquo;</p>
          </div>
        )}

        {/* Script Selector */}
        {!demo.isRunning && demo.results.length === 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {scriptsLoading ? (
              <div className="col-span-2 flex justify-center py-10">
                <LoadingDots />
              </div>
            ) : (
              scripts.map((script) => (
                <button
                  key={script.name}
                  onClick={() => demo.runScript(script.name)}
                  className="text-left p-6 bg-card border border-border rounded-lg hover:border-white/30 transition-all group"
                >
                  <h3 className="text-white font-bold text-lg tracking-wide group-hover:text-profit transition-colors">
                    {script.name === "full_showcase" ? "Full Showcase" : "Behavioral Focus"}
                  </h3>
                  <p className="text-muted text-sm mt-2">{script.description}</p>
                  <div className="flex items-center gap-4 mt-4 text-xs text-muted">
                    <span>{script.step_count} steps</span>
                    <span>~{Math.ceil(script.total_duration_sec / 60)} min</span>
                  </div>
                  <div className="mt-4 px-4 py-2 bg-white text-black text-xs font-bold tracking-wider rounded text-center group-hover:bg-profit transition-colors">
                    RUN DEMO
                  </div>
                </button>
              ))
            )}
          </div>
        )}

        {/* Running State */}
        {demo.isRunning && (
          <DataCard title="Running Demo...">
            <div className="flex flex-col items-center py-8 space-y-4">
              <LoadingDots />
              <p className="text-muted text-sm">This may take 30-60 seconds</p>
            </div>
          </DataCard>
        )}

        {/* Error */}
        {demo.error && (
          <div className="p-4 bg-loss/10 border border-loss/30 rounded-md text-loss text-sm">
            {demo.error}
          </div>
        )}

        {/* Step Progress */}
        {demo.results.length > 0 && (
          <>
            {/* Step Stepper */}
            <div className="flex items-center justify-center gap-2">
              {demo.results.map((step, i) => (
                <div key={i} className="flex items-center">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                      step.status === "success"
                        ? "bg-profit text-black"
                        : "bg-loss text-white"
                    }`}
                  >
                    {step.step_number}
                  </div>
                  {i < demo.results.length - 1 && (
                    <div className="w-8 h-0.5 bg-border mx-1" />
                  )}
                </div>
              ))}
            </div>

            {/* Result Cards */}
            <div className="space-y-4">
              {demo.results.map((step) => (
                <DataCard
                  key={step.step_number}
                  title={`Step ${step.step_number}: ${step.title}`}
                >
                  <div className="space-y-3">
                    {/* Narration */}
                    {step.narration && (
                      <p className="text-muted text-sm italic">
                        {step.narration}
                      </p>
                    )}

                    {/* Status + Duration */}
                    <div className="flex items-center justify-between text-xs">
                      <span
                        className={`px-2 py-1 rounded font-bold tracking-wider ${
                          step.status === "success"
                            ? "bg-profit/20 text-profit"
                            : "bg-loss/20 text-loss"
                        }`}
                      >
                        {step.status.toUpperCase()}
                      </span>
                      <span className="text-muted mono-data">{step.duration_ms}ms</span>
                    </div>

                    {/* Wow Factor */}
                    {step.wow_factor && (
                      <div className="text-xs text-yellow-400 bg-yellow-400/10 px-3 py-1.5 rounded border border-yellow-400/20">
                        {step.wow_factor}
                      </div>
                    )}

                    {/* Result Preview */}
                    <details className="group">
                      <summary className="text-xs text-muted cursor-pointer hover:text-white transition-colors">
                        View raw result
                      </summary>
                      <pre className="mt-2 text-xs text-muted bg-surface p-3 rounded overflow-x-auto max-h-48 overflow-y-auto">
                        {JSON.stringify(step.result, null, 2)}
                      </pre>
                    </details>
                  </div>
                </DataCard>
              ))}
            </div>

            {/* Total Duration */}
            <div className="text-center text-sm text-muted mono-data">
              Total: {(demo.totalDurationMs / 1000).toFixed(1)}s
            </div>
          </>
        )}

        {/* Closing Line */}
        {demo.closingLine && !demo.isRunning && demo.results.length > 0 && (
          <div className="p-4 bg-surface border border-profit/30 rounded-lg text-center">
            <p className="text-profit text-sm italic">&ldquo;{demo.closingLine}&rdquo;</p>
          </div>
        )}

        {/* Reset Button */}
        {demo.results.length > 0 && !demo.isRunning && (
          <div className="flex justify-center">
            <button
              onClick={demo.reset}
              className="px-6 py-2 text-xs font-bold tracking-wider bg-surface hover:bg-surface-hover text-white border border-border rounded-md transition-colors"
            >
              RUN ANOTHER DEMO
            </button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
