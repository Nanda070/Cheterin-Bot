"""OAuth-логин и выбор сервера (Фаза 2.3, модель MEE6).

Логин больше не завязан на членство в одном сервере: пользователь входит через
Discord (scope `identify guilds`), затем выбирает сервер из тех, где у него есть
Manage Server и где присутствует бот. Активный сервер хранится в сессии
(`active_guild_id`); токены — там же (шифрованная cookie-сессия).
"""

import secrets
import time
import urllib.parse

from aiohttp import web
from aiohttp_session import get_session

from .discord_oauth import (
    DiscordOAuthError,
    exchange_code_for_token,
    fetch_discord_identity,
    fetch_user_guilds,
    refresh_access_token,
)
from .access import has_super_admin_access, has_manage_server, manageable_guilds
from .member_lookup import resolve_guild_member

routes = web.RouteTableDef()

STATE_COOKIE_NAME = "oauth_state"
DISCORD_AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"
OAUTH_SCOPE = "identify guilds"
GUILDS_CACHE_TTL = 60  # сек, антифлуд по рейт-лимитам Discord

# Права, нужные боту для полноценной работы модулей (битмаска для invite-ссылки).
INVITE_PERMISSIONS = (
    0x2               # KICK_MEMBERS
    | 0x4             # BAN_MEMBERS
    | 0x10            # MANAGE_CHANNELS
    | 0x20            # MANAGE_GUILD
    | 0x40            # ADD_REACTIONS
    | 0x80            # VIEW_AUDIT_LOG
    | 0x400           # VIEW_CHANNEL
    | 0x800           # SEND_MESSAGES
    | 0x2000          # MANAGE_MESSAGES
    | 0x4000          # EMBED_LINKS
    | 0x8000          # ATTACH_FILES
    | 0x10000         # READ_MESSAGE_HISTORY
    | 0x100000        # CONNECT
    | 0x1000000       # MOVE_MEMBERS
    | 0x10000000      # MANAGE_ROLES
    | 0x20000000      # MANAGE_WEBHOOKS
    | 0x10000000000   # MODERATE_MEMBERS
)


def _frontend(request: web.Request) -> str:
    return request.app["dashboard_config"].frontend_url


@routes.get("/api/auth/login")
async def login(request: web.Request) -> web.Response:
    config = request.app["dashboard_config"]
    state = secrets.token_urlsafe(32)
    authorize_url = (
        f"{DISCORD_AUTHORIZE_URL}?client_id={config.client_id}"
        f"&redirect_uri={urllib.parse.quote(config.redirect_uri, safe='')}"
        f"&response_type=code&scope={urllib.parse.quote(OAUTH_SCOPE)}&state={state}"
    )
    response = web.HTTPFound(authorize_url)
    response.set_cookie(STATE_COOKIE_NAME, state, httponly=True, max_age=600)
    return response


@routes.get("/api/auth/discord/callback")
async def callback(request: web.Request) -> web.Response:
    config = request.app["dashboard_config"]

    if request.query.get("error"):
        return web.HTTPFound(f"{config.frontend_url}/login?auth_error=denied")

    code = request.query.get("code")
    returned_state = request.query.get("state")
    cookie_state = request.cookies.get(STATE_COOKIE_NAME)
    if (
        not code
        or not returned_state
        or not cookie_state
        or not secrets.compare_digest(returned_state, cookie_state)
    ):
        return web.HTTPFound(f"{config.frontend_url}/login?auth_error=state_mismatch")

    http_session = request.app["http_session"]
    try:
        token_data = await exchange_code_for_token(
            http_session, code, config.client_id, config.client_secret, config.redirect_uri
        )
        identity = await fetch_discord_identity(http_session, token_data["access_token"])
    except DiscordOAuthError:
        return web.HTTPFound(f"{config.frontend_url}/login?auth_error=oauth_failed")

    user_id = int(identity["id"])

    session = await get_session(request)
    session["discord_user_id"] = str(user_id)
    session["access_token"] = token_data.get("access_token")
    session["refresh_token"] = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in")
    session["token_expires_at"] = int(time.time()) + int(expires_in) if expires_in else 0
    # Смена сервера через /servers: старый выбор сбрасываем.
    session.pop("active_guild_id", None)

    response = web.HTTPFound(f"{config.frontend_url}/servers")
    response.del_cookie(STATE_COOKIE_NAME)
    return response


async def _valid_access_token(request: web.Request, session) -> str | None:
    """Вернуть рабочий access_token, при необходимости обновив его по refresh_token."""
    token = session.get("access_token")
    expires_at = session.get("token_expires_at", 0)
    if token and (not expires_at or expires_at > int(time.time()) + 30):
        return token

    refresh = session.get("refresh_token")
    if not refresh:
        return token
    config = request.app["dashboard_config"]
    try:
        data = await refresh_access_token(
            request.app["http_session"], refresh, config.client_id, config.client_secret
        )
    except DiscordOAuthError:
        return None
    session["access_token"] = data.get("access_token")
    if data.get("refresh_token"):
        session["refresh_token"] = data["refresh_token"]
    expires_in = data.get("expires_in")
    session["token_expires_at"] = int(time.time()) + int(expires_in) if expires_in else 0
    return session["access_token"]


