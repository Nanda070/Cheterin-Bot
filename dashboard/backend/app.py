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
from .routes.supply import routes as supply_routes
from .routes.voice import routes as voice_routes
from .routes.news import routes as news_routes
from .session import setup_session
from .static import setup_static_routes

logger = logging.getLogger("dashboard")


@web.middleware
async def json_error_middleware(request, handler):
    try:
        return await handler(request)
    except web.HTTPException:
        raise
    except Exception:
        logger.exception("Unhandled dashboard error on %s", request.path)
        return web.json_response({"error": "internal_error"}, status=500)


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
    app.add_routes(supply_routes)
    app.add_routes(voice_routes)
    app.add_routes(news_routes)

    async def health(request: web.Request) -> web.Response:
        return web.json_response({"status": "ok"})

    app.router.add_get("/api/health", health)

    if frontend_dist is not None and frontend_dist.is_dir():
        setup_static_routes(app, frontend_dist)

    async def cleanup_http_session(cleanup_app: web.Application) -> None:
        await cleanup_app["http_session"].close()

    app.on_cleanup.append(cleanup_http_session)
    return app


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
        runner = web.AppRunner(app)
        await runner.setup()
        try:
            site = web.TCPSite(runner, "0.0.0.0", config.port)
            await site.start()
        except OSError as exc:
            logger.error("Dashboard disabled: failed to bind port %s (%s)", config.port, exc)
            await runner.cleanup()
            return None
    except Exception:
        # Belt-and-braces: any unexpected failure during app construction or
        # startup must never propagate out of start_dashboard, or it would
        # take the whole bot process down with it. Log and disable instead.
        logger.exception("Dashboard disabled: unexpected error during startup")
        if runner is not None:
            try:
                await runner.cleanup()
            except Exception:
                logger.exception("Dashboard: error while cleaning up after failed startup")
        return None

    logger.info("Dashboard listening on port %s", config.port)
    return runner
