import pytest
import os
import bot.core.settings_db as settings_db
from contextlib import closing

os.environ["SETTINGS_DB_PATH"] = "test_settings.db"
settings_db.init()

@pytest.fixture(autouse=True)
def reset_settings_db():
    settings_db._cache.clear()
    with closing(settings_db.connect()) as conn, conn:
        conn.execute("DELETE FROM module_settings")
