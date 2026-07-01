from cryptography.fernet import Fernet

from dashboard.backend.session import derive_fernet_key


def test_derive_fernet_key_is_valid_fernet_key():
    key = derive_fernet_key("any-length-secret-works-fine")
    Fernet(key)  # raises ValueError if not a valid 32-byte urlsafe-base64 key


def test_derive_fernet_key_is_deterministic():
    assert derive_fernet_key("same-secret") == derive_fernet_key("same-secret")


def test_derive_fernet_key_differs_per_secret():
    assert derive_fernet_key("secret-one") != derive_fernet_key("secret-two")
