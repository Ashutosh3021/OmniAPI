/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    // API base URL is set via NEXT_PUBLIC_API_URL environment variable
    // Development default: http://localhost:8000/api/v1
    // Production: Set in deployment platform (Vercel, etc.)
  },
  // Production optimizations
  compress: true,
  poweredByHeader: false,
};

export default nextConfig;
