"use client";

import { useCallback } from "react";
import { useApiWithFallback } from "./useApiWithFallback";
import api from "@/lib/api";

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

const PERSONA_ICON_MAP: Record<string, string> = {
  "Calm Analyst": "📊",
  "Data Nerd": "🧮",
  "Bold Commentator": "🔥",
  "The Calm Analyst": "📊",
  "The Data Nerd": "🧮",
  "The Trading Coach": "🎯",
};

export function usePersonas() {
  const fetchPersonas = useCallback(async () => {
    const personasResp = await api.getPersonas();
    const postsResp = await api.getPosts().catch(() => ({ results: [] }));

    const personas = Array.isArray(personasResp) ? personasResp : personasResp.results || [];
    const posts = Array.isArray(postsResp) ? postsResp : postsResp.results || [];

    return personas.map((persona) => {
      const personaPosts = posts.filter((post) => String(post.persona) === String(persona.id));
      return {
        id: persona.id,
        name: persona.name,
        style: persona.personality_type || "Professional",
        icon: PERSONA_ICON_MAP[persona.name] || "📊",
        postCount: personaPosts.length,
        engagement: personaPosts.reduce((acc, post) => {
          const likes = Number((post as { engagement_metrics?: Record<string, unknown> }).engagement_metrics?.likes || 0);
          const reposts = Number((post as { engagement_metrics?: Record<string, unknown> }).engagement_metrics?.reposts || 0);
          return acc + likes + reposts;
        }, 0),
      };
    });
  }, []);

  return useApiWithFallback<PersonaDisplay[]>({
    fetcher: fetchPersonas,
    fallbackData: [],
    pollInterval: 30000,
    cacheKey: "personas",
  });
}

export function usePosts() {
  const fetchPosts = useCallback(async () => {
    const response = await api.getPosts();
    const posts = Array.isArray(response) ? response : response.results || [];

    return posts.map((post): PostDisplay => {
      const created = new Date(post.created_at || Date.now());
      const now = new Date();
      const diffMs = now.getTime() - created.getTime();
      const diffMin = Math.max(0, Math.floor(diffMs / 60000));
      const timeStr = diffMin < 60 ? `${diffMin}m ago` : `${Math.floor(diffMin / 60)}h ago`;

      const engagementMetrics = (post as { engagement_metrics?: Record<string, unknown> }).engagement_metrics || {};
      const likes = Number(engagementMetrics.likes || 0);
      const reposts = Number(engagementMetrics.reposts || 0);

      return {
        id: post.id,
        persona: post.persona_name || post.persona,
        content: post.content,
        platform: post.platform,
        status: (post.status as PostDisplay["status"]) || "draft",
        time: post.published_at
          ? new Date(post.published_at).toLocaleString()
          : post.scheduled_at
            ? `Scheduled: ${new Date(post.scheduled_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`
            : timeStr,
        engagement: `${likes} likes, ${reposts} reposts`,
      };
    });
  }, []);

  return useApiWithFallback<PostDisplay[]>({
    fetcher: fetchPosts,
    fallbackData: [],
    pollInterval: 30000,
    cacheKey: "posts",
  });
}

export function useContentStats() {
  const fetchStats = useCallback(async () => {
    const response = await api.getPosts();
    const posts = Array.isArray(response) ? response : response.results || [];

    const published = posts.filter((p) => p.status === "published").length;
    const total = posts.length;
    const engagement = posts.reduce((acc, post) => {
      const metrics = (post as { engagement_metrics?: Record<string, unknown> }).engagement_metrics || {};
      return acc + Number(metrics.likes || 0) + Number(metrics.reposts || 0);
    }, 0);

    return {
      postsGenerated: total,
      published,
      engagement,
      complianceRate: 100,
    };
  }, []);

  return useApiWithFallback({
    fetcher: fetchStats,
    fallbackData: {
      postsGenerated: 0,
      published: 0,
      engagement: 0,
      complianceRate: 100,
    },
    pollInterval: 30000,
    cacheKey: "content-stats",
  });
}
