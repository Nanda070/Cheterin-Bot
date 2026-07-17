# resolve_guild_member()

> 21 nodes

## Key Concepts

- **resolve_guild_member()** (14 connections) — `dashboard/backend/member_lookup.py`
- **test_member_lookup.py** (11 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **FakeGuild** (8 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **FakeBot** (8 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **member_lookup.py** (5 connections) — `dashboard/backend/member_lookup.py`
- **test_not_found_when_fetch_raises_notfound()** (5 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **test_service_error_when_fetch_raises_http_exception()** (5 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **test_returns_cached_member_without_fetching()** (4 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **test_falls_back_to_fetch_when_not_cached()** (4 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **MemberLookupResult** (3 connections) — `dashboard/backend/member_lookup.py`
- **_StubNotFound** (3 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **_StubHTTPException** (3 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **test_service_error_when_guild_missing()** (3 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **.__init__()** (1 connections) — `dashboard/backend/member_lookup.py`
- **.__init__()** (1 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **.__init__()** (1 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **.__init__()** (1 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **.get_member()** (1 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **.fetch_member()** (1 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **.__init__()** (1 connections) — `dashboard/backend/tests/test_member_lookup.py`
- **.get_guild()** (1 connections) — `dashboard/backend/tests/test_member_lookup.py`

## Relationships

- [access_middleware.py](access_middleware.py.md) (4 shared connections)
- [auth.py](auth.py.md) (4 shared connections)

## Source Files

- `dashboard/backend/member_lookup.py`
- `dashboard/backend/tests/test_member_lookup.py`

## Audit Trail

- EXTRACTED: 84 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*