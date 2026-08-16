"""Кастомки cog: dashboard-published lobbies with button UX (Events-style).

No player slash commands — join/rank/teams/host controls live on the lobby embed.
Map voting (when enabled) uses a separate message; main lobby stays ≤2 button rows
until the match is live (or team VCs exist), when «Назад в лобби» is added on row 3.
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from typing import Any

import discord
from discord.ext import commands, tasks

import embed_style
import i18n
import customs_core
import valorant_maps

logger = logging.getLogger("cheterin.customs")

COG_NAME = "CustomsCog"

# Persistent custom_ids (restart-safe).
CID_JOIN = "customs:join"
CID_CODE_CREATE = "customs:code_create"
CID_CODE_JOIN = "customs:code_join"
CID_LEAVE = "customs:leave"
CID_RANK = "customs:rank"
CID_BALANCE = "customs:balance"
CID_MAP = "customs:map"
CID_START = "customs:start"
CID_CANCEL = "customs:cancel"
CID_BACK_LOBBY = "customs:back_lobby"
CID_SCORE = "customs:score"
CID_SCORE_A = "customs:score:a"
CID_SCORE_B = "customs:score:b"
CID_SCORE_MODAL = "customs:score:modal"
CID_MVOTE = ("customs:mvote:0", "customs:mvote:1", "customs:mvote:2", "customs:mvote:3", "customs:mvote:4")

VC_CLEANUP_DELAY_SEC = 2
VOICE_REFRESH_DEBOUNCE_SEC = 2.0


def _map_info(map_id: str) -> dict[str, str] | None:
    return next((m for m in valorant_maps.MAPS if m["id"] == map_id), None)


def _voice_channel_url(guild_id: int, channel_id: int) -> str:
    return f"https://discord.com/channels/{guild_id}/{channel_id}"


_DEFAULT_LOBBY_NAMES = frozenset({"кастомка", "custom"})


def _lobby_embed_title(lobby: dict, lang: str) -> str:
    """Avoid 'Кастомка · Кастомка' when the lobby uses the default name."""
    name = str(lobby.get("name") or "").strip()
    if not name or name.casefold() in _DEFAULT_LOBBY_NAMES:
        return i18n.t("customs.embed.title_plain", lang)
    return i18n.t("customs.embed.title", lang, name=name)


def _is_host_or_mod(member: discord.Member, lobby: dict, settings: dict) -> bool:
    if str(member.id) == str(lobby.get("host_id")):
        return True
    if member.guild_permissions.manage_guild:
        return True
    host_role = settings.get("host_role_id") or ""
    if host_role and any(str(r.id) == host_role for r in member.roles):
        return True
    return False


def _fmt_player(
    p: dict,
    *,
    show_code: bool = False,
    in_voice: set[str] | None = None,
    lang: str = "ru",
) -> str:
    rank = p.get("rank_name") or p.get("rank") or "?"
    code = str(p.get("team_code") or "")
    code_bit = f" · `{code}`" if show_code and code else ""
    uid = str(p.get("user_id") or "")
    prefix = ""
    if in_voice is not None:
        key = "customs.embed.vc_in" if uid in in_voice else "customs.embed.vc_out"
        prefix = f"{i18n.t(key, lang)} "
    return f"{prefix}<@{uid}> · {rank}{code_bit}"


def apply_map_image(embed: discord.Embed, lobby: dict) -> list[discord.File]:
    """Splash on the main lobby embed as soon as a map is chosen."""
    map_id = str(lobby.get("map_id") or "")
    if not map_id:
        return []
    info = _map_info(map_id)
    if info is None:
        return []
    path, url = valorant_maps.embed_image(info)
    embed.set_image(url=url)
    if path is not None:
        return [discord.File(path, filename=path.name)]
    return []


def in_voice_user_ids(guild: discord.Guild, lobby: dict) -> set[str] | None:
    vc_ids = customs_core.lobby_voice_ids(lobby)
    if not vc_ids:
        return None
    found: set[str] = set()
    for cid in vc_ids:
        ch = guild.get_channel(cid)
        if isinstance(ch, discord.VoiceChannel):
            found.update(str(m.id) for m in ch.members)
    return found


def ping_message_content(settings: dict, lobby: dict, *, include_participants: bool) -> str | None:
    ping = customs_core._normalize_ping(lobby.get("ping") or settings.get("default_ping"))
    if ping == customs_core.PING_ROLE:
        rid = str(settings.get("ping_role_id") or "")
        if rid.isdigit():
            return f"<@&{rid}>"
        return None
    if ping == customs_core.PING_PARTICIPANTS and include_participants:
        ids = customs_core.lobby_participant_ids(lobby)
        if not ids:
            return None
        return " ".join(f"<@{uid}>" for uid in ids)
    return None


def build_lobby_embed(lobby: dict, lang: str, *, in_voice: set[str] | None = None) -> discord.Embed:
    status = lobby.get("status") or customs_core.STATUS_OPEN
    title = _lobby_embed_title(lobby, lang)
    color = embed_style.VALORANT
    if status == customs_core.STATUS_CANCELLED:
        color = embed_style.NEUTRAL
    elif status == customs_core.STATUS_FINISHED:
        color = embed_style.SUCCESS
    elif status == customs_core.STATUS_LIVE:
        color = embed_style.WARN

    embed = discord.Embed(title=title, color=color)
    notes = (lobby.get("notes") or "").strip()
    mode = lobby.get("join_mode") or customs_core.JOIN_MODE_SOLO
    mode_label = i18n.t(
        "customs.mode.solo" if mode == customs_core.JOIN_MODE_SOLO else "customs.mode.team_code",
        lang,
    )
    desc_parts = [i18n.t("customs.embed.mode", lang, mode=mode_label)]
    if notes:
        desc_parts.append(notes[:900])
    signup_ends = int(lobby.get("signup_ends_at") or 0)
    if signup_ends and status in (
        customs_core.STATUS_OPEN,
        customs_core.STATUS_CHECKIN,
        customs_core.STATUS_READY,
    ):
        desc_parts.append(i18n.t("customs.embed.signup", lang, when=f"<t:{signup_ends}:R>"))
    embed.description = "\n".join(desc_parts)

    players = lobby.get("players") or []
    subs = lobby.get("subs") or []
    max_p = lobby.get("max_players") or customs_core.MAX_PLAYERS
    show_code = mode == customs_core.JOIN_MODE_TEAM_CODE
    roster_lines = [
        _fmt_player(p, show_code=show_code, in_voice=in_voice, lang=lang) for p in players
    ] or [i18n.t("customs.embed.empty", lang)]
    embed.add_field(
        name=i18n.t("customs.embed.players", lang, n=len(players), max=max_p),
        value="\n".join(roster_lines)[:1024],
        inline=False,
    )
    if subs:
        embed.add_field(
            name=i18n.t("customs.embed.subs", lang, n=len(subs)),
            value="\n".join(
                _fmt_player(p, show_code=show_code, in_voice=in_voice, lang=lang) for p in subs
            )[:1024],
            inline=False,
        )

    team_a = lobby.get("team_a") or []
    team_b = lobby.get("team_b") or []
    if team_a or team_b:
        embed.add_field(
            name=i18n.t("customs.embed.team_a", lang),
            value=(
                "\n".join(_fmt_player(p, show_code=show_code, in_voice=in_voice, lang=lang) for p in team_a)
                or "—"
            )[:1024],
            inline=True,
        )
        embed.add_field(
            name=i18n.t("customs.embed.team_b", lang),
            value=(
                "\n".join(_fmt_player(p, show_code=show_code, in_voice=in_voice, lang=lang) for p in team_b)
                or "—"
            )[:1024],
            inline=True,
        )

    map_name = lobby.get("map_name") or ""
    if map_name:
        embed.add_field(name=i18n.t("customs.embed.map", lang), value=map_name, inline=True)
    side = lobby.get("side") or ""
    if side:
        side_label = i18n.t(
            "customs.embed.side_attack_a" if side == "attack_a" else "customs.embed.side_defense_a",
            lang,
        )
        embed.add_field(name=i18n.t("customs.embed.side", lang), value=side_label, inline=True)

    embed.set_footer(
        text=embed_style.module_footer(
            i18n.t("customs.footer.module", lang),
            i18n.t("customs.footer.id", lang, id=lobby.get("id")),
        )
    )
    embed.add_field(
        name=i18n.t("customs.embed.host", lang),
        value=f"<@{lobby.get('host_id')}>",
        inline=True,
    )
    embed.add_field(
        name=i18n.t("customs.embed.status", lang),
        value=i18n.t(f"customs.status.{status}", lang),
        inline=True,
    )
    return embed


def build_vote_embed(lobby: dict, lang: str, *, finished: bool = False, winner_label: str = "") -> discord.Embed:
    vote = lobby.get("vote") or {}
    ends = vote.get("ends_at")
    title = i18n.t("customs.embed.vote_title", lang, name=lobby.get("name") or "Кастомка")
    if finished:
        color = embed_style.SUCCESS
        desc = i18n.t("customs.ok.vote_finished", lang, map=winner_label or "—")
    else:
        color = embed_style.INFO
        desc = i18n.t("customs.embed.vote", lang, ends=f"<t:{ends}:R>") if ends else ""

    embed = discord.Embed(title=title, description=desc, color=color)
    opts = vote.get("options") or []
    tallies: dict[str, int] = {}
    for oid in (vote.get("votes") or {}).values():
        tallies[oid] = tallies.get(oid, 0) + 1
    lines = [f"• {o.get('label')}: **{tallies.get(o['id'], 0)}**" for o in opts]
    if lines:
        embed.add_field(
            name=i18n.t("customs.embed.vote_options", lang),
            value="\n".join(lines)[:1024],
            inline=False,
        )
    embed.set_footer(
        text=embed_style.module_footer(
            i18n.t("customs.footer.module", lang),
            i18n.t("customs.footer.id", lang, id=lobby.get("id")),
        )
    )
    return embed


def build_score_embed(lobby: dict, lang: str, *, finished: bool = False) -> discord.Embed:
    title = i18n.t("customs.embed.score_title", lang, name=lobby.get("name") or "Кастомка")
    if finished:
        score = lobby.get("score") or {}
        color = embed_style.SUCCESS
        desc = i18n.t(
            "customs.embed.score_result",
            lang,
            a=score.get("a", 0),
            b=score.get("b", 0),
            map=lobby.get("map_name") or "—",
        )
    else:
        color = embed_style.INFO
        desc = i18n.t("customs.embed.score_hint", lang)
    embed = discord.Embed(title=title, description=desc, color=color)
    embed.set_footer(
        text=embed_style.module_footer(
            i18n.t("customs.footer.module", lang),
            i18n.t("customs.footer.id", lang, id=lobby.get("id")),
        )
    )
    return embed


def build_result_embed(lobby: dict, lang: str) -> discord.Embed:
    embed = discord.Embed(
        title=i18n.t("customs.embed.result_title", lang),
        color=embed_style.SUCCESS,
    )
    map_name = lobby.get("map_name") or "—"
    embed.add_field(name=i18n.t("customs.embed.map", lang), value=map_name, inline=True)
    winner = customs_core.score_winner(lobby)
    score = lobby.get("score") or {}
    a = int(score.get("a") or 0)
    b = int(score.get("b") or 0)
    if winner == "a":
        result = i18n.t("customs.embed.result_winner_a", lang)
    elif winner == "b":
        result = i18n.t("customs.embed.result_winner_b", lang)
    elif a or b:
        result = i18n.t("customs.embed.result_draw", lang)
    else:
        result = i18n.t("customs.embed.result_no_score", lang)
    embed.description = result
    if winner is not None or a or b:
        embed.add_field(name=i18n.t("customs.embed.score", lang), value=f"{a} : {b}", inline=True)
    embed.set_footer(
        text=embed_style.module_footer(
            i18n.t("customs.footer.module", lang),
            i18n.t("customs.footer.id", lang, id=lobby.get("id")),
        )
    )
    apply_map_image(embed, lobby)
    return embed


async def assign_rank_roles(member: discord.Member, rank_id: str, settings: dict) -> None:
    """Assign mapped Discord role for rank; remove other configured rank roles."""
    rank_roles = settings.get("rank_roles") or {}
    configured = customs_core.configured_rank_role_ids(rank_roles)
    if not configured:
        return
    target_raw = str(rank_roles.get(rank_id) or "")
    target_id = int(target_raw) if target_raw.isdigit() else None
    to_remove = [r for r in member.roles if r.id in configured and r.id != target_id]
    if to_remove:
        try:
            await member.remove_roles(*to_remove, reason="customs rank")
        except (discord.Forbidden, discord.HTTPException):
            logger.debug("customs: could not remove rank roles for %s", member.id)
    if target_id:
        role = member.guild.get_role(target_id)
        if role and role not in member.roles:
            try:
                await member.add_roles(role, reason="customs rank")
            except (discord.Forbidden, discord.HTTPException):
                logger.debug("customs: could not add rank role for %s", member.id)


async def clear_customs_rank_roles(member: discord.Member, settings: dict) -> None:
    """Remove only mapped customs rank roles from a member."""
    configured = customs_core.configured_rank_role_ids(settings.get("rank_roles") or {})
    if not configured:
        return
    to_remove = [r for r in member.roles if r.id in configured]
    if not to_remove:
        return
    try:
        await member.remove_roles(*to_remove, reason="customs lobby ended")
    except (discord.Forbidden, discord.HTTPException):
        logger.debug("customs: could not clear rank roles for %s", member.id)


def _bot_can_manage_voice(guild: discord.Guild) -> bool:
    me = guild.me
    if me is None:
        return False
    perms = me.guild_permissions
    return bool(perms.manage_channels and perms.move_members and perms.connect)


def _resolve_voice_category(
    guild: discord.Guild, settings: dict, announce: discord.abc.GuildChannel | None
) -> discord.CategoryChannel | None:
    raw = str(settings.get("voice_category_id") or "")
    if raw.isdigit():
        ch = guild.get_channel(int(raw))
        if isinstance(ch, discord.CategoryChannel):
            return ch
    if announce is not None and getattr(announce, "category", None) is not None:
        cat = announce.category
        if isinstance(cat, discord.CategoryChannel):
            return cat
    return None


def _show_back_to_lobby(lobby: dict) -> bool:
    """Host recall button: after start (live) and/or whenever team VCs exist."""
    if str(lobby.get("status") or "") == customs_core.STATUS_LIVE:
        return True
    for key in ("team_a_vc_id", "team_b_vc_id"):
        if str(lobby.get(key) or "").isdigit():
            return True
    return False


def _match_team_user_ids(lobby: dict) -> list[str]:
    """Unique ids on both teams; fall back to the player roster if teams are empty."""
    seen: set[str] = set()
    out: list[str] = []
    for bucket in ("team_a", "team_b"):
        for p in lobby.get(bucket) or []:
            if not isinstance(p, dict):
                continue
            uid = str(p.get("user_id") or "")
            if uid and uid not in seen:
                seen.add(uid)
                out.append(uid)
    if out:
        return out
    for p in lobby.get("players") or []:
        if not isinstance(p, dict):
            continue
        uid = str(p.get("user_id") or "")
        if uid and uid not in seen:
            seen.add(uid)
            out.append(uid)
    return out


async def _move_user_ids_to_vc(
    guild: discord.Guild,
    user_ids: list[str],
    dest: discord.VoiceChannel,
    *,
    reason: str,
) -> list[str]:
    """Move members to dest. Returns ids not in voice or that failed to move."""
    failed: list[str] = []
    for uid in user_ids:
        if not uid.isdigit():
            continue
        member = guild.get_member(int(uid))
        if member is None or member.voice is None or member.voice.channel is None:
            failed.append(uid)
            continue
        if member.voice.channel.id == dest.id:
            continue
        try:
            await member.move_to(dest, reason=reason)
        except (discord.Forbidden, discord.HTTPException):
            failed.append(uid)
    return failed


async def _announce_move_failures(
    announce: discord.TextChannel | None,
    guild: discord.Guild,
    failed: list[tuple[discord.VoiceChannel, list[str]]],
    lang: str,
    lobby_id: str,
) -> None:
    if not failed or announce is None:
        return
    lines: list[str] = [i18n.t("customs.ok.move_manual_header", lang)]
    for vc, uids in failed:
        if not uids:
            continue
        mentions = " ".join(f"<@{u}>" for u in uids)
        url = _voice_channel_url(guild.id, vc.id)
        lines.append(
            i18n.t(
                "customs.ok.move_manual_line",
                lang,
                mentions=mentions,
                mention=vc.mention,
                url=url,
            )
        )
    if len(lines) < 2:
        return
    try:
        await announce.send("\n".join(lines)[:1900])
    except discord.HTTPException:
        logger.debug("customs: could not post move-manual notice lobby=%s", lobby_id)


def _team_vc_labels(lobby: dict, lang: str) -> tuple[str, str]:
    lid = lobby.get("id") or "?"
    side = lobby.get("side") or ""
    if side == "attack_a":
        a = i18n.t("customs.vc.team_attack", lang, id=lid)
        b = i18n.t("customs.vc.team_defense", lang, id=lid)
    elif side == "defense_a":
        a = i18n.t("customs.vc.team_defense", lang, id=lid)
        b = i18n.t("customs.vc.team_attack", lang, id=lid)
    else:
        a = i18n.t("customs.vc.team_a", lang, id=lid)
        b = i18n.t("customs.vc.team_b", lang, id=lid)
    return a[:100], b[:100]


class TeamCodeModal(discord.ui.Modal):
    def __init__(self, cog: "CustomsCog", lobby_id: str, lang: str):
        super().__init__(title=i18n.t("customs.modal.team_code_title", lang)[:45])
        self.cog = cog
        self.lobby_id = lobby_id
        self.lang = lang
        self.code = discord.ui.TextInput(
            label=i18n.t("customs.modal.team_code_label", lang)[:45],
            required=True,
            min_length=4,
            max_length=6,
            placeholder="AB12C",
        )
        self.add_item(self.code)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        view = RankSelectView(
            self.cog,
            self.lobby_id,
            self.lang,
            team_code=str(self.code.value),
            create_code=False,
            change_only=False,
        )
        await interaction.response.send_message(
            i18n.t("customs.ok.pick_rank", self.lang),
            view=view,
            ephemeral=True,
        )


class RankSelect(discord.ui.Select):
    def __init__(
        self,
        cog: "CustomsCog",
        lobby_id: str,
        lang: str,
        *,
        team_code: str,
        create_code: bool,
        change_only: bool,
    ):
        options = [
            discord.SelectOption(label=r["name"], value=r["id"]) for r in customs_core.RANKS
        ]
        super().__init__(
            placeholder=i18n.t("customs.select.rank", lang)[:100],
            min_values=1,
            max_values=1,
            options=options,
        )
        self.cog = cog
        self.lobby_id = lobby_id
        self.lang = lang
        self.team_code = team_code
        self.create_code = create_code
        self.change_only = change_only

    async def callback(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None
        rank = customs_core.rank_by_id(self.values[0])
        if rank is None:
            return await interaction.response.send_message(
                i18n.t("customs.err.bad_rank", self.lang), ephemeral=True
            )
        settings = customs_core.get_settings(interaction.guild.id)
        member = interaction.user
        if isinstance(member, discord.Member):
            await assign_rank_roles(member, rank["id"], settings)

        if self.change_only:
            result = customs_core.set_player_rank(
                interaction.guild.id, self.lobby_id, interaction.user.id, rank
            )
            if result != "ok":
                return await interaction.response.send_message(
                    i18n.t("customs.err.not_in", self.lang), ephemeral=True
                )
            await interaction.response.edit_message(
                content=i18n.t("customs.ok.rank_set", self.lang, rank=rank["name"]),
                view=None,
            )
            await self.cog.refresh_lobby_message(interaction.guild, self.lobby_id)
            return

        status, lobby = customs_core.join_lobby(
            interaction.guild.id,
            self.lobby_id,
            interaction.user.id,
            rank,
            as_sub=False,
            team_code=self.team_code,
            create_code=self.create_code,
        )
        err_map = {
            "no_rank": "customs.err.need_rank",
            "already": "customs.err.already",
            "full": "customs.err.full",
            "closed": "customs.err.closed",
            "not_found": "customs.err.not_found",
            "bad_code": "customs.err.bad_code",
        }
        if status in err_map:
            return await interaction.response.send_message(
                i18n.t(err_map[status], self.lang), ephemeral=True
            )

        code = ""
        if lobby:
            uid = str(interaction.user.id)
            for p in (lobby.get("players") or []) + (lobby.get("subs") or []):
                if p.get("user_id") == uid:
                    code = str(p.get("team_code") or "")
                    break

        if status == "joined_sub":
            msg = i18n.t("customs.ok.joined_sub", self.lang)
        else:
            msg = i18n.t("customs.ok.joined", self.lang)
        if code:
            msg = i18n.t("customs.ok.joined_code", self.lang, code=code)

        await interaction.response.edit_message(content=msg, view=None)
        await self.cog.refresh_lobby_message(interaction.guild, self.lobby_id)


class RankSelectView(discord.ui.View):
    def __init__(
        self,
        cog: "CustomsCog",
        lobby_id: str,
        lang: str,
        *,
        team_code: str = "",
        create_code: bool = False,
        change_only: bool = False,
    ):
        super().__init__(timeout=120)
        self.add_item(
            RankSelect(
                cog,
                lobby_id,
                lang,
                team_code=team_code,
                create_code=create_code,
                change_only=change_only,
            )
        )


class _LobbyButton(discord.ui.Button):
    def __init__(
        self,
        *,
        label: str,
        style: discord.ButtonStyle,
        custom_id: str,
        row: int,
        handler: str,
    ):
        super().__init__(label=label, style=style, custom_id=custom_id, row=row)
        self.handler = handler

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        assert isinstance(view, CustomsLobbyView)
        await getattr(view, self.handler)(interaction)


class CustomsLobbyView(discord.ui.View):
    """Main lobby controls. Mode-specific rows; host actions gated in handlers."""

    def __init__(
        self,
        cog: "CustomsCog",
        *,
        join_mode: str | None = None,
        lang: str = "ru",
        status: str | None = None,
        show_back_to_lobby: bool | None = None,
    ):
        super().__init__(timeout=None)
        self.cog = cog
        mode = join_mode or customs_core.JOIN_MODE_SOLO
        live = status == customs_core.STATUS_LIVE
        if show_back_to_lobby is None:
            show_back_to_lobby = live
        if mode == customs_core.JOIN_MODE_TEAM_CODE:
            self.add_item(
                _LobbyButton(
                    label=i18n.t("customs.btn.create_code", lang),
                    style=discord.ButtonStyle.success,
                    custom_id=CID_CODE_CREATE,
                    row=0,
                    handler="on_create_code",
                )
            )
            self.add_item(
                _LobbyButton(
                    label=i18n.t("customs.btn.join_code", lang),
                    style=discord.ButtonStyle.primary,
                    custom_id=CID_CODE_JOIN,
                    row=0,
                    handler="on_join_code",
                )
            )
        else:
            self.add_item(
                _LobbyButton(
                    label=i18n.t("customs.btn.join", lang),
                    style=discord.ButtonStyle.success,
                    custom_id=CID_JOIN,
                    row=0,
                    handler="on_join",
                )
            )
        self.add_item(
            _LobbyButton(
                label=i18n.t("customs.btn.leave", lang),
                style=discord.ButtonStyle.danger,
                custom_id=CID_LEAVE,
                row=0,
                handler="on_leave",
            )
        )
        self.add_item(
            _LobbyButton(
                label=i18n.t("customs.btn.rank", lang),
                style=discord.ButtonStyle.secondary,
                custom_id=CID_RANK,
                row=0,
                handler="on_rank",
            )
        )
        self.add_item(
            _LobbyButton(
                label=i18n.t("customs.btn.balance", lang),
                style=discord.ButtonStyle.secondary,
                custom_id=CID_BALANCE,
                row=1,
                handler="on_balance",
            )
        )
        self.add_item(
            _LobbyButton(
                label=i18n.t("customs.btn.map", lang),
                style=discord.ButtonStyle.secondary,
                custom_id=CID_MAP,
                row=1,
                handler="on_map",
            )
        )
        self.add_item(
            _LobbyButton(
                label=i18n.t("customs.btn.finish" if live else "customs.btn.start", lang),
                style=discord.ButtonStyle.success,
                custom_id=CID_START,
                row=1,
                handler="on_start",
            )
        )
        self.add_item(
            _LobbyButton(
                label=i18n.t("customs.btn.cancel", lang),
                style=discord.ButtonStyle.danger,
                custom_id=CID_CANCEL,
                row=1,
                handler="on_cancel",
            )
        )
        if live:
            self.add_item(
                _LobbyButton(
                    label=i18n.t("customs.btn.score", lang),
                    style=discord.ButtonStyle.primary,
                    custom_id=CID_SCORE,
                    row=1,
                    handler="on_score",
                )
            )
        if show_back_to_lobby:
            # Row 2: live already fills row 1 (Balance/Map/Start/Cancel/Score).
            self.add_item(
                _LobbyButton(
                    label=i18n.t("customs.btn.back_lobby", lang),
                    style=discord.ButtonStyle.secondary,
                    custom_id=CID_BACK_LOBBY,
                    row=2,
                    handler="on_back_lobby",
                )
            )

    @classmethod
    def persistent(cls, cog: "CustomsCog") -> "CustomsLobbyView":
        """Register every lobby custom_id so restarts keep working for both modes."""
        view = cls.__new__(cls)
        discord.ui.View.__init__(view, timeout=None)
        view.cog = cog
        specs = [
            (i18n.t("customs.btn.join", "ru"), discord.ButtonStyle.success, CID_JOIN, 0, "on_join"),
            (
                i18n.t("customs.btn.create_code", "ru"),
                discord.ButtonStyle.success,
                CID_CODE_CREATE,
                0,
                "on_create_code",
            ),
            (
                i18n.t("customs.btn.join_code", "ru"),
                discord.ButtonStyle.primary,
                CID_CODE_JOIN,
                0,
                "on_join_code",
            ),
            (i18n.t("customs.btn.leave", "ru"), discord.ButtonStyle.danger, CID_LEAVE, 0, "on_leave"),
            (i18n.t("customs.btn.rank", "ru"), discord.ButtonStyle.secondary, CID_RANK, 0, "on_rank"),
            (
                i18n.t("customs.btn.balance", "ru"),
                discord.ButtonStyle.secondary,
                CID_BALANCE,
                1,
                "on_balance",
            ),
            (i18n.t("customs.btn.map", "ru"), discord.ButtonStyle.secondary, CID_MAP, 1, "on_map"),
            (i18n.t("customs.btn.start", "ru"), discord.ButtonStyle.success, CID_START, 1, "on_start"),
            (
                i18n.t("customs.btn.cancel", "ru"),
                discord.ButtonStyle.danger,
                CID_CANCEL,
                1,
                "on_cancel",
            ),
            (
                i18n.t("customs.btn.score", "ru"),
                discord.ButtonStyle.primary,
                CID_SCORE,
                1,
                "on_score",
            ),
            (
                i18n.t("customs.btn.back_lobby", "ru"),
                discord.ButtonStyle.secondary,
                CID_BACK_LOBBY,
                2,
                "on_back_lobby",
            ),
        ]
        for label, style, cid, row, handler in specs:
            view.add_item(_LobbyButton(label=label, style=style, custom_id=cid, row=row, handler=handler))
        return view

    def _lobby(self, interaction: discord.Interaction) -> dict | None:
        if interaction.message is None or interaction.guild_id is None:
            return None
        return customs_core.get_lobby_by_message(interaction.guild_id, interaction.message.id)

    async def _ephemeral(self, interaction: discord.Interaction, key: str, **kwargs) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        msg = i18n.t(key, lang, **kwargs)
        if interaction.response.is_done():
            await interaction.followup.send(msg, ephemeral=True)
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    def _send_rank_select(
        self,
        interaction: discord.Interaction,
        lobby_id: str,
        lang: str,
        *,
        team_code: str = "",
        create_code: bool = False,
        change_only: bool = False,
    ) -> Any:
        view = RankSelectView(
            self.cog,
            lobby_id,
            lang,
            team_code=team_code,
            create_code=create_code,
            change_only=change_only,
        )
        return interaction.response.send_message(
            i18n.t("customs.ok.pick_rank", lang),
            view=view,
            ephemeral=True,
        )

    async def on_join(self, interaction: discord.Interaction) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        lobby = self._lobby(interaction)
        if lobby is None or interaction.guild is None:
            return await self._ephemeral(interaction, "customs.err.not_found")
        settings = customs_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await self._ephemeral(interaction, "customs.err.disabled")
        mode = lobby.get("join_mode") or customs_core.JOIN_MODE_SOLO
        if mode == customs_core.JOIN_MODE_TEAM_CODE:
            return await self._ephemeral(interaction, "customs.err.use_team_buttons")
        return await self._send_rank_select(interaction, lobby["id"], lang)

    async def on_create_code(self, interaction: discord.Interaction) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        lobby = self._lobby(interaction)
        if lobby is None or interaction.guild is None:
            return await self._ephemeral(interaction, "customs.err.not_found")
        if (lobby.get("join_mode") or "") != customs_core.JOIN_MODE_TEAM_CODE:
            return await self._ephemeral(interaction, "customs.err.solo_mode")
        settings = customs_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await self._ephemeral(interaction, "customs.err.disabled")
        return await self._send_rank_select(interaction, lobby["id"], lang, create_code=True)

    async def on_join_code(self, interaction: discord.Interaction) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        lobby = self._lobby(interaction)
        if lobby is None:
            return await self._ephemeral(interaction, "customs.err.not_found")
        if (lobby.get("join_mode") or "") != customs_core.JOIN_MODE_TEAM_CODE:
            return await self._ephemeral(interaction, "customs.err.solo_mode")
        await interaction.response.send_modal(TeamCodeModal(self.cog, lobby["id"], lang))

    async def on_leave(self, interaction: discord.Interaction) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        lobby = self._lobby(interaction)
        if lobby is None or interaction.guild is None:
            return await self._ephemeral(interaction, "customs.err.not_found")
        result = customs_core.leave_lobby(interaction.guild.id, lobby["id"], interaction.user.id)
        if result != "left":
            return await self._ephemeral(interaction, "customs.err.not_in")
        await interaction.response.defer()
        await self.cog.refresh_lobby_message(interaction.guild, lobby["id"])
        await interaction.followup.send(i18n.t("customs.ok.left", lang), ephemeral=True)

    async def on_rank(self, interaction: discord.Interaction) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        lobby = self._lobby(interaction)
        if lobby is None or interaction.guild is None:
            return await self._ephemeral(interaction, "customs.err.not_found")
        uid = str(interaction.user.id)
        in_lobby = any(
            p["user_id"] == uid for p in (lobby.get("players") or []) + (lobby.get("subs") or [])
        )
        if not in_lobby:
            return await self._ephemeral(interaction, "customs.err.not_in")
        return await self._send_rank_select(interaction, lobby["id"], lang, change_only=True)

    async def on_balance(self, interaction: discord.Interaction) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        lobby = self._lobby(interaction)
        if lobby is None or interaction.guild is None:
            return await self._ephemeral(interaction, "customs.err.not_found")
        settings = customs_core.get_settings(interaction.guild.id)
        if not _is_host_or_mod(interaction.user, lobby, settings):  # type: ignore[arg-type]
            return await self._ephemeral(interaction, "customs.err.host_only")
        lobby = customs_core.apply_balance(interaction.guild.id, lobby["id"], 0)
        await interaction.response.defer()
        await self.cog.refresh_lobby_message(interaction.guild, lobby["id"] if lobby else "")
        await interaction.followup.send(i18n.t("customs.ok.balance", lang), ephemeral=True)

    async def on_map(self, interaction: discord.Interaction) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        lobby = self._lobby(interaction)
        if lobby is None or interaction.guild is None:
            return await self._ephemeral(interaction, "customs.err.not_found")
        settings = customs_core.get_settings(interaction.guild.id)
        if not _is_host_or_mod(interaction.user, lobby, settings):  # type: ignore[arg-type]
            return await self._ephemeral(interaction, "customs.err.host_only")

        await interaction.response.defer()
        if settings.get("features", {}).get("voting"):
            pool = customs_core.maps_for_pick(interaction.guild.id, lobby=lobby)
            last = settings.get("last_map_id") if settings.get("avoid_last_map", True) else ""
            candidates = [m for m in pool if m["id"] != last] or list(pool)
            random.shuffle(candidates)
            options = [{"id": m["id"], "label": m["name"]} for m in candidates[:5]]
            if not options:
                return await interaction.followup.send(
                    i18n.t("customs.err.not_found", lang), ephemeral=True
                )
            customs_core.start_vote(
                interaction.guild.id,
                lobby["id"],
                kind="map",
                options=options,
                seconds=settings.get("vote_seconds"),
            )
            await self.cog.post_map_vote(interaction.guild, lobby["id"])
            self.cog.schedule_vote_resolve(interaction.guild.id, lobby["id"])
            await interaction.followup.send(i18n.t("customs.ok.vote_map", lang), ephemeral=True)
            return

        chosen = customs_core.pick_random_map(interaction.guild.id, lobby=lobby)
        customs_core.update_lobby(
            interaction.guild.id, lobby["id"], map_id=chosen["id"], map_name=chosen["name"]
        )
        await self.cog.refresh_lobby_message(interaction.guild, lobby["id"])
        await interaction.followup.send(
            i18n.t("customs.ok.map", lang, map=chosen["name"]), ephemeral=True
        )

    async def on_start(self, interaction: discord.Interaction) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        lobby = self._lobby(interaction)
        if lobby is None or interaction.guild is None:
            return await self._ephemeral(interaction, "customs.err.not_found")
        settings = customs_core.get_settings(interaction.guild.id)
        if not _is_host_or_mod(interaction.user, lobby, settings):  # type: ignore[arg-type]
            return await self._ephemeral(interaction, "customs.err.host_only")

        # Live → finish + cleanup (same custom_id as start).
        if lobby.get("status") == customs_core.STATUS_LIVE:
            customs_core.finish_lobby(interaction.guild.id, lobby["id"])
            await interaction.response.defer()
            await self.cog.cleanup_lobby(interaction.guild, lobby["id"])
            await self.cog.refresh_lobby_message(interaction.guild, lobby["id"])
            await self.cog.finish_vote_message(interaction.guild, lobby["id"], delete=True)
            await self.cog.finish_score_message(interaction.guild, lobby["id"], delete=True)
            await self.cog.post_match_result(interaction.guild, lobby["id"])
            await interaction.followup.send(i18n.t("customs.ok.finished", lang), ephemeral=True)
            return

        if lobby.get("status") not in (
            customs_core.STATUS_OPEN,
            customs_core.STATUS_CHECKIN,
            customs_core.STATUS_READY,
        ):
            return await self._ephemeral(interaction, "customs.err.closed")
        if len(lobby.get("players") or []) < 2:
            return await self._ephemeral(interaction, "customs.err.need_players")
        if settings.get("features", {}).get("side_random") and not lobby.get("side"):
            customs_core.random_side(interaction.guild.id, lobby["id"])
            lobby = customs_core.get_lobby(interaction.guild.id, lobby["id"]) or lobby
        if not lobby.get("map_id"):
            chosen = customs_core.pick_random_map(interaction.guild.id, lobby=lobby)
            customs_core.update_lobby(
                interaction.guild.id, lobby["id"], map_id=chosen["id"], map_name=chosen["name"]
            )
            lobby = customs_core.get_lobby(interaction.guild.id, lobby["id"]) or lobby
        if not (lobby.get("team_a") or lobby.get("team_b")):
            customs_core.apply_balance(interaction.guild.id, lobby["id"], 0)
        customs_core.update_lobby(interaction.guild.id, lobby["id"], status=customs_core.STATUS_LIVE)
        await interaction.response.defer()
        move_note = await self.cog.setup_team_voice_on_start(interaction.guild, lobby["id"])
        await self.cog.refresh_lobby_message(interaction.guild, lobby["id"])
        await self.cog.announce_start(interaction.guild, lobby["id"])
        msg = i18n.t("customs.ok.started", lang)
        if move_note:
            msg = f"{msg}\n{move_note}"
        await interaction.followup.send(msg, ephemeral=True)

    async def on_score(self, interaction: discord.Interaction) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        lobby = self._lobby(interaction)
        if lobby is None or interaction.guild is None:
            return await self._ephemeral(interaction, "customs.err.not_found")
        settings = customs_core.get_settings(interaction.guild.id)
        if not _is_host_or_mod(interaction.user, lobby, settings):  # type: ignore[arg-type]
            return await self._ephemeral(interaction, "customs.err.host_only")
        if lobby.get("status") != customs_core.STATUS_LIVE:
            return await self._ephemeral(interaction, "customs.err.not_live")
        await interaction.response.defer()
        await self.cog.post_score_embed(interaction.guild, lobby["id"])
        await interaction.followup.send(i18n.t("customs.ok.score_posted", lang), ephemeral=True)

    async def on_back_lobby(self, interaction: discord.Interaction) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        lobby = self._lobby(interaction)
        if lobby is None or interaction.guild is None:
            return await self._ephemeral(interaction, "customs.err.not_found")
        settings = customs_core.get_settings(interaction.guild.id)
        if not _is_host_or_mod(interaction.user, lobby, settings):  # type: ignore[arg-type]
            return await self._ephemeral(interaction, "customs.err.host_only")
        if lobby.get("status") not in customs_core.ACTIVE_STATUSES:
            return await self._ephemeral(interaction, "customs.err.closed")
        await interaction.response.defer()
        move_note = await self.cog.move_players_to_waiting_lobby(interaction.guild, lobby["id"])
        await self.cog.refresh_lobby_message(interaction.guild, lobby["id"])
        await interaction.followup.send(move_note or i18n.t("customs.ok.back_ok", lang), ephemeral=True)

    async def on_cancel(self, interaction: discord.Interaction) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        lobby = self._lobby(interaction)
        if lobby is None or interaction.guild is None:
            return await self._ephemeral(interaction, "customs.err.not_found")
        settings = customs_core.get_settings(interaction.guild.id)
        if not _is_host_or_mod(interaction.user, lobby, settings):  # type: ignore[arg-type]
            return await self._ephemeral(interaction, "customs.err.host_only")
        customs_core.cancel_lobby(interaction.guild.id, lobby["id"])
        await interaction.response.defer()
        await self.cog.cleanup_lobby(interaction.guild, lobby["id"])
        await self.cog.refresh_lobby_message(interaction.guild, lobby["id"])
        await self.cog.finish_vote_message(interaction.guild, lobby["id"], delete=True)
        await self.cog.finish_score_message(interaction.guild, lobby["id"], delete=True)
        await interaction.followup.send(i18n.t("customs.ok.cancelled", lang), ephemeral=True)


class _MapVoteButton(discord.ui.Button):
    def __init__(self, index: int, *, label: str = "—"):
        super().__init__(
            label=label[:80],
            style=discord.ButtonStyle.secondary,
            custom_id=CID_MVOTE[index],
            row=0 if index < 5 else 1,
        )
        self.index = index

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        assert isinstance(view, CustomsMapVoteView)
        await view.on_vote(interaction, self.index)


class CustomsMapVoteView(discord.ui.View):
    """Separate map-vote message (not on the main lobby embed)."""

    def __init__(
        self,
        cog: "CustomsCog",
        *,
        options: list[dict[str, str]] | None = None,
        register_all: bool = False,
    ):
        super().__init__(timeout=None)
        self.cog = cog
        if register_all:
            for i in range(5):
                self.add_item(_MapVoteButton(i, label=f"#{i + 1}"))
            return
        for i, opt in enumerate((options or [])[:5]):
            self.add_item(_MapVoteButton(i, label=str(opt.get("label") or f"#{i + 1}")))

    @classmethod
    def persistent(cls, cog: "CustomsCog") -> "CustomsMapVoteView":
        return cls(cog, register_all=True)

    async def on_vote(self, interaction: discord.Interaction, index: int) -> None:
        if interaction.guild is None or interaction.message is None:
            lang = i18n.lang_for(interaction.guild_id)
            return await interaction.response.send_message(
                i18n.t("customs.err.not_found", lang), ephemeral=True
            )
        lobby = customs_core.get_lobby_by_vote_message(interaction.guild.id, interaction.message.id)
        if lobby is None:
            return await interaction.response.send_message(
                i18n.t("customs.err.not_found", i18n.lang_for(interaction.guild_id)),
                ephemeral=True,
            )
        vote = lobby.get("vote") or {}
        options = vote.get("options") or []
        if index >= len(options):
            return await interaction.response.send_message(
                i18n.t("customs.err.no_vote", i18n.lang_for(interaction.guild_id)),
                ephemeral=True,
            )
        result = customs_core.cast_vote(
            interaction.guild.id, lobby["id"], interaction.user.id, options[index]["id"]
        )
        lang = i18n.lang_for(interaction.guild_id)
        if result != "ok":
            key = f"customs.err.vote_{result}" if result != "not_found" else "customs.err.not_found"
            return await interaction.response.send_message(i18n.t(key, lang), ephemeral=True)
        await interaction.response.defer()
        await self.cog.refresh_vote_message(interaction.guild, lobby["id"])
        await interaction.followup.send(
            i18n.t("customs.ok.voted", lang, option=options[index].get("label") or ""),
            ephemeral=True,
        )


def _score_select_options() -> list[discord.SelectOption]:
    return [discord.SelectOption(label=f"13 : {n}", value=str(n)) for n in range(13)]


class ScoreModal(discord.ui.Modal):
    def __init__(self, cog: "CustomsCog", lobby_id: str, lang: str):
        super().__init__(title=i18n.t("customs.modal.score_title", lang)[:45])
        self.cog = cog
        self.lobby_id = lobby_id
        self.lang = lang
        self.score_a = discord.ui.TextInput(
            label=i18n.t("customs.modal.score_a", lang)[:45],
            required=True,
            max_length=2,
            placeholder="13",
        )
        self.score_b = discord.ui.TextInput(
            label=i18n.t("customs.modal.score_b", lang)[:45],
            required=True,
            max_length=2,
            placeholder="7",
        )
        self.add_item(self.score_a)
        self.add_item(self.score_b)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            a = int(str(self.score_a.value).strip())
            b = int(str(self.score_b.value).strip())
        except (TypeError, ValueError):
            return await interaction.response.send_message(
                i18n.t("customs.err.bad_score", self.lang), ephemeral=True
            )
        if a < 0 or b < 0 or a > 99 or b > 99:
            return await interaction.response.send_message(
                i18n.t("customs.err.bad_score", self.lang), ephemeral=True
            )
        if interaction.guild is None:
            return await interaction.response.send_message(
                i18n.t("customs.err.not_found", self.lang), ephemeral=True
            )
        await interaction.response.defer(ephemeral=True)
        ok = await self.cog.apply_match_score(interaction.guild, self.lobby_id, a, b)
        if not ok:
            await interaction.followup.send(i18n.t("customs.err.not_found", self.lang), ephemeral=True)
            return
        await interaction.followup.send(
            i18n.t("customs.ok.score_set", self.lang, a=a, b=b), ephemeral=True
        )


class _ScoreSelect(discord.ui.Select):
    def __init__(self, winner: str, lang: str = "ru"):
        super().__init__(
            placeholder=i18n.t(f"customs.score.select_{winner}", lang)[:100],
            custom_id=CID_SCORE_A if winner == "a" else CID_SCORE_B,
            min_values=1,
            max_values=1,
            options=_score_select_options(),
            row=0 if winner == "a" else 1,
        )
        self.winner = winner

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        assert isinstance(view, CustomsScoreView)
        await view.on_pick(interaction, self.winner, self.values[0])


class _ScoreModalButton(discord.ui.Button):
    def __init__(self, lang: str = "ru"):
        super().__init__(
            label=i18n.t("customs.btn.score_modal", lang)[:80],
            style=discord.ButtonStyle.secondary,
            custom_id=CID_SCORE_MODAL,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        assert isinstance(view, CustomsScoreView)
        await view.on_modal(interaction)


class CustomsScoreView(discord.ui.View):
    """Separate score embed (13–X selects + modal), not on the main lobby."""

    def __init__(self, cog: "CustomsCog", *, lang: str = "ru"):
        super().__init__(timeout=None)
        self.cog = cog
        self.add_item(_ScoreSelect("a", lang))
        self.add_item(_ScoreSelect("b", lang))
        self.add_item(_ScoreModalButton(lang))

    @classmethod
    def persistent(cls, cog: "CustomsCog") -> "CustomsScoreView":
        return cls(cog, lang="ru")

    def _lobby(self, interaction: discord.Interaction) -> dict | None:
        if interaction.guild is None or interaction.message is None:
            return None
        return customs_core.get_lobby_by_score_message(interaction.guild.id, interaction.message.id)

    async def on_pick(self, interaction: discord.Interaction, winner: str, loss_raw: str) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        lobby = self._lobby(interaction)
        if lobby is None or interaction.guild is None:
            return await interaction.response.send_message(
                i18n.t("customs.err.not_found", lang), ephemeral=True
            )
        settings = customs_core.get_settings(interaction.guild.id)
        if not _is_host_or_mod(interaction.user, lobby, settings):  # type: ignore[arg-type]
            return await interaction.response.send_message(
                i18n.t("customs.err.host_only", lang), ephemeral=True
            )
        if lobby.get("status") != customs_core.STATUS_LIVE:
            return await interaction.response.send_message(
                i18n.t("customs.err.not_live", lang), ephemeral=True
            )
        try:
            loss = int(loss_raw)
        except (TypeError, ValueError):
            return await interaction.response.send_message(
                i18n.t("customs.err.bad_score", lang), ephemeral=True
            )
        a, b = (13, loss) if winner == "a" else (loss, 13)
        await interaction.response.defer(ephemeral=True)
        ok = await self.cog.apply_match_score(interaction.guild, lobby["id"], a, b)
        key = "customs.ok.score_set" if ok else "customs.err.not_found"
        await interaction.followup.send(i18n.t(key, lang, a=a, b=b), ephemeral=True)

    async def on_modal(self, interaction: discord.Interaction) -> None:
        lang = i18n.lang_for(interaction.guild_id)
        lobby = self._lobby(interaction)
        if lobby is None or interaction.guild is None:
            return await interaction.response.send_message(
                i18n.t("customs.err.not_found", lang), ephemeral=True
            )
        settings = customs_core.get_settings(interaction.guild.id)
        if not _is_host_or_mod(interaction.user, lobby, settings):  # type: ignore[arg-type]
            return await interaction.response.send_message(
                i18n.t("customs.err.host_only", lang), ephemeral=True
            )
        await interaction.response.send_modal(ScoreModal(self.cog, lobby["id"], lang))


class CustomsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._vote_tasks: dict[str, asyncio.Task] = {}
        self._voice_refresh_tasks: dict[str, asyncio.Task] = {}
        self._synced_lobbies = False
        bot.add_view(CustomsLobbyView.persistent(self))
        bot.add_view(CustomsMapVoteView.persistent(self))
        bot.add_view(CustomsScoreView.persistent(self))
        self.schedule_sweeper.start()

    def cog_unload(self) -> None:
        self.schedule_sweeper.cancel()
        for task in list(self._vote_tasks.values()) + list(self._voice_refresh_tasks.values()):
            task.cancel()

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if self._synced_lobbies:
            return
        self._synced_lobbies = True
        for guild in self.bot.guilds:
            for lobby in customs_core.list_active_lobbies(guild.id):
                try:
                    await self.refresh_lobby_message(guild, lobby["id"])
                    vote = lobby.get("vote") or {}
                    if vote and not vote.get("applied"):
                        if lobby.get("vote_message_id"):
                            await self.refresh_vote_message(guild, lobby["id"])
                        else:
                            await self.post_map_vote(guild, lobby["id"])
                        self.schedule_vote_resolve(guild.id, lobby["id"])
                    if lobby.get("score_message_id") and lobby.get("status") == customs_core.STATUS_LIVE:
                        await self.refresh_score_message(guild, lobby["id"])
                except Exception:
                    logger.exception(
                        "customs on_ready sync failed guild=%s lobby=%s",
                        guild.id,
                        lobby.get("id"),
                    )

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        if member.bot or member.guild is None:
            return
        before_id = before.channel.id if before.channel else None
        after_id = after.channel.id if after.channel else None
        if before_id == after_id:
            return
        guild = member.guild
        uid = str(member.id)
        for lobby in customs_core.list_active_lobbies(guild.id):
            vc_ids = customs_core.lobby_voice_ids(lobby)
            if not vc_ids:
                continue
            roster = set(customs_core.lobby_participant_ids(lobby))
            if uid not in roster:
                continue
            if before_id in vc_ids or after_id in vc_ids:
                self._schedule_voice_refresh(guild, str(lobby["id"]))
                break

    def _schedule_voice_refresh(self, guild: discord.Guild, lobby_id: str) -> None:
        key = f"{guild.id}:{lobby_id}"
        prev = self._voice_refresh_tasks.get(key)
        if prev and not prev.done():
            return

        async def _run() -> None:
            try:
                await asyncio.sleep(VOICE_REFRESH_DEBOUNCE_SEC)
                await self.refresh_lobby_message(guild, lobby_id)
            except asyncio.CancelledError:
                return
            except Exception:
                logger.debug("customs voice refresh failed lobby=%s", lobby_id)
            finally:
                self._voice_refresh_tasks.pop(key, None)

        self._voice_refresh_tasks[key] = asyncio.create_task(_run())

    @tasks.loop(minutes=1)
    async def schedule_sweeper(self) -> None:
        try:
            for guild in self.bot.guilds:
                settings = customs_core.get_settings(guild.id)
                if not settings.get("enabled"):
                    continue
                for sch in customs_core.due_schedules(guild.id):
                    try:
                        await self.publish_scheduled(guild, sch)
                    except Exception:
                        logger.exception(
                            "customs schedule publish failed guild=%s schedule=%s",
                            guild.id,
                            sch.get("id"),
                        )
        except Exception:
            logger.exception("customs schedule sweeper error")

    @schedule_sweeper.before_loop
    async def before_schedule_sweeper(self) -> None:
        await self.bot.wait_until_ready()

    def lobby_view_for(self, lobby: dict, lang: str) -> CustomsLobbyView:
        mode = lobby.get("join_mode") or customs_core.JOIN_MODE_SOLO
        return CustomsLobbyView(
            self,
            join_mode=mode,
            lang=lang,
            status=str(lobby.get("status") or ""),
            show_back_to_lobby=_show_back_to_lobby(lobby),
        )

    def schedule_vote_resolve(self, guild_id: int, lobby_id: str) -> None:
        key = f"{guild_id}:{lobby_id}"
        prev = self._vote_tasks.get(key)
        if prev and not prev.done():
            prev.cancel()

        async def _run() -> None:
            lobby = customs_core.get_lobby(guild_id, lobby_id)
            if not lobby or not lobby.get("vote"):
                return
            ends = int((lobby["vote"] or {}).get("ends_at") or 0)
            delay = max(0, ends - int(time.time()))
            try:
                await asyncio.sleep(delay + 0.5)
            except asyncio.CancelledError:
                return
            lobby, winner = customs_core.resolve_vote(guild_id, lobby_id)
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                return
            await self.refresh_lobby_message(guild, lobby_id)
            winner_label = ""
            if lobby and winner:
                opts = (lobby.get("vote") or {}).get("options") or []
                winner_label = next((o.get("label") or "" for o in opts if o.get("id") == winner), "")
                if not winner_label and lobby.get("map_name"):
                    winner_label = str(lobby.get("map_name"))
            await self.finish_vote_message(guild, lobby_id, winner_label=winner_label)

        self._vote_tasks[key] = asyncio.create_task(_run())

    async def _fetch_text_channel(
        self, guild: discord.Guild, channel_id: str | int | None
    ) -> discord.TextChannel | None:
        if not channel_id:
            return None
        channel = guild.get_channel(int(channel_id))
        if channel is None:
            try:
                channel = await guild.fetch_channel(int(channel_id))
            except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                return None
        return channel if isinstance(channel, discord.TextChannel) else None

    async def refresh_lobby_message(self, guild: discord.Guild, lobby_id: str) -> None:
        if not lobby_id:
            return
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None:
            return
        lang = i18n.lang_for(guild.id)
        channel = await self._fetch_text_channel(guild, lobby.get("channel_id"))
        message_id = lobby.get("message_id")
        if channel is None or not message_id:
            return
        try:
            message = await channel.fetch_message(int(message_id))
        except (discord.NotFound, discord.HTTPException, discord.Forbidden):
            return
        embed = build_lobby_embed(lobby, lang, in_voice=in_voice_user_ids(guild, lobby))
        files = apply_map_image(embed, lobby)
        view = self.lobby_view_for(lobby, lang)
        try:
            if files:
                await message.edit(embed=embed, attachments=files, view=view)
            else:
                await message.edit(embed=embed, view=view)
        except discord.HTTPException:
            logger.exception("customs refresh failed lobby=%s", lobby_id)

    async def refresh_vote_message(self, guild: discord.Guild, lobby_id: str) -> None:
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None:
            return
        vote_mid = lobby.get("vote_message_id")
        if not vote_mid:
            return
        lang = i18n.lang_for(guild.id)
        channel = await self._fetch_text_channel(guild, lobby.get("channel_id"))
        if channel is None:
            return
        try:
            message = await channel.fetch_message(int(vote_mid))
        except (discord.NotFound, discord.HTTPException, discord.Forbidden):
            return
        vote = lobby.get("vote") or {}
        options = vote.get("options") or []
        embed = build_vote_embed(lobby, lang)
        view = CustomsMapVoteView(self, options=options)
        try:
            await message.edit(embed=embed, view=view)
        except discord.HTTPException:
            logger.exception("customs vote refresh failed lobby=%s", lobby_id)

    async def post_map_vote(self, guild: discord.Guild, lobby_id: str) -> None:
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None:
            return
        await self.finish_vote_message(guild, lobby_id, delete=True)
        lobby = customs_core.get_lobby(guild.id, lobby_id) or lobby
        lang = i18n.lang_for(guild.id)
        channel = await self._fetch_text_channel(guild, lobby.get("channel_id"))
        if channel is None:
            return
        vote = lobby.get("vote") or {}
        options = vote.get("options") or []
        if not options:
            return
        embed = build_vote_embed(lobby, lang)
        view = CustomsMapVoteView(self, options=options)
        try:
            message = await channel.send(embed=embed, view=view)
        except discord.HTTPException:
            logger.exception("customs vote post failed lobby=%s", lobby_id)
            return
        customs_core.update_lobby(guild.id, lobby_id, vote_message_id=str(message.id))

    async def finish_vote_message(
        self,
        guild: discord.Guild,
        lobby_id: str,
        *,
        winner_label: str = "",
        delete: bool = False,
    ) -> None:
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None:
            return
        vote_mid = lobby.get("vote_message_id")
        if not vote_mid:
            return
        channel = await self._fetch_text_channel(guild, lobby.get("channel_id"))
        if channel is None:
            customs_core.update_lobby(guild.id, lobby_id, vote_message_id="")
            return
        try:
            message = await channel.fetch_message(int(vote_mid))
        except (discord.NotFound, discord.HTTPException, discord.Forbidden):
            customs_core.update_lobby(guild.id, lobby_id, vote_message_id="")
            return
        try:
            if delete:
                await message.delete()
            else:
                lang = i18n.lang_for(guild.id)
                embed = build_vote_embed(lobby, lang, finished=True, winner_label=winner_label)
                await message.edit(embed=embed, view=None)
        except discord.HTTPException:
            logger.debug("customs: could not finish vote message lobby=%s", lobby_id)
        customs_core.update_lobby(guild.id, lobby_id, vote_message_id="")

    async def refresh_score_message(self, guild: discord.Guild, lobby_id: str) -> None:
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None:
            return
        score_mid = lobby.get("score_message_id")
        if not score_mid:
            return
        lang = i18n.lang_for(guild.id)
        channel = await self._fetch_text_channel(guild, lobby.get("channel_id"))
        if channel is None:
            return
        try:
            message = await channel.fetch_message(int(score_mid))
        except (discord.NotFound, discord.HTTPException, discord.Forbidden):
            return
        finished = lobby.get("status") == customs_core.STATUS_FINISHED
        embed = build_score_embed(lobby, lang, finished=finished)
        view = None if finished else CustomsScoreView(self, lang=lang)
        try:
            await message.edit(embed=embed, view=view)
        except discord.HTTPException:
            logger.exception("customs score refresh failed lobby=%s", lobby_id)

    async def post_score_embed(self, guild: discord.Guild, lobby_id: str) -> None:
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None:
            return
        await self.finish_score_message(guild, lobby_id, delete=True)
        lobby = customs_core.get_lobby(guild.id, lobby_id) or lobby
        lang = i18n.lang_for(guild.id)
        channel = await self._fetch_text_channel(guild, lobby.get("channel_id"))
        if channel is None:
            return
        embed = build_score_embed(lobby, lang)
        view = CustomsScoreView(self, lang=lang)
        try:
            message = await channel.send(embed=embed, view=view)
        except discord.HTTPException:
            logger.exception("customs score post failed lobby=%s", lobby_id)
            return
        customs_core.update_lobby(guild.id, lobby_id, score_message_id=str(message.id))

    async def finish_score_message(
        self,
        guild: discord.Guild,
        lobby_id: str,
        *,
        delete: bool = False,
    ) -> None:
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None:
            return
        score_mid = lobby.get("score_message_id")
        if not score_mid:
            return
        channel = await self._fetch_text_channel(guild, lobby.get("channel_id"))
        if channel is None:
            customs_core.update_lobby(guild.id, lobby_id, score_message_id="")
            return
        try:
            message = await channel.fetch_message(int(score_mid))
        except (discord.NotFound, discord.HTTPException, discord.Forbidden):
            customs_core.update_lobby(guild.id, lobby_id, score_message_id="")
            return
        try:
            if delete:
                await message.delete()
            else:
                lang = i18n.lang_for(guild.id)
                embed = build_score_embed(lobby, lang, finished=True)
                await message.edit(embed=embed, view=None)
        except discord.HTTPException:
            logger.debug("customs: could not finish score message lobby=%s", lobby_id)
        if delete:
            customs_core.update_lobby(guild.id, lobby_id, score_message_id="")

    async def apply_match_score(self, guild: discord.Guild, lobby_id: str, score_a: int, score_b: int) -> bool:
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None or lobby.get("status") != customs_core.STATUS_LIVE:
            return False
        updated = customs_core.set_result(guild.id, lobby_id, score_a, score_b)
        if updated is None:
            return False
        try:
            customs_core.award_xp_winners(guild.id, updated)
        except Exception:
            logger.debug("customs: xp award failed lobby=%s", lobby_id)
        await self.cleanup_lobby(guild, lobby_id)
        await self.refresh_lobby_message(guild, lobby_id)
        await self.finish_vote_message(guild, lobby_id, delete=True)
        await self.finish_score_message(guild, lobby_id, delete=False)
        await self.post_match_result(guild, lobby_id)
        return True

    async def post_match_result(self, guild: discord.Guild, lobby_id: str) -> None:
        settings = customs_core.get_settings(guild.id)
        channel = await self._fetch_text_channel(guild, settings.get("results_channel_id"))
        if channel is None:
            return
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None:
            return
        lang = i18n.lang_for(guild.id)
        embed = build_result_embed(lobby, lang)
        files = apply_map_image(embed, lobby)
        try:
            kwargs: dict[str, Any] = {"embed": embed}
            if files:
                kwargs["files"] = files
            await channel.send(**kwargs)
        except discord.HTTPException:
            logger.debug("customs: could not post result lobby=%s", lobby_id)

    async def announce_start(self, guild: discord.Guild, lobby_id: str) -> None:
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None:
            return
        settings = customs_core.get_settings(guild.id)
        content = ping_message_content(settings, lobby, include_participants=True)
        if not content:
            return
        channel = await self._fetch_text_channel(guild, lobby.get("channel_id"))
        if channel is None:
            return
        lang = i18n.lang_for(guild.id)
        try:
            await channel.send(f"{content}\n{i18n.t('customs.ok.started_public', lang)}")
        except discord.HTTPException:
            logger.debug("customs: could not announce start lobby=%s", lobby_id)

    async def publish_scheduled(self, guild: discord.Guild, sch: dict) -> None:
        import timezone_core

        settings = customs_core.get_settings(guild.id)
        channel_id = str(sch.get("channel_id") or settings.get("channel_id") or "")
        channel = await self._fetch_text_channel(guild, channel_id)
        if channel is None:
            return
        host_id = guild.me.id if guild.me is not None else guild.owner_id or 0
        lobby = customs_core.create_lobby(
            guild.id,
            host_id=int(host_id),
            name=str(sch.get("name") or settings.get("default_name") or "Кастомка"),
            notes=str(sch.get("notes") or settings.get("default_notes") or ""),
            join_mode=str(sch.get("join_mode") or settings.get("default_mode") or customs_core.JOIN_MODE_SOLO),
            ping=str(sch.get("ping") or settings.get("default_ping") or customs_core.PING_NONE),
            signup_minutes=int(sch.get("signup_minutes") or 0),
        )
        await self.publish_lobby(guild, lobby, channel)
        day_key = timezone_core.now_local(guild.id).strftime("%Y-%m-%d")
        customs_core.mark_schedule_run(guild.id, str(sch.get("id")), day_key)

    async def kick_and_refresh(self, guild: discord.Guild, lobby_id: str, user_id: int) -> str:
        result = customs_core.kick_player(guild.id, lobby_id, user_id)
        if result == "kicked":
            await self.refresh_lobby_message(guild, lobby_id)
        return result

    async def publish_lobby(
        self,
        guild: discord.Guild,
        lobby: dict,
        channel: discord.TextChannel,
        *,
        ping: str | None = None,
    ) -> discord.Message:
        if ping is not None:
            updated = customs_core.update_lobby(
                guild.id, lobby["id"], ping=customs_core._normalize_ping(ping)
            )
            if updated is not None:
                lobby = updated
        lang = i18n.lang_for(guild.id)
        embed = build_lobby_embed(lobby, lang)
        files = apply_map_image(embed, lobby)
        settings = customs_core.get_settings(guild.id)
        content = ping_message_content(settings, lobby, include_participants=False)
        view = self.lobby_view_for(lobby, lang)
        send_kwargs: dict[str, Any] = {"content": content, "embed": embed, "view": view}
        if files:
            send_kwargs["files"] = files
        message = await channel.send(**send_kwargs)
        customs_core.update_lobby(
            guild.id,
            lobby["id"],
            channel_id=str(channel.id),
            message_id=str(message.id),
        )
        await self.ensure_waiting_voice(guild, lobby["id"], announce_channel=channel)
        return message

    async def ensure_waiting_voice(
        self,
        guild: discord.Guild,
        lobby_id: str,
        *,
        announce_channel: discord.TextChannel | None = None,
        force: bool = False,
    ) -> discord.VoiceChannel | None:
        """Create waiting lobby VC and post a jump link in the announce chat."""
        settings = customs_core.get_settings(guild.id)
        if not force and not settings.get("auto_lobby_vc", True):
            return None
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None:
            return None
        existing = str(lobby.get("lobby_vc_id") or "")
        if existing.isdigit():
            ch = guild.get_channel(int(existing))
            if isinstance(ch, discord.VoiceChannel):
                return ch

        lang = i18n.lang_for(guild.id)
        if not _bot_can_manage_voice(guild):
            text_ch = announce_channel or await self._fetch_text_channel(guild, lobby.get("channel_id"))
            if text_ch is not None:
                try:
                    await text_ch.send(i18n.t("customs.err.voice_perms", lang))
                except discord.HTTPException:
                    pass
            return None

        category = _resolve_voice_category(guild, settings, announce_channel)
        name = i18n.t("customs.vc.lobby", lang, id=lobby_id)[:100]
        try:
            vc = await guild.create_voice_channel(
                name=name,
                category=category,
                reason=f"customs lobby #{lobby_id}",
            )
        except (discord.Forbidden, discord.HTTPException):
            logger.exception("customs: failed to create lobby VC guild=%s lobby=%s", guild.id, lobby_id)
            text_ch = announce_channel or await self._fetch_text_channel(guild, lobby.get("channel_id"))
            if text_ch is not None:
                try:
                    await text_ch.send(i18n.t("customs.err.voice_create", lang))
                except discord.HTTPException:
                    pass
            return None

        customs_core.update_lobby(guild.id, lobby_id, lobby_vc_id=str(vc.id))
        text_ch = announce_channel or await self._fetch_text_channel(guild, lobby.get("channel_id"))
        if text_ch is not None:
            try:
                await text_ch.send(i18n.t("customs.ok.lobby_vc", lang, mention=vc.mention))
            except discord.HTTPException:
                logger.debug("customs: could not post lobby VC link lobby=%s", lobby_id)
        return vc

    async def setup_team_voice_on_start(self, guild: discord.Guild, lobby_id: str) -> str:
        """Create team VCs and move players. Returns ephemeral note for the host."""
        settings = customs_core.get_settings(guild.id)
        lang = i18n.lang_for(guild.id)
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None:
            return ""

        if not settings.get("auto_move_on_start", True):
            return ""

        if not _bot_can_manage_voice(guild):
            return i18n.t("customs.err.voice_perms", lang)

        announce = await self._fetch_text_channel(guild, lobby.get("channel_id"))
        category = _resolve_voice_category(guild, settings, announce)
        # Prefer same category as waiting lobby VC when present.
        lobby_vc_raw = str(lobby.get("lobby_vc_id") or "")
        if lobby_vc_raw.isdigit():
            lobby_vc = guild.get_channel(int(lobby_vc_raw))
            if isinstance(lobby_vc, discord.VoiceChannel) and lobby_vc.category is not None:
                category = lobby_vc.category

        name_a, name_b = _team_vc_labels(lobby, lang)
        try:
            team_a_vc = await guild.create_voice_channel(
                name=name_a, category=category, reason=f"customs team A #{lobby_id}"
            )
            team_b_vc = await guild.create_voice_channel(
                name=name_b, category=category, reason=f"customs team B #{lobby_id}"
            )
        except (discord.Forbidden, discord.HTTPException):
            logger.exception("customs: failed to create team VCs lobby=%s", lobby_id)
            return i18n.t("customs.err.voice_create", lang)

        customs_core.update_lobby(
            guild.id,
            lobby_id,
            team_a_vc_id=str(team_a_vc.id),
            team_b_vc_id=str(team_b_vc.id),
        )

        failed_groups: list[tuple[discord.VoiceChannel, list[str]]] = []
        for team_key, vc in (("team_a", team_a_vc), ("team_b", team_b_vc)):
            ids = [
                str(p.get("user_id") or "")
                for p in (lobby.get(team_key) or [])
                if isinstance(p, dict)
            ]
            missed = await _move_user_ids_to_vc(
                guild, ids, vc, reason=f"customs start #{lobby_id}"
            )
            if missed:
                failed_groups.append((vc, missed))

        await _announce_move_failures(announce, guild, failed_groups, lang, lobby_id)

        failed_n = sum(len(uids) for _, uids in failed_groups)
        if failed_n:
            return i18n.t("customs.ok.move_partial", lang, n=failed_n)
        return i18n.t("customs.ok.move_ok", lang)

    async def move_players_to_waiting_lobby(self, guild: discord.Guild, lobby_id: str) -> str:
        """Move both teams back to the waiting lobby VC. Recreates it if deleted."""
        lang = i18n.lang_for(guild.id)
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None:
            return i18n.t("customs.err.not_found", lang)

        if not _bot_can_manage_voice(guild):
            return i18n.t("customs.err.voice_perms", lang)

        announce = await self._fetch_text_channel(guild, lobby.get("channel_id"))
        lobby_vc = await self.ensure_waiting_voice(
            guild, lobby_id, announce_channel=announce, force=True
        )
        if lobby_vc is None:
            return i18n.t("customs.err.voice_create", lang)

        lobby = customs_core.get_lobby(guild.id, lobby_id) or lobby
        user_ids = _match_team_user_ids(lobby)
        failed = await _move_user_ids_to_vc(
            guild, user_ids, lobby_vc, reason=f"customs back to lobby #{lobby_id}"
        )
        if failed:
            await _announce_move_failures(
                announce, guild, [(lobby_vc, failed)], lang, lobby_id
            )
            return i18n.t("customs.ok.move_partial", lang, n=len(failed))
        return i18n.t("customs.ok.back_ok", lang)

    async def cleanup_lobby(self, guild: discord.Guild, lobby_id: str) -> None:
        """Strip customs rank roles and delete lobby/team voice channels."""
        settings = customs_core.get_settings(guild.id)
        lobby = customs_core.get_lobby(guild.id, lobby_id)
        if lobby is None:
            return

        vc_ids = [
            str(lobby.get(key) or "")
            for key in ("lobby_vc_id", "team_a_vc_id", "team_b_vc_id")
            if str(lobby.get(key) or "").isdigit()
        ]

        for uid in customs_core.lobby_participant_ids(lobby):
            if not uid.isdigit():
                continue
            member = guild.get_member(int(uid))
            if member is None:
                continue
            await clear_customs_rank_roles(member, settings)

        if VC_CLEANUP_DELAY_SEC > 0:
            await asyncio.sleep(VC_CLEANUP_DELAY_SEC)

        for raw in vc_ids:
            ch = guild.get_channel(int(raw))
            if ch is None:
                try:
                    fetched = await guild.fetch_channel(int(raw))
                    ch = fetched if isinstance(fetched, discord.VoiceChannel) else None
                except (discord.NotFound, discord.HTTPException, discord.Forbidden):
                    ch = None
            if isinstance(ch, discord.VoiceChannel):
                try:
                    await ch.delete(reason=f"customs cleanup #{lobby_id}")
                except (discord.Forbidden, discord.HTTPException):
                    logger.debug("customs: could not delete VC %s lobby=%s", raw, lobby_id)

        customs_core.update_lobby(
            guild.id,
            lobby_id,
            lobby_vc_id="",
            team_a_vc_id="",
            team_b_vc_id="",
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(CustomsCog(bot))
