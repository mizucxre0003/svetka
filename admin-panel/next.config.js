/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Admin Panel доступен по /admin
  basePath: '/admin',
  assetPrefix: '/admin',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || '',
    NEXT_PUBLIC_ADMIN_TOKEN: process.env.NEXT_PUBLIC_ADMIN_TOKEN || '',
  },
}

module.exports = nextConfig
