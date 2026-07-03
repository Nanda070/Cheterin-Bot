import asyncio
import logging

import discord

import events

logger = logging.getLogger("chetbot.events_core")


async def close_event(bot, message_id: str) -> dict:
    data = await events.load_events()
    ev = data["events"].get(message_id)
    if not ev:
        return {"ok": False, "error": "not_found"}

    ev["status"] = "closed"
    await events.save_events(data)

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
                emb.set_footer(text="🔴 Статус: Закрыто")
                view = events.create_participation_view(message_id, ev, disabled=True)
                await msg.edit(embed=emb, view=view)
    except Exception as e:
        logger.warning("Не удалось закрыть сообщение события %s: %s", message_id, e)

    return {"ok": True}


async def delete_event(bot, guild, message_id: str) -> dict:
    data = await events.load_events()
    ev = data["events"].pop(message_id, None)
    if not ev:
        return {"ok": False, "error": "not_found"}
    await events.save_events(data)

    role_id = ev.get("role_reward")
    if role_id and guild:
        role = guild.get_role(role_id)
        if role:
            for p in ev.get("participants", []):
                try:
                    mem = guild.get_member(p["user_id"])
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


async def notify_participants(bot, guild, message_id: str, text: str) -> dict:
    data = await events.load_events()
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
            user = (guild.get_member(uid) if guild else None) or await bot.fetch_user(uid)
            if user:
                await user.send(content=f"**📢 Уведомление о событии «{ev.get('title')}»:**\n\n{text}")
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
    emb = discord.Embed(
        title=spec["title"],
        description=spec["description"],
        color=discord.Color.brand_red() if spec["type"] == "tournament" else discord.Color.blurple(),
    )
    banner_url = spec.get("banner_url") or ""
    if banner_url:
        emb.set_image(url=banner_url)

    if spec["type"] == "tournament":
        mode_str = {"solo": "Соло", "team_captain": "Командный", "team_code": "Командный (по коду)"}.get(
            spec.get("mode", "solo")
        )
        emb.add_field(name="Формат", value=mode_str, inline=True)
        max_limit = spec.get("max_limit", 0)
        if max_limit > 0:
            emb.add_field(name="Лимит", value=f"0 / {max_limit}", inline=True)
        else:
            emb.add_field(name="Участники", value="0", inline=True)
    else:
        for opt in spec.get("options", []):
            emb.add_field(name=opt, value="░░░░░░░░░░ 0% (0 гол.)", inline=False)

    emb.set_footer(text="🟢 Статус: Открыто")

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

    data = await events.load_events()
    data["events"][str(msg.id)] = event_obj
    await events.save_events(data)

    view = events.create_participation_view(str(msg.id), event_obj)
    await msg.edit(view=view)

    return msg
