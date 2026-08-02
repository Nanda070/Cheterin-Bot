"""ValChecker Discord embeds — Valorant red accent brand exception."""

from __future__ import annotations

import discord

import i18n
import valchecker_stats as stats
import valchecker_valorant_api as vap

COLORS = {
    "valorant": 0xFF4655,
    "dark": 0x1C252E,
    "win": 0x3DD68C,
    "loss": 0xFF4655,
    "info": 0x7AA2F7,
    "soft": 0x8899AA,
    "accent": 0xFF8A80,
}

RANK_COLORS = {
    "Unrated": 0x6B7280,
    "Iron": 0x6B7280,
    "Bronze": 0xA97142,
    "Silver": 0x9AA4B2,
    "Gold": 0xD4AF37,
    "Platinum": 0x45C4B0,
    "Diamond": 0x7DD3FC,
    "Ascendant": 0x34D399,
    "Immortal": 0xF43F5E,
    "Radiant": 0xFBBF24,
}


def color_for_rank(rank_name: str | None) -> int:
    return RANK_COLORS.get(stats.rank_group(rank_name), COLORS["dark"])


def _brand_footer(extra: str | None = None) -> str:
    return f"ValChecker · {extra}" if extra else "ValChecker"


def base_embed(*, color: int | None = None, timestamp: bool = False, footer: str | None = None) -> discord.Embed:
    embed = discord.Embed(color=color if color is not None else COLORS["dark"])
    embed.set_footer(text=_brand_footer(footer))
    if timestamp:
        embed.timestamp = discord.utils.utcnow()
    return embed


def error_embed(message: str, lang: str = "en") -> discord.Embed:
    embed = base_embed(color=COLORS["soft"])
    embed.title = i18n.t("valchecker.common.error_title", lang)
    embed.description = message
    return embed


def _rank_field_value(rank_info: dict | None) -> str:
    if not rank_info:
        return "—"
    lines = []
    if rank_info.get("movement") in ("promoted", "demoted"):
        lines.append(f"{rank_info.get('prevRank') or '?'} → **{rank_info['rank']}**")
    else:
        lines.append(f"**{rank_info['rank']}**")
    if rank_info.get("delta") is not None:
        lines.append(f"{rank_info['rr']} RR · {stats.signed(rank_info['delta'])}")
    else:
        lines.append(f"{rank_info['rr']} RR")
    return "\n".join(lines)


def match_embed(summary: dict, rank_info=None, lang: str = "en") -> discord.Embed:
    p = summary.get("player")
    won = summary.get("won") is True
    lost = summary.get("won") is False
    mark = "W" if won else "L" if lost else "·"
    color = COLORS["win"] if won else COLORS["loss"] if lost else COLORS["info"]
    mode = stats.mode_label(summary.get("mode"), lang)

    desc_parts = [
        f"**{mark}**  ·  {mode or i18n.t('valchecker.common.unknown', lang)}"
        + (f"  ·  {summary['season']}" if summary.get("season") else ""),
        f"**{p['agent']}**" if p else i18n.t("valchecker.match.player_missing", lang),
    ]
    embed = base_embed(color=color, timestamp=True, footer=mode or None)
    embed.set_author(
        name=stats.riot_id(p["name"], p["tag"]) if p else i18n.t("valchecker.match.title", lang),
        icon_url=p.get("agentIcon") if p else None,
    )
    embed.title = summary.get("map") or i18n.t("valchecker.match.title", lang)
    embed.description = "\n".join(x for x in desc_parts if x)

    if p:
        if rank_info and rank_info.get("movement") == "promoted":
            rank_name = i18n.t("valchecker.match.rank_promoted", lang)
        elif rank_info and rank_info.get("movement") == "demoted":
            rank_name = i18n.t("valchecker.match.rank_demoted", lang)
        else:
            rank_name = i18n.t("valchecker.match.rank", lang)

        embed.add_field(
            name=i18n.t("valchecker.match.score", lang),
            value=f"`{summary.get('scoreline')}`\n{stats.ago(summary.get('startedAt'), lang)}",
            inline=True,
        )
        embed.add_field(
            name=i18n.t("valchecker.match.kda", lang),
            value=(
                f"`{p['kills']}/{p['deaths']}/{p['assists']}`\n"
                f"KD **{stats.kd(p['kills'], p['deaths'])}** · ACS **{p['acs']:.0f}** · HS **{stats.pct(p['hsPct'])}**"
            ),
            inline=True,
        )
        embed.add_field(
            name=rank_name,
            value=_rank_field_value(rank_info) if rank_info else "—",
            inline=True,
        )
    elif rank_info:
        embed.add_field(
            name=i18n.t("valchecker.match.rank", lang),
            value=_rank_field_value(rank_info),
            inline=True,
        )

    if p and p.get("agentIcon"):
        embed.set_thumbnail(url=p["agentIcon"])
    if summary.get("mapImage"):
        embed.set_image(url=summary["mapImage"])
    return embed


