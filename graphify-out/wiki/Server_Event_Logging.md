# Server Event Logging

> 60 nodes

## Key Concepts

- **ServerLog** (27 connections) — `serverlog.py`
- **._embed()** (26 connections) — `serverlog.py`
- **.emit()** (25 connections) — `serverlog.py`
- **serverlog.py** (12 connections) — `serverlog.py`
- **_clip()** (10 connections) — `serverlog.py`
- **_recent_audit_actor()** (7 connections) — `serverlog.py`
- **.on_voice_state_update()** (7 connections) — `serverlog.py`
- **serverlog.py** (6 connections) — `dashboard/backend/routes/serverlog.py`
- **get_settings()** (6 connections) — `serverlog.py`
- **.on_app_command_completion()** (6 connections) — `serverlog.py`
- **serverlog_put()** (5 connections) — `dashboard/backend/routes/serverlog.py`
- **Guild** (5 connections)
- **event_channel_id()** (5 connections) — `serverlog.py`
- **.on_message_edit()** (5 connections) — `serverlog.py`
- **.on_message_delete()** (5 connections) — `serverlog.py`
- **.on_member_remove()** (5 connections) — `serverlog.py`
- **.on_member_ban()** (5 connections) — `serverlog.py`
- **.on_member_unban()** (5 connections) — `serverlog.py`
- **.on_member_update()** (5 connections) — `serverlog.py`
- **.on_guild_role_update()** (5 connections) — `serverlog.py`
- **.on_guild_channel_update()** (5 connections) — `serverlog.py`
- **.on_thread_update()** (5 connections) — `serverlog.py`
- **.on_guild_update()** (5 connections) — `serverlog.py`
- **.on_guild_emojis_update()** (5 connections) — `serverlog.py`
- **.on_invite_create()** (5 connections) — `serverlog.py`
- *... and 35 more nodes in this community*

## Relationships

- [access_middleware.py](access_middleware.py.md) (2 shared connections)
- [Feedback Panel Tests](Feedback_Panel_Tests.md) (2 shared connections)
- [Test Fake Channels](Test_Fake_Channels.md) (1 shared connections)

## Source Files

- `dashboard/backend/routes/serverlog.py`
- `dashboard/backend/tests/fakes.py`
- `serverlog.py`

## Audit Trail

- EXTRACTED: 293 (99%)
- INFERRED: 4 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*