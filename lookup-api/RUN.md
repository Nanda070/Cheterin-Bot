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
