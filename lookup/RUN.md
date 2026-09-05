# Cheterin Lookup (SPA)

Public Lookup UI for `https://cheterin.online/lookup`.

## Local run

```bash
cd lookup
npm install
npm run dev
```

Dev server: `http://127.0.0.1:5174/lookup/`  
API proxy: `/api/lookup` → `http://127.0.0.1:8090` (start `lookup-api` separately).

```bash
npm run build
npm run preview
```

## Notes

- Vite `base` is `/lookup/`.
- Language key: `chetbot_ui_lang` (RU default).
- Does **not** import dashboard frontend code.
- Brand header name: **Cheterin**.
