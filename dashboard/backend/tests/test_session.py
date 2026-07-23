from cryptography.fernet import Fernet

from dashboard.backend.session import cookie_secure_flag, derive_fernet_key


def test_derive_fernet_key_is_valid_fernet_key():
    key = derive_fernet_key("any-length-secret-works-fine")
    Fernet(key)  # raises ValueError if not a valid 32-byte urlsafe-base64 key


def test_derive_fernet_key_is_deterministic():
    assert derive_fernet_key("same-secret") == derive_fernet_key("same-secret")


def test_derive_fernet_key_differs_per_secret():
    assert derive_fernet_key("secret-one") != derive_fernet_key("secret-two")


def test_cookie_secure_flag_from_env(monkeypatch):
    monkeypatch.delenv("DASHBOARD_FRONTEND_URL", raising=False)
    monkeypatch.delenv("FRONTEND_URL", raising=False)
    monkeypatch.setenv("DASHBOARD_COOKIE_SECURE", "true")
    assert cookie_secure_flag() is True
    monkeypatch.setenv("DASHBOARD_COOKIE_SECURE", "0")
    assert cookie_secure_flag() is False


def test_cookie_secure_flag_detects_https_frontend(monkeypatch):
    monkeypatch.delenv("DASHBOARD_COOKIE_SECURE", raising=False)
    monkeypatch.setenv("DASHBOARD_FRONTEND_URL", "https://dash.example.com")
    assert cookie_secure_flag() is True
    monkeypatch.setenv("DASHBOARD_FRONTEND_URL", "http://localhost:5173")
    assert cookie_secure_flag() is False
