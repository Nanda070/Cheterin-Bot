"""EU DSA Transparency Database client for Discord Netherlands B.V.

Official public source (no Research API token required):
  GET https://transparency.dsa.ec.europa.eu/statement/csv?platform_id[]=59&s=<id>

Discord embeds entity snowflakes in the exported ``platform_uid`` field (PUID).
We only return rows whose platform_uid exactly matches the queried id, or where
the id appears as a hyphen/underscore-delimited token inside platform_uid.

Honesty constraints:
- Empty result ≠ clean account; only means no matching public SoR in the
  searchable export for Discord Netherlands B.V.
- Web HTML detail pages omit PUID; CSV export is the public machine-readable path.
- Research API requires EU Login auth — optional LOOKUP_DSA_RESEARCH_TOKEN later.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
from typing import Any
from urllib.parse import urlencode

from aiohttp import ClientSession, ClientTimeout

DSA_CSV_BASE = "https://transparency.dsa.ec.europa.eu/statement/csv"
DSA_STATEMENT_BASE = "https://transparency.dsa.ec.europa.eu/statement"
# Stable platform id from the official statement-search form (Discord Netherlands B.V.)
DEFAULT_DISCORD_PLATFORM_ID = "59"
DISCORD_PLATFORM_NAME = "Discord Netherlands B.V."
DISCORD_PLATFORM_UUID = "caca0689-3c4f-4a72-8a10-ddc719d22256"

SNOWFLAKE_RE = re.compile(r"^\d{17,20}$")
DSA_CACHE_TTL = 15 * 60


def discord_platform_id() -> str:
    return os.getenv("LOOKUP_DSA_PLATFORM_ID", DEFAULT_DISCORD_PLATFORM_ID).strip() or DEFAULT_DISCORD_PLATFORM_ID


def puid_matches(platform_uid: str, queried_id: str) -> bool:
    uid = (platform_uid or "").strip()
    if not uid:
        return False
    if uid == queried_id:
        return True
    # Compound PUIDs used by some Discord tooling: split tokens
    for part in re.split(r"[-_]", uid):
        if part == queried_id:
            return True
    return False


def _parse_jsonish(value: str) -> Any:
    raw = (value or "").strip()
    if not raw:
        return None
    if raw.startswith("[") or raw.startswith("{"):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def _as_list(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v is not None and str(v) != ""]
    if isinstance(value, str):
        parsed = _parse_jsonish(value)
        if isinstance(parsed, list):
            return [str(v) for v in parsed if v is not None and str(v) != ""]
        return [value] if value else []
    return [str(value)]


def humanize_code(code: str | None) -> str | None:
    if not code:
        return None
    text = code.strip()
    if not text:
        return None
    if text.startswith("STATEMENT_CATEGORY_"):
        text = text[len("STATEMENT_CATEGORY_") :]
    elif text.startswith("DECISION_"):
        text = text[len("DECISION_") :]
    elif text.startswith("SOURCE_"):
        text = text[len("SOURCE_") :]
    elif text.startswith("AUTOMATED_DECISION_"):
        text = text[len("AUTOMATED_DECISION_") :]
    elif text.startswith("CONTENT_TYPE_"):
        text = text[len("CONTENT_TYPE_") :]
    return text.replace("_", " ").strip().title()


def normalize_row(row: dict[str, str], queried_id: str) -> dict[str, Any]:
    uuid = (row.get("uuid") or "").strip()
    platform_uid = (row.get("platform_uid") or "").strip()
    decision_account = (row.get("decision_account") or "").strip() or None
    decision_visibility = _as_list(row.get("decision_visibility"))
    decision_provision = (row.get("decision_provision") or "").strip() or None
    category = (row.get("category") or "").strip() or None
    content_type_other = (row.get("content_type_other") or "").strip() or None
    entity_kind = "account" if (content_type_other or "").lower() == "user account" else "content"

    return {
        "uuid": uuid,
        "permalink": f"{DSA_STATEMENT_BASE}/{uuid}" if uuid else None,
        "platform_uid": platform_uid,
        "queried_id": queried_id,
        "entity_kind": entity_kind,
        "platform_name": (row.get("platform_name") or DISCORD_PLATFORM_NAME).strip(),
        "decision_account": decision_account,
        "decision_account_label": humanize_code(decision_account),
        "decision_visibility": decision_visibility,
        "decision_visibility_labels": [humanize_code(v) or v for v in decision_visibility],
        "decision_provision": decision_provision,
        "decision_provision_label": humanize_code(decision_provision),
        "decision_ground": (row.get("decision_ground") or "").strip() or None,
        "decision_ground_label": humanize_code((row.get("decision_ground") or "").strip() or None),
        "category": category,
        "category_label": humanize_code(category),
        "category_specification": _as_list(row.get("category_specification")),
        "incompatible_content_ground": (row.get("incompatible_content_ground") or "").strip() or None,
        "incompatible_content_explanation": (row.get("incompatible_content_explanation") or "").strip() or None,
        "illegal_content_explanation": (row.get("illegal_content_explanation") or "").strip() or None,
        "decision_facts": (row.get("decision_facts") or "").strip() or None,
        "content_type": _as_list(row.get("content_type")),
        "content_type_other": content_type_other,
        "application_date": (row.get("application_date") or "").strip() or None,
        "content_date": (row.get("content_date") or "").strip() or None,
        "created_at": (row.get("created_at") or "").strip() or None,
        "source_type": (row.get("source_type") or "").strip() or None,
        "source_type_label": humanize_code((row.get("source_type") or "").strip() or None),
        "automated_detection": (row.get("automated_detection") or "").strip() or None,
        "automated_decision": (row.get("automated_decision") or "").strip() or None,
        "automated_decision_label": humanize_code((row.get("automated_decision") or "").strip() or None),
        "territorial_scope": _as_list(row.get("territorial_scope")),
    }


def parse_csv(text: str, queried_id: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(text))
    out: list[dict[str, Any]] = []
    for row in reader:
        if not puid_matches(row.get("platform_uid") or "", queried_id):
            continue
        out.append(normalize_row(row, queried_id))
    # Newest first when dates exist
    out.sort(key=lambda r: r.get("created_at") or r.get("application_date") or "", reverse=True)
    return out


def build_csv_url(queried_id: str) -> str:
    qs = urlencode({"platform_id[]": discord_platform_id(), "s": queried_id})
    return f"{DSA_CSV_BASE}?{qs}"


async def fetch_discord_statements(session: ClientSession, queried_id: str) -> list[dict[str, Any]]:
    url = build_csv_url(queried_id)
    timeout = ClientTimeout(total=25)
    headers = {
        "Accept": "text/csv,text/plain,*/*",
        "User-Agent": "CheterinLookup/1.0 (+https://cheterin.online/lookup; DSA public CSV client)",
    }
    async with session.get(url, headers=headers, timeout=timeout) as resp:
        if resp.status >= 400:
            raise RuntimeError(f"dsa_upstream_{resp.status}")
        text = await resp.text()
    return parse_csv(text, queried_id)


def source_meta() -> dict[str, Any]:
    return {
        "name": "EU DSA Transparency Database",
        "platform": DISCORD_PLATFORM_NAME,
        "platform_uuid": DISCORD_PLATFORM_UUID,
        "platform_id": discord_platform_id(),
        "search_url": "https://transparency.dsa.ec.europa.eu/statement-search",
        "csv_pattern": f"{DSA_CSV_BASE}?platform_id[]={{platform_id}}&s={{id}}",
        "retention_note": "Official searchable export covers recent statements under the database retention policy (commonly ~6 months in the live index).",
        "honesty": [
            "No matching SoR does not mean the account is clean or flagged.",
            "Only Discord Netherlands B.V. statements are queried.",
            "We never invent violations; rows come from the official public CSV export.",
        ],
    }
