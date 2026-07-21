import discord
from discord.ext import commands
import bot_config
import feedback_categories
import json
import os
import asyncio
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

import settings_db
import settings_migration

load_dotenv()

logger = logging.getLogger("chetbot")


def get_main_guild_id() -> int:
    """Мейн-сервер (CTD/новости/супер-админ, миграция плоских конфигов).

    Фаза 2.4: GUILD_ID больше не обязателен для запуска бота. Порядок разрешения:
    GUILD_ID → MAIN_GUILD_ID → исторический дефолт мейна.
    """
    return int(os.getenv("GUILD_ID") or os.getenv("MAIN_GUILD_ID") or "1324239354154975252")


class ChetBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.invites = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)



    def utcnow(self):
        return datetime.now(timezone.utc)

    async def send_log(self, guild_id: int, embed: discord.Embed):
        raw = bot_config.get(guild_id, "LOG_CHANNEL_ID")
        if not raw:
            return
        ch = self.get_channel(int(raw))
        if ch:
            await ch.send(embed=embed)

    async def setup_hook(self):
        settings_db.init()
        # Одноразовая миграция исторических плоских конфигов/ENV привязана к мейн-серверу.
        main_guild_id = get_main_guild_id()
        migrated = settings_migration.migrate_all(main_guild_id)
        if migrated:
            logger.info(
                "Плоские конфиги перенесены в settings_db: %s", ", ".join(migrated),
            )
        bot_config.migrate_from_env_if_needed(main_guild_id)
        feedback_categories.migrate_from_env_if_needed(main_guild_id)
        await self.load_extension("feedback_menu")
        await self.load_extension("welcome")
        await self.load_extension("button")
        await self.load_extension("memobb")
        await self.load_extension("lockdown")
        await self.load_extension("tempban")
        await self.load_extension("spam")
        await self.load_extension("events")
        await self.load_extension("reaction_roles")
        await self.load_extension("news")
        await self.load_extension("voice_rooms")
        await self.load_extension("supply")
        await self.load_extension("serverlog")
        await self.load_extension("voice_tracker")
        await self.load_extension("xp")
        await self.load_extension("streams")
        await self.load_extension("family_roster")
        await self.load_extension("family_tickets")
        await self.load_extension("family_birthdays")
        await self.load_extension("mafia")
        await self.load_extension("giveaways")
        await self.load_extension("daily_topic")
        await self.load_extension("automod")
        await self.load_extension("bunker")
        await self.load_extension("fun")
        await self.load_extension("moderation_commands")
        await self.load_extension("wordle")
        await self.load_extension("economy")
        await self.load_extension("casino")
        await self.load_extension("blackjack")
        await self.load_extension("antiraid")
        await self.load_extension("verification")

        # Фаза 2.4: обычные команды регистрируются ГЛОБАЛЬНО (бот на многих серверах).
        # Фаза 2b: команды-привилегии мейна (CTD `/ctd_setup`) привязаны к мейну через
        # @app_commands.guilds — их пушим отдельным guild-sync. Этот же guild-sync
        # заменяет прежний набор guild-команд мейна (наследие copy_global_to) на
        # актуальный (только CTD), убирая старые дубли без отдельного clear_commands.
        await self.tree.sync()
        main_guild = discord.Object(id=get_main_guild_id())
        try:
            await self.tree.sync(guild=main_guild)
        except discord.HTTPException:
            logger.exception("Не удалось синхронизировать guild-команды мейн-сервера")


bot = ChetBot()

DASHBOARD_URL = os.getenv("DASHBOARD_FRONTEND_URL", "https://cheterin.online")


@bot.event
async def on_ready():
    logger.info(f"{bot.user} запущен и готов к работе! Серверов: {len(bot.guilds)}")


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Бота добавили на новый сервер: реактивируем настройки и здороваемся."""
    logger.info("Бот добавлен на сервер %s (%s)", guild.name, guild.id)
    settings_db.set_guild_active(guild.id, True)

    embed = discord.Embed(
        title="Спасибо, что добавили Cheterin!",
        description=(
            "Модули по умолчанию выключены — включите и настройте нужные в дашборде.\n\n"
            f"🔧 Панель управления: {DASHBOARD_URL}\n"
            "Для доступа нужны права **Управлять сервером** на этом сервере."
        ),
        color=discord.Color.blurple(),
    )
    channel = guild.system_channel
    if channel is None or not channel.permissions_for(guild.me).send_messages:
        channel = next(
            (c for c in guild.text_channels if c.permissions_for(guild.me).send_messages),
            None,
        )
    if channel is not None:
        try:
            await channel.send(embed=embed)
            return
        except discord.HTTPException:
            pass
    # Фолбэк — в личку владельцу.
    if guild.owner is not None:
        try:
            await guild.owner.send(embed=embed)
        except discord.HTTPException:
            pass


@bot.event
async def on_guild_remove(guild: discord.Guild):
    """Бота удалили с сервера: помечаем настройки неактивными (не удаляем)."""
    logger.info("Бот удалён с сервера %s (%s)", guild.name, guild.id)
    settings_db.set_guild_active(guild.id, False)


async def main():
    # Дашборд стартует с мейн-сервером как дефолтным (супер-админ/CTD/новости);
    # конкретный сервер выбирается пользователем в UI (Фаза 2.3).
    main_guild_id = get_main_guild_id()

    from dashboard.backend.app import start_dashboard

    dashboard_runner = await start_dashboard(bot, main_guild_id)

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Переменная окружения BOT_TOKEN не задана.")

    try:
        await bot.start(token)
    finally:
        if dashboard_runner is not None:
            await dashboard_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
