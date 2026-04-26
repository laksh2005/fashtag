/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://127.0.0.1:8000/:path*"
      },
      {
        source: "/assets/:path*",
        destination: "http://127.0.0.1:8000/assets/:path*"
      }
    ];
  }
};

module.exports = nextConfig;
