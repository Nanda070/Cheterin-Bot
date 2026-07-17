# XP Core Tests

> 25 nodes

## Key Concepts

- **xp_core.py** (22 connections) — `xp_core.py`
- **test_xp_core.py** (11 connections) — `dashboard/backend/tests/test_xp_core.py`
- **level_progress()** (8 connections) — `xp_core.py`
- **xp_for_level_step()** (6 connections) — `xp_core.py`
- **total_xp_for_level()** (6 connections) — `xp_core.py`
- **level_from_xp()** (5 connections) — `xp_core.py`
- **test_deserved_roles()** (4 connections) — `dashboard/backend/tests/test_xp_core.py`
- **test_level_from_xp_roundtrip()** (3 connections) — `dashboard/backend/tests/test_xp_core.py`
- **test_level_progress()** (3 connections) — `dashboard/backend/tests/test_xp_core.py`
- **voice_xp_per_minute()** (3 connections) — `xp_core.py`
- **test_level_formula_monotonic()** (2 connections) — `dashboard/backend/tests/test_xp_core.py`
- **test_roll_text_xp_respects_multiplier()** (2 connections) — `dashboard/backend/tests/test_xp_core.py`
- **test_voice_xp_requires_two_active()** (2 connections) — `dashboard/backend/tests/test_xp_core.py`
- **test_render_announce()** (2 connections) — `dashboard/backend/tests/test_xp_core.py`
- **roll_text_xp()** (2 connections) — `xp_core.py`
- **deserved_level_roles()** (2 connections) — `xp_core.py`
- **deserved_voice_roles()** (2 connections) — `xp_core.py`
- **all_reward_role_ids()** (2 connections) — `xp_core.py`
- **render_announce()** (2 connections) — `xp_core.py`
- **isolated_config()** (1 connections) — `dashboard/backend/tests/test_xp_core.py`
- **Ядро системы уровней: конфигурация, формула уровней, награды, шаблоны.  Механи** (1 connections) — `xp_core.py`
- **Сколько XP нужно, чтобы перейти с уровня `level` на `level + 1`.** (1 connections) — `xp_core.py`
- **Суммарный XP, необходимый для достижения уровня `level`.** (1 connections) — `xp_core.py`
- **(уровень, XP внутри уровня, XP до следующего уровня).** (1 connections) — `xp_core.py`
- **XP за минуту голосовой активности при active_count активных участниках.** (1 connections) — `xp_core.py`

## Relationships

- [xp.py](xp.py.md) (8 shared connections)
- [format_voice_time()](format_voice_time%28%29.md) (2 shared connections)
- [access_middleware.py](access_middleware.py.md) (1 shared connections)
- [test_xp_routes.py](test_xp_routes.py.md) (1 shared connections)
- [VoiceTracker](VoiceTracker.md) (1 shared connections)
- [XPCog](XPCog.md) (1 shared connections)
- [xp_card.py](xp_card.py.md) (1 shared connections)

## Source Files

- `dashboard/backend/tests/test_xp_core.py`
- `xp_core.py`

## Audit Trail

- EXTRACTED: 95 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*