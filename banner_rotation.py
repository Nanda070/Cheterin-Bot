"""Banner + server icon rotation cog (playlist + optional dynamic banner)."""

from __future__ import annotations

import logging
import time

import discord
from discord.ext import commands, tasks

import banner_rotation_core
import dynamic_banner
import i18n
import settings_db
import stats_db
from discord_banner_bytes import (
    classify_discord_asset_error,
    ensure_discord_banner_bytes,
    ensure_discord_icon_bytes,
    format_discord_http_error,
)

logger = logging.getLogger("cheterin.banner_rotation")


def _count_in_voice(guild: discord.Guild) -> int:
    total = 0
    for channel in guild.voice_channels:
        total += sum(1 for m in channel.members if not m.bot)
    for channel in getattr(guild, "stage_channels", ()) or ():
        total += sum(1 for m in channel.members if not m.bot)
    return total


class BannerRotationCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._last_error: dict | None = None
        self._rotation_loop.start()

    def cog_unload(self) -> None:
        self._rotation_loop.cancel()

    @tasks.loop(minutes=1)
    async def _rotation_loop(self) -> None:
        now = int(time.time())
        for guild in list(self.bot.guilds):
            try:
                await self._maybe_rotate(guild.id, now)
            except Exception:
                logger.exception("banner_rotation: unexpected error for guild=%s", guild.id)

    @_rotation_loop.before_loop
    async def _before_loop(self) -> None:
        await self.bot.wait_until_ready()

    def _advance_next_run(self, guild_id: int, interval_minutes: int, now: int | None = None) -> None:
        """Backoff so empty playlists / permission failures do not retry every minute."""
        ts = int(time.time()) if now is None else now
        data = settings_db.get(guild_id, banner_rotation_core.MODULE_NAME)
        data["next_run_at"] = ts + max(1, int(interval_minutes)) * 60
        settings_db.put(guild_id, banner_rotation_core.MODULE_NAME, data)

    async def _resolve_most_active(
        self, guild: discord.Guild
    ) -> tuple[str | None, bytes | None]:
        rows = stats_db.voice_leaderboard(guild.id, limit=5)
        for row in rows:
            if int(row["voice_seconds"] or 0) <= 0:
                continue
            user_id = int(row["user_id"])
            member = guild.get_member(user_id)
            if member is None:
                try:
                    member = await guild.fetch_member(user_id)
                except (discord.NotFound, discord.HTTPException):
                    continue
            if member.bot:
                continue
            avatar_bytes: bytes | None = None
            try:
                avatar_bytes = await member.display_avatar.replace(size=256).read()
            except (discord.HTTPException, OSError):
                avatar_bytes = None
            return member.display_name, avatar_bytes
        return None, None

    async def _build_dynamic_banner(self, guild: discord.Guild, lang: str) -> bytes:
        display_name, avatar_bytes = await self._resolve_most_active(guild)
        return dynamic_banner.render_dynamic_banner(
            display_name=display_name,
            avatar_bytes=avatar_bytes,
            member_count=guild.member_count or len(guild.members),
            voice_count=_count_in_voice(guild),
            guild_name=guild.name,
            lang=lang,
        )

    async def _apply_banner(
        self,
        guild: discord.Guild,
        raw: bytes,
        *,
        reason: str,
        log_name: str,
        lang: str,
        log_channel: discord.TextChannel | None,
        interval: int,
        image_id: str,
    ) -> bool:
        try:
            payload = ensure_discord_banner_bytes(raw)
        except Exception as exc:
            detail = {"status": None, "code": None, "text": f"image_encode_failed: {exc}"}
            self._last_error = {**detail, "reason": "invalid_image", "kind": "banner"}
            logger.warning("banner_rotation: banner encode failed guild=%s: %s", guild.id, exc, exc_info=True)
            if log_channel:
                await self._try_log(
                    log_channel,
                    i18n.t("banner_rotation.log_http_banner", lang, error=detail["text"]),
                )
            return False

        try:
            await guild.edit(banner=payload, reason=reason)
            banner_rotation_core.mark_rotated(guild.id, "banner", image_id, interval)
            logger.info(
                i18n.t("banner_rotation.rotated_banner", lang, name=log_name),
            )
            if log_channel:
                await self._try_log(
                    log_channel,
                    i18n.t("banner_rotation.log_banner", lang, name=log_name),
                )
            return True
        except discord.Forbidden as exc:
            detail = format_discord_http_error(exc)
            reason_code = classify_discord_asset_error(detail)
            self._last_error = {**detail, "reason": reason_code, "kind": "banner"}
            logger.warning(
                "banner_rotation: banner forbidden guild=%s status=%s code=%s text=%s",
                guild.id,
                detail.get("status"),
                detail.get("code"),
                detail.get("text"),
            )
            if log_channel:
                await self._try_log(
                    log_channel,
                    i18n.t(
                        "banner_rotation.log_http_banner",
                        lang,
                        error=f"{detail.get('text')} (HTTP {detail.get('status')}, code {detail.get('code')})",
                    ),
                )
        except discord.HTTPException as exc:
            detail = format_discord_http_error(exc)
            reason_code = classify_discord_asset_error(detail)
            self._last_error = {**detail, "reason": reason_code, "kind": "banner"}
            logger.warning(
                "banner_rotation: banner rejected guild=%s status=%s code=%s text=%s reason=%s",
                guild.id,
                detail.get("status"),
                detail.get("code"),
                detail.get("text"),
                reason_code,
            )
            if log_channel:
                await self._try_log(
                    log_channel,
                    i18n.t(
                        "banner_rotation.log_http_banner",
                        lang,
                        error=f"{detail.get('text')} (HTTP {detail.get('status')}, code {detail.get('code')})",
                    ),
                )
        except Exception as exc:
            detail = {"status": None, "code": None, "text": str(exc)[:500]}
            self._last_error = {**detail, "reason": "discord_rejected", "kind": "banner"}
            logger.warning("banner_rotation: banner unexpected error guild=%s: %s", guild.id, exc, exc_info=True)
        return False

    async def _maybe_rotate(self, guild_id: int, now: int) -> None:
        self._last_error = None
        cfg = banner_rotation_core.get_settings(guild_id)
        if not cfg["enabled"]:
            return
        next_run = cfg["next_run_at"]
        if next_run and now < next_run:
            return

        interval = cfg["interval_minutes"]
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            self._advance_next_run(guild_id, interval, now)
            return

        me = guild.me
        if me is None or not me.guild_permissions.manage_guild:
            self._advance_next_run(guild_id, interval, now)
            return

        banner_mode = cfg["banner_mode"]
        dynamic_banner_on = (
            bool(cfg["banner_enabled"]) and banner_mode == banner_rotation_core.BANNER_MODE_DYNAMIC
        )
        playlist_banner_on = (
            bool(cfg["banner_enabled"])
            and banner_mode == banner_rotation_core.BANNER_MODE_PLAYLIST
            and bool(cfg["banners"])
        )
        want_banner = dynamic_banner_on or playlist_banner_on
        want_icon = bool(cfg["icon_enabled"] and cfg["icons"])
        if not want_banner and not want_icon:
            self._advance_next_run(guild_id, interval, now)
            return

        lang = i18n.lang_for(guild_id)
        log_ch_id = cfg["log_channel_id"]
        log_channel = None
        if log_ch_id and log_ch_id.isdigit():
            ch = self.bot.get_channel(int(log_ch_id))
            if isinstance(ch, discord.TextChannel):
                log_channel = ch

        did_rotate = False

        if dynamic_banner_on:
            try:
                raw = await self._build_dynamic_banner(guild, lang)
            except Exception:
                logger.exception("banner_rotation: dynamic banner render failed guild=%s", guild_id)
                raw = None
            if raw:
                ok = await self._apply_banner(
                    guild,
                    raw,
                    reason="Dynamic banner",
                    log_name=i18n.t("banner_rotation.dynamic_name", lang),
                    lang=lang,
                    log_channel=log_channel,
                    interval=interval,
                    image_id="dynamic",
                )
                did_rotate = did_rotate or ok
        elif playlist_banner_on:
            img = banner_rotation_core.pick_next_image(cfg["banners"], cfg["last_banner_id"])
            if img is not None:
                path = banner_rotation_core.get_image_path(guild_id, "banner", img["id"])
                if path is not None:
                    raw = path.read_bytes()
                    ok = await self._apply_banner(
                        guild,
                        raw,
                        reason="Banner rotation",
                        log_name=img.get("original_name", ""),
                        lang=lang,
                        log_channel=log_channel,
                        interval=interval,
                        image_id=img["id"],
                    )
                    did_rotate = did_rotate or ok

        if want_icon:
            cfg2 = banner_rotation_core.get_settings(guild_id)
            img = banner_rotation_core.pick_next_image(cfg2["icons"], cfg2["last_icon_id"])
            if img is not None:
                path = banner_rotation_core.get_image_path(guild_id, "icon", img["id"])
                if path is not None:
                    raw = path.read_bytes()
                    try:
                        payload = ensure_discord_icon_bytes(raw)
                        await guild.edit(icon=payload, reason="Icon rotation")
                        banner_rotation_core.mark_rotated(guild_id, "icon", img["id"], interval)
                        did_rotate = True
                        logger.info(
                            i18n.t(
                                "banner_rotation.rotated_icon",
                                lang,
                                name=img.get("original_name", ""),
                            ),
                        )
                        if log_channel:
                            await self._try_log(
                                log_channel,
                                i18n.t(
                                    "banner_rotation.log_icon",
                                    lang,
                                    name=img.get("original_name", ""),
                                ),
                            )
                    except Exception as exc:
                        detail = format_discord_http_error(exc) if isinstance(exc, discord.HTTPException) else {
                            "status": None,
                            "code": None,
                            "text": str(exc)[:500],
                        }
                        reason_code = classify_discord_asset_error(detail)
                        self._last_error = {**detail, "reason": reason_code, "kind": "icon"}
                        logger.warning(
                            "banner_rotation: icon rejected guild=%s status=%s code=%s text=%s",
                            guild.id,
                            detail.get("status"),
                            detail.get("code"),
                            detail.get("text"),
                        )
                        if log_channel and isinstance(exc, discord.HTTPException):
                            await self._try_log(
                                log_channel,
                                i18n.t(
                                    "banner_rotation.log_http_banner",
                                    lang,
                                    error=f"{detail.get('text')} (HTTP {detail.get('status')})",
                                ),
                            )

        if not did_rotate:
            self._advance_next_run(guild_id, interval, now)

    async def _try_log(self, channel: discord.abc.Messageable, text: str) -> None:
        try:
            await channel.send(text)
        except Exception:
            pass

    async def rotate_now(self, guild_id: int) -> dict:
        """Force immediate rotation (called from dashboard route)."""
        self._last_error = None
        data = settings_db.get(guild_id, banner_rotation_core.MODULE_NAME)
        data["next_run_at"] = 0
        settings_db.put(guild_id, banner_rotation_core.MODULE_NAME, data)
        try:
            before = banner_rotation_core.get_settings(guild_id)
            before_banner_at = int(before.get("last_banner_at") or 0)
            before_icon_at = int(before.get("last_icon_at") or 0)
            await self._maybe_rotate(guild_id, int(time.time()))
            after = banner_rotation_core.get_settings(guild_id)
            rotated = (
                int(after.get("last_banner_at") or 0) > before_banner_at
                or int(after.get("last_icon_at") or 0) > before_icon_at
            )
            if rotated:
                return {"ok": True}
            err = self._last_error or {}
            if err:
                return {
                    "ok": False,
                    "error": err.get("reason") or "discord_rejected",
                    "discord_status": err.get("status"),
                    "discord_code": err.get("code"),
                    "discord_text": err.get("text"),
                    "kind": err.get("kind"),
                }
            return {"ok": False, "error": "nothing_to_rotate"}
        except Exception:
            logger.exception("banner_rotation: rotate_now failed for guild=%s", guild_id)
            return {"ok": False, "error": "internal_error"}


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BannerRotationCog(bot))
