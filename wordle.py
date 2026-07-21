"""Ког «Вордл»: русский Wordle в стиле официального Discord-приложения.

- /вордл — общее «слово дня»: 6 попыток, своя доска эфемерна (буквы видит только
  игрок), в канал бот постит live-карточку «X играет» с цветами без букв и
  редактирует её после каждой попытки.
- /вордл-тренировка — безлимитные игры со случайным словом, без статистики.
- /вордл-стата, /вордл-топ — личная статистика и серверный топ.
- Ежедневный анонс: в настроенное время бот подводит итоги вчерашнего дня
  (серия сервера, 👑 лучший результат, сводная PNG-карточка) и зовёт играть
  кнопкой «Играть» (persistent view — переживает перезапуск).

Модуль выключен по умолчанию, настраивается в дашборде (раздел «Развлечения»).
"""

import asyncio
import io
import logging
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks

import wordle_card
import wordle_core
import wordle_db

logger = logging.getLogger("wordle")

DISABLED_TEXT = "Модуль «Вордл» отключён."


async def _avatar_bytes(user) -> bytes | None:
    try:
        return await user.display_avatar.read()
    except (discord.HTTPException, AttributeError):
        return None


def _card_file(png: bytes) -> discord.File:
    return discord.File(io.BytesIO(png), filename="wordle.png")


def build_board_embed(day_title: str, guesses: list[str], states: list[str], answer: str,
                      finished: bool, won: bool) -> discord.Embed:
    lines = wordle_core.board_lines(guesses, states)
    embed = discord.Embed(title=day_title, description="\n".join(lines), color=discord.Color.from_str("#538d4e"))
    if finished:
        score = wordle_core.result_score_text(won, len(guesses))
        if won:
            embed.add_field(name="Результат", value=f"🎉 Отгадано: **{score}**", inline=False)
        else:
            embed.add_field(name="Результат", value=f"💀 **{score}** — слово было **{answer.upper()}**", inline=False)
    else:
        present, absent = wordle_core.letter_hints(guesses, states, answer)
        hints = []
        if present:
            hints.append(f"🟡 В слове: {present}")
        if absent:
            hints.append(f"⚫ Нет в слове: {absent}")
        hints.append(f"Осталось попыток: **{wordle_core.MAX_ATTEMPTS - len(guesses)}**")
        embed.add_field(name="Подсказки", value="\n".join(hints), inline=False)
    return embed


class GuessModal(discord.ui.Modal):
    def __init__(self, cog: "WordleCog", training: bool):
        super().__init__(title="Вордл: ваша догадка")
        self.cog = cog
        self.training = training
        self.word_input = discord.ui.TextInput(
            label=f"Слово из {wordle_core.WORD_LEN} букв",
            min_length=wordle_core.WORD_LEN,
            max_length=wordle_core.WORD_LEN,
            placeholder="слово",
        )
        self.add_item(self.word_input)

    async def on_submit(self, interaction: discord.Interaction):
        if self.training:
            await self.cog.handle_training_guess(interaction, str(self.word_input.value))
        else:
            await self.cog.handle_daily_guess(interaction, str(self.word_input.value))


