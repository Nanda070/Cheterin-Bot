# Фаза 7 (Deploy) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Teach the aiohttp dashboard backend to serve the built React frontend from the same origin (with SPA fallback for client-side routes), and write a `DEPLOY.md` runbook for the user's already-provisioned Oracle Ubuntu server.

**Architecture:** A new `dashboard/backend/static.py` module registers a static-assets route plus a catch-all SPA-fallback route on an `aiohttp.web.Application`. `create_app()` gets an optional `frontend_dist: Path | None` parameter that, when given an existing directory, wires this module in as the *last* thing registered (after every `/api/*` route), so API routes always win the match first. `start_dashboard()` resolves this path from a new `DASHBOARD_FRONTEND_DIST` env var (empty/unset in dev, matching the existing `DASHBOARD_FRONTEND_URL` pattern). Separately, `DEPLOY.md` documents the exact server-side commands for DNS, Oracle Security List, nginx, certbot, and tmux.

**Tech Stack:** Python 3.11+, aiohttp (`web.Application`, `add_static`, `FileResponse`), pytest + pytest-aiohttp (`asyncio_mode = auto`, see `pytest.ini`).

## Global Constraints

- Route registration order matters: any new static/fallback routes must be registered **after** all existing `/api/*` routes in `create_app()`, never before — this project has twice shipped a route that was unreachable or shadowed due to registration order/omission (see `docs/superpowers/specs/2026-07-04-dashboard-phase7-deploy-design.md`).
- `create_app()`'s new `frontend_dist` parameter must default to `None` and change nothing about current dev behavior when omitted (Vite continues to serve the frontend separately on :5173).
- The new env var is `DASHBOARD_FRONTEND_DIST`, read the same way `DASHBOARD_FRONTEND_URL` already is (`env.get(key, "")`), not added to `REQUIRED_KEYS` in `dashboard/backend/config.py`.
- Deployment target: Oracle Cloud Ubuntu server (already provisioned, SSH access exists, Security List/ports 80+443 not yet opened), domain `cheterin.online` (already purchased, DNS panel accessible), nginx as reverse proxy with certbot/Let's Encrypt for TLS, **tmux for process persistence — systemd is explicitly out of scope**, no server-side file logging.
- Code is already transferred to the server via `git clone` (done by the user) — `DEPLOY.md` must say `git pull`, not `git clone`.
- `DEPLOY.md` is committed to the repo in plain text (it contains no secrets, only commands).

---

### Task 1: `DashboardConfig.frontend_dist` config field

**Files:**
- Modify: `dashboard/backend/config.py:9-16` (dataclass fields), `dashboard/backend/config.py:53-61` (`load_dashboard_config` return)
- Test: `dashboard/backend/tests/test_config.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `DashboardConfig.frontend_dist: str` (default `""`), read by Task 3's `start_dashboard()`.

- [ ] **Step 1: Write the failing tests**

Add to `dashboard/backend/tests/test_config.py` (after the existing `test_frontend_url_picked_up_when_present`, end of file):

```python
def test_frontend_dist_defaults_to_empty_string():
    config = load_dashboard_config(VALID_ENV)
    assert config.frontend_dist == ""


def test_frontend_dist_picked_up_when_present():
    env = dict(VALID_ENV, DASHBOARD_FRONTEND_DIST="/srv/chetmain/dashboard/frontend/dist")
    config = load_dashboard_config(env)
    assert config.frontend_dist == "/srv/chetmain/dashboard/frontend/dist"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_config.py -v`
Expected: the two new tests FAIL with `TypeError: DashboardConfig.__init__() got an unexpected keyword argument` or `AttributeError: 'DashboardConfig' object has no attribute 'frontend_dist'` (whichever surfaces first — the field doesn't exist yet).

- [ ] **Step 3: Add the field**

In `dashboard/backend/config.py`, the `DashboardConfig` dataclass currently ends with (lines 9-16):

```python
@dataclass(frozen=True)
class DashboardConfig:
    port: int
    client_id: str
    client_secret: str
    redirect_uri: str
    session_secret: str
    access_role_ids: frozenset
    frontend_url: str
