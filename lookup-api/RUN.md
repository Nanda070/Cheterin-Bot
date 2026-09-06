# Lookup API — local run

Isolated aiohttp service. **Not** started from `main.py`. Default bind: `127.0.0.1:8090`.

## Setup

```bash
cd lookup-api
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env   # or cp on Unix
# Edit .env — set LOOKUP_DISCORD_TOKEN (Lookup app bot token only)
```

## Run

```bash
python app.py
```

Health: `GET http://127.0.0.1:8090/api/lookup/health`

## Tests

```bash
pytest
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

Upstream CSV (no Research API key required):

`https://transparency.dsa.ec.europa.eu/statement/csv?platform_id[]=59&s=<snowflake>`

The Discord entity id is in CSV field `platform_uid`. Empty results are honest “no public SoR”, not a clearance status.
