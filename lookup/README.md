# Cheterin Lookup UI

Separate Vite + React + TypeScript SPA for Cheterin Lookup.

- **EN:** See [RUN.md](./RUN.md) for local commands.
- **RU:** Локальный запуск и сборка — в [RUN.md](./RUN.md). Прод: nginx `/lookup/*`, API — отдельный процесс `lookup-api` (systemd `cheterin-lookup`), не из `main.py`.

Production path prefix: `/lookup/*`. Built by root `update.sh` together with the dashboard.
