# Cheterin Lookup API

Isolated aiohttp service for Cheterin Lookup. Prefix in production: `/api/lookup/*`.

## Local run

```bash
cd lookup-api
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Unix:
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # then set LOOKUP_DISCORD_TOKENS or LOOKUP_DISCORD_TOKEN
python app.py
```

Default listen: `http://127.0.0.1:8090`

Health: `GET /api/lookup/health` (also `/health`) — includes `token_count` from `TokenPool`.

## Isolation

- Tokens: **`LOOKUP_DISCORD_TOKENS`** (comma-list, round-robin + 429 rotate) or fallback **`LOOKUP_DISCORD_TOKEN`**. Never `BOT_TOKEN`.
- Does not import cogs, `dashboard.backend`, `member_lookup.py`, or ValChecker
- Not started from `main.py` / `start_dashboard` / tmux `chetmain`

## Reverse proxy (cheterin.online)

See [PROXY.md](./PROXY.md).
