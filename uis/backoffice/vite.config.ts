import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
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
    },
  },
})
