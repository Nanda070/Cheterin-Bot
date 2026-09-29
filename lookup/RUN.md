# Cheterin Lookup (SPA)

Vite + React UI for Cheterin Lookup. Production base path: `/lookup/`.

Does **not** use `BOT_TOKEN` or `LOOKUP_DISCORD_TOKEN(S)` — those belong to `lookup-api/` (`TokenPool`). This SPA only calls `/api/lookup/*`.

## Local

```bash
cd lookup
npm install
npm run dev
```

Open `http://127.0.0.1:5174/lookup/` (dev server proxies `/api/lookup` → `127.0.0.1:8090`).

Home modes: `user` / `bot` / `server` / `dsa` (`?mode=`). Tools live under `/lookup/plugins/{snowflake,timestamp,permissions,badges,avatars}`.

## Build

```bash
npm run build
# output: lookup/dist  (nginx alias /lookup/ on Oracle; also dashboard Vite preview)
```

Repo `update.sh` builds **both** the dashboard frontend and this Lookup SPA, then restarts systemd `cheterin-bot` + `cheterin-lookup`. For a Lookup-only local rebuild: `npm run build` here (nginx serves `lookup/dist`; API restart only needed for `lookup-api` code).

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
