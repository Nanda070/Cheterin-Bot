import asyncio
import logging

import discord

import bot.core.embed_style as embed_style
import bot.modules.community.events as events
import bot.core.i18n as i18n

logger = logging.getLogger("chetbot.events_core")


async def close_event(bot, guild_id: int, message_id: str) -> dict:
    lang = i18n.lang_for(guild_id)
    data = events.load_events(guild_id)
    ev = data["events"].get(message_id)
    if not ev:
        return {"ok": False, "error": "not_found"}

    ev["status"] = "closed"
    events.save_events(guild_id, data)

    try:
        ch = bot.get_channel(ev["channel_id"])
        if not ch:
            try:
                ch = await bot.fetch_channel(ev["channel_id"])
            except Exception:
                ch = None
        if ch:
            msg = await ch.fetch_message(int(message_id))
            if msg.embeds:
                emb = msg.embeds[0].copy()
                emb.set_footer(text=i18n.t("events.core.status.closed", lang))
                view = events.create_participation_view(message_id, ev, disabled=True, lang=lang)
                await msg.edit(embed=emb, view=view)
    except Exception as e:
        logger.warning("Не удалось закрыть сообщение события %s: %s", message_id, e)

    return {"ok": True}


async def delete_event(bot, guild_id: int, message_id: str) -> dict:
    data = events.load_events(guild_id)
    ev = data["events"].pop(message_id, None)
    if not ev:
        return {"ok": False, "error": "not_found"}
    events.save_events(guild_id, data)

    role_id = ev.get("role_reward")
    guild = bot.get_guild(guild_id)
    if role_id and guild:
        role = guild.get_role(role_id)
        if role:
            for p in ev.get("participants", []):
                try:
                    mem = bot.get_guild(guild_id).get_member(p["user_id"])
                    if mem:
                        await mem.remove_roles(role)
                except Exception as e:
                    logger.debug("Не удалось снять роль с участника %s: %s", p.get("user_id"), e)

    try:
        ch = bot.get_channel(ev["channel_id"])
        if not ch:
            try:
                ch = await bot.fetch_channel(ev["channel_id"])
            except Exception:
                ch = None
        if ch:
            msg = await ch.fetch_message(int(message_id))
            await msg.delete()
    except Exception as e:
        logger.warning("Не удалось удалить сообщение события %s: %s", message_id, e)

    return {"ok": True}


async def notify_participants(bot, guild_id: int, message_id: str, text: str) -> dict:
    lang = i18n.lang_for(guild_id)
    data = events.load_events(guild_id)
    ev = data.get("events", {}).get(message_id)
    if not ev:
        return {"ok": False, "error": "not_found"}

    participants = ev.get("participants", [])
    if not participants:
        return {"ok": False, "error": "no_participants"}

    user_ids = list(set(p.get("user_id") for p in participants if p.get("user_id")))

    success = 0
    failed = 0
    for uid in user_ids:
        try:
            guild = bot.get_guild(guild_id)
            user = (guild.get_member(uid) if guild else None) or await bot.fetch_user(uid)
            if user:
                await user.send(content=i18n.t("events.core.notify_dm", lang, title=ev.get("title"), text=text))
                success += 1
            else:
                failed += 1
        except Exception as e:
            logger.debug("Не удалось отправить уведомление участнику %s: %s", uid, e)
            failed += 1
        await asyncio.sleep(0.1)

    return {"ok": True, "success": success, "failed": failed}


def validate_event_spec(spec: dict) -> str | None:
    if spec.get("type") not in ("tournament", "poll"):
        return "invalid_type"

    title = spec.get("title", "")
    if not title or len(title) > 100:
        return "invalid_title"

    description = spec.get("description", "")
    if not description or len(description) > 2000:
        return "invalid_description"

    if spec.get("ping", "none") not in ("none", "everyone", "here"):
        return "invalid_ping"

    if spec["type"] == "tournament":
        if spec.get("mode") not in ("solo", "team_captain", "team_code"):
            return "invalid_mode"
        max_limit = spec.get("max_limit", 0)
        if not isinstance(max_limit, int) or max_limit < 0:
            return "invalid_max_limit"
        if spec.get("mode") != "solo":
            team_size = spec.get("team_size", 5)
            if not isinstance(team_size, int) or team_size < 2:
                return "invalid_team_size"
    else:
        options = spec.get("options")
        if (
            not isinstance(options, list)
            or not (2 <= len(options) <= 10)
            or not all(isinstance(o, str) and o.strip() for o in options)
        ):
            return "invalid_options"

    return None


async def publish_event(bot, channel, spec: dict, author_id: int) -> discord.Message:
    lang = i18n.lang_for(channel.guild.id)
    emb = discord.Embed(
        title=spec["title"],
        description=spec["description"],
        color=embed_style.DANGER if spec["type"] == "tournament" else embed_style.INFO,
    )
    banner_url = spec.get("banner_url") or ""
    if banner_url:
        emb.set_image(url=banner_url)

    if spec["type"] == "tournament":
        mode_key = f"events.core.mode.{spec.get('mode', 'solo')}"
        mode_str = i18n.t(mode_key, lang)
        emb.add_field(name=i18n.t("events.core.field.format", lang), value=mode_str, inline=True)
        max_limit = spec.get("max_limit", 0)
        if max_limit > 0:
            emb.add_field(name=i18n.t("events.core.field.limit", lang), value=f"0 / {max_limit}", inline=True)
        else:
            emb.add_field(name=i18n.t("events.core.field.participants", lang), value="0", inline=True)
    else:
        for opt in spec.get("options", []):
            emb.add_field(name=opt, value=i18n.t("events.core.poll.bar", lang), inline=False)

    emb.set_footer(text=i18n.t("events.core.status.open", lang))

    ping = spec.get("ping", "none")
    content = None
    if ping == "everyone":
        content = "@everyone"
    elif ping == "here":
        content = "@here"

    msg = await channel.send(content=content, embed=emb)

    role_reward_raw = spec.get("role_reward")
    event_obj = {
        "type": spec["type"],
        "channel_id": channel.id,
        "author_id": author_id,
        "title": spec["title"],
        "description": spec["description"],
        "banner_url": banner_url,
        "mode": spec.get("mode", "solo"),
        "require_info": spec.get("require_info", False),
        "max_limit": spec.get("max_limit", 0),
        "team_size": spec.get("team_size", 5),
        "role_reward": int(role_reward_raw) if role_reward_raw else None,
        "ping": ping,
        "status": "open",
        "participants": [],
        "options": spec.get("options", []),
        "multi_select": spec.get("multi_select", False),
        "votes": {},
    }

    guild_id = channel.guild.id
    data = events.load_events(guild_id)
    data["events"][str(msg.id)] = event_obj
    events.save_events(guild_id, data)

    view = events.create_participation_view(str(msg.id), event_obj, lang=lang)
    await msg.edit(view=view)

    return msg
