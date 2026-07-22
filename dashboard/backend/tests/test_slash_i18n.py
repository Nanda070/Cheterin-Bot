from discord import Locale
from discord import app_commands
from discord.app_commands import TranslationContext, TranslationContextLocation

import i18n
import slash_i18n
import slash_registry


def test_localize_command_sets_english_base_and_locale_str():
    @app_commands.command(name="ping", description="Пинг")
    async def ping(interaction):
        pass

    slash_i18n.localize_command(ping, desc_key="slash.leaders.desc", name_key="slash.leaders")
    assert ping.name == "leaders"
    assert ping.description == i18n.t("slash.leaders.desc", "en")
    assert ping._locale_name is not None
    assert ping._locale_name.extras.get("i18n_key") == "slash.leaders"
    assert ping._locale_description is not None
    assert ping._locale_description.extras.get("i18n_key") == "slash.leaders.desc"


async def test_translator_returns_russian_command_name():
    @app_commands.command(name="ранг", description="Показать ранг")
    async def rank(interaction):
        pass

    slash_i18n.localize_command(rank, desc_key="slash.rank.desc", name_key="slash.rank")
    translator = slash_i18n.SlashI18nTranslator()
    ctx = TranslationContext(location=TranslationContextLocation.command_name, data=rank)
    ru = await translator.translate(rank._locale_name, Locale.russian, ctx)
    assert ru == "ранг"
    en = await translator.translate(rank._locale_name, Locale.american_english, ctx)
    assert en is None  # same as base "rank"


async def test_translator_returns_russian_description():
    @app_commands.command(name="rank", description="x")
    async def rank(interaction):
        pass

    slash_i18n.localize_command(rank, desc_key="slash.rank.desc", name_key="slash.rank")
    translator = slash_i18n.SlashI18nTranslator()
    ctx = TranslationContext(location=TranslationContextLocation.command_description, data=rank)
    ru = await translator.translate(rank._locale_description, Locale.russian, ctx)
    assert ru == i18n.t("slash.rank.desc", "ru")
    assert ru.startswith("Показать")


def test_slash_locale_keys_exist_in_both_languages():
    for key in slash_registry.SLASH_KEYS:
        base = f"slash.{key}"
        for lang in ("ru", "en"):
            assert i18n.t(f"{base}.en", lang), f"missing {base}.en for {lang}"
            assert i18n.t(f"{base}.ru", lang), f"missing {base}.ru for {lang}"
            assert i18n.t(f"{base}.desc", lang), f"missing {base}.desc for {lang}"
            assert not i18n.t(f"{base}.desc", lang).endswith(".desc")
