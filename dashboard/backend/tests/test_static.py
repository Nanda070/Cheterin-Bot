import pytest
from aiohttp import web

from dashboard.backend.static import setup_static_routes


@pytest.fixture
def dist_dir(tmp_path):
    d = tmp_path / "dist"
    d.mkdir()
    (d / "index.html").write_text("<html>SPA</html>", encoding="utf-8")
    assets = d / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("console.log('hi')", encoding="utf-8")
    return d


@pytest.mark.asyncio
async def test_unmatched_path_serves_index_html(aiohttp_client, dist_dir):
    app = web.Application()
    setup_static_routes(app, dist_dir)
    client = await aiohttp_client(app)

    resp = await client.get("/brackets/abc123")

    assert resp.status == 200
    text = await resp.text()
    assert text == "<html>SPA</html>"


@pytest.mark.asyncio
async def test_root_path_serves_index_html(aiohttp_client, dist_dir):
    app = web.Application()
    setup_static_routes(app, dist_dir)
    client = await aiohttp_client(app)

    resp = await client.get("/")

    assert resp.status == 200
    text = await resp.text()
    assert text == "<html>SPA</html>"


@pytest.mark.asyncio
async def test_asset_path_serves_asset_file(aiohttp_client, dist_dir):
    app = web.Application()
    setup_static_routes(app, dist_dir)
    client = await aiohttp_client(app)

    resp = await client.get("/assets/app.js")

    assert resp.status == 200
    text = await resp.text()
    assert text == "console.log('hi')"
