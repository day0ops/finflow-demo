import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    const bffUrl = process.env.BFF_URL ?? "http://localhost:8001";
    return [
      { source: "/api/:path*", destination: `${bffUrl}/api/:path*` },
    ];
  },
};

export default nextConfig;
