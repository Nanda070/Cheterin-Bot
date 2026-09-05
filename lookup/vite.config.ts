import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  base: '/lookup/',
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
    proxy: {
      '/api/lookup': {
        target: 'http://127.0.0.1:8090',
        changeOrigin: true,
      },
    },
  },
  preview: {
    port: 4174,
  },
})
