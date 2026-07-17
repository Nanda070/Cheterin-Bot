# Test Fake Bot

> 77 nodes

## Key Concepts

- **FakeGuild** (154 connections) — `dashboard/backend/tests/fakes.py`
- **FakeBot** (140 connections) — `dashboard/backend/tests/fakes.py`
- **test_events_core.py** (21 connections) — `dashboard/backend/tests/test_events_core.py`
- **FakeThread** (20 connections) — `dashboard/backend/tests/fakes.py`
- **test_feedback_core.py** (19 connections) — `dashboard/backend/tests/test_feedback_core.py`
- **test_fakes_feedback_extensions.py** (16 connections) — `dashboard/backend/tests/test_fakes_feedback_extensions.py`
- **test_access_middleware.py** (15 connections) — `dashboard/backend/tests/test_access_middleware.py`
- **decide_case()** (14 connections) — `feedback_core.py`
- **test_decide_case_approve_updates_status_persists_and_notifies()** (10 connections) — `dashboard/backend/tests/test_feedback_core.py`
- **test_decide_case_reject_sets_denied_status_and_red_color()** (10 connections) — `dashboard/backend/tests/test_feedback_core.py`
- **feedback_core.py** (10 connections) — `feedback_core.py`
- **_tournament_event()** (9 connections) — `dashboard/backend/tests/test_events_core.py`
- **test_decide_case_dm_falls_back_to_fetch_user_when_submitter_left_guild()** (9 connections) — `dashboard/backend/tests/test_feedback_core.py`
- **test_decide_case_survives_missing_public_channel()** (9 connections) — `dashboard/backend/tests/test_feedback_core.py`
- **events_core.py** (9 connections) — `events_core.py`
- **close_event()** (9 connections) — `events_core.py`
- **delete_event()** (8 connections) — `events_core.py`
- **make_client_app()** (7 connections) — `dashboard/backend/tests/test_access_middleware.py`
- **test_close_event_disables_participation_buttons_on_live_message()** (7 connections) — `dashboard/backend/tests/test_events_core.py`
- **test_delete_event_removes_role_from_all_participants()** (7 connections) — `dashboard/backend/tests/test_events_core.py`
- **test_delete_event_deletes_live_message()** (7 connections) — `dashboard/backend/tests/test_events_core.py`
- **_build_case()** (7 connections) — `dashboard/backend/tests/test_feedback_core.py`
- **test_activate_guild_unavailable_503()** (7 connections) — `dashboard/backend/tests/test_lockdown_routes.py`
- **test_member_with_access_reaches_handler()** (6 connections) — `dashboard/backend/tests/test_access_middleware.py`
- **test_member_without_access_role_gets_403()** (6 connections) — `dashboard/backend/tests/test_access_middleware.py`
- *... and 52 more nodes in this community*

## Relationships

- [Test Fake Channels](Test_Fake_Channels.md) (41 shared connections)
- [Test Fake Members](Test_Fake_Members.md) (30 shared connections)
- [Feedback Panel Tests](Feedback_Panel_Tests.md) (29 shared connections)
- [Automod Route Tests](Automod_Route_Tests.md) (26 shared connections)
- [Mass Role Assignment](Mass_Role_Assignment.md) (26 shared connections)
- [Reaction Roles Tests](Reaction_Roles_Tests.md) (20 shared connections)
- [Event Publish Tests](Event_Publish_Tests.md) (11 shared connections)
- [Feedback Cases](Feedback_Cases.md) (11 shared connections)
- [events.py](events.py.md) (9 shared connections)
- [test_feedback_routes.py](test_feedback_routes.py.md) (9 shared connections)
- [Game Settings & Bunker DB](Game_Settings_%26_Bunker_DB.md) (8 shared connections)
- [test_family_routes.py](test_family_routes.py.md) (6 shared connections)

## Source Files

- `dashboard/backend/tests/fakes.py`
- `dashboard/backend/tests/test_access_middleware.py`
- `dashboard/backend/tests/test_events_core.py`
- `dashboard/backend/tests/test_fakes_feedback_extensions.py`
- `dashboard/backend/tests/test_feedback_core.py`
- `dashboard/backend/tests/test_lockdown_routes.py`
- `events_core.py`
- `feedback_core.py`

## Audit Trail

- EXTRACTED: 664 (97%)
- INFERRED: 21 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*