import logging

import bot.core.settings_db as settings_db
import discord
from discord.ext import commands

import bot.core.embed_style as embed_style
import bot.config as bot_config
import bot.core.i18n as i18n
import bot.modules.community.invites_core as invites_core
import bot.modules.community.sticky_roles_core as sticky_roles_core
import bot.modules.community.welcome_core as welcome_core

logger = logging.getLogger("welcome")


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cached_invites: dict[int, list[discord.Invite]] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        sticky_roles_core.init()
        for guild in self.bot.guilds:
            try:
                self.cached_invites[guild.id] = await guild.invites()
            except discord.Forbidden:
                self.cached_invites[guild.id] = []

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        self.cached_invites.setdefault(invite.guild.id, []).append(invite)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        self.cached_invites[invite.guild.id] = [
            item for item in self.cached_invites.get(invite.guild.id, []) if item.code != invite.code
        ]

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        lang = i18n.lang_for(guild.id)
        try:
            new_invites = await guild.invites()
        except discord.Forbidden:
            new_invites = []

        old_invites = self.cached_invites.get(guild.id, [])
        used = None
        for new_inv in new_invites:
            for old_inv in old_invites:
                if new_inv.code == old_inv.code and new_inv.uses > old_inv.uses:
                    used = new_inv
                    break
            if used:
                break
        self.cached_invites[guild.id] = new_invites

        if bot_config.get(guild.id, "WELCOME_CHANNEL_ENABLED", True):
            welcome_ch_id = bot_config.get(guild.id, "WELCOME_CHANNEL_ID")
            if welcome_ch_id:
                welcome_ch = self.bot.get_channel(int(welcome_ch_id))
                if welcome_ch:
                    msg_settings = welcome_core.get_settings(guild.id)
                    payload = welcome_core.build_channel_payload(
                        msg_settings, member, guild, lang, bot_config.get
                    )
                    await welcome_ch.send(**payload)

        sticky_settings = sticky_roles_core.get_settings(guild.id)
        if sticky_settings["enabled"]:
            sticky_ids = sticky_roles_core.pop_snapshot(guild.id, member.id)
            if sticky_ids:
                roles_to_restore = []
                ignored = {int(x) for x in sticky_settings["ignored_role_ids"]}
                tracked = {int(x) for x in sticky_settings["tracked_role_ids"]}
                for rid in sticky_ids:
                    if rid in ignored:
                        continue
                    if tracked and rid not in tracked:
                        continue
                    role = guild.get_role(rid)
                    if role is None or role.is_default() or role.managed:
                        continue
                    me = guild.me
                    if me is not None and getattr(role, "position", 0) >= getattr(me.top_role, "position", 0):
                        continue
                    roles_to_restore.append(role)
                if roles_to_restore:
                    try:
                        await member.add_roles(
                            *roles_to_restore,
                            reason=i18n.t("welcome.sticky_roles_reason", lang),
                        )
                    except discord.Forbidden:
                        logger.warning("sticky roles restore forbidden guild=%s user=%s", guild.id, member.id)
                    except discord.HTTPException:
                        logger.exception("sticky roles restore failed guild=%s user=%s", guild.id, member.id)

        auto_role_ids = bot_config.get(guild.id, "AUTO_ROLE_IDS", [])
        if auto_role_ids:
            roles_to_add = [guild.get_role(int(rid)) for rid in auto_role_ids]
            roles_to_add = [r for r in roles_to_add if r is not None]
            if roles_to_add:
                try:
                    await member.add_roles(*roles_to_add, reason=i18n.t("welcome.auto_role_reason", lang))
                except discord.Forbidden:
                    pass

        if used and used.inviter:
            inviter_id = str(used.inviter.id)
            invites_data = settings_db.get(member.guild.id, "invites_stats", {})
            stats = invites_data.setdefault("stats", {})
            invite_history = invites_data.setdefault("invite_history", {})

            stats.setdefault(inviter_id, {"joins": 0, "leaves": 0, "invites": 0})
            stats[inviter_id]["joins"] += 1
            stats[inviter_id]["invites"] += 1
            invite_history[str(member.id)] = inviter_id

            settings_db.put(member.guild.id, "invites_stats", invites_data)

            # Если модуль Invites сам пишет лог — не дублируем embed из Welcome.
            inv_settings = invites_core.get_settings(guild.id)
            invites_logs = inv_settings["enabled"] and (
                bool(inv_settings["log_channel_id"]) or inv_settings["welcome_mention"]
            )
            if not invites_logs:
                embed_inv = discord.Embed(
                    title=i18n.t("welcome.invite_log_title", lang),
                    description=i18n.t(
                        "welcome.invite_log_body",
                        lang,
                        inviter=used.inviter.mention,
                        member=member.mention,
                        code=used.code,
                        invites=stats[inviter_id]["invites"],
                    ),
                    color=embed_style.INFO,
                    timestamp=self.bot.utcnow(),
                )
                inv_ch_id = bot_config.get(guild.id, "INVITE_LOG_CHANNEL_ID")
                if inv_ch_id:
                    inv_ch = self.bot.get_channel(int(inv_ch_id))
                    if inv_ch:
                        await inv_ch.send(embed=embed_inv)

        dm_sent = False
        if bot_config.get(guild.id, "WELCOME_DM_ENABLED", True):
            msg_settings = welcome_core.get_settings(guild.id)
            dm_payload = welcome_core.build_dm_payload(
                msg_settings, member, guild, lang, bot_config.get
            )
            try:
                await member.send(**{k: v for k, v in dm_payload.items() if v is not None})
                dm_sent = True
            except discord.Forbidden:
                dm_sent = False

        dm_log = discord.Embed(
            title=i18n.t("welcome.dm_log_title", lang),
            color=embed_style.SUCCESS if dm_sent else embed_style.DANGER,
            timestamp=self.bot.utcnow(),
        )
        dm_log.add_field(name=i18n.t("welcome.dm_log_user", lang), value=member.mention, inline=False)
        dm_log.add_field(
            name=i18n.t("welcome.dm_log_status", lang),
            value=i18n.t("welcome.dm_log_sent" if dm_sent else "welcome.dm_log_denied", lang),
            inline=False,
        )

        await self.bot.send_log(member.guild.id, dm_log)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        lang = i18n.lang_for(guild.id)
        mid = str(member.id)

        sticky_settings = sticky_roles_core.get_settings(guild.id)
        if sticky_settings["enabled"]:
            role_ids = sticky_roles_core.filter_member_roles(member, sticky_settings)
            if role_ids:
                sticky_roles_core.save_snapshot(guild.id, member.id, role_ids)

        invites_data = settings_db.get(guild.id, "invites_stats", {})
        stats = invites_data.setdefault("stats", {})
        invite_history = invites_data.setdefault("invite_history", {})

        if mid in invite_history:
            inv_id = invite_history.pop(mid)
            if inv_id in stats:
                stats[inv_id]["leaves"] += 1
                stats[inv_id]["invites"] = max(0, stats[inv_id].get("invites", 0) - 1)
            settings_db.put(guild.id, "invites_stats", invites_data)

        if bot_config.get(guild.id, "GOODBYE_CHANNEL_ENABLED", False):
            goodbye_ch_id = bot_config.get(guild.id, "GOODBYE_CHANNEL_ID") or bot_config.get(
                guild.id, "WELCOME_CHANNEL_ID"
            )
            if goodbye_ch_id:
                goodbye_ch = self.bot.get_channel(int(goodbye_ch_id))
                if goodbye_ch:
                    try:
                        msg_settings = welcome_core.get_settings(guild.id)
                        text = welcome_core.build_goodbye_text(msg_settings, member, guild, lang)
                        await goodbye_ch.send(text)
                    except discord.HTTPException:
                        pass

async def setup(bot):
    sticky_roles_core.init()
    cog = Welcome(bot)
    await bot.add_cog(cog)
