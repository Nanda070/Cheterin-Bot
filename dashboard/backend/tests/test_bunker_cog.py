"""Тесты игрового цикла кога «Бункер»: старт игры (раздача карточек, голосовой канал,
личные ссылки), завершение игры (удаление голосового канала), режимы раздачи карточек."""

import discord
import pytest

import bunker_db
import settings_db
from bunker import BunkerCog
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("BUNKER_DB_PATH", str(tmp_path / "bunker.db"))
    bunker_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    monkeypatch.setenv("DASHBOARD_FRONTEND_URL", "https://dash.example")


def build(player_ids=(20, 21, 22, 23)):
    members = [FakeMember(uid, name=f"p{uid}") for uid in player_ids]
    channel = FakeChannel(500, name="bunker-game")
    guild = FakeGuild(members=members, channels=[channel])
    bot = FakeBot(guild)
    cog = BunkerCog(bot)
    bot.get_cog = lambda name: cog if name == "BunkerCog" else None
    return bot, guild, channel, cog, members


def _make_lobby(guild, channel, player_ids, unique_cards=True):
    game = bunker_db.create_game(guild.id, channel.id, player_ids[0], 4, 12, 180, 90, unique_cards)
    for uid in player_ids:
        bunker_db.add_player(game["id"], uid)
    return game


def _cleanup_timer(cog, game_id):
    task = cog._timers.get(game_id)
    if task:
        task.cancel()


@pytest.mark.asyncio
async def test_start_game_uses_cheterin_online_when_frontend_url_unset(monkeypatch):
    monkeypatch.delenv("DASHBOARD_FRONTEND_URL", raising=False)
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    player_ids = (20, 21, 22, 23)
    bot, guild, channel, cog, members = build(player_ids)
    game = _make_lobby(guild, channel, player_ids)

    await cog.start_game(game["id"])
    try:
        for member in members:
            player = bunker_db.get_player(game["id"], member.id)
            dm_text = member.send_calls[0]["content"]
            assert f"https://cheterin.online/bunker/{player['token']}" in dm_text
            assert player["avatar_url"] == str(member.display_avatar.url)
    finally:
        _cleanup_timer(cog, game["id"])


@pytest.mark.asyncio
async def test_start_game_full_flow():
    player_ids = (20, 21, 22, 23)
    bot, guild, channel, cog, members = build(player_ids)
    game = _make_lobby(guild, channel, player_ids)

    await cog.start_game(game["id"])
    try:
        updated = bunker_db.get_game(game["id"])
        assert updated["status"] == "active"
        assert updated["phase"] == "discussion"
        assert updated["round_number"] == 1
        assert updated["bunker_capacity"] == 2  # половина от 4 по умолчанию
        assert updated["catastrophe_name"]
        assert updated["bunker_conditions_name"]
        assert updated["phase_deadline_ts"] is not None

        # Голосовой канал создан, назван по игре и сохранён в БД.
        assert len(guild.created_voice_channels) == 1
        voice = guild.created_voice_channels[0]
        assert voice.name == f"Бункер • Игра #{game['id']}"
        assert updated["voice_channel_id"] == voice.id

        # Каждый игрок получил карточку, токен и личное сообщение со ссылкой.
        for member in members:
            player = bunker_db.get_player(game["id"], member.id)
            assert player["character"] is not None
            assert player["token"]
            assert len(player["character"]["special_abilities"]) == 2
            assert len(member.send_calls) == 1
            dm_text = member.send_calls[0]["content"]
            assert f"https://dash.example/bunker/{player['token']}" in dm_text
            assert f"<#{voice.id}>" in dm_text

        # unique_cards=True (дефолт): профессии не повторяются между игроками.
        professions = [bunker_db.get_player(game["id"], uid)["character"]["profession"]["name"] for uid in player_ids]
        assert len(set(professions)) == len(professions)

        # Объявление о старте отправлено в канал игры.
        assert any("embed" in call for call in channel.send_calls)
    finally:
        _cleanup_timer(cog, game["id"])


