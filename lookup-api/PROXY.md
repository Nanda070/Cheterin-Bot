# Reverse proxy mapping — cheterin.online

Lookup is a **separate** UI + API from the Cheterin bot dashboard process.

Production (Ubuntu / Oracle): nginx on the same host. Bot+dashboard = tmux `chetmain` (`python main.py`). Lookup API = tmux `chetlookup` (`lookup-api`, `:8090`). Tokens: `LOOKUP_DISCORD_TOKENS` (TokenPool) in `lookup-api/.env` — never `BOT_TOKEN`.

## Concept

| Path | Upstream |
|---|---|
| `/lookup`, `/lookup/*` | Lookup static SPA (`lookup/dist`, Vite `base: '/lookup/'`) |
| `/api/lookup/*` | Lookup API (`lookup-api`, default `127.0.0.1:8090`) |
| `/about`, `/docs`, `/dev-blog`, `/terms`, `/privacy`, `/cookies`, `/disclaimer`, panel routes | Existing dashboard frontend/backend |

## Local single-port preview (dashboard `:4173`)

Dashboard Vite **dev** and **preview** mount `lookup/dist` under `/lookup/` and proxy `/api/lookup` → `:8090`.

```bash
# 1) Build Lookup SPA (required once / after Lookup UI changes)
npm --prefix lookup run build

# 2) Build + preview dashboard (serves About/docs AND /lookup on the same port)
npm --prefix dashboard/frontend run build
npm --prefix dashboard/frontend run preview -- --host 127.0.0.1 --port 4173
```

Then open:

- http://127.0.0.1:4173/about
- http://127.0.0.1:4173/docs
- http://127.0.0.1:4173/lookup/
- http://127.0.0.1:4173/lookup/about (SPA fallback via Lookup `index.html`)

If `/lookup` returns **503**, Lookup dist is missing — run step 1 and restart preview.

Optional API for live lookups:

```bash
# from lookup-api/
python app.py   # listens on 8090
```

## Example (nginx)

```nginx
# Lookup UI
location /lookup/ {
  alias /var/www/cheterin/lookup/;
  try_files $uri $uri/ /lookup/index.html;
}

# Lookup API (same host — no CORS subdomain)
location /api/lookup/ {
  proxy_pass http://127.0.0.1:8090;
  proxy_set_header Host $host;
  proxy_set_header X-Real-IP $remote_addr;
  proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
  proxy_set_header X-Forwarded-Proto $scheme;
}
```

## Standalone (dev / smoke)

- UI: `npm run dev` in `lookup/` (proxies `/api/lookup` → `:8090`, port **5174**)
- API: `python app.py` in `lookup-api/`

Do **not** start Lookup from `main.py`.
