import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const lookupApiProxy = {
  '/api/lookup': {
    target: 'http://127.0.0.1:8090',
    changeOrigin: true,
  },
} as const

export default defineConfig({
  base: '/lookup/',
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
    proxy: { ...lookupApiProxy },
  },
  preview: {
    port: 4174,
    proxy: { ...lookupApiProxy },
  },
})