class BoardView(discord.ui.View):
    """Кнопка «Ввести слово» под эфемерной доской (живёт до конца игры)."""

    def __init__(self, cog: "WordleCog", training: bool):
        super().__init__(timeout=3600)
        self.cog = cog
        self.training = training

    @discord.ui.button(label="Ввести слово", style=discord.ButtonStyle.success, emoji="⌨️")
    async def enter_word(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.send_modal(GuessModal(self.cog, self.training))


class PlayNowView(discord.ui.View):
    """Persistent-кнопка «Играть» под ежедневным анонсом."""

    def __init__(self, cog: "WordleCog"):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Играть", style=discord.ButtonStyle.primary, custom_id="wordle:play")
    async def play(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self.cog.open_daily_board(interaction)


class WordleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # user_id -> {"answer", "guesses", "states"} — тренировка живёт только в памяти
        self._training: dict[int, dict] = {}
        self.announce_loop.start()

    def cog_unload(self):
        self.announce_loop.cancel()

    # ────────────────────────── Доска дня ──────────────────────────

    async def open_daily_board(self, interaction: discord.Interaction):
        settings = wordle_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)

        day_no = wordle_core.day_number()
        answer = wordle_core.word_for_day(day_no)
        game = wordle_db.get_daily_game(interaction.user.id, day_no) or wordle_db.start_daily_game(
            interaction.user.id, day_no
        )
        states = [wordle_core.evaluate(g, answer) for g in game["guesses"]]
        finished = bool(game["finished"])

        embed = build_board_embed(
            f"Вордл №{day_no}", game["guesses"], states, answer, finished, bool(game["won"])
        )
        view = None if finished else BoardView(self, training=False)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def handle_daily_guess(self, interaction: discord.Interaction, raw_word: str):
        settings = wordle_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)

        day_no = wordle_core.day_number()
        answer = wordle_core.word_for_day(day_no)
        game = wordle_db.get_daily_game(interaction.user.id, day_no) or wordle_db.start_daily_game(
            interaction.user.id, day_no
        )
        if game["finished"] or len(game["guesses"]) >= wordle_core.MAX_ATTEMPTS:
            return await interaction.response.send_message("Игра дня уже завершена — жди следующее слово!", ephemeral=True)

        word = wordle_core.normalize(raw_word)
        error = wordle_core.guess_error(word)
        if error:
            return await interaction.response.send_message(error, ephemeral=True)

        state = wordle_core.evaluate(word, answer)
        won = wordle_core.is_win(state)
        finished = won or len(game["guesses"]) + 1 >= wordle_core.MAX_ATTEMPTS
        game = wordle_db.add_guess(interaction.user.id, day_no, word, finished, won)
        states = [wordle_core.evaluate(g, answer) for g in game["guesses"]]

        if finished:
            wordle_db.record_result(interaction.user.id, day_no, won, len(game["guesses"]))

        embed = build_board_embed(f"Вордл №{day_no}", game["guesses"], states, answer, finished, won)
        view = None if finished else BoardView(self, training=False)
        await interaction.response.edit_message(embed=embed, view=view)

        try:
            await self._update_live_card(interaction, game, states, day_no, finished, won)
        except discord.HTTPException:
            logger.warning("Не удалось обновить live-карточку Вордла (user=%s)", interaction.user.id)

    async def _update_live_card(self, interaction: discord.Interaction, game: dict,
                                states: list[str], day_no: int, finished: bool, won: bool):
        """Публичная карточка «X играет»: создаётся на первой догадке, дальше редактируется."""
        avatar = await _avatar_bytes(interaction.user)
        png = await asyncio.to_thread(wordle_card.render_playing_card, avatar, day_no, states)
        name = interaction.user.display_name
        if finished:
            score = wordle_core.result_score_text(won, len(game["guesses"]))
            content = f"**{name}** сыграл(а) в Вордл №{day_no}: **{score}**"
        else:
            content = f"**{name}** играет в Вордл №{day_no}…"

        channel = None
        if game["live_channel_id"] and game["live_message_id"]:
            channel = self.bot.get_channel(game["live_channel_id"])
        if channel is not None:
            try:
                message = await channel.fetch_message(game["live_message_id"])
                await message.edit(content=content, attachments=[_card_file(png)])
                return
            except discord.HTTPException:
                pass  # сообщение удалили — публикуем заново ниже

        settings = wordle_core.get_settings(interaction.guild.id)
        channel = self.bot.get_channel(int(settings["channel_id"])) if settings["channel_id"] else None
        if channel is None:
            channel = interaction.channel
        if channel is None or not hasattr(channel, "send"):
            return
        message = await channel.send(content=content, file=_card_file(png))
        wordle_db.set_live_message(interaction.user.id, day_no, channel.id, message.id)

    # ────────────────────────── Тренировка ──────────────────────────

    async def handle_training_guess(self, interaction: discord.Interaction, raw_word: str):
        game = self._training.get(interaction.user.id)
        if game is None:
            return await interaction.response.send_message(
                "Тренировка не начата — запусти /вордл-тренировка.", ephemeral=True
            )

        word = wordle_core.normalize(raw_word)
        error = wordle_core.guess_error(word)
        if error:
            return await interaction.response.send_message(error, ephemeral=True)

        state = wordle_core.evaluate(word, game["answer"])
        game["guesses"].append(word)
        game["states"].append(state)
        won = wordle_core.is_win(state)
        finished = won or len(game["guesses"]) >= wordle_core.MAX_ATTEMPTS

        embed = build_board_embed(
            "Вордл · тренировка", game["guesses"], game["states"], game["answer"], finished, won
        )
        view = None if finished else BoardView(self, training=True)
        if finished:
            self._training.pop(interaction.user.id, None)
        await interaction.response.edit_message(embed=embed, view=view)

    # ────────────────────────── Команды ──────────────────────────

    @app_commands.command(name="вордл", description="Слово дня: 6 попыток угадать слово из 5 букв")
    async def wordle_command(self, interaction: discord.Interaction):
        await self.open_daily_board(interaction)

    @app_commands.command(name="вордл-тренировка", description="Тренировочный Вордл со случайным словом (без статистики)")
    async def training_command(self, interaction: discord.Interaction):
        settings = wordle_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)

        game = {"answer": wordle_core.training_word(), "guesses": [], "states": []}
        self._training[interaction.user.id] = game
        embed = build_board_embed("Вордл · тренировка", [], [], game["answer"], False, False)
        await interaction.response.send_message(embed=embed, view=BoardView(self, training=True), ephemeral=True)

    @app_commands.command(name="вордл-стата", description="Ваша статистика Вордла: победы, стрики, распределение")
    async def stats_command(self, interaction: discord.Interaction):
        settings = wordle_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)

        stats = wordle_db.get_stats(interaction.user.id)
        if stats["played"] == 0:
            return await interaction.response.send_message(
                "Вы ещё не играли в Вордл — начните с /вордл!", ephemeral=True
            )

        win_rate = round(stats["won"] / stats["played"] * 100)
        max_bucket = max(stats["distribution"]) or 1
        dist_lines = []
        for i, count in enumerate(stats["distribution"], start=1):
            bar = "█" * max(1, round(count / max_bucket * 12)) if count else "▏"
            dist_lines.append(f"`{i}` {bar} {count}")

        embed = discord.Embed(title="📊 Ваша статистика Вордла", color=discord.Color.from_str("#538d4e"))
        embed.add_field(name="Сыграно", value=str(stats["played"]))
        embed.add_field(name="Побед", value=f"{stats['won']} ({win_rate}%)")
        embed.add_field(name="Серия", value=f"🔥 {stats['streak']} (макс. {stats['max_streak']})")
        embed.add_field(name="Распределение попыток", value="\n".join(dist_lines), inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="вордл-топ", description="Топ игроков сервера в Вордл")
    async def top_command(self, interaction: discord.Interaction):
        settings = wordle_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)

        top = wordle_db.top_players(10)
        if not top:
            return await interaction.response.send_message("В Вордл ещё никто не играл.", ephemeral=True)

        medals = ("🥇", "🥈", "🥉")
        lines = []
        for i, stats in enumerate(top):
            prefix = medals[i] if i < len(medals) else f"`{i + 1}.`"
            lines.append(
                f"{prefix} <@{stats['user_id']}> — побед: **{stats['won']}** из {stats['played']}, "
                f"макс. серия: {stats['max_streak']}"
            )
        embed = discord.Embed(
            title="🏆 Топ Вордла", description="\n".join(lines), color=discord.Color.from_str("#538d4e")
        )
        await interaction.response.send_message(embed=embed)

    # ────────────────────────── Ежедневный анонс ──────────────────────────

    @tasks.loop(minutes=1)
    async def announce_loop(self):
        # Всё тело под try/except: необработанное исключение навсегда остановило бы
        # tasks.loop (урок «Ежедневной рубрики»).
        try:
            day_no = wordle_core.day_number()
            if wordle_db.get_last_announced_day() >= day_no:
                return

            now = datetime.now(wordle_core.MSK)

            for guild in self.bot.guilds:
                settings = wordle_core.get_settings(guild.id)
                if not settings["enabled"] or not settings["channel_id"]:
                    continue
                if not wordle_core.is_valid_announce_time(settings["announce_time"]):
                    continue

                hour, minute = (int(p) for p in settings["announce_time"].split(":"))
                if (now.hour, now.minute) != (hour, minute):
                    continue

                channel = self.bot.get_channel(int(settings["channel_id"]))
                if channel is None:
                    continue

                try:
                    await self.post_daily_announce(channel, day_no)
                    # Глобальный (не per-guild) трекер — как и раньше, пока бот работает на
                    # одном сервере. С несколькими серверами и разным announce_time это
                    # потребует per-guild отметки (Фаза 2.2/2.4 MULTIGUILD_PLAN.md).
                    wordle_db.set_last_announced_day(day_no)
                except Exception:
                    logger.exception("announce_loop: не удалось опубликовать анонс для guild %s", guild.id)
        except Exception:
            logger.exception("announce_loop: ошибка итерации — цикл продолжает работать")

    @announce_loop.error
    async def announce_loop_error(self, _error: BaseException):
        logger.exception("announce_loop: критическая ошибка — перезапуск цикла")
        self.announce_loop.restart()

    @announce_loop.before_loop
    async def before_announce_loop(self):
        await self.bot.wait_until_ready()

    async def post_daily_announce(self, channel, day_no: int):
        """Итоги вчерашнего дня + приглашение сыграть сегодня."""
        yesterday = day_no - 1
        games = [g for g in wordle_db.list_day_games(yesterday) if g["finished"]]
        winners = sorted((g for g in games if g["won"]), key=lambda g: len(g["guesses"]))
        streak = wordle_db.update_group_streak(yesterday, bool(winners))

        lines = []
        if not games:
            lines.append("Вчера никто не играл в Вордл… но сегодня новый день 🌞")
        elif not winners:
            lines.append("Никто не отгадал вчерашний Вордл… но сегодня новый день 🌞")
        else:
            day_word = "день" if streak == 1 else "дня" if streak in (2, 3, 4) else "дней"
            lines.append(f"Ваш сервер держит серию **{streak} {day_word}**! 🔥 Вчерашние результаты:")
            lines.extend(self._result_lines(games))
        if games:
            answer = wordle_core.word_for_day(yesterday)
            lines.append(f"Вчерашнее слово: **{answer.upper()}**")
        lines.append(f"Сегодня — Вордл №{day_no}. Жми «Играть»!")

        file = None
        if games:
            players = []
            for game in games[:5]:
                user = self.bot.get_user(game["user_id"])
                avatar = await _avatar_bytes(user) if user else None
                answer = wordle_core.word_for_day(yesterday)
                players.append({
                    "avatar_bytes": avatar,
                    "states_rows": [wordle_core.evaluate(g, answer) for g in game["guesses"]],
                })
            try:
                png = await asyncio.to_thread(wordle_card.render_summary_card, yesterday, players)
                file = _card_file(png)
            except Exception:
                logger.exception("Не удалось отрисовать сводную карточку Вордла")

        kwargs = {"content": "\n".join(lines), "view": PlayNowView(self)}
        if file is not None:
            kwargs["file"] = file
        await channel.send(**kwargs)

    def _result_lines(self, games: list[dict]) -> list[str]:
        """Строки «👑 4/6: @user» — корона у лучшего результата дня."""
        def sort_key(game):
            return (0, len(game["guesses"])) if game["won"] else (1, len(game["guesses"]))

        ordered = sorted(games, key=sort_key)
        best_attempts = len(ordered[0]["guesses"]) if ordered and ordered[0]["won"] else None
        lines = []
        for game in ordered:
            score = wordle_core.result_score_text(bool(game["won"]), len(game["guesses"]))
            crown = "👑 " if game["won"] and len(game["guesses"]) == best_attempts else ""
            lines.append(f"{crown}**{score}**: <@{game['user_id']}>")
        return lines


async def setup(bot: commands.Bot):
    wordle_db.init()
    cog = WordleCog(bot)
    await bot.add_cog(cog)
    bot.add_view(PlayNowView(cog))  # persistent «Играть» переживает перезапуск
