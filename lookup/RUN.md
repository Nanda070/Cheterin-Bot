# Cheterin Lookup (SPA)

Vite + React UI for Cheterin Lookup. Production base path: `/lookup/`.

## Local

```bash
cd lookup
npm install
npm run dev
```

Open `http://127.0.0.1:5174/lookup/` (dev server proxies `/api/lookup` → `127.0.0.1:8090`).

## Build

```bash
npm run build
# output: lookup/dist  (served under /lookup/ by nginx or dashboard preview)
```

## Combined preview with dashboard (port 4173)

```bash
npm --prefix lookup run build
npm --prefix dashboard/frontend run build
npm --prefix dashboard/frontend run preview -- --host 127.0.0.1 --port 4173
```

Requires Lookup API on `:8090` for live Discord lookups:

```bash
cd lookup-api
python app.py
```

See `lookup-api/RUN.md` and `lookup-api/PROXY.md`.
