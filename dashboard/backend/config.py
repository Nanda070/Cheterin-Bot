from dataclasses import dataclass


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class DashboardConfig:
    port: int
    client_id: str
    client_secret: str
    redirect_uri: str
    session_secret: str
    access_role_ids: frozenset
    frontend_url: str
    frontend_dist: str = ""


REQUIRED_KEYS = (
    "DASHBOARD_PORT",
    "DISCORD_CLIENT_ID",
    "DISCORD_CLIENT_SECRET",
    "DISCORD_OAUTH_REDIRECT_URI",
    "SESSION_SECRET",
)


def load_dashboard_config(env: dict) -> DashboardConfig:
    missing = [key for key in REQUIRED_KEYS if not env.get(key)]
    if missing:
        raise ConfigError(f"Missing required env vars: {', '.join(missing)}")

    try:
        port = int(env["DASHBOARD_PORT"])
    except ValueError as exc:
        raise ConfigError(
            f"DASHBOARD_PORT must be an integer, got {env['DASHBOARD_PORT']!r}"
        ) from exc

    # Фаза 2.3: доступ = Manage Server на выбранном сервере. DASHBOARD_ACCESS_ROLE_IDS
    # больше не обязателен; если задан — работает как дополнительный (переходный)
    # грант по роли на активном сервере.
    role_ids = frozenset(
        role_id.strip()
        for role_id in env.get("DASHBOARD_ACCESS_ROLE_IDS", "").split(",")
        if role_id.strip()
    )

    session_secret = env["SESSION_SECRET"]
    if len(session_secret) < 32:
        raise ConfigError("SESSION_SECRET must be at least 32 characters long")

    return DashboardConfig(
        port=port,
        client_id=env["DISCORD_CLIENT_ID"],
        client_secret=env["DISCORD_CLIENT_SECRET"],
        redirect_uri=env["DISCORD_OAUTH_REDIRECT_URI"],
        session_secret=session_secret,
        access_role_ids=role_ids,
        frontend_url=env.get("DASHBOARD_FRONTEND_URL", ""),
        frontend_dist=env.get("DASHBOARD_FRONTEND_DIST", ""),
    )
