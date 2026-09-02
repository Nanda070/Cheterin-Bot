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


@pytest.mark.asyncio
async def test_well_known_discord_not_spa_fallback(aiohttp_client, dist_dir):
    well_known = dist_dir / ".well-known"
    well_known.mkdir()
    (well_known / "discord").write_text(
        "dh=cf90ba633c23069048cee5676d56aa69e395e188\n"
        "dh=608fcfb7697fc80b4a151675c6342afdd40a1e5a\n",
        encoding="utf-8",
    )

    app = web.Application()
    setup_static_routes(app, dist_dir)
    client = await aiohttp_client(app)

    resp = await client.get("/.well-known/discord")

    assert resp.status == 200
    text = await resp.text()
    assert text == (
        "dh=cf90ba633c23069048cee5676d56aa69e395e188\n"
        "dh=608fcfb7697fc80b4a151675c6342afdd40a1e5a\n"
    )
    assert "SPA" not in text


@pytest.mark.asyncio
async def test_riot_txt_not_spa_fallback(aiohttp_client, dist_dir):
    (dist_dir / "riot.txt").write_bytes(
        b"aed65606-0fad-4950-af04-1695d5cc8421\n"
    )

    app = web.Application()
    setup_static_routes(app, dist_dir)
    client = await aiohttp_client(app)

    resp = await client.get("/riot.txt")

    assert resp.status == 200
    text = await resp.text()
    assert text == "aed65606-0fad-4950-af04-1695d5cc8421\n"
    assert "SPA" not in text
