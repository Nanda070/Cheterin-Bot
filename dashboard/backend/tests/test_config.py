import pytest

from dashboard.backend.config import ConfigError, load_dashboard_config

VALID_ENV = {
    "DASHBOARD_PORT": "8080",
    "DISCORD_CLIENT_ID": "123",
    "DISCORD_CLIENT_SECRET": "secret",
    "DISCORD_OAUTH_REDIRECT_URI": "http://localhost:8080/api/auth/discord/callback",
    "SESSION_SECRET": "x" * 32,
    "DASHBOARD_ACCESS_ROLE_IDS": "1324239354209632357,1324239354209632358",
}


def test_loads_valid_config():
    config = load_dashboard_config(VALID_ENV)
    assert config.port == 8080
    assert config.client_id == "123"
    assert config.access_role_ids == frozenset({"1324239354209632357", "1324239354209632358"})


def test_missing_required_var_raises():
    env = dict(VALID_ENV)
    del env["DISCORD_CLIENT_ID"]
    with pytest.raises(ConfigError, match="DISCORD_CLIENT_ID"):
        load_dashboard_config(env)


def test_invalid_port_raises():
    env = dict(VALID_ENV, DASHBOARD_PORT="not-a-number")
    with pytest.raises(ConfigError, match="DASHBOARD_PORT"):
        load_dashboard_config(env)


def test_short_session_secret_raises():
    env = dict(VALID_ENV, SESSION_SECRET="short")
    with pytest.raises(ConfigError, match="SESSION_SECRET"):
        load_dashboard_config(env)


def test_access_role_ids_optional_empty_when_absent():
    # Фаза 2.3: доступ по Manage Server, роль-список больше не обязателен.
    env = dict(VALID_ENV)
    del env["DASHBOARD_ACCESS_ROLE_IDS"]
    config = load_dashboard_config(env)
    assert config.access_role_ids == frozenset()


def test_access_role_ids_empty_string_ok():
    env = dict(VALID_ENV, DASHBOARD_ACCESS_ROLE_IDS="")
    config = load_dashboard_config(env)
    assert config.access_role_ids == frozenset()


def test_frontend_url_defaults_to_empty_string():
    config = load_dashboard_config(VALID_ENV)
    assert config.frontend_url == ""


def test_frontend_url_picked_up_when_present():
    env = dict(VALID_ENV, DASHBOARD_FRONTEND_URL="http://localhost:5173")
    config = load_dashboard_config(env)
    assert config.frontend_url == "http://localhost:5173"


def test_frontend_dist_defaults_to_empty_string():
    config = load_dashboard_config(VALID_ENV)
    assert config.frontend_dist == ""


def test_frontend_dist_picked_up_when_present():
    env = dict(VALID_ENV, DASHBOARD_FRONTEND_DIST="/srv/chetmain/dashboard/frontend/dist")
    config = load_dashboard_config(env)
    assert config.frontend_dist == "/srv/chetmain/dashboard/frontend/dist"
