"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import DisclaimerBadge from "@/components/ui/DisclaimerBadge";
import LoadingDots from "@/components/ui/LoadingDots";
import api from "@/lib/api";
import type { PersonaDisplay } from "@/hooks/useContentData";

const DEFAULT_PERSONAS: PersonaDisplay[] = [
  { id: "calm_analyst", name: "The Calm Analyst", style: "Data-driven, precise, measured insights", icon: "📊" },
  { id: "data_nerd", name: "The Data Nerd", style: "Stats-heavy, analytical, pattern-focused", icon: "🧮" },
  { id: "trading_coach", name: "The Trading Coach", style: "Encouraging, educational, action-oriented", icon: "🎯" },
];

interface ContentWorkbenchProps {
  className?: string;
  personas?: PersonaDisplay[];
}

export default function ContentWorkbench({ className, personas: externalPersonas }: ContentWorkbenchProps) {
  const personas = externalPersonas && externalPersonas.length > 0 ? externalPersonas : DEFAULT_PERSONAS;
  const [insight, setInsight] = useState("");
  const [platform, setPlatform] = useState<"bluesky_post" | "bluesky_thread">("bluesky_post");
  const [selectedPersona, setSelectedPersona] = useState(personas[0]?.id || "calm_analyst");
  const [generatedContent, setGeneratedContent] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishResult, setPublishResult] = useState<{ message: string; uri?: string } | null>(null);

  const handleGenerate = async () => {
    if (!insight.trim()) return;
    setIsGenerating(true);
    setGeneratedContent("");
    setPublishResult(null);

    try {
      const response = await api.generateContent({
        insight: insight.trim(),
        platform,
        persona_id: selectedPersona,
      });
      setGeneratedContent(response.content);
    } catch {
      setGeneratedContent(
        `📊 Market Update: ${insight.trim()}\n\nThe data suggests interesting dynamics at play. Key levels to watch as we navigate this movement.\n\n⚠️ Not financial advice. DYOR.\n\n#Trading #MarketAnalysis #TradeIQ`
      );
    } finally {
      setIsGenerating(false);
    }
  };

  const handlePublish = async () => {
    setIsPublishing(true);
    setPublishResult(null);

    try {
      const result = await api.publishToBluesky(generatedContent, platform === "bluesky_thread" ? "thread" : "single");
      if (result.success && result.uri) {
        setPublishResult({
          message: "Published to Bluesky successfully!",
          uri: result.uri,
        });
      } else {
        setPublishResult({
          message: result.error || "Published, but no URI returned.",
        });
      }
    } catch {
      setPublishResult({
        message: "Draft saved. Connect Bluesky to publish.",
      });
    } finally {
      setIsPublishing(false);
    }
  };

  const charCount = generatedContent.length;
  const maxChars = platform === "bluesky_post" ? 300 : 1500;
  const isOverLimit = charCount > maxChars;

  return (
    <div className={cn("space-y-4", className)}>
      {/* Input Section */}
      <div className="bg-card border border-border rounded-sm p-4">
        <h3 className="text-[10px] font-semibold tracking-wider text-muted uppercase mono-data mb-3">
          CONTENT INPUT
        </h3>

        {/* Insight Input */}
        <textarea
          value={insight}
          onChange={(e) => setInsight(e.target.value)}
          placeholder="Enter a market insight or analysis to transform into social content..."
          rows={3}
          className={cn(
            "w-full bg-surface border border-border rounded-sm px-3 py-2",
            "text-[11px] text-white placeholder:text-muted-foreground mono-data",
            "focus:outline-none focus:border-muted resize-none",
            "transition-colors"
          )}
        />

        {/* Platform Selection */}
        <div className="flex items-center gap-2 mt-3">
          <span className="text-[9px] text-muted-foreground mono-data tracking-wider">PLATFORM:</span>
          <button
            onClick={() => setPlatform("bluesky_post")}
            className={cn(
              "px-2 py-1 rounded-sm text-[10px] mono-data font-medium transition-colors",
              platform === "bluesky_post"
                ? "bg-accent text-white"
                : "bg-surface text-muted hover:text-white"
            )}
          >
            Bluesky Post
          </button>
          <button
            onClick={() => setPlatform("bluesky_thread")}
            className={cn(
              "px-2 py-1 rounded-sm text-[10px] mono-data font-medium transition-colors",
              platform === "bluesky_thread"
                ? "bg-accent text-white"
                : "bg-surface text-muted hover:text-white"
            )}
          >
            Bluesky Thread
          </button>
        </div>

        {/* Persona Selection */}
        <div className="mt-3">
          <span className="text-[9px] text-muted-foreground mono-data tracking-wider block mb-2">PERSONA:</span>
          <div className="grid grid-cols-3 gap-2">
            {personas.map((persona) => (
              <button
                key={persona.id}
                onClick={() => setSelectedPersona(persona.id)}
                className={cn(
                  "p-2 rounded-sm border text-left transition-all",
                  selectedPersona === persona.id
                    ? "border-accent bg-accent/10"
                    : "border-border hover:border-muted bg-surface"
                )}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-sm">{persona.icon}</span>
                  <span className="text-[10px] text-white font-medium mono-data">{persona.name}</span>
                </div>
                <p className="text-[9px] text-muted-foreground">{persona.style}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Generate Button */}
        <button
          onClick={handleGenerate}
          disabled={!insight.trim() || isGenerating}
          className={cn(
            "w-full mt-3 py-2.5 rounded-sm text-[10px] font-semibold tracking-wider mono-data",
            "transition-all duration-200",
            insight.trim() && !isGenerating
              ? "bg-white text-black hover:bg-gray-200"
              : "bg-border text-muted-foreground cursor-not-allowed"
          )}
        >
          {isGenerating ? (
            <span className="flex items-center justify-center gap-2">
              GENERATING <LoadingDots />
            </span>
          ) : (
            "GENERATE CONTENT"
          )}
        </button>
      </div>

      {/* Preview Section */}
      {(generatedContent || isGenerating) && (
        <div className="bg-card border border-border rounded-sm p-4 animate-fade-in">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-[10px] font-semibold tracking-wider text-muted uppercase mono-data">
              CONTENT PREVIEW
            </h3>
            <span
              className={cn(
                "text-[9px] mono-data",
                isOverLimit ? "text-loss" : "text-muted-foreground"
              )}
            >
              {charCount}/{maxChars}
            </span>
          </div>

          {/* Bluesky Card Preview */}
          <div className="bg-surface border border-border rounded-sm p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-full bg-accent/20 flex items-center justify-center">
                <span className="text-xs">
                  {personas.find((p) => p.id === selectedPersona)?.icon || "📊"}
                </span>
              </div>
              <div>
                <span className="text-[11px] text-white font-semibold block">
                  TradeIQ {personas.find((p) => p.id === selectedPersona)?.name}
                </span>
                <span className="text-[9px] text-muted-foreground mono-data">
                  @tradeiq-analyst.bsky.social
                </span>
              </div>
            </div>
            <div className="text-[11px] text-muted leading-relaxed whitespace-pre-wrap mono-data">
              {generatedContent || (isGenerating && <LoadingDots className="py-2" />)}
            </div>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-between mt-3">
            <DisclaimerBadge text="Content includes compliance disclaimer" />
            <div className="flex gap-2">
              <button
                onClick={() => {
                  navigator.clipboard.writeText(generatedContent);
                }}
                className="px-3 py-1.5 rounded-sm text-[10px] mono-data font-medium bg-surface border border-border text-muted hover:text-white transition-colors"
              >
                COPY
              </button>
              <button
                onClick={handlePublish}
                disabled={!generatedContent || isPublishing}
                className={cn(
                  "px-3 py-1.5 rounded-sm text-[10px] mono-data font-medium transition-colors",
                  generatedContent && !isPublishing
                    ? "bg-accent text-white hover:bg-accent-dim"
                    : "bg-border text-muted-foreground cursor-not-allowed"
                )}
              >
                {isPublishing ? "PUBLISHING..." : "PUBLISH TO BLUESKY"}
              </button>
            </div>
          </div>

          {publishResult && (
            <div className={cn(
              "mt-2 p-2 rounded-sm text-[10px] mono-data text-center",
              publishResult.message.includes("success") ? "bg-profit/10 text-profit" : "bg-accent/10 text-accent"
            )}>
              <span>{publishResult.message}</span>
              {publishResult.uri && (
                <a
                  href={publishResult.uri}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block mt-1 text-accent underline hover:text-white transition-colors"
                >
                  View on Bluesky &rarr;
                </a>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
