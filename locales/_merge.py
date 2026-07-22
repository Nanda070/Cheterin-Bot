"""Merge locale module dicts into one MESSAGES map."""


def merge_messages(*parts: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in parts:
        out.update(part)
    return out