@routes.get("/api/auth/guilds")
async def list_guilds(request: web.Request) -> web.Response:
    session = await get_session(request)
    user_id = session.get("discord_user_id")
    if not user_id:
        return web.json_response({"error": "unauthorized"}, status=401)

    cache = request.app.setdefault("_guilds_cache", {})
    cached = cache.get(user_id)
    now = time.time()
    if cached and now - cached[0] < GUILDS_CACHE_TTL:
        return web.json_response({"guilds": cached[1]})

    token = await _valid_access_token(request, session)
    if not token:
        return web.json_response({"error": "unauthorized"}, status=401)

    try:
        raw = await fetch_user_guilds(request.app["http_session"], token)
    except DiscordOAuthError:
        return web.json_response({"error": "service_unavailable"}, status=503)

    guilds = manageable_guilds(raw, request.app["bot"])
    cache[user_id] = (now, guilds)
    return web.json_response({"guilds": guilds})


@routes.post("/api/auth/select-guild")
async def select_guild(request: web.Request) -> web.Response:
    session = await get_session(request)
    user_id = session.get("discord_user_id")
    if not user_id:
        return web.json_response({"error": "unauthorized"}, status=401)

    try:
        body = await request.json()
        guild_id = int(body["guild_id"])
    except (ValueError, KeyError, TypeError):
        return web.json_response({"error": "invalid_request"}, status=400)

    bot = request.app["bot"]
    if bot.get_guild(guild_id) is None:
        return web.json_response({"error": "bot_not_in_guild"}, status=404)

    # Не доверяем только OAuth-списку — проверяем реальные права участника на сервере.
    lookup = await resolve_guild_member(bot, guild_id, int(user_id))
    if lookup.service_error:
        return web.json_response({"error": "service_unavailable"}, status=503)
    if lookup.not_found or lookup.member is None or not has_manage_server(lookup.member):
        return web.json_response({"error": "forbidden"}, status=403)

    session["active_guild_id"] = str(guild_id)
    return web.json_response({"ok": True, "guild_id": str(guild_id)})


@routes.get("/api/auth/invite-url")
async def invite_url(request: web.Request) -> web.Response:
    config = request.app["dashboard_config"]
    guild_id = request.query.get("guild_id")
    params = {
        "client_id": config.client_id,
        "scope": "bot applications.commands",
        "permissions": str(INVITE_PERMISSIONS),
    }
    if guild_id and guild_id.isdigit():
        params["guild_id"] = guild_id
        params["disable_guild_select"] = "true"
    url = f"{DISCORD_AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"
    return web.json_response({"url": url})


@routes.post("/api/auth/logout")
async def logout(request: web.Request) -> web.Response:
    session = await get_session(request)
    cache = request.app.get("_guilds_cache")
    if cache is not None:
        cache.pop(session.get("discord_user_id"), None)
    session.invalidate()
    return web.json_response({"ok": True})


@routes.get("/api/auth/me")
async def me(request: web.Request) -> web.Response:
    session = await get_session(request)
    user_id = session.get("discord_user_id")
    if not user_id:
        return web.json_response({"error": "unauthorized"}, status=401)

    bot = request.app["bot"]
    active_guild_id = session.get("active_guild_id")

    # Супер-админ определяется на МЕЙН-сервере (дефолт приложения).
    is_super_admin = False
    main_guild_id = request.app.get("guild_id")
    if main_guild_id is not None:
        main_lookup = await resolve_guild_member(bot, int(main_guild_id), int(user_id))
        if main_lookup.member is not None:
            is_super_admin = has_super_admin_access(main_lookup.member)

    # Активен ли сейчас мейн-сервер (для CTD-настроек — привилегия мейна, Фаза 2b).
    is_main_guild = (
        active_guild_id is not None
        and main_guild_id is not None
        and int(active_guild_id) == int(main_guild_id)
    )

    payload = {
        "id": str(user_id),
        "active_guild_id": str(active_guild_id) if active_guild_id else None,
        "active_guild_name": None,
        "active_guild_icon": None,
        "is_super_admin": is_super_admin,
        "is_main_guild": is_main_guild,
    }

    # Данные активного сервера (имя/иконка) + участника на нём (имя/аватар/is_admin).
    if active_guild_id is not None:
        guild = bot.get_guild(int(active_guild_id))
        if guild is not None:
            payload["active_guild_name"] = guild.name
            payload["active_guild_icon"] = str(guild.icon.url) if guild.icon else None

        lookup = await resolve_guild_member(bot, int(active_guild_id), int(user_id))
        member = lookup.member
        if member is not None:
            payload.update({
                "username": member.name,
                "avatar": str(member.display_avatar.url) if member.display_avatar else None,
                "is_admin": member.guild_permissions.administrator,
            })
    return web.json_response(payload)