def profile_embed(player, mmr, account, agg, summaries=None, lang: str = "en") -> discord.Embed:
    summaries = summaries or []
    rank_asset = vap.rank_by_tier(mmr.get("tier"))
    rank_icon = (rank_asset or {}).get("largeIcon") or (rank_asset or {}).get("smallIcon")
    level = "—"
    if account:
        level = account.get("account_level") or account.get("accountLevel") or "—"
    dots = stats.form_strip_dots(summaries, 5)
    color = color_for_rank(mmr.get("rank"))

    peak = None
    if mmr.get("peak"):
        peak = mmr["peak"]["name"]
        if mmr["peak"].get("season"):
            peak = f"{peak} · {mmr['peak']['season']}"

    desc = [
        f"**{mmr.get('rank')}**  ·  {mmr.get('rr')} RR",
        f"{i18n.t('valchecker.common.last', lang)} {stats.signed(mmr['lastChange'])}"
        if mmr.get("lastChange") is not None
        else None,
        f"LB #{mmr['leaderboard']['rank']}" if (mmr.get("leaderboard") or {}).get("rank") else None,
        f"{i18n.t('valchecker.common.peak', lang)} {peak}" if peak else None,
        f"\n{dots}" if dots != "—" else None,
    ]

    embed = base_embed(color=color, footer=(player.get("region") or "").upper() or None)
    embed.set_author(name=stats.riot_id(player["name"], player["tag"]), icon_url=rank_icon)
    embed.title = i18n.t("valchecker.profile.title", lang)
    embed.description = "\n".join(x for x in desc if x)

    acct_lines = [
        f"{i18n.t('valchecker.profile.level', lang)} **{level}**",
        f"{(player.get('region') or '—').upper()}",
        f"Elo **{mmr['elo']}**" if mmr.get("elo") is not None else None,
    ]
    embed.add_field(
        name=i18n.t("valchecker.profile.account", lang),
        value="\n".join(x for x in acct_lines if x),
        inline=True,
    )

    if agg and agg.get("games"):
        embed.add_field(
            name=i18n.t("valchecker.profile.last_n", lang, n=agg["games"]),
            value=f"**{agg['wins']}W** · **{agg['losses']}L**\nWR **{stats.pct(agg['wr'])}**",
            inline=True,
        )
        embed.add_field(
            name=i18n.t("valchecker.profile.perf", lang),
            value=(
                f"KD **{agg['kd']:.2f}**\n"
                f"ACS **{agg['avgAcs']:.0f}**\n"
                f"HS **{stats.pct(agg['avgHs'])}**"
            ),
            inline=True,
        )
        top_agents = sorted(agg["agents"].items(), key=lambda x: x[1]["games"], reverse=True)[:3]
        top_maps = sorted(agg["maps"].items(), key=lambda x: x[1]["games"], reverse=True)[:3]
        if top_agents:
            embed.add_field(
                name=i18n.t("valchecker.profile.agents", lang),
                value="\n".join(
                    f"{name} · {s['games']}g · {stats.pct(stats.bucket_wr(s))}"
                    for name, s in top_agents
                ),
                inline=True,
            )
        if top_maps:
            embed.add_field(
                name=i18n.t("valchecker.profile.maps", lang),
                value="\n".join(
                    f"{name} · {s['games']}g · {stats.pct(stats.bucket_wr(s))}"
                    for name, s in top_maps
                ),
                inline=True,
            )
    else:
        embed.add_field(
            name=i18n.t("valchecker.profile.form", lang),
            value=i18n.t("valchecker.profile.no_recent", lang),
            inline=True,
        )

    if rank_icon:
        embed.set_thumbnail(url=rank_icon)
    card = None
    if account:
        c = account.get("card")
        if isinstance(c, dict):
            card = c.get("large") or c.get("small")
        elif isinstance(c, str):
            card = c
    if isinstance(card, str):
        embed.set_image(url=card)
    return embed


