import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  // Keep VITE_* (API base URL) and expose NEXT_PUBLIC_TELEMETRY_ENDPOINT.
  envPrefix: ['VITE_', 'NEXT_PUBLIC_'],
  define: {
    __APP_RELEASE__: JSON.stringify(process.env.npm_package_version ?? '0.0.0'),
  },
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      '/incidents': {
        target: process.env.API_PROXY_TARGET,
        changeOrigin: true,
      },
      '/inventory': {
        target: process.env.API_PROXY_TARGET,
        changeOrigin: true,
      },
      '/health': {
        target: process.env.API_PROXY_TARGET,
        changeOrigin: true,
      },
      '/telemetry': {
        target: process.env.API_PROXY_TARGET,
        changeOrigin: true,
      },
    },
  },
})
