"""Banner + server icon rotation cog."""

from __future__ import annotations

import logging
import time

import discord
from discord.ext import commands, tasks

import banner_rotation_core
import i18n
import settings_db

logger = logging.getLogger("cheterin.banner_rotation")


class BannerRotationCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
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

    async def _maybe_rotate(self, guild_id: int, now: int) -> None:
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

        # Nothing queued — still advance so we do not busy-loop.
        want_banner = bool(cfg["banner_enabled"] and cfg["banners"])
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

        if want_banner:
            img = banner_rotation_core.pick_next_image(cfg["banners"], cfg["last_banner_id"])
            if img is not None:
                path = banner_rotation_core.get_image_path(guild_id, "banner", img["id"])
                if path is not None:
                    raw = path.read_bytes()
                    try:
                        await guild.edit(banner=raw, reason="Banner rotation")
                        banner_rotation_core.mark_rotated(guild_id, "banner", img["id"], interval)
                        did_rotate = True
                        logger.info(
                            i18n.t(
                                "banner_rotation.rotated_banner",
                                lang,
                                name=img.get("original_name", ""),
                            ),
                        )
                        if log_channel:
                            await self._try_log(
                                log_channel,
                                i18n.t(
                                    "banner_rotation.log_banner",
                                    lang,
                                    name=img.get("original_name", ""),
                                ),
                            )
                    except discord.Forbidden:
                        logger.warning(
                            i18n.t("banner_rotation.forbidden_banner", lang, guild=guild.name),
                        )
                        if log_channel:
                            await self._try_log(
                                log_channel,
                                i18n.t("banner_rotation.log_forbidden_banner", lang),
                            )
                    except discord.HTTPException as exc:
                        logger.warning(
                            i18n.t("banner_rotation.http_error", lang, error=str(exc)),
                        )

        if want_icon:
            cfg2 = banner_rotation_core.get_settings(guild_id)
            img = banner_rotation_core.pick_next_image(cfg2["icons"], cfg2["last_icon_id"])
            if img is not None:
                path = banner_rotation_core.get_image_path(guild_id, "icon", img["id"])
                if path is not None:
                    raw = path.read_bytes()
                    try:
                        await guild.edit(icon=raw, reason="Icon rotation")
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
                    except discord.Forbidden:
                        logger.warning(
                            i18n.t("banner_rotation.forbidden_icon", lang, guild=guild.name),
                        )
                        if log_channel:
                            await self._try_log(
                                log_channel,
                                i18n.t("banner_rotation.log_forbidden_icon", lang),
                            )
                    except discord.HTTPException as exc:
                        logger.warning(
                            i18n.t("banner_rotation.http_error", lang, error=str(exc)),
                        )

        if not did_rotate:
            self._advance_next_run(guild_id, interval, now)

    async def _try_log(self, channel: discord.abc.Messageable, text: str) -> None:
        try:
            await channel.send(text)
        except Exception:
            pass

    async def rotate_now(self, guild_id: int) -> bool:
        """Force immediate rotation (called from dashboard route)."""
        data = settings_db.get(guild_id, banner_rotation_core.MODULE_NAME)
        data["next_run_at"] = 0
        settings_db.put(guild_id, banner_rotation_core.MODULE_NAME, data)
        try:
            await self._maybe_rotate(guild_id, int(time.time()))
            return True
        except Exception:
            logger.exception("banner_rotation: rotate_now failed for guild=%s", guild_id)
            return False


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BannerRotationCog(bot))
