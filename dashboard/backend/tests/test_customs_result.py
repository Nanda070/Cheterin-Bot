"""Customs match-result embed and winner GIF."""

import bot.modules.valorant.customs as customs
import bot.modules.valorant.customs_core as customs_core
import bot.cards.customs_winner_card as winner_card
import bot.core.embed_style as embed_style
import bot.core.i18n as i18n


def _finished_lobby(**overrides) -> dict:
    lobby = {
        "id": "28",
        "name": "Кастомка",
        "map_id": "breeze",
        "map_name": "Breeze",
        "score": {"a": 13, "b": 3},
        "status": customs_core.STATUS_FINISHED,
    }
    lobby.update(overrides)
    return lobby


def test_result_embed_matches_mock_layout():
    embed = customs.build_result_embed(_finished_lobby(), "ru")
    assert embed.title == i18n.t("customs.embed.result_title", "ru")
    assert embed.title == "Кастомка · результат"
    assert embed.description == "Победа команды A"
    assert embed.color == embed_style.SUCCESS
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Карта"] == "Breeze"
    assert fields["Счёт"] == "13 : 3"
    assert embed.footer.text == "Кастомки · #28"
    assert embed.image.url


def test_result_embed_team_b_and_english():
    embed = customs.build_result_embed(_finished_lobby(score={"a": 8, "b": 13}), "en")
    assert embed.title == "Custom · result"
    assert embed.description == "Team B wins"
    fields = {f.name: f.value for f in embed.fields}
    assert fields["Map"] == "Breeze"
    assert fields["Score"] == "8 : 13"


def test_winner_gif_is_animated_gif():
    buf = winner_card.build_winner_gif("Кастомка · результат", "Победа команды A", 13, 3)
    data = buf.getvalue()
    assert data[:6] in (b"GIF87a", b"GIF89a")
    assert buf.name == "customs-winner.gif"
    assert winner_card.BRAND == "VALORANTCUSTOMS"
    assert len(data) > 800
