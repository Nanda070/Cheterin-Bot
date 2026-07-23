import functools

from aiohttp import web
from aiohttp_session import get_session

from .access import has_manage_server, has_super_admin_access
from .member_lookup import resolve_guild_member


def _has_legacy_role_access(member, allowed_role_ids: frozenset) -> bool:
    """Переходный грант по роли на активном сервере (если задан DASHBOARD_ACCESS_ROLE_IDS)."""
    if not allowed_role_ids:
        return False
    member_role_ids = {str(role.id) for role in member.roles}
    return not member_role_ids.isdisjoint(allowed_role_ids)


def require_dashboard_access(handler):
    """Гейт доступа к серверу (Фаза 2.3): сессия → активный сервер → Manage Server.

    Активный сервер берётся только из `session["active_guild_id"]` (выбор в дашборде).
    Без выбора — 400 `no_guild_selected` (без фолбэка на мейн-сервер приложения).
    Доступ = Manage Server/Administrator на этом сервере (плюс переходный грант по роли).
    Резолвнутый участник кладётся в `request["moderator"]`, а активная гильдия —
    в `request["guild_id"]`.
    """

    @functools.wraps(handler)
    async def wrapper(request: web.Request) -> web.StreamResponse:
        session = await get_session(request)
        user_id = session.get("discord_user_id")
        if not user_id:
            return web.json_response({"error": "unauthorized"}, status=401)

        config = request.app["dashboard_config"]
        bot = request.app["bot"]

        active_guild_id = session.get("active_guild_id")
        if active_guild_id is None:
            return web.json_response({"error": "no_guild_selected"}, status=400)
        guild_id = int(active_guild_id)

        lookup = await resolve_guild_member(bot, guild_id, int(user_id))
        if lookup.service_error:
            return web.json_response({"error": "service_unavailable"}, status=503)
        if lookup.not_found or lookup.member is None:
            return web.json_response({"error": "forbidden"}, status=403)
        if not (has_manage_server(lookup.member) or _has_legacy_role_access(lookup.member, config.access_role_ids)):
            return web.json_response({"error": "forbidden"}, status=403)

        request["guild_id"] = guild_id
        request["moderator"] = lookup.member
        return await handler(request)

    return wrapper


def require_super_admin(handler):
    """Гейт для списка серверов бота — намеренно хардкод-роль, см. access.py."""

    @functools.wraps(handler)
    async def wrapper(request: web.Request) -> web.StreamResponse:
        session = await get_session(request)
        user_id = session.get("discord_user_id")
        if not user_id:
            return web.json_response({"error": "unauthorized"}, status=401)

        bot = request.app["bot"]
        guild_id = request.app["guild_id"]

        lookup = await resolve_guild_member(bot, guild_id, int(user_id))
        if lookup.service_error:
            return web.json_response({"error": "service_unavailable"}, status=503)
        if lookup.not_found or lookup.member is None:
            return web.json_response({"error": "forbidden"}, status=403)
        if not has_super_admin_access(lookup.member):
            return web.json_response({"error": "forbidden"}, status=403)

        request["moderator"] = lookup.member
        # Привилегии мейна (news и т.п.) всегда пишут/читают настройки мейн-сервера,
        # даже если в сессии выбран другой active_guild_id.
        request["guild_id"] = guild_id
        return await handler(request)

    return wrapper
