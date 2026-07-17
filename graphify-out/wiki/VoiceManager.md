# VoiceManager

> 16 nodes

## Key Concepts

- **VoiceManager** (9 connections) — `voice_rooms.py`
- **VoiceChannel** (7 connections)
- **Member** (6 connections)
- **apply_owner_permissions()** (5 connections) — `voice_rooms.py`
- **set_member_allow()** (5 connections) — `voice_rooms.py`
- **set_member_deny()** (5 connections) — `voice_rooms.py`
- **.on_voice_state_update()** (5 connections) — `voice_rooms.py`
- **.recover_private_rooms()** (5 connections) — `voice_rooms.py`
- **remove_owner_permissions()** (4 connections) — `voice_rooms.py`
- **set_open_state()** (3 connections) — `voice_rooms.py`
- **set_closed_state()** (3 connections) — `voice_rooms.py`
- **.get_channel_owner_id()** (3 connections) — `voice_rooms.py`
- **.on_guild_channel_update()** (3 connections) — `voice_rooms.py`
- **.on_ready()** (2 connections) — `voice_rooms.py`
- **GuildChannel** (1 connections)
- **VoiceState** (1 connections)

## Relationships

- [voice_rooms.py](voice_rooms.py.md) (11 shared connections)
- [ensure_owner()](ensure_owner%28%29.md) (8 shared connections)

## Source Files

- `voice_rooms.py`

## Audit Trail

- EXTRACTED: 66 (99%)
- INFERRED: 1 (1%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*