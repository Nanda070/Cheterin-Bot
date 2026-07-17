# Mafia Public Route Tests

> 32 nodes

## Key Concepts

- **test_mafia_public_routes.py** (41 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **build()** (32 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **_setup_game()** (30 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **update_game()** (14 connections) — `mafia_db.py`
- **test_action_triggers_early_night_resolution()** (7 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_vote_triggers_early_day_vote_resolution()** (7 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **eliminate_player()** (7 connections) — `mafia_db.py`
- **test_public_state_mafia_sees_teammates_and_votes()** (5 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_public_state_citizen_no_night_action_but_day_vote_required()** (5 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_public_state_includes_roster_with_hidden_alive_roles()** (5 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_public_state_vote_tally_during_day_vote()** (5 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_public_state_dead_player_no_action()** (5 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_action_dead_player()** (5 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_action_game_not_active()** (5 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_action_deadline_passed()** (5 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_vote_dead_player()** (5 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_vote_game_not_active()** (5 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_vote_deadline_passed()** (5 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_public_state_no_action_during_discussion()** (4 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_public_state_hides_other_alive_player_roles()** (4 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_action_happy_path_and_resubmit()** (4 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_action_wrong_phase()** (4 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_action_invalid_target_not_alive()** (4 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_action_self_target_forbidden_for_mafia_and_sheriff()** (4 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- **test_action_self_target_allowed_for_doctor()** (4 connections) — `dashboard/backend/tests/test_mafia_public_routes.py`
- *... and 7 more nodes in this community*

## Relationships

- [Test Fake Members](Test_Fake_Members.md) (25 shared connections)
- [Mafia DB Tests](Mafia_DB_Tests.md) (17 shared connections)
- [mafia.py](mafia.py.md) (5 shared connections)
- [Test Fake Bot](Test_Fake_Bot.md) (4 shared connections)
- [Mafia Discord Cog](Mafia_Discord_Cog.md) (4 shared connections)
- [Test Fake Channels](Test_Fake_Channels.md) (3 shared connections)
- [Feedback Panel Tests](Feedback_Panel_Tests.md) (2 shared connections)
- [test_mafia_routes.py](test_mafia_routes.py.md) (2 shared connections)
- [Mafia Core Tests](Mafia_Core_Tests.md) (1 shared connections)

## Source Files

- `dashboard/backend/tests/test_mafia_public_routes.py`
- `mafia_db.py`

## Audit Trail

- EXTRACTED: 243 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*