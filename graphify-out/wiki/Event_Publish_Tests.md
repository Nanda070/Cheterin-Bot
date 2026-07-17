# Event Publish Tests

> 24 nodes

## Key Concepts

- **test_events_core_publish.py** (26 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **validate_event_spec()** (16 connections) — `events_core.py`
- **_tournament_spec()** (14 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **publish_event()** (9 connections) — `events_core.py`
- **test_publish_event_tournament_creates_matching_event_obj_and_view()** (7 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_publish_event_poll_creates_matching_event_obj_and_view()** (7 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_publish_event_role_reward_none_stays_none()** (7 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **_poll_spec()** (5 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_rejects_invalid_type()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_rejects_empty_title()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_rejects_title_too_long()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_rejects_empty_description()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_rejects_description_too_long()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_rejects_invalid_ping()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_rejects_invalid_mode_for_tournament()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_rejects_negative_max_limit()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_rejects_team_size_below_2_when_not_solo()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_allows_missing_team_size_check_for_solo_mode()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_rejects_poll_with_too_few_options()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_rejects_poll_with_non_list_options()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_accepts_valid_tournament_spec()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **test_validate_event_spec_accepts_valid_poll_spec()** (3 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **isolated_events_file()** (1 connections) — `dashboard/backend/tests/test_events_core_publish.py`
- **Message** (1 connections)

## Relationships

- [Test Fake Bot](Test_Fake_Bot.md) (11 shared connections)
- [events.py](events.py.md) (8 shared connections)
- [Test Fake Channels](Test_Fake_Channels.md) (5 shared connections)
- [Automod Route Tests](Automod_Route_Tests.md) (1 shared connections)

## Source Files

- `dashboard/backend/tests/test_events_core_publish.py`
- `events_core.py`

## Audit Trail

- EXTRACTED: 135 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*