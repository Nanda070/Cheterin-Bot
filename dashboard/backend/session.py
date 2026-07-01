import base64
import hashlib

from aiohttp import web
from aiohttp_session import setup as setup_aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage


def derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def setup_session(app: web.Application, session_secret: str) -> None:
    # EncryptedCookieStorage re-encodes bytes/bytearray keys with an extra
    # base64 pass (see aiohttp_session.cookie_storage.EncryptedCookieStorage.__init__),
    # which would double-encode our already-base64 Fernet key. Passing it as
    # str routes straight to fernet.Fernet(secret_key) and avoids that.
    fernet_key = derive_fernet_key(session_secret).decode("ascii")
    storage = EncryptedCookieStorage(fernet_key, cookie_name="chetbot_dashboard_session")
    setup_aiohttp_session(app, storage)
