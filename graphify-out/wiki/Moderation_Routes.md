# Moderation Routes

> 54 nodes

## Key Concepts

- **moderation.py** (32 connections) — `dashboard/backend/routes/moderation.py`
- **test_moderation_log_routes.py** (13 connections) — `dashboard/backend/tests/test_moderation_log_routes.py`
- **load_events()** (11 connections) — `moderation_log.py`
- **Request** (10 connections)
- **Response** (10 connections)
- **moderation_log.py** (10 connections) — `moderation_log.py`
- **_get_target_or_response()** (8 connections) — `dashboard/backend/routes/moderation.py`
- **grant_role()** (8 connections) — `dashboard/backend/routes/moderation.py`
- **revoke_role()** (8 connections) — `dashboard/backend/routes/moderation.py`
- **test_moderation_log.py** (8 connections) — `dashboard/backend/tests/test_moderation_log.py`
- **build()** (8 connections) — `dashboard/backend/tests/test_moderation_log_routes.py`
- **append_event()** (8 connections) — `moderation_log.py`
- **_get_guild_or_none()** (7 connections) — `dashboard/backend/routes/moderation.py`
- **ban_member()** (7 connections) — `dashboard/backend/routes/moderation.py`
- **kick_member()** (7 connections) — `dashboard/backend/routes/moderation.py`
- **mass_assign_role()** (7 connections) — `dashboard/backend/routes/moderation.py`
- **member_detail()** (6 connections) — `dashboard/backend/routes/moderation.py`
- **dashboard_reason()** (6 connections) — `dashboard/backend/routes/moderation.py`
- **_send_action_log()** (6 connections) — `dashboard/backend/routes/moderation.py`
- **_resolve_assignable_role()** (6 connections) — `dashboard/backend/routes/moderation.py`
- **TempBan** (6 connections) — `tempban.py`
- **list_members()** (5 connections) — `dashboard/backend/routes/moderation.py`
- **_map_discord_error()** (5 connections) — `dashboard/backend/routes/moderation.py`
- **list_roles()** (5 connections) — `dashboard/backend/routes/moderation.py`
- **get_moderation_log()** (4 connections) — `dashboard/backend/routes/moderation.py`
- *... and 29 more nodes in this community*

## Relationships

- [Test Fake Members](Test_Fake_Members.md) (6 shared connections)
- [Mass Role Assignment](Mass_Role_Assignment.md) (5 shared connections)
- [Feedback Panel Tests](Feedback_Panel_Tests.md) (4 shared connections)
- [Test Fake Bot](Test_Fake_Bot.md) (4 shared connections)
- [Automod Route Tests](Automod_Route_Tests.md) (3 shared connections)
- [access_middleware.py](access_middleware.py.md) (2 shared connections)
- [Test Fake Channels](Test_Fake_Channels.md) (1 shared connections)
- [Automod Cog](Automod_Cog.md) (1 shared connections)
- [Supply Module](Supply_Module.md) (1 shared connections)
- [Anti-Spam Cog](Anti-Spam_Cog.md) (1 shared connections)
- [Bot Config Store](Bot_Config_Store.md) (1 shared connections)

## Source Files

- `dashboard/backend/__init__.py`
- `dashboard/backend/routes/moderation.py`
- `dashboard/backend/tests/test_moderation_log.py`
- `dashboard/backend/tests/test_moderation_log_routes.py`
- `moderation_log.py`
- `tempban.py`

## Audit Trail

- EXTRACTED: 275 (99%)
- INFERRED: 2 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*