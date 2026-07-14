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

import mafia_core
import mafia_db

logger = logging.getLogger("mafia")

PAGE_SIZE = 24  # + пункт «Пропустить» = 25 опций максимум


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _frontend_url() -> str:
    return os.getenv("DASHBOARD_FRONTEND_URL", "").rstrip("/")


def _resolve_alive_members(guild: discord.Guild | None, game_id: int) -> list[dict]:
    members = []
    for player in mafia_db.list_alive_players(game_id):
        member = guild.get_member(player["user_id"]) if guild else None
        display = member.display_name if member else str(player["user_id"])
        members.append({"user_id": player["user_id"], "display_name": display})
    return members


# ────────────────────────── Эмбеды ──────────────────────────

def build_lobby_embed(game: dict, players: list[dict]) -> discord.Embed:
    embed = discord.Embed(
        title="🎭 Лобби «Мафия»",
        description="Нажмите «Присоединиться», чтобы принять участие.",
        color=0x5865F2,
    )
    embed.add_field(name="Инициатор", value=f"<@{game['created_by']}>", inline=True)
    embed.add_field(name="Игроков нужно", value=f"{game['min_players']}–{game['max_players']}", inline=True)
    embed.add_field(
        name="Таймеры",
        value=f"🌙 {game['night_timer_sec']}с · 💬 {game['day_discussion_timer_sec']}с · 🗳️ {game['day_vote_timer_sec']}с",
        inline=True,
    )
    mentions = "\n".join(f"`{i + 1}.` <@{p['user_id']}>" for i, p in enumerate(players)) or "—"
    embed.add_field(name=f"Участники [{len(players)}/{game['max_players']}]", value=mentions, inline=False)
    return embed


def build_lobby_cancelled_embed(_game: dict) -> discord.Embed:
    return discord.Embed(title="🚫 Лобби отменено", color=0x2B2D31)


def build_game_started_embed(game: dict, players: list[dict], voice_channel_id: int | None) -> discord.Embed:
    embed = discord.Embed(
        title="🎭 Игра «Мафия» началась!",
        description=(
            "Роли розданы в личные сообщения. У ролей с ночными действиями (мафия/доктор/шериф) — "
            "персональная ссылка на весь матч."
        ),
        color=0x5865F2,
    )
    embed.add_field(name="Игроков", value=str(len(players)), inline=True)
    if voice_channel_id:
        embed.add_field(name="Голосовой канал", value=f"<#{voice_channel_id}>", inline=True)
    embed.add_field(name="Раунд 1", value=f"🌙 Ночь — {game['night_timer_sec']} сек", inline=False)
    return embed


def build_morning_embed(died_id: int | None, died_player: dict | None) -> discord.Embed:
    if died_id is None:
        return discord.Embed(title="🌅 Утро", description="Ночь прошла тихо — никто не погиб.", color=0x57F287)
    role = mafia_core.role_label(died_player["role"]) if died_player else "?"
    return discord.Embed(title="🌅 Утро", description=f"Этой ночью погиб <@{died_id}> ({role}).", color=0xED4245)


