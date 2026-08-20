from pathlib import Path

from aiohttp import web


def setup_static_routes(app: web.Application, dist_dir: Path) -> None:
    assets_dir = dist_dir / "assets"
    if assets_dir.is_dir():
        app.router.add_static("/assets", assets_dir)

    # Domain verification (Discord etc.) must not fall through to SPA index.html.
    well_known_dir = dist_dir / ".well-known"
    if well_known_dir.is_dir():
        app.router.add_static("/.well-known", well_known_dir, show_index=False)

    riot_path = dist_dir / "riot.txt"
    if riot_path.is_file():

        async def serve_riot(_request: web.Request) -> web.Response:
            return web.FileResponse(riot_path)

        app.router.add_get("/riot.txt", serve_riot)

    index_path = dist_dir / "index.html"

    async def spa_fallback(request: web.Request) -> web.Response:
        return web.FileResponse(index_path)

    app.router.add_get("/{tail:.*}", spa_fallback)
