# Family DB Tests

> 35 nodes

## Key Concepts

- **family_db.py** (32 connections) — `family_db.py`
- **connect()** (24 connections) — `family_db.py`
- **test_family_db.py** (9 connections) — `dashboard/backend/tests/test_family_db.py`
- **init()** (7 connections) — `family_db.py`
- **create_ticket_record()** (7 connections) — `family_db.py`
- **update_ticket_status()** (7 connections) — `family_db.py`
- **test_ticket_lifecycle()** (6 connections) — `dashboard/backend/tests/test_family_db.py`
- **get_ticket_by_user()** (6 connections) — `family_db.py`
- **test_list_and_count_tickets_filters_by_status()** (5 connections) — `dashboard/backend/tests/test_family_db.py`
- **test_birthday_roundtrip_and_queries()** (5 connections) — `dashboard/backend/tests/test_family_db.py`
- **test_roster_message_roundtrip()** (4 connections) — `dashboard/backend/tests/test_family_db.py`
- **test_pending_form_roundtrip()** (4 connections) — `dashboard/backend/tests/test_family_db.py`
- **test_ticket_recreate_replaces_previous_open_ticket()** (4 connections) — `dashboard/backend/tests/test_family_db.py`
- **test_birthday_message_roundtrip()** (4 connections) — `dashboard/backend/tests/test_family_db.py`
- **get_ticket_by_thread()** (4 connections) — `family_db.py`
- **list_tickets()** (4 connections) — `family_db.py`
- **count_tickets()** (4 connections) — `family_db.py`
- **update_ticket_indexes()** (4 connections) — `family_db.py`
- **save_birthday()** (4 connections) — `family_db.py`
- **delete_birthday()** (4 connections) — `family_db.py`
- **get_all_birthdays()** (4 connections) — `family_db.py`
- **get_roster_data()** (3 connections) — `family_db.py`
- **save_roster_data()** (3 connections) — `family_db.py`
- **clear_roster_data()** (3 connections) — `family_db.py`
- **save_pending_form()** (3 connections) — `family_db.py`
- *... and 10 more nodes in this community*

## Relationships

- [test_family_routes.py](test_family_routes.py.md) (7 shared connections)
- [family.py](family.py.md) (6 shared connections)
- [Family Tickets](Family_Tickets.md) (4 shared connections)
- [Family Birthdays](Family_Birthdays.md) (2 shared connections)
- [RosterCog](RosterCog.md) (2 shared connections)
- [Dashboard App Bootstrap](Dashboard_App_Bootstrap.md) (1 shared connections)
- [Supply Module](Supply_Module.md) (1 shared connections)
- [Interaction](Interaction.md) (1 shared connections)

## Source Files

- `dashboard/backend/tests/test_family_db.py`
- `family_db.py`

## Audit Trail

- EXTRACTED: 188 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*