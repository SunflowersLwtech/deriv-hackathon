"use client";

import { useEffect, useState, useMemo } from "react";
import AppShell from "@/components/layout/AppShell";
import DataCard from "@/components/ui/DataCard";
import LoadingDots from "@/components/ui/LoadingDots";
import { useDemoFlow } from "@/hooks/useDemoFlow";
import api from "@/lib/api";
import type { DemoStepResult } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ScriptInfo {
  name: string;
  description: string;
  total_duration_sec: number;
  step_count: number;
}

/* ─── ACT metadata ─────────────────────────────────────────────── */

const ACT_META: Record<string, { label: string; color: string; icon: string; time: string }> = {
  "ACT 1: THE HOOK":             { label: "THE HOOK",             color: "text-cyan",    icon: "01", time: "0:00–0:30" },
  "ACT 2: THE WOW":              { label: "THE WOW",              color: "text-yellow-400", icon: "02", time: "0:30–1:00" },
  "ACT 3: THE COMPLETE PICTURE": { label: "THE COMPLETE PICTURE", color: "text-profit",  icon: "03", time: "1:00–1:40" },
  "ACT 4: THE CLOSE":            { label: "THE CLOSE",            color: "text-white",   icon: "04", time: "1:40–2:00" },
};

const ACT_ORDER = [
  "ACT 1: THE HOOK",
  "ACT 2: THE WOW",
  "ACT 3: THE COMPLETE PICTURE",
  "ACT 4: THE CLOSE",
];

function groupByAct(steps: DemoStepResult[]) {
  const groups: { act: string; steps: DemoStepResult[] }[] = [];
  let current: { act: string; steps: DemoStepResult[] } | null = null;

  for (const step of steps) {
    const act = step.act || "Unknown";
    if (!current || current.act !== act) {
      current = { act, steps: [] };
      groups.push(current);
    }
    current.steps.push(step);
  }
  return groups;
}

/* ─── Progress Timeline ────────────────────────────────────────── */

