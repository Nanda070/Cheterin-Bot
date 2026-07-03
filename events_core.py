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