@pytest.mark.asyncio
async def test_start_game_with_repeats_mode(monkeypatch):
    import bunker_data

    tiny_pool = [{"id": 1, "name": "Единственная профессия", "category": "Тест"}]
    monkeypatch.setattr(bunker_data, "PROFESSIONS", tiny_pool)

    player_ids = (20, 21, 22, 23)
    bot, guild, channel, cog, _ = build(player_ids)
    game = _make_lobby(guild, channel, player_ids, unique_cards=False)

    await cog.start_game(game["id"])
    try:
        professions = [bunker_db.get_player(game["id"], uid)["character"]["profession"]["name"] for uid in player_ids]
        assert professions == ["Единственная профессия"] * 4  # с повторами — из пула в одну карту
    finally:
        _cleanup_timer(cog, game["id"])


@pytest.mark.asyncio
async def test_start_game_survives_voice_channel_failure():
    player_ids = (20, 21, 22, 23)
    bot, guild, channel, cog, _ = build(player_ids)
    guild.create_voice_channel_raises = discord.HTTPException.__new__(discord.HTTPException)
    game = _make_lobby(guild, channel, player_ids)

    await cog.start_game(game["id"])
    try:
        updated = bunker_db.get_game(game["id"])
        assert updated["status"] == "active"
        assert updated["voice_channel_id"] is None
    finally:
        _cleanup_timer(cog, game["id"])


@pytest.mark.asyncio
async def test_refresh_vote_tally_edits_single_message_instead_of_spamming():
    player_ids = (20, 21, 22, 23)
    bot, guild, channel, cog, _ = build(player_ids)
    game = _make_lobby(guild, channel, player_ids)
    await cog.start_game(game["id"])
    _cleanup_timer(cog, game["id"])
    game_id = game["id"]

    await cog._finish_discussion(game_id)
    _cleanup_timer(cog, game_id)

    updated = bunker_db.get_game(game_id)
    assert updated["phase"] == "vote"
    assert updated["vote_message_id"] is not None
    sends_after_open = len(channel.send_calls)

    bunker_db.upsert_vote(game_id, 1, 20, 21)
    await cog.refresh_vote_tally(game_id)
    bunker_db.upsert_vote(game_id, 1, 21, 20)
    await cog.refresh_vote_tally(game_id)

    assert len(channel.send_calls) == sends_after_open  # новых сообщений нет
    tally_message = channel._messages[updated["vote_message_id"]]
    assert len(tally_message.edit_calls) == 2  # табло отредактировано по разу на голос


@pytest.mark.asyncio
async def test_end_game_deletes_voice_channel():
    player_ids = (20, 21, 22, 23)
    bot, guild, channel, cog, _ = build(player_ids)
    game = _make_lobby(guild, channel, player_ids)
    await cog.start_game(game["id"])
    _cleanup_timer(cog, game["id"])
    voice = guild.created_voice_channels[0]

    await cog.end_game(game["id"])

    updated = bunker_db.get_game(game["id"])
    assert updated["status"] == "finished"
    assert updated["phase"] == "ended"
    assert voice.deleted is True


@pytest.mark.asyncio
async def test_force_advance_phase_discussion_to_vote():
    player_ids = (20, 21, 22, 23)
    bot, guild, channel, cog, _ = build(player_ids)
    game = _make_lobby(guild, channel, player_ids)
    await cog.start_game(game["id"])
    _cleanup_timer(cog, game["id"])

    ok = await cog.force_advance_phase(game["id"])
    assert ok is True
    updated = bunker_db.get_game(game["id"])
    assert updated["phase"] == "vote"
    _cleanup_timer(cog, game["id"])


@pytest.mark.asyncio
async def test_force_advance_phase_returns_false_for_inactive_game():
    player_ids = (20, 21, 22, 23)
    bot, guild, channel, cog, _ = build(player_ids)
    game = _make_lobby(guild, channel, player_ids)  # status="lobby" — start_game not called

    ok = await cog.force_advance_phase(game["id"])
    assert ok is False


