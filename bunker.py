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
import bunker_db

logger = logging.getLogger("bunker")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _frontend_url() -> str:
    return os.getenv("DASHBOARD_FRONTEND_URL", "").rstrip("/")


def _resolve_alive_members(guild: discord.Guild | None, game_id: int) -> list[dict]:
    members = []
    for player in bunker_db.list_alive_players(game_id):
        member = guild.get_member(player["user_id"]) if guild else None
        display = member.display_name if member else str(player["user_id"])
        members.append({"user_id": player["user_id"], "display_name": display})
    return members


def _display_name(guild: discord.Guild | None, user_id: int) -> str:
    member = guild.get_member(user_id) if guild else None
    return member.display_name if member else str(user_id)


# ────────────────────────── Эмбеды ──────────────────────────

def build_lobby_embed(game: dict, players: list[dict]) -> discord.Embed:
    embed = discord.Embed(
        title="🚪 Лобби «Бункер»",
        description="Нажмите «Присоединиться», чтобы принять участие.",
        color=0x5865F2,
    )
    embed.add_field(name="Инициатор", value=f"<@{game['created_by']}>", inline=True)
    embed.add_field(name="Игроков нужно", value=f"{game['min_players']}–{game['max_players']}", inline=True)
    embed.add_field(
        name="Таймеры",
        value=f"💬 {game['discussion_timer_sec']}с · 🗳️ {game['vote_timer_sec']}с",
        inline=True,
    )
    if game["bunker_capacity"]:
        embed.add_field(name="Вместимость бункера", value=str(game["bunker_capacity"]), inline=True)
    embed.add_field(
        name="Карточки",
        value="Без повторов" if game["unique_cards"] else "С повторами",
        inline=True,
    )
    mentions = "\n".join(f"`{i + 1}.` <@{p['user_id']}>" for i, p in enumerate(players)) or "—"
    embed.add_field(name=f"Участники [{len(players)}/{game['max_players']}]", value=mentions, inline=False)
    return embed


def build_lobby_cancelled_embed(_game: dict) -> discord.Embed:
    return discord.Embed(title="🚫 Лобби отменено", color=0x2B2D31)


def build_game_started_embed(game: dict, players: list[dict], voice_channel_id: int | None) -> discord.Embed:
    embed = discord.Embed(
        title="🚪 Игра «Бункер» началась!",
        description=(
            "Карточки персонажей розданы в личные сообщения. Каждый игрок получил персональную ссылку "
            "на дашборд — там вся игра: карточка, раскрытие характеристик, спец. возможности и "
            "голосование за исключение."
        ),
        color=0x5865F2,
    )
    embed.add_field(name="Игроков", value=str(len(players)), inline=True)
    embed.add_field(name="Вместимость бункера", value=str(game["bunker_capacity"]), inline=True)
    if voice_channel_id:
        embed.add_field(name="Голосовой канал", value=f"<#{voice_channel_id}>", inline=True)
    embed.add_field(name="Катаклизм", value=f"**{game['catastrophe_name']}**\n{game['catastrophe_description']}", inline=False)
    embed.add_field(
        name="Условия бункера",
        value=f"**{game['bunker_conditions_name']}**\n{game['bunker_conditions_description']}",
        inline=False,
    )
    embed.add_field(name="Раунд 1", value=f"💬 Обсуждение — {game['discussion_timer_sec']} сек", inline=False)
    return embed


def build_vote_embed(game: dict, members: list[dict], votes: list[dict]) -> discord.Embed:
    embed = discord.Embed(
        title="🗳️ Голосование за исключение",
        description=(
            f"Голосование проходит на персональной ссылке каждого игрока. "
            f"Голосование открытое. Время: {game['vote_timer_sec']} сек."
        ),
        color=0xFEE75C,
    )
    if not votes:
        embed.add_field(name="Голоса", value="Пока никто не проголосовал.", inline=False)
    else:
        tally: dict[str, int] = {}
        for vote in votes:
            key = f"<@{vote['target_user_id']}>" if vote["target_user_id"] else "Пропустить"
            tally[key] = tally.get(key, 0) + 1
        lines = [f"{name}: {count}" for name, count in sorted(tally.items(), key=lambda kv: -kv[1])]
        embed.add_field(name="Голоса", value="\n".join(lines), inline=False)
    embed.set_footer(text=f"Живых игроков: {len(members)}")
    return embed


