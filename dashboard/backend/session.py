import base64
import hashlib

from aiohttp import web
from aiohttp_session import setup as setup_aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage


def derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def setup_session(app: web.Application, session_secret: str) -> None:
    storage = EncryptedCookieStorage(derive_fernet_key(session_secret), cookie_name="chetbot_dashboard_session")
    setup_aiohttp_session(app, storage)
