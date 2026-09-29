"""Banner + icon rotation routes."""

from __future__ import annotations

import mimetypes

from aiohttp import web

import bot.modules.community.banner_rotation_core as banner_rotation_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


# ──────────────────────── helpers ────────────────────────


def _settings_response(guild_id: int) -> dict:
    cfg = banner_rotation_core.get_settings(guild_id)
    return cfg


def _image_url(image_id: str, kind: str) -> str:
    return f"/api/banner-rotation/assets/{kind}/{image_id}"


def _enrich(cfg: dict) -> dict:
    for img in cfg.get("banners", []):
        img["url"] = _image_url(img["id"], "banner")
    for img in cfg.get("icons", []):
        img["url"] = _image_url(img["id"], "icon")
    return cfg


# ──────────────────────── settings ────────────────────────


@routes.get("/api/banner-rotation")
@require_dashboard_access
async def banner_rotation_get(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    cfg = banner_rotation_core.get_settings(guild_id)
    return web.json_response(_enrich(cfg))


@routes.put("/api/banner-rotation")
@require_dashboard_access
async def banner_rotation_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    guild_id = request["guild_id"]

    try:
        interval = int(body.get("interval_minutes", banner_rotation_core.INTERVAL_DEFAULT))
        banner_rotation_core.validate_interval(interval)
    except (ValueError, TypeError):
        return web.json_response({"error": "invalid_interval"}, status=400)

    try:
        banner_mode = banner_rotation_core.normalize_banner_mode(
            body.get("banner_mode", banner_rotation_core.BANNER_MODE_PLAYLIST),
        )
    except ValueError:
        return web.json_response({"error": "invalid_banner_mode"}, status=400)
    dynamic_window_days = banner_rotation_core.normalize_dynamic_window_days(
        body.get("dynamic_window_days", banner_rotation_core.DYNAMIC_WINDOW_DAYS_DEFAULT),
    )

    try:
        cfg = banner_rotation_core.save_settings(
            guild_id,
            enabled=bool(body.get("enabled", False)),
            banner_enabled=bool(body.get("banner_enabled", True)),
            banner_mode=banner_mode,
            dynamic_window_days=dynamic_window_days,
            icon_enabled=bool(body.get("icon_enabled", True)),
            interval_minutes=interval,
            log_channel_id=str(body.get("log_channel_id") or ""),
        )
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)

    return web.json_response(_enrich(cfg))


# ──────────────────────── banner images ────────────────────────


@routes.post("/api/banner-rotation/banners")
@require_dashboard_access
async def banner_upload(request: web.Request) -> web.Response:
    return await _upload(request, "banner")


@routes.delete("/api/banner-rotation/banners/{image_id}")
@require_dashboard_access
async def banner_delete(request: web.Request) -> web.Response:
    return await _delete(request, "banner")


# ──────────────────────── icon images ────────────────────────


@routes.post("/api/banner-rotation/icons")
@require_dashboard_access
async def icon_upload(request: web.Request) -> web.Response:
    return await _upload(request, "icon")


@routes.delete("/api/banner-rotation/icons/{image_id}")
@require_dashboard_access
async def icon_delete(request: web.Request) -> web.Response:
    return await _delete(request, "icon")


# ──────────────────────── rotate now ────────────────────────


@routes.post("/api/banner-rotation/rotate-now")
@require_dashboard_access
async def rotate_now(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    bot = request.app["bot"]
    cog = bot.get_cog("BannerRotationCog")
    if cog is None:
        return web.json_response({"error": "cog_unavailable"}, status=503)
    result = await cog.rotate_now(guild_id)
    if not isinstance(result, dict):
        result = {"ok": bool(result), "error": None if result else "discord_rejected"}
    cfg = banner_rotation_core.get_settings(guild_id)
    if not result.get("ok"):
        error = str(result.get("error") or "discord_rejected")
        status = {
            "nothing_to_rotate": 400,
            "missing_permissions": 403,
            "boost_required": 502,
            "invalid_image": 502,
            "rate_limited": 429,
            "discord_rejected": 502,
            "internal_error": 500,
            "cog_unavailable": 503,
        }.get(error, 502)
        body: dict = {"ok": False, "error": error, "settings": _enrich(cfg)}
        for key in ("discord_status", "discord_code", "discord_text", "kind"):
            if result.get(key) is not None:
                body[key] = result[key]
        return web.json_response(body, status=status)
    return web.json_response({"ok": True, "settings": _enrich(cfg)})


# ──────────────────────── asset preview ────────────────────────


@routes.get("/api/banner-rotation/assets/{kind}/{image_id}")
@require_dashboard_access
async def asset_serve(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    kind = request.match_info["kind"]
    image_id = request.match_info["image_id"]

    if kind not in ("banner", "icon"):
        return web.json_response({"error": "not_found"}, status=404)

    path = banner_rotation_core.get_image_path(guild_id, kind, image_id)
    if path is None:
        return web.json_response({"error": "not_found"}, status=404)

    ct, _ = mimetypes.guess_type(str(path))
    ct = ct or "application/octet-stream"
    return web.Response(
        body=path.read_bytes(),
        content_type=ct,
        headers={"Cache-Control": "private, max-age=300"},
    )


# ──────────────────────── shared upload/delete ────────────────────────


async def _upload(request: web.Request, kind: str) -> web.Response:
    guild_id = request["guild_id"]

    content_type = request.headers.get("Content-Type", "")
    original_name = "upload"

    if "multipart/form-data" in content_type:
        reader = await request.multipart()
        field = await reader.next()
        if field is None:
            return web.json_response({"error": "no_file"}, status=400)
        original_name = field.filename or "upload"
        raw = await field.read(decode=True)
    else:
        raw = await request.read()

    if not raw:
        return web.json_response({"error": "no_file"}, status=400)

    fn_hint = request.headers.get("X-Filename", "")
    if fn_hint:
        original_name = fn_hint

    try:
        entry = banner_rotation_core.add_image(guild_id, kind, raw, original_name)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)

    entry["url"] = _image_url(entry["id"], kind)
    return web.json_response({"ok": True, "image": entry})


async def _delete(request: web.Request, kind: str) -> web.Response:
    guild_id = request["guild_id"]
    image_id = request.match_info["image_id"]
    deleted = banner_rotation_core.delete_image(guild_id, kind, image_id)
    if not deleted:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True})
