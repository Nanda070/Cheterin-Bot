import discord
from discord.ext import commands
import feedback_categories
import json
import os
import asyncio
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

DATA_FILE = "invites_stats.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

data = load_data()

class ChetBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.invites = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

        self.stats = data.setdefault("stats", {})
        self.invite_history = data.setdefault("invite_history", {})
        self.feedback_counters = data.setdefault("feedback_counters", {})
        self.feedback_cases = data.setdefault("feedback_cases", {})
        self._file_lock = asyncio.Lock()

    async def update_file(self):
        async with self._file_lock:
            data["stats"] = self.stats
            data["invite_history"] = self.invite_history
            data["feedback_counters"] = self.feedback_counters
            data["feedback_cases"] = self.feedback_cases
            await asyncio.to_thread(self._write_data_sync)

    @staticmethod
    def _write_data_sync():
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def utcnow(self):
        return datetime.now(timezone.utc)

    async def send_log(self, embed: discord.Embed):
        raw = os.getenv("LOG_CHANNEL_ID")
        if not raw:
            return
        ch = self.get_channel(int(raw))
        if ch:
            await ch.send(embed=embed)

    async def setup_hook(self):
        feedback_categories.migrate_from_env_if_needed()
        await self.load_extension("feedback_menu")
        await self.load_extension("welcome")
        await self.load_extension("button")
        await self.load_extension("memobb")
        await self.load_extension("lockdown")
        await self.load_extension("tempban")
        await self.load_extension("spam")
        await self.load_extension("events")
        await self.load_extension("reaction_roles")
        guild_id = os.getenv("GUILD_ID")
        if not guild_id:
            raise RuntimeError("Переменная окружения GUILD_ID не задана.")
        guild = discord.Object(id=int(guild_id))
        self.tree.copy_global_to(guild=guild)
        self.tree.clear_commands(guild=None)
        await self.tree.sync(guild=guild)

bot = ChetBot()

@bot.event
async def on_ready():
    logging.getLogger("chetbot").info(f"{bot.user} запущен и готов к работе!")


async def main():
    guild_id_raw = os.getenv("GUILD_ID")
    if not guild_id_raw:
        raise RuntimeError("Переменная окружения GUILD_ID не задана.")
    guild_id = int(guild_id_raw)

    from dashboard.backend.app import start_dashboard

    dashboard_runner = await start_dashboard(bot, guild_id)

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
