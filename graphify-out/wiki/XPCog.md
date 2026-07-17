# XPCog

> 22 nodes

## Key Concepts

- **XPCog** (12 connections) — `xp.py`
- **Member** (9 connections)
- **xp.py** (8 connections) — `xp.py`
- **.process_member()** (7 connections) — `xp.py`
- **.sync_reward_roles()** (6 connections) — `xp.py`
- **.on_message()** (5 connections) — `xp.py`
- **setup()** (4 connections) — `xp.py`
- **member_has_ignored_role()** (3 connections) — `xp.py`
- **.apply_voice_session()** (3 connections) — `xp.py`
- **.announce_level_up()** (3 connections) — `xp.py`
- **.reset_member()** (3 connections) — `xp.py`
- **.set_member_xp()** (3 connections) — `xp.py`
- **.rank_command()** (3 connections) — `xp.py`
- **channel_allowed()** (2 connections) — `xp.py`
- **.__init__()** (2 connections) — `xp.py`
- **Bot** (2 connections)
- **.on_member_remove()** (2 connections) — `xp.py`
- **Message** (1 connections)
- **Interaction** (1 connections)
- **Ког системы уровней: XP за текст, обработка уровней и наград, /ранг.  XP за во** (1 connections) — `xp.py`
- **Пересчитывает уровень, синхронизирует роли-награды, шлёт уведомление.** (1 connections) — `xp.py`
- **Приводит роли-награды участника в соответствие с его прогрессом.** (1 connections) — `xp.py`

## Relationships

- [Audit Log & Stats DB](Audit_Log_%26_Stats_DB.md) (2 shared connections)
- [xp_card.py](xp_card.py.md) (1 shared connections)
- [XP Core Tests](XP_Core_Tests.md) (1 shared connections)

## Source Files

- `xp.py`

## Audit Trail

- EXTRACTED: 82 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*