import discord
import pytest

import feedback_core
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild, FakeMember, FakeMessage, FakeThread


@pytest.fixture(autouse=True)
def isolated_feedback_categories(tmp_path, monkeypatch):
    import feedback_categories

    monkeypatch.setattr(feedback_categories, "CONFIG_FILE", str(tmp_path / "feedback_categories.json"))
    feedback_categories.save_categories(
        {
            "players": {
                "title": "Жалоба на участника",
                "button_label": "Жалоба на участника",
                "channel_id": "500",
                "case_prefix": "PR",
                "case_title": "Жалоба на участника",
                "thread_name": "player-report",
                "review_role_ids": ["111"],
                "review_user_ids": [],
                "approved_text": "Участник наказан.",
                "denied_text": "Жалоба отклонена.",
                "modal_title": "Жалоба на участника",
                "fields": [
                    {
                        "key": "offender",
                        "label": "Ник / ID участника",
                        "style": "short",
                        "required": True,
                        "max_length": 120,
                    },
                    {
                        "key": "complaint",
                        "label": "Суть жалобы",
                        "style": "paragraph",
                        "required": True,
                        "max_length": 1000,
                    },
                    {
                        "key": "datetime",
                        "label": "Дата и время ситуации",
                        "style": "short",
                        "required": False,
                        "max_length": 120,
                    },
                    {
                        "key": "proof",
                        "label": "Доказательства",
                        "style": "paragraph",
                        "required": False,
                        "max_length": 1000,
                    },
                ],
                "mini_summary_key": "offender",
            },
        }
    )
    yield


def _base_embed(title="Case"):
    return discord.Embed(title=title, color=discord.Color.orange())


def _build_case(public_message_id, decision_message_id, status="pending"):
    return {
        "case_id": "PR-0001",
        "category_key": "players",
        "submitter_id": 50,
        "public_channel_id": 500,
        "public_message_id": public_message_id,
        "thread_id": 700,
        "decision_message_id": decision_message_id,
        "status": status,
        "created_at": "2026-07-03T00:00:00+00:00",
    }


@pytest.mark.asyncio
async def test_decide_case_not_found_returns_error():
    guild = FakeGuild()
    bot = FakeBot(guild)
    result = await feedback_core.decide_case(bot, guild, "MISSING", True, decided_by_id=10, decided_by_mention="<@10>")
    assert result == {"ok": False, "error": "not_found"}


@pytest.mark.asyncio
async def test_decide_case_already_decided_returns_error():
    guild = FakeGuild()
    bot = FakeBot(guild)
    bot.feedback_cases["PR-0001"] = _build_case(900, 901, status="approved")
    result = await feedback_core.decide_case(
        bot, guild, "PR-0001", True, decided_by_id=10, decided_by_mention="<@10>"
    )
    assert result == {"ok": False, "error": "already_decided"}


@pytest.mark.asyncio
async def test_decide_case_category_deleted_returns_error_without_mutating_status():
    import feedback_categories

    guild = FakeGuild()
    bot = FakeBot(guild)
    bot.feedback_cases["PR-0001"] = _build_case(900, 901, status="pending")

    # Category "players" is deleted from the categories config after the case was created.
    feedback_categories.save_categories({})

    result = await feedback_core.decide_case(
        bot, guild, "PR-0001", True, decided_by_id=10, decided_by_mention="<@10>"
    )

    assert result == {"ok": False, "error": "category_deleted"}
    assert bot.feedback_cases["PR-0001"]["status"] == "pending"


@pytest.mark.asyncio
async def test_decide_case_approve_updates_status_persists_and_notifies():
    submitter = FakeMember(50, name="submitter")
    public_message = FakeMessage(900, embeds=[_base_embed()])
    channel = FakeChannel(500, messages={900: public_message})
    decision_message = FakeMessage(901, embeds=[_base_embed()])
    thread = FakeThread(700, messages={901: decision_message})
    guild = FakeGuild(members=[submitter], channels=[channel], threads=[thread])
    bot = FakeBot(guild)
    bot.feedback_cases["PR-0001"] = _build_case(900, 901)

    result = await feedback_core.decide_case(
        bot, guild, "PR-0001", True, decided_by_id=10, decided_by_mention="<@10>"
    )

    assert result == {"ok": True, "error": None}
    assert bot.feedback_cases["PR-0001"]["status"] == "approved"
    assert bot.feedback_cases["PR-0001"]["reviewed_by"] == 10
    assert bot.update_file_calls == 1
    assert public_message.edit_calls[0]["embed"].color.value == discord.Color.green().value
    assert decision_message.edit_calls[0]["embed"].color.value == discord.Color.green().value
    assert len(submitter.send_calls) == 1
    assert thread.archived is True
    assert thread.locked is True
    assert len(thread.send_calls) == 1


@pytest.mark.asyncio
async def test_decide_case_reject_sets_denied_status_and_red_color():
    submitter = FakeMember(50, name="submitter")
    public_message = FakeMessage(900, embeds=[_base_embed()])
    channel = FakeChannel(500, messages={900: public_message})
    decision_message = FakeMessage(901, embeds=[_base_embed()])
    thread = FakeThread(700, messages={901: decision_message})
    guild = FakeGuild(members=[submitter], channels=[channel], threads=[thread])
    bot = FakeBot(guild)
    bot.feedback_cases["PR-0001"] = _build_case(900, 901)

    result = await feedback_core.decide_case(
        bot, guild, "PR-0001", False, decided_by_id=10, decided_by_mention="<@10>"
    )

    assert result == {"ok": True, "error": None}
    assert bot.feedback_cases["PR-0001"]["status"] == "denied"
    assert public_message.edit_calls[0]["embed"].color.value == discord.Color.red().value


@pytest.mark.asyncio
async def test_decide_case_dm_falls_back_to_fetch_user_when_submitter_left_guild():
    gone_submitter = FakeMember(50, name="gone")
    decision_message = FakeMessage(901, embeds=[_base_embed()])
    thread = FakeThread(700, messages={901: decision_message})
    guild = FakeGuild(members=[], threads=[thread])  # submitter NOT in guild.members
    bot = FakeBot(guild, fetchable_users=[gone_submitter])
    bot.feedback_cases["PR-0001"] = _build_case(900, 901)

    result = await feedback_core.decide_case(
        bot, guild, "PR-0001", True, decided_by_id=10, decided_by_mention="<@10>"
    )

    assert result == {"ok": True, "error": None}
    assert len(gone_submitter.send_calls) == 1


@pytest.mark.asyncio
async def test_decide_case_survives_missing_public_channel():
    submitter = FakeMember(50, name="submitter")
    decision_message = FakeMessage(901, embeds=[_base_embed()])
    thread = FakeThread(700, messages={901: decision_message})
    # No channels configured -- public_channel_id 500 won't resolve.
    guild = FakeGuild(members=[submitter], channels=[], threads=[thread])
    bot = FakeBot(guild)
    bot.feedback_cases["PR-0001"] = _build_case(900, 901)

    result = await feedback_core.decide_case(
        bot, guild, "PR-0001", True, decided_by_id=10, decided_by_mention="<@10>"
    )

    assert result == {"ok": True, "error": None}
    assert bot.feedback_cases["PR-0001"]["status"] == "approved"
    assert len(submitter.send_calls) == 1
