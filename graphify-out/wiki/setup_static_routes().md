# setup_static_routes()

> 9 nodes

## Key Concepts

- **setup_static_routes()** (7 connections) — `dashboard/backend/static.py`
- **test_static.py** (6 connections) — `dashboard/backend/tests/test_static.py`
- **static.py** (2 connections) — `dashboard/backend/static.py`
- **test_unmatched_path_serves_index_html()** (2 connections) — `dashboard/backend/tests/test_static.py`
- **test_root_path_serves_index_html()** (2 connections) — `dashboard/backend/tests/test_static.py`
- **test_asset_path_serves_asset_file()** (2 connections) — `dashboard/backend/tests/test_static.py`
- **Application** (1 connections)
- **Path** (1 connections)
- **dist_dir()** (1 connections) — `dashboard/backend/tests/test_static.py`

## Relationships

- No strong cross-community connections detected

## Source Files

- `dashboard/backend/static.py`
- `dashboard/backend/tests/test_static.py`

## Audit Trail

- EXTRACTED: 24 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*