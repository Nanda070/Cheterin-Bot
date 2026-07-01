import aiohttp

DISCORD_API_BASE = "https://discord.com/api/v10"


class DiscordOAuthError(Exception):
    pass


async def exchange_code_for_token(
    session: aiohttp.ClientSession,
    code: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    api_base: str = DISCORD_API_BASE,
) -> dict:
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    async with session.post(f"{api_base}/oauth2/token", data=data) as resp:
        if resp.status != 200:
            raise DiscordOAuthError(f"Token exchange failed with status {resp.status}")
        return await resp.json()


async def fetch_discord_identity(
    session: aiohttp.ClientSession,
    access_token: str,
    api_base: str = DISCORD_API_BASE,
) -> dict:
    headers = {"Authorization": f"Bearer {access_token}"}
    async with session.get(f"{api_base}/users/@me", headers=headers) as resp:
        if resp.status != 200:
            raise DiscordOAuthError(f"Fetching identity failed with status {resp.status}")
        return await resp.json()
