"""Ког «Экономика»: баланс, переводы, топ и магазин ролей.

Монеты начисляются автоматически как процент от заработанного XP — хук
economy_core.award_for_xp() вызывается из xp.py (текст и войс). Тратятся
в магазине ролей (/магазин) и на ставках в русской рулетке (fun.py).
Модуль выключен по умолчанию, настраивается в дашборде (раздел «Экономика»).
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

import economy_core
import economy_db

logger = logging.getLogger("economy")

DISABLED_TEXT = "Модуль «Экономика» отключён."


DEFAULT_ITEM_LABEL = {"role": "Роль", "frame_color": "Рамка", "title": "Титул"}


class ShopView(discord.ui.View):
    """Кнопки покупки по товарам магазина (эфемерное сообщение)."""

    def __init__(self, cog: "EconomyCog", items: list[dict]):
        super().__init__(timeout=600)
        self.cog = cog
        for item in items[:economy_core.SHOP_ITEMS_MAX]:
            label = item["name"] or DEFAULT_ITEM_LABEL.get(item["type"], "Товар")
            button = discord.ui.Button(
                label=f"{label} — {item['price']}",
                style=discord.ButtonStyle.primary,
                custom_id=f"economy:buy:{item['id']}",
            )
            button.callback = self._make_callback(item["id"])
            self.add_item(button)

    def _make_callback(self, item_id: str):
        async def callback(interaction: discord.Interaction):
            await self.cog.handle_purchase(interaction, item_id)
        return callback


class CosmeticsView(discord.ui.View):
    """Селекторы «Рамка» / «Титул» из уже купленных предметов (эфемерное сообщение)."""

    def __init__(self, cog: "EconomyCog", frames: list[dict], titles: list[dict]):
        super().__init__(timeout=180)
        self.cog = cog
        if frames:
            self.add_item(self._build_select("frame_color", "Рамка карточки", "Без рамки", frames))
        if titles:
            self.add_item(self._build_select("title", "Титул под именем", "Без титула", titles))

    def _build_select(self, kind: str, placeholder: str, none_label: str, owned: list[dict]) -> discord.ui.Select:
        options = [discord.SelectOption(label=none_label, value="__none__")]
        options += [discord.SelectOption(label=item["name"][:100], value=item["item_id"]) for item in owned[:24]]
        select = discord.ui.Select(placeholder=placeholder, options=options, custom_id=f"economy:equip:{kind}")

        async def callback(interaction: discord.Interaction):
            value = select.values[0]
            await self.cog.handle_equip(interaction, kind, None if value == "__none__" else value)

        select.callback = callback
        return select


class EconomyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ────────────────────────── /daily ──────────────────────────

    @app_commands.command(name="daily", description="Забрать ежедневный бонус монет — растёт со стриком дней подряд")
    async def daily_command(self, interaction: discord.Interaction):
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)
        if not settings["daily_bonus_enabled"]:
            return await interaction.response.send_message("Ежедневный бонус отключён.", ephemeral=True)

        result = economy_core.claim_daily_bonus(interaction.guild.id, interaction.user.id)
        if result["already_claimed"]:
            return await interaction.response.send_message(
                f"Бонус за сегодня уже получен. Стрик: **{result['streak']}** 🔥 Возвращайся завтра!",
                ephemeral=True,
            )

        streak = result["streak"]
        day_word = "день" if streak == 1 else "дня" if streak in (2, 3, 4) else "дней"
        await interaction.response.send_message(
            f"🎁 Ежедневный бонус: **{economy_core.format_amount(result['amount'], settings)}**\n"
            f"Стрик: **{streak}** {day_word} 🔥 (баланс: {economy_core.format_amount(result['balance'], settings)}).",
            ephemeral=True,
        )

    # ────────────────────────── /баланс ──────────────────────────

    @app_commands.command(name="баланс", description="Показать баланс монет (свой или другого участника)")
    @app_commands.describe(участник="Чей баланс показать (по умолчанию — свой)")
    async def balance_command(self, interaction: discord.Interaction, участник: discord.Member | None = None):
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)

        target = участник or interaction.user
        if target.bot:
            return await interaction.response.send_message("У ботов нет кошелька.", ephemeral=True)

        balance = economy_db.get_balance(target.id)
        rank = economy_db.rank_of(target.id)
        embed = discord.Embed(
            title=f"{settings['currency_emoji']} Баланс — {target.display_name}",
            description=f"**{economy_core.format_amount(balance, settings)}**"
            + (f"\nМесто в топе: **#{rank}**" if rank else ""),
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ────────────────────────── /выдать-баланс ──────────────────────────

    @app_commands.command(name="выдать-баланс", description="Начислить (или списать) монеты участнику")
    @app_commands.describe(
        участник="Кому изменить баланс",
        количество="Сколько монет начислить (можно отрицательное число, чтобы списать)",
    )
    @app_commands.default_permissions(manage_guild=True)
    async def grant_balance_command(
        self, interaction: discord.Interaction, участник: discord.Member,
        количество: app_commands.Range[int, -economy_core.BALANCE_ADMIN_MAX, economy_core.BALANCE_ADMIN_MAX],
    ):
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)
        if участник.bot:
            return await interaction.response.send_message("У ботов нет кошелька.", ephemeral=True)

        current = economy_db.get_balance(участник.id)
        new_balance = min(economy_core.BALANCE_ADMIN_MAX, max(0, current + количество))
        economy_db.set_balance(участник.id, new_balance, "admin_grant")

        await interaction.response.send_message(
            f"✅ Баланс {участник.mention}: {economy_core.format_amount(current, settings)} → "
            f"**{economy_core.format_amount(new_balance, settings)}**.",
            ephemeral=True,
        )

    # ────────────────────────── /перевести ──────────────────────────

    @app_commands.command(name="перевести", description="Перевести монеты другому участнику")
    @app_commands.describe(участник="Получатель перевода", количество="Сколько монет перевести")
    async def transfer_command(
        self, interaction: discord.Interaction, участник: discord.Member,
        количество: app_commands.Range[int, 1, economy_core.BALANCE_ADMIN_MAX],
    ):
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)
        if not settings["transfer_enabled"]:
            return await interaction.response.send_message("Переводы между участниками отключены.", ephemeral=True)
        if участник.bot:
            return await interaction.response.send_message("Ботам переводить нельзя.", ephemeral=True)
        if участник.id == interaction.user.id:
            return await interaction.response.send_message("Себе переводить нельзя.", ephemeral=True)

        fee = economy_core.transfer_fee(количество, settings["transfer_fee_percent"])
        if not economy_db.transfer(interaction.user.id, участник.id, количество, fee):
            balance = economy_db.get_balance(interaction.user.id)
            return await interaction.response.send_message(
                f"Недостаточно средств: нужно {economy_core.format_amount(количество + fee, settings)} "
                f"(с комиссией), на балансе {economy_core.format_amount(balance, settings)}.",
                ephemeral=True,
            )

        fee_text = f" Комиссия: {economy_core.format_amount(fee, settings)}." if fee else ""
        await interaction.response.send_message(
            f"💸 {interaction.user.mention} перевёл(а) {economy_core.format_amount(количество, settings)} "
            f"{участник.mention}.{fee_text}"
        )

    # ────────────────────────── /монеты-топ ──────────────────────────

    @app_commands.command(name="монеты-топ", description="Топ участников по количеству монет")
    async def top_command(self, interaction: discord.Interaction):
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)

        top = economy_db.top(10)
        if not top:
            return await interaction.response.send_message("Пока ни у кого нет монет.", ephemeral=True)

        guild = interaction.guild
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for i, row in enumerate(top, start=1):
            member = guild.get_member(row["user_id"]) if guild else None
            name = member.display_name if member else str(row["user_id"])
            prefix = medals.get(i, f"{i}.")
            lines.append(f"{prefix} **{name}** — {economy_core.format_amount(row['balance'], settings)}")

        embed = discord.Embed(
            title=f"{settings['currency_emoji']} Топ по {settings['currency_name']}",
            description="\n".join(lines),
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed)

    # ────────────────────────── /магазин ──────────────────────────

    @app_commands.command(name="магазин", description="Магазин ролей за монеты")
    async def shop_command(self, interaction: discord.Interaction):
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)

        items = settings["shop_items"]
        if not items:
            return await interaction.response.send_message("Магазин пока пуст — товары добавляются в дашборде.", ephemeral=True)

        balance = economy_db.get_balance(interaction.user.id)
        lines = [self._shop_item_line(item, interaction.guild, settings) for item in items]

        embed = discord.Embed(
            title="🛒 Магазин",
            description="\n".join(lines) + f"\n\nВаш баланс: **{economy_core.format_amount(balance, settings)}**",
            color=discord.Color.gold(),
        )
        await interaction.response.send_message(embed=embed, view=ShopView(self, items), ephemeral=True)

    def _shop_item_line(self, item: dict, guild: discord.Guild | None, settings: dict) -> str:
        """Строка товара в /магазин — раньше пыталась резолвить role_id для
        ЛЮБОГО товара (включая косметику без роли вообще), из-за чего рамки и
        титулы всегда показывали «не найдена». Теперь ветвится по типу."""
        price_text = economy_core.format_amount(item["price"], settings)
        if item["type"] == "role":
            role = guild.get_role(int(item["role_id"])) if guild and item["role_id"] else None
            target = role.mention if role else f"роль `{item['role_id']}` (не найдена)"
            name = item["name"] or (role.name if role else "Товар")
        elif item["type"] == "frame_color":
            target = f"рамка карточки `{item['color_hex']}`"
            name = item["name"] or f"Рамка {item['color_hex']}"
        else:  # title
            target = f"титул «{item['title_text']}»"
            name = item["name"] or f"Титул «{item['title_text']}»"
        return f"• **{name}** — {target}: {price_text}"

    async def handle_purchase(self, interaction: discord.Interaction, item_id: str):
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)

        item = economy_core.find_shop_item(settings, item_id)
        if item is None:
            return await interaction.response.send_message("Этот товар уже убрали из магазина.", ephemeral=True)

        if item["type"] == "role":
            await self._purchase_role(interaction, item, settings)
        else:
            await self._purchase_cosmetic(interaction, item, settings)

    async def _purchase_role(self, interaction: discord.Interaction, item: dict, settings: dict):
        guild = interaction.guild
        role = guild.get_role(int(item["role_id"])) if guild and item["role_id"] else None
        if role is None:
            return await interaction.response.send_message("Роль товара не найдена на сервере — сообщите админам.", ephemeral=True)
        if any(r.id == role.id for r in interaction.user.roles):
            return await interaction.response.send_message(f"Роль {role.mention} у вас уже есть.", ephemeral=True)

        if not economy_db.try_spend(interaction.user.id, item["price"], f"shop_{item['id']}"):
            balance = economy_db.get_balance(interaction.user.id)
            return await interaction.response.send_message(
                f"Не хватает средств: цена {economy_core.format_amount(item['price'], settings)}, "
                f"на балансе {economy_core.format_amount(balance, settings)}.",
                ephemeral=True,
            )

        try:
            await interaction.user.add_roles(role, reason=f"Покупка в магазине за {item['price']}")
        except discord.HTTPException:
            economy_db.add(interaction.user.id, item["price"], f"shop_refund_{item['id']}")
            logger.warning("Не удалось выдать роль %s покупателю %s — монеты возвращены", role.id, interaction.user.id)
            return await interaction.response.send_message(
                "Не удалось выдать роль (не хватает прав у бота?) — монеты возвращены.", ephemeral=True
            )

        balance = economy_db.get_balance(interaction.user.id)
        await interaction.response.send_message(
            f"✅ Куплено: {role.mention} за {economy_core.format_amount(item['price'], settings)}. "
            f"Остаток: {economy_core.format_amount(balance, settings)}.",
            ephemeral=True,
        )

    async def _purchase_cosmetic(self, interaction: discord.Interaction, item: dict, settings: dict):
        if economy_db.owns_cosmetic(interaction.user.id, item["id"]):
            return await interaction.response.send_message("У вас уже есть этот товар.", ephemeral=True)

        if not economy_db.try_spend(interaction.user.id, item["price"], f"shop_{item['id']}"):
            balance = economy_db.get_balance(interaction.user.id)
            return await interaction.response.send_message(
                f"Не хватает средств: цена {economy_core.format_amount(item['price'], settings)}, "
                f"на балансе {economy_core.format_amount(balance, settings)}.",
                ephemeral=True,
            )

        value = item["color_hex"] if item["type"] == "frame_color" else item["title_text"]
        display_name = item["name"] or (DEFAULT_ITEM_LABEL[item["type"]] + f" «{value}»")
        economy_db.grant_cosmetic(interaction.user.id, item["id"], item["type"], value, display_name)

        balance = economy_db.get_balance(interaction.user.id)
        await interaction.response.send_message(
            f"✅ Куплено: **{display_name}** за {economy_core.format_amount(item['price'], settings)}. "
            f"Остаток: {economy_core.format_amount(balance, settings)}. Наденьте через /косметика.",
            ephemeral=True,
        )

    # ────────────────────────── /косметика ──────────────────────────

    @app_commands.command(name="косметика", description="Выбрать рамку карточки ранга и титул из купленного в магазине")
    async def cosmetics_command(self, interaction: discord.Interaction):
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(DISABLED_TEXT, ephemeral=True)

        frames = economy_db.list_owned_cosmetics(interaction.user.id, "frame_color")
        titles = economy_db.list_owned_cosmetics(interaction.user.id, "title")
        if not frames and not titles:
            return await interaction.response.send_message(
                "У вас пока нет купленной косметики — загляните в /магазин.", ephemeral=True
            )

        await interaction.response.send_message(
            "Выберите рамку и/или титул для карточки /ранг:",
            view=CosmeticsView(self, frames, titles),
            ephemeral=True,
        )

    async def handle_equip(self, interaction: discord.Interaction, kind: str, item_id: str | None):
        label = "Рамка" if kind == "frame_color" else "Титул"
        if item_id is None:
            economy_db.clear_equipped(interaction.user.id, kind)
            return await interaction.response.send_message(f"{label} снят(а).", ephemeral=True)

        if not economy_db.owns_cosmetic(interaction.user.id, item_id):
            return await interaction.response.send_message("Вы не владеете этим товаром.", ephemeral=True)

        economy_db.set_equipped(interaction.user.id, kind, item_id)
        await interaction.response.send_message(f"{label} применён(а)! Проверьте /ранг.", ephemeral=True)


async def setup(bot: commands.Bot):
    economy_db.init()
    await bot.add_cog(EconomyCog(bot))
