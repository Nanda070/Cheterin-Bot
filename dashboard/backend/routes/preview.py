from aiohttp import web

import bot.core.preview_core as preview_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.post("/api/preview/template")
@require_dashboard_access
async def preview_template(request: web.Request) -> web.Response:
    """Dry-run placeholder substitution for text/embed templates. Does not send to Discord."""
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    variables = body.get("variables")
    if variables is not None and not isinstance(variables, dict):
        return web.json_response({"error": "invalid_variables"}, status=400)
    if isinstance(variables, dict):
        variables = {str(k): str(v) for k, v in variables.items()}

    result: dict = {}
    content = body.get("content")
    if content is not None:
        if not isinstance(content, str):
            return web.json_response({"error": "invalid_content"}, status=400)
        result.update(preview_core.preview_text(content, variables))

    embed = body.get("embed")
    if embed is not None:
        if not isinstance(embed, dict):
            return web.json_response({"error": "invalid_embed"}, status=400)
        previewed = preview_core.preview_embed(embed, variables)
        result["embed"] = previewed["embed"]
        result.setdefault("variables", previewed["variables"])

    if "content" not in result and "embed" not in result:
        return web.json_response({"error": "content_or_embed_required"}, status=400)

    return web.json_response(result)
