import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

const backendTarget = process.env.ESIMU_DEV_BACKEND_URL ?? 'http://127.0.0.1:18001'

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      '/api': backendTarget,
      '/config': backendTarget,
      '/healthz': backendTarget,
      '/ws': {
        target: backendTarget,
        ws: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
  },
})
