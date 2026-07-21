"""Per-request guild-контекст (Фаза 2.3).

Раньше гильдия была одна на всё приложение (`app["guild_id"]`). Теперь каждый
запрос работает со своим сервером: этот middleware выставляет `request["guild_id"]`
дефолтом (мейн-сервер из `app["guild_id"]`), а `require_dashboard_access`
перезаписывает его выбранным в сессии `active_guild_id`. Благодаря дефолту даже
публичные (без авторизации) роуты безопасно читают `request["guild_id"]`.
"""

from aiohttp import web


@web.middleware
async def guild_context_middleware(request: web.Request, handler):
    request["guild_id"] = request.app.get("guild_id")
    return await handler(request)