def profile_stats_embed(player, agg, count, summaries=None, lang: str = "en") -> discord.Embed:
    summaries = summaries or []
    dots = stats.form_strip_dots(summaries, 5)
    spaced = stats.form_strip_spaced(summaries, 5)
    embed = base_embed(color=COLORS["info"])
    embed.set_author(name=stats.riot_id(player["name"], player["tag"]))
    embed.title = i18n.t("valchecker.profile.stats_title", lang, n=agg.get("games") or count)
    if agg.get("games"):
        parts = [
            f"**{agg['wins']}W** · **{agg['losses']}L**  ·  WR **{stats.pct(agg['wr'])}**",
            dots if dots != "—" else None,
            f"`{spaced}`" if spaced != "—" else None,
        ]
        embed.description = "\n".join(x for x in parts if x)
        embed.add_field(
            name="KDA",
            value=f"`{agg['kills']}/{agg['deaths']}/{agg['assists']}`\nKD **{agg['kd']:.2f}**",
            inline=True,
        )
        embed.add_field(name="ACS", value=f"**{agg['avgAcs']:.0f}**", inline=True)
        embed.add_field(name="HS", value=f"**{stats.pct(agg['avgHs'])}**", inline=True)
    else:
        embed.description = i18n.t("valchecker.profile.no_window", lang)
    return embed


def profile_agents_embed(player, agg, filter_name=None, summaries=None, lang: str = "en") -> discord.Embed:
    summaries = summaries or []
    entries = sorted((agg.get("agents") or {}).items(), key=lambda x: x[1]["games"], reverse=True)
    if filter_name:
        entries = [e for e in entries if e[0].lower() == filter_name.lower()]
    dots = stats.form_strip_dots(summaries, 5)
    lines = [
        f"**{i + 1}.** {name} · {s['games']}g · {stats.pct(stats.bucket_wr(s))} · "
        f"KD {stats.kd(s['kills'], s['deaths'])} · ACS {(s['acs'] / s['games']):.0f}"
        for i, (name, s) in enumerate(entries[:12])
    ]
    title = (
        i18n.t("valchecker.profile.agent_title", lang, name=filter_name)
        if filter_name
        else i18n.t("valchecker.profile.agents_title", lang)
    )
    desc_parts = [f"{dots}\n" if dots != "—" else None, "\n".join(lines) or i18n.t("valchecker.profile.no_agents", lang)]
    embed = base_embed(color=COLORS["accent"])
    embed.set_author(name=stats.riot_id(player["name"], player["tag"]))
    embed.title = title
    embed.description = "\n".join(x for x in desc_parts if x)
    return embed


