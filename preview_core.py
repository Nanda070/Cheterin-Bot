"""Dry-run preview for slash help text and embed/message templates."""

from __future__ import annotations

from message_template_core import normalize_embed_spec, substitute, substitute_embed_spec

SAMPLE_VARS = {
    "mention": "@User",
    "name": "User",
    "guild": "Example Server",
    "guild_name": "Example Server",
    "user_id": "123456789012345678",
    "invite": "https://discord.gg/example",
    "channel": "StreamerName",
    "stream": "Playing something cool",
    "game": "Just Chatting",
    "channel.url": "https://twitch.tv/example",
}


def preview_text(template: str, variables: dict | None = None) -> dict:
    vars_ = {**SAMPLE_VARS, **(variables or {})}
    # Support both {var} and {{var}} styles
    text = substitute(template or "", {k: str(v) for k, v in vars_.items()})
    for key, value in vars_.items():
        text = text.replace("{{" + key + "}}", str(value))
    return {"content": text, "variables": vars_}


def preview_embed(spec: dict, variables: dict | None = None) -> dict:
    vars_ = {**SAMPLE_VARS, **(variables or {})}
    normalized = normalize_embed_spec(spec or {})
    rendered = substitute_embed_spec(normalized, {k: str(v) for k, v in vars_.items()})
    # Also replace {{var}} in string fields
    for key in ("title", "description", "url", "color"):
        if isinstance(rendered.get(key), str):
            for vk, vv in vars_.items():
                rendered[key] = rendered[key].replace("{{" + vk + "}}", str(vv))
    return {"embed": rendered, "variables": vars_}


def preview_slash_help(name: str, description: str, options: list | None = None) -> dict:
    opts = []
    for opt in options or []:
        if not isinstance(opt, dict):
            continue
        opts.append(
            {
                "name": str(opt.get("name") or ""),
                "description": str(opt.get("description") or ""),
                "required": bool(opt.get("required", False)),
                "type": str(opt.get("type") or "string"),
            }
        )
    usage_parts = [f"/{name}"]
    for opt in opts:
        token = f"<{opt['name']}>" if opt["required"] else f"[{opt['name']}]"
        usage_parts.append(token)
    return {
        "name": name,
        "description": description,
        "options": opts,
        "usage": " ".join(usage_parts),
    }
