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

## Deploy notes

- Reverse-proxy `/api/lookup/*` to this process (see `PROXY.md`).
- Rotate Lookup Discord tokens if ever exposed in chat/logs.
- Optional CAPTCHA: set `LOOKUP_CAPTCHA_ENABLED=true` plus site key + secret.
- Curated plugins: edit `plugins.json` and restart the API (or redeploy).

## DSA Lookup

Official public Statements of Reasons for Discord Netherlands B.V. (platform id **59**):

- Meta: `GET /api/lookup/dsa`
- By entity snowflake: `GET /api/lookup/dsa/{id}`