def profile_maps_embed(player, agg, filter_name=None, summaries=None, lang: str = "en") -> discord.Embed:
    summaries = summaries or []
    entries = sorted((agg.get("maps") or {}).items(), key=lambda x: x[1]["games"], reverse=True)
    if filter_name:
        entries = [e for e in entries if filter_name.lower() in e[0].lower()]
    dots = stats.form_strip_dots(summaries, 5)
    lines = [
        f"**{i + 1}.** {name} · {s['games']}g · {stats.pct(stats.bucket_wr(s))} · "
        f"KD {stats.kd(s['kills'], s['deaths'])} · ACS {(s['acs'] / s['games']):.0f}"
        for i, (name, s) in enumerate(entries[:12])
    ]
    title = (
        i18n.t("valchecker.profile.map_title", lang, name=filter_name)
        if filter_name
        else i18n.t("valchecker.profile.maps_title", lang)
    )
    desc_parts = [f"{dots}\n" if dots != "—" else None, "\n".join(lines) or i18n.t("valchecker.profile.no_maps", lang)]
    embed = base_embed(color=COLORS["info"])
    embed.set_author(name=stats.riot_id(player["name"], player["tag"]))
    embed.title = title
    embed.description = "\n".join(x for x in desc_parts if x)
    return embed


def history_embed(player, summaries, lang: str = "en") -> discord.Embed:
    lines = []
    for s in summaries:
        p = s.get("player")
        mark = "W" if s.get("won") is True else "L" if s.get("won") is False else "?"
        kda = f"{p['kills']}/{p['deaths']}/{p['assists']}" if p else "—"
        agent = (p or {}).get("agent") or "?"
        lines.append(
            f"**{mark}** · **{s.get('map')}** · {agent} · `{kda}` · {stats.ago(s.get('startedAt'), lang)}"
        )
    embed = base_embed(color=COLORS["dark"])
    embed.set_author(name=stats.riot_id(player["name"], player["tag"]))
    embed.title = i18n.t("valchecker.profile.history_title", lang)
    embed.description = "\n".join(lines) or i18n.t("valchecker.profile.no_matches", lang)
    return embed


def compare_embed(a, pa, b, pb, lang: str = "en") -> discord.Embed:
    def row(label, left, right):
        return {"name": label, "value": f"**{left}**\nvs\n**{right}**", "inline": True}

    embed = base_embed(color=COLORS["info"])
    embed.title = i18n.t("valchecker.compare.title", lang)
    embed.description = (
        f"**{stats.riot_id(a['name'], a['tag'])}**  vs  **{stats.riot_id(b['name'], b['tag'])}**"
    )
    for f in (
        row(
            i18n.t("valchecker.compare.rank", lang),
            f"{pa['mmr']['rank']}\n{pa['mmr']['rr']} RR",
            f"{pb['mmr']['rank']}\n{pb['mmr']['rr']} RR",
        ),
        row(i18n.t("valchecker.compare.winrate", lang), stats.pct(pa["agg"]["wr"]), stats.pct(pb["agg"]["wr"])),
        row("KD", f"{pa['agg']['kd']:.2f}", f"{pb['agg']['kd']:.2f}"),
        row("ACS", f"{pa['agg']['avgAcs']:.0f}", f"{pb['agg']['avgAcs']:.0f}"),
        row("HS%", stats.pct(pa["agg"]["avgHs"]), stats.pct(pb["agg"]["avgHs"])),
        row(
            i18n.t("valchecker.compare.sample", lang),
            f"{pa['agg']['games']}g",
            f"{pb['agg']['games']}g",
        ),
    ):
        embed.add_field(**f)
    return embed


def status_embed(region: str, fields: list[dict], lang: str = "en") -> discord.Embed:
    embed = base_embed(color=COLORS["info"], timestamp=True, footer=i18n.t("valchecker.common.live", lang))
    embed.title = i18n.t("valchecker.status.title", lang, region=region.upper())
    for f in fields:
        embed.add_field(name=f["name"], value=f["value"], inline=f.get("inline", False))
    return embed


def simple_embed(title: str, description: str, color: int | None = None) -> discord.Embed:
    embed = base_embed(color=color if color is not None else COLORS["dark"])
    embed.title = title
    embed.description = description
    return embed


def leaderboard_embed(guild_name: str, lines: list[str], sort_label: str, lang: str = "en") -> discord.Embed:
    embed = base_embed(color=COLORS["dark"], footer=sort_label)
    embed.title = i18n.t("valchecker.lb.title", lang, guild=guild_name)
    embed.description = "\n".join(lines) or i18n.t("valchecker.lb.empty", lang)
    return embed
