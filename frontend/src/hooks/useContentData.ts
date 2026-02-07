"use client";

import { useCallback } from "react";
import { useApiWithFallback } from "./useApiWithFallback";
import api from "@/lib/api";

// ── Types ──
export interface PersonaDisplay {
  id: string;
  name: string;
  style: string;
  icon: string;
  postCount?: number;
  engagement?: number;
}

export interface PostDisplay {
  id: string;
  persona: string;
  content: string;
  platform: string;
  status: "published" | "draft" | "scheduled";
  time: string;
  engagement: string;
}

// ── Mock data ──
const MOCK_PERSONAS: PersonaDisplay[] = [
  { id: "calm_analyst", name: "The Calm Analyst", style: "Data-driven, precise, measured insights", icon: "\ud83d\udcca", postCount: 18, engagement: 156 },
  { id: "data_nerd", name: "The Data Nerd", style: "Stats-heavy, analytical, pattern-focused", icon: "\ud83e\uddee", postCount: 15, engagement: 124 },
  { id: "trading_coach", name: "The Trading Coach", style: "Encouraging, educational, action-oriented", icon: "\ud83c\udfaf", postCount: 14, engagement: 62 },
];

const MOCK_POSTS: PostDisplay[] = [
  {
    id: "1", persona: "The Calm Analyst",
    content: "\ud83d\udcca EUR/USD Technical Update: Price testing 1.0840 support after rejecting 1.0890 resistance. RSI at 42 suggests room for further downside. Key level: 1.0820. \u26a0\ufe0f Not financial advice.",
    platform: "bluesky_post", status: "published", time: "2h ago", engagement: "12 likes, 3 reposts",
  },
  {
    id: "2", persona: "The Data Nerd",
    content: "\ud83e\udde0 Trading Tip: Ever notice you trade more after a loss? That's called 'revenge trading' \u2014 and it's one of the most common behavioral biases. The fix? Set a daily loss limit BEFORE you start trading.",
    platform: "bluesky_post", status: "draft", time: "30m ago", engagement: "\u2014",
  },
  {
    id: "3", persona: "The Trading Coach",
    content: "\ud83d\udd25 Hot take: Most retail traders lose not because of bad analysis, but bad behavior. Build systems, not opinions. \u26a0\ufe0f Educational only.",
    platform: "bluesky_post", status: "scheduled", time: "Scheduled: 16:00", engagement: "\u2014",
  },
];

const PERSONA_ICON_MAP: Record<string, string> = {
  "Calm Analyst": "\ud83d\udcca",
  "Data Nerd": "\ud83e\uddee",
  "Bold Commentator": "\ud83d\udd25",
  "The Calm Analyst": "\ud83d\udcca",
  "The Data Nerd": "\ud83e\uddee",
  "The Trading Coach": "\ud83c\udfaf",
  "The Analyst": "\ud83d\udcca",
  "The Educator": "\ud83d\udcda",
  "The Maverick": "\ud83d\udd25",
};

// ── Hooks ──
export function usePersonas() {
  const fetchPersonas = useCallback(async () => {
    const response = await api.getPersonas();
    const personas = Array.isArray(response) ? response : response.results || [];
    if (!personas || personas.length === 0) throw new Error("No personas");

    return personas.map((p): PersonaDisplay => ({
      id: p.id,
      name: p.name,
      style: p.personality_type || "Professional",
      icon: PERSONA_ICON_MAP[p.name] || "\ud83d\udcca",
    }));
  }, []);

  return useApiWithFallback<PersonaDisplay[]>({
    fetcher: fetchPersonas,
    fallbackData: MOCK_PERSONAS,
  });
}

export function usePosts() {
  const fetchPosts = useCallback(async () => {
    const response = await api.getPosts();
    const posts = Array.isArray(response) ? response : response.results || [];
    if (!posts || posts.length === 0) throw new Error("No posts");

    return posts.map((p): PostDisplay => {
      const created = new Date(p.created_at);
      const now = new Date();
      const diffMs = now.getTime() - created.getTime();
      const diffMin = Math.floor(diffMs / 60000);
      const timeStr = diffMin < 60 ? `${diffMin}m ago` : `${Math.floor(diffMin / 60)}h ago`;

      return {
        id: p.id,
        persona: p.persona,
        content: p.content,
        platform: p.platform,
        status: p.status as PostDisplay["status"],
        time: p.published_at ? new Date(p.published_at).toLocaleString() : timeStr,
        engagement: "\u2014",
      };
    });
  }, []);

  return useApiWithFallback<PostDisplay[]>({
    fetcher: fetchPosts,
    fallbackData: MOCK_POSTS,
    pollInterval: 30000,
  });
}

export function useContentStats() {
  const fetchStats = useCallback(async () => {
    const response = await api.getPosts();
    const posts = Array.isArray(response) ? response : response.results || [];
    if (!posts) throw new Error("No posts");

    const published = posts.filter((p) => p.status === "published").length;
    const total = posts.length;

    return {
      postsGenerated: total,
      published,
      engagement: published * 15,
      complianceRate: 100,
    };
  }, []);

  return useApiWithFallback({
    fetcher: fetchStats,
    fallbackData: {
      postsGenerated: 47,
      published: 23,
      engagement: 342,
      complianceRate: 100,
    },
  });
}
