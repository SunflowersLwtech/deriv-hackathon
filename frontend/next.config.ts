import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // "standalone" for Docker/Railway/Render deployments
  // Vercel auto-detects and ignores this setting
  // Set NEXT_OUTPUT=standalone env var in Docker, or leave undefined for Vercel
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,

  // Allow backend API images if any
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.supabase.co",
      },
    ],
  },
};

export default nextConfig;
