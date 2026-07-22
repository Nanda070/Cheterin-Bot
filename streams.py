"""Стрим-уведомления: Twitch и YouTube.

- Twitch: опрос Helix API (нужны TWITCH_CLIENT_ID / TWITCH_CLIENT_SECRET в .env).
  Уведомление при переходе канала в эфир.
- YouTube: опрос публичного RSS-фида канала. Уведомление о новом видео/премьере.

Подписки настраиваются в дашборде: канал публикации, роль для пинга, свой
шаблон, ключевые слова по названию, минимальный интервал между уведомлениями.
"""

import asyncio
import logging
import os
import re
import time
import xml.etree.ElementTree as ET

import aiohttp
import discord
from discord.ext import commands, tasks

import settings_db

import i18n

logger = logging.getLogger("streams")

MODULE_NAME = "streams"

POLL_SECONDS = 120


def default_template(platform: str, lang: str) -> str:
    if platform == "youtube":
        return i18n.t("streams.default_template_youtube", lang)
    return i18n.t("streams.default_template_twitch", lang)


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
            "last_notified_ts": int(sub.get("last_notified_ts", 0)),
            "last_stream_id": str(sub.get("last_stream_id") or ""),
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


class Streams(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._twitch_token: str | None = None
        self._twitch_token_expires = 0
        self._poll.start()

    def cog_unload(self):
        self._poll.cancel()

    @property
    def http(self) -> aiohttp.ClientSession:
        # Переиспользуем сессию бота, чтобы не плодить коннекторы
        if not hasattr(self, "_http") or self._http.closed:
            self._http = aiohttp.ClientSession()
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

    # ────────────────── Поллер ──────────────────

    @tasks.loop(seconds=POLL_SECONDS)
    async def _poll(self):
        # Всё тело под try/except: необработанное исключение навсегда остановило бы tasks.loop.
        try:
            for guild in self.bot.guilds:
                subs = [s for s in get_subscriptions(guild.id) if s["enabled"] and s["channel_id"]]
                if not subs:
                    continue

                twitch_subs = [s for s in subs if s["platform"] == "twitch"]
                youtube_subs = [s for s in subs if s["platform"] == "youtube"]

                if twitch_subs:
                    await self._poll_twitch(guild.id, twitch_subs)
                for sub in youtube_subs:
                    await self._poll_youtube_one(guild.id, sub)
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
            template = sub["template"] or default_template("twitch", lang)
            content = render_template(
                template,
                stream.get("user_name") or sub["display_name"],
                stream.get("title", ""),
                stream.get("game_name", ""),
                url,
                lang,
            )

            embed = discord.Embed(
                title=stream.get("title") or i18n.t("streams.embed.stream_title", lang),
                url=url,
                color=discord.Color.purple(),
                timestamp=discord.utils.utcnow(),
            )
            embed.set_author(
                name=i18n.t(
                    "streams.embed.author_twitch",
                    lang,
                    name=stream.get("user_name", sub["display_name"]),
                ),
                icon_url=sub["avatar_url"] or None,
            )
            if stream.get("game_name"):
                embed.add_field(name=i18n.t("streams.embed.game", lang), value=stream["game_name"], inline=True)
            if stream.get("viewer_count") is not None:
                embed.add_field(
                    name=i18n.t("streams.embed.viewers", lang),
                    value=str(stream["viewer_count"]),
                    inline=True,
                )
            thumb = (stream.get("thumbnail_url") or "").replace("{width}", "640").replace("{height}", "360")
            if thumb:
                embed.set_image(url=f"{thumb}?t={int(time.time())}")

            await self._announce(sub, content, embed)
            update_subscription(guild_id, sub["id"], last_stream_id=stream_id, last_notified_ts=now)

    async def _poll_youtube_one(self, guild_id: int, sub: dict):
        lang = i18n.lang_for(guild_id)
        feed = await self._youtube_feed(sub["identifier"])
        if feed is None or not feed["entries"]:
            return
        latest = feed["entries"][0]
        if latest["video_id"] == sub["last_stream_id"]:
            return
        if not sub["last_stream_id"]:
            # Первая проверка после добавления: запоминаем последнее видео без анонса
            update_subscription(guild_id, sub["id"], last_stream_id=latest["video_id"])
            return
        if not keywords_match(latest["title"], sub["keywords"], sub["keyword_mode"]):
            update_subscription(guild_id, sub["id"], last_stream_id=latest["video_id"])
            return
        now = int(time.time())
        if sub["min_interval_minutes"] and now - sub["last_notified_ts"] < sub["min_interval_minutes"] * 60:
            update_subscription(guild_id, sub["id"], last_stream_id=latest["video_id"])
            return

        url = f"https://www.youtube.com/watch?v={latest['video_id']}"
        template = sub["template"] or default_template("youtube", lang)
        channel_name = feed["channel_name"] or sub["display_name"]
        content = render_template(template, channel_name, latest["title"], "", url, lang)

        embed = discord.Embed(title=latest["title"], url=url, color=discord.Color.red(), timestamp=discord.utils.utcnow())
        embed.set_author(name=i18n.t("streams.embed.author_youtube", lang, name=channel_name))
        embed.set_image(url=f"https://i.ytimg.com/vi/{latest['video_id']}/hqdefault.jpg")

        await self._announce(sub, content, embed)
        update_subscription(guild_id, sub["id"], last_stream_id=latest["video_id"], last_notified_ts=now)

    async def _announce(self, sub: dict, content: str, embed: discord.Embed):
        channel = self.bot.get_channel(int(sub["channel_id"]))
        if channel is None:
            return
        if sub["ping_role_id"]:
            content = f"<@&{sub['ping_role_id']}>\n{content}"
            allowed = discord.AllowedMentions(roles=[discord.Object(id=int(sub["ping_role_id"]))])
        else:
            allowed = discord.AllowedMentions.none()
        try:
            await channel.send(content=content or None, embed=embed, allowed_mentions=allowed)
        except discord.HTTPException as exc:
            logger.warning("Не удалось отправить стрим-уведомление %s: %s", sub["id"], exc)


async def setup(bot: commands.Bot):
    await bot.add_cog(Streams(bot))
