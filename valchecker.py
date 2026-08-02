"""ValChecker cog — Valorant profile / match / tracking (port of ValChecker Node bot)."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import discord
from discord import app_commands
from discord.ext import commands, tasks

import i18n
import slash_i18n
import slash_registry
import valchecker_core
import valchecker_db
import valchecker_embeds as embeds
import valchecker_henrik as henrik
import valchecker_stats as stats
import valchecker_valorant_api as vap

logger = logging.getLogger("valchecker")

REGION_CHOICES = [
    slash_i18n.localized_choice("eu", "slash.val.region.eu"),
    slash_i18n.localized_choice("na", "slash.val.region.na"),
    slash_i18n.localized_choice("ap", "slash.val.region.ap"),
    slash_i18n.localized_choice("kr", "slash.val.region.kr"),
    slash_i18n.localized_choice("latam", "slash.val.region.latam"),
    slash_i18n.localized_choice("br", "slash.val.region.br"),
]


def _lang(guild_id: int | None) -> str:
    return i18n.lang_for(guild_id)


def _module_ok(guild_id: int | None) -> bool:
    if guild_id is None:
        return False
    return bool(valchecker_core.get_settings(guild_id)["enabled"])


async def _deny_disabled(interaction: discord.Interaction) -> bool:
    """Return True if denied (and reply sent)."""
    lang = _lang(interaction.guild_id)
    if interaction.guild_id is None:
        await interaction.response.send_message(
            i18n.t("valchecker.common.server_only_cmd", lang), ephemeral=True
        )
        return True
    if not _module_ok(interaction.guild_id):
        await interaction.response.send_message(
            i18n.module_disabled(lang, "valchecker"), ephemeral=True
        )
        return True
    return False


async def _deny_disabled_followup(interaction: discord.Interaction) -> bool:
    """Like _deny_disabled but for already-deferred / button interactions."""
    lang = _lang(interaction.guild_id)
    if interaction.guild_id is None or not _module_ok(interaction.guild_id):
        msg = (
            i18n.t("valchecker.common.server_only_cmd", lang)
            if interaction.guild_id is None
            else i18n.module_disabled(lang, "valchecker")
        )
        emb = embeds.error_embed(msg, lang)
        if interaction.response.is_done():
            await interaction.followup.send(embed=emb, ephemeral=True)
        else:
            await interaction.response.send_message(embed=emb, ephemeral=True)
        return True
    return False


# ── Setup panel ─────────────────────────────────────────────────────────────

class SetupLinkModal(discord.ui.Modal):
    def __init__(self, lang: str, user_id: int):
        super().__init__(title=i18n.t("valchecker.setup.modal_title", lang))
        self.lang = lang
        self.user_id = user_id
        self.riot_input = discord.ui.TextInput(
            label=i18n.t("valchecker.setup.modal_riot", lang),
            placeholder="Player#1234",
            required=True,
            max_length=40,
            custom_id="riot_id",
        )
        self.region_input = discord.ui.TextInput(
            label=i18n.t("valchecker.setup.modal_region", lang),
            placeholder="eu",
            required=False,
            max_length=8,
            custom_id="region",
        )
        self.add_item(self.riot_input)
        self.add_item(self.region_input)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.lang
        await interaction.response.defer(ephemeral=True)
        if await _deny_disabled_followup(interaction):
            return
        parsed = stats.parse_riot_id(self.riot_input.value)
        if not parsed:
            await interaction.followup.send(
                embed=embeds.error_embed(i18n.t("valchecker.setup.err_bad_riot", lang), lang),
                ephemeral=True,
            )
            return
        region_raw = (self.region_input.value or "").strip().lower()
        allowed = {c.value for c in REGION_CHOICES}
        try:
            acc = await henrik.account(parsed["name"], parsed["tag"])
            account = acc["data"]
            region = region_raw if region_raw in allowed else (account.get("region") or "eu")
            valchecker_db.link_user(
                discord_id=str(interaction.user.id),
                puuid=account["puuid"],
                name=account["name"],
                tag=account["tag"],
                region=region,
                platform="pc",
            )
            rank_line = ""
            try:
                mmr = stats.normalize_mmr(
                    await henrik.mmr_by_puuid(region, "pc", account["puuid"])
                )
                rank_line = f"\n**{mmr['rank']}**  ·  {mmr['rr']} RR"
            except Exception:
                pass
            await interaction.followup.send(
                embed=embeds.simple_embed(
                    i18n.t("valchecker.setup.linked_title", lang),
                    i18n.t(
                        "valchecker.setup.linked_desc",
                        lang,
                        id=stats.riot_id(account["name"], account["tag"]),
                        region=region.upper(),
                        rank=rank_line,
                    ),
                    embeds.COLORS["win"],
                ),
                ephemeral=True,
            )
            await interaction.followup.send(
                **build_setup_panel(interaction.user, lang),
                ephemeral=True,
            )
        except Exception as e:
            await interaction.followup.send(
                embed=embeds.error_embed(
                    henrik.friendly_error(e, lang) or i18n.t("valchecker.setup.err_failed_link", lang),
                    lang,
                ),
                ephemeral=True,
            )


class SetupView(discord.ui.View):
    def __init__(self, user_id: int, lang: str):
        super().__init__(timeout=1800)
        self.user_id = user_id
        self.lang = lang
        linked = valchecker_db.get_user(str(user_id))
        link_btn = discord.ui.Button(
            label=i18n.t("valchecker.setup.btn_relink" if linked else "valchecker.setup.btn_link", lang),
            style=discord.ButtonStyle.success,
            custom_id=f"vc:setup:link:{user_id}",
        )
        track_btn = discord.ui.Button(
            label=i18n.t(
                "valchecker.setup.btn_track_on" if linked and linked.get("track") else "valchecker.setup.btn_track_off",
                lang,
            ),
            style=discord.ButtonStyle.primary if linked and linked.get("track") else discord.ButtonStyle.secondary,
            custom_id=f"vc:setup:track:{user_id}",
            disabled=not linked,
        )
        unlink_btn = discord.ui.Button(
            label=i18n.t("valchecker.setup.btn_unlink", lang),
            style=discord.ButtonStyle.danger,
            custom_id=f"vc:setup:unlink:{user_id}",
            disabled=not linked,
        )
        link_btn.callback = self._link  # type: ignore[method-assign]
        track_btn.callback = self._track  # type: ignore[method-assign]
        unlink_btn.callback = self._unlink  # type: ignore[method-assign]
        self.add_item(link_btn)
        self.add_item(track_btn)
        self.add_item(unlink_btn)

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=embeds.error_embed(
                    i18n.t("valchecker.setup.err_not_yours", self.lang), self.lang
                ),
                ephemeral=True,
            )
            return False
        if await _deny_disabled(interaction):
            return False
        return True

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    async def _link(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        await interaction.response.send_modal(SetupLinkModal(self.lang, self.user_id))

    async def _track(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        user = valchecker_db.get_user(str(interaction.user.id))
        if not user:
            await interaction.response.send_message(
                embed=embeds.error_embed(i18n.t("valchecker.setup.err_link_first", self.lang), self.lang),
                ephemeral=True,
            )
            return
        next_on = not bool(user.get("track"))
        valchecker_db.set_tracking(str(interaction.user.id), next_on)
        await interaction.response.edit_message(**build_setup_panel(interaction.user, self.lang))
        await interaction.followup.send(
            embed=embeds.simple_embed(
                i18n.t("valchecker.setup.track_on_title" if next_on else "valchecker.setup.track_off_title", self.lang),
                (
                    i18n.t(
                        "valchecker.setup.track_on_desc",
                        self.lang,
                        id=stats.riot_id(user["name"], user["tag"]),
                    )
                    if next_on
                    else i18n.t("valchecker.setup.track_off_desc", self.lang)
                ),
                embeds.COLORS["win"] if next_on else embeds.COLORS["soft"],
            ),
            ephemeral=True,
        )

    async def _unlink(self, interaction: discord.Interaction):
        if not await self._guard(interaction):
            return
        user = valchecker_db.get_user(str(interaction.user.id))
        if not user:
            await interaction.response.send_message(
                embed=embeds.error_embed(i18n.t("valchecker.setup.err_no_linked", self.lang), self.lang),
                ephemeral=True,
            )
            return
        valchecker_db.unlink_user(str(interaction.user.id))
        await interaction.response.edit_message(**build_setup_panel(interaction.user, self.lang))
        await interaction.followup.send(
            embed=embeds.simple_embed(
                i18n.t("valchecker.setup.unlinked_title", self.lang),
                i18n.t(
                    "valchecker.setup.unlinked_desc",
                    self.lang,
                    id=stats.riot_id(user["name"], user["tag"]),
                ),
                embeds.COLORS["soft"],
            ),
            ephemeral=True,
        )


def build_setup_panel(discord_user: discord.abc.User, lang: str) -> dict:
    linked = valchecker_db.get_user(str(discord_user.id))
    embed = embeds.base_embed(color=embeds.COLORS["dark"])
    avatar = getattr(discord_user, "display_avatar", None)
    embed.set_author(
        name=getattr(discord_user, "display_name", None) or discord_user.name,
        icon_url=getattr(avatar, "url", None),
    )
    embed.title = i18n.t("valchecker.setup.title", lang)
    if linked:
        embed.description = "\n".join([
            f"{i18n.t('valchecker.setup.linked', lang)}  ·  **{stats.riot_id(linked['name'], linked['tag'])}**",
            f"{i18n.t('valchecker.setup.region', lang)}  ·  **{linked['region'].upper()}**",
            f"{i18n.t('valchecker.setup.tracking', lang)}  ·  **{i18n.t('valchecker.common.on' if linked.get('track') else 'valchecker.common.off', lang)}**",
            "",
            i18n.t("valchecker.setup.hint_linked", lang),
        ])
    else:
        embed.description = "\n".join([
            i18n.t("valchecker.setup.hint_empty", lang),
            "",
            i18n.t("valchecker.setup.hint_link", lang),
            i18n.t("valchecker.setup.hint_track", lang),
            i18n.t("valchecker.setup.hint_unlink", lang),
        ])
    embed.set_footer(text=f"ValChecker · {i18n.t('valchecker.setup.footer', lang)}")
    return {"embeds": [embed], "view": SetupView(discord_user.id, lang)}


# ── Nav panels ──────────────────────────────────────────────────────────────

class ProfileNavView(discord.ui.View):
    def __init__(self, session_id: str, active: str, lang: str):
        super().__init__(timeout=1800)
        self.session_id = session_id
        self.lang = lang
        for view, key in (
            ("overview", "valchecker.nav.overview"),
            ("stats", "valchecker.nav.stats"),
            ("agents", "valchecker.nav.agents"),
            ("maps", "valchecker.nav.maps"),
        ):
            btn = discord.ui.Button(
                label=i18n.t(key, lang),
                style=discord.ButtonStyle.primary if active == view else discord.ButtonStyle.secondary,
                custom_id=f"vc:nav:profile:{view}:{session_id}",
            )
            btn.callback = self._make_cb(view)  # type: ignore[method-assign]
            self.add_item(btn)

    def _make_cb(self, view: str):
        async def cb(interaction: discord.Interaction):
            await self._nav(interaction, view)
        return cb

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    async def _nav(self, interaction: discord.Interaction, view: str):
        session = stats.get_session(self.session_id)
        lang = self.lang
        if not session:
            await interaction.response.send_message(
                embed=embeds.error_embed(i18n.t("valchecker.nav.err_expired", lang), lang),
                ephemeral=True,
            )
            return
        if session.get("ownerId") != interaction.user.id:
            await interaction.response.send_message(
                embed=embeds.error_embed(i18n.t("valchecker.nav.err_not_yours", lang), lang),
                ephemeral=True,
            )
            return
        if await _deny_disabled(interaction):
            return
        await interaction.response.defer()
        try:
            payload = await load_profile_payload(session, view)
            await interaction.edit_original_response(
                embeds=payload["embeds"],
                view=ProfileNavView(self.session_id, view, lang),
            )
        except Exception as e:
            await interaction.followup.send(
                embed=embeds.error_embed(
                    henrik.friendly_error(e, lang) or i18n.t("valchecker.nav.err_update", lang),
                    lang,
                ),
                ephemeral=True,
            )


class MatchNavView(discord.ui.View):
    def __init__(self, session_id: str, active: str, history_count: int, lang: str):
        super().__init__(timeout=1800)
        self.session_id = session_id
        self.lang = lang
        latest = discord.ui.Button(
            label=i18n.t("valchecker.nav.latest", lang),
            style=discord.ButtonStyle.primary if active == "latest" else discord.ButtonStyle.secondary,
            custom_id=f"vc:nav:match:latest:{session_id}",
        )
        history = discord.ui.Button(
            label=i18n.t("valchecker.nav.history", lang),
            style=discord.ButtonStyle.primary if active == "history" else discord.ButtonStyle.secondary,
            custom_id=f"vc:nav:match:history:{session_id}",
        )
        more = discord.ui.Button(
            label="+5",
            style=discord.ButtonStyle.success,
            custom_id=f"vc:nav:match:more:{session_id}",
            disabled=active != "history" or history_count >= 15,
        )
        latest.callback = self._make_cb("latest")  # type: ignore[method-assign]
        history.callback = self._make_cb("history")  # type: ignore[method-assign]
        more.callback = self._make_cb("more")  # type: ignore[method-assign]
        self.add_item(latest)
        self.add_item(history)
        self.add_item(more)

    def _make_cb(self, action: str):
        async def cb(interaction: discord.Interaction):
            await self._nav(interaction, action)
        return cb

    async def on_timeout(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True

    async def _nav(self, interaction: discord.Interaction, action: str):
        session = stats.get_session(self.session_id)
        lang = self.lang
        if not session:
            await interaction.response.send_message(
                embed=embeds.error_embed(i18n.t("valchecker.nav.err_expired", lang), lang),
                ephemeral=True,
            )
            return
        if session.get("ownerId") != interaction.user.id:
            await interaction.response.send_message(
                embed=embeds.error_embed(i18n.t("valchecker.nav.err_not_yours", lang), lang),
                ephemeral=True,
            )
            return
        if await _deny_disabled(interaction):
            return
        await interaction.response.defer()
        try:
            view = action
            if action == "more":
                view = "history"
                stats.update_session(
                    self.session_id,
                    {"count": min(15, (session.get("count") or 5) + 5), "view": "history"},
                )
            else:
                stats.update_session(self.session_id, {"view": view})
            fresh = stats.get_session(self.session_id)
            payload = await load_match_payload(fresh, view)
            await interaction.edit_original_response(
                embeds=payload["embeds"],
                view=MatchNavView(self.session_id, view, (fresh or {}).get("count") or 5, lang),
            )
        except Exception as e:
            await interaction.followup.send(
                embed=embeds.error_embed(
                    henrik.friendly_error(e, lang) or i18n.t("valchecker.nav.err_update", lang),
                    lang,
                ),
                ephemeral=True,
            )


async def load_profile_payload(session: dict, view: str) -> dict:
    lang = session.get("locale") or "en"
    player = {
        "puuid": session["puuid"],
        "name": session["name"],
        "tag": session["tag"],
        "region": session["region"],
        "platform": "pc",
    }
    count = session.get("count") or 10

    mmr_raw, acc_raw, matches_raw = await asyncio.gather(
        henrik.mmr_by_puuid(player["region"], "pc", player["puuid"]),
        henrik.account_by_puuid(player["puuid"]),
        henrik.matches_by_puuid(player["region"], "pc", player["puuid"], size=count),
        return_exceptions=True,
    )
    mmr_body = mmr_raw if isinstance(mmr_raw, dict) else {}
    acc_body = acc_raw if isinstance(acc_raw, dict) else None
    matches_body = matches_raw if isinstance(matches_raw, dict) else {}

    mmr = stats.normalize_mmr(mmr_body or {})
    account = (acc_body or {}).get("data") if acc_body else None
    if mmr.get("account"):
        player["name"] = mmr["account"].get("name", player["name"])
        player["tag"] = mmr["account"].get("tag", player["tag"])
        session["name"] = player["name"]
        session["tag"] = player["tag"]

    summaries = stats.summaries_from_matches(
        matches_body.get("data"), player["puuid"], player["name"], player["tag"]
    )
    for s in summaries:
        row = stats.to_cache_row(s, player["region"])
        if row:
            valchecker_db.upsert_match_cache(row)
    agg = stats.aggregate_stats(summaries)

    if view == "stats":
        return {"embeds": [embeds.profile_stats_embed(player, agg, count, summaries, lang)]}
    if view == "agents":
        emb = embeds.profile_agents_embed(player, agg, session.get("filter"), summaries, lang)
        top = session.get("filter") or (
            sorted(agg["agents"].items(), key=lambda x: x[1]["games"], reverse=True)[0][0]
            if agg["agents"]
            else None
        )
        icon = vap.agent_by_name(top)
        if icon and icon.get("displayIcon"):
            emb.set_thumbnail(url=icon["displayIcon"])
        return {"embeds": [emb]}
    if view == "maps":
        emb = embeds.profile_maps_embed(player, agg, session.get("filter"), summaries, lang)
        top = session.get("filter") or (
            sorted(agg["maps"].items(), key=lambda x: x[1]["games"], reverse=True)[0][0]
            if agg["maps"]
            else None
        )
        m = vap.map_by_path_or_name(top)
        if m and m.get("listViewIcon"):
            emb.set_thumbnail(url=m["listViewIcon"])
        return {"embeds": [emb]}
    return {"embeds": [embeds.profile_embed(player, mmr, account, agg, summaries, lang)]}


async def load_match_payload(session: dict, view: str) -> dict:
    lang = session.get("locale") or "en"
    player = {
        "puuid": session["puuid"],
        "name": session["name"],
        "tag": session["tag"],
        "region": session["region"],
        "platform": "pc",
    }
    count = min(15, session.get("count") or 5)
    lst = await henrik.matches_by_puuid(
        player["region"], "pc", player["puuid"], size=count if view == "history" else 10
    )
    if view == "history":
        summaries = stats.summaries_from_matches(
            lst.get("data"), player["puuid"], player["name"], player["tag"]
        )[:count]
        for s in summaries:
            row = stats.to_cache_row(s, player["region"])
            if row:
                valchecker_db.upsert_match_cache(row)
        if not summaries:
            return {"embeds": [embeds.error_embed(i18n.t("valchecker.nav.err_no_matches", lang), lang)]}
        return {"embeds": [embeds.history_embed(player, summaries, lang)]}

    match = stats.pick_latest_match(lst.get("data"))
    if not match:
        return {"embeds": [embeds.error_embed(i18n.t("valchecker.nav.err_no_matches", lang), lang)]}
    summary = stats.summarize_match(match, player["puuid"], player["name"], player["tag"])
    row = stats.to_cache_row(summary, player["region"])
    if row:
        valchecker_db.upsert_match_cache(row)
    return {"embeds": [embeds.match_embed(summary, None, lang)]}


async def build_profile_reply(owner_id: int, player: dict, view: str, *, count=10, filter=None, lang="en"):
    sid = stats.create_session({
        "kind": "profile",
        "ownerId": owner_id,
        "puuid": player["puuid"],
        "name": player["name"],
        "tag": player["tag"],
        "region": player["region"],
        "count": count,
        "filter": filter,
        "locale": lang,
    })
    session = stats.get_session(sid)
    payload = await load_profile_payload(session, view)
    return {**payload, "view": ProfileNavView(sid, view, lang)}


async def build_match_reply(owner_id: int, player: dict, view: str, *, count=5, lang="en"):
    sid = stats.create_session({
        "kind": "match",
        "ownerId": owner_id,
        "puuid": player["puuid"],
        "name": player["name"],
        "tag": player["tag"],
        "region": player["region"],
        "view": view,
        "count": count,
        "locale": lang,
    })
    session = stats.get_session(sid)
    payload = await load_match_payload(session, view)
    return {**payload, "view": MatchNavView(sid, view, session.get("count") or 5, lang)}


async def resolve_player(
    interaction: discord.Interaction,
    *,
    riot_id_opt: str | None,
    user_opt: discord.User | None,
    region_opt: str | None,
    require_link: bool = False,
) -> dict:
    lang = _lang(interaction.guild_id)
    if riot_id_opt:
        parsed = stats.parse_riot_id(riot_id_opt)
        if not parsed:
            return {"error": i18n.t("valchecker.resolve.bad_riot", lang)}
        acc = await henrik.account(parsed["name"], parsed["tag"])
        account = acc["data"]
        return {
            "name": account["name"],
            "tag": account["tag"],
            "puuid": account["puuid"],
            "region": region_opt or account.get("region") or "eu",
            "platform": "pc",
            "account": account,
            "linked": False,
        }

    target = user_opt or interaction.user
    linked = valchecker_db.get_user(str(target.id))
    if not linked:
        if require_link or user_opt is None:
            return {
                "error": (
                    i18n.t("valchecker.resolve.user_no_link_setup", lang, user=str(user_opt))
                    if user_opt
                    else i18n.t("valchecker.resolve.link_self", lang)
                )
            }
        return {"error": i18n.t("valchecker.resolve.user_no_link", lang, user=str(user_opt))}
    return {
        "name": linked["name"],
        "tag": linked["tag"],
        "puuid": linked["puuid"],
        "region": region_opt or linked["region"],
        "platform": "pc",
        "discordId": linked["discord_id"],
        "linked": True,
        "db": linked,
    }


# ── Cog ─────────────────────────────────────────────────────────────────────

class ValCheckerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._poll_running = False
        self._posted_match_keys: dict[str, float] = {}
        self._posted_relation_keys: dict[str, float] = {}
        # guild_id → monotonic deadline; skip chunk() retries until then
        self._chunk_backoff: dict[int, float] = {}
        self.match_poller.start()
        self.status_monitor.start()

    async def cog_load(self):
        valchecker_db.init()
        try:
            assets = await vap.load_assets()
            logger.info("assets agents=%s maps=%s ranks=%s", assets["agents"], assets["maps"], assets["ranks"])
        except Exception as e:
            logger.warning("assets preload failed: %s", e)

    async def cog_unload(self):
        self.match_poller.cancel()
        self.status_monitor.cancel()
        await henrik.close_client()

    def _remember(self, store: dict[str, float], key: str, ttl: float = 21600):
        store[key] = time.monotonic() + ttl
        now = time.monotonic()
        expired = [k for k, exp in store.items() if exp < now]
        for k in expired:
            store.pop(k, None)

    def _has(self, store: dict[str, float], key: str) -> bool:
        exp = store.get(key)
        if exp is None:
            return False
        if exp < time.monotonic():
            store.pop(key, None)
            return False
        return True

    # ── poller ──────────────────────────────────────────────────────────────

    @tasks.loop(seconds=90)
    async def match_poller(self):
        try:
            await self._poll_once()
        except Exception:
            logger.exception("match poller error")

    @match_poller.before_loop
    async def _before_poll(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)

    async def _poll_once(self):
        if self._poll_running:
            return
        self._poll_running = True
        try:
            intervals = []
            enabled_guild_ids: list[int] = []
            for g in self.bot.guilds:
                s = valchecker_core.get_settings(g.id)
                if s["enabled"]:
                    intervals.append(max(30, s["poll_interval_sec"]))
                    enabled_guild_ids.append(g.id)
            if intervals:
                new_iv = min(intervals)
                if abs(self.match_poller.seconds - new_iv) > 0.5:
                    self.match_poller.change_interval(seconds=new_iv)

            if not valchecker_core.any_enabled_match_guild(enabled_guild_ids):
                return

            for user in valchecker_db.get_tracked_users():
                try:
                    await self._poll_one(user)
                except Exception as e:
                    logger.warning("poller %s#%s: %s", user.get("name"), user.get("tag"), e)
        finally:
            self._poll_running = False

    async def _resolve_text_channel(self, guild: discord.Guild, channel_id: str):
        try:
            ch = guild.get_channel(int(channel_id))
            if ch is None:
                ch = await self.bot.fetch_channel(int(channel_id))
        except (discord.NotFound, discord.Forbidden, discord.HTTPException, ValueError):
            return None
        if isinstance(ch, discord.TextChannel):
            return ch
        return None

    async def _poll_one(self, user: dict):
        matches_res = await henrik.matches_by_puuid(user["region"], "pc", user["puuid"], size=5)
        match = stats.pick_latest_match(matches_res.get("data"))
        if not match:
            return
        summary = stats.summarize_match(match, user["puuid"], user["name"], user["tag"])
        if not summary.get("matchId"):
            return
        row = stats.to_cache_row(summary, user["region"])
        if row:
            valchecker_db.upsert_match_cache(row)

        is_new = bool(user.get("last_match_id") and user["last_match_id"] != summary["matchId"])
        self_player = stats.find_player(match, user["puuid"], user["name"], user["tag"])

        mmr = None
        rank_info = None
        try:
            mmr = stats.normalize_mmr(await henrik.mmr_by_puuid(user["region"], "pc", user["puuid"]))
            if is_new:
                rank_info = stats.rank_change_info(user.get("last_rank"), user.get("last_rr"), mmr)
        except Exception:
            pass

        if not is_new:
            valchecker_db.update_track_state(
                user["discord_id"],
                last_match_id=summary["matchId"],
                last_rr=mmr.get("rr") if mmr else None,
                last_rank=mmr.get("rank") if mmr else None,
            )
            return

        post_failures = 0
        for guild in self.bot.guilds:
            settings = valchecker_core.get_settings(guild.id)
            if not settings["enabled"]:
                continue
            member = guild.get_member(int(user["discord_id"]))
            if member is None:
                try:
                    member = await guild.fetch_member(int(user["discord_id"]))
                except (discord.NotFound, discord.HTTPException):
                    continue

            channel_id = valchecker_core.resolve_match_channel_id(guild.id)
            if not channel_id:
                continue
            channel = await self._resolve_text_channel(guild, channel_id)
            if channel is None:
                continue

            lang = _lang(guild.id)
            match_key = f"{guild.id}:{summary['matchId']}"
            if not self._has(self._posted_match_keys, match_key):
                emb = embeds.match_embed(summary, rank_info, lang)
                emb.set_footer(
                    text=f"ValChecker · {i18n.t('valchecker.match.tracked_footer', lang, id=stats.riot_id(user['name'], user['tag']))}"
                )
                try:
                    await channel.send(embeds=[emb])
                    self._remember(self._posted_match_keys, match_key)
                except discord.HTTPException:
                    post_failures += 1
                    continue

            if self_player:
                await self._report_relations(guild, channel, match, user, self_player, lang)

        # Advance cursor only when every target guild got the match (or none needed it).
        if post_failures == 0:
            valchecker_db.update_track_state(
                user["discord_id"],
                last_match_id=summary["matchId"],
                last_rr=mmr.get("rr") if mmr else None,
                last_rank=mmr.get("rank") if mmr else None,
            )
        else:
            valchecker_db.update_track_state(
                user["discord_id"],
                last_rr=mmr.get("rr") if mmr else None,
                last_rank=mmr.get("rank") if mmr else None,
            )

    async def _ensure_chunked(self, guild: discord.Guild) -> None:
        if guild.chunked:
            return
        until = self._chunk_backoff.get(guild.id)
        if until is not None and until > time.monotonic():
            return
        try:
            await guild.chunk()
            self._chunk_backoff.pop(guild.id, None)
        except Exception:
            self._chunk_backoff[guild.id] = time.monotonic() + 900  # 15 min

    async def _report_relations(self, guild, channel, match, self_user, self_player, lang):
        await self._ensure_chunked(guild)
        member_ids = [str(m.id) for m in guild.members]
        others = [
            u for u in valchecker_db.get_linked_in_guild(member_ids)
            if u["puuid"] != self_user["puuid"]
        ]
        if not others:
            return

        allies, enemies = [], []
        for other in others:
            p = next((x for x in (match.get("players") or []) if x.get("puuid") == other["puuid"]), None)
            if not p:
                continue
            line = self._player_line(other["discord_id"], p)
            if p.get("team_id") and self_player.get("team_id") and p["team_id"] == self_player["team_id"]:
                allies.append(line)
            elif p.get("team_id") and self_player.get("team_id"):
                enemies.append(line)

        match_id = (match.get("metadata") or {}).get("match_id")
        self_line = self._player_line(self_user["discord_id"], self_player)

        if enemies:
            key = f"{guild.id}:{match_id}:enemy"
            if not self._has(self._posted_relation_keys, key):
                parts = [
                    i18n.t("valchecker.match.enemy_desc", lang),
                    "",
                    f"**{i18n.t('valchecker.match.us', lang)}**\n{self_line}",
                    "",
                    f"**{i18n.t('valchecker.match.them', lang)}**\n" + "\n".join(enemies),
                ]
                if allies:
                    parts.append(
                        "\n" + i18n.t(
                            "valchecker.match.also_allied",
                            lang,
                            list=", ".join(l.split("  ·  ")[0] for l in allies),
                        )
                    )
                try:
                    await channel.send(
                        embeds=[embeds.simple_embed(
                            i18n.t("valchecker.match.enemy_title", lang),
                            "\n".join(parts),
                            embeds.COLORS["loss"],
                        )]
                    )
                    self._remember(self._posted_relation_keys, key)
                except discord.HTTPException:
                    pass
        elif allies:
            key = f"{guild.id}:{match_id}:ally"
            if not self._has(self._posted_relation_keys, key):
                try:
                    await channel.send(
                        embeds=[embeds.simple_embed(
                            i18n.t("valchecker.match.squad_title", lang),
                            "\n".join([self_line, *allies]),
                            embeds.COLORS["info"],
                        )]
                    )
                    self._remember(self._posted_relation_keys, key)
                except discord.HTTPException:
                    pass

    @staticmethod
    def _player_line(discord_id, player) -> str:
        agent = ((player.get("agent") or {}).get("name")) or "?"
        st = player.get("stats") or {}
        k = st.get("kills", "?")
        d = st.get("deaths", "?")
        a = st.get("assists", "?")
        return f"<@{discord_id}>  ·  {agent}  ·  `{k}/{d}/{a}`"

    # ── status monitor ──────────────────────────────────────────────────────

    @tasks.loop(seconds=120)
    async def status_monitor(self):
        try:
            await self._check_status_once()
        except Exception:
            logger.exception("status monitor error")

    @status_monitor.before_loop
    async def _before_status(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(8)

    def _regions_to_watch(self) -> list[str]:
        """Regions relevant to at least one enabled guild (linked members there)."""
        regions: set[str] = set()
        for guild in self.bot.guilds:
            settings = valchecker_core.get_settings(guild.id)
            if not settings["enabled"]:
                continue
            if not valchecker_core.resolve_alert_channel_id(guild.id):
                continue
            member_ids = [str(m.id) for m in guild.members]
            for u in valchecker_db.get_linked_in_guild(member_ids):
                if u.get("region"):
                    regions.add(str(u["region"]).lower())
        return list(regions) if regions else []

    async def _check_status_once(self):
        regions = self._regions_to_watch()
        if not regions:
            return
        for region in regions:
            try:
                res = await henrik.status(region)
                state = stats.summarize_status(res.get("data") or {})
                stored = valchecker_db.get_status_fingerprints(region)
                if stored is None:
                    valchecker_db.set_status_fingerprints(
                        region,
                        stats.diff_status_items(state["items"], {}).get("nextFingerprints"),
                    )
                    continue
                delta = stats.diff_status_items(state["items"], stored)
                if delta["added"] or delta["updated"]:
                    await self._post_delta_alert(region, delta, state)
                elif delta["resolvedAll"]:
                    await self._post_recovery_alert(region)
                valchecker_db.set_status_fingerprints(region, delta["nextFingerprints"])
            except Exception as e:
                logger.warning("status %s: %s", region, e)

    async def _post_per_guild(self, build_embed, *, region: str | None = None):
        for guild in self.bot.guilds:
            settings = valchecker_core.get_settings(guild.id)
            if not settings["enabled"]:
                continue
            if region:
                member_ids = [str(m.id) for m in guild.members]
                guild_regions = {
                    str(u.get("region") or "").lower()
                    for u in valchecker_db.get_linked_in_guild(member_ids)
                    if u.get("region")
                }
                if region.lower() not in guild_regions:
                    continue
            channel_id = valchecker_core.resolve_alert_channel_id(guild.id)
            if not channel_id:
                continue
            channel = await self._resolve_text_channel(guild, channel_id)
            if channel is None:
                continue
            lang = _lang(guild.id)
            emb = build_embed(lang)
            if emb is None:
                continue
            try:
                await channel.send(embeds=[emb])
            except discord.HTTPException:
                pass

    async def _post_delta_alert(self, region, delta, state):
        def build(lang):
            parts = []
            if delta["added"]:
                parts.append(f"**{i18n.t('valchecker.status.new', lang)}**\n{stats.format_delta(delta['added'], lang)}")
            if delta["updated"]:
                parts.append(f"**{i18n.t('valchecker.status.updated', lang)}**\n{stats.format_delta(delta['updated'], lang)}")
            if not parts:
                return None
            counts = []
            if state["maintenanceCount"]:
                counts.append(i18n.t("valchecker.status.count_maint", lang, n=state["maintenanceCount"]))
            if state["incidentCount"]:
                key = "valchecker.status.count_inc" if state["incidentCount"] == 1 else "valchecker.status.count_inc_plural"
                counts.append(i18n.t(key, lang, n=state["incidentCount"]))
            sevs = [
                str((x.get("issue") or {}).get("incident_severity") or "").lower()
                for x in [*delta["added"], *delta["updated"]]
            ]
            color = embeds.COLORS["loss"] if "critical" in sevs else (
                embeds.COLORS["accent"] if "warning" in sevs else embeds.COLORS["soft"]
            )
            body = "\n\n".join(parts)
            if counts:
                body = f"{body}\n\n{' · '.join(counts)}"
            return embeds.simple_embed(
                i18n.t("valchecker.status.alert_title", lang, region=region.upper()),
                body,
                color,
            )
        await self._post_per_guild(build, region=region)

    async def _post_recovery_alert(self, region):
        await self._post_per_guild(
            lambda lang: embeds.simple_embed(
                i18n.t("valchecker.status.recovery_title", lang, region=region.upper()),
                i18n.t("valchecker.status.recovery_desc", lang),
                embeds.COLORS["info"],
            ),
            region=region,
        )

    # ── slash commands ──────────────────────────────────────────────────────

    @app_commands.command(name="val-setup", description="Open your account panel — link, track, unlink")
    async def val_setup(self, interaction: discord.Interaction):
        if await _deny_disabled(interaction):
            return
        lang = _lang(interaction.guild_id)
        panel = build_setup_panel(interaction.user, lang)
        await interaction.response.send_message(**panel, ephemeral=True)

    @app_commands.command(name="val-profile", description="Player profile — rank, form, agents and maps")
    @app_commands.describe(
        riot_id="Riot ID Name#TAG",
        user="Linked Discord user",
        region="Region",
        view="What to show",
        count="Matches to analyze (default 10, max 15)",
        filter="Agent or map name (for Agents / Maps view)",
    )
    @app_commands.choices(
        region=REGION_CHOICES,
        view=[
            slash_i18n.localized_choice("overview", "slash.val.profile.overview"),
            slash_i18n.localized_choice("stats", "slash.val.profile.stats"),
            slash_i18n.localized_choice("agents", "slash.val.profile.agents"),
            slash_i18n.localized_choice("maps", "slash.val.profile.maps"),
        ],
    )
    async def val_profile(
        self,
        interaction: discord.Interaction,
        riot_id: str | None = None,
        user: discord.User | None = None,
        region: app_commands.Choice[str] | None = None,
        view: app_commands.Choice[str] | None = None,
        count: app_commands.Range[int, 1, 15] | None = None,
        filter: str | None = None,
    ):
        if await _deny_disabled(interaction):
            return
        await interaction.response.defer()
        lang = _lang(interaction.guild_id)
        try:
            player = await resolve_player(
                interaction,
                riot_id_opt=riot_id,
                user_opt=user,
                region_opt=region.value if region else None,
            )
            if player.get("error"):
                return await interaction.followup.send(embed=embeds.error_embed(player["error"], lang))
            reply = await build_profile_reply(
                interaction.user.id,
                player,
                (view.value if view else "overview"),
                count=count or 10,
                filter=filter,
                lang=lang,
            )
            await interaction.followup.send(**reply)
        except Exception as e:
            await interaction.followup.send(
                embed=embeds.error_embed(
                    henrik.friendly_error(e, lang) or i18n.t("valchecker.err.generic", lang),
                    lang,
                )
            )

    @app_commands.command(name="val-match", description="Latest match or recent history")
    @app_commands.describe(
        riot_id="Riot ID Name#TAG",
        user="Linked Discord user",
        view="What to show",
        count="History size (1–10, default 5)",
    )
    @app_commands.choices(
        view=[
            slash_i18n.localized_choice("latest", "slash.val.match.latest"),
            slash_i18n.localized_choice("history", "slash.val.match.history"),
        ],
    )
    async def val_match(
        self,
        interaction: discord.Interaction,
        riot_id: str | None = None,
        user: discord.User | None = None,
        view: app_commands.Choice[str] | None = None,
        count: app_commands.Range[int, 1, 10] | None = None,
    ):
        if await _deny_disabled(interaction):
            return
        await interaction.response.defer()
        lang = _lang(interaction.guild_id)
        try:
            player = await resolve_player(
                interaction, riot_id_opt=riot_id, user_opt=user, region_opt=None
            )
            if player.get("error"):
                return await interaction.followup.send(embed=embeds.error_embed(player["error"], lang))
            reply = await build_match_reply(
                interaction.user.id,
                player,
                (view.value if view else "latest"),
                count=count or 5,
                lang=lang,
            )
            await interaction.followup.send(**reply)
        except Exception as e:
            await interaction.followup.send(
                embed=embeds.error_embed(
                    henrik.friendly_error(e, lang) or i18n.t("valchecker.err.generic", lang),
                    lang,
                )
            )

    @app_commands.command(name="val-compare", description="Compare two players")
    @app_commands.describe(
        user_a="Player A (Discord)",
        user_b="Player B (Discord)",
        riot_a="Player A Riot ID",
        riot_b="Player B Riot ID",
        region="Region",
    )
    @app_commands.choices(region=REGION_CHOICES)
    async def val_compare(
        self,
        interaction: discord.Interaction,
        user_a: discord.User | None = None,
        user_b: discord.User | None = None,
        riot_a: str | None = None,
        riot_b: str | None = None,
        region: app_commands.Choice[str] | None = None,
    ):
        if await _deny_disabled(interaction):
            return
        await interaction.response.defer()
        lang = _lang(interaction.guild_id)
        region_val = region.value if region else None

        async def resolve_one(riot_str, user, fallback):
            if riot_str:
                parsed = stats.parse_riot_id(riot_str)
                if not parsed:
                    raise ValueError(i18n.t("valchecker.compare.bad_riot", lang, id=riot_str))
                acc = await henrik.account(parsed["name"], parsed["tag"])
                return {
                    "name": acc["data"]["name"],
                    "tag": acc["data"]["tag"],
                    "puuid": acc["data"]["puuid"],
                    "region": region_val or acc["data"].get("region") or "eu",
                    "platform": "pc",
                }
            u = user or fallback
            if u is None:
                raise ValueError(i18n.t("valchecker.compare.need_b", lang))
            linked = valchecker_db.get_user(str(u.id))
            if not linked:
                raise ValueError(i18n.t("valchecker.compare.no_link", lang, user=u.display_name))
            return {
                "name": linked["name"],
                "tag": linked["tag"],
                "puuid": linked["puuid"],
                "region": region_val or linked["region"],
                "platform": "pc",
            }

        try:
            a = await resolve_one(riot_a, user_a, interaction.user)
            if not user_b and not riot_b:
                return await interaction.followup.send(
                    embed=embeds.error_embed(i18n.t("valchecker.compare.need_b", lang), lang)
                )
            b = await resolve_one(riot_b, user_b, None)

            async def pack(p):
                mmr_raw, matches_raw = await asyncio.gather(
                    henrik.mmr_by_puuid(p["region"], "pc", p["puuid"]),
                    henrik.matches_by_puuid(p["region"], "pc", p["puuid"], size=10),
                    return_exceptions=True,
                )
                mmr_body = mmr_raw if isinstance(mmr_raw, dict) else {}
                matches = matches_raw if isinstance(matches_raw, dict) else {}
                return {
                    "mmr": stats.normalize_mmr(mmr_body),
                    "agg": stats.aggregate_stats(
                        stats.summaries_from_matches(
                            matches.get("data"), p["puuid"], p["name"], p["tag"]
                        )
                    ),
                }

            pa, pb = await asyncio.gather(pack(a), pack(b))
            await interaction.followup.send(embed=embeds.compare_embed(a, pa, b, pb, lang))
        except Exception as e:
            await interaction.followup.send(
                embed=embeds.error_embed(
                    henrik.friendly_error(e, lang) or i18n.t("valchecker.err.generic", lang),
                    lang,
                )
            )

    @app_commands.command(name="val-lb", description="Server leaderboard of linked players")
    @app_commands.describe(sort="Sort by", limit="Max players (default 15)")
    @app_commands.choices(
        sort=[
            slash_i18n.localized_choice("rank", "slash.val.lb.rank"),
            slash_i18n.localized_choice("wr", "slash.val.lb.wr"),
            slash_i18n.localized_choice("acs", "slash.val.lb.acs"),
        ]
    )
    async def val_lb(
        self,
        interaction: discord.Interaction,
        sort: app_commands.Choice[str] | None = None,
        limit: app_commands.Range[int, 3, 25] | None = None,
    ):
        if await _deny_disabled(interaction):
            return
        await interaction.response.defer()
        lang = _lang(interaction.guild_id)
        try:
            if interaction.guild is None:
                return await interaction.followup.send(
                    embed=embeds.error_embed(i18n.t("valchecker.common.server_only_cmd", lang), lang)
                )
            await self._ensure_chunked(interaction.guild)
            linked = valchecker_db.get_linked_in_guild([str(m.id) for m in interaction.guild.members])
            if not linked:
                return await interaction.followup.send(
                    embed=embeds.error_embed(i18n.t("valchecker.lb.no_linked", lang), lang)
                )

            sort_val = sort.value if sort else "rank"
            lim = limit or 15
            rows: list[dict] = []
            sem = asyncio.Semaphore(2)

            async def one(u):
                async with sem:
                    try:
                        mmr_body, matches_body = await asyncio.gather(
                            henrik.mmr_by_puuid(u["region"], "pc", u["puuid"]),
                            henrik.matches_by_puuid(u["region"], "pc", u["puuid"], size=10),
                        )
                        mmr = stats.normalize_mmr(mmr_body)
                        summaries = stats.summaries_from_matches(
                            matches_body.get("data"), u["puuid"], u["name"], u["tag"]
                        )
                        agg = stats.aggregate_stats(summaries)
                        rows.append({
                            "discordId": u["discord_id"],
                            "rank": mmr["rank"],
                            "rr": mmr["rr"],
                            "peak": (mmr.get("peak") or {}).get("name"),
                            "rankKey": stats.rank_sort_key(mmr["rank"], mmr["rr"]),
                            "wr": agg["wr"],
                            "acs": agg["avgAcs"],
                            "form": stats.form_strip(summaries, 5),
                        })
                    except Exception:
                        pass

            await asyncio.gather(*(one(u) for u in linked))
            if not rows:
                return await interaction.followup.send(
                    embed=embeds.error_embed(i18n.t("valchecker.lb.load_fail", lang), lang)
                )

            if sort_val == "wr":
                rows.sort(key=lambda r: ((r["wr"] if r["wr"] is not None else -1), r["rankKey"]), reverse=True)
            elif sort_val == "acs":
                rows.sort(key=lambda r: ((r["acs"] if r["acs"] is not None else -1), r["rankKey"]), reverse=True)
            else:
                rows.sort(key=lambda r: r["rankKey"], reverse=True)

            lines = []
            for i, r in enumerate(rows[:lim]):
                n = f"{i + 1:02d}"
                extra = f"{r['rr']}RR"
                if sort_val == "wr":
                    extra = f"WR {stats.pct(r['wr'] or 0)}"
                if sort_val == "acs":
                    extra = f"ACS {(r['acs'] or 0):.0f}"
                peak = (
                    i18n.t("valchecker.lb.peak", lang, name=r["peak"])
                    if r["peak"]
                    else i18n.t("valchecker.lb.peak_none", lang)
                )
                form = r["form"] if r["form"] and r["form"] != "—" else "-----"
                lines.append(
                    f"`#{n}` <@{r['discordId']}> · **{r['rank']}** · {extra} · {peak} · `{form}`"
                )

            title_sort = {
                "wr": i18n.t("valchecker.lb.sort_wr", lang),
                "acs": i18n.t("valchecker.lb.sort_acs", lang),
            }.get(sort_val, i18n.t("valchecker.lb.sort_rank", lang))

            await interaction.followup.send(
                embed=embeds.leaderboard_embed(interaction.guild.name, lines, title_sort, lang)
            )
        except Exception as e:
            await interaction.followup.send(
                embed=embeds.error_embed(
                    henrik.friendly_error(e, lang) or i18n.t("valchecker.err.generic", lang),
                    lang,
                )
            )

    @app_commands.command(name="val-status", description="Valorant server / queue status")
    @app_commands.describe(region="Region", type="What to show")
    @app_commands.choices(
        region=REGION_CHOICES,
        type=[
            slash_i18n.localized_choice("status", "slash.val.status.incidents"),
            slash_i18n.localized_choice("queues", "slash.val.status.queues"),
            slash_i18n.localized_choice("both", "slash.val.status.both"),
        ],
    )
    async def val_status(
        self,
        interaction: discord.Interaction,
        region: app_commands.Choice[str],
        type: app_commands.Choice[str] | None = None,
    ):
        if await _deny_disabled(interaction):
            return
        await interaction.response.defer()
        lang = _lang(interaction.guild_id)
        try:
            region_val = region.value
            type_val = type.value if type else "both"
            fields = []

            if type_val in ("status", "both"):
                res = await henrik.status(region_val)
                d = res.get("data") or {}
                maintenances = d.get("maintenances") or []
                incidents = d.get("incidents") or []
                fields.append({
                    "name": i18n.t("valchecker.status.maintenances", lang, n=len(maintenances)),
                    "value": stats.format_issue_list(maintenances, lang),
                })
                fields.append({
                    "name": i18n.t("valchecker.status.incidents", lang, n=len(incidents)),
                    "value": stats.format_issue_list(incidents, lang),
                })

            if type_val in ("queues", "both"):
                try:
                    q = await henrik.queue_status(region_val)
                    modes = q.get("data") or []
                    if isinstance(modes, dict):
                        lst = [{"mode": k, **(v or {})} for k, v in modes.items()]
                    else:
                        lst = modes
                    lines = []
                    for m in lst[:12]:
                        name = m.get("mode") or m.get("name") or m.get("queueId") or "queue"
                        wait = m.get("wait_time") or m.get("waitTime") or m.get("estimated_wait") or m.get("status") or "—"
                        lines.append(f"**{name}**  ·  {wait}")
                    fields.append({
                        "name": i18n.t("valchecker.status.queues", lang),
                        "value": "\n".join(lines) or i18n.t("valchecker.status.no_queue", lang),
                    })
                except Exception as e:
                    fields.append({
                        "name": i18n.t("valchecker.status.queues", lang),
                        "value": i18n.t("valchecker.status.queues_unavailable", lang, msg=str(e)),
                    })

            await interaction.followup.send(embed=embeds.status_embed(region_val, fields, lang))
        except Exception as e:
            await interaction.followup.send(
                embed=embeds.error_embed(
                    henrik.friendly_error(e, lang) or i18n.t("valchecker.err.generic", lang),
                    lang,
                )
            )


async def setup(bot: commands.Bot):
    cog = ValCheckerCog(bot)
    await bot.add_cog(cog)
    slash_registry.register_valchecker(cog)
