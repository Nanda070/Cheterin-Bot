"""Ког «Экономика»: баланс, переводы, топ и магазин ролей.

Монеты начисляются автоматически как процент от заработанного XP — хук
economy_core.award_for_xp() вызывается из xp.py (текст и войс). Тратятся
в магазине ролей (/магазин) и на ставках в русской рулетке (fun.py).
Модуль выключен по умолчанию, настраивается в дашборде (раздел «Экономика»).
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands, tasks

import embed_style
import economy_core
import economy_db
import i18n
import slash_registry

logger = logging.getLogger("economy")


DEFAULT_ITEM_LABEL = {
    "role": "economy.item_label.role",
    "frame_color": "economy.item_label.frame_color",
    "title": "economy.item_label.title",
}


def _item_label(item_type: str, lang: str) -> str:
    key = DEFAULT_ITEM_LABEL.get(item_type, "economy.item_label.default")
    return i18n.t(key, lang)


def _streak_day_word(streak: int, lang: str) -> str:
    if streak == 1:
        return i18n.t("economy.daily.streak_day_one", lang)
    if lang == "ru" and streak in (2, 3, 4):
        return i18n.t("economy.daily.streak_day_few", lang)
    return i18n.t("economy.daily.streak_day_many", lang)


class ShopView(discord.ui.View):
    """Кнопки покупки по товарам магазина (эфемерное сообщение)."""

    def __init__(self, cog: "EconomyCog", items: list[dict], lang: str):
        super().__init__(timeout=600)
        self.cog = cog
        self.lang = lang
        for item in items[:economy_core.SHOP_ITEMS_MAX]:
            label = item["name"] or _item_label(item["type"], lang)
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

    def __init__(self, cog: "EconomyCog", frames: list[dict], titles: list[dict], lang: str):
        super().__init__(timeout=180)
        self.cog = cog
        self.lang = lang
        if frames:
            self.add_item(
                self._build_select(
                    "frame_color",
                    i18n.t("economy.cosmetics.frame_placeholder", lang),
                    i18n.t("economy.cosmetics.no_frame", lang),
                    frames,
                )
            )
        if titles:
            self.add_item(
                self._build_select(
                    "title",
                    i18n.t("economy.cosmetics.title_placeholder", lang),
                    i18n.t("economy.cosmetics.no_title", lang),
                    titles,
                )
            )

    def _build_select(
        self, kind: str, placeholder: str, none_label: str, owned: list[dict]
    ) -> discord.ui.Select:
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
        self.weekly_report_loop.start()

    def cog_unload(self):
        self.weekly_report_loop.cancel()

    def build_weekly_embed(self, guild: discord.Guild, days: int, lang: str) -> discord.Embed:
        settings = economy_core.get_settings(guild.id)
        rows = economy_db.weekly_report(guild.id, days=days)[:15]
        embed = discord.Embed(
            title=i18n.t("economy.weekly.title", lang, days=days, emoji=settings["currency_emoji"]),
            color=embed_style.GOLD,
            timestamp=discord.utils.utcnow(),
        )
        if not rows:
            embed.description = i18n.t("economy.weekly.empty", lang)
            return embed
        lines = []
        for i, row in enumerate(rows, 1):
            member = guild.get_member(row["user_id"])
            name = member.display_name if member else str(row["user_id"])
            lines.append(
                i18n.t(
                    "economy.weekly.line",
                    lang,
                    rank=i,
                    name=name,
                    earned=row["earned"],
                    spent=row["spent"],
                    net=row["net"],
                    emoji=settings["currency_emoji"],
                )
            )
        embed.description = "\n".join(lines)
        return embed

    async def post_weekly_report(self, guild_id: int) -> bool:
        settings = economy_core.get_settings(guild_id)
        channel_id = settings.get("weekly_report_channel_id") or ""
        if not channel_id:
            return False
        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            return False
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return False
        lang = i18n.lang_for(guild_id)
        days = max(1, min(30, int(settings.get("weekly_report_days") or 7)))
        try:
            await channel.send(embed=self.build_weekly_embed(guild, days, lang))
        except discord.HTTPException:
            logger.warning("Failed to post weekly economy report guild=%s", guild_id)
            return False
        from datetime import datetime
        import timezone_core

        week_key = timezone_core.now_local(guild_id).strftime("%G-W%V")
        economy_core.mark_weekly_report_posted(guild_id, week_key)
        return True

    @tasks.loop(minutes=15)
    async def weekly_report_loop(self):
        try:
            for guild in self.bot.guilds:
                try:
                    if economy_core.should_post_weekly_report(guild.id):
                        await self.post_weekly_report(guild.id)
                except Exception as exc:
                    logger.exception("weekly_report_loop guild=%s", guild.id)
                    cog = self.bot.get_cog("OwnerAlertsCog")
                    if cog:
                        cog.report_module_error(guild.id, "economy", str(exc))
        except Exception:
            logger.exception("weekly_report_loop error")

    @weekly_report_loop.before_loop
    async def before_weekly_report_loop(self):
        await self.bot.wait_until_ready()

    # ────────────────────────── /daily ──────────────────────────

    @app_commands.command(name="daily", description="Забрать ежедневный бонус монет — растёт со стриком дней подряд")
    async def daily_command(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "economy"), ephemeral=True
            )
        if not settings["daily_bonus_enabled"]:
            return await interaction.response.send_message(
                i18n.t("economy.daily.disabled", lang), ephemeral=True
            )

        result = economy_core.claim_daily_bonus(interaction.guild.id, interaction.user.id)
        if result["already_claimed"]:
            return await interaction.response.send_message(
                i18n.t(
                    "economy.daily.already_claimed",
                    lang,
                    streak=result["streak"],
                ),
                ephemeral=True,
            )

        streak = result["streak"]
        await interaction.response.send_message(
            i18n.t(
                "economy.daily.claimed",
                lang,
                amount=economy_core.format_amount(result["amount"], settings),
                streak=streak,
                day_word=_streak_day_word(streak, lang),
                balance=economy_core.format_amount(result["balance"], settings),
            ),
            ephemeral=True,
        )

    # ────────────────────────── /баланс ──────────────────────────

    @app_commands.command(name="баланс", description="Показать баланс монет (свой или другого участника)")
    @app_commands.describe(участник="Чей баланс показать (по умолчанию — свой)")
    async def balance_command(self, interaction: discord.Interaction, участник: discord.Member | None = None):
        lang = i18n.lang_for(interaction.guild_id)
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "economy"), ephemeral=True
            )

        target = участник or interaction.user
        if target.bot:
            return await interaction.response.send_message(
                i18n.t("economy.error.bot_no_wallet", lang), ephemeral=True
            )

        balance = economy_db.get_balance(interaction.guild.id, target.id)
        rank = economy_db.rank_of(interaction.guild.id, target.id)
        embed = discord.Embed(
            title=i18n.t(
                "economy.balance.title",
                lang,
                emoji=settings["currency_emoji"],
                name=target.display_name,
            ),
            description=f"**{economy_core.format_amount(balance, settings)}**"
            + (i18n.t("economy.balance.rank", lang, rank=rank) if rank else ""),
            color=embed_style.GOLD,
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
        self,
        interaction: discord.Interaction,
        участник: discord.Member,
        количество: app_commands.Range[int, -economy_core.BALANCE_ADMIN_MAX, economy_core.BALANCE_ADMIN_MAX],
    ):
        lang = i18n.lang_for(interaction.guild_id)
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "economy"), ephemeral=True
            )
        if участник.bot:
            return await interaction.response.send_message(
                i18n.t("economy.error.bot_no_wallet", lang), ephemeral=True
            )

        current = economy_db.get_balance(interaction.guild.id, участник.id)
        new_balance = min(economy_core.BALANCE_ADMIN_MAX, max(0, current + количество))
        economy_db.set_balance(interaction.guild.id, участник.id, new_balance, "admin_grant")

        await interaction.response.send_message(
            i18n.t(
                "economy.grant.success",
                lang,
                mention=участник.mention,
                old_balance=economy_core.format_amount(current, settings),
                new_balance=economy_core.format_amount(new_balance, settings),
            ),
            ephemeral=True,
        )

    # ────────────────────────── /перевести ──────────────────────────

    @app_commands.command(name="перевести", description="Перевести монеты другому участнику")
    @app_commands.describe(участник="Получатель перевода", количество="Сколько монет перевести")
    async def transfer_command(
        self,
        interaction: discord.Interaction,
        участник: discord.Member,
        количество: app_commands.Range[int, 1, economy_core.BALANCE_ADMIN_MAX],
    ):
        lang = i18n.lang_for(interaction.guild_id)
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "economy"), ephemeral=True
            )
        if not settings["transfer_enabled"]:
            return await interaction.response.send_message(
                i18n.t("economy.transfer.disabled", lang), ephemeral=True
            )
        if участник.bot:
            return await interaction.response.send_message(
                i18n.t("economy.transfer.no_bots", lang), ephemeral=True
            )
        if участник.id == interaction.user.id:
            return await interaction.response.send_message(
                i18n.t("economy.transfer.no_self", lang), ephemeral=True
            )

        fee = economy_core.transfer_fee(количество, settings["transfer_fee_percent"])
        if not economy_db.transfer(interaction.guild.id, interaction.user.id, участник.id, количество, fee):
            balance = economy_db.get_balance(interaction.guild.id, interaction.user.id)
            return await interaction.response.send_message(
                i18n.t(
                    "economy.transfer.insufficient",
                    lang,
                    needed=economy_core.format_amount(количество + fee, settings),
                    balance=economy_core.format_amount(balance, settings),
                ),
                ephemeral=True,
            )

        fee_text = (
            i18n.t("economy.transfer.fee", lang, fee=economy_core.format_amount(fee, settings))
            if fee
            else ""
        )
        await interaction.response.send_message(
            i18n.t(
                "economy.transfer.success",
                lang,
                sender=interaction.user.mention,
                amount=economy_core.format_amount(количество, settings),
                recipient=участник.mention,
                fee_text=fee_text,
            )
        )

    # ────────────────────────── /монеты-топ ──────────────────────────

    @app_commands.command(name="монеты-топ", description="Топ участников по количеству монет")
    async def top_command(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "economy"), ephemeral=True
            )

        top = economy_db.top(interaction.guild.id, 10)
        if not top:
            return await interaction.response.send_message(
                i18n.t("economy.top.empty", lang), ephemeral=True
            )

        guild = interaction.guild
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for i, row in enumerate(top, start=1):
            member = guild.get_member(row["user_id"]) if guild else None
            name = member.display_name if member else str(row["user_id"])
            prefix = medals.get(i, f"{i}.")
            lines.append(f"{prefix} **{name}** — {economy_core.format_amount(row['balance'], settings)}")

        embed = discord.Embed(
            title=i18n.t(
                "economy.top.title",
                lang,
                emoji=settings["currency_emoji"],
                currency_name=settings["currency_name"],
            ),
            description="\n".join(lines),
            color=embed_style.GOLD,
        )
        await interaction.response.send_message(embed=embed)

    # ────────────────────────── /магазин ──────────────────────────

    @app_commands.command(name="магазин", description="Магазин ролей за монеты")
    async def shop_command(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "economy"), ephemeral=True
            )

        items = settings["shop_items"]
        if not items:
            return await interaction.response.send_message(
                i18n.t("economy.shop.empty", lang), ephemeral=True
            )

        balance = economy_db.get_balance(interaction.guild.id, interaction.user.id)
        lines = [self._shop_item_line(item, interaction.guild, settings, lang) for item in items]

        embed = discord.Embed(
            title=i18n.t("economy.shop.title", lang),
            description="\n".join(lines)
            + i18n.t(
                "economy.shop.balance",
                lang,
                balance=economy_core.format_amount(balance, settings),
            ),
            color=embed_style.GOLD,
        )
        await interaction.response.send_message(
            embed=embed, view=ShopView(self, items, lang), ephemeral=True
        )

    def _shop_item_line(
        self, item: dict, guild: discord.Guild | None, settings: dict, lang: str
    ) -> str:
        """Строка товара в /магазин — раньше пыталась резолвить role_id для
        ЛЮБОГО товара (включая косметику без роли вообще), из-за чего рамки и
        титулы всегда показывали «не найдена». Теперь ветвится по типу."""
        price_text = economy_core.format_amount(item["price"], settings)
        if item["type"] == "role":
            role = guild.get_role(int(item["role_id"])) if guild and item["role_id"] else None
            target = (
                role.mention
                if role
                else i18n.t("economy.shop.role_not_found", lang, role_id=item["role_id"])
            )
            name = item["name"] or (role.name if role else i18n.t("economy.item_label.default", lang))
        elif item["type"] == "frame_color":
            target = i18n.t("economy.shop.frame_target", lang, color_hex=item["color_hex"])
            name = item["name"] or i18n.t("economy.shop.frame_name", lang, color_hex=item["color_hex"])
        else:  # title
            target = i18n.t("economy.shop.title_target", lang, title_text=item["title_text"])
            name = item["name"] or i18n.t("economy.shop.title_name", lang, title_text=item["title_text"])
        return i18n.t("economy.shop.item_line", lang, name=name, target=target, price=price_text)

    async def handle_purchase(self, interaction: discord.Interaction, item_id: str):
        lang = i18n.lang_for(interaction.guild_id)
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "economy"), ephemeral=True
            )

        item = economy_core.find_shop_item(settings, item_id)
        if item is None:
            return await interaction.response.send_message(
                i18n.t("economy.purchase.item_removed", lang), ephemeral=True
            )

        if item["type"] == "role":
            await self._purchase_role(interaction, item, settings, lang)
        else:
            await self._purchase_cosmetic(interaction, item, settings, lang)

    async def _purchase_role(
        self, interaction: discord.Interaction, item: dict, settings: dict, lang: str
    ):
        guild = interaction.guild
        role = guild.get_role(int(item["role_id"])) if guild and item["role_id"] else None
        if role is None:
            return await interaction.response.send_message(
                i18n.t("economy.purchase.role_not_found", lang), ephemeral=True
            )
        if any(r.id == role.id for r in interaction.user.roles):
            return await interaction.response.send_message(
                i18n.t("economy.purchase.role_already_owned", lang, mention=role.mention),
                ephemeral=True,
            )

        if not economy_db.try_spend(interaction.guild.id, interaction.user.id, item["price"], f"shop_{item['id']}"):
            balance = economy_db.get_balance(interaction.guild.id, interaction.user.id)
            return await interaction.response.send_message(
                i18n.t(
                    "economy.purchase.insufficient",
                    lang,
                    price=economy_core.format_amount(item["price"], settings),
                    balance=economy_core.format_amount(balance, settings),
                ),
                ephemeral=True,
            )

        try:
            await interaction.user.add_roles(role, reason=f"Покупка в магазине за {item['price']}")
        except discord.HTTPException:
            economy_db.add(interaction.guild.id, interaction.user.id, item["price"], f"shop_refund_{item['id']}")
            logger.warning("Не удалось выдать роль %s покупателю %s — монеты возвращены", role.id, interaction.user.id)
            return await interaction.response.send_message(
                i18n.t("economy.purchase.role_grant_failed", lang), ephemeral=True
            )

        balance = economy_db.get_balance(interaction.guild.id, interaction.user.id)
        await interaction.response.send_message(
            i18n.t(
                "economy.purchase.role_success",
                lang,
                role=role.mention,
                price=economy_core.format_amount(item["price"], settings),
                balance=economy_core.format_amount(balance, settings),
            ),
            ephemeral=True,
        )

    async def _purchase_cosmetic(
        self, interaction: discord.Interaction, item: dict, settings: dict, lang: str
    ):
        if economy_db.owns_cosmetic(interaction.guild.id, interaction.user.id, item["id"]):
            return await interaction.response.send_message(
                i18n.t("economy.purchase.cosmetic_already_owned", lang), ephemeral=True
            )

        if not economy_db.try_spend(interaction.guild.id, interaction.user.id, item["price"], f"shop_{item['id']}"):
            balance = economy_db.get_balance(interaction.guild.id, interaction.user.id)
            return await interaction.response.send_message(
                i18n.t(
                    "economy.purchase.insufficient",
                    lang,
                    price=economy_core.format_amount(item["price"], settings),
                    balance=economy_core.format_amount(balance, settings),
                ),
                ephemeral=True,
            )

        value = item["color_hex"] if item["type"] == "frame_color" else item["title_text"]
        display_name = item["name"] or (_item_label(item["type"], lang) + f" «{value}»")
        economy_db.grant_cosmetic(
            interaction.guild.id, interaction.user.id, item["id"], item["type"], value, display_name
        )

        balance = economy_db.get_balance(interaction.guild.id, interaction.user.id)
        await interaction.response.send_message(
            i18n.t(
                "economy.purchase.cosmetic_success",
                lang,
                name=display_name,
                price=economy_core.format_amount(item["price"], settings),
                balance=economy_core.format_amount(balance, settings),
            ),
            ephemeral=True,
        )

    # ────────────────────────── /косметика ──────────────────────────

    @app_commands.command(name="косметика", description="Выбрать рамку карточки ранга и титул из купленного в магазине")
    async def cosmetics_command(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "economy"), ephemeral=True
            )

        frames = economy_db.list_owned_cosmetics(interaction.guild.id, interaction.user.id, "frame_color")
        titles = economy_db.list_owned_cosmetics(interaction.guild.id, interaction.user.id, "title")
        if not frames and not titles:
            return await interaction.response.send_message(
                i18n.t("economy.cosmetics.empty", lang), ephemeral=True
            )

        await interaction.response.send_message(
            i18n.t("economy.cosmetics.prompt", lang),
            view=CosmeticsView(self, frames, titles, lang),
            ephemeral=True,
        )

    async def handle_equip(self, interaction: discord.Interaction, kind: str, item_id: str | None):
        lang = i18n.lang_for(interaction.guild_id)
        if item_id is None:
            economy_db.clear_equipped(interaction.guild.id, interaction.user.id, kind)
            key = "economy.equip.frame_removed" if kind == "frame_color" else "economy.equip.title_removed"
            return await interaction.response.send_message(i18n.t(key, lang), ephemeral=True)

        if not economy_db.owns_cosmetic(interaction.guild.id, interaction.user.id, item_id):
            return await interaction.response.send_message(
                i18n.t("economy.equip.not_owned", lang), ephemeral=True
            )

        economy_db.set_equipped(interaction.guild.id, interaction.user.id, kind, item_id)
        key = "economy.equip.frame_applied" if kind == "frame_color" else "economy.equip.title_applied"
        await interaction.response.send_message(i18n.t(key, lang), ephemeral=True)

    # ────────────────────────── /economy-weekly ──────────────────────────

    @app_commands.command(name="economy-weekly", description="Show the weekly economy report")
    @app_commands.default_permissions(manage_guild=True)
    async def weekly_command(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        settings = economy_core.get_settings(interaction.guild.id)
        if not settings["enabled"]:
            return await interaction.response.send_message(
                i18n.module_disabled(lang, "economy"), ephemeral=True
            )
        days = max(1, min(30, int(settings.get("weekly_report_days") or 7)))
        embed = self.build_weekly_embed(interaction.guild, days, lang)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    economy_db.init()
    cog = EconomyCog(bot)
    slash_registry.register_economy(cog)
    await bot.add_cog(cog)
