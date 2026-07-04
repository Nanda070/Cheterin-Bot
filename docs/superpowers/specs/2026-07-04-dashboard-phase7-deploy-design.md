# Фаза 7: Деплой — дизайн

## Контекст

Последняя фаза 7-фазного роадмапа ChetMain dashboard. К моменту написания этого спека уже сделано (вне обычного пайплайна brainstorm→spec→plan, как прямая операционная работа по явному запросу пользователя 2026-07-04):

- Репозиторий выложен на GitHub (`https://github.com/Nanda070/Cheterin_Bot_Dashboard.git`, ветка `main`), включая реальный `.env` с боевыми секретами — осознанное решение пользователя, задокументировано в памяти.
- Боевой токен бота уже в рабочем `.env`.
- Папки на диске разработчика переименованы (`ChetMain` = рабочая копия).
- Домен `cheterin.online` куплен, DNS-панель доступна.
- Oracle Cloud Ubuntu-сервер уже создан, есть SSH-доступ; Security List/порты 80/443 ещё не настроены.
- Файлы проекта уже перенесены на сервер (`git clone` пользователь выполнил сам).

Пользователь подтвердил инфраструктурные решения:
- **nginx** — reverse proxy перед aiohttp, для TLS через Let's Encrypt/certbot.
- **tmux** — персистентность процесса. **Systemd явно не нужен** (дважды подтверждено).
- Логирование в файл на сервере — не нужно сейчас.
- Раздача статики фронтенда через aiohttp — часть этой фазы (не откладывается).

Работа делится на две независимые части:
1. **Код** — aiohttp должен научиться отдавать собранный фронтенд (`dashboard/frontend/dist`) с SPA-fallback. Тестируемо, идёт через subagent-driven-development.
2. **Раздок** (`DEPLOY.md`) — пошаговые команды для сервера. Не код, не через TDD, но пишется точно под текущий `.env`/конфиг проекта и коммитится в репозиторий.

## Часть 1: Раздача статики фронтенда через aiohttp

### Новый модуль `dashboard/backend/static.py`

```python
def setup_static_routes(app: web.Application, dist_dir: Path) -> None:
    ...
```

Регистрирует, в этом порядке (порядок критичен в роутере aiohttp — этот проект уже дважды натыкался на баг «роут создан, но не зарегистрирован» / «зарегистрирован не в том порядке»):

1. `app.router.add_static('/assets', dist_dir / 'assets')` — хэшированные JS/CSS-файлы, которые Vite кладёт в `dist/assets/`.
2. Один catch-all `GET /{tail:.*}` handler, регистрируемый **после** всех `/api/*` роутов и после `add_static` (то есть вызов `setup_static_routes` — последняя строка в `create_app()`, после всех остальных `app.add_routes(...)`). Handler:
   - Если путь начинается с `/api/` — не должен сюда попасть вообще (все `/api/*` роуты уже зарегистрированы раньше и матчатся первыми); это защищается тестом, а не кодом.
   - Иначе читает и отдаёт `dist_dir / 'index.html'` как `text/html` (React Router на клиенте сам разберёт путь).

### Интеграция в `create_app()`

`create_app(bot, config, guild_id, frontend_dist: Path | None = None)` — новый опциональный параметр, по умолчанию `None` (текущее dev-поведение: Vite отдаёт фронтенд отдельно на :5173, aiohttp статику не трогает). Если `frontend_dist` передан и директория существует — в конце `create_app()` вызывается `setup_static_routes(app, frontend_dist)`.

`start_dashboard()` резолвит `frontend_dist` из нового env-ключа `DASHBOARD_FRONTEND_DIST` (пусто/не задан в dev — по аналогии с уже существующим паттерном `DASHBOARD_FRONTEND_URL`, которое тоже пусто в проде). В `DashboardConfig` добавляется поле `frontend_dist: str` (default `""` через `env.get(...)`, не входит в `REQUIRED_KEYS`).

**Редиректы `auth.py` менять не нужно** — `config.frontend_url` уже `""` в проде, поэтому `f"{config.frontend_url}/login?..."` уже резолвится в относительный `/login?...`, что и есть правильное поведение при раздаче с одного origin.

### Тесты

