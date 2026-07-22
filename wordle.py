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

import i18n
import slash_registry
import wordle_card
import wordle_core
import wordle_db

logger = logging.getLogger("wordle")


async def _avatar_bytes(user) -> bytes | None:
    try:
        return await user.display_avatar.read()
    except (discord.HTTPException, AttributeError):
        return None


def _card_file(png: bytes) -> discord.File:
    return discord.File(io.BytesIO(png), filename="wordle.png")


def _streak_day_word(streak: int, lang: str) -> str:
    if streak == 1:
        return i18n.t("wordle.streak.day_one", lang)
    if lang == "ru" and streak in (2, 3, 4):
        return i18n.t("wordle.streak.day_few", lang)
    return i18n.t("wordle.streak.day_many", lang)


def build_board_embed(
    day_title: str,
    guesses: list[str],
    states: list[str],
    answer: str,
    finished: bool,
    won: bool,
    lang: str = i18n.DEFAULT_LANGUAGE,
) -> discord.Embed:
    lines = wordle_core.board_lines(guesses, states)
    embed = discord.Embed(title=day_title, description="\n".join(lines), color=discord.Color.from_str("#538d4e"))
    if finished:
        score = wordle_core.result_score_text(won, len(guesses))
        if won:
            embed.add_field(
                name=i18n.t("wordle.board.result", lang),
                value=i18n.t("wordle.board.won", lang, score=score),
                inline=False,
            )
        else:
            embed.add_field(
                name=i18n.t("wordle.board.result", lang),
                value=i18n.t("wordle.board.lost", lang, score=score, answer=answer.upper()),
                inline=False,
            )
    else:
        present, absent = wordle_core.letter_hints(guesses, states, answer)
        hints = []
        if present:
            hints.append(i18n.t("wordle.board.hint_present", lang, letters=present))
        if absent:
            hints.append(i18n.t("wordle.board.hint_absent", lang, letters=absent))
        hints.append(i18n.t("wordle.board.attempts_left", lang, count=wordle_core.MAX_ATTEMPTS - len(guesses)))
        embed.add_field(name=i18n.t("wordle.board.hints", lang), value="\n".join(hints), inline=False)
    return embed


class GuessModal(discord.ui.Modal):
    def __init__(self, cog: "WordleCog", training: bool, lang: str):
        super().__init__(title=i18n.t("wordle.modal.title", lang))
        self.cog = cog
        self.training = training
        self.lang = lang
        self.word_input = discord.ui.TextInput(
            label=i18n.t("wordle.modal.word_label", lang, word_len=wordle_core.WORD_LEN),
            min_length=wordle_core.WORD_LEN,
            max_length=wordle_core.WORD_LEN,
            placeholder=i18n.t("wordle.modal.placeholder", lang),
        )
        self.add_item(self.word_input)

    async def on_submit(self, interaction: discord.Interaction):
        if self.training:
            await self.cog.handle_training_guess(interaction, str(self.word_input.value))
        else:
            await self.cog.handle_daily_guess(interaction, str(self.word_input.value))


