import { defineConfig } from 'vite'

const backendTarget = process.env.ESIMU_DEV_BACKEND_URL ?? 'http://127.0.0.1:18001'

export default defineConfig({
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
})