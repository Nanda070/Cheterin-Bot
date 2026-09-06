"""Unit tests for DSA CSV parsing (no network)."""
from __future__ import annotations

from dsa import parse_csv, source_meta


SAMPLE_CSV = """\
uuid,platform_uid,decision_account,decision_visibility,category,incompatible_content_ground,decision_facts,application_date,created_at,automated_decision,content_type,content_type_other
abc-1,123456789012345678,ACCOUNT_DISABLED,,ILLEGAL_OR_HARMFUL_SPEECH,hate speech,facts here,2024-01-02,2024-01-01,AUTOMATED_DECISION_PARTIALLY,VIDEO,user account
"""


def test_source_meta_points_at_eu_portal():
    meta = source_meta()
    assert "transparency.dsa.ec.europa.eu" in meta["search_url"]
    assert str(meta["platform_id"]) == "59"
    assert meta["honesty"]


def test_parse_csv_maps_platform_uid():
    statements = parse_csv(SAMPLE_CSV, "123456789012345678")
    assert len(statements) == 1
    assert statements[0]["platform_uid"] == "123456789012345678"
    assert statements[0]["entity_kind"] == "account"
    assert statements[0]["uuid"] == "abc-1"


def test_parse_csv_ignores_non_matching():
    assert parse_csv(SAMPLE_CSV, "999999999999999999") == []
