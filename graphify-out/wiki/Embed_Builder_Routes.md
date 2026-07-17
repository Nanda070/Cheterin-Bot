# Embed Builder Routes

> 52 nodes

## Key Concepts

- **test_embed_builder_core.py** (20 connections) — `dashboard/backend/tests/test_embed_builder_core.py`
- **embed_builder.py** (16 connections) — `embed_builder.py`
- **embed_builder.py** (15 connections) — `dashboard/backend/routes/embed_builder.py`
- **validate_embed_spec()** (15 connections) — `embed_builder.py`
- **create_embed_message()** (11 connections) — `dashboard/backend/routes/embed_builder.py`
- **update_embed_message()** (11 connections) — `dashboard/backend/routes/embed_builder.py`
- **build_embed()** (11 connections) — `embed_builder.py`
- **create_embed_template()** (7 connections) — `dashboard/backend/routes/embed_builder.py`
- **Request** (6 connections)
- **Response** (6 connections)
- **get_embed_message()** (6 connections) — `dashboard/backend/routes/embed_builder.py`
- **is_embed_spec_empty()** (6 connections) — `embed_builder.py`
- **build_role_button_view()** (6 connections) — `embed_builder.py`
- **_validate_role_ids_structure()** (5 connections) — `dashboard/backend/routes/embed_builder.py`
- **_validate_role_ids_assignable()** (5 connections) — `dashboard/backend/routes/embed_builder.py`
- **embed_to_spec()** (5 connections) — `embed_builder.py`
- **save_template()** (5 connections) — `embed_builder.py`
- **_get_guild_or_none()** (4 connections) — `dashboard/backend/routes/embed_builder.py`
- **_parse_body()** (4 connections) — `dashboard/backend/routes/embed_builder.py`
- **list_embed_templates()** (4 connections) — `dashboard/backend/routes/embed_builder.py`
- **delete_embed_template()** (4 connections) — `dashboard/backend/routes/embed_builder.py`
- **test_build_role_button_view_creates_buttons_with_role_names()** (4 connections) — `dashboard/backend/tests/test_embed_builder_buttons.py`
- **_load_templates_data()** (4 connections) — `embed_builder.py`
- **delete_template()** (4 connections) — `embed_builder.py`
- **test_build_role_button_view_falls_back_to_id_when_role_missing()** (3 connections) — `dashboard/backend/tests/test_embed_builder_buttons.py`
- *... and 27 more nodes in this community*

## Relationships

- [Test Fake Channels](Test_Fake_Channels.md) (7 shared connections)
- [access_middleware.py](access_middleware.py.md) (2 shared connections)
- [Test Fake Bot](Test_Fake_Bot.md) (2 shared connections)
- [Mass Role Assignment](Mass_Role_Assignment.md) (1 shared connections)
- [Supply Module](Supply_Module.md) (1 shared connections)

## Source Files

- `dashboard/backend/routes/embed_builder.py`
- `dashboard/backend/tests/test_embed_builder_buttons.py`
- `dashboard/backend/tests/test_embed_builder_core.py`
- `embed_builder.py`

## Audit Trail

- EXTRACTED: 241 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*