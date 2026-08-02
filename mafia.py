"""Ког игры «Мафия»: лобби, раздача ролей, ночь/день/голосование, персистентные View.

Ночные действия (мафия/доктор/шериф) собираются через персональную ссылку на
дашборд (см. dashboard/backend/routes/mafia.py) — POST-эндпоинт вызывает
maybe_finish_night_early ровно так же, как дашборд вызывает методы когов
других модулей (family.py -> bot.get_cog("FamilyTicketsCog")).

Таймеры переживают рестарт бота: phase_deadline_ts хранится в БД, on_ready
пересоздаёт задачи для всех активных игр (тот же паттерн, что и в supply.py).
"""

import asyncio
import logging
import os
import secrets
import time
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

import embed_style
import i18n
import slash_registry
import mafia_core
import mafia_db

logger = logging.getLogger("mafia")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


DEFAULT_FRONTEND_URL = "https://cheterin.online"


def _frontend_url() -> str:
    """Public dashboard origin for personal game links in DMs.

    Prefers DASHBOARD_FRONTEND_URL / FRONTEND_URL; falls back to production
    so relative paths like `/mafia/TOKEN` are never sent to players.
    """
    for key in ("DASHBOARD_FRONTEND_URL", "FRONTEND_URL"):
        value = (os.getenv(key) or "").strip().rstrip("/")
        if value:
            return value
    return DEFAULT_FRONTEND_URL


def _role_label(role: str, lang: str) -> str:
    key = f"mafia.role.{role}"
    text = i18n.t(key, lang)
    return text if text != key else role


def _resolve_alive_members(guild: discord.Guild | None, game_id: int) -> list[dict]:
    members = []
    for player in mafia_db.list_alive_players(game_id):
        member = guild.get_member(player["user_id"]) if guild else None
        display = (
            member.display_name
            if member
            else (player.get("display_name") or str(player["user_id"]))
        )
        members.append({"user_id": player["user_id"], "display_name": display})
    return members


def _display_name(guild: discord.Guild | None, user_id: int, stored: str | None = None) -> str:
    member = guild.get_member(user_id) if guild else None
    if member is not None:
        return member.display_name
    return stored or str(user_id)


def _player_display_name(guild: discord.Guild | None, player: dict) -> str:
    return _display_name(guild, player["user_id"], player.get("display_name"))


def _member_avatar_url(member: discord.abc.User | None) -> str | None:
    if member is None:
        return None
    avatar = getattr(member, "display_avatar", None)
    return str(avatar.url) if avatar is not None else None


def _refresh_player_avatars(guild: discord.Guild | None, game_id: int, player_ids: list[int]) -> None:
    for user_id in player_ids:
        member = guild.get_member(user_id) if guild else None
        avatar_url = _member_avatar_url(member)
        if avatar_url:
            mafia_db.set_player_avatar(game_id, user_id, avatar_url)


# ────────────────────────── Эмбеды ──────────────────────────

def build_lobby_embed(game: dict, players: list[dict], lang: str) -> discord.Embed:
    embed = discord.Embed(
        title=i18n.t("mafia.lobby.title", lang),
        description=i18n.t("mafia.lobby.description", lang),
        color=embed_style.INFO_INT,
    )
    embed.add_field(name=i18n.t("mafia.lobby.initiator", lang), value=f"<@{game['created_by']}>", inline=True)
    embed.add_field(
        name=i18n.t("mafia.lobby.players_needed", lang),
        value=f"{game['min_players']}–{game['max_players']}",
        inline=True,
    )
    embed.add_field(
        name=i18n.t("mafia.lobby.timers", lang),
        value=i18n.t(
            "mafia.lobby.timers_value",
            lang,
            night=game["night_timer_sec"],
            discussion=game["day_discussion_timer_sec"],
            vote=game["day_vote_timer_sec"],
        ),
        inline=True,
    )
    mentions = "\n".join(f"`{i + 1}.` <@{p['user_id']}>" for i, p in enumerate(players)) or "—"
    embed.add_field(
        name=i18n.t(
            "mafia.lobby.participants",
            lang,
            count=len(players),
            max=game["max_players"],
        ),
        value=mentions,
        inline=False,
    )
    return embed


