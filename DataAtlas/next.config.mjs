/** @type {import('next').NextConfig} */
const nextConfig = {
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  async rewrites() {
    return [
      {
        // Proxy backend API calls to FastAPI
        source: '/backend-api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
}

export default nextConfig
