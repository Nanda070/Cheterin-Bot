from aiohttp import web

from ..access_middleware import require_super_admin

routes = web.RouteTableDef()


@routes.get("/api/superadmin/guilds")
@require_super_admin
async def superadmin_guilds(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    return web.json_response({
        "guilds": [
            {
                "id": str(guild.id),
                "name": guild.name,
                "icon": str(guild.icon.url) if guild.icon else None,
                "member_count": guild.member_count,
                "owner_id": str(guild.owner_id) if guild.owner_id else None,
            }
            for guild in bot.guilds
        ],
    })
