/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_GATEWAY_URL: process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8000",
    NEXT_PUBLIC_SANDBOX_URL: process.env.NEXT_PUBLIC_SANDBOX_URL || "http://localhost:8001",
  },
};

module.exports = nextConfig;
