import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Pin tracing to web/ so Next.js doesn't pick a parent lockfile as workspace root.
  outputFileTracingRoot: path.join(__dirname),
  async rewrites() {
    const api = process.env.API_URL || "http://127.0.0.1:3000";
    return [
      { source: "/api/:path*", destination: `${api}/:path*` },
      // Fly combined image: health check hits Next :3000 → API on loopback
      { source: "/health", destination: `${api}/health` },
    ];
  },
};

export default nextConfig;