class BoardView(discord.ui.View):
    """Кнопка «Ввести слово» под эфемерной доской (живёт до конца игры)."""

    def __init__(self, cog: "WordleCog", training: bool, lang: str):
        super().__init__(timeout=3600)
        self.cog = cog
        self.training = training
        self.lang = lang
        self._set_button_labels()

    def _set_button_labels(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.label = i18n.t("wordle.button.enter_word", self.lang)

    @discord.ui.button(label="Ввести слово", style=discord.ButtonStyle.success, emoji="⌨️")
    async def enter_word(self, interaction: discord.Interaction, _button: discord.ui.Button):
        lang = i18n.lang_for(interaction.guild_id)
        await interaction.response.send_modal(GuessModal(self.cog, self.training, lang))


class PlayNowView(discord.ui.View):
    """Persistent-кнопка «Играть» под ежедневным анонсом."""

    def __init__(self, cog: "WordleCog", lang: str | None = None):
        super().__init__(timeout=None)
        self.cog = cog
        lang = lang or i18n.DEFAULT_LANGUAGE
        for child in self.children:
            if isinstance(child, discord.ui.Button) and child.custom_id == "wordle:play":
                child.label = i18n.t("wordle.button.play", lang)

    @discord.ui.button(label="Играть", style=discord.ButtonStyle.primary, custom_id="wordle:play")
    async def play(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self.cog.open_daily_board(interaction)


class WordleCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._training: dict[int, dict] = {}
        self.announce_loop.start()

    def cog_unload(self):
        self.announce_loop.cancel()

    async def open_daily_board(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        settings = wordle_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "wordle"), ephemeral=True,
            )

        day_no = wordle_core.day_number()
        answer = wordle_core.word_for_day(day_no)
        game = wordle_db.get_daily_game(interaction.user.id, day_no) or wordle_db.start_daily_game(
            interaction.user.id, day_no
        )
        states = [wordle_core.evaluate(g, answer) for g in game["guesses"]]
        finished = bool(game["finished"])

        embed = build_board_embed(
            i18n.t("wordle.daily.title", lang, day_no=day_no),
            game["guesses"],
            states,
            answer,
            finished,
            bool(game["won"]),
            lang,
        )
        view = None if finished else BoardView(self, training=False, lang=lang)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    async def handle_daily_guess(self, interaction: discord.Interaction, raw_word: str):
        lang = i18n.lang_for(interaction.guild_id)
        settings = wordle_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "wordle"), ephemeral=True,
            )

        day_no = wordle_core.day_number()
        answer = wordle_core.word_for_day(day_no)
        game = wordle_db.get_daily_game(interaction.user.id, day_no) or wordle_db.start_daily_game(
            interaction.user.id, day_no
        )
        if game["finished"] or len(game["guesses"]) >= wordle_core.MAX_ATTEMPTS:
            return await interaction.response.send_message(
                i18n.t("wordle.error.game_finished", lang), ephemeral=True,
            )

        word = wordle_core.normalize(raw_word)
        error = wordle_core.guess_error(word, lang=lang)
        if error:
            return await interaction.response.send_message(error, ephemeral=True)

        state = wordle_core.evaluate(word, answer)
        won = wordle_core.is_win(state)
        finished = won or len(game["guesses"]) + 1 >= wordle_core.MAX_ATTEMPTS
        game = wordle_db.add_guess(interaction.user.id, day_no, word, finished, won)
        states = [wordle_core.evaluate(g, answer) for g in game["guesses"]]

        if finished:
            wordle_db.record_result(interaction.user.id, day_no, won, len(game["guesses"]))

        embed = build_board_embed(
            i18n.t("wordle.daily.title", lang, day_no=day_no),
            game["guesses"],
            states,
            answer,
            finished,
            won,
            lang,
        )
        view = None if finished else BoardView(self, training=False, lang=lang)
        await interaction.response.edit_message(embed=embed, view=view)

        try:
            await self._update_live_card(interaction, game, states, day_no, finished, won, lang)
        except discord.HTTPException:
            logger.warning("Не удалось обновить live-карточку Вордла (user=%s)", interaction.user.id)

    async def _update_live_card(
        self,
        interaction: discord.Interaction,
        game: dict,
        states: list[str],
        day_no: int,
        finished: bool,
        won: bool,
        lang: str,
    ):
        avatar = await _avatar_bytes(interaction.user)
        png = await asyncio.to_thread(wordle_card.render_playing_card, avatar, day_no, states)
        name = interaction.user.display_name
        if finished:
            score = wordle_core.result_score_text(won, len(game["guesses"]))
            content = i18n.t("wordle.live.finished", lang, name=name, day_no=day_no, score=score)
        else:
            content = i18n.t("wordle.live.playing", lang, name=name, day_no=day_no)

        channel = None
        if game["live_channel_id"] and game["live_message_id"]:
            channel = self.bot.get_channel(game["live_channel_id"])
        if channel is not None:
            try:
                message = await channel.fetch_message(game["live_message_id"])
                await message.edit(content=content, attachments=[_card_file(png)])
                return
            except discord.HTTPException:
                pass

        settings = wordle_core.get_settings(interaction.guild.id)
        channel = self.bot.get_channel(int(settings["channel_id"])) if settings["channel_id"] else None
        if channel is None:
            channel = interaction.channel
        if channel is None or not hasattr(channel, "send"):
            return
        message = await channel.send(content=content, file=_card_file(png))
        wordle_db.set_live_message(interaction.user.id, day_no, channel.id, message.id)

    async def handle_training_guess(self, interaction: discord.Interaction, raw_word: str):
        lang = i18n.lang_for(interaction.guild_id)
        game = self._training.get(interaction.user.id)
        if game is None:
            return await interaction.response.send_message(
                i18n.t("wordle.error.training_not_started", lang), ephemeral=True,
            )

        word = wordle_core.normalize(raw_word)
        error = wordle_core.guess_error(word, lang=lang)
        if error:
            return await interaction.response.send_message(error, ephemeral=True)

        state = wordle_core.evaluate(word, game["answer"])
        game["guesses"].append(word)
        game["states"].append(state)
        won = wordle_core.is_win(state)
        finished = won or len(game["guesses"]) >= wordle_core.MAX_ATTEMPTS

        embed = build_board_embed(
            i18n.t("wordle.training.title", lang),
            game["guesses"],
            game["states"],
            game["answer"],
            finished,
            won,
            lang,
        )
        view = None if finished else BoardView(self, training=True, lang=lang)
        if finished:
            self._training.pop(interaction.user.id, None)
        await interaction.response.edit_message(embed=embed, view=view)

    @app_commands.command(name="вордл", description="Слово дня: 6 попыток угадать слово из 5 букв")
    async def wordle_command(self, interaction: discord.Interaction):
        await self.open_daily_board(interaction)

    @app_commands.command(name="вордл-тренировка", description="Тренировочный Вордл со случайным словом (без статистики)")
    async def training_command(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        settings = wordle_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "wordle"), ephemeral=True,
            )

        game = {"answer": wordle_core.training_word(), "guesses": [], "states": []}
        self._training[interaction.user.id] = game
        embed = build_board_embed(
            i18n.t("wordle.training.title", lang), [], [], game["answer"], False, False, lang,
        )
        await interaction.response.send_message(
            embed=embed, view=BoardView(self, training=True, lang=lang), ephemeral=True,
        )

    @app_commands.command(name="вордл-стата", description="Ваша статистика Вордла: победы, стрики, распределение")
    async def stats_command(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        settings = wordle_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "wordle"), ephemeral=True,
            )

        stats = wordle_db.get_stats(interaction.user.id)
        if stats["played"] == 0:
            return await interaction.response.send_message(
                i18n.t("wordle.stats.empty", lang), ephemeral=True,
            )

        win_rate = round(stats["won"] / stats["played"] * 100)
        max_bucket = max(stats["distribution"]) or 1
        dist_lines = []
        for i, count in enumerate(stats["distribution"], start=1):
            bar = "█" * max(1, round(count / max_bucket * 12)) if count else "▏"
            dist_lines.append(f"`{i}` {bar} {count}")

        embed = discord.Embed(title=i18n.t("wordle.stats.title", lang), color=discord.Color.from_str("#538d4e"))
        embed.add_field(name=i18n.t("wordle.stats.played", lang), value=str(stats["played"]))
        embed.add_field(
            name=i18n.t("wordle.stats.won", lang),
            value=i18n.t("wordle.stats.won_value", lang, won=stats["won"], rate=win_rate),
        )
        embed.add_field(
            name=i18n.t("wordle.stats.streak", lang),
            value=i18n.t("wordle.stats.streak_value", lang, streak=stats["streak"], max_streak=stats["max_streak"]),
        )
        embed.add_field(
            name=i18n.t("wordle.stats.distribution", lang),
            value="\n".join(dist_lines),
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="вордл-топ", description="Топ игроков сервера в Вордл")
    async def top_command(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        settings = wordle_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "wordle"), ephemeral=True,
            )

        top = wordle_db.top_players(10)
        if not top:
            return await interaction.response.send_message(i18n.t("wordle.top.empty", lang), ephemeral=True)

        medals = ("🥇", "🥈", "🥉")
        lines = []
        for i, stats in enumerate(top):
            prefix = medals[i] if i < len(medals) else f"`{i + 1}.`"
            lines.append(i18n.t(
                "wordle.top.line",
                lang,
                prefix=prefix,
                user_id=stats["user_id"],
                won=stats["won"],
                played=stats["played"],
                max_streak=stats["max_streak"],
            ))
        embed = discord.Embed(
            title=i18n.t("wordle.top.title", lang),
            description="\n".join(lines),
            color=discord.Color.from_str("#538d4e"),
        )
        await interaction.response.send_message(embed=embed)

    @tasks.loop(minutes=1)
    async def announce_loop(self):
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
        lang = i18n.lang_for(channel.guild.id if channel.guild else None)
        yesterday = day_no - 1
        games = [g for g in wordle_db.list_day_games(yesterday) if g["finished"]]
        winners = sorted((g for g in games if g["won"]), key=lambda g: len(g["guesses"]))
        streak = wordle_db.update_group_streak(yesterday, bool(winners))

        lines = []
        if not games:
            lines.append(i18n.t("wordle.announce.nobody_played", lang))
        elif not winners:
            lines.append(i18n.t("wordle.announce.nobody_won", lang))
        else:
            day_word = _streak_day_word(streak, lang)
            lines.append(i18n.t("wordle.announce.streak", lang, streak=streak, day_word=day_word))
            lines.extend(self._result_lines(games, lang))
        if games:
            answer = wordle_core.word_for_day(yesterday)
            lines.append(i18n.t("wordle.announce.yesterday_word", lang, word=answer.upper()))
        lines.append(i18n.t("wordle.announce.today", lang, day_no=day_no))

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

        kwargs = {"content": "\n".join(lines), "view": PlayNowView(self, lang)}
        if file is not None:
            kwargs["file"] = file
        await channel.send(**kwargs)

    def _result_lines(self, games: list[dict], lang: str) -> list[str]:
        def sort_key(game):
            return (0, len(game["guesses"])) if game["won"] else (1, len(game["guesses"]))

        ordered = sorted(games, key=sort_key)
        best_attempts = len(ordered[0]["guesses"]) if ordered and ordered[0]["won"] else None
        lines = []
        for game in ordered:
            score = wordle_core.result_score_text(bool(game["won"]), len(game["guesses"]))
            crown = "👑 " if game["won"] and len(game["guesses"]) == best_attempts else ""
            lines.append(i18n.t(
                "wordle.announce.result_line",
                lang,
                crown=crown,
                score=score,
                user_id=game["user_id"],
            ))
        return lines


async def setup(bot: commands.Bot):
    wordle_db.init()
    cog = WordleCog(bot)
    slash_registry.register_wordle(cog)
    await bot.add_cog(cog)
    bot.add_view(PlayNowView(cog))
