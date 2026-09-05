# Lookup local run

```bash
# Terminal 1 — API
cd lookup-api
pip install -r requirements.txt
# set LOOKUP_DISCORD_TOKEN in lookup-api/.env
python app.py

# Terminal 2 — UI
cd lookup
npm install
npm run dev
```

Open `http://127.0.0.1:5174/lookup/`
