import settings_db
import logging

import discord

import embed_style
import feedback_panel_core
import i18n

logger = logging.getLogger(__name__)


def upsert_embed_field(embed: discord.Embed, field_name: str, value: str, inline: bool = False):
    for index, field in enumerate(embed.fields):
        if field.name == field_name:
            embed.set_field_at(index, name=field_name, value=value, inline=inline)
            return
    embed.add_field(name=field_name, value=value, inline=inline)


async def decide_case(bot, guild, case_id: str, approved: bool, decided_by_id: int, decided_by_mention: str) -> dict:
    from feedback_menu import FeedbackDecisionView, get_feedback_categories

    lang = i18n.lang_for(guild.id if guild else None)
    cases = settings_db.get(guild.id, "feedback_cases", {})
    case_data = cases.get(case_id)
    if not case_data:
        return {"ok": False, "error": "not_found"}
    if case_data.get("status") != "pending":
        return {"ok": False, "error": "already_decided"}

    category_key = case_data["category_key"]
    config = get_feedback_categories(guild.id).get(category_key)
    if config is None:
        return {"ok": False, "error": "category_deleted"}
    status_text = (
        i18n.t("feedback.status.approved", lang)
        if approved
        else i18n.t("feedback.status.denied", lang)
    )
    reviewed_status = i18n.t("feedback.status.reviewed_with", lang, status=status_text)
    status_field = i18n.t("feedback.field.status", lang)
    reviewer_field = i18n.t("feedback.field.reviewer", lang)

    case_data["status"] = "approved" if approved else "denied"
    case_data["status_label"] = reviewed_status
    case_data["reviewed_by"] = decided_by_id
    case_data["reviewed_at"] = bot.utcnow().isoformat()
    settings_db.put(guild.id, "feedback_cases", cases)

    color = embed_style.SUCCESS if approved else embed_style.DANGER

    public_channel = bot.get_channel(case_data.get("public_channel_id"))
    if public_channel is not None:
        try:
            public_message = await public_channel.fetch_message(case_data["public_message_id"])
            if public_message.embeds:
                emb = public_message.embeds[0].copy()
                emb.color = color
                upsert_embed_field(emb, status_field, reviewed_status, inline=True)
                upsert_embed_field(emb, reviewer_field, decided_by_mention, inline=False)
                await public_message.edit(embed=emb)
        except Exception as e:
            logger.warning("Не удалось обновить публичное сообщение для %s: %s", case_id, e)

    thread = bot.get_channel(case_data.get("thread_id"))
    if thread is not None:
        try:
            decision_message = await thread.fetch_message(case_data["decision_message_id"])
            if decision_message.embeds:
                emb = decision_message.embeds[0].copy()
                emb.color = color
                upsert_embed_field(emb, status_field, reviewed_status, inline=False)
                upsert_embed_field(
                    emb,
                    reviewer_field,
                    f"{decided_by_mention} (`{decided_by_id}`)",
                    inline=False,
                )
                await decision_message.edit(
                    embed=emb,
                    view=FeedbackDecisionView(
                        bot, case_id, case_data["submitter_id"], category_key, guild.id, disabled=True
                    ),
                )
        except Exception as e:
            logger.warning("Не удалось обновить сообщение решения для %s: %s", case_id, e)

    user = guild.get_member(case_data["submitter_id"]) if guild else None
    if user is None:
        try:
            user = await bot.fetch_user(case_data["submitter_id"])
        except Exception as e:
            logger.debug("Не удалось получить пользователя %s: %s", case_data["submitter_id"], e)

    dm_ok = False
    if user:
        dm_emb = discord.Embed(
            title=i18n.t("feedback.dm.title", lang, case_id=case_id),
            description=i18n.t("feedback.dm.description", lang),
            color=color,
            timestamp=bot.utcnow(),
        )
        dm_emb.add_field(name=status_field, value=i18n.t("feedback.status.reviewed", lang), inline=False)
        dm_emb.add_field(
            name=i18n.t("feedback.dm.field.outcome", lang),
            value=config["approved_text"] if approved else config["denied_text"],
            inline=False,
        )
        dm_emb.add_field(
            name=reviewer_field,
            value=f"{decided_by_mention} (`{decided_by_id}`)",
            inline=False,
        )
        dm_emb.set_footer(text=i18n.t("feedback.dm.footer", lang, case_id=case_id))
        try:
            await user.send(embed=dm_emb)
            dm_ok = True
        except Exception as e:
            logger.debug("Не удалось отправить DM пользователю %s: %s", user.id, e)

    dm_status = i18n.t("feedback.log.dm_ok", lang) if dm_ok else i18n.t("feedback.log.dm_fail", lang)
    log_emb = discord.Embed(
        title=i18n.t("feedback.log.decision", lang),
        description=i18n.t(
            "feedback.log.decision_body",
            lang,
            case_id=case_id,
            decision=status_text,
            mention=decided_by_mention,
            user_id=decided_by_id,
            dm_status=dm_status,
        ),
        color=color,
        timestamp=bot.utcnow(),
    )
    await bot.send_log(guild.id if guild else 0, log_emb)

    if thread is not None:
        dec_emb = discord.Embed(
            title=i18n.t("feedback.thread.decision_title", lang, case_id=case_id),
            color=color,
            timestamp=bot.utcnow(),
        )
        dec_emb.add_field(name=status_field, value=status_text, inline=False)
        dec_emb.add_field(
            name=reviewer_field,
            value=f"{decided_by_mention} (`{decided_by_id}`)",
            inline=False,
        )
        try:
            await thread.send(embed=dec_emb)
            await thread.edit(archived=True, locked=True)
        except Exception as e:
            logger.warning("Не удалось закрыть тред %s: %s", thread.id, e)

    return {"ok": True, "error": None}


async def publish_feedback_panel(bot, channel, published_by_id: int, published_by_mention: str) -> discord.Message:
    from feedback_menu import FeedbackView

    lang = i18n.lang_for(channel.guild.id)
    payload = feedback_panel_core.build_panel_payload(channel.guild.id, lang)
    message = await channel.send(**{k: v for k, v in payload.items() if v is not None}, view=FeedbackView(bot, channel.guild.id))

    log_embed = discord.Embed(
        title=i18n.t("feedback.log.panel_published", lang),
        description=i18n.t(
            "feedback.log.panel_published_body",
            lang,
            mention=published_by_mention,
            user_id=published_by_id,
            channel_mention=channel.mention,
            jump_url=message.jump_url,
        ),
        color=embed_style.INFO,
        timestamp=bot.utcnow(),
    )
    await bot.send_log(channel.guild.id, log_embed)

    return message
