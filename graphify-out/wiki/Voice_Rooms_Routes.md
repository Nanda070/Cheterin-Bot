# Voice Rooms Routes

> 37 nodes

## Key Concepts

- **test_voice_routes.py** (18 connections) — `dashboard/backend/tests/test_voice_routes.py`
- **voice_db.py** (18 connections) — `voice_db.py`
- **db_connect()** (16 connections) — `voice_db.py`
- **build()** (11 connections) — `dashboard/backend/tests/test_voice_routes.py`
- **FakeVoiceChannel** (9 connections) — `dashboard/backend/tests/test_voice_routes.py`
- **test_delete_room()** (8 connections) — `dashboard/backend/tests/test_voice_routes.py`
- **voice.py** (7 connections) — `dashboard/backend/routes/voice.py`
- **test_rooms_list()** (6 connections) — `dashboard/backend/tests/test_voice_routes.py`
- **voice_room_delete()** (5 connections) — `dashboard/backend/routes/voice.py`
- **voice_rooms_list()** (4 connections) — `dashboard/backend/routes/voice.py`
- **test_delete_room_not_found()** (4 connections) — `dashboard/backend/tests/test_voice_routes.py`
- **db_upsert_room()** (4 connections) — `voice_db.py`
- **db_get_room()** (4 connections) — `voice_db.py`
- **Request** (3 connections)
- **Response** (3 connections)
- **voice_panel_publish()** (3 connections) — `dashboard/backend/routes/voice.py`
- **.delete()** (3 connections) — `dashboard/backend/tests/test_voice_routes.py`
- **voice_channel_isinstance()** (3 connections) — `dashboard/backend/tests/test_voice_routes.py`
- **test_rooms_empty()** (3 connections) — `dashboard/backend/tests/test_voice_routes.py`
- **test_panel_publish()** (3 connections) — `dashboard/backend/tests/test_voice_routes.py`
- **db_init()** (3 connections) — `voice_db.py`
- **db_delete_room()** (3 connections) — `voice_db.py`
- **db_get_all_rooms()** (3 connections) — `voice_db.py`
- **isolated_db()** (2 connections) — `dashboard/backend/tests/test_voice_routes.py`
- **test_requires_auth()** (2 connections) — `dashboard/backend/tests/test_voice_routes.py`
- *... and 12 more nodes in this community*

## Relationships

- [Test Fake Bot](Test_Fake_Bot.md) (6 shared connections)
- [Automod Route Tests](Automod_Route_Tests.md) (6 shared connections)
- [Test Fake Members](Test_Fake_Members.md) (5 shared connections)
- [access_middleware.py](access_middleware.py.md) (2 shared connections)
- [Feedback Panel Tests](Feedback_Panel_Tests.md) (2 shared connections)
- [Test Fake Channels](Test_Fake_Channels.md) (1 shared connections)
- [voice_rooms.py](voice_rooms.py.md) (1 shared connections)

## Source Files

- `dashboard/backend/routes/voice.py`
- `dashboard/backend/tests/test_voice_routes.py`
- `voice_db.py`

## Audit Trail

- EXTRACTED: 164 (97%)
- INFERRED: 5 (3%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*