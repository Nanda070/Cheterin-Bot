from pathlib import Path

from aiohttp import web


def setup_static_routes(app: web.Application, dist_dir: Path) -> None:
    assets_dir = dist_dir / "assets"
    if assets_dir.is_dir():
        app.router.add_static("/assets", assets_dir)

    index_path = dist_dir / "index.html"

    async def spa_fallback(request: web.Request) -> web.Response:
        return web.FileResponse(index_path)

    app.router.add_get("/{tail:.*}", spa_fallback)
