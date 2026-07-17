# Reaction Roles Tests

> 41 nodes

## Key Concepts

- **test_reaction_roles_cog.py** (19 connections) — `dashboard/backend/tests/test_reaction_roles_cog.py`
- **reaction_roles.py** (15 connections) — `reaction_roles.py`
- **FakePayload** (14 connections) — `dashboard/backend/tests/test_reaction_roles_cog.py`
- **handle_reaction_change()** (13 connections) — `reaction_roles.py`
- **load_config()** (12 connections) — `reaction_roles.py`
- **test_reaction_roles_core.py** (11 connections) — `dashboard/backend/tests/test_reaction_roles_core.py`
- **_setup_config()** (9 connections) — `dashboard/backend/tests/test_reaction_roles_cog.py`
- **save_config()** (9 connections) — `reaction_roles.py`
- **test_handle_reaction_change_add_grants_role_using_payload_member()** (8 connections) — `dashboard/backend/tests/test_reaction_roles_cog.py`
- **test_handle_reaction_change_remove_revokes_role_by_resolving_member()** (8 connections) — `dashboard/backend/tests/test_reaction_roles_cog.py`
- **test_handle_reaction_change_remove_falls_back_to_fetch_member_when_not_cached()** (8 connections) — `dashboard/backend/tests/test_reaction_roles_cog.py`
- **test_handle_reaction_change_ignores_unmatched_emoji()** (8 connections) — `dashboard/backend/tests/test_reaction_roles_cog.py`
- **test_cleanup_missing_messages_keeps_entries_for_existing_messages()** (8 connections) — `dashboard/backend/tests/test_reaction_roles_cog.py`
- **test_handle_reaction_change_ignores_bots_own_reaction()** (7 connections) — `dashboard/backend/tests/test_reaction_roles_cog.py`
- **test_cleanup_missing_messages_removes_entries_for_deleted_messages()** (7 connections) — `dashboard/backend/tests/test_reaction_roles_cog.py`
- **cleanup_missing_messages()** (7 connections) — `reaction_roles.py`
- **test_handle_reaction_change_ignores_unconfigured_message()** (5 connections) — `dashboard/backend/tests/test_reaction_roles_cog.py`
- **get_pairs_for_message()** (5 connections) — `reaction_roles.py`
- **ReactionRoles** (5 connections) — `reaction_roles.py`
- **find_pair_by_emoji()** (4 connections) — `reaction_roles.py`
- **has_duplicate_emoji()** (4 connections) — `reaction_roles.py`
- **test_save_then_load_round_trip()** (3 connections) — `dashboard/backend/tests/test_reaction_roles_core.py`
- **test_get_pairs_for_message_returns_pairs_when_present()** (3 connections) — `dashboard/backend/tests/test_reaction_roles_core.py`
- **test_get_pairs_for_message_returns_none_when_absent()** (3 connections) — `dashboard/backend/tests/test_reaction_roles_core.py`
- **.on_raw_reaction_add()** (3 connections) — `reaction_roles.py`
- *... and 16 more nodes in this community*

## Relationships

- [Test Fake Bot](Test_Fake_Bot.md) (20 shared connections)
- [Test Fake Channels](Test_Fake_Channels.md) (9 shared connections)
- [reaction_roles.py](reaction_roles.py.md) (9 shared connections)
- [Mass Role Assignment](Mass_Role_Assignment.md) (7 shared connections)
- [Test Fake Members](Test_Fake_Members.md) (6 shared connections)

## Source Files

- `dashboard/backend/tests/test_reaction_roles_cog.py`
- `dashboard/backend/tests/test_reaction_roles_core.py`
- `reaction_roles.py`

## Audit Trail

- EXTRACTED: 221 (97%)
- INFERRED: 6 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*