function ActTimeline({ results }: { results: DemoStepResult[] }) {
  const groups = useMemo(() => groupByAct(results), [results]);

  return (
    <div className="flex items-stretch gap-0 w-full">
      {groups.map((group, gi) => {
        const meta = ACT_META[group.act];
        const allSuccess = group.steps.every((s) => s.status === "success");
        const hasError = group.steps.some((s) => s.status === "error");

        return (
          <div key={group.act} className="flex-1 flex flex-col items-center">
            {/* Act label */}
            <span className={cn("text-[10px] font-bold tracking-widest mono-data mb-2", meta?.color || "text-muted")}>
              {meta?.label || group.act}
            </span>

            {/* Step dots */}
            <div className="flex items-center gap-1.5 mb-1.5">
              {group.steps.map((step) => (
                <div
                  key={step.step_number}
                  className={cn(
                    "w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold mono-data transition-all",
                    step.status === "success"
                      ? "bg-profit text-black"
                      : "bg-loss/80 text-white"
                  )}
                >
                  {step.step_number}
                </div>
              ))}
            </div>

            {/* Act progress bar */}
            <div className="w-full h-1 rounded-full bg-border/50 overflow-hidden">
              <div
                className={cn(
                  "h-full rounded-full transition-all duration-700",
                  allSuccess ? "bg-profit" : hasError ? "bg-loss" : "bg-border"
                )}
                style={{ width: "100%" }}
              />
            </div>

            {/* Time range */}
            <span className="text-[9px] text-muted-foreground mono-data mt-1">
              {meta?.time || ""}
            </span>

            {/* Connector between acts */}
            {gi < groups.length - 1 && (
              <div className="hidden" />
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ─── Main Page ────────────────────────────────────────────────── */

export default function DemoPage() {
  const [scripts, setScripts] = useState<ScriptInfo[]>([]);
  const [scriptsLoading, setScriptsLoading] = useState(true);
  const demo = useDemoFlow();

  const hasActData = demo.results.some((s) => !!s.act);
  const actGroups = useMemo(
    () => (hasActData ? groupByAct(demo.results) : []),
    [demo.results, hasActData]
  );

  useEffect(() => {
    const loadScripts = async () => {
      try {
        const resp = await api.getDemoScripts();
        setScripts(resp.scripts || []);
      } catch {
        setScripts([
          { name: "championship_run", description: "Championship Demo — 2 min, 7 steps, 4 acts", total_duration_sec: 120, step_count: 7 },
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
        {/* Championship Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-profit/10 border border-profit/20 rounded-full text-[10px] text-profit font-bold tracking-widest mono-data">
            DERIV AI HACKATHON 2026
          </div>
          <h1 className="text-3xl font-bold text-white tracking-wider">
            TRADEIQ DEMO
          </h1>
          <p className="text-muted text-sm max-w-lg mx-auto">
            2-minute championship run — Detect, Analyze, Coach, Publish
          </p>
        </div>

        {/* Opening Narration */}
        {demo.openingLine && (
          <div className="p-5 bg-surface border border-border rounded-lg text-center animate-fade-in">
            <p className="text-white text-sm italic leading-relaxed">
              &ldquo;{demo.openingLine}&rdquo;
            </p>
          </div>
        )}

        {/* Script Selector */}
        {!demo.isRunning && demo.results.length === 0 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {scriptsLoading ? (
              <div className="col-span-3 flex justify-center py-10">
                <LoadingDots />
              </div>
            ) : (
              scripts.map((script) => {
                const isChampionship = script.name === "championship_run";
                return (
                  <button
                    key={script.name}
                    onClick={() => demo.runScript(script.name)}
                    className={cn(
                      "text-left p-6 border rounded-lg transition-all group",
                      isChampionship
                        ? "bg-profit/5 border-profit/30 hover:border-profit/60 md:col-span-3"
                        : "bg-card border-border hover:border-white/30"
                    )}
                  >
                    {isChampionship && (
                      <span className="inline-block text-[9px] font-bold tracking-widest text-profit mono-data mb-2 px-2 py-0.5 bg-profit/10 rounded">
                        RECOMMENDED
                      </span>
                    )}
                    <h3 className={cn(
                      "font-bold text-lg tracking-wide transition-colors",
                      isChampionship
                        ? "text-profit group-hover:text-white"
                        : "text-white group-hover:text-profit"
                    )}>
                      {script.name === "championship_run"
                        ? "Championship Run"
                        : script.name === "full_showcase"
                          ? "Full Showcase"
                          : script.name === "behavioral_focus"
                            ? "Behavioral Focus"
                            : script.name}
                    </h3>
                    <p className="text-muted text-sm mt-2">{script.description}</p>
                    <div className="flex items-center gap-4 mt-4 text-xs text-muted">
                      <span>{script.step_count} steps</span>
                      <span>~{Math.ceil(script.total_duration_sec / 60)} min</span>
                    </div>
                    <div className={cn(
                      "mt-4 px-4 py-2 text-xs font-bold tracking-wider rounded text-center transition-colors",
                      isChampionship
                        ? "bg-profit text-black group-hover:bg-white"
                        : "bg-white text-black group-hover:bg-profit"
                    )}>
                      {isChampionship ? "START CHAMPIONSHIP DEMO" : "RUN DEMO"}
                    </div>
                  </button>
                );
              })
            )}
          </div>
        )}

        {/* Running State */}
        {demo.isRunning && (
          <DataCard title="Running Demo...">
            <div className="flex flex-col items-center py-8 space-y-4">
              <LoadingDots />
              <p className="text-muted text-sm">Executing championship script...</p>
            </div>
          </DataCard>
        )}

        {/* Error */}
        {demo.error && (
          <div className="p-4 bg-loss/10 border border-loss/30 rounded-md text-loss text-sm">
            {demo.error}
          </div>
        )}

        {/* Results */}
        {demo.results.length > 0 && (
          <>
            {/* ACT Progress Timeline */}
            {hasActData && (
              <div className="p-4 bg-surface border border-border rounded-lg">
                <ActTimeline results={demo.results} />
              </div>
            )}

            {/* Flat stepper fallback for V1 scripts */}
            {!hasActData && (
              <div className="flex items-center justify-center gap-2">
                {demo.results.map((step, i) => (
                  <div key={i} className="flex items-center">
                    <div
                      className={cn(
                        "w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold",
                        step.status === "success"
                          ? "bg-profit text-black"
                          : "bg-loss text-white"
                      )}
                    >
                      {step.step_number}
                    </div>
                    {i < demo.results.length - 1 && (
                      <div className="w-8 h-0.5 bg-border mx-1" />
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* ACT-grouped Result Cards */}
            {hasActData ? (
              <div className="space-y-8">
                {actGroups.map((group) => {
                  const meta = ACT_META[group.act];
                  return (
                    <div key={group.act}>
                      {/* ACT Divider */}
                      <div className="flex items-center gap-3 mb-4">
                        <div className={cn(
                          "w-8 h-8 rounded-md flex items-center justify-center text-[10px] font-bold mono-data border",
                          meta?.color || "text-muted",
                          "border-current/20 bg-current/5"
                        )}
                        style={{
                          borderColor: "currentColor",
                          backgroundColor: "transparent",
                        }}
                        >
                          <span className={meta?.color}>{meta?.icon || "?"}</span>
                        </div>
                        <div>
                          <h2 className={cn("text-sm font-bold tracking-widest mono-data", meta?.color || "text-muted")}>
                            {meta?.label || group.act}
                          </h2>
                          <span className="text-[10px] text-muted-foreground mono-data">
                            {meta?.time || ""}
                          </span>
                        </div>
                        <div className="flex-1 h-px bg-border/50" />
                      </div>

                      {/* Step Cards within ACT */}
                      <div className="space-y-3 pl-4 border-l-2 border-border/30 ml-4">
                        {group.steps.map((step) => (
                          <DataCard
                            key={step.step_number}
                            title={`${step.step_number}. ${step.title}`}
                          >
                            <div className="space-y-3">
                              {step.narration && (
                                <p className="text-muted text-sm italic leading-relaxed">
                                  {step.narration}
                                </p>
                              )}

                              <div className="flex items-center justify-between text-xs">
                                <span
                                  className={cn(
                                    "px-2 py-1 rounded font-bold tracking-wider",
                                    step.status === "success"
                                      ? "bg-profit/20 text-profit"
                                      : "bg-loss/20 text-loss"
                                  )}
                                >
                                  {step.status.toUpperCase()}
                                </span>
                                <span className="text-muted mono-data">{step.duration_ms}ms</span>
                              </div>

                              {step.wow_factor && (
                                <div className="text-xs text-yellow-400 bg-yellow-400/10 px-3 py-1.5 rounded border border-yellow-400/20">
                                  {step.wow_factor}
                                </div>
                              )}

                              {step.fallback_used && (
                                <div className="text-[10px] text-orange-400 bg-orange-400/10 px-2 py-1 rounded">
                                  Fallback: {step.fallback_used}
                                </div>
                              )}

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
                    </div>
                  );
                })}
              </div>
            ) : (
              /* Flat result cards for V1 scripts */
              <div className="space-y-4">
                {demo.results.map((step) => (
                  <DataCard
                    key={step.step_number}
                    title={`Step ${step.step_number}: ${step.title}`}
                  >
                    <div className="space-y-3">
                      {step.narration && (
                        <p className="text-muted text-sm italic">
                          {step.narration}
                        </p>
                      )}
                      <div className="flex items-center justify-between text-xs">
                        <span
                          className={cn(
                            "px-2 py-1 rounded font-bold tracking-wider",
                            step.status === "success"
                              ? "bg-profit/20 text-profit"
                              : "bg-loss/20 text-loss"
                          )}
                        >
                          {step.status.toUpperCase()}
                        </span>
                        <span className="text-muted mono-data">{step.duration_ms}ms</span>
                      </div>
                      {step.wow_factor && (
                        <div className="text-xs text-yellow-400 bg-yellow-400/10 px-3 py-1.5 rounded border border-yellow-400/20">
                          {step.wow_factor}
                        </div>
                      )}
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
            )}

            {/* Total Duration */}
            <div className="text-center text-sm text-muted mono-data">
              Total: {(demo.totalDurationMs / 1000).toFixed(1)}s
            </div>
          </>
        )}

        {/* Closing Narration */}
        {demo.closingLine && !demo.isRunning && demo.results.length > 0 && (
          <div className="p-5 bg-surface border border-profit/30 rounded-lg text-center animate-fade-in">
            <p className="text-profit text-sm italic leading-relaxed">
              &ldquo;{demo.closingLine}&rdquo;
            </p>
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
