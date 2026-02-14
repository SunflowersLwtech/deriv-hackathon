"use client";

import { useState, useCallback } from "react";
import api, { type DemoStepResult, type DemoRunResult } from "@/lib/api";

interface DemoFlowState {
  isRunning: boolean;
  currentStep: number;
  results: DemoStepResult[];
  error: string | null;
  scriptName: string | null;
  openingLine: string;
  closingLine: string;
  totalDurationMs: number;
}

export function useDemoFlow() {
  const [state, setState] = useState<DemoFlowState>({
    isRunning: false,
    currentStep: 0,
    results: [],
    error: null,
    scriptName: null,
    openingLine: "",
    closingLine: "",
    totalDurationMs: 0,
  });

  const runScript = useCallback(async (scriptName: string) => {
    setState({
      isRunning: true,
      currentStep: 1,
      results: [],
      error: null,
      scriptName,
      openingLine: "",
      closingLine: "",
      totalDurationMs: 0,
    });

    try {
      // Prefer V2 endpoint for championship_run, fallback to V1
      let result: DemoRunResult & {
        opening_line?: string;
        closing_line?: string;
        opening_narration?: string;
        closing_narration?: string;
      };

      if (scriptName === "championship_run") {
        result = await api.runDemoScriptV2(scriptName);
      } else {
        result = await api.runDemoScript(scriptName);
      }

      setState((prev) => ({
        ...prev,
        isRunning: false,
        currentStep: result.steps.length,
        results: result.steps,
        openingLine:
          result.opening_narration || result.opening_line || "",
        closingLine:
          result.closing_narration || result.closing_line || "",
        totalDurationMs: result.total_duration_ms,
        error: result.status === "error" ? "Some steps failed" : null,
      }));
    } catch (err) {
      setState((prev) => ({
        ...prev,
        isRunning: false,
        error: err instanceof Error ? err.message : "Demo execution failed",
      }));
    }
  }, []);

  const reset = useCallback(() => {
    setState({
      isRunning: false,
      currentStep: 0,
      results: [],
      error: null,
      scriptName: null,
      openingLine: "",
      closingLine: "",
      totalDurationMs: 0,
    });
  }, []);

  return { ...state, runScript, reset };
}