def build_vote_embed(game: dict, members: list[dict], votes: list[dict]) -> discord.Embed:
    embed = discord.Embed(
        title="🗳️ Дневное голосование",
        description=f"Выберите, кого казнить, в списке ниже. Голосование открытое. Время: {game['day_vote_timer_sec']} сек.",
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


def build_lynch_result_embed(lynched_id: int | None, lynched_player: dict | None) -> discord.Embed:
    if lynched_id is None:
        return discord.Embed(
            title="⚖️ Итоги голосования", description="Большинства не набралось — никто не казнён.", color=0x2B2D31
        )
    role = mafia_core.role_label(lynched_player["role"]) if lynched_player else "?"
    return discord.Embed(title="⚖️ Итоги голосования", description=f"Городом казнён <@{lynched_id}> ({role}).", color=0xED4245)


def build_result_embed(winner: str | None, players: list[dict]) -> discord.Embed:
    if winner is None:
        title, desc, color = "🚫 Игра остановлена", "Игра остановлена модератором досрочно.", 0x2B2D31
    elif winner == "town":
        title, desc, color = "🏆 Победа мирных жителей!", "Мафия обезврежена.", 0x57F287
    else:
        title, desc, color = "🏆 Победа мафии!", "Мафия захватила контроль над городом.", 0xED4245

    embed = discord.Embed(title=title, description=desc, color=color)
    lines = [f"<@{p['user_id']}> — {mafia_core.role_label(p['role'] or 'citizen')}" for p in players]
    embed.add_field(name="Роли", value="\n".join(lines) or "—", inline=False)
    return embed


# ────────────────────────── Голосование: Select с пагинацией ──────────────────────────

def _vote_options(members: list[dict], page: int) -> list[discord.SelectOption]:
    window = members[page * PAGE_SIZE: page * PAGE_SIZE + PAGE_SIZE]
    options = [discord.SelectOption(label=m["display_name"][:100], value=str(m["user_id"])) for m in window]
    options.append(discord.SelectOption(label="Пропустить", value="skip", emoji="⏭️"))
    return options


class MafiaVoteView(discord.ui.View):
    def __init__(self, members: list[dict] | None = None, page: int = 0):
        super().__init__(timeout=None)
        members = members or []
        if members:
            self.vote_select.options = _vote_options(members, page)
        last_page = max(0, (len(members) - 1) // PAGE_SIZE) if members else 0
        self.prev_btn.disabled = page <= 0
        self.next_btn.disabled = page >= last_page

    @discord.ui.select(
        custom_id="mafia_vote_select", placeholder="Кого казнить?", min_values=1, max_values=1,
        options=[discord.SelectOption(label="—", value="skip")],
    )
    async def vote_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        if interaction.message is None:
            return await interaction.response.send_message("Голосование недоступно.", ephemeral=True)
        game = mafia_db.get_game_by_vote_message(interaction.message.id)
        if game is None or game["status"] != "active" or game["phase"] != "day_vote":
            return await interaction.response.send_message("Голосование сейчас недоступно.", ephemeral=True)
        player = mafia_db.get_player(game["id"], interaction.user.id)
        if player is None or not player["alive"]:
            return await interaction.response.send_message("Ты не в игре или уже выбыл.", ephemeral=True)

        value = select.values[0]
        target = None if value == "skip" else int(value)
        mafia_db.upsert_day_vote(game["id"], game["round_number"], interaction.user.id, target)
        await interaction.response.send_message("Голос учтён.", ephemeral=True)

        cog = interaction.client.get_cog("MafiaCog")
        if cog:
            await cog.refresh_vote_tally(game["id"])

    async def _change_page(self, interaction: discord.Interaction, delta: int):
        if interaction.message is None:
            return await interaction.response.send_message("Голосование недоступно.", ephemeral=True)
        game = mafia_db.get_game_by_vote_message(interaction.message.id)
        if game is None or game["status"] != "active" or game["phase"] != "day_vote":
            return await interaction.response.send_message("Голосование сейчас недоступно.", ephemeral=True)

        members = _resolve_alive_members(interaction.guild, game["id"])
        last_page = max(0, (len(members) - 1) // PAGE_SIZE)
        new_page = max(0, min(last_page, game["vote_page"] + delta))
        mafia_db.update_game(game["id"], vote_page=new_page)
        await interaction.response.edit_message(view=MafiaVoteView(members, new_page))

    @discord.ui.button(label="‹", style=discord.ButtonStyle.secondary, custom_id="mafia_vote_prev")
    async def prev_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._change_page(interaction, -1)

    @discord.ui.button(label="›", style=discord.ButtonStyle.secondary, custom_id="mafia_vote_next")
    async def next_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._change_page(interaction, 1)


# ────────────────────────── Лобби ──────────────────────────

class MafiaLobbyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    def _get_game(self, interaction: discord.Interaction) -> dict | None:
        if interaction.message is None:
            return None
        return mafia_db.get_game_by_lobby_message(interaction.message.id)

    @discord.ui.button(label="Присоединиться", style=discord.ButtonStyle.success, custom_id="mafia_lobby_join")
    async def join_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message("Лобби недоступно.", ephemeral=True)
        if mafia_db.count_players(game["id"]) >= game["max_players"]:
            return await interaction.response.send_message("Лобби заполнено.", ephemeral=True)
        if not mafia_db.add_player(game["id"], interaction.user.id):
            return await interaction.response.send_message("Ты уже в лобби.", ephemeral=True)

        players = mafia_db.list_players(game["id"])
        await interaction.response.edit_message(embed=build_lobby_embed(game, players))

        if len(players) >= game["max_players"]:
            cog = interaction.client.get_cog("MafiaCog")
            if cog:
                await cog.start_game(game["id"])

    @discord.ui.button(label="Покинуть", style=discord.ButtonStyle.secondary, custom_id="mafia_lobby_leave")
    async def leave_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message("Лобби недоступно.", ephemeral=True)
        if not mafia_db.remove_player(game["id"], interaction.user.id):
            return await interaction.response.send_message("Тебя нет в лобби.", ephemeral=True)
        players = mafia_db.list_players(game["id"])
        await interaction.response.edit_message(embed=build_lobby_embed(game, players))

    @discord.ui.button(label="Начать сейчас", style=discord.ButtonStyle.primary, custom_id="mafia_lobby_force_start")
    async def force_start_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message("Лобби недоступно.", ephemeral=True)
        if not mafia_core.has_moderator_access(interaction.user):
            return await interaction.response.send_message("Нет доступа.", ephemeral=True)
        count = mafia_db.count_players(game["id"])
        if count < game["min_players"]:
            return await interaction.response.send_message(
                f"Нужно минимум {game['min_players']} игроков (сейчас {count}).", ephemeral=True
            )
        await interaction.response.defer()
        cog = interaction.client.get_cog("MafiaCog")
        if cog:
            await cog.start_game(game["id"])

    @discord.ui.button(label="Отменить", style=discord.ButtonStyle.danger, custom_id="mafia_lobby_cancel")
    async def cancel_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        game = self._get_game(interaction)
        if game is None or game["status"] != "lobby":
            return await interaction.response.send_message("Лобби недоступно.", ephemeral=True)
        if not mafia_core.has_moderator_access(interaction.user):
            return await interaction.response.send_message("Нет доступа.", ephemeral=True)
        mafia_db.update_game(game["id"], status="cancelled", ended_at=_now_iso())
        await interaction.response.edit_message(embed=build_lobby_cancelled_embed(game), view=None)


# ────────────────────────── Ког ──────────────────────────

class MafiaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._timers: dict[int, asyncio.Task] = {}
        self._recovered = False
        self.lobby_view = MafiaLobbyView()
        self.vote_view = MafiaVoteView()

    async def cog_load(self):
        self.bot.add_view(self.lobby_view)
        self.bot.add_view(self.vote_view)

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
        settings = mafia_core.get_settings()
        if not settings["enabled"]:
            return await interaction.response.send_message("Модуль «Мафия» отключён.", ephemeral=True)

        if mafia_db.get_active_game_in_channel(interaction.channel.id) is not None:
            return await interaction.response.send_message("В этом канале уже есть активное лобби/игра.", ephemeral=True)

        min_players = мин_игроков if мин_игроков is not None else settings["default_min_players"]
        max_players = макс_игроков if макс_игроков is not None else settings["default_max_players"]
        if min_players > max_players:
            return await interaction.response.send_message("Минимум игроков не может быть больше максимума.", ephemeral=True)

        night_timer = таймер_ночи if таймер_ночи is not None else settings["default_night_timer_sec"]
        discussion_timer = таймер_обсуждения if таймер_обсуждения is not None else settings["default_day_discussion_timer_sec"]
        vote_timer = таймер_голосования if таймер_голосования is not None else settings["default_day_vote_timer_sec"]

        game = mafia_db.create_game(
            interaction.guild.id, interaction.channel.id, interaction.user.id,
            min_players, max_players, night_timer, discussion_timer, vote_timer,
        )
        mafia_db.add_player(game["id"], interaction.user.id)
        players = mafia_db.list_players(game["id"])

        await interaction.response.send_message(embed=build_lobby_embed(game, players), view=self.lobby_view)
        message = await interaction.original_response()
        mafia_db.update_game(game["id"], lobby_message_id=message.id)

    @app_commands.command(name="мафия-стоп", description="Остановить лобби/игру «Мафия» в этом канале")
    @app_commands.default_permissions(manage_guild=True)
    async def stop_game(self, interaction: discord.Interaction):
        game = mafia_db.get_active_game_in_channel(interaction.channel.id)
        if game is None:
            return await interaction.response.send_message("В этом канале нет активной игры.", ephemeral=True)
        if not mafia_core.has_moderator_access(interaction.user):
            return await interaction.response.send_message("Нет доступа.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        if game["status"] == "lobby":
            mafia_db.update_game(game["id"], status="cancelled", ended_at=_now_iso())
            channel = self.bot.get_channel(game["channel_id"])
            if channel is not None and game["lobby_message_id"]:
                try:
                    message = await channel.fetch_message(game["lobby_message_id"])
                    await message.edit(embed=build_lobby_cancelled_embed(game), view=None)
                except discord.HTTPException:
                    pass
        else:
            await self.end_game(game["id"], winner=None)
        await interaction.followup.send("Остановлено.", ephemeral=True)

    # ────────────────────────── Игровой цикл ──────────────────────────

    async def start_game(self, game_id: int):
        game = mafia_db.get_game(game_id)
        if game is None or game["status"] != "lobby":
            return
        guild = self.bot.get_guild(game["guild_id"])
        channel = self.bot.get_channel(game["channel_id"])
        if guild is None or channel is None:
            return

        players = mafia_db.list_players(game_id)
        assignment = mafia_core.assign_roles([p["user_id"] for p in players])
        for user_id, role in assignment.items():
            token = secrets.token_urlsafe(32) if role in mafia_core.NIGHT_ACTION_ROLES else None
            mafia_db.assign_player_role(game_id, user_id, role, token)

        voice_channel_id = None
        try:
            category = channel.category if isinstance(channel, discord.TextChannel) else None
            overwrites = {guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)}
            voice_channel = await guild.create_voice_channel(
                name=f"Мафия • Игра #{game_id}", overwrites=overwrites, category=category,
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
            if role not in mafia_core.NIGHT_ACTION_ROLES:
                continue
            member = guild.get_member(user_id)
            if member is None:
                continue
            player = mafia_db.get_player(game_id, user_id)
            link = f"{frontend}/mafia/{player['token']}"
            try:
                await member.send(
                    content=(
                        f"Игра «Мафия» началась. Твоя роль: **{mafia_core.role_label(role)}**.\n"
                        f"Персональная ссылка для ночных действий (действует всю игру): {link}"
                    )
                )
            except discord.Forbidden:
                pass

        try:
            await channel.send(embed=build_game_started_embed(game, players, voice_channel_id))
        except discord.HTTPException:
            pass

        self._add_event(game_id, 1, "game_started", f"Игроков: {len(players)}.")
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

    async def refresh_vote_tally(self, game_id: int):
        game = mafia_db.get_game(game_id)
        if game is None or not game["vote_message_id"]:
            return
        channel = self.bot.get_channel(game["channel_id"])
        if channel is None:
            return
        guild = self.bot.get_guild(game["guild_id"])
        members = _resolve_alive_members(guild, game_id)
        votes = mafia_db.get_day_votes(game_id, game["round_number"])
        try:
            message = await channel.fetch_message(game["vote_message_id"])
            await message.edit(embed=build_vote_embed(game, members, votes))
        except discord.HTTPException:
            pass

    async def _finish_night(self, game_id: int):
        game = mafia_db.get_game(game_id)
        if game is None or game["status"] != "active" or game["phase"] != "night":
            return
        self._cancel_timer(game_id)

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
                await channel.send(embed=build_morning_embed(died, died_player))
            except discord.HTTPException:
                pass

        self._add_event(game_id, round_number, "night_kill" if died else "night_no_kill",
                         f"Убит: {died}" if died else "Ночь прошла тихо.")

        winner = self._check_winner(game_id)
        if winner:
            return await self.end_game(game_id, winner)

        now_ts = int(time.time())
        game = mafia_db.update_game(
            game_id, phase="day_discussion", phase_deadline_ts=now_ts + game["day_discussion_timer_sec"],
        )
        if channel is not None:
            voice_part = f" В <#{game['voice_channel_id']}>." if game["voice_channel_id"] else ""
            try:
                await channel.send(content=f"💬 Начинается обсуждение.{voice_part} У вас {game['day_discussion_timer_sec']} сек.")
            except discord.HTTPException:
                pass
        self.schedule_phase_timer(game_id)

    async def _finish_day_discussion(self, game_id: int):
        game = mafia_db.get_game(game_id)
        if game is None or game["status"] != "active" or game["phase"] != "day_discussion":
            return
        self._cancel_timer(game_id)

        guild = self.bot.get_guild(game["guild_id"])
        channel = self.bot.get_channel(game["channel_id"])
        members = _resolve_alive_members(guild, game_id)

        now_ts = int(time.time())
        game = mafia_db.update_game(
            game_id, phase="day_vote", phase_deadline_ts=now_ts + game["day_vote_timer_sec"], vote_page=0,
        )

        message = None
        if channel is not None:
            try:
                message = await channel.send(embed=build_vote_embed(game, members, []), view=MafiaVoteView(members, 0))
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

        round_number = game["round_number"]
        votes = {v["voter_user_id"]: v["target_user_id"] for v in mafia_db.get_day_votes(game_id, round_number)}
        lynched = mafia_core.resolve_day_vote(votes)

        channel = self.bot.get_channel(game["channel_id"])

        if lynched is not None:
            mafia_db.eliminate_player(game_id, lynched, round_number, "lynched")
            self._add_event(game_id, round_number, "lynch", f"Казнён: {lynched}")
        else:
            self._add_event(game_id, round_number, "no_lynch", "Никто не казнён (нет большинства).")

        if channel is not None:
            lynched_player = mafia_db.get_player(game_id, lynched) if lynched else None
            try:
                await channel.send(embed=build_lynch_result_embed(lynched, lynched_player))
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
                    content=(
                        f"🌙 Наступает ночь {game['round_number']}. У активных ролей есть {game['night_timer_sec']} сек — "
                        "ссылки уже на руках."
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

        guild = self.bot.get_guild(game["guild_id"])
        channel = self.bot.get_channel(game["channel_id"])
        players = mafia_db.list_players(game_id)

        mafia_db.update_game(game_id, status="finished", phase="ended", winner=winner, ended_at=_now_iso())

        if channel is not None:
            try:
                await channel.send(embed=build_result_embed(winner, players))
            except discord.HTTPException:
                pass

        if game["voice_channel_id"] and guild is not None:
            voice_channel = guild.get_channel(game["voice_channel_id"])
            if voice_channel is not None:
                try:
                    await voice_channel.delete(reason="Игра «Мафия» завершена")
                except discord.HTTPException:
                    pass

        self._add_event(game_id, game["round_number"], "game_ended", f"Победитель: {winner or 'остановлено'}")
        await self._send_log(game, winner)

    async def _send_log(self, game: dict, winner: str | None):
        log_channel_id = mafia_core.get_settings()["log_channel_id"]
        if not log_channel_id:
            return
        channel = self.bot.get_channel(int(log_channel_id))
        if channel is None:
            return
        text = f"Игра #{game['id']} в <#{game['channel_id']}> завершена. Победитель: {winner or 'остановлено досрочно'}."
        try:
            await channel.send(content=text)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    mafia_db.init()
    await bot.add_cog(MafiaCog(bot))
