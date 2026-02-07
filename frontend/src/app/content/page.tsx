"use client";

import AppShell from "@/components/layout/AppShell";
import ContentWorkbench from "@/components/content/ContentWorkbench";
import DataCard from "@/components/ui/DataCard";
import DisclaimerBadge from "@/components/ui/DisclaimerBadge";
import StatusBadge from "@/components/ui/StatusBadge";
import DataSourceBadge from "@/components/ui/DataSourceBadge";
import { usePersonas, usePosts, useContentStats } from "@/hooks/useContentData";

export default function ContentPage() {
  const { data: personas, isUsingMock: personasIsMock } = usePersonas();
  const { data: posts, isUsingMock: postsIsMock, isBackendOnline } = usePosts();
  const { data: stats, isUsingMock: statsIsMock } = useContentStats();

  const isAnyMock = personasIsMock || postsIsMock || statsIsMock;

  return (
    <AppShell>
      <div className="p-6 md:p-10 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Content Engine</h1>
              <p className="text-sm text-muted mono-data mt-2">
                AI-powered social media content generation for Bluesky
              </p>
            </div>
            <DataSourceBadge isUsingMock={isAnyMock} isBackendOnline={isBackendOnline} />
          </div>
          <DisclaimerBadge variant="banner" text="All generated content includes compliance disclaimer." className="max-w-xs" />
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
          <DataCard title="Posts Generated" value={String(stats.postsGenerated)} subtitle="This week" trend="up" />
          <DataCard title="Published" value={String(stats.published)} subtitle={`${stats.published} posts`} trend="up" />
          <DataCard title="Engagement" value={String(stats.engagement)} subtitle="Likes + Reposts" trend="up" glow />
          <DataCard title="Compliance" value={`${stats.complianceRate}%`} subtitle="All posts verified" trend="neutral">
            <StatusBadge status="success" label="COMPLIANT" />
          </DataCard>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Content Workbench */}
          <div className="lg:col-span-3">
            <ContentWorkbench personas={personas} />
          </div>

          {/* Recent Posts */}
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-card border border-border rounded-md">
              <div className="px-5 py-4 border-b border-border flex items-center justify-between">
                <h3 className="text-xs font-semibold tracking-wider text-muted uppercase mono-data">RECENT POSTS</h3>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground mono-data">{posts.length} posts</span>
                  <DataSourceBadge isUsingMock={postsIsMock} />
                </div>
              </div>
              <div className="divide-y divide-border/30">
                {posts.map((post) => (
                  <div key={post.id} className="p-5 card-hover">
                    <div className="flex items-center justify-between mb-2.5">
                      <div className="flex items-center gap-2.5">
                        <span className="text-xs text-white font-medium mono-data">{post.persona}</span>
                        <PostStatusBadge status={post.status} />
                      </div>
                      <span className="text-xs text-muted-foreground mono-data">{post.time}</span>
                    </div>
                    <p className="text-sm text-muted leading-relaxed mono-data line-clamp-3">{post.content}</p>
                    <div className="flex items-center justify-between mt-3 pt-3 border-t border-border/30">
                      <span className="text-xs text-muted-foreground mono-data">{post.engagement}</span>
                      <div className="flex gap-3">
                        <button className="text-xs text-muted hover:text-white transition-colors mono-data">EDIT</button>
                        {post.status === "draft" && (
                          <button className="text-xs text-accent hover:text-white transition-colors mono-data">PUBLISH</button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
                {posts.length === 0 && (
                  <div className="p-10 text-center text-sm text-muted-foreground mono-data">
                    No posts yet. Generate content to see it here.
                  </div>
                )}
              </div>
            </div>

            {/* Persona Stats */}
            <div className="bg-card border border-border rounded-md p-5">
              <h3 className="text-xs font-semibold tracking-wider text-muted uppercase mono-data mb-4">
                PERSONA PERFORMANCE
              </h3>
              <div className="space-y-3">
                {personas.map((persona) => (
                  <div key={persona.id} className="flex items-center gap-3.5 p-3 rounded-md hover:bg-surface transition-colors">
                    <span className="text-xl">{persona.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-white font-medium mono-data">{persona.name}</span>
                        <span className="text-xs text-muted-foreground mono-data">{persona.postCount ?? 0} posts</span>
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-muted-foreground">{persona.style}</span>
                        <span className="text-xs text-profit mono-data">{persona.engagement ?? 0} engagements</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        <DisclaimerBadge variant="footer" />
      </div>
    </AppShell>
  );
}

function PostStatusBadge({ status }: { status: "published" | "draft" | "scheduled" }) {
  const config = {
    published: { status: "success" as const, label: "PUBLISHED" },
    draft: { status: "neutral" as const, label: "DRAFT" },
    scheduled: { status: "info" as const, label: "SCHEDULED" },
  };
  const { status: badgeStatus, label } = config[status];
  return <StatusBadge status={badgeStatus} label={label} />;
}