```

Add `frontend_dist` with a default of `""` right after `frontend_url` (a default is required here since it's the last field and every other field has no default — dataclass field ordering requires defaulted fields to come after non-defaulted ones, and giving it a default also means the two existing direct-construction call sites, `dashboard/backend/tests/fakes.py` and `dashboard/backend/tests/test_auth.py`, don't need to change):

```python
@dataclass(frozen=True)
class DashboardConfig:
    port: int
    client_id: str
    client_secret: str
    redirect_uri: str
    session_secret: str
    access_role_ids: frozenset
    frontend_url: str
    frontend_dist: str = ""
```

Then in `load_dashboard_config` (lines 53-61), currently:

```python
    return DashboardConfig(
        port=port,
        client_id=env["DISCORD_CLIENT_ID"],
        client_secret=env["DISCORD_CLIENT_SECRET"],
        redirect_uri=env["DISCORD_OAUTH_REDIRECT_URI"],
        session_secret=session_secret,
        access_role_ids=role_ids,
        frontend_url=env.get("DASHBOARD_FRONTEND_URL", ""),
    )
```

change to:

```python
    return DashboardConfig(
        port=port,
        client_id=env["DISCORD_CLIENT_ID"],
        client_secret=env["DISCORD_CLIENT_SECRET"],
        redirect_uri=env["DISCORD_OAUTH_REDIRECT_URI"],
        session_secret=session_secret,
        access_role_ids=role_ids,
        frontend_url=env.get("DASHBOARD_FRONTEND_URL", ""),
        frontend_dist=env.get("DASHBOARD_FRONTEND_DIST", ""),
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_config.py -v`
Expected: all tests PASS, including the two new ones.

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/config.py dashboard/backend/tests/test_config.py
git commit -m "feat: add DashboardConfig.frontend_dist for prod static serving"
```

---

### Task 2: `static.py` — static assets + SPA fallback

**Files:**
- Create: `dashboard/backend/static.py`
- Test: `dashboard/backend/tests/test_static.py`

**Interfaces:**
- Consumes: nothing from Task 1 (this module only takes a plain `pathlib.Path`, no config dependency).
- Produces: `def setup_static_routes(app: aiohttp.web.Application, dist_dir: Path) -> None`, called by Task 3's `create_app()`.

- [ ] **Step 1: Write the failing tests**

Create `dashboard/backend/tests/test_static.py`:

```python
import pytest
from aiohttp import web

from dashboard.backend.static import setup_static_routes


@pytest.fixture
def dist_dir(tmp_path):
    d = tmp_path / "dist"
    d.mkdir()
    (d / "index.html").write_text("<html>SPA</html>", encoding="utf-8")
    assets = d / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('hi')", encoding="utf-8")
    return d


@pytest.mark.asyncio
async def test_unmatched_path_serves_index_html(aiohttp_client, dist_dir):
    app = web.Application()
    setup_static_routes(app, dist_dir)
    client = await aiohttp_client(app)

    resp = await client.get("/brackets/abc123")

    assert resp.status == 200
    text = await resp.text()
    assert text == "<html>SPA</html>"


@pytest.mark.asyncio
async def test_root_path_serves_index_html(aiohttp_client, dist_dir):
    app = web.Application()
    setup_static_routes(app, dist_dir)
    client = await aiohttp_client(app)

    resp = await client.get("/")

    assert resp.status == 200
    text = await resp.text()
    assert text == "<html>SPA</html>"


@pytest.mark.asyncio
async def test_asset_path_serves_asset_file(aiohttp_client, dist_dir):
    app = web.Application()
    setup_static_routes(app, dist_dir)
    client = await aiohttp_client(app)

    resp = await client.get("/assets/app.js")

    assert resp.status == 200
    text = await resp.text()
    assert text == "console.log('hi')"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_static.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'dashboard.backend.static'` (module doesn't exist yet).

- [ ] **Step 3: Write the implementation**

Create `dashboard/backend/static.py`:

```python
from pathlib import Path

from aiohttp import web


def setup_static_routes(app: web.Application, dist_dir: Path) -> None:
    assets_dir = dist_dir / "assets"
    if assets_dir.is_dir():
        app.router.add_static("/assets", assets_dir)

    index_path = dist_dir / "index.html"

    async def spa_fallback(request: web.Request) -> web.Response:
        return web.FileResponse(index_path)

    app.router.add_get("/{tail:.*}", spa_fallback)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_static.py -v`
Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add dashboard/backend/static.py dashboard/backend/tests/test_static.py
git commit -m "feat: add static.py for serving built frontend with SPA fallback"
```

---

### Task 3: Wire static serving into `create_app()` / `start_dashboard()`

**Files:**
- Modify: `dashboard/backend/app.py` (imports, `create_app` signature + body, `start_dashboard` body)
- Test: `dashboard/backend/tests/test_app.py`

**Interfaces:**
- Consumes: `DashboardConfig.frontend_dist: str` (Task 1), `setup_static_routes(app, dist_dir)` (Task 2).
- Produces: `create_app(bot, config, guild_id, frontend_dist: Path | None = None) -> web.Application` — the 4th parameter is new; existing 3-arg call sites (all current tests) keep working unchanged since it defaults to `None`.

- [ ] **Step 1: Write the failing tests**

Add to `dashboard/backend/tests/test_app.py`. First add `from pathlib import Path` to the imports at the top of the file (currently `import socket` / `from unittest.mock import patch` / `import pytest` / `import dashboard.backend.app as app_module` / `from dashboard.backend.app import create_app, start_dashboard`):

```python
from pathlib import Path
```

Then append these tests at the end of the file:

```python
@pytest.mark.asyncio
async def test_health_route_not_shadowed_by_static_fallback(aiohttp_client, tmp_path):
    from dashboard.backend.config import load_dashboard_config

    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html>SPA</html>", encoding="utf-8")

    config = load_dashboard_config(VALID_ENV)
    app = create_app(FakeBot(), config, guild_id=1, frontend_dist=dist_dir)
    client = await aiohttp_client(app)

    resp = await client.get("/api/health")

    assert resp.status == 200
    body = await resp.json()
    assert body == {"status": "ok"}


@pytest.mark.asyncio
async def test_unmatched_path_falls_back_to_index_when_frontend_dist_set(aiohttp_client, tmp_path):
    from dashboard.backend.config import load_dashboard_config

    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html>SPA</html>", encoding="utf-8")

    config = load_dashboard_config(VALID_ENV)
    app = create_app(FakeBot(), config, guild_id=1, frontend_dist=dist_dir)
    client = await aiohttp_client(app)

    resp = await client.get("/brackets/abc123")

    assert resp.status == 200
    text = await resp.text()
    assert text == "<html>SPA</html>"


@pytest.mark.asyncio
async def test_no_static_fallback_when_frontend_dist_is_none(aiohttp_client):
    from dashboard.backend.config import load_dashboard_config

    config = load_dashboard_config(VALID_ENV)
    app = create_app(FakeBot(), config, guild_id=1)
    client = await aiohttp_client(app)

    resp = await client.get("/some/nonexistent/path")

    assert resp.status == 404


@pytest.mark.asyncio
async def test_start_dashboard_passes_frontend_dist_from_config(tmp_path):
    dist_dir = tmp_path / "dist"
    dist_dir.mkdir()
    (dist_dir / "index.html").write_text("<html>SPA</html>", encoding="utf-8")

    captured = {}
    orig_create_app = app_module.create_app

    def spy_create_app(bot, config, guild_id, frontend_dist=None):
        captured["frontend_dist"] = frontend_dist
        return orig_create_app(bot, config, guild_id, frontend_dist=frontend_dist)

    env = dict(VALID_ENV, DASHBOARD_FRONTEND_DIST=str(dist_dir))
    with patch.object(app_module, "create_app", side_effect=spy_create_app):
        runner = await start_dashboard(FakeBot(), guild_id=1, env=env)

    assert runner is not None
    assert captured["frontend_dist"] == dist_dir
    await runner.cleanup()


@pytest.mark.asyncio
async def test_start_dashboard_passes_none_frontend_dist_when_unset():
    captured = {}
    orig_create_app = app_module.create_app

    def spy_create_app(bot, config, guild_id, frontend_dist=None):
        captured["frontend_dist"] = frontend_dist
        return orig_create_app(bot, config, guild_id, frontend_dist=frontend_dist)

    with patch.object(app_module, "create_app", side_effect=spy_create_app):
        runner = await start_dashboard(FakeBot(), guild_id=1, env=VALID_ENV)

    assert runner is not None
    assert captured["frontend_dist"] is None
    await runner.cleanup()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest dashboard/backend/tests/test_app.py -v`
Expected: the 5 new tests FAIL — the first three with `TypeError: create_app() got an unexpected keyword argument 'frontend_dist'`, the last two with an `AssertionError` (captured `frontend_dist` key missing, since `create_app` doesn't accept the parameter yet so the spy's signature itself would raise before that — either way, a clear failure pinned to the missing parameter).

- [ ] **Step 3: Modify `create_app()` and `start_dashboard()`**

In `dashboard/backend/app.py`, the imports at the top currently are:

```python
import logging
import os

import aiohttp
from aiohttp import web

from .auth import routes as auth_routes
from .config import ConfigError, DashboardConfig, load_dashboard_config
from .routes.brackets import routes as brackets_routes
from .routes.lockdown import routes as lockdown_routes
from .routes.moderation import routes as moderation_routes
from .routes.reaction_roles import routes as reaction_roles_routes
from .routes.embed_builder import routes as embed_builder_routes
from .routes.feedback import routes as feedback_routes
from .routes.events import routes as events_routes
from .routes.config import routes as config_routes
from .routes.welcome import routes as welcome_routes
from .routes.auto_roles import routes as auto_roles_routes
from .session import setup_session
```

Add `from pathlib import Path` (with the other stdlib imports) and `from .static import setup_static_routes`:

```python
import logging
import os
from pathlib import Path

import aiohttp
from aiohttp import web

from .auth import routes as auth_routes
from .config import ConfigError, DashboardConfig, load_dashboard_config
from .routes.brackets import routes as brackets_routes
from .routes.lockdown import routes as lockdown_routes
from .routes.moderation import routes as moderation_routes
from .routes.reaction_roles import routes as reaction_roles_routes
from .routes.embed_builder import routes as embed_builder_routes
from .routes.feedback import routes as feedback_routes
from .routes.events import routes as events_routes
from .routes.config import routes as config_routes
from .routes.welcome import routes as welcome_routes
from .routes.auto_roles import routes as auto_roles_routes
from .session import setup_session
from .static import setup_static_routes
```

Then `create_app()` currently ends (lines 35-63):

```python
def create_app(bot, config: DashboardConfig, guild_id: int) -> web.Application:
    app = web.Application(middlewares=[json_error_middleware])
    app["bot"] = bot
    app["dashboard_config"] = config
    app["guild_id"] = guild_id
    app["http_session"] = aiohttp.ClientSession()
    setup_session(app, config.session_secret)
    app.add_routes(auth_routes)
    app.add_routes(brackets_routes)
    app.add_routes(moderation_routes)
    app.add_routes(lockdown_routes)
    app.add_routes(reaction_roles_routes)
    app.add_routes(embed_builder_routes)
    app.add_routes(feedback_routes)
    app.add_routes(events_routes)
    app.add_routes(config_routes)
    app.add_routes(welcome_routes)
    app.add_routes(auto_roles_routes)

    async def health(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    app.router.add_get("/api/health", health)

    async def cleanup_http_session(cleanup_app: web.Application) -> None:
        await cleanup_app["http_session"].close()

    app.on_cleanup.append(cleanup_http_session)
    return app
```

Change the signature to accept `frontend_dist`, and register static routes **last**, after `/api/health` (which itself stays last among the API routes):

```python
def create_app(
    bot,
    config: DashboardConfig,
    guild_id: int,
    frontend_dist: Path | None = None,
) -> web.Application:
    app = web.Application(middlewares=[json_error_middleware])
    app["bot"] = bot
    app["dashboard_config"] = config
    app["guild_id"] = guild_id
    app["http_session"] = aiohttp.ClientSession()
    setup_session(app, config.session_secret)
    app.add_routes(auth_routes)
    app.add_routes(brackets_routes)
    app.add_routes(moderation_routes)
    app.add_routes(lockdown_routes)
    app.add_routes(reaction_roles_routes)
    app.add_routes(embed_builder_routes)
    app.add_routes(feedback_routes)
    app.add_routes(events_routes)
    app.add_routes(config_routes)
    app.add_routes(welcome_routes)
    app.add_routes(auto_roles_routes)

    async def health(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    app.router.add_get("/api/health", health)

    if frontend_dist is not None and frontend_dist.is_dir():
        setup_static_routes(app, frontend_dist)

    async def cleanup_http_session(cleanup_app: web.Application) -> None:
        await cleanup_app["http_session"].close()

    app.on_cleanup.append(cleanup_http_session)
    return app
```

Finally, `start_dashboard()` currently starts:

```python
async def start_dashboard(bot, guild_id: int, env: dict | None = None) -> web.AppRunner | None:
    env = env if env is not None else os.environ
    try:
        config = load_dashboard_config(env)
    except ConfigError as exc:
        logger.error("Dashboard disabled: %s", exc)
        return None

    runner = None
    try:
        app = create_app(bot, config, guild_id)
```

Change to resolve `frontend_dist` from the config and pass it through:

```python
async def start_dashboard(bot, guild_id: int, env: dict | None = None) -> web.AppRunner | None:
    env = env if env is not None else os.environ
    try:
        config = load_dashboard_config(env)
    except ConfigError as exc:
        logger.error("Dashboard disabled: %s", exc)
        return None

    frontend_dist = Path(config.frontend_dist) if config.frontend_dist else None

    runner = None
    try:
        app = create_app(bot, config, guild_id, frontend_dist=frontend_dist)
```

The rest of `start_dashboard()` (the `try`/`except OSError`/`except Exception` blocks below this line) is unchanged.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest dashboard/backend/tests/test_app.py -v`
Expected: all tests PASS (existing tests plus the 5 new ones).

- [ ] **Step 5: Run the full backend test suite**

Run: `python -m pytest dashboard/backend/tests/ -v`
Expected: all tests PASS — this confirms nothing in the other route test files broke from the `create_app` signature change (all existing call sites use `create_app(bot, config, guild_id=N)`, which still works since `frontend_dist` is keyword-only-by-convention with a default).

- [ ] **Step 6: Commit**

```bash
git add dashboard/backend/app.py dashboard/backend/tests/test_app.py
git commit -m "feat: serve built frontend with SPA fallback when DASHBOARD_FRONTEND_DIST is set"
```

---

### Task 4: `DEPLOY.md` runbook

**Files:**
- Create: `DEPLOY.md` (repo root)

**Interfaces:**
- Consumes: `DASHBOARD_FRONTEND_DIST` env var name (Task 1), confirms the app now supports prod static serving (Task 3).
- Produces: nothing consumed by other tasks — this is the terminal deliverable of the plan.

- [ ] **Step 1: Write `DEPLOY.md`**

Create `DEPLOY.md` at the repo root with this exact content:

````markdown
# Деплой на продакшен (Oracle Cloud, Ubuntu)

Этот гайд предполагает: Oracle Cloud compute instance с Ubuntu уже создан, есть SSH-доступ, домен `cheterin.online` уже куплен и панель DNS-провайдера доступна. Код уже перенесён на сервер через `git clone` (репозиторий `https://github.com/Nanda070/Cheterin_Bot_Dashboard.git`).

## 1. DNS

В панели вашего DNS-провайдера (там, где куплен `cheterin.online`) добавьте A-запись:

| Тип | Имя | Значение |
|-----|-----|----------|
| A   | `@` (или `cheterin.online`) | публичный IP сервера |
| A   | `www` | публичный IP сервера |

Подождите распространения DNS (обычно от нескольких минут до часа) перед шагом с certbot — certbot проверяет, что домен резолвится на этот сервер.

## 2. Oracle Cloud Security List

В консоли Oracle Cloud: **Networking → Virtual Cloud Networks → (ваша VCN) → Security Lists → (список по умолчанию) → Ingress Rules → Add Ingress Rules**.

Добавьте два правила (если ещё не добавлены):

- Source CIDR `0.0.0.0/0`, IP Protocol `TCP`, Destination Port Range `80`
- Source CIDR `0.0.0.0/0`, IP Protocol `TCP`, Destination Port Range `443`

Это отдельный уровень firewall от `ufw` на самой машине — оба должны быть открыты одновременно, иначе соединение не пройдёт даже при правильно настроенном `ufw`.

## 3. Firewall на сервере (ufw)

Подключитесь по SSH к серверу и выполните:

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw status
```

Убедитесь, что порт 22 (SSH) в списке разрешённых, прежде чем включать `ufw`, если он ещё не включён (`sudo ufw enable`) — иначе можно потерять доступ к серверу.

## 4. Системные зависимости

```bash
sudo apt update
sudo apt install -y nginx certbot python3-certbot-nginx tmux python3 python3-venv python3-pip
```

Для сборки фронтенда нужен Node.js (LTS, через NodeSource, так как версия в стандартном репозитории Ubuntu обычно старая):

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
node --version
```

## 5. Обновление кода

Код уже склонирован на сервер. Перед каждым обновлением (включая внедрение раздачи статики из этой фазы):

```bash
cd ~/ChetMain
git pull origin main
```

## 6. Правки `.env` на сервере

Откройте `.env` в корне проекта на сервере и измените/добавьте следующие значения (остальные ключи — токены, ID каналов и ролей — не трогайте, они те же, что и в разработке):

```
DISCORD_OAUTH_REDIRECT_URI=https://cheterin.online/api/auth/discord/callback
DASHBOARD_FRONTEND_URL=
DASHBOARD_FRONTEND_DIST=/home/<ваш-пользователь>/ChetMain/dashboard/frontend/dist
```

Замените `<ваш-пользователь>` на реальное имя пользователя на сервере (проверить командой `whoami`), и используйте **абсолютный путь** — не относительный, так как `python main.py` может быть запущен из tmux-сессии с произвольным текущим рабочим каталогом.

Также добавьте `https://cheterin.online/api/auth/discord/callback` в список Redirect URIs в [Discord Developer Portal](https://discord.com/developers/applications) → ваше приложение → OAuth2 → Redirects. **Не удаляйте** существующий `http://localhost:8080/...` URI — оба могут сосуществовать, это нужно для локальной разработки.

## 7. Установка зависимостей и сборка

```bash
cd ~/ChetMain
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd dashboard/frontend
npm ci
npm run build
cd ~/ChetMain
```

Сборка фронтенда создаёт `dashboard/frontend/dist/` — именно на эту папку должен указывать `DASHBOARD_FRONTEND_DIST` из шага 6.

## 8. nginx + TLS (certbot)

Создайте конфиг `/etc/nginx/sites-available/cheterin`:

```nginx
server {
    listen 80;
    server_name cheterin.online www.cheterin.online;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Включите сайт и перезапустите nginx:

```bash
sudo ln -s /etc/nginx/sites-available/cheterin /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Получите TLS-сертификат (certbot сам допишет `listen 443 ssl` и настроит редирект с http на https в этом файле):

```bash
sudo certbot --nginx -d cheterin.online -d www.cheterin.online
```

## 9. Запуск бота+дашборда в tmux

tmux используется вместо systemd осознанно — процесс не переживёт перезагрузку сервера, после ребута нужно будет зайти по SSH и перезапустить вручную.

```bash
cd ~/ChetMain
tmux new -s chetmain
source venv/bin/activate
python main.py
```

Отсоединиться от сессии, оставив процесс работать: `Ctrl+B`, затем `D`.

Подключиться обратно после переподключения по SSH:

```bash
tmux attach -t chetmain
```

Посмотреть список запущенных tmux-сессий: `tmux ls`.

## 10. Проверка

1. Откройте `https://cheterin.online` в браузере — должна открыться страница логина.
2. Пройдите логин через Discord OAuth — должно перекинуть на главную страницу дашборда.
3. Откройте любую страницу с client-side маршрутом (например раздел "Сетки" → конкретная сетка) и сделайте обновление страницы (F5) — страница должна открыться заново, а не выдать 404 (это и есть проверка SPA-fallback в проде).
4. Проверьте, что бот онлайн на Discord-сервере как обычно.
````

- [ ] **Step 2: Cross-check the content against the real repo**

Confirm the exact values used above are correct for the current codebase:

```bash
grep -n "DISCORD_OAUTH_REDIRECT_URI\|DASHBOARD_FRONTEND_URL" .env
grep -n "DASHBOARD_PORT" .env
cat requirements.txt
```

Confirm: the `.env` redirect URI line exists and is being replaced (not left duplicated), the port referenced in the nginx `proxy_pass` (`8080`) matches `DASHBOARD_PORT` in `.env`, and `requirements.txt` is the correct file name referenced in step 7.

- [ ] **Step 3: Commit**

```bash
git add DEPLOY.md
git commit -m "docs: add DEPLOY.md runbook for Oracle Cloud production deployment"
```