def build_lobby_cancelled_embed(_game: dict, lang: str) -> discord.Embed:
    return discord.Embed(title=i18n.t("mafia.lobby.cancelled", lang), color=embed_style.NEUTRAL_INT)


def build_game_started_embed(
    game: dict, players: list[dict], voice_channel_id: int | None, lang: str
) -> discord.Embed:
    title_key = "mafia.started.title_test" if game.get("is_test") else "mafia.started.title"
    embed = discord.Embed(
        title=i18n.t(title_key, lang),
        description=i18n.t("mafia.started.description", lang),
        color=embed_style.DANGER_INT if game.get("is_test") else embed_style.INFO_INT,
    )
    embed.add_field(name=i18n.t("mafia.started.players", lang), value=str(len(players)), inline=True)
    if voice_channel_id:
        embed.add_field(
            name=i18n.t("mafia.started.voice_channel", lang),
            value=f"<#{voice_channel_id}>",
            inline=True,
        )
    embed.add_field(
        name="\u200b",
        value=i18n.t("mafia.started.round_night", lang, round=1, seconds=game["night_timer_sec"]),
        inline=False,
    )
    return embed


def build_morning_embed(died_id: int | None, died_player: dict | None, lang: str) -> discord.Embed:
    if died_id is None:
        return discord.Embed(
            title=i18n.t("mafia.morning.title", lang),
            description=i18n.t("mafia.morning.peaceful", lang),
            color=embed_style.SUCCESS_INT,
        )
    role = _role_label(died_player["role"], lang) if died_player else "?"
    return discord.Embed(
        title=i18n.t("mafia.morning.title", lang),
        description=i18n.t("mafia.morning.death", lang, user_id=died_id, role=role),
        color=embed_style.DANGER_INT,
    )


def build_vote_embed(game: dict, members: list[dict], votes: list[dict], lang: str) -> discord.Embed:
    embed = discord.Embed(
        title=i18n.t("mafia.vote.title", lang),
        description=i18n.t("mafia.vote.description", lang, seconds=game["day_vote_timer_sec"]),
        color=embed_style.GOLD_INT,
    )
    if not votes:
        embed.add_field(name=i18n.t("mafia.vote.votes", lang), value=i18n.t("mafia.vote.no_votes", lang), inline=False)
    else:
        tally: dict[str, int] = {}
        for vote in votes:
            key = (
                f"<@{vote['target_user_id']}>"
                if vote["target_user_id"]
                else i18n.t("mafia.vote.skip", lang)
            )
            tally[key] = tally.get(key, 0) + 1
        lines = [f"{name}: {count}" for name, count in sorted(tally.items(), key=lambda kv: -kv[1])]
        embed.add_field(name=i18n.t("mafia.vote.votes", lang), value="\n".join(lines), inline=False)
    embed.set_footer(text=i18n.t("mafia.vote.alive_footer", lang, count=len(members)))
    return embed


def build_lynch_result_embed(lynched_id: int | None, lynched_player: dict | None, lang: str) -> discord.Embed:
    if lynched_id is None:
        return discord.Embed(
            title=i18n.t("mafia.lynch.title", lang),
            description=i18n.t("mafia.lynch.no_majority", lang),
            color=embed_style.NEUTRAL_INT,
        )
    role = _role_label(lynched_player["role"], lang) if lynched_player else "?"
    return discord.Embed(
        title=i18n.t("mafia.lynch.title", lang),
        description=i18n.t("mafia.lynch.executed", lang, user_id=lynched_id, role=role),
        color=embed_style.DANGER_INT,
    )


