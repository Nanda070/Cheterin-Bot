# Lookup API - local run

Isolated aiohttp service. **Not** started from `main.py`. Default bind: `127.0.0.1:8090`.

## Setup

```bash
cd lookup-api
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then edit .env
```

## Token configuration

### Single token (simple)
```env
LOOKUP_DISCORD_TOKEN=<bot-token>
```

### Multi-token round-robin (production)
Set `LOOKUP_DISCORD_TOKENS` to a comma-separated list:
```env
LOOKUP_DISCORD_TOKENS=Token1,Token2,Token3,Token4,Token5
```
- Requests are distributed round-robin across all tokens.
- On HTTP 429 the pool rotates to the next token immediately and retries.
- After all tokens are exhausted it waits `min(Retry-After, 5 s)` then tries once more.
- `LOOKUP_DISCORD_TOKENS` takes priority over `LOOKUP_DISCORD_TOKEN`.
- Never use `BOT_TOKEN` here — the guardrail rejects it.

Health endpoint shows the count: `GET /api/lookup/health` → `{"token_count": N, ...}`

## Run

```bash
python app.py
```

Health: `GET http://127.0.0.1:8090/api/lookup/health`

## Tests

```bash
pytest                        # all tests
pytest tests/test_token_pool.py -v   # token pool unit tests only
```

## Deploy notes (Oracle / Ubuntu)

- Process: systemd **`cheterin-lookup.service`** (`python app.py` in `lookup-api/`). Not started from `main.py` / `cheterin-bot`.
- Unit file: `deploy/systemd/cheterin-lookup.service` (install once — see `deploy/systemd/README.md`).
- Reverse-proxy `/api/lookup/*` to `127.0.0.1:8090` (see `PROXY.md`). Static SPA is nginx `/lookup` → `lookup/dist`.
- Repo `update.sh` builds Lookup SPA + installs lookup-api deps and `systemctl restart`s **`cheterin-lookup`** (and the bot unit).
- `LOOKUP_DISCORD_TOKENS` (comma-list) is the production pool; never `BOT_TOKEN`.
- Rotate Lookup Discord tokens in the Developer Portal if they were ever exposed in chat/logs.
- Optional CAPTCHA: set `LOOKUP_CAPTCHA_ENABLED=true` plus `LOOKUP_CAPTCHA_SITE_KEY` + `LOOKUP_CAPTCHA_SECRET` (and optional `LOOKUP_CAPTCHA_PROVIDER`). Until then the widget stays off.
- Curated plugins: `plugins.json` is operator-filled; edit and restart the API (`systemctl restart cheterin-lookup.service`).

## DSA Lookup

Official public Statements of Reasons for Discord Netherlands B.V. (platform id **59**):

- Meta: `GET /api/lookup/dsa`
- By entity snowflake: `GET /api/lookup/dsa/{id}`