"""CTD create-ticket callback must accept only interaction (discord.py Button API)."""

from __future__ import annotations

import inspect

from memobb import CTDView


def test_create_ticket_callback_signature_matches_discord_button():
    params = [
        name
        for name, p in inspect.signature(CTDView.create_ticket).parameters.items()
        if name != "self" and p.kind in (p.POSITIONAL_OR_KEYWORD, p.POSITIONAL_ONLY)
    ]
    assert params == ["interaction"], params
