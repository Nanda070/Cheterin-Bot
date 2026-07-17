import secrets

from aiohttp import web
from aiohttp_session import get_session

from .discord_oauth import DiscordOAuthError, exchange_code_for_token, fetch_discord_identity
from .access import has_dashboard_access, has_super_admin_access
from .member_lookup import resolve_guild_member

routes = web.RouteTableDef()

STATE_COOKIE_NAME = "oauth_state"
DISCORD_AUTHORIZE_URL = "https://discord.com/api/oauth2/authorize"


@routes.get("/api/auth/login")
async def login(request: web.Request) -> web.Response:
    config = request.app["dashboard_config"]
    state = secrets.token_urlsafe(32)
    authorize_url = (
        f"{DISCORD_AUTHORIZE_URL}?client_id={config.client_id}"
        f"&redirect_uri={config.redirect_uri}"
        f"&response_type=code&scope=identify&state={state}"
    )
    response = web.HTTPFound(authorize_url)
    response.set_cookie(STATE_COOKIE_NAME, state, httponly=True, max_age=600)
    return response


@routes.get("/api/auth/discord/callback")
async def callback(request: web.Request) -> web.Response:
    config = request.app["dashboard_config"]
    bot = request.app["bot"]
    guild_id = request.app["guild_id"]

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
    lookup = await resolve_guild_member(bot, guild_id, user_id)

    if lookup.service_error:
        return web.HTTPFound(f"{config.frontend_url}/login?auth_error=service_unavailable")
    if lookup.not_found or lookup.member is None:
        return web.HTTPFound(f"{config.frontend_url}/access-denied?reason=not_a_member")
    if not has_dashboard_access(lookup.member, config.access_role_ids):
        return web.HTTPFound(f"{config.frontend_url}/access-denied?reason=insufficient_role")

    session = await get_session(request)
    session["discord_user_id"] = str(user_id)

    response = web.HTTPFound(f"{config.frontend_url}/")
    response.del_cookie(STATE_COOKIE_NAME)
    return response


@routes.post("/api/auth/logout")
async def logout(request: web.Request) -> web.Response:
    session = await get_session(request)
    session.invalidate()
    return web.json_response({"ok": True})


@routes.get("/api/auth/me")
async def me(request: web.Request) -> web.Response:
    session = await get_session(request)
    user_id = session.get("discord_user_id")
    if not user_id:
        return web.json_response({"error": "unauthorized"}, status=401)

    config = request.app["dashboard_config"]
    bot = request.app["bot"]
    guild_id = request.app["guild_id"]

    lookup = await resolve_guild_member(bot, guild_id, int(user_id))
    if lookup.service_error:
        return web.json_response({"error": "service_unavailable"}, status=503)
    if lookup.not_found or lookup.member is None:
        return web.json_response({"error": "forbidden"}, status=403)
    if not has_dashboard_access(lookup.member, config.access_role_ids):
        return web.json_response({"error": "forbidden"}, status=403)

    member = lookup.member
    return web.json_response(
        {
            "id": str(member.id),
            "username": member.name,
            "avatar": str(member.display_avatar.url) if member.display_avatar else None,
            "is_admin": member.guild_permissions.administrator,
            "is_super_admin": has_super_admin_access(member),
        }
    )