def build_result_embed(winner: str | None, players: list[dict], lang: str) -> discord.Embed:
    if winner is None:
        title = i18n.t("mafia.result.stopped_title", lang)
        desc = i18n.t("mafia.result.stopped_desc", lang)
        color = embed_style.NEUTRAL_INT
    elif winner == "town":
        title = i18n.t("mafia.result.town_title", lang)
        desc = i18n.t("mafia.result.town_desc", lang)
        color = embed_style.SUCCESS_INT
    else:
        title = i18n.t("mafia.result.mafia_title", lang)
        desc = i18n.t("mafia.result.mafia_desc", lang)
        color = embed_style.DANGER_INT

    embed = discord.Embed(title=title, description=desc, color=color)
    lines = [
        f"<@{p['user_id']}> — {_role_label(p['role'] or 'citizen', lang)}" for p in players
    ]
    embed.add_field(name=i18n.t("mafia.result.roles", lang), value="\n".join(lines) or "—", inline=False)
    return embed


# ────────────────────────── Лобби ──────────────────────────

class MafiaLobbyView(discord.ui.View):
    def __init__(self, lang: str | None = None):
        super().__init__(timeout=None)
        self._default_lang = lang or i18n.DEFAULT_LANGUAGE
        self._add_button("mafia_lobby_join", "mafia.lobby.btn.join", discord.ButtonStyle.success, self._join)
        self._add_button("mafia_lobby_leave", "mafia.lobby.btn.leave", discord.ButtonStyle.secondary, self._leave)
        self._add_button(
            "mafia_lobby_force_start", "mafia.lobby.btn.force_start", discord.ButtonStyle.primary, self._force_start
        )
        self._add_button("mafia_lobby_cancel", "mafia.lobby.btn.cancel", discord.ButtonStyle.danger, self._cancel)

    def _add_button(self, custom_id: str, label_key: str, style: discord.ButtonStyle, callback):
        button = discord.ui.Button(
            label=i18n.t(label_key, self._default_lang),
            style=style,
            custom_id=custom_id,
        )
        button.callback = callback
        self.add_item(button)

    def _get_game(self, interaction: discord.Interaction) -> dict | None:
        if interaction.message is None:
            return None
        return mafia_db.get_game_by_lobby_message(interaction.message.id)

    async def _join(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message(
                i18n.t("mafia.lobby.unavailable", lang), ephemeral=True
            )
        if mafia_db.count_players(game["id"]) >= game["max_players"]:
            return await interaction.response.send_message(i18n.t("mafia.lobby.full", lang), ephemeral=True)
        if not mafia_db.add_player(game["id"], interaction.user.id, _member_avatar_url(interaction.user)):
            return await interaction.response.send_message(
                i18n.t("mafia.lobby.already_joined", lang), ephemeral=True
            )

        players = mafia_db.list_players(game["id"])
        await interaction.response.edit_message(embed=build_lobby_embed(game, players, lang))

        if len(players) >= game["max_players"]:
            cog = interaction.client.get_cog("MafiaCog")
            if cog:
                await cog.start_game(game["id"])

    async def _leave(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message(
                i18n.t("mafia.lobby.unavailable", lang), ephemeral=True
            )
        if not mafia_db.remove_player(game["id"], interaction.user.id):
            return await interaction.response.send_message(
                i18n.t("mafia.lobby.not_in_lobby", lang), ephemeral=True
            )
        players = mafia_db.list_players(game["id"])
        await interaction.response.edit_message(embed=build_lobby_embed(game, players, lang))

    async def _force_start(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message(
                i18n.t("mafia.lobby.unavailable", lang), ephemeral=True
            )
        if not mafia_core.has_moderator_access(interaction.user):
            return await interaction.response.send_message(i18n.t("mafia.lobby.no_access", lang), ephemeral=True)
        count = mafia_db.count_players(game["id"])
        if count < game["min_players"]:
            return await interaction.response.send_message(
                i18n.t("mafia.lobby.min_players", lang, min=game["min_players"], count=count),
                ephemeral=True,
            )
        await interaction.response.defer()
        cog = interaction.client.get_cog("MafiaCog")
        if cog:
            await cog.start_game(game["id"])

    async def _cancel(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message(
                i18n.t("mafia.lobby.unavailable", lang), ephemeral=True
            )
        if not mafia_core.has_moderator_access(interaction.user):
            return await interaction.response.send_message(i18n.t("mafia.lobby.no_access", lang), ephemeral=True)
        mafia_db.update_game(game["id"], status="cancelled", ended_at=_now_iso())
        await interaction.response.edit_message(embed=build_lobby_cancelled_embed(game, lang), view=None)


# ────────────────────────── Ког ──────────────────────────

class MafiaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._timers: dict[int, asyncio.Task] = {}
        self._recovered = False
        self.lobby_view = MafiaLobbyView()

    async def cog_load(self):
        self.bot.add_view(self.lobby_view)

    def cog_unload(self):
        for task in self._timers.values():
            task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if self._recovered:
            return
        self._recovered = True
        await self.recover_games()

    async def recover_games(self):
        recovered = 0
        for game in mafia_db.list_active_games():
            if game["status"] == "active" and game["phase"] in ("night", "day_discussion", "day_vote"):
                self.schedule_phase_timer(game["id"])
                recovered += 1
        if recovered:
            logger.info("Восстановлено активных игр «Мафия»: %s", recovered)

    # ────────────────────────── Команды ──────────────────────────

    @app_commands.command(name="мафия-игра", description="Создать лобби игры «Мафия»")
    @app_commands.describe(
        мин_игроков="Минимум игроков (5-99, по умолчанию из настроек модуля)",
        макс_игроков="Максимум игроков (5-99, по умолчанию из настроек модуля)",
        таймер_ночи="Таймер ночных действий, сек (по умолчанию из настроек)",
        таймер_обсуждения="Таймер дневного обсуждения, сек (по умолчанию из настроек)",
        таймер_голосования="Таймер дневного голосования, сек (по умолчанию из настроек)",
    )
    async def start_lobby(
        self,
        interaction: discord.Interaction,
        мин_игроков: app_commands.Range[int, mafia_core.PLAYERS_FLOOR, mafia_core.PLAYERS_CEIL] = None,
        макс_игроков: app_commands.Range[int, mafia_core.PLAYERS_FLOOR, mafia_core.PLAYERS_CEIL] = None,
        таймер_ночи: app_commands.Range[int, 10, 3600] = None,
        таймер_обсуждения: app_commands.Range[int, 10, 3600] = None,
        таймер_голосования: app_commands.Range[int, 10, 3600] = None,
    ):
        lang = i18n.lang_for(interaction.guild_id)
        settings = mafia_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "mafia"), ephemeral=True
            )

        if mafia_db.get_active_game_in_channel(interaction.channel.id) is not None:
            return await interaction.response.send_message(
                i18n.t("mafia.error.channel_busy", lang), ephemeral=True
            )

        min_players = мин_игроков if мин_игроков is not None else settings["default_min_players"]
        max_players = макс_игроков if макс_игроков is not None else settings["default_max_players"]
        if min_players > max_players:
            return await interaction.response.send_message(
                i18n.t("mafia.error.min_gt_max", lang), ephemeral=True
            )

        night_timer = таймер_ночи if таймер_ночи is not None else settings["default_night_timer_sec"]
        discussion_timer = (
            таймер_обсуждения if таймер_обсуждения is not None else settings["default_day_discussion_timer_sec"]
        )
        vote_timer = таймер_голосования if таймер_голосования is not None else settings["default_day_vote_timer_sec"]

        game = mafia_db.create_game(
            interaction.guild.id, interaction.channel.id, interaction.user.id,
            min_players, max_players, night_timer, discussion_timer, vote_timer,
        )
        mafia_db.add_player(game["id"], interaction.user.id, _member_avatar_url(interaction.user))
        players = mafia_db.list_players(game["id"])

        await interaction.response.send_message(
            embed=build_lobby_embed(game, players, lang), view=MafiaLobbyView(lang)
        )
        message = await interaction.original_response()
        mafia_db.update_game(game["id"], lobby_message_id=message.id)

    @app_commands.command(name="мафия-стоп", description="Остановить лобби/игру «Мафия» в этом канале")
    @app_commands.default_permissions(manage_guild=True)
    async def stop_game(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        game = mafia_db.get_active_game_in_channel(interaction.channel.id)
        if game is None:
            return await interaction.response.send_message(
                i18n.t("mafia.error.no_active_game", lang), ephemeral=True
            )
        if not mafia_core.has_moderator_access(interaction.user):
            return await interaction.response.send_message(i18n.t("mafia.lobby.no_access", lang), ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        guild_lang = i18n.lang_for(game["guild_id"])
        if game["status"] == "lobby":
            mafia_db.update_game(game["id"], status="cancelled", ended_at=_now_iso())
            channel = self.bot.get_channel(game["channel_id"])
            if channel is not None and game["lobby_message_id"]:
                try:
                    message = await channel.fetch_message(game["lobby_message_id"])
                    await message.edit(embed=build_lobby_cancelled_embed(game, guild_lang), view=None)
                except discord.HTTPException:
                    pass
        else:
            await self.end_game(game["id"], winner=None)
        await interaction.followup.send(i18n.t("mafia.stopped", lang), ephemeral=True)

    # ────────────────────────── Игровой цикл ──────────────────────────

    async def start_game(self, game_id: int):
        game = mafia_db.get_game(game_id)
        if game is None or game["status"] != "lobby":
            return
        guild = self.bot.get_guild(game["guild_id"])
        channel = self.bot.get_channel(game["channel_id"])
        if guild is None or channel is None:
            return

        lang = i18n.lang_for(game["guild_id"])
        players = mafia_db.list_players(game_id)
        player_ids = [p["user_id"] for p in players]
        _refresh_player_avatars(guild, game_id, player_ids)
        assignment = mafia_core.assign_roles(player_ids)
        for user_id, role in assignment.items():
            token = secrets.token_urlsafe(32)
            mafia_db.assign_player_role(game_id, user_id, role, token)

        voice_channel_id = None
        try:
            category = channel.category if isinstance(channel, discord.TextChannel) else None
            overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)}
            voice_name_key = "mafia.voice_channel_test" if game.get("is_test") else "mafia.voice_channel"
            voice_channel = await guild.create_voice_channel(
                name=i18n.t(voice_name_key, lang, game_id=game_id),
                overwrites=overwrites,
                category=category,
            )
            voice_channel_id = voice_channel.id
        except discord.HTTPException:
            logger.warning("Не удалось создать голосовой канал для игры «Мафия» #%s", game_id)

        now_ts = int(time.time())
        game = mafia_db.update_game(
            game_id, status="active", phase="night", round_number=1,
            phase_deadline_ts=now_ts + game["night_timer_sec"],
            voice_channel_id=voice_channel_id, started_at=_now_iso(),
        )

        frontend = _frontend_url()
        for user_id, role in assignment.items():
            member = guild.get_member(user_id)
            if member is None:
                continue
            player = mafia_db.get_player(game_id, user_id)
            link = f"{frontend}/mafia/{player['token']}"
            if role in mafia_core.NIGHT_ACTION_ROLES:
                note = i18n.t("mafia.dm.note_night", lang)
            else:
                note = i18n.t("mafia.dm.note_day", lang)
            try:
                await member.send(
                    content=i18n.t(
                        "mafia.dm.started",
                        lang,
                        role=_role_label(role, lang),
                        link=link,
                        note=note,
                    )
                )
            except discord.Forbidden:
                pass

        try:
            await channel.send(embed=build_game_started_embed(game, players, voice_channel_id, lang))
        except discord.HTTPException:
            pass

        self._add_event(
            game_id, 1, "game_started",
            i18n.t("mafia.event.game_started", lang, count=len(players)),
        )
        self.schedule_phase_timer(game_id)

    def schedule_phase_timer(self, game_id: int):
        old = self._timers.pop(game_id, None)
        if old:
            old.cancel()
        self._timers[game_id] = self.bot.loop.create_task(self._run_phase_timer(game_id))

    async def _run_phase_timer(self, game_id: int):
        try:
            game = mafia_db.get_game(game_id)
            if game is None or game["status"] != "active":
                return
            remaining = (game["phase_deadline_ts"] or 0) - int(time.time())
            if remaining > 0:
                await asyncio.sleep(remaining)

            game = mafia_db.get_game(game_id)
            if game is None or game["status"] != "active":
                return

            handlers = {
                "night": self._finish_night,
                "day_discussion": self._finish_day_discussion,
                "day_vote": self._finish_day_vote,
            }
            handler = handlers.get(game["phase"])
            if handler:
                await handler(game_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Mafia phase timer failed for game %s", game_id)

    def _cancel_timer(self, game_id: int):
        task = self._timers.pop(game_id, None)
        if task and task is not asyncio.current_task():
            task.cancel()

    def _check_winner(self, game_id: int) -> str | None:
        alive = mafia_db.list_alive_players(game_id)
        return mafia_core.check_win_condition([p["role"] for p in alive])

    def _add_event(self, game_id: int, round_number: int, event_type: str, payload: str = ""):
        mafia_db.add_round_event(game_id, round_number, event_type, payload)

    async def maybe_finish_night_early(self, game_id: int):
        """Вызывается дашбордом после каждой отправки ночного действия."""
        game = mafia_db.get_game(game_id)
        if game is None or game["status"] != "active" or game["phase"] != "night":
            return
        round_number = game["round_number"]
        actors = [p for p in mafia_db.list_alive_players(game_id) if p["role"] in mafia_core.NIGHT_ACTION_ROLES]
        if not actors:
            return await self._finish_night(game_id)
        submitted = {a["actor_user_id"] for a in mafia_db.get_night_actions(game_id, round_number)}
        if all(p["user_id"] in submitted for p in actors):
            await self._finish_night(game_id)

    async def maybe_finish_day_vote_early(self, game_id: int):
        """Вызывается дашбордом после каждой отправки дневного голоса."""
        game = mafia_db.get_game(game_id)
        if game is None or game["status"] != "active" or game["phase"] != "day_vote":
            return
        round_number = game["round_number"]
        alive = mafia_db.list_alive_players(game_id)
        if not alive:
            return await self._finish_day_vote(game_id)
        submitted = {v["voter_user_id"] for v in mafia_db.get_day_votes(game_id, round_number)}
        if all(p["user_id"] in submitted for p in alive):
            await self._finish_day_vote(game_id)

    async def refresh_vote_tally(self, game_id: int):
        game = mafia_db.get_game(game_id)
        if game is None or not game["vote_message_id"]:
            return
        channel = self.bot.get_channel(game["channel_id"])
        if channel is None:
            return
        guild = self.bot.get_guild(game["guild_id"])
        lang = i18n.lang_for(game["guild_id"])
        members = _resolve_alive_members(guild, game_id)
        votes = mafia_db.get_day_votes(game_id, game["round_number"])
        try:
            message = await channel.fetch_message(game["vote_message_id"])
            await message.edit(embed=build_vote_embed(game, members, votes, lang))
        except discord.HTTPException:
            pass

    async def force_advance_phase(self, game_id: int) -> bool:
        """Ведущий/админ форсирует переход фазы из дашборда, не дожидаясь таймера
        или всех действий/голосов. Возвращает False, если игра не активна."""
        game = mafia_db.get_game(game_id)
        if game is None or game["status"] != "active":
            return False
        handlers = {
            "night": self._finish_night,
            "day_discussion": self._finish_day_discussion,
            "day_vote": self._finish_day_vote,
        }
        handler = handlers.get(game["phase"])
        if handler is None:
            return False
        await handler(game_id)
        return True

    async def force_end_game(self, game_id: int) -> bool:
        """Ведущий/админ досрочно завершает игру из дашборда (без победителя)."""
        game = mafia_db.get_game(game_id)
        if game is None or game["status"] != "active":
            return False
        await self.end_game(game_id, None)
        return True

    async def _finish_night(self, game_id: int):
        game = mafia_db.get_game(game_id)
        if game is None or game["status"] != "active" or game["phase"] != "night":
            return
        self._cancel_timer(game_id)
        lang = i18n.lang_for(game["guild_id"])

        round_number = game["round_number"]
        actions = mafia_db.get_night_actions(game_id, round_number)
        by_role: dict[str, dict[int, int | None]] = {"mafia": {}, "doctor": {}, "sheriff": {}}
        for action in actions:
            if action["actor_role"] in by_role:
                by_role[action["actor_role"]][action["actor_user_id"]] = action["target_user_id"]

        kill_target = mafia_core.resolve_mafia_kill(by_role["mafia"])
        heal_target = next(iter(by_role["doctor"].values()), None)

        died = None
        if kill_target is not None and kill_target != heal_target:
            died = kill_target
            mafia_db.eliminate_player(game_id, died, round_number, "killed")

        for actor_id, target_id in by_role["sheriff"].items():
            if target_id is None:
                continue
            target_player = mafia_db.get_player(game_id, target_id)
            result = "mafia" if target_player and target_player["role"] == "mafia" else "not_mafia"
            mafia_db.set_night_action_result(game_id, round_number, actor_id, result)

        guild = self.bot.get_guild(game["guild_id"])
        channel = self.bot.get_channel(game["channel_id"])
        died_player = mafia_db.get_player(game_id, died) if died else None

        if channel is not None:
            try:
                await channel.send(embed=build_morning_embed(died, died_player, lang))
            except discord.HTTPException:
                pass

        self._add_event(
            game_id,
            round_number,
            "night_kill" if died else "night_no_kill",
            i18n.t("mafia.event.night_kill", lang, user_id=died)
            if died
            else i18n.t("mafia.event.night_peaceful", lang),
        )

        winner = self._check_winner(game_id)
        if winner:
            return await self.end_game(game_id, winner)

        now_ts = int(time.time())
        game = mafia_db.update_game(
            game_id, phase="day_discussion", phase_deadline_ts=now_ts + game["day_discussion_timer_sec"],
        )
        if channel is not None:
            voice_part = (
                i18n.t("mafia.phase.discussion_voice", lang, channel_id=game["voice_channel_id"])
                if game["voice_channel_id"]
                else ""
            )
            try:
                await channel.send(
                    content=i18n.t(
                        "mafia.phase.discussion",
                        lang,
                        voice=voice_part,
                        seconds=game["day_discussion_timer_sec"],
                    )
                )
            except discord.HTTPException:
                pass
        self.schedule_phase_timer(game_id)

    async def _finish_day_discussion(self, game_id: int):
        game = mafia_db.get_game(game_id)
        if game is None or game["status"] != "active" or game["phase"] != "day_discussion":
            return
        self._cancel_timer(game_id)
        lang = i18n.lang_for(game["guild_id"])

        guild = self.bot.get_guild(game["guild_id"])
        channel = self.bot.get_channel(game["channel_id"])
        members = _resolve_alive_members(guild, game_id)

        now_ts = int(time.time())
        game = mafia_db.update_game(
            game_id, phase="day_vote", phase_deadline_ts=now_ts + game["day_vote_timer_sec"],
        )

        message = None
        if channel is not None:
            try:
                await channel.send(content=i18n.t("mafia.phase.vote_open", lang))
                message = await channel.send(embed=build_vote_embed(game, members, [], lang))
            except discord.HTTPException:
                pass
        if message is not None:
            mafia_db.update_game(game_id, vote_message_id=message.id)

        self.schedule_phase_timer(game_id)

    async def _finish_day_vote(self, game_id: int):
        game = mafia_db.get_game(game_id)
        if game is None or game["status"] != "active" or game["phase"] != "day_vote":
            return
        self._cancel_timer(game_id)
        lang = i18n.lang_for(game["guild_id"])

        round_number = game["round_number"]
        votes = {v["voter_user_id"]: v["target_user_id"] for v in mafia_db.get_day_votes(game_id, round_number)}
        lynched = mafia_core.resolve_day_vote(votes)

        channel = self.bot.get_channel(game["channel_id"])

        if lynched is not None:
            mafia_db.eliminate_player(game_id, lynched, round_number, "lynched")
            self._add_event(
                game_id, round_number, "lynch",
                i18n.t("mafia.event.lynch", lang, user_id=lynched),
            )
        else:
            self._add_event(
                game_id, round_number, "no_lynch",
                i18n.t("mafia.event.no_lynch", lang),
            )

        if channel is not None:
            lynched_player = mafia_db.get_player(game_id, lynched) if lynched else None
            try:
                await channel.send(embed=build_lynch_result_embed(lynched, lynched_player, lang))
            except discord.HTTPException:
                pass

        winner = self._check_winner(game_id)
        if winner:
            return await self.end_game(game_id, winner)

        now_ts = int(time.time())
        game = mafia_db.update_game(
            game_id, phase="night", round_number=round_number + 1, phase_deadline_ts=now_ts + game["night_timer_sec"],
        )
        if channel is not None:
            try:
                await channel.send(
                    content=i18n.t(
                        "mafia.phase.night",
                        lang,
                        round=game["round_number"],
                        seconds=game["night_timer_sec"],
                    )
                )
            except discord.HTTPException:
                pass
        self.schedule_phase_timer(game_id)

    async def end_game(self, game_id: int, winner: str | None):
        game = mafia_db.get_game(game_id)
        if game is None:
            return
        self._cancel_timer(game_id)
        lang = i18n.lang_for(game["guild_id"])

        guild = self.bot.get_guild(game["guild_id"])
        channel = self.bot.get_channel(game["channel_id"])
        players = mafia_db.list_players(game_id)

        mafia_db.update_game(game_id, status="finished", phase="ended", winner=winner, ended_at=_now_iso())

        if channel is not None:
            try:
                await channel.send(embed=build_result_embed(winner, players, lang))
            except discord.HTTPException:
                pass

        if game["voice_channel_id"] and guild is not None:
            voice_channel = guild.get_channel(game["voice_channel_id"])
            if voice_channel is not None:
                try:
                    await voice_channel.delete(reason=i18n.t("mafia.voice_delete_reason", lang))
                except discord.HTTPException:
                    pass

        winner_text = (
            winner
            if winner
            else i18n.t("mafia.event.winner_stopped", lang)
        )
        self._add_event(
            game_id, game["round_number"], "game_ended",
            i18n.t("mafia.event.game_ended", lang, winner=winner_text),
        )
        await self._send_log(game, winner, lang)

    async def _send_log(self, game: dict, winner: str | None, lang: str):
        log_channel_id = mafia_core.get_settings(game["guild_id"])["log_channel_id"]
        if not log_channel_id:
            return
        channel = self.bot.get_channel(int(log_channel_id))
        if channel is None:
            return
        winner_text = winner or i18n.t("mafia.log.winner_stopped", lang)
        text = i18n.t(
            "mafia.log.finished",
            lang,
            game_id=game["id"],
            channel_id=game["channel_id"],
            winner=winner_text,
        )
        try:
            await channel.send(content=text)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    mafia_db.init()
    cog = MafiaCog(bot)
    slash_registry.register_mafia(cog)
    await bot.add_cog(cog)
