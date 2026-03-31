/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  // Mini App сидит на корне /
  env: {
    NEXT_PUBLIC_MINI_APP_API_URL: process.env.NEXT_PUBLIC_MINI_APP_API_URL || '',
  },
}

module.exports = nextConfig
