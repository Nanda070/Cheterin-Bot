from discord import Locale

import i18n
import slash_i18n
import slash_registry
from discord import app_commands


def test_localize_command_sets_description_localizations():
    @app_commands.command(name="ping", description="Пинг")
    async def ping(interaction):
        pass

    slash_i18n.localize_command(ping, desc_key="slash.leaders.desc", name_key="slash.leaders")
    assert ping.name == "leaders"
    assert Locale.american_english in ping.description_localizations
    assert Locale.russian in ping.description_localizations
    assert ping.description == i18n.t("slash.leaders.desc", "en")


def test_localize_command_sets_russian_name_localization():
    @app_commands.command(name="ранг", description="Показать ранг")
    async def rank(interaction):
        pass

    slash_i18n.localize_command(rank, desc_key="slash.rank.desc", name_key="slash.rank")
    assert rank.name == "rank"
    assert rank.name_localizations[Locale.russian] == "ранг"


def test_slash_locale_keys_exist_in_both_languages():
    for key in slash_registry.SLASH_KEYS:
        base = f"slash.{key}"
        for lang in ("ru", "en"):
            assert i18n.t(f"{base}.en", lang), f"missing {base}.en for {lang}"
            assert i18n.t(f"{base}.ru", lang), f"missing {base}.ru for {lang}"
            assert i18n.t(f"{base}.desc", lang), f"missing {base}.desc for {lang}"
            assert not i18n.t(f"{base}.desc", lang).endswith(".desc")
