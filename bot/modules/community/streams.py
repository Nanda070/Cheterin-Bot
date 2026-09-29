"""Стрим- и видео-уведомления: Twitch, YouTube, TikTok (per-guild).

- Twitch: опрос Helix API (нужны TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET в .env).
  Уведомление при переходе канала в эфир.
- YouTube: опрос публичного RSS-фида канала. Уведомление о новом видео/премьере.
- TikTok: видео — embed/@user (videoList), tikwm, RSSHub;
  LIVE — /@user/live (SIGI) с fallback на api-live/user/room и webcast.
  Resolve: TikTok oEmbed профиля + embed + tikwm.

Подписки настраиваются в дашборде: канал публикации, роль для пинга, свой
шаблон, ключевые слова по названию, минимальный интервал между уведомлениями.
Настройки хранятся per-guild в settings_db.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import xml.etree.ElementTree as ET

import aiohttp
import discord
from discord.ext import commands, tasks

import bot.core.components_v2 as components_v2
import bot.core.embed_style as embed_style
import bot.core.i18n as i18n
import bot.core.settings_db as settings_db

logger = logging.getLogger("streams")

MODULE_NAME = "streams"

POLL_SECONDS = 120
VIDEO_POLL_SECONDS = 300

_HTTP_HEADERS = {
    "User-Agent": "Cheterin-Bot/1.0 (+https://github.com/Nanda070/Cheterin_Bot_Dashboard)",
    "Accept": "application/json, application/xml, text/xml, text/html;q=0.9, */*;q=0.8",
}
_TIKTOK_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)
_TIKTOK_SEC_CH_UA = '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"'
_TIKTOK_BROWSER_HEADERS = {
    "User-Agent": _TIKTOK_CHROME_UA,
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Referer": "https://www.tiktok.com/",
    "sec-ch-ua": _TIKTOK_SEC_CH_UA,
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "Upgrade-Insecure-Requests": "1",
}
_TIKTOK_API_HEADERS = {
    "User-Agent": _TIKTOK_CHROME_UA,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Referer": "https://www.tiktok.com/",
    "Origin": "https://www.tiktok.com",
    "sec-ch-ua": _TIKTOK_SEC_CH_UA,
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
}

_TIKTOK_USER_RE = re.compile(r"^[A-Za-z0-9._]{2,24}$")
_TIKTOK_URL_USER_RE = re.compile(
    r"(?:https?://)?(?:www\.|vm\.|vt\.|m\.)?tiktok\.com/@([A-Za-z0-9._]{2,24})",
    re.I,
)
_DEFAULT_TIKTOK_RSS = "https://rsshub.app/tiktok/user/{username}"
# EU / WAF often returns a ~1KB "status eu: Internal Error" page instead of SIGI.
_TIKTOK_LIVE_HTML_MIN_OK = 8000
_TIKTOK_LIVE_FAIL_LOG_COOLDOWN = 1800.0
_TIKTOK_LIVE_HTML_HOSTS = (
    "https://www.tiktok.com",
    "https://m.tiktok.com",
)


def default_template(platform: str, lang: str) -> str:
    if platform == "youtube":
        return i18n.t("streams.default_template_youtube", lang)
    if platform == "tiktok_live":
        return i18n.t("streams.default_template_tiktok_live", lang)
    if platform == "tiktok":
        return i18n.t("streams.default_template_tiktok", lang)
    return i18n.t("streams.default_template_twitch", lang)


_LIVE_TITLE_STYLES = frozenset({"live_dot", "title_only", "live_badge"})


def tiktok_template(sub: dict, kind: str, lang: str) -> str:
    specific = str(sub.get(f"{kind}_template") or "").strip()
    if specific:
        return specific
    general = str(sub.get("template") or "").strip()
    if general:
        return general
    return default_template("tiktok_live" if kind == "live" else "tiktok", lang)


def tiktok_embed_color(sub: dict, kind: str) -> discord.Color:
    for key in (f"{kind}_embed_color", "embed_color"):
        raw = str(sub.get(key) or "").strip()
        if raw.startswith("#") and len(raw) == 7:
            try:
                return discord.Color(int(raw[1:], 16))
            except ValueError:
                pass
    return embed_style.TIKTOK_LIVE if kind == "live" else embed_style.TIKTOK


def tiktok_mention_everyone(sub: dict, kind: str) -> bool:
    key = f"{kind}_mention_everyone"
    if key in sub:
        return bool(sub[key])
    return bool(sub.get("mention_everyone", False))


def tiktok_use_embed(sub: dict, kind: str) -> bool:
    key = f"{kind}_use_embed"
    if key in sub:
        return bool(sub[key])
    return bool(sub.get("use_embed", True))


def tiktok_live_embed_title(sub: dict, title: str) -> str:
    style = sub.get("live_title_style") or "title_only"
    if style not in _LIVE_TITLE_STYLES:
        style = "live_dot"
    if style == "title_only":
        return title[:256]
    if style == "live_badge":
        return f"LIVE · {title}"[:256]
    return f"\U0001f534 LIVE · {title}"[:256]


def parse_tiktok_username(query: str) -> str | None:
    """@handle, unique id or profile URL → clean username, or None."""
    q = (query or "").strip()
    if not q:
        return None
    q = q.split("?")[0].split("#")[0].strip().rstrip("/")
    m = _TIKTOK_URL_USER_RE.search(q)
    if m:
        return m.group(1)
    q = re.sub(r"^https?://(?:www\.|vm\.|vt\.|m\.)?tiktok\.com/", "", q, flags=re.I)
    if "/" in q:
        parts = [p for p in q.split("/") if p]
        q = parts[0] if parts else q
    q = q.lstrip("@").strip().rstrip("/")
    if _TIKTOK_USER_RE.fullmatch(q):
        return q
    return None


def parse_tiktok_rss_xml(text: str) -> list[dict]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    items = []
    channel = root.find("channel")
    nodes = channel.findall("item") if channel is not None else root.findall(".//item")
    for item in nodes:
        link = (item.findtext("link") or "").strip()
        title = (item.findtext("title") or "").strip()
        desc = (item.findtext("description") or "").strip()
        video_id = ""
        m = re.search(r"/video/(\d+)", link)
        if m:
            video_id = m.group(1)
        enclosure = item.find("enclosure")
        cover = (enclosure.get("url") if enclosure is not None else "") or ""
        if not cover:
            media = item.find("{http://search.yahoo.com/mrss/}content")
            if media is not None:
                cover = media.get("url") or ""
        if not video_id and not link:
            continue
        items.append({
            "video_id": video_id or link,
            "title": title or desc,
            "url": link,
            "cover": cover,
            "vertical": True,
        })
    return items


def parse_tiktok_embed_html(text: str, username: str) -> dict | None:
    """Parse ``/embed/@user`` HTML for userInfo + videoList."""
    if not text:
        return None
    scripts = re.findall(
        r'<script[^>]*type=["\']application/json["\'][^>]*>(.*?)</script>',
        text,
        flags=re.I | re.S,
    )
    payload = None
    for raw in scripts:
        try:
            obj = json.loads(raw)
        except (TypeError, ValueError):
            continue
        if isinstance(obj, dict) and isinstance(obj.get("source"), dict):
            payload = obj
            break
    if payload is None:
        return None

    source_data = (payload.get("source") or {}).get("data") or {}
    if not isinstance(source_data, dict):
        return None
    key = f"/embed/@{username}"
    block = source_data.get(key)
    if not isinstance(block, dict):
        for cand_key, cand in source_data.items():
            if isinstance(cand, dict) and (
                str(cand_key).lower().endswith(f"@{username.lower()}")
                or (cand.get("userInfo") or {}).get("uniqueId", "").lower() == username.lower()
            ):
                block = cand
                break
    if not isinstance(block, dict):
        return None

    user = block.get("userInfo") or {}
    unique = str(user.get("uniqueId") or username).lstrip("@")
    display = str(user.get("nickname") or unique)
    avatar = ""
    for av_key in ("avatarUri", "avatarLarger", "avatarMedium", "avatarThumb", "avatar"):
        val = user.get(av_key)
        if isinstance(val, str) and val.startswith("http"):
            avatar = val
            break
        if isinstance(val, list) and val and isinstance(val[0], str):
            avatar = val[0]
            break

    entries = []
    for vid in block.get("videoList") or []:
        if not isinstance(vid, dict):
            continue
        vid_id = str(vid.get("id") or "")
        if not vid_id:
            continue
        author_unique = str(vid.get("authorUniqueId") or unique).lstrip("@")
        entries.append({
            "video_id": vid_id,
            "title": str(vid.get("desc") or ""),
            "url": f"https://www.tiktok.com/@{author_unique}/video/{vid_id}",
            "cover": str(vid.get("coverUrl") or vid.get("originCoverUrl") or vid.get("dynamicCoverUrl") or ""),
            "vertical": True,
            "create_time": int(vid.get("createTime") or 0),
        })
    return {
        "identifier": unique,
        "display_name": display,
        "avatar_url": avatar,
        "entries": entries,
    }


def _sort_tiktok_entries(entries: list[dict]) -> list[dict]:
    return sorted(entries, key=lambda e: e.get("create_time") or 0, reverse=True)


_TIKTOK_LIVE_ACTIVE = frozenset({2, 4, "2", "4"})


def _tiktok_first(*values):
    for value in values:
        if value is not None and value != "":
            return value
    return None


def _tiktok_cover_url(cover_raw) -> str:
    if isinstance(cover_raw, dict):
        urls = cover_raw.get("url_list") or cover_raw.get("urlList") or []
        return str(urls[0] if urls else cover_raw.get("url") or "")
    if isinstance(cover_raw, str):
        return cover_raw
    return ""


def _tiktok_avatar_url(user: dict) -> str:
    if not isinstance(user, dict):
        return ""
    for key in ("avatarLarger", "avatarMedium", "avatarThumb", "avatarUri", "avatar"):
        val = user.get(key)
        if isinstance(val, str) and val.startswith("http"):
            return val
        url = _tiktok_cover_url(val)
        if url:
            return url
    return ""


def _tiktok_cover_looks_small(url: str) -> bool:
    if not url:
        return True
    lowered = url.lower()
    if "shrink" in lowered or "resize" in lowered:
        return True
    if "tplv-tiktok" in lowered and "origin" not in lowered:
        return True
    for token in (":100:", ":200:", ":300:", "~c5", "100x100", "200x200"):
        if token in lowered:
            return True
    return False


def _tiktok_live_not_live() -> dict:
    return {
        "is_live": False,
        "room_id": "",
        "title": "",
        "cover": "",
        "cover_url": "",
        "avatar_url": "",
        "viewer_count": None,
    }


def _extract_tiktok_live_json(html: str) -> dict | None:
    """Load SIGI_STATE (preferred) or nested live payload from universal rehydration data."""
    for script_id in ("SIGI_STATE", "__UNIVERSAL_DATA_FOR_REHYDRATION__"):
        match = re.search(
            rf'<script id="{re.escape(script_id)}"[^>]*>(.*?)</script>',
            html,
            flags=re.S,
        )
        if not match:
            continue
        try:
            obj = json.loads(match.group(1))
        except (TypeError, ValueError):
            continue
        if not isinstance(obj, dict):
            continue
        if script_id == "SIGI_STATE" or obj.get("LiveRoom"):
            return obj
        scope = obj.get("__DEFAULT_SCOPE__") or {}
        if isinstance(scope, dict):
            for value in scope.values():
                if isinstance(value, dict) and value.get("LiveRoom"):
                    return value
    return None


def _parse_tiktok_live_payload(obj: dict) -> dict:
    live_room = obj.get("LiveRoom") or {}
    current = obj.get("CurrentRoom") or {}
    room_info = current.get("roomInfo") or {}
    live_user = live_room.get("liveRoomUserInfo") or {}
    nested_live = live_user.get("liveRoom") or {}
    user = live_user.get("user") or {}

    room_id = str(
        _tiktok_first(
            current.get("roomId"),
            room_info.get("id"),
            nested_live.get("roomId"),
            nested_live.get("id"),
            user.get("roomId"),
        )
        or ""
    ).strip()

    # Nested liveRoom/user status is authoritative; envelope liveRoomStatus is often 0 on /live.
    status = _tiktok_first(
        nested_live.get("status"),
        user.get("status"),
        room_info.get("status"),
        live_room.get("liveRoomStatus"),
    )

    is_live = status in _TIKTOK_LIVE_ACTIVE
    if not is_live and room_id and status not in (0, "0", None, ""):
        is_live = True

    if not is_live:
        return _tiktok_live_not_live()

    title = str(
        _tiktok_first(nested_live.get("title"), room_info.get("title"), user.get("title"))
        or ""
    )
    cover = _tiktok_cover_url(
        _tiktok_first(
            nested_live.get("cover"),
            nested_live.get("cover_url"),
            nested_live.get("streamCover"),
            nested_live.get("stream_cover"),
            room_info.get("cover"),
            room_info.get("cover_url"),
            room_info.get("streamCover"),
            room_info.get("stream_cover"),
        )
    )
    avatar_url = _tiktok_avatar_url(user)
    if not avatar_url:
        avatar_url = _tiktok_cover_url(
            _tiktok_first(
                nested_live.get("ownerAvatar"),
                nested_live.get("owner_avatar"),
                room_info.get("ownerAvatar"),
            )
        )

    room_stats = nested_live.get("liveRoomStats") or {}
    user_stats = live_user.get("stats") or {}
    viewer_count = _tiktok_first(
        room_stats.get("userCount"),
        user_stats.get("userCount"),
        user_stats.get("viewerCount"),
        room_info.get("user_count"),
    )
    try:
        viewers = int(viewer_count) if viewer_count is not None else None
    except (TypeError, ValueError):
        viewers = None

    return {
        "is_live": True,
        "room_id": room_id or f"live-{int(time.time())}",
        "title": title,
        "cover": cover,
        "cover_url": cover,
        "avatar_url": avatar_url,
        "viewer_count": viewers,
    }


def parse_tiktok_live_sigi(html: str) -> dict | None:
    """Parse ``/@user/live`` HTML (SIGI_STATE / universal JSON, browser UA required)."""
    if not html:
        return None
    payload = _extract_tiktok_live_json(html)
    if payload is None:
        return None
    return _parse_tiktok_live_payload(payload)


def _tiktok_html_looks_blocked(html: str) -> bool:
    """True when TikTok returned a tiny error/WAF page instead of a live rehydrate shell."""
    if not html:
        return True
    lowered = html.lower()
    if "status eu" in lowered or "internal error" in lowered:
        return True
    if len(html) < _TIKTOK_LIVE_HTML_MIN_OK:
        has_json = "SIGI_STATE" in html or "__UNIVERSAL_DATA_FOR_REHYDRATION__" in html
        return not has_json
    return False


def parse_tiktok_api_live_room(payload: dict) -> dict | None:
    """Parse ``/api-live/user/room`` JSON into the same shape as ``parse_tiktok_live_sigi``."""
    if not isinstance(payload, dict):
        return None
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    user = data.get("user") if isinstance(data.get("user"), dict) else {}
    live_room = data.get("liveRoom") if isinstance(data.get("liveRoom"), dict) else {}
    if not user and not live_room:
        return None

    room_id = str(
        _tiktok_first(user.get("roomId"), live_room.get("roomId"), live_room.get("roomID")) or ""
    ).strip()
    status = _tiktok_first(live_room.get("status"), user.get("status"))
    is_live = status in _TIKTOK_LIVE_ACTIVE
    if not is_live and room_id and live_room.get("streamData"):
        is_live = True
    if not is_live:
        return _tiktok_live_not_live()

    title = str(live_room.get("title") or user.get("title") or "")
    cover = _tiktok_cover_url(
        _tiktok_first(live_room.get("coverUrl"), live_room.get("squareCoverImg"), live_room.get("cover"))
    )
    avatar_url = _tiktok_avatar_url(user)
    room_stats = live_room.get("liveRoomStats") if isinstance(live_room.get("liveRoomStats"), dict) else {}
    viewer_count = _tiktok_first(room_stats.get("userCount"), room_stats.get("enterCount"))
    try:
        viewers = int(viewer_count) if viewer_count is not None else None
    except (TypeError, ValueError):
        viewers = None

    return {
        "is_live": True,
        "room_id": room_id or f"live-{int(time.time())}",
        "title": title,
        "cover": cover,
        "cover_url": cover,
        "avatar_url": avatar_url,
        "viewer_count": viewers,
    }


def parse_tiktok_webcast_by_user(payload: dict) -> dict | None:
    """Parse webcast ``room/info_by_user`` — useful when HTML is blocked; 30003 = offline."""
    if not isinstance(payload, dict):
        return None
    code = payload.get("status_code", payload.get("statusCode"))
    if code in (30003, "30003"):
        return _tiktok_live_not_live()
    data = payload.get("data")
    if not isinstance(data, dict):
        return None
    if data.get("message") in ("room has finished", "user is not living"):
        return _tiktok_live_not_live()

    room = data.get("room") if isinstance(data.get("room"), dict) else data
    owner = room.get("owner") if isinstance(room.get("owner"), dict) else {}
    room_id = str(_tiktok_first(room.get("id"), room.get("room_id"), room.get("roomId")) or "").strip()
    status = _tiktok_first(room.get("status"), data.get("status"))
    is_live = status in _TIKTOK_LIVE_ACTIVE
    if not is_live and room_id and status not in (0, "0", None, ""):
        is_live = True
    if not is_live:
        # Ambiguous payload without a clear live signal — let caller try other sources.
        if code not in (0, "0", None):
            return None
        return _tiktok_live_not_live()

    title = str(room.get("title") or "")
    cover = _tiktok_cover_url(_tiktok_first(room.get("cover"), room.get("cover_url")))
    avatar_url = _tiktok_avatar_url(owner)
    viewer_count = _tiktok_first(
        room.get("user_count"),
        room.get("userCount"),
        (room.get("stats") or {}).get("user_count") if isinstance(room.get("stats"), dict) else None,
    )
    try:
        viewers = int(viewer_count) if viewer_count is not None else None
    except (TypeError, ValueError):
        viewers = None

    return {
        "is_live": True,
        "room_id": room_id or f"live-{int(time.time())}",
        "title": title,
        "cover": cover,
        "cover_url": cover,
        "avatar_url": avatar_url,
        "viewer_count": viewers,
    }


def _normalized(data: dict) -> dict:
    data.setdefault("seq", 0)
    data.setdefault("subscriptions", [])
    return data


def get_subscriptions(guild_id: int) -> list[dict]:
    result = []
    for sub in _normalized(settings_db.get(guild_id, MODULE_NAME))["subscriptions"]:
        result.append({
            "id": str(sub.get("id") or ""),
            "platform": sub.get("platform") or "twitch",
            "identifier": str(sub.get("identifier") or ""),
            "display_name": str(sub.get("display_name") or ""),
            "avatar_url": str(sub.get("avatar_url") or ""),
            "enabled": bool(sub.get("enabled", True)),
            "channel_id": str(sub.get("channel_id") or ""),
            "ping_role_id": str(sub.get("ping_role_id") or ""),
            "template": str(sub.get("template") or ""),
            "keywords": [str(k) for k in sub.get("keywords", [])],
            "keyword_mode": sub.get("keyword_mode") or "any",
            "min_interval_minutes": int(sub.get("min_interval_minutes", 0)),
            "mention_everyone": bool(sub.get("mention_everyone", False)),
            "use_embed": bool(sub.get("use_embed", True)),
            "embed_color": str(sub.get("embed_color") or ""),
            "video_template": str(sub.get("video_template") or ""),
            "live_template": str(sub.get("live_template") or ""),
            "video_embed_color": str(sub.get("video_embed_color") or ""),
            "live_embed_color": str(sub.get("live_embed_color") or ""),
            "video_mention_everyone": bool(sub.get("video_mention_everyone", sub.get("mention_everyone", False))),
            "live_mention_everyone": bool(sub.get("live_mention_everyone", sub.get("mention_everyone", False))),
            "video_use_embed": bool(sub.get("video_use_embed", sub.get("use_embed", True))),
            "live_use_embed": bool(sub.get("live_use_embed", sub.get("use_embed", True))),
            "live_title_style": str(sub.get("live_title_style") or "title_only"),
            "last_notified_ts": int(sub.get("last_notified_ts", 0)),
            "last_stream_id": str(sub.get("last_stream_id") or ""),
            "last_live_room_id": str(sub.get("last_live_room_id") or ""),
        })
    return result


def add_subscription(guild_id: int, sub: dict) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    data["seq"] += 1
    sub = {**sub, "id": str(data["seq"])}
    data["subscriptions"].append(sub)
    settings_db.put(guild_id, MODULE_NAME, data)
    return sub


def update_subscription(guild_id: int, sub_id: str, **fields) -> dict | None:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    for sub in data["subscriptions"]:
        if str(sub.get("id")) == str(sub_id):
            sub.update(fields)
            settings_db.put(guild_id, MODULE_NAME, data)
            return sub
    return None


def delete_subscription(guild_id: int, sub_id: str) -> bool:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    before = len(data["subscriptions"])
    data["subscriptions"] = [s for s in data["subscriptions"] if str(s.get("id")) != str(sub_id)]
    if len(data["subscriptions"]) != before:
        settings_db.put(guild_id, MODULE_NAME, data)
        return True
    return False


def keywords_match(title: str, keywords: list[str], mode: str) -> bool:
    if not keywords:
        return True
    lowered = title.lower()
    hits = [k for k in keywords if k.lower() in lowered]
    return bool(hits) if mode == "any" else len(hits) == len(keywords)


def render_template(template: str, channel_name: str, stream_title: str, game: str, url: str, lang: str) -> str:
    replacements = {
        "{{channel}}": channel_name,
        "{{stream}}": stream_title,
        "{{game}}": game or i18n.t("streams.game_unknown", lang),
        "{{channel.url}}": url,
    }
    text = template
    for key, value in replacements.items():
        text = text.replace(key, value)
    return text.strip()


def resolve_template(sub: dict, lang: str, platform: str, *, tiktok_kind: str | None = None) -> str:
    if platform == "tiktok":
        return tiktok_template(sub, tiktok_kind or "video", lang)
    raw = str(sub.get("template") or "").strip()
    return raw or default_template(platform, lang)


def card_title(platform: str, name: str, lang: str, *, tiktok_kind: str | None = None) -> str:
    clean = components_v2.v2_plain_text(name)
    if platform == "youtube":
        key = "streams.card.title_youtube"
    elif platform == "tiktok" and tiktok_kind == "live":
        key = "streams.card.title_tiktok_live"
    elif platform == "tiktok":
        key = "streams.card.title_tiktok"
    else:
        key = "streams.card.title_twitch"
    return i18n.t(key, lang, name=clean)


def _video_view(watch_url: str, channel_url: str | None, lang: str) -> discord.ui.View:
    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        style=discord.ButtonStyle.link,
        label=i18n.t("streams.btn.watch_video", lang),
        url=watch_url,
    ))
    if channel_url:
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.link,
            label=i18n.t("streams.btn.tiktok", lang),
            url=channel_url,
        ))
    return view


def _live_view(live_url: str, channel_url: str | None, lang: str) -> discord.ui.View:
    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        style=discord.ButtonStyle.link,
        label=i18n.t("streams.btn.watch_live", lang),
        url=live_url,
    ))
    if channel_url:
        view.add_item(discord.ui.Button(
            style=discord.ButtonStyle.link,
            label=i18n.t("streams.btn.tiktok", lang),
            url=channel_url,
        ))
    return view


def _watch_view(url: str, lang: str, *, live: bool) -> discord.ui.View:
    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        style=discord.ButtonStyle.link,
        label=i18n.t("streams.btn.watch_live" if live else "streams.btn.watch_video", lang),
        url=url,
    ))
    return view


class Streams(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._twitch_token: str | None = None
        self._twitch_token_expires = 0
        self._last_video_poll = 0.0
        self._tiktok_live_fail_log: dict[str, float] = {}
        self._poll.start()

    def cog_unload(self):
        self._poll.cancel()

    @property
    def http(self) -> aiohttp.ClientSession:
        if not hasattr(self, "_http") or self._http.closed:
            self._http = aiohttp.ClientSession(headers=_HTTP_HEADERS)
        return self._http

    async def cog_unload_session(self):
        if hasattr(self, "_http") and not self._http.closed:
            await self._http.close()

    # ────────────────── Twitch API ──────────────────

    def twitch_configured(self) -> bool:
        return bool(os.getenv("TWITCH_CLIENT_ID") and os.getenv("TWITCH_CLIENT_SECRET"))

    async def _twitch_get_token(self) -> str | None:
        if not self.twitch_configured():
            return None
        if self._twitch_token and time.time() < self._twitch_token_expires - 60:
            return self._twitch_token

        try:
            async with self.http.post(
                "https://id.twitch.tv/oauth2/token",
                data={
                    "client_id": os.getenv("TWITCH_CLIENT_ID"),
                    "client_secret": os.getenv("TWITCH_CLIENT_SECRET"),
                    "grant_type": "client_credentials",
                },
            ) as resp:
                if resp.status != 200:
                    logger.warning("Twitch token request failed: %s", resp.status)
                    return None
                body = await resp.json()
                self._twitch_token = body["access_token"]
                self._twitch_token_expires = time.time() + int(body.get("expires_in", 3600))
                return self._twitch_token
        except aiohttp.ClientError as exc:
            logger.warning("Twitch token request error: %s", exc)
            return None

    async def _twitch_api(self, path: str, params) -> dict | None:
        token = await self._twitch_get_token()
        if token is None:
            return None
        headers = {"Client-ID": os.getenv("TWITCH_CLIENT_ID"), "Authorization": f"Bearer {token}"}
        try:
            async with self.http.get(f"https://api.twitch.tv/helix/{path}", params=params, headers=headers) as resp:
                if resp.status != 200:
                    logger.warning("Twitch API %s failed: %s", path, resp.status)
                    return None
                return await resp.json()
        except aiohttp.ClientError as exc:
            logger.warning("Twitch API error: %s", exc)
            return None

    async def resolve_twitch(self, query: str) -> dict | None:
        """Логин или ссылка -> {identifier, display_name, avatar_url} или None."""
        login = query.strip().rstrip("/").split("/")[-1].lstrip("@").lower()
        if not re.fullmatch(r"[a-z0-9_]{3,25}", login):
            return None
        body = await self._twitch_api("users", {"login": login})
        if not body or not body.get("data"):
            return None
        user = body["data"][0]
        return {
            "identifier": user["login"],
            "display_name": user["display_name"],
            "avatar_url": user.get("profile_image_url", ""),
        }

    # ────────────────── YouTube ──────────────────

    async def resolve_youtube(self, query: str) -> dict | None:
        """UC-id, ссылка на канал или @handle -> данные канала."""
        query = query.strip()
        channel_id = None

        match = re.search(r"(UC[0-9A-Za-z_-]{22})", query)
        if match:
            channel_id = match.group(1)
        else:
            handle = query.rstrip("/").split("/")[-1]
            if not handle.startswith("@"):
                handle = "@" + handle
            try:
                async with self.http.get(f"https://www.youtube.com/{handle}") as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        m = re.search(r'"channelId":"(UC[0-9A-Za-z_-]{22})"', html)
                        if m:
                            channel_id = m.group(1)
            except aiohttp.ClientError:
                pass

        if not channel_id:
            return None

        feed = await self._youtube_feed(channel_id)
        if feed is None:
            return None
        return {
            "identifier": channel_id,
            "display_name": feed["channel_name"] or channel_id,
            "avatar_url": "",
        }

    async def _youtube_feed(self, channel_id: str) -> dict | None:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        try:
            async with self.http.get(url) as resp:
                if resp.status != 200:
                    return None
                text = await resp.text()
        except aiohttp.ClientError:
            return None

        try:
            root = ET.fromstring(text)
        except ET.ParseError:
            return None

        ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
        channel_name = (root.findtext("a:title", namespaces=ns) or "").strip()
        entries = []
        for entry in root.findall("a:entry", ns):
            video_id = entry.findtext("yt:videoId", namespaces=ns)
            title = (entry.findtext("a:title", namespaces=ns) or "").strip()
            if video_id:
                entries.append({"video_id": video_id, "title": title})
        return {"channel_name": channel_name, "entries": entries}

    # ────────────────── TikTok ──────────────────

    async def _tiktok_get(self, url: str, *, browser: bool = False) -> tuple[int, str]:
        headers = _TIKTOK_BROWSER_HEADERS if browser else _HTTP_HEADERS
        try:
            async with self.http.get(url, headers=headers) as resp:
                return resp.status, await resp.text()
        except aiohttp.ClientError as exc:
            logger.warning("TikTok GET %s error: %s", url, exc)
            return 0, ""

    async def _tiktok_get_json(self, url: str, *, headers: dict | None = None) -> tuple[int, dict | None]:
        req_headers = headers or _TIKTOK_API_HEADERS
        try:
            async with self.http.get(url, headers=req_headers) as resp:
                if resp.status != 200:
                    return resp.status, None
                body = await resp.json(content_type=None)
                return resp.status, body if isinstance(body, dict) else None
        except (aiohttp.ClientError, ValueError) as exc:
            logger.debug("TikTok JSON GET %s error: %s", url, exc)
            return 0, None

    def _log_tiktok_live_fail(self, username: str, message: str, *args) -> None:
        """Warn once per account, then debug until cooldown elapses (avoids poll spam)."""
        key = username.lower()
        now = time.time()
        last = self._tiktok_live_fail_log.get(key, 0.0)
        if now - last >= _TIKTOK_LIVE_FAIL_LOG_COOLDOWN:
            self._tiktok_live_fail_log[key] = now
            logger.warning(message, *args)
        else:
            logger.debug(message, *args)

    def _clear_tiktok_live_fail(self, username: str) -> None:
        self._tiktok_live_fail_log.pop(username.lower(), None)

    async def seed_tiktok_subscription(self, guild_id: int, sub_id: str, username: str) -> None:
        """Seed last video / live ids so only future events notify."""
        fields: dict[str, str] = {}
        feed = await self._tiktok_feed(username)
        if feed and feed.get("entries"):
            fields["last_stream_id"] = str(feed["entries"][0]["video_id"])
        live = await self._tiktok_live_status(username)
        if live and live.get("is_live") and live.get("room_id"):
            fields["last_live_room_id"] = str(live["room_id"])
        if fields:
            update_subscription(guild_id, sub_id, **fields)

    async def resolve_tiktok(self, query: str) -> dict | None:
        username = parse_tiktok_username(query)
        if not username:
            return None

        info = await self._tiktok_oembed_profile(username)
        if info:
            return info

        info = await self._tiktok_user_info(username)
        if info:
            return info

        embed = await self._tiktok_embed_page(username)
        if embed:
            return {
                "identifier": embed.get("identifier") or username,
                "display_name": embed.get("display_name") or username,
                "avatar_url": embed.get("avatar_url") or "",
            }

        feed = await self._tiktok_feed(username)
        if feed is None:
            return None
        return {
            "identifier": username,
            "display_name": feed.get("display_name") or username,
            "avatar_url": feed.get("avatar_url") or "",
        }

    async def _tiktok_oembed_profile(self, username: str) -> dict | None:
        profile_url = f"https://www.tiktok.com/@{username}"
        try:
            async with self.http.get(
                "https://www.tiktok.com/oembed",
                params={"url": profile_url},
            ) as resp:
                if resp.status == 400:
                    return None
                if resp.status != 200:
                    logger.warning("TikTok oEmbed profile failed: %s", resp.status)
                    return None
                body = await resp.json(content_type=None)
        except (aiohttp.ClientError, ValueError) as exc:
            logger.warning("TikTok oEmbed profile error: %s", exc)
            return None
        if not isinstance(body, dict):
            return None
        unique = str(body.get("embed_product_id") or username).lstrip("@")
        if not unique or not _TIKTOK_USER_RE.fullmatch(unique):
            unique = username
        return {
            "identifier": unique,
            "display_name": str(body.get("author_name") or unique),
            "avatar_url": str(body.get("thumbnail_url") or ""),
        }

    async def _tiktok_user_info(self, username: str) -> dict | None:
        url = f"https://www.tikwm.com/api/user/info?unique_id={username}"
        try:
            async with self.http.get(url) as resp:
                if resp.status != 200:
                    return None
                body = await resp.json(content_type=None)
        except (aiohttp.ClientError, ValueError):
            return None
        if not isinstance(body, dict):
            return None
        if body.get("code") not in (0, "0", None):
            if body.get("data") in (None, {}, []):
                return None
        data = body.get("data") or {}
        if not isinstance(data, dict):
            return None
        user = data.get("user") or data
        if not isinstance(user, dict):
            return None
        unique = str(user.get("uniqueId") or user.get("unique_id") or "").lstrip("@")
        if not unique:
            return None
        return {
            "identifier": unique,
            "display_name": str(user.get("nickname") or unique),
            "avatar_url": str(
                user.get("avatarLarger") or user.get("avatarThumb") or user.get("avatar") or ""
            ),
        }

    async def _tiktok_embed_page(self, username: str) -> dict | None:
        status, text = await self._tiktok_get(f"https://www.tiktok.com/embed/@{username}")
        if status != 200:
            logger.warning("TikTok embed page failed: %s", status)
            return None
        parsed = parse_tiktok_embed_html(text, username)
        if parsed and parsed.get("entries"):
            parsed["entries"] = _sort_tiktok_entries(parsed["entries"])
        return parsed

    async def _tiktok_feed(self, username: str) -> dict | None:
        embed = await self._tiktok_embed_page(username)
        if embed is not None and embed.get("entries"):
            return {
                "display_name": embed.get("display_name") or username,
                "avatar_url": embed.get("avatar_url") or "",
                "entries": embed["entries"],
            }
        posts = await self._tiktok_tikwm_posts(username)
        if posts is not None:
            return posts
        return await self._tiktok_rsshub_feed(username)

    async def _tiktok_live_status(self, username: str) -> dict | None:
        """LIVE status via /@user/live HTML, then api-live / webcast JSON fallbacks."""
        html_errors: list[str] = []
        for host in _TIKTOK_LIVE_HTML_HOSTS:
            url = f"{host}/@{username}/live"
            status, text = await self._tiktok_get(url, browser=True)
            if status != 200:
                html_errors.append(f"{host} HTTP {status}")
                continue
            if not text:
                html_errors.append(f"{host} empty")
                continue
            if _tiktok_html_looks_blocked(text):
                html_errors.append(f"{host} blocked/tiny html={len(text)}")
                continue
            parsed = parse_tiktok_live_sigi(text)
            if parsed is not None:
                self._clear_tiktok_live_fail(username)
                if parsed.get("is_live"):
                    logger.info(
                        "TikTok live detected @%s room=%s viewers=%s via html",
                        username,
                        parsed.get("room_id"),
                        parsed.get("viewer_count"),
                    )
                return parsed
            has_sigi = "SIGI_STATE" in text or "__UNIVERSAL_DATA_FOR_REHYDRATION__" in text
            html_errors.append(f"{host} parse fail html={len(text)} json_script={has_sigi}")

        api_url = (
            "https://www.tiktok.com/api-live/user/room/"
            f"?aid=1988&sourceType=54&uniqueId={username}"
        )
        api_status, api_body = await self._tiktok_get_json(api_url)
        if api_body is not None:
            parsed = parse_tiktok_api_live_room(api_body)
            if parsed is not None:
                self._clear_tiktok_live_fail(username)
                if parsed.get("is_live"):
                    logger.info(
                        "TikTok live detected @%s room=%s viewers=%s via api-live",
                        username,
                        parsed.get("room_id"),
                        parsed.get("viewer_count"),
                    )
                return parsed
        elif api_status:
            html_errors.append(f"api-live HTTP {api_status}")

        webcast_url = (
            "https://webcast.tiktok.com/webcast/room/info_by_user/"
            f"?aid=1988&unique_id={username}"
        )
        wc_status, wc_body = await self._tiktok_get_json(
            webcast_url,
            headers={**_TIKTOK_API_HEADERS, "sec-fetch-site": "same-site"},
        )
        if wc_body is not None:
            parsed = parse_tiktok_webcast_by_user(wc_body)
            if parsed is not None:
                self._clear_tiktok_live_fail(username)
                if parsed.get("is_live"):
                    logger.info(
                        "TikTok live detected @%s room=%s viewers=%s via webcast",
                        username,
                        parsed.get("room_id"),
                        parsed.get("viewer_count"),
                    )
                return parsed
        elif wc_status:
            html_errors.append(f"webcast HTTP {wc_status}")

        detail = "; ".join(html_errors) if html_errors else "all sources failed"
        self._log_tiktok_live_fail(
            username,
            "TikTok live parse failed @%s (%s)",
            username,
            detail,
        )
        return _tiktok_live_not_live()

    async def _tiktok_tikwm_posts(self, username: str) -> dict | None:
        url = f"https://www.tikwm.com/api/user/posts?unique_id={username}&count=10"
        try:
            async with self.http.get(url) as resp:
                if resp.status != 200:
                    return None
                body = await resp.json(content_type=None)
        except (aiohttp.ClientError, ValueError):
            return None
        if not isinstance(body, dict):
            return None
        if body.get("code") not in (0, "0", None) and not (body.get("data") or {}).get("videos"):
            return None
        data = body.get("data") or {}
        videos = data.get("videos") or []
        if not videos:
            return None
        entries = []
        for vid in videos:
            vid_id = str(vid.get("video_id") or vid.get("id") or "")
            if not vid_id:
                continue
            author = vid.get("author") or {}
            author_unique = str(author.get("unique_id") or username).lstrip("@")
            entries.append({
                "video_id": vid_id,
                "title": str(vid.get("title") or ""),
                "url": f"https://www.tiktok.com/@{author_unique}/video/{vid_id}",
                "cover": str(vid.get("cover") or vid.get("origin_cover") or ""),
                "vertical": True,
                "create_time": int(vid.get("create_time") or 0),
            })
        if not entries:
            return None
        entries.sort(key=lambda e: e.get("create_time") or 0, reverse=True)
        author0 = (videos[0].get("author") if videos else {}) or {}
        return {
            "display_name": str(author0.get("nickname") or username),
            "avatar_url": str(author0.get("avatar") or ""),
            "entries": entries,
        }

    async def _tiktok_rsshub_feed(self, username: str) -> dict | None:
        template = (os.getenv("TIKTOK_RSS_TEMPLATE") or _DEFAULT_TIKTOK_RSS).strip()
        url = template.replace("{username}", username)
        try:
            async with self.http.get(url) as resp:
                if resp.status != 200:
                    logger.warning("TikTok RSSHub failed: %s", resp.status)
                    return None
                text = await resp.text()
        except aiohttp.ClientError as exc:
            logger.warning("TikTok RSSHub error: %s", exc)
            return None
        entries = parse_tiktok_rss_xml(text)
        if not entries:
            return None
        return {"display_name": username, "avatar_url": "", "entries": entries}

    async def _tiktok_video_cover(self, username: str, video_id: str, cover: str) -> str:
        """Prefer full cover from embed videoList; oEmbed thumbnail is fallback only."""
        if cover and not _tiktok_cover_looks_small(cover):
            return cover
        embed = await self._tiktok_embed_page(username)
        if embed:
            for entry in embed.get("entries") or []:
                if str(entry.get("video_id") or "") != str(video_id):
                    continue
                full = str(entry.get("cover") or "")
                if full and not _tiktok_cover_looks_small(full):
                    return full
                if full:
                    cover = cover or full
        if cover and not _tiktok_cover_looks_small(cover):
            return cover
        watch = f"https://www.tiktok.com/@{username}/video/{video_id}"
        oembed = await self._tiktok_oembed(watch)
        return str(oembed.get("thumbnail") or cover or "")

    async def _tiktok_oembed(self, video_url: str) -> dict:
        try:
            async with self.http.get(
                "https://www.tiktok.com/oembed",
                params={"url": video_url},
            ) as resp:
                if resp.status != 200:
                    return {}
                body = await resp.json(content_type=None)
        except (aiohttp.ClientError, ValueError):
            return {}
        if not isinstance(body, dict):
            return {}
        return {
            "title": str(body.get("title") or ""),
            "thumbnail": str(body.get("thumbnail_url") or ""),
            "author": str(body.get("author_name") or ""),
        }

    # ────────────────── Поллер ──────────────────

    @tasks.loop(seconds=POLL_SECONDS)
    async def _poll(self):
        try:
            now = time.time()
            poll_videos = now - self._last_video_poll >= VIDEO_POLL_SECONDS
            if poll_videos:
                self._last_video_poll = now
            for guild in self.bot.guilds:
                try:
                    subs = [s for s in get_subscriptions(guild.id) if s["enabled"] and s["channel_id"]]
                    if not subs:
                        continue

                    twitch_subs = [s for s in subs if s["platform"] == "twitch"]
                    youtube_subs = [s for s in subs if s["platform"] == "youtube"]
                    tiktok_subs = [s for s in subs if s["platform"] == "tiktok"]

                    if twitch_subs:
                        await self._poll_twitch(guild.id, twitch_subs)
                    if tiktok_subs:
                        for sub in tiktok_subs:
                            await self._poll_tiktok_live_one(guild.id, sub)
                    if poll_videos:
                        for sub in youtube_subs:
                            await self._poll_youtube_one(guild.id, sub)
                        for sub in tiktok_subs:
                            await self._poll_tiktok_video_one(guild.id, sub)
                except Exception as exc:
                    logger.exception("_poll guild=%s", guild.id)
                    cog = self.bot.get_cog("OwnerAlertsCog")
                    if cog:
                        cog.report_module_error(guild.id, "streams", str(exc))
        except Exception:
            logger.exception("_poll: ошибка итерации — цикл продолжает работать")

    @_poll.error
    async def _poll_error(self, _error: BaseException):
        logger.exception("_poll: критическая ошибка — перезапуск цикла")
        self._poll.restart()

    @_poll.before_loop
    async def _before_poll(self):
        await self.bot.wait_until_ready()

    async def _poll_twitch(self, guild_id: int, subs: list[dict]):
        lang = i18n.lang_for(guild_id)
        logins = list({s["identifier"] for s in subs})
        body = await self._twitch_api("streams", [("user_login", l) for l in logins[:100]])
        if body is None:
            return
        live = {s["user_login"].lower(): s for s in body.get("data", [])}

        for sub in subs:
            stream = live.get(sub["identifier"].lower())
            if stream is None:
                continue
            stream_id = str(stream["id"])
            if stream_id == sub["last_stream_id"]:
                continue
            if not keywords_match(stream.get("title", ""), sub["keywords"], sub["keyword_mode"]):
                update_subscription(guild_id, sub["id"], last_stream_id=stream_id)
                continue
            now = int(time.time())
            if sub["min_interval_minutes"] and now - sub["last_notified_ts"] < sub["min_interval_minutes"] * 60:
                update_subscription(guild_id, sub["id"], last_stream_id=stream_id)
                continue

            url = f"https://www.twitch.tv/{sub['identifier']}"
            name = stream.get("user_name") or sub["display_name"]
            title = components_v2.v2_plain_text(stream.get("title") or i18n.t("streams.embed.stream_title", lang))
            game = components_v2.v2_plain_text(stream.get("game_name") or "")
            template = resolve_template(sub, lang, "twitch")
            content = render_template(template, name, title, game, url, lang)

            embed = discord.Embed(
                title=card_title("twitch", name, lang),
                description=title,
                color=embed_style.TWITCH,
                timestamp=discord.utils.utcnow(),
            )
            if stream.get("viewer_count") is not None:
                embed.add_field(
                    name=i18n.t("streams.embed.viewers", lang),
                    value=str(stream["viewer_count"]),
                    inline=True,
                )
            if game:
                embed.add_field(name=i18n.t("streams.embed.game", lang), value=game, inline=True)
            thumb = (stream.get("thumbnail_url") or "").replace("{width}", "640").replace("{height}", "360")
            if thumb:
                embed.set_image(url=f"{thumb}?t={int(time.time())}")

            await self._announce(sub, content, embed, view=_watch_view(url, lang, live=True))
            update_subscription(guild_id, sub["id"], last_stream_id=stream_id, last_notified_ts=now)

    async def _should_skip_video(self, guild_id: int, sub: dict, video_id: str, title: str) -> bool:
        if video_id == sub["last_stream_id"]:
            return True
        if not sub["last_stream_id"]:
            update_subscription(guild_id, sub["id"], last_stream_id=video_id)
            return True
        if not keywords_match(title, sub["keywords"], sub["keyword_mode"]):
            update_subscription(guild_id, sub["id"], last_stream_id=video_id)
            return True
        now = int(time.time())
        if sub["min_interval_minutes"] and now - sub["last_notified_ts"] < sub["min_interval_minutes"] * 60:
            update_subscription(guild_id, sub["id"], last_stream_id=video_id)
            return True
        return False

    async def _poll_youtube_one(self, guild_id: int, sub: dict):
        lang = i18n.lang_for(guild_id)
        feed = await self._youtube_feed(sub["identifier"])
        if feed is None or not feed["entries"]:
            logger.debug("YouTube feed empty for %s", sub["identifier"])
            return
        latest = feed["entries"][0]
        if await self._should_skip_video(guild_id, sub, latest["video_id"], latest["title"]):
            return

        url = f"https://www.youtube.com/watch?v={latest['video_id']}"
        channel_name = feed["channel_name"] or sub["display_name"]
        title = components_v2.v2_plain_text(latest["title"])
        template = resolve_template(sub, lang, "youtube")
        content = render_template(template, channel_name, title, "", url, lang)

        embed = discord.Embed(
            title=card_title("youtube", channel_name, lang),
            description=title,
            color=embed_style.YOUTUBE,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_image(url=f"https://i.ytimg.com/vi/{latest['video_id']}/hqdefault.jpg")

        await self._announce(sub, content, embed, view=_watch_view(url, lang, live=False))
        update_subscription(guild_id, sub["id"], last_stream_id=latest["video_id"], last_notified_ts=int(time.time()))

    async def _poll_tiktok_live_one(self, guild_id: int, sub: dict):
        lang = i18n.lang_for(guild_id)
        live = await self._tiktok_live_status(sub["identifier"])
        if live is None:
            return
        if not live.get("is_live"):
            return

        room_id = str(live.get("room_id") or "")
        if not room_id:
            return
        if room_id == sub.get("last_live_room_id"):
            return

        title = live.get("title") or i18n.t("streams.embed.live_title", lang)
        if not keywords_match(title, sub["keywords"], sub["keyword_mode"]):
            update_subscription(guild_id, sub["id"], last_live_room_id=room_id)
            return

        now = int(time.time())
        if sub["min_interval_minutes"] and now - sub["last_notified_ts"] < sub["min_interval_minutes"] * 60:
            update_subscription(guild_id, sub["id"], last_live_room_id=room_id)
            return

        content, embed, view = self._build_tiktok_live_announce(sub, live, lang)
        await self._announce(sub, content, embed, view=view, tiktok_kind="live")
        update_subscription(
            guild_id,
            sub["id"],
            last_live_room_id=room_id,
            last_notified_ts=now,
        )

    async def _poll_tiktok_video_one(self, guild_id: int, sub: dict):
        lang = i18n.lang_for(guild_id)
        feed = await self._tiktok_feed(sub["identifier"])
        if feed is None or not feed.get("entries"):
            logger.warning("TikTok video feed empty for @%s (sub %s)", sub["identifier"], sub["id"])
            return
        latest = feed["entries"][0]
        video_id = str(latest.get("video_id") or "")
        if not video_id:
            return
        if await self._should_skip_video(guild_id, sub, video_id, latest.get("title") or ""):
            return

        content, embed, view = await self._build_tiktok_video_announce(sub, feed, latest, lang)
        await self._announce(sub, content, embed, view=view, tiktok_kind="video")
        update_subscription(guild_id, sub["id"], last_stream_id=video_id, last_notified_ts=int(time.time()))

    def _build_tiktok_live_announce(
        self,
        sub: dict,
        live: dict,
        lang: str,
    ) -> tuple[str, discord.Embed, discord.ui.View]:
        channel_name = sub.get("display_name") or sub["identifier"]
        live_url = f"https://www.tiktok.com/@{sub['identifier']}/live"
        channel_url = f"https://www.tiktok.com/@{sub['identifier']}"
        title = components_v2.v2_plain_text(live.get("title") or i18n.t("streams.embed.live_title", lang))
        template = tiktok_template(sub, "live", lang)
        content = render_template(template, channel_name, title, "", live_url, lang)

        cover = live.get("cover_url") or live.get("cover") or ""

        embed = discord.Embed(
            title=card_title("tiktok", channel_name, lang, tiktok_kind="live"),
            description=title,
            color=tiktok_embed_color(sub, "live"),
            timestamp=discord.utils.utcnow(),
        )
        if live.get("viewer_count") is not None:
            embed.add_field(
                name=i18n.t("streams.embed.viewers", lang),
                value=str(live["viewer_count"]),
                inline=True,
            )
        if cover:
            embed.set_image(url=cover)
        return content, embed, _live_view(live_url, channel_url, lang)

    async def _build_tiktok_video_announce(
        self,
        sub: dict,
        feed: dict,
        latest: dict,
        lang: str,
    ) -> tuple[str, discord.Embed, discord.ui.View]:
        video_id = str(latest.get("video_id") or "")
        watch = latest.get("url") or f"https://www.tiktok.com/@{sub['identifier']}/video/{video_id}"
        channel_url = f"https://www.tiktok.com/@{sub['identifier']}"
        title = latest.get("title") or ""
        cover = await self._tiktok_video_cover(sub["identifier"], video_id, latest.get("cover") or "")
        if not title:
            oembed = await self._tiktok_oembed(watch)
            title = oembed.get("title") or ""
        title = components_v2.v2_plain_text(title)

        channel_name = feed.get("display_name") or sub.get("display_name") or sub["identifier"]
        template = tiktok_template(sub, "video", lang)
        content = render_template(template, channel_name, title, "", watch, lang)

        embed = discord.Embed(
            title=card_title("tiktok", channel_name, lang, tiktok_kind="video"),
            description=title[:4096] if title else i18n.t("streams.embed.stream_title", lang),
            color=tiktok_embed_color(sub, "video"),
            timestamp=discord.utils.utcnow(),
        )
        if cover:
            embed.set_image(url=cover)
        return content, embed, _video_view(watch, channel_url, lang)

    async def _announce(
        self,
        sub: dict,
        content: str,
        embed: discord.Embed,
        view: discord.ui.View | None = None,
        *,
        tiktok_kind: str | None = None,
    ) -> bool:
        channel = self.bot.get_channel(int(sub["channel_id"]))
        if channel is None:
            return False
        if sub.get("platform") == "tiktok" and tiktok_kind in ("live", "video"):
            embed.color = tiktok_embed_color(sub, tiktok_kind)
            mention_everyone = tiktok_mention_everyone(sub, tiktok_kind)
            use_embed = tiktok_use_embed(sub, tiktok_kind)
        else:
            raw_color = (sub.get("embed_color") or "").strip()
            if raw_color.startswith("#") and len(raw_color) == 7:
                try:
                    embed.color = discord.Color(int(raw_color[1:], 16))
                except ValueError:
                    pass
            mention_everyone = bool(sub.get("mention_everyone", False))
            use_embed = bool(sub.get("use_embed", True))

        mentions = []
        allowed_roles = []
        allowed_everyone = False
        if sub.get("ping_role_id"):
            mentions.append(f"<@&{sub['ping_role_id']}>")
            allowed_roles.append(discord.Object(id=int(sub["ping_role_id"])))
        if mention_everyone:
            mentions.append("@everyone")
            allowed_everyone = True
        if mentions:
            content = "\n".join(mentions) + ("\n" + content if content else "")
            allowed = discord.AllowedMentions(roles=allowed_roles, everyone=allowed_everyone)
        else:
            allowed = discord.AllowedMentions.none()
        try:
            await components_v2.send_message(
                channel,
                version=components_v2.VERSION_V2,
                content=content or None,
                embed=embed if use_embed else None,
                view=view,
                allowed_mentions=allowed,
                detach_layout=True,
                stream_card=True,
            )
            return True
        except discord.HTTPException as exc:
            logger.warning("Не удалось отправить стрим-уведомление %s: %s", sub["id"], exc)
            return False

    async def send_test_announce(self, guild_id: int, sub: dict) -> str | None:
        """Send a sample notification without updating last_stream_id. Returns error code or None."""
        if not sub.get("channel_id"):
            return "channel_required"
        if self.bot.get_channel(int(sub["channel_id"])) is None:
            return "channel_not_found"
        lang = i18n.lang_for(guild_id)
        display = sub.get("display_name") or sub.get("identifier") or "stream"
        platform = sub.get("platform") or "twitch"
        title = i18n.t("streams.test.sample_title", lang)
        if platform == "youtube":
            url = f"https://www.youtube.com/channel/{sub.get('identifier', '')}"
            template = resolve_template(sub, lang, "youtube")
            content = render_template(template, display, title, "", url, lang)
            embed = discord.Embed(
                title=card_title("youtube", display, lang),
                description=title,
                color=embed_style.YOUTUBE,
                timestamp=discord.utils.utcnow(),
            )
            embed.set_footer(text=i18n.t("streams.test.footer", lang))
            view = _watch_view(url, lang, live=False)
            if not await self._announce(sub, content, embed, view=view):
                return "send_failed"
            return None
        if platform == "tiktok":
            ident = sub.get("identifier") or "tiktok"
            url = f"https://www.tiktok.com/@{ident}"
            template = resolve_template(sub, lang, "tiktok", tiktok_kind="video")
            content = render_template(template, display, title, "", url, lang)
            embed = discord.Embed(
                title=card_title("tiktok", display, lang, tiktok_kind="video"),
                description=title,
                color=tiktok_embed_color(sub, "video"),
                timestamp=discord.utils.utcnow(),
            )
            embed.set_footer(text=i18n.t("streams.test.footer", lang))
            view = _video_view(url, url, lang)
            if not await self._announce(sub, content, embed, view=view, tiktok_kind="video"):
                return "send_failed"
            return None

        url = f"https://www.twitch.tv/{sub.get('identifier', '')}"
        game = i18n.t("streams.test.sample_game", lang)
        template = resolve_template(sub, lang, "twitch")
        content = render_template(template, display, title, game, url, lang)
        embed = discord.Embed(
            title=card_title("twitch", display, lang),
            description=title,
            color=embed_style.TWITCH,
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name=i18n.t("streams.embed.viewers", lang), value="42", inline=True)
        embed.add_field(name=i18n.t("streams.embed.game", lang), value=game, inline=True)
        embed.set_footer(text=i18n.t("streams.test.footer", lang))
        view = _watch_view(url, lang, live=True)
        if not await self._announce(sub, content, embed, view=view):
            return "send_failed"
        return None


async def setup(bot: commands.Bot):
    await bot.add_cog(Streams(bot))