`dashboard/backend/tests/test_static.py`:
- Фикстура создаёт временную `dist/`-директорию (`tmp_path`) с фиктивным `index.html` и `assets/app.js` — **не** настоящую сборку через `npm run build` (слишком медленно/тяжело для юнит-теста).
- Незаматченный путь (например `/brackets/abc123`) → 200, тело = содержимое `index.html`.
- `/assets/app.js` → 200, тело = содержимое файла.
- `/api/health` (существующий роут) всё ещё отдаёт `{"status": "ok"}`, а не перехватывается catch-all-хендлером — регрессионный тест именно на порядок регистрации роутов, по опыту прошлых фаз.
- Тест на `create_app(..., frontend_dist=None)` — старое поведение не ломается, catch-all не регистрируется вовсе.

### Ручная локальная проверка (не автотест, перед переносом на сервер)

1. `cd dashboard/frontend && npm run build` — реальная прод-сборка.
2. Запустить бэкенд с `DASHBOARD_FRONTEND_DIST` указывающим на `dashboard/frontend/dist` и пустым `DASHBOARD_FRONTEND_URL`.
3. Открыть `http://localhost:8080` напрямую (без Vite dev-сервера на :5173), пройти логин, открыть страницу с client-side маршрутом (например `/brackets/...`) и сделать hard refresh — убедиться, что не 404.

## Часть 2: `DEPLOY.md`

Новый файл в корне репозитория, коммитится в git (не секрет — только команды и инструкции). Содержит, по порядку:

1. **DNS** — какую A-запись добавить в панели DNS-провайдера для `cheterin.online` (и `www`), указывающую на публичный IP сервера. (Действие пользователя в панели провайдера.)
2. **Oracle Security List** — открыть ingress для TCP 80 и 443 (0.0.0.0/0) в VCN Security List в консоли Oracle Cloud — отдельно от `ufw`, это частая ловушка Oracle Free Tier.
3. **ufw** — `sudo ufw allow 80,443/tcp`, проверка что 22 (SSH) остаётся открытым.
4. **Системные зависимости** — `apt install nginx certbot python3-certbot-nginx tmux`, Python 3.11+, Node.js (LTS) — точные команды под Ubuntu.
5. **Синхронизация кода** — файлы уже перенесены (`git clone` пользователь сделал сам); здесь просто `git pull origin main`, чтобы забрать коммит с раздачей статики, когда он появится.
6. **Правки `.env` на сервере** — `DISCORD_OAUTH_REDIRECT_URI=https://cheterin.online/api/auth/discord/callback`, `DASHBOARD_FRONTEND_URL=` (пусто), `DASHBOARD_FRONTEND_DIST=` абсолютный путь до `dist/` на сервере (например `/home/<пользователь>/ChetMain/dashboard/frontend/dist` — абсолютный, а не относительный, потому что `python main.py` может запускаться из tmux-сессии с произвольным текущим рабочим каталогом). Плюс явное напоминание добавить новый redirect URI в Discord Developer Portal (OAuth2 → Redirects) — старый `localhost`-URI не удалять, оба могут сосуществовать.
7. **Установка зависимостей и сборка** — `pip install -r requirements.txt` (или venv-эквивалент, смотря что уже есть в репозитории), `cd dashboard/frontend && npm ci && npm run build`.
8. **nginx** — конфиг reverse-proxy для `cheterin.online` → `127.0.0.1:8080`, затем `sudo certbot --nginx -d cheterin.online` для TLS.
9. **Запуск в tmux** — `tmux new -s chetmain`, `python main.py`, детач (`Ctrl+B D`); как переподключиться (`tmux attach -t chetmain`); явное предупреждение, что tmux-сессия не переживёт перезагрузку сервера — после ребута нужно будет руками зайти по SSH и перезапустить (осознанный компромисс выбора tmux вместо systemd).
10. **Проверка** — открыть `https://cheterin.online`, пройти логин через Discord, открыть страницу с client-side маршрутом и обновить её (проверка SPA-fallback уже в проде).

## Границы (что НЕ входит в эту фазу)

- Автозапуск при перезагрузке сервера (сознательно отклонено — tmux, не systemd).
- Файловое логирование на сервере (пользователь ответил "нет").
- Создание самого Oracle compute instance — сервер уже существует.
- CI/CD (автодеплой по пушу) — не запрашивалось.
