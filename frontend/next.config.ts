import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // "standalone" for Docker/Railway/Render deployments
  // Vercel auto-detects and ignores this setting
  // Set NEXT_OUTPUT=standalone env var in Docker, or leave undefined for Vercel
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,

  // Enable gzip compression for smaller transfer sizes
  compress: true,

  // Remove X-Powered-By header (minor security + smaller response)
  poweredByHeader: false,

  // Allow backend API images if any
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.supabase.co",
      },
    ],
  },

  // Cache static assets aggressively on Render
  headers: async () => [
    {
      // Match any path ending with a static asset extension
      source: "/:path*.:ext(svg|jpg|png|webp|avif|ico|woff|woff2)",
      headers: [
        {
          key: "Cache-Control",
          value: "public, max-age=31536000, immutable",
        },
      ],
    },
    {
      source: "/_next/static/:path*",
      headers: [
        {
          key: "Cache-Control",
          value: "public, max-age=31536000, immutable",
        },
      ],
    },
  ],
};

export default nextConfig;
