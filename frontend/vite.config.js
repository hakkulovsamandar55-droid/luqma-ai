import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev rejimda API va rasm so'rovlari lokal backendga proxy qilinadi.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
      '/media': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
})
