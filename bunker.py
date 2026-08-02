"""Ког игры «Бункер»: лобби, раздача карточек персонажей, раунды обсуждение/голосование.

Раскрытие характеристик, голосование за исключение и заявки на спец. возможности
собираются через персональную ссылку на дашборд (см. dashboard/backend/routes/bunker.py) —
POST-эндпоинты вызывают методы этого кога ровно так же, как дашборд вызывает методы
когов других модулей (mafia.py -> maybe_finish_night_early).

Таймеры переживают рестарт бота: phase_deadline_ts хранится в БД, on_ready
пересоздаёт задачи для всех активных игр (тот же паттерн, что и в mafia.py).
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

import bunker_core
import embed_style
import bunker_db
import bunker_localize
import i18n
import slash_registry

logger = logging.getLogger("bunker")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


DEFAULT_FRONTEND_URL = "https://cheterin.online"


def _frontend_url() -> str:
    """Public dashboard origin for personal game links in DMs.

    Prefers DASHBOARD_FRONTEND_URL / FRONTEND_URL; falls back to production
    so relative paths like `/bunker/TOKEN` are never sent to players.
    """
    for key in ("DASHBOARD_FRONTEND_URL", "FRONTEND_URL"):
        value = (os.getenv(key) or "").strip().rstrip("/")
        if value:
            return value
    return DEFAULT_FRONTEND_URL


def _resolve_alive_members(guild: discord.Guild | None, game_id: int) -> list[dict]:
    members = []
    for player in bunker_db.list_alive_players(game_id):
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
            bunker_db.set_player_avatar(game_id, user_id, avatar_url)


# ────────────────────────── Эмбеды ──────────────────────────

def build_lobby_embed(game: dict, players: list[dict], lang: str) -> discord.Embed:
    embed = discord.Embed(
        title=i18n.t("bunker.lobby.title", lang),
        description=i18n.t("bunker.lobby.description", lang),
        color=embed_style.INFO_INT,
    )
    embed.add_field(name=i18n.t("bunker.lobby.initiator", lang), value=f"<@{game['created_by']}>", inline=True)
    embed.add_field(
        name=i18n.t("bunker.lobby.players_needed", lang),
        value=f"{game['min_players']}–{game['max_players']}",
        inline=True,
    )
    embed.add_field(
        name=i18n.t("bunker.lobby.timers", lang),
        value=i18n.t(
            "bunker.lobby.timers_value",
            lang,
            discussion=game["discussion_timer_sec"],
            vote=game["vote_timer_sec"],
        ),
        inline=True,
    )
    if game["bunker_capacity"]:
        embed.add_field(
            name=i18n.t("bunker.lobby.capacity", lang),
            value=str(game["bunker_capacity"]),
            inline=True,
        )
    cards_key = "bunker.lobby.cards_unique" if game["unique_cards"] else "bunker.lobby.cards_repeat"
    embed.add_field(name=i18n.t("bunker.lobby.cards", lang), value=i18n.t(cards_key, lang), inline=True)
    mentions = "\n".join(f"`{i + 1}.` <@{p['user_id']}>" for i, p in enumerate(players)) or "—"
    embed.add_field(
        name=i18n.t(
            "bunker.lobby.participants",
            lang,
            count=len(players),
            max=game["max_players"],
        ),
        value=mentions,
        inline=False,
    )
    return embed


def build_lobby_cancelled_embed(_game: dict, lang: str) -> discord.Embed:
    return discord.Embed(title=i18n.t("bunker.lobby.cancelled", lang), color=embed_style.NEUTRAL_INT)


def build_game_started_embed(
    game: dict, players: list[dict], voice_channel_id: int | None, lang: str
) -> discord.Embed:
    cat_name, cat_desc, cond_name, cond_desc = bunker_localize.localize_game_scenario(game, lang)
    title_key = "bunker.started.title_test" if game.get("is_test") else "bunker.started.title"
    embed = discord.Embed(
        title=i18n.t(title_key, lang),
        description=i18n.t("bunker.started.description", lang),
        color=embed_style.DANGER_INT if game.get("is_test") else embed_style.INFO_INT,
    )
    embed.add_field(name=i18n.t("bunker.started.players", lang), value=str(len(players)), inline=True)
    embed.add_field(
        name=i18n.t("bunker.started.capacity", lang),
        value=str(game["bunker_capacity"]),
        inline=True,
    )
    if voice_channel_id:
        embed.add_field(
            name=i18n.t("bunker.started.voice_channel", lang),
            value=f"<#{voice_channel_id}>",
            inline=True,
        )
    embed.add_field(
        name=i18n.t("bunker.started.catastrophe", lang),
        value=f"**{cat_name}**\n{cat_desc}",
        inline=False,
    )
    embed.add_field(
        name=i18n.t("bunker.started.conditions", lang),
        value=f"**{cond_name}**\n{cond_desc}",
        inline=False,
    )
    embed.add_field(
        name="\u200b",
        value=i18n.t(
            "bunker.started.round_discussion",
            lang,
            round=1,
            seconds=game["discussion_timer_sec"],
        ),
        inline=False,
    )
    return embed


def build_vote_embed(game: dict, members: list[dict], votes: list[dict], lang: str) -> discord.Embed:
    embed = discord.Embed(
        title=i18n.t("bunker.vote.title", lang),
        description=i18n.t("bunker.vote.description", lang, seconds=game["vote_timer_sec"]),
        color=embed_style.GOLD_INT,
    )
    if not votes:
        embed.add_field(
            name=i18n.t("bunker.vote.votes", lang),
            value=i18n.t("bunker.vote.no_votes", lang),
            inline=False,
        )
    else:
        tally: dict[str, int] = {}
        for vote in votes:
            key = (
                f"<@{vote['target_user_id']}>"
                if vote["target_user_id"]
                else i18n.t("bunker.vote.skip", lang)
            )
            tally[key] = tally.get(key, 0) + 1
        lines = [f"{name}: {count}" for name, count in sorted(tally.items(), key=lambda kv: -kv[1])]
        embed.add_field(name=i18n.t("bunker.vote.votes", lang), value="\n".join(lines), inline=False)
    embed.set_footer(text=i18n.t("bunker.vote.alive_footer", lang, count=len(members)))
    return embed


def build_expulsion_result_embed(expelled_id: int | None, lang: str) -> discord.Embed:
    if expelled_id is None:
        return discord.Embed(
            title=i18n.t("bunker.expulsion.title", lang),
            description=i18n.t("bunker.expulsion.no_majority", lang),
            color=embed_style.NEUTRAL_INT,
        )
    return discord.Embed(
        title=i18n.t("bunker.expulsion.title", lang),
        description=i18n.t("bunker.expulsion.expelled", lang, user_id=expelled_id),
        color=embed_style.DANGER_INT,
    )


def _character_summary(character: dict, lang: str) -> str:
    if not character:
        return "—"
    character = bunker_localize.localize_character(character, lang) or character
    return (
        f"{character['profession']['name']} ({character['profession']['experience_level']}), "
        f"{character['age']['label']}, {character['gender']}"
    )


def build_result_embed(players: list[dict], lang: str, stopped: bool = False) -> discord.Embed:
    if stopped:
        title = i18n.t("bunker.result.stopped_title", lang)
        desc = i18n.t("bunker.result.stopped_desc", lang)
        color = embed_style.NEUTRAL_INT
    else:
        title = i18n.t("bunker.result.finished_title", lang)
        desc = i18n.t("bunker.result.finished_desc", lang)
        color = embed_style.SUCCESS_INT

    embed = discord.Embed(title=title, description=desc, color=color)
    survivors = [p for p in players if p["alive"]]
    eliminated = [p for p in players if not p["alive"]]
    if survivors:
        lines = [f"<@{p['user_id']}> — {_character_summary(p['character'], lang)}" for p in survivors]
        embed.add_field(name=i18n.t("bunker.result.survivors", lang), value="\n".join(lines), inline=False)
    if eliminated:
        lines = [f"<@{p['user_id']}> — {_character_summary(p['character'], lang)}" for p in eliminated]
        embed.add_field(name=i18n.t("bunker.result.eliminated", lang), value="\n".join(lines), inline=False)
    return embed


# ────────────────────────── Лобби ──────────────────────────

class BunkerLobbyView(discord.ui.View):
    def __init__(self, lang: str | None = None):
        super().__init__(timeout=None)
        self._default_lang = lang or i18n.DEFAULT_LANGUAGE
        self._add_button("bunker_lobby_join", "bunker.lobby.btn.join", discord.ButtonStyle.success, self._join)
        self._add_button("bunker_lobby_leave", "bunker.lobby.btn.leave", discord.ButtonStyle.secondary, self._leave)
        self._add_button(
            "bunker_lobby_force_start", "bunker.lobby.btn.force_start", discord.ButtonStyle.primary, self._force_start
        )
        self._add_button("bunker_lobby_cancel", "bunker.lobby.btn.cancel", discord.ButtonStyle.danger, self._cancel)

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
        return bunker_db.get_game_by_lobby_message(interaction.message.id)

    async def _join(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message(
                i18n.t("bunker.lobby.unavailable", lang), ephemeral=True
            )
        if bunker_db.count_players(game["id"]) >= game["max_players"]:
            return await interaction.response.send_message(i18n.t("bunker.lobby.full", lang), ephemeral=True)
        if not bunker_db.add_player(game["id"], interaction.user.id, _member_avatar_url(interaction.user)):
            return await interaction.response.send_message(
                i18n.t("bunker.lobby.already_joined", lang), ephemeral=True
            )

        players = bunker_db.list_players(game["id"])
        await interaction.response.edit_message(embed=build_lobby_embed(game, players, lang))

        if len(players) >= game["max_players"]:
            cog = interaction.client.get_cog("BunkerCog")
            if cog:
                await cog.start_game(game["id"])

    async def _leave(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message(
                i18n.t("bunker.lobby.unavailable", lang), ephemeral=True
            )
        if not bunker_db.remove_player(game["id"], interaction.user.id):
            return await interaction.response.send_message(
                i18n.t("bunker.lobby.not_in_lobby", lang), ephemeral=True
            )
        players = bunker_db.list_players(game["id"])
        await interaction.response.edit_message(embed=build_lobby_embed(game, players, lang))

    async def _force_start(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message(
                i18n.t("bunker.lobby.unavailable", lang), ephemeral=True
            )
        if not bunker_core.has_moderator_access(interaction.user):
            return await interaction.response.send_message(i18n.t("bunker.lobby.no_access", lang), ephemeral=True)
        count = bunker_db.count_players(game["id"])
        if count < game["min_players"]:
            return await interaction.response.send_message(
                i18n.t("bunker.lobby.min_players", lang, min=game["min_players"], count=count),
                ephemeral=True,
            )
        await interaction.response.defer()
        cog = interaction.client.get_cog("BunkerCog")
        if cog:
            await cog.start_game(game["id"])

    async def _cancel(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message(
                i18n.t("bunker.lobby.unavailable", lang), ephemeral=True
            )
        if not bunker_core.has_moderator_access(interaction.user):
            return await interaction.response.send_message(i18n.t("bunker.lobby.no_access", lang), ephemeral=True)
        bunker_db.update_game(game["id"], status="cancelled", ended_at=_now_iso())
        await interaction.response.edit_message(embed=build_lobby_cancelled_embed(game, lang), view=None)


# ────────────────────────── Ког ──────────────────────────

class BunkerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._timers: dict[int, asyncio.Task] = {}
        self._phase_locks: dict[int, asyncio.Lock] = {}
        self._recovered = False
        self.lobby_view = BunkerLobbyView()

    def _phase_lock(self, game_id: int) -> asyncio.Lock:
        lock = self._phase_locks.get(game_id)
        if lock is None:
            lock = asyncio.Lock()
            self._phase_locks[game_id] = lock
        return lock

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
        for game in bunker_db.list_active_games():
            if game["status"] == "active" and game["phase"] in ("discussion", "vote"):
                self.schedule_phase_timer(game["id"])
                recovered += 1
        if recovered:
            logger.info("Восстановлено активных игр «Бункер»: %s", recovered)

    # ────────────────────────── Команды ──────────────────────────

    @app_commands.command(name="бункер-игра", description="Создать лобби игры «Бункер»")
    @app_commands.describe(
        мин_игроков="Минимум игроков (по умолчанию из настроек модуля)",
        макс_игроков="Максимум игроков (по умолчанию из настроек модуля)",
        вместимость_бункера="Сколько игроков выживет (по умолчанию — половина от итогового числа игроков)",
        таймер_обсуждения="Таймер обсуждения/раскрытия характеристик, сек (по умолчанию из настроек)",
        таймер_голосования="Таймер голосования за исключение, сек (по умолчанию из настроек)",
        уникальные_карты="Раздавать карточки без повторов, как колодой (по умолчанию из настроек — обычно включено)",
    )
    async def start_lobby(
        self,
        interaction: discord.Interaction,
        мин_игроков: app_commands.Range[int, bunker_core.PLAYERS_FLOOR, bunker_core.PLAYERS_CEIL] = None,
        макс_игроков: app_commands.Range[int, bunker_core.PLAYERS_FLOOR, bunker_core.PLAYERS_CEIL] = None,
        вместимость_бункера: app_commands.Range[int, 1, bunker_core.PLAYERS_CEIL] = None,
        таймер_обсуждения: app_commands.Range[int, 10, 3600] = None,
        таймер_голосования: app_commands.Range[int, 10, 3600] = None,
        уникальные_карты: bool = None,
    ):
        lang = i18n.lang_for(interaction.guild_id)
        settings = bunker_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "bunker"), ephemeral=True
            )

        if bunker_db.get_active_game_in_channel(interaction.channel.id) is not None:
            return await interaction.response.send_message(
                i18n.t("bunker.error.channel_busy", lang), ephemeral=True
            )

        min_players = мин_игроков if мин_игроков is not None else settings["default_min_players"]
        max_players = макс_игроков if макс_игроков is not None else settings["default_max_players"]
        if min_players > max_players:
            return await interaction.response.send_message(
                i18n.t("bunker.error.min_gt_max", lang), ephemeral=True
            )
        if вместимость_бункера is not None and вместимость_бункера >= max_players:
            return await interaction.response.send_message(
                i18n.t("bunker.error.capacity_too_high", lang), ephemeral=True
            )

        discussion_timer = таймер_обсуждения if таймер_обсуждения is not None else settings["default_discussion_timer_sec"]
        vote_timer = таймер_голосования if таймер_голосования is not None else settings["default_vote_timer_sec"]
        unique_cards = уникальные_карты if уникальные_карты is not None else settings["default_unique_cards"]

        game = bunker_db.create_game(
            interaction.guild.id, interaction.channel.id, interaction.user.id,
            min_players, max_players, discussion_timer, vote_timer, unique_cards,
        )
        if вместимость_бункера is not None:
            game = bunker_db.update_game(game["id"], bunker_capacity=вместимость_бункера)
        bunker_db.add_player(game["id"], interaction.user.id, _member_avatar_url(interaction.user))
        players = bunker_db.list_players(game["id"])

        await interaction.response.send_message(
            embed=build_lobby_embed(game, players, lang), view=BunkerLobbyView(lang)
        )
        message = await interaction.original_response()
        bunker_db.update_game(game["id"], lobby_message_id=message.id)

    @app_commands.command(name="бункер-стоп", description="Остановить лобби/игру «Бункер» в этом канале")
    @app_commands.default_permissions(manage_guild=True)
    async def stop_game(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        game = bunker_db.get_active_game_in_channel(interaction.channel.id)
        if game is None:
            return await interaction.response.send_message(
                i18n.t("bunker.error.no_active_game", lang), ephemeral=True
            )
        if not bunker_core.has_moderator_access(interaction.user):
            return await interaction.response.send_message(i18n.t("bunker.lobby.no_access", lang), ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        guild_lang = i18n.lang_for(game["guild_id"])
        if game["status"] == "lobby":
            bunker_db.update_game(game["id"], status="cancelled", ended_at=_now_iso())
            channel = self.bot.get_channel(game["channel_id"])
            if channel is not None and game["lobby_message_id"]:
                try:
                    message = await channel.fetch_message(game["lobby_message_id"])
                    await message.edit(embed=build_lobby_cancelled_embed(game, guild_lang), view=None)
                except discord.HTTPException:
                    pass
        else:
            await self.end_game(game["id"], stopped=True)
        await interaction.followup.send(i18n.t("bunker.stopped", lang), ephemeral=True)

    # ────────────────────────── Игровой цикл ──────────────────────────

    async def start_game(self, game_id: int):
        game = bunker_db.get_game(game_id)
        if game is None or game["status"] != "lobby":
            return
        guild = self.bot.get_guild(game["guild_id"])
        channel = self.bot.get_channel(game["channel_id"])
        if guild is None or channel is None:
            return

        lang = i18n.lang_for(game["guild_id"])
        players = bunker_db.list_players(game_id)
        player_ids = [p["user_id"] for p in players]
        _refresh_player_avatars(guild, game_id, player_ids)
        display_names = {
            p["user_id"]: _player_display_name(guild, p) for p in players
        }

        bunker_capacity = game["bunker_capacity"] or bunker_core.default_bunker_capacity(len(player_ids))
        if bunker_capacity >= len(player_ids):
            bunker_capacity = bunker_core.default_bunker_capacity(len(player_ids))

        characters = bunker_core.generate_characters(player_ids, display_names, unique_cards=bool(game["unique_cards"]))
        for user_id, character in characters.items():
            token = secrets.token_urlsafe(32)
            bunker_db.assign_character(game_id, user_id, character, token)

        catastrophe = bunker_core.pick_catastrophe()
        conditions = bunker_core.pick_bunker_conditions()

        voice_channel_id = None
        try:
            category = channel.category if isinstance(channel, discord.TextChannel) else None
            overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)}
            voice_name_key = "bunker.voice_channel_test" if game.get("is_test") else "bunker.voice_channel"
            voice_channel = await guild.create_voice_channel(
                name=i18n.t(voice_name_key, lang, game_id=game_id),
                overwrites=overwrites,
                category=category,
            )
            voice_channel_id = voice_channel.id
        except discord.HTTPException:
            logger.warning("Не удалось создать голосовой канал для игры «Бункер» #%s", game_id)

        now_ts = int(time.time())
        game = bunker_db.update_game(
            game_id, status="active", phase="discussion", round_number=1,
            phase_deadline_ts=now_ts + game["discussion_timer_sec"],
            bunker_capacity=bunker_capacity, voice_channel_id=voice_channel_id,
            catastrophe_name=catastrophe["name"], catastrophe_description=catastrophe["description"],
            catastrophe_key=catastrophe["key"],
            bunker_conditions_name=conditions["name"], bunker_conditions_description=conditions["description"],
            bunker_conditions_key=conditions["key"],
            started_at=_now_iso(),
        )

        frontend = _frontend_url()
        voice_note = (
            i18n.t("bunker.dm.voice", lang, channel_id=voice_channel_id) if voice_channel_id else ""
        )
        for user_id in player_ids:
            member = guild.get_member(user_id)
            if member is None:
                continue
            player = bunker_db.get_player(game_id, user_id)
            link = f"{frontend}/bunker/{player['token']}"
            try:
                await member.send(
                    content=i18n.t("bunker.dm.started", lang, link=link, voice=voice_note)
                )
            except discord.Forbidden:
                pass

        try:
            await channel.send(embed=build_game_started_embed(game, players, voice_channel_id, lang))
        except discord.HTTPException:
            pass

        self._add_event(
            game_id, 1, "game_started",
            i18n.t("bunker.event.game_started", lang, count=len(players), capacity=bunker_capacity),
        )
        self.schedule_phase_timer(game_id)

    def schedule_phase_timer(self, game_id: int):
        old = self._timers.pop(game_id, None)
        if old:
            old.cancel()
        self._timers[game_id] = self.bot.loop.create_task(self._run_phase_timer(game_id))

    async def _run_phase_timer(self, game_id: int):
        try:
            game = bunker_db.get_game(game_id)
            if game is None or game["status"] != "active":
                return
            remaining = (game["phase_deadline_ts"] or 0) - int(time.time())
            if remaining > 0:
                await asyncio.sleep(remaining)

            game = bunker_db.get_game(game_id)
            if game is None or game["status"] != "active":
                return

            handlers = {
                "discussion": self._finish_discussion,
                "vote": self._finish_vote,
            }
            handler = handlers.get(game["phase"])
            if handler:
                await handler(game_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Bunker phase timer failed for game %s", game_id)

    def _cancel_timer(self, game_id: int):
        task = self._timers.pop(game_id, None)
        if task and task is not asyncio.current_task():
            task.cancel()

    def _add_event(self, game_id: int, round_number: int, event_type: str, payload: str = ""):
        bunker_db.add_round_event(game_id, round_number, event_type, payload)

    async def maybe_finish_vote_early(self, game_id: int):
        """Вызывается дашбордом после каждой отправки голоса за исключение."""
        game = bunker_db.get_game(game_id)
        if game is None or game["status"] != "active" or game["phase"] != "vote":
            return
        round_number = game["round_number"]
        alive = bunker_db.list_alive_players(game_id)
        if not alive:
            return await self._finish_vote(game_id)
        submitted = {v["voter_user_id"] for v in bunker_db.get_votes(game_id, round_number)}
        if all(p["user_id"] in submitted for p in alive):
            await self._finish_vote(game_id)

    async def refresh_vote_tally(self, game_id: int):
        """Обновляет информационное табло голосования в канале (редактирует одно сообщение,
        а не шлёт новое на каждый голос — тот же паттерн, что и в mafia.py)."""
        game = bunker_db.get_game(game_id)
        if game is None or not game["vote_message_id"]:
            return
        channel = self.bot.get_channel(game["channel_id"])
        if channel is None:
            return
        guild = self.bot.get_guild(game["guild_id"])
        lang = i18n.lang_for(game["guild_id"])
        members = _resolve_alive_members(guild, game_id)
        votes = bunker_db.get_votes(game_id, game["round_number"])
        try:
            message = await channel.fetch_message(game["vote_message_id"])
            await message.edit(embed=build_vote_embed(game, members, votes, lang))
        except discord.HTTPException:
            pass

    async def force_advance_phase(self, game_id: int) -> bool:
        """Ведущий/админ форсирует переход фазы из дашборда, не дожидаясь таймера
        или всех голосов. Возвращает False, если игра не активна."""
        game = bunker_db.get_game(game_id)
        if game is None or game["status"] != "active":
            return False
        handlers = {
            "discussion": self._finish_discussion,
            "vote": self._finish_vote,
        }
        handler = handlers.get(game["phase"])
        if handler is None:
            return False
        # Cancel the sleeping timer before awaiting the handler so it cannot
        # race into the same phase transition after we pass the phase check.
        self._cancel_timer(game_id)
        await handler(game_id)
        return True

    async def force_end_game(self, game_id: int) -> bool:
        """Ведущий/админ досрочно завершает игру из дашборда."""
        game = bunker_db.get_game(game_id)
        if game is None or game["status"] != "active":
            return False
        await self.end_game(game_id, stopped=True)
        return True

    async def announce_ability(self, game_id: int, announcement: dict):
        """Публикует в канал игры заявку игрока на спец. возможность — ведущий/админ применяет её вручную
        через панель дашборда."""
        game = bunker_db.get_game(game_id)
        if game is None:
            return
        channel = self.bot.get_channel(game["channel_id"])
        if channel is None:
            return
        guild = self.bot.get_guild(game["guild_id"])
        lang = i18n.lang_for(game["guild_id"])
        actor = bunker_db.get_player(game_id, announcement["player_user_id"])
        player_name = _display_name(
            guild,
            announcement["player_user_id"],
            actor.get("display_name") if actor else None,
        )
        target_part = ""
        if announcement["target_user_id"] is not None:
            target = bunker_db.get_player(game_id, announcement["target_user_id"])
            target_part = i18n.t(
                "bunker.ability.target",
                lang,
                target=_display_name(
                    guild,
                    announcement["target_user_id"],
                    target.get("display_name") if target else None,
                ),
            )
        note_part = (
            i18n.t("bunker.ability.note", lang, note=announcement["note"])
            if announcement["note"]
            else ""
        )
        try:
            await channel.send(
                content=i18n.t(
                    "bunker.ability.announce",
                    lang,
                    player=player_name,
                    card_name=announcement["card_name"],
                    target=target_part,
                    note=note_part,
                )
            )
        except discord.HTTPException:
            pass

    async def _finish_discussion(self, game_id: int):
        async with self._phase_lock(game_id):
            game = bunker_db.get_game(game_id)
            if game is None or game["status"] != "active" or game["phase"] != "discussion":
                return
            self._cancel_timer(game_id)
            lang = i18n.lang_for(game["guild_id"])

            guild = self.bot.get_guild(game["guild_id"])
            channel = self.bot.get_channel(game["channel_id"])
            members = _resolve_alive_members(guild, game_id)

            now_ts = int(time.time())
            game = bunker_db.update_game(game_id, phase="vote", phase_deadline_ts=now_ts + game["vote_timer_sec"])

            message = None
            if channel is not None:
                try:
                    await channel.send(content=i18n.t("bunker.phase.vote_open", lang))
                    message = await channel.send(embed=build_vote_embed(game, members, [], lang))
                except discord.HTTPException:
                    pass
            if message is not None:
                bunker_db.update_game(game_id, vote_message_id=message.id)

            self.schedule_phase_timer(game_id)

    async def _finish_vote(self, game_id: int):
        should_end = False
        async with self._phase_lock(game_id):
            game = bunker_db.get_game(game_id)
            if game is None or game["status"] != "active" or game["phase"] != "vote":
                return
            self._cancel_timer(game_id)
            lang = i18n.lang_for(game["guild_id"])

            round_number = game["round_number"]
            votes = {v["voter_user_id"]: v["target_user_id"] for v in bunker_db.get_votes(game_id, round_number)}
            expelled = bunker_core.resolve_expulsion_vote(votes)

            channel = self.bot.get_channel(game["channel_id"])

            if expelled is not None:
                bunker_db.eliminate_player(game_id, expelled, round_number)
                self._add_event(
                    game_id, round_number, "expelled",
                    i18n.t("bunker.event.expelled", lang, user_id=expelled),
                )
            else:
                self._add_event(
                    game_id, round_number, "no_expulsion",
                    i18n.t("bunker.event.no_expulsion", lang),
                )

            if channel is not None:
                try:
                    await channel.send(embed=build_expulsion_result_embed(expelled, lang))
                except discord.HTTPException:
                    pass

            alive_count = len(bunker_db.list_alive_players(game_id))
            if bunker_core.is_game_over(alive_count, game["bunker_capacity"]):
                should_end = True
            else:
                now_ts = int(time.time())
                game = bunker_db.update_game(
                    game_id,
                    phase="discussion",
                    round_number=round_number + 1,
                    phase_deadline_ts=now_ts + game["discussion_timer_sec"],
                )
                if channel is not None:
                    try:
                        await channel.send(
                            content=i18n.t(
                                "bunker.phase.discussion",
                                lang,
                                round=game["round_number"],
                                seconds=game["discussion_timer_sec"],
                            )
                        )
                    except discord.HTTPException:
                        pass
                self.schedule_phase_timer(game_id)

        if should_end:
            await self.end_game(game_id)

    async def end_game(self, game_id: int, stopped: bool = False):
        game = bunker_db.get_game(game_id)
        if game is None:
            return
        self._cancel_timer(game_id)
        lang = i18n.lang_for(game["guild_id"])

        guild = self.bot.get_guild(game["guild_id"])
        channel = self.bot.get_channel(game["channel_id"])
        players = bunker_db.list_players(game_id)

        bunker_db.update_game(game_id, status="finished", phase="ended", ended_at=_now_iso())

        if channel is not None:
            try:
                await channel.send(embed=build_result_embed(players, lang, stopped=stopped))
            except discord.HTTPException:
                pass

        if game["voice_channel_id"] and guild is not None:
            voice_channel = guild.get_channel(game["voice_channel_id"])
            if voice_channel is not None:
                try:
                    await voice_channel.delete(reason=i18n.t("bunker.voice_delete_reason", lang))
                except discord.HTTPException:
                    pass

        ended_key = "bunker.event.game_ended_stopped" if stopped else "bunker.event.game_ended_finished"
        self._add_event(game_id, game["round_number"], "game_ended", i18n.t(ended_key, lang))
        await self._send_log(game, players, stopped, lang)

    async def _send_log(self, game: dict, players: list[dict], stopped: bool, lang: str):
        log_channel_id = bunker_core.get_settings(game["guild_id"])["log_channel_id"]
        if not log_channel_id:
            return
        channel = self.bot.get_channel(int(log_channel_id))
        if channel is None:
            return
        survivors = sum(1 for p in players if p["alive"])
        if stopped:
            outcome = i18n.t("bunker.log.stopped", lang)
        else:
            outcome = i18n.t(
                "bunker.log.survivors",
                lang,
                survivors=survivors,
                total=len(players),
            )
        text = i18n.t(
            "bunker.log.finished",
            lang,
            game_id=game["id"],
            channel_id=game["channel_id"],
            outcome=outcome,
        )
        try:
            await channel.send(content=text)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    bunker_db.init()
    cog = BunkerCog(bot)
    slash_registry.register_bunker(cog)
    await bot.add_cog(cog)
