import type { NextConfig } from "next";

// Static export: deploys to Vercel, Netlify or GitHub Pages with no server.
const nextConfig: NextConfig = {
  output: "export",
};

export default nextConfig;
