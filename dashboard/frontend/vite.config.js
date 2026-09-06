/// <reference types="vitest/config" />
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const lookupDistDir = path.resolve(__dirname, '../../lookup/dist')

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.map': 'application/json',
}

function contentTypeFor(filePath) {
  return MIME[path.extname(filePath).toLowerCase()] ?? 'application/octet-stream'
}

function sendFile(res, filePath) {
  res.statusCode = 200
  res.setHeader('Content-Type', contentTypeFor(filePath))
  fs.createReadStream(filePath).pipe(res)
}

function sendLookupMissing(res) {
  res.statusCode = 503
  res.setHeader('Content-Type', 'text/plain; charset=utf-8')
  res.end(
    'Lookup SPA is not built. From repo root run: npm --prefix lookup run build\n' +
      'Then restart dashboard Vite (dev or preview). See lookup-api/PROXY.md.',
  )
}

function serveLookupStatic() {
  const mount = (middlewares) => {
    middlewares.use((req, res, next) => {
      const rawUrl = req.url ?? ''
      if (!rawUrl.startsWith('/lookup')) {
        next()
        return
      }

      if (!fs.existsSync(lookupDistDir)) {
        sendLookupMissing(res)
        return
      }

      const urlPath = rawUrl.split('?')[0] ?? '/lookup/'
      let rel = urlPath.slice('/lookup'.length)
      if (!rel || rel === '/') {
        rel = '/index.html'
      }

      const candidate = path.normalize(path.join(lookupDistDir, rel))
      if (!candidate.startsWith(lookupDistDir)) {
        res.statusCode = 403
        res.end('Forbidden')
        return
      }

      if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
        sendFile(res, candidate)
        return
      }

      const spaIndex = path.join(lookupDistDir, 'index.html')
      if (fs.existsSync(spaIndex)) {
        sendFile(res, spaIndex)
        return
      }

      sendLookupMissing(res)
    })
  }

  return {
    name: 'serve-lookup-static',
    configureServer(server) {
      mount(server.middlewares)
    },
    configurePreviewServer(server) {
      mount(server.middlewares)
    },
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), serveLookupStatic()],
  server: {
    proxy: {
      '/api/lookup': {
        target: 'http://127.0.0.1:8090',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  preview: {
    proxy: {
      '/api/lookup': {
        target: 'http://127.0.0.1:8090',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/setupTests.ts',
  },
})
