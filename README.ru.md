<p align="center">
  <img src="dashboard/frontend/public/favicon.svg" alt="Cheterin" width="72" height="72" />
</p>

<h1 align="center">Cheterin</h1>

<p align="center">
  <strong>Публичный мультисерверный Discord-бот с веб-панелью</strong> для живых сообществ.<br />
  Модерация, уровни, экономика, события, игры и инструменты VALORANT — без лишней возни в чате.
</p>

<p align="center">
  <a href="README.md">English</a> ·
  <a href="LICENSE">Apache-2.0</a>
</p>

<p align="center">
  <a href="https://cheterin.online"><img src="https://img.shields.io/badge/Панель-cheterin.online-a8283c?style=for-the-badge" alt="Panel" /></a>
  <a href="https://discord.gg/cheterin"><img src="https://img.shields.io/badge/Cheterin_Group-Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord" /></a>
  <a href="https://github.com/Nanda070/Cheterin_Bot_Dashboard"><img src="https://img.shields.io/badge/GitHub-Cheterin-181717?style=for-the-badge&logo=github" alt="GitHub" /></a>
</p>

<p align="center">
  <a href="https://cheterin.online">Панель</a> ·
  <a href="https://cheterin.online/docs">Документация</a> ·
  <a href="https://cheterin.online/about">О боте</a> ·
  <a href="https://cheterin.online/lookup">Lookup</a> ·
  <a href="https://cheterin.online/dev-blog">Dev Blog</a> ·
  <a href="https://cheterin.online/terms">Условия</a> ·
  <a href="https://cheterin.online/credits">Авторы</a> ·
  <a href="https://discord.gg/cheterin">Cheterin Group</a>
</p>

---

## Зачем Cheterin

Один бот вместо десятка разрозненных утилит. Cheterin работает на нескольких Discord-серверах, а настройки и данные каждого сервера **изолированы**. Админы настраивают модули в браузере — участники пользуются slash-командами и interactions в Discord.

| | |
|:---|:---|
| **Модерация** | Логи, антиспам, автомод, верификация, антирейд, варны |
| **Сообщество** | Уровни и XP, приветствия, инвайты, sticky-роли, дни рождения |
| **Экономика** | Валюта сервера, магазин, daily, казино |
| **VALORANT** | Premier-заявки, ролевые панели, команды `/valorant`, ValChecker и Кастомки |
| **Игры** | Семья и поставки (GTA5RP), Мафия, Бункер, Wordle, рулетка и Relations |
| **Контент** | События, розыгрыши, опросы, эмбеды, стримы, ротация баннера и иконки |

На сервере: **`/help`**. Статус бота: `Playing /help • Cheterin`.  
Публичный Lookup (ID / инвайт, без входа в панель): [cheterin.online/lookup](https://cheterin.online/lookup).

---

## С чего начать

1. Добавьте бота на сервер через [cheterin.online](https://cheterin.online).
2. Войдите в панель тем же Discord-аккаунтом.
3. Выберите сервер и включите нужные модули — настройки каждого сервера независимы.
4. Подробности — в [документации](https://cheterin.online/docs).

Поддержка: **[Cheterin Group](https://discord.gg/cheterin)** · Почта: **turkapahf@gmail.com**

---

## Структура репозитория

| Путь | Назначение |
|:---|:---|
| `main.py` | Точка входа бота + встроенная панель (один OS-процесс) |
| `bot/` | Пакет бота: `core/`, `modules/*`, `cards/`, `data/` |
| `dashboard/` | Веб-панель (backend aiohttp + frontend Vite/React) |
| `lookup/` + `lookup-api/` | Публичный Lookup (**отдельный процесс**, не из `main.py`) |
| `docs/` | Инженерные docs (`ARCHITECTURE`, план Lookup) — EN + RU |
| `scripts/` + `update.sh` | Полный VPS-update (сборки bot+Lookup + restart systemd) |
| `deploy/systemd/` | Unit-файлы `cheterin-bot` / `cheterin-lookup` |
| `locales/` | Строки бота (RU/EN) |
| `LICENSE` | Apache License 2.0 |
| `.github/workflows/ci.yml` | CI: pytest + сборки фронтендов |

Карты: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (EN) · [`docs/ARCHITECTURE.ru.md`](docs/ARCHITECTURE.ru.md) (RU).

---

## Локальная разработка (кратко)

**Бот + панель** (корневой `.env` из `.env.example` — секреты не коммитить):

```bash
pip install -r requirements.txt
cd dashboard/frontend && npm ci && npm run build && cd ../..
python main.py
```

**Lookup** (изолирован; `lookup-api/.env` с `LOOKUP_DISCORD_TOKENS` / `LOOKUP_DISCORD_TOKEN`, никогда `BOT_TOKEN`):

```bash
cd lookup-api && pip install -r requirements.txt && python app.py
cd lookup && npm ci && npm run dev
```

Тесты без Discord-токенов:

```bash
pytest
cd lookup-api && pytest
cd dashboard/frontend && npm ci && npm run build
cd lookup && npm ci && npm run build
```

---

## Деплой (операторы)

Сайт: [cheterin.online](https://cheterin.online).

- **Процессы:** systemd **`cheterin-bot.service`** (`python main.py` = бот + панель) и **`cheterin-lookup.service`** (Lookup API на **8090**). Статика SPA: nginx `/lookup` → `lookup/dist`. Unit-файлы: [`deploy/systemd/`](deploy/systemd/).
- **Один update:** `bash ~/Cheterin_Bot_Dashboard/update.sh` — `git pull`, pip для bot + lookup-api, сборка **обоих** фронтендов, `systemctl restart` обоих unit.
- Unit ставятся на хост один раз (см. [`deploy/systemd/README.md`](deploy/systemd/README.md)). Агенты не делают SSH и не включают unit за вас.

SSH-хост, ключи и прочие ops-секреты хранятся только локально в `.cursor/rules/` (в gitignore). Не коммитьте IP продакшена, пути к ключам и значения `.env`.

---

## Contributing / гигиена

- Лицензия: [Apache-2.0](LICENSE) · © 2026 Cheterin Group.
- CI на push/PR в `main` (приватные Discord-токены не нужны).
- Lookup не встраивать в `main.py`.
- Не коммитить `.env`, токены, SSH-ключи.
- Публичный email: `turkapahf@gmail.com`.

Языки UI: **русский** и **английский**. Канонический README репозитория — [английский](README.md).

---

## Ссылки

| | |
|:---|:---|
| **Панель** | [cheterin.online](https://cheterin.online) |
| **Документация** | [cheterin.online/docs](https://cheterin.online/docs) |
| **Dev Blog** | [cheterin.online/dev-blog](https://cheterin.online/dev-blog) |
| **Lookup** | [cheterin.online/lookup](https://cheterin.online/lookup) |
| **Авторы** | [cheterin.online/credits](https://cheterin.online/credits) |
| **Репозиторий** | [github.com/Nanda070/Cheterin_Bot_Dashboard](https://github.com/Nanda070/Cheterin_Bot_Dashboard) |
| **Cheterin Group** | [discord.gg/cheterin](https://discord.gg/cheterin) |
| **Организация** | [github.com/orgs/ChetTeam](https://github.com/orgs/ChetTeam) |
| **Privacy / Terms** | [privacy](https://cheterin.online/privacy) · [terms](https://cheterin.online/terms) |
| **README (EN)** | [README.md](README.md) |

---

<p align="center">
  <sub>© 2026 Cheterin Group Ø · часть экосистемы <a href="https://discord.gg/cheterin">Cheterin Group</a> · Apache-2.0</sub>
</p>
