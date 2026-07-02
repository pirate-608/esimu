/**
 * Vite development/build configuration for the game frontend.
 */
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { fileURLToPath, URL } from 'node:url'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 15173,
    proxy: {
      // Local development proxies backend traffic to the Compose-published API.
      '/api': {
        target: 'http://127.0.0.1:18000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://127.0.0.1:18000',
        ws: true,
      },
      '/world': {
        target: 'http://127.0.0.1:18000',
        changeOrigin: true,
      }
    }
  }
})
