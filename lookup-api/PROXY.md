# Reverse proxy mapping — cheterin.online

Lookup is a **separate** UI + API from the Cheterin bot dashboard process.

## Concept

| Path | Upstream |
|---|---|
| `/lookup`, `/lookup/*` | Lookup static SPA (`lookup/dist`, Vite `base: '/lookup/'`) |
| `/api/lookup/*` | Lookup API (`lookup-api`, default `127.0.0.1:8090`) |
| `/about`, `/docs`, `/terms`, `/privacy`, `/cookies`, `/disclaimer`, panel routes | Existing dashboard frontend/backend |

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

- UI: `npm run dev` in `lookup/` (proxies `/api/lookup` → `:8090`)
- API: `python app.py` in `lookup-api/`

Do **not** start Lookup from `main.py`.