@pytest.mark.asyncio
async def test_force_advance_phase_returns_false_for_missing_game():
    bot, guild, channel, cog, _ = build()
    ok = await cog.force_advance_phase(999)
    assert ok is False


@pytest.mark.asyncio
async def test_concurrent_phase_advance_runs_once():
    """force_advance + _finish_discussion must not double-transition discussion→vote."""
    import asyncio

    import i18n

    player_ids = (20, 21, 22, 23)
    bot, guild, channel, cog, _ = build(player_ids)
    game = _make_lobby(guild, channel, player_ids)
    await cog.start_game(game["id"])
    _cleanup_timer(cog, game["id"])
    before = len(channel.send_calls)

    await asyncio.gather(
        cog.force_advance_phase(game["id"]),
        cog._finish_discussion(game["id"]),
    )

    updated = bunker_db.get_game(game["id"])
    assert updated["phase"] == "vote"
    lang = i18n.lang_for(guild.id)
    vote_open = i18n.t("bunker.phase.vote_open", lang)
    opens = sum(1 for c in channel.send_calls[before:] if c.get("content") == vote_open)
    assert opens == 1
    _cleanup_timer(cog, game["id"])


@pytest.mark.asyncio
async def test_force_end_game_deletes_voice_channel():
    player_ids = (20, 21, 22, 23)
    bot, guild, channel, cog, _ = build(player_ids)
    game = _make_lobby(guild, channel, player_ids)
    await cog.start_game(game["id"])
    _cleanup_timer(cog, game["id"])
    voice = guild.created_voice_channels[0]

    ok = await cog.force_end_game(game["id"])
    assert ok is True

    updated = bunker_db.get_game(game["id"])
    assert updated["status"] == "finished"
    assert voice.deleted is True


@pytest.mark.asyncio
async def test_force_end_game_returns_false_for_inactive_game():
    player_ids = (20, 21, 22, 23)
    bot, guild, channel, cog, _ = build(player_ids)
    game = _make_lobby(guild, channel, player_ids)  # status="lobby"

    ok = await cog.force_end_game(game["id"])
    assert ok is False


@pytest.mark.asyncio
async def test_full_round_vote_ends_game_at_capacity():
    """Полный цикл: старт (4 игрока, вместимость 2) -> два раунда голосований -> игра завершена,
    голосовой канал удалён."""
    player_ids = (20, 21, 22, 23)
    bot, guild, channel, cog, _ = build(player_ids)
    game = _make_lobby(guild, channel, player_ids)
    await cog.start_game(game["id"])
    _cleanup_timer(cog, game["id"])
    game_id = game["id"]

    # Раунд 1: все голосуют против 23 -> исключён, живых 3 > 2, игра продолжается.
    bunker_db.update_game(game_id, phase="vote")
    for uid in player_ids:
        bunker_db.upsert_vote(game_id, 1, uid, 23)
    await cog.maybe_finish_vote_early(game_id)
    _cleanup_timer(cog, game_id)

    updated = bunker_db.get_game(game_id)
    assert updated["phase"] == "discussion"
    assert updated["round_number"] == 2
    assert bunker_db.get_player(game_id, 23)["alive"] == 0

    # Раунд 2: оставшиеся голосуют против 22 -> живых 2 == вместимость, игра завершается.
    bunker_db.update_game(game_id, phase="vote")
    for uid in (20, 21, 22):
        bunker_db.upsert_vote(game_id, 2, uid, 22)
    await cog.maybe_finish_vote_early(game_id)

    updated = bunker_db.get_game(game_id)
    assert updated["status"] == "finished"
    assert updated["phase"] == "ended"
    assert guild.created_voice_channels[0].deleted is True
    alive = bunker_db.list_alive_players(game_id)
    assert {p["user_id"] for p in alive} == {20, 21}