def build_expulsion_result_embed(expelled_id: int | None) -> discord.Embed:
    if expelled_id is None:
        return discord.Embed(
            title="⚖️ Итоги голосования", description="Большинства не набралось — никто не покинул бункер.", color=0x2B2D31
        )
    return discord.Embed(title="⚖️ Итоги голосования", description=f"Бункер покидает <@{expelled_id}>.", color=0xED4245)


def _character_summary(character: dict) -> str:
    if not character:
        return "—"
    return (
        f"{character['profession']['name']} ({character['profession']['experience_level']}), "
        f"{character['age']['label']}, {character['gender']}"
    )


def build_result_embed(players: list[dict], stopped: bool = False) -> discord.Embed:
    if stopped:
        title, desc, color = "🚫 Игра остановлена", "Игра остановлена модератором досрочно.", 0x2B2D31
    else:
        title, desc, color = "🏆 Бункер укомплектован!", "Голосования завершены — состав выживших определён.", 0x57F287

    embed = discord.Embed(title=title, description=desc, color=color)
    survivors = [p for p in players if p["alive"]]
    eliminated = [p for p in players if not p["alive"]]
    if survivors:
        lines = [f"<@{p['user_id']}> — {_character_summary(p['character'])}" for p in survivors]
        embed.add_field(name="✅ В бункере", value="\n".join(lines), inline=False)
    if eliminated:
        lines = [f"<@{p['user_id']}> — {_character_summary(p['character'])}" for p in eliminated]
        embed.add_field(name="❌ Не прошли", value="\n".join(lines), inline=False)
    return embed


# ────────────────────────── Лобби ──────────────────────────

class BunkerLobbyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def _get_game(self, interaction: discord.Interaction) -> dict | None:
        if interaction.message is None:
            return None
        return bunker_db.get_game_by_lobby_message(interaction.message.id)

    @discord.ui.button(label="Присоединиться", style=discord.ButtonStyle.success, custom_id="bunker_lobby_join")
    async def join_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message("Лобби недоступно.", ephemeral=True)
        if bunker_db.count_players(game["id"]) >= game["max_players"]:
            return await interaction.response.send_message("Лобби заполнено.", ephemeral=True)
        if not bunker_db.add_player(game["id"], interaction.user.id):
            return await interaction.response.send_message("Ты уже в лобби.", ephemeral=True)

        players = bunker_db.list_players(game["id"])
        await interaction.response.edit_message(embed=build_lobby_embed(game, players))

        if len(players) >= game["max_players"]:
            cog = interaction.client.get_cog("BunkerCog")
            if cog:
                await cog.start_game(game["id"])

    @discord.ui.button(label="Покинуть", style=discord.ButtonStyle.secondary, custom_id="bunker_lobby_leave")
    async def leave_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message("Лобби недоступно.", ephemeral=True)
        if not bunker_db.remove_player(game["id"], interaction.user.id):
            return await interaction.response.send_message("Тебя нет в лобби.", ephemeral=True)
        players = bunker_db.list_players(game["id"])
        await interaction.response.edit_message(embed=build_lobby_embed(game, players))

    @discord.ui.button(label="Начать сейчас", style=discord.ButtonStyle.primary, custom_id="bunker_lobby_force_start")
    async def force_start_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message("Лобби недоступно.", ephemeral=True)
        if not bunker_core.has_moderator_access(interaction.user):
            return await interaction.response.send_message("Нет доступа.", ephemeral=True)
        count = bunker_db.count_players(game["id"])
        if count < game["min_players"]:
            return await interaction.response.send_message(
                f"Нужно минимум {game['min_players']} игроков (сейчас {count}).", ephemeral=True
            )
        await interaction.response.defer()
        cog = interaction.client.get_cog("BunkerCog")
        if cog:
            await cog.start_game(game["id"])

    @discord.ui.button(label="Отменить", style=discord.ButtonStyle.danger, custom_id="bunker_lobby_cancel")
    async def cancel_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message("Лобби недоступно.", ephemeral=True)
        if not bunker_core.has_moderator_access(interaction.user):
            return await interaction.response.send_message("Нет доступа.", ephemeral=True)
        bunker_db.update_game(game["id"], status="cancelled", ended_at=_now_iso())
        await interaction.response.edit_message(embed=build_lobby_cancelled_embed(game), view=None)


# ────────────────────────── Ког ──────────────────────────

class BunkerCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._timers: dict[int, asyncio.Task] = {}
        self._recovered = False
        self.lobby_view = BunkerLobbyView()

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
        settings = bunker_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message("Модуль «Бункер» отключён.", ephemeral=True)

        if bunker_db.get_active_game_in_channel(interaction.channel.id) is not None:
            return await interaction.response.send_message("В этом канале уже есть активное лобби/игра.", ephemeral=True)

        min_players = мин_игроков if мин_игроков is not None else settings["default_min_players"]
        max_players = макс_игроков if макс_игроков is not None else settings["default_max_players"]
        if min_players > max_players:
            return await interaction.response.send_message("Минимум игроков не может быть больше максимума.", ephemeral=True)
        if вместимость_бункера is not None and вместимость_бункера >= max_players:
            return await interaction.response.send_message(
                "Вместимость бункера должна быть меньше максимума игроков.", ephemeral=True
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
        bunker_db.add_player(game["id"], interaction.user.id)
        players = bunker_db.list_players(game["id"])

        await interaction.response.send_message(embed=build_lobby_embed(game, players), view=self.lobby_view)
        message = await interaction.original_response()
        bunker_db.update_game(game["id"], lobby_message_id=message.id)

    @app_commands.command(name="бункер-стоп", description="Остановить лобби/игру «Бункер» в этом канале")
    @app_commands.default_permissions(manage_guild=True)
    async def stop_game(self, interaction: discord.Interaction):
        game = bunker_db.get_active_game_in_channel(interaction.channel.id)
        if game is None:
            return await interaction.response.send_message("В этом канале нет активной игры.", ephemeral=True)
        if not bunker_core.has_moderator_access(interaction.user):
            return await interaction.response.send_message("Нет доступа.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        if game["status"] == "lobby":
            bunker_db.update_game(game["id"], status="cancelled", ended_at=_now_iso())
            channel = self.bot.get_channel(game["channel_id"])
            if channel is not None and game["lobby_message_id"]:
                try:
                    message = await channel.fetch_message(game["lobby_message_id"])
                    await message.edit(embed=build_lobby_cancelled_embed(game), view=None)
                except discord.HTTPException:
                    pass
        else:
            await self.end_game(game["id"], stopped=True)
        await interaction.followup.send("Остановлено.", ephemeral=True)

    # ────────────────────────── Игровой цикл ──────────────────────────

    async def start_game(self, game_id: int):
        game = bunker_db.get_game(game_id)
        if game is None or game["status"] != "lobby":
            return
        guild = self.bot.get_guild(game["guild_id"])
        channel = self.bot.get_channel(game["channel_id"])
        if guild is None or channel is None:
            return

        players = bunker_db.list_players(game_id)
        player_ids = [p["user_id"] for p in players]
        display_names = {uid: _display_name(guild, uid) for uid in player_ids}

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
            voice_channel = await guild.create_voice_channel(
                name=f"Бункер • Игра #{game_id}", overwrites=overwrites, category=category,
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
            bunker_conditions_name=conditions["name"], bunker_conditions_description=conditions["description"],
            started_at=_now_iso(),
        )

        frontend = _frontend_url()
        voice_note = f" В <#{voice_channel_id}>." if voice_channel_id else ""
        for user_id in player_ids:
            member = guild.get_member(user_id)
            if member is None:
                continue
            player = bunker_db.get_player(game_id, user_id)
            link = f"{frontend}/bunker/{player['token']}"
            try:
                await member.send(
                    content=(
                        "Игра «Бункер» началась. Твоя личная карточка персонажа (профессия, здоровье, рюкзак, "
                        "спец. возможности и т.д.) — на персональной ссылке (действует всю игру): "
                        f"{link}\nТам же: раскрытие характеристик, заявка на спец. возможность и голосование "
                        f"за исключение.{voice_note}"
                    )
                )
            except discord.Forbidden:
                pass

        try:
            await channel.send(embed=build_game_started_embed(game, players, voice_channel_id))
        except discord.HTTPException:
            pass

        self._add_event(game_id, 1, "game_started", f"Игроков: {len(players)}. Вместимость: {bunker_capacity}.")
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
        members = _resolve_alive_members(guild, game_id)
        votes = bunker_db.get_votes(game_id, game["round_number"])
        try:
            message = await channel.fetch_message(game["vote_message_id"])
            await message.edit(embed=build_vote_embed(game, members, votes))
        except discord.HTTPException:
            pass

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
        player_name = _display_name(guild, announcement["player_user_id"])
        target_part = ""
        if announcement["target_user_id"] is not None:
            target_part = f" Цель: {_display_name(guild, announcement['target_user_id'])}."
        note_part = f" Комментарий: {announcement['note']}" if announcement["note"] else ""
        try:
            await channel.send(
                content=(
                    f"🃏 Стоп игра! Игрок **{player_name}** хочет использовать спец. возможность "
                    f"«{announcement['card_name']}».{target_part}{note_part}\nВедущий применяет эффект вручную "
                    "через панель модуля «Бункер» в дашборде."
                )
            )
        except discord.HTTPException:
            pass

    async def _finish_discussion(self, game_id: int):
        game = bunker_db.get_game(game_id)
        if game is None or game["status"] != "active" or game["phase"] != "discussion":
            return
        self._cancel_timer(game_id)

        guild = self.bot.get_guild(game["guild_id"])
        channel = self.bot.get_channel(game["channel_id"])
        members = _resolve_alive_members(guild, game_id)

        now_ts = int(time.time())
        game = bunker_db.update_game(game_id, phase="vote", phase_deadline_ts=now_ts + game["vote_timer_sec"])

        message = None
        if channel is not None:
            try:
                await channel.send(content="🗳️ Голосование за исключение открыто — голосуйте на своей персональной ссылке.")
                message = await channel.send(embed=build_vote_embed(game, members, []))
            except discord.HTTPException:
                pass
        if message is not None:
            bunker_db.update_game(game_id, vote_message_id=message.id)

        self.schedule_phase_timer(game_id)

    async def _finish_vote(self, game_id: int):
        game = bunker_db.get_game(game_id)
        if game is None or game["status"] != "active" or game["phase"] != "vote":
            return
        self._cancel_timer(game_id)

        round_number = game["round_number"]
        votes = {v["voter_user_id"]: v["target_user_id"] for v in bunker_db.get_votes(game_id, round_number)}
        expelled = bunker_core.resolve_expulsion_vote(votes)

        channel = self.bot.get_channel(game["channel_id"])

        if expelled is not None:
            bunker_db.eliminate_player(game_id, expelled, round_number)
            self._add_event(game_id, round_number, "expelled", f"Исключён: {expelled}")
        else:
            self._add_event(game_id, round_number, "no_expulsion", "Никто не исключён (нет большинства).")

        if channel is not None:
            try:
                await channel.send(embed=build_expulsion_result_embed(expelled))
            except discord.HTTPException:
                pass

        alive_count = len(bunker_db.list_alive_players(game_id))
        if bunker_core.is_game_over(alive_count, game["bunker_capacity"]):
            return await self.end_game(game_id)

        now_ts = int(time.time())
        game = bunker_db.update_game(
            game_id, phase="discussion", round_number=round_number + 1, phase_deadline_ts=now_ts + game["discussion_timer_sec"],
        )
        if channel is not None:
            try:
                await channel.send(
                    content=(
                        f"💬 Раунд {game['round_number']}: обсуждение и раскрытие характеристик — "
                        f"{game['discussion_timer_sec']} сек. Ссылки уже на руках."
                    )
                )
            except discord.HTTPException:
                pass
        self.schedule_phase_timer(game_id)

    async def end_game(self, game_id: int, stopped: bool = False):
        game = bunker_db.get_game(game_id)
        if game is None:
            return
        self._cancel_timer(game_id)

        guild = self.bot.get_guild(game["guild_id"])
        channel = self.bot.get_channel(game["channel_id"])
        players = bunker_db.list_players(game_id)

        bunker_db.update_game(game_id, status="finished", phase="ended", ended_at=_now_iso())

        if channel is not None:
            try:
                await channel.send(embed=build_result_embed(players, stopped=stopped))
            except discord.HTTPException:
                pass

        if game["voice_channel_id"] and guild is not None:
            voice_channel = guild.get_channel(game["voice_channel_id"])
            if voice_channel is not None:
                try:
                    await voice_channel.delete(reason="Игра «Бункер» завершена")
                except discord.HTTPException:
                    pass

        self._add_event(game_id, game["round_number"], "game_ended", "Остановлено" if stopped else "Бункер укомплектован")
        await self._send_log(game, players, stopped)

    async def _send_log(self, game: dict, players: list[dict], stopped: bool):
        log_channel_id = bunker_core.get_settings(game["guild_id"])["log_channel_id"]
        if not log_channel_id:
            return
        channel = self.bot.get_channel(int(log_channel_id))
        if channel is None:
            return
        survivors = sum(1 for p in players if p["alive"])
        text = (
            f"Игра «Бункер» #{game['id']} в <#{game['channel_id']}> завершена. "
            f"{'Остановлено досрочно.' if stopped else f'Выжило: {survivors}/{len(players)}.'}"
        )
        try:
            await channel.send(content=text)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    bunker_db.init()
    await bot.add_cog(BunkerCog(bot))
