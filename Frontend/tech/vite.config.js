import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3002,
    hmr: {
      overlay: true,
    },
    watch: {
      usePolling: false,
      interval: 1000,
    },
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  build: {
    outDir: '../../backend/frontend_build',
    emptyOutDir: true,
  }
})
