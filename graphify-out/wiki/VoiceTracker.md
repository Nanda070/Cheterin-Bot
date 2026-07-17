# VoiceTracker

> 20 nodes

## Key Concepts

- **VoiceTracker** (13 connections) — `voice_tracker.py`
- **voice_tracker.py** (7 connections) — `voice_tracker.py`
- **.on_voice_state_update()** (5 connections) — `voice_tracker.py`
- **._tick()** (5 connections) — `voice_tracker.py`
- **VoiceSession** (4 connections) — `voice_tracker.py`
- **setup()** (4 connections) — `voice_tracker.py`
- **is_active()** (3 connections) — `voice_tracker.py`
- **Member** (3 connections)
- **._close_session()** (3 connections) — `voice_tracker.py`
- **._xp_member_ignored()** (3 connections) — `voice_tracker.py`
- **VoiceState** (2 connections)
- **.__init__()** (2 connections) — `voice_tracker.py`
- **Bot** (2 connections)
- **.on_ready()** (2 connections) — `voice_tracker.py`
- **._xp_channel_allowed()** (2 connections) — `voice_tracker.py`
- **.cog_unload()** (1 connections) — `voice_tracker.py`
- **._before_tick()** (1 connections) — `voice_tracker.py`
- **._prune()** (1 connections) — `voice_tracker.py`
- **._before_prune()** (1 connections) — `voice_tracker.py`
- **Войс-трекер: единый учёт голосовых сессий.  Кормит сразу два модуля: - статис** (1 connections) — `voice_tracker.py`

## Relationships

- [Audit Log & Stats DB](Audit_Log_%26_Stats_DB.md) (2 shared connections)
- [XP Core Tests](XP_Core_Tests.md) (1 shared connections)

## Source Files

- `voice_tracker.py`

## Audit Trail

- EXTRACTED: 65 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*