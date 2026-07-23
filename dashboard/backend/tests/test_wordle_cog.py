"""Тесты кога Вордла — вызов через .callback()/методы кога, паттерн test_xp_commands_cog.py."""

import pytest

import settings_db
import wordle_core
import wordle_db
from wordle import WordleCog, build_board_embed
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember

DAY = 10
ANSWER = "канат"


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("WORDLE_DB_PATH", str(tmp_path / "wordle.db"))
    wordle_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    monkeypatch.setattr(wordle_core, "day_number", lambda today=None: DAY)
    monkeypatch.setattr(wordle_core, "word_for_day", lambda day_no: ANSWER)


class FakeResponse:
    def __init__(self):
        self.messages = []
        self.edits = []

    async def send_message(self, content=None, embed=None, view=None, ephemeral=False, **kwargs):
        self.messages.append({"content": content, "embed": embed, "view": view, "ephemeral": ephemeral})

    async def edit_message(self, embed=None, view=None, **kwargs):
        self.edits.append({"embed": embed, "view": view})


class FakeInteraction:
    guild_id = 1
    def __init__(self, user, guild, channel):
        self.user = user
        self.guild = guild
        self.channel = channel
        self.response = FakeResponse()


def build(enabled=True, channel_id=0):
    player = FakeMember(20, name="player", display_name="Player")
    channel = FakeChannel(500)
    guild = FakeGuild(members=[player], channels=[channel])
    wordle_core.save_config(guild.id, {"enabled": enabled, "channel_id": channel_id, "announce_time": "09:00"})
    bot = FakeBot(guild)
    cog = WordleCog(bot)
    cog.announce_loop.cancel()  # в тестах цикл не нужен
    return cog, guild, player, channel


# ────────────────────────── Гейт модуля ──────────────────────────

@pytest.mark.asyncio
async def test_commands_disabled_module():
    cog, guild, player, channel = build(enabled=False)
    for handler in (cog.open_daily_board,):
        interaction = FakeInteraction(player, guild, channel)
        await handler(interaction)
        assert "отключён" in interaction.response.messages[0]["content"]

    interaction = FakeInteraction(player, guild, channel)
    await WordleCog.training_command.callback(cog, interaction)
    assert "отключён" in interaction.response.messages[0]["content"]

    interaction = FakeInteraction(player, guild, channel)
    await WordleCog.stats_command.callback(cog, interaction)
    assert "отключён" in interaction.response.messages[0]["content"]

    interaction = FakeInteraction(player, guild, channel)
    await WordleCog.top_command.callback(cog, interaction)
    assert "отключён" in interaction.response.messages[0]["content"]


# ────────────────────────── Доска дня ──────────────────────────

@pytest.mark.asyncio
async def test_open_daily_board_creates_game_with_button():
    cog, guild, player, channel = build()
    interaction = FakeInteraction(player, guild, channel)

    await cog.open_daily_board(interaction)

    msg = interaction.response.messages[0]
    assert msg["ephemeral"] is True
    assert f"Вордл №{DAY}" in msg["embed"].title
    assert msg["view"] is not None
    assert wordle_db.get_daily_game(guild.id, player.id, DAY) is not None


@pytest.mark.asyncio
async def test_daily_guess_rejects_unknown_word():
    cog, guild, player, channel = build()
    wordle_db.start_daily_game(guild.id, player.id, DAY)
    interaction = FakeInteraction(player, guild, channel)

    await cog.handle_daily_guess(interaction, "бзыкф")

    assert "нет в словаре" in interaction.response.messages[0]["content"]
    assert wordle_db.get_daily_game(guild.id, player.id, DAY)["guesses"] == []


@pytest.mark.asyncio
async def test_daily_guess_progresses_and_posts_live_card():
    cog, guild, player, channel = build()
    wordle_db.start_daily_game(guild.id, player.id, DAY)
    interaction = FakeInteraction(player, guild, channel)

    await cog.handle_daily_guess(interaction, "катер")

    game = wordle_db.get_daily_game(guild.id, player.id, DAY)
    assert game["guesses"] == ["катер"]
    assert game["finished"] == 0
    # доска обновлена через edit_message
    assert interaction.response.edits
    # live-карточка ушла в канал команды (channel_id=0 в настройках)
    assert channel.send_calls
    assert "играет" in channel.send_calls[0]["content"]
    assert game["live_channel_id"] == channel.id


@pytest.mark.asyncio
async def test_daily_guess_edits_existing_live_card():
    cog, guild, player, channel = build()
    wordle_db.start_daily_game(guild.id, player.id, DAY)
    interaction = FakeInteraction(player, guild, channel)

    await cog.handle_daily_guess(interaction, "катер")
    message_id = wordle_db.get_daily_game(guild.id, player.id, DAY)["live_message_id"]
    await cog.handle_daily_guess(FakeInteraction(player, guild, channel), "школа")

    assert len(channel.send_calls) == 1  # второй раз — edit, не send
    assert channel._messages[message_id].edit_calls


@pytest.mark.asyncio
async def test_daily_win_finishes_game_and_records_stats():
    cog, guild, player, channel = build()
    wordle_db.start_daily_game(guild.id, player.id, DAY)
    interaction = FakeInteraction(player, guild, channel)

    await cog.handle_daily_guess(interaction, ANSWER)

    game = wordle_db.get_daily_game(guild.id, player.id, DAY)
    assert game["finished"] == 1 and game["won"] == 1
    stats = wordle_db.get_stats(guild.id, player.id)
    assert stats["won"] == 1 and stats["streak"] == 1
    assert stats["distribution"][0] == 1
    # финальная доска без кнопки
    assert interaction.response.edits[0]["view"] is None
    assert "сыграл" in channel.send_calls[0]["content"]


@pytest.mark.asyncio
async def test_daily_six_misses_is_loss():
    cog, guild, player, channel = build()
    wordle_db.start_daily_game(guild.id, player.id, DAY)
    wrong = ["катер", "школа", "лодка", "мешок", "рулет"]
    for word in wrong:
        await cog.handle_daily_guess(FakeInteraction(player, guild, channel), word)
    await cog.handle_daily_guess(FakeInteraction(player, guild, channel), "тайга")

    game = wordle_db.get_daily_game(guild.id, player.id, DAY)
    assert game["finished"] == 1 and game["won"] == 0
    assert len(game["guesses"]) == 6
    assert wordle_db.get_stats(guild.id, player.id)["streak"] == 0


@pytest.mark.asyncio
async def test_finished_game_blocks_more_guesses():
    cog, guild, player, channel = build()
    wordle_db.start_daily_game(guild.id, player.id, DAY)
    await cog.handle_daily_guess(FakeInteraction(player, guild, channel), ANSWER)

    interaction = FakeInteraction(player, guild, channel)
    await cog.handle_daily_guess(interaction, "школа")
    assert "завершена" in interaction.response.messages[0]["content"]


# ────────────────────────── Тренировка ──────────────────────────

@pytest.mark.asyncio
async def test_training_flow_win_without_stats(monkeypatch):
    cog, guild, player, channel = build()
    monkeypatch.setattr(wordle_core, "training_word", lambda: "школа")

    interaction = FakeInteraction(player, guild, channel)
    await WordleCog.training_command.callback(cog, interaction)
    assert interaction.response.messages[0]["ephemeral"] is True

    interaction = FakeInteraction(player, guild, channel)
    await cog.handle_training_guess(interaction, "школа")
    assert interaction.response.edits[0]["view"] is None  # победа — кнопки нет
    assert player.id not in cog._training
    # тренировка не пишет ни игр дня, ни статистику
    assert wordle_db.get_daily_game(guild.id, player.id, DAY) is None
    assert wordle_db.get_stats(guild.id, player.id)["played"] == 0
    assert channel.send_calls == []  # и не постит live-карточку


@pytest.mark.asyncio
async def test_training_guess_without_game():
    cog, guild, player, channel = build()
    interaction = FakeInteraction(player, guild, channel)
    await cog.handle_training_guess(interaction, "школа")
    assert "не начата" in interaction.response.messages[0]["content"]


# ────────────────────────── Статистика и топ ──────────────────────────

@pytest.mark.asyncio
async def test_stats_command_empty_and_filled():
    cog, guild, player, channel = build()
    interaction = FakeInteraction(player, guild, channel)
    await WordleCog.stats_command.callback(cog, interaction)
    assert "не играли" in interaction.response.messages[0]["content"]

    wordle_db.record_result(guild.id, player.id, DAY, won=True, attempts=4)
    interaction = FakeInteraction(player, guild, channel)
    await WordleCog.stats_command.callback(cog, interaction)
    embed = interaction.response.messages[0]["embed"]
    assert "статистика" in embed.title


@pytest.mark.asyncio
async def test_top_command_lists_players():
    cog, guild, player, channel = build()
    wordle_db.record_result(guild.id, player.id, DAY, won=True, attempts=4)
    interaction = FakeInteraction(player, guild, channel)

    await WordleCog.top_command.callback(cog, interaction)

    embed = interaction.response.messages[0]["embed"]
    assert "🥇" in embed.description
    assert str(player.id) in embed.description


# ────────────────────────── Ежедневный анонс ──────────────────────────

@pytest.mark.asyncio
async def test_announce_nobody_played():
    cog, guild, player, channel = build(channel_id=500)
    await cog.post_daily_announce(channel, DAY)
    content = channel.send_calls[0]["content"]
    assert "никто не играл" in content
    assert f"Вордл №{DAY}" in content


@pytest.mark.asyncio
async def test_announce_nobody_won_reveals_word():
    cog, guild, player, channel = build(channel_id=500)
    wordle_db.add_guess(guild.id, player.id, DAY - 1, "школа", True, False)
    await cog.post_daily_announce(channel, DAY)
    content = channel.send_calls[0]["content"]
    assert "Никто не отгадал" in content
    assert ANSWER.upper() in content
    assert wordle_db.get_group_streak(guild.id) == 0


@pytest.mark.asyncio
async def test_announce_with_winner_crowns_best_and_streak():
    cog, guild, player, channel = build(channel_id=500)
    other = FakeMember(21, name="other")
    guild.members.append(other)
    wordle_db.add_guess(guild.id, player.id, DAY - 1, "катер", False, False)
    wordle_db.add_guess(guild.id, player.id, DAY - 1, ANSWER, True, True)
    wordle_db.add_guess(guild.id, other.id, DAY - 1, "школа", True, False)

    await cog.post_daily_announce(channel, DAY)

    content = channel.send_calls[0]["content"]
    assert "серию **1 день**" in content
    assert f"👑 **2/6**: <@{player.id}>" in content
    assert f"**X/6**: <@{other.id}>" in content
    assert channel.send_calls[0].get("file") is not None  # сводная PNG-карточка
    assert wordle_db.get_group_streak(guild.id) == 1


def test_build_board_embed_finished_loss_reveals_answer():
    embed = build_board_embed("Вордл №1", ["школа"], ["bbbbb"], "канат", True, False, "ru")
    assert "КАНАТ" in embed.fields[0].value
