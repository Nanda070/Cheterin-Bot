"""One-shot filesystem reorg: flat root *.py -> bot/ packages + import rewrite.

Inspired by VALORANT/scripts/_reorg_bot.py (layout pattern, not a 1:1 copy).

Run from repo root:  python scripts/_reorg_bot.py
Safe to re-run only if source files still exist at old locations.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# basename (without .py) -> package-relative dotted path under bot.
MAP: dict[str, str] = {}


def _add(pkg: str, *names: str) -> None:
    for name in names:
        MAP[name] = f"bot.{pkg}.{name}" if pkg else f"bot.{name}"


# bot/config.py  (was bot_config.py)
MAP["bot_config"] = "bot.config"

_add(
    "core",
    "settings_db",
    "settings_migration",
    "embed_style",
    "embed_builder",
    "i18n",
    "slash_i18n",
    "slash_modules",
    "slash_registry",
    "language_core",
    "timezone_core",
    "message_template_core",
    "preview_core",
    "bot_profile_core",
    "moderation_embed_core",
    "moderation_log",
    "case_timeline_core",
    "stats_db",
    "feedback_categories",
    "components_v2",
)

_add(
    "cards",
    "profile_card",
    "quote_card",
    "xp_card",
    "wordle_card",
    "customs_winner_card",
    "discord_banner_bytes",
    "dynamic_banner",
)

_add(
    "data",
    "bunker_data",
    "bunker_data_en",
    "wordle_data",
)

_add(
    "modules.valorant",
    "premier",
    "valorant_panels",
    "ideas",
    "ideas_core",
    "customs",
    "customs_core",
    "valchecker",
    "valchecker_core",
    "valchecker_db",
    "valchecker_embeds",
    "valchecker_henrik",
    "valchecker_stats",
    "valchecker_valorant_api",
    "valorant_features_core",
    "valorant_maps",
    "valorant_random",
)

_add(
    "modules.voice",
    "voice_rooms",
    "voice_db",
    "voice_logs",
    "voice_tracker",
)

_add(
    "modules.levels",
    "xp",
    "xp_core",
)

_add(
    "modules.feedback",
    "feedback_menu",
    "feedback_core",
    "feedback_panel_core",
)

_add(
    "modules.moderation",
    "antiraid",
    "antiraid_core",
    "automod",
    "automod_core",
    "spam",
    "spam_core",
    "lockdown",
    "lockdown_core",
    "tempban",
    "tempban_core",
    "moderation_commands",
    "moderation_commands_core",
    "serverlog",
    "warns_core",
    "warns_db",
    "ban_db",
    "verification",
    "verification_core",
    "verification_db",
)

_add(
    "modules.community",
    "welcome",
    "welcome_core",
    "invites",
    "invites_core",
    "invites_db",
    "reaction_roles",
    "timed_roles",
    "timed_roles_db",
    "sticky",
    "sticky_core",
    "sticky_roles_core",
    "polls",
    "polls_db",
    "giveaways",
    "giveaway_core",
    "events",
    "events_core",
    "news",
    "daily_topic",
    "daily_topic_core",
    "streams",
    "auto_reactions",
    "auto_reactions_core",
    "scheduled_messages",
    "scheduled_messages_core",
    "starboard",
    "starboard_core",
    "starboard_db",
    "birthdays",
    "birthdays_core",
    "birthdays_db",
    "banner_rotation",
    "banner_rotation_core",
)

_add(
    "modules.utility",
    "button",
    "help_cog",
    "owner_alerts",
    "owner_alerts_core",
    "memobb",
    "quote",
    "quote_core",
    "custom_commands",
    "custom_commands_core",
)

_add(
    "modules.games",
    "fun",
    "fun_core",
    "wordle",
    "wordle_core",
    "wordle_db",
    "mafia",
    "mafia_core",
    "mafia_db",
    "bunker",
    "bunker_core",
    "bunker_db",
    "bunker_localize",
    "casino",
    "casino_core",
    "casino_db",
    "blackjack",
    "blackjack_core",
    "economy",
    "economy_core",
    "economy_db",
    "relations",
    "relations_core",
    "relations_db",
    "family_core",
    "family_db",
    "family_birthdays",
    "family_roster",
    "family_tickets",
    "supply",
    "supply_core",
    "brackets",
    "game_test_lobby",
)

SKIP_ROOT = {"main", "test_memobb_ctd"}


def target_path(dotted: str) -> Path:
    parts = dotted.split(".")
    return ROOT.joinpath(*parts).with_suffix(".py")


def ensure_packages(dotted: str) -> None:
    parts = dotted.split(".")
    for i in range(1, len(parts)):
        pkg_dir = ROOT.joinpath(*parts[:i])
        pkg_dir.mkdir(parents=True, exist_ok=True)
        init = pkg_dir / "__init__.py"
        if not init.exists():
            init.write_text('"""Package."""\n', encoding="utf-8")


def move_files() -> list[tuple[str, str]]:
    moved: list[tuple[str, str]] = []
    src_config = ROOT / "bot_config.py"
    if src_config.exists():
        ensure_packages("bot.config")
        dst = ROOT / "bot" / "config.py"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_config), str(dst))
        moved.append(("bot_config.py", "bot/config.py"))

    for old_name, dotted in sorted(MAP.items()):
        if old_name == "bot_config":
            continue
        src = ROOT / f"{old_name}.py"
        if not src.exists():
            continue
        ensure_packages(dotted)
        dst = target_path(dotted)
        if dst.exists():
            print(f"SKIP exists: {dst.relative_to(ROOT)}")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        moved.append((f"{old_name}.py", str(dst.relative_to(ROOT))))

    test_src = ROOT / "test_memobb_ctd.py"
    if test_src.exists():
        tests_dir = ROOT / "tests"
        tests_dir.mkdir(exist_ok=True)
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")
        shutil.move(str(test_src), str(tests_dir / "test_memobb_ctd.py"))
        moved.append(("test_memobb_ctd.py", "tests/test_memobb_ctd.py"))

    return moved


SORTED_NAMES = sorted(MAP.keys(), key=len, reverse=True)


def rewrite_imports_in_text(text: str) -> str:
    def repl_import(m: re.Match) -> str:
        indent, names, rest = m.group(1), m.group(2), m.group(3)
        parts = [p.strip() for p in names.split(",")]
        lines = []
        for part in parts:
            if " as " in part:
                mod, alias = part.split(" as ", 1)
                mod, alias = mod.strip(), alias.strip()
            else:
                mod, alias = part.strip(), None
            if mod in MAP:
                dotted = MAP[mod]
                if alias:
                    lines.append(f"{indent}import {dotted} as {alias}")
                else:
                    lines.append(f"{indent}import {dotted} as {mod}")
            else:
                if alias:
                    lines.append(f"{indent}import {mod} as {alias}")
                else:
                    lines.append(f"{indent}import {mod}")
        if rest.strip() and lines:
            lines[-1] = lines[-1] + rest
        return "\n".join(lines)

    text = re.sub(
        r"^([ \t]*)import ([a-zA-Z0-9_., ]+)(.*)$",
        repl_import,
        text,
        flags=re.MULTILINE,
    )

    def repl_from(m: re.Match) -> str:
        indent, mod, rest = m.group(1), m.group(2), m.group(3)
        if mod in MAP:
            return f"{indent}from {MAP[mod]} import{rest}"
        return m.group(0)

    text = re.sub(
        r"^([ \t]*)from ([a-zA-Z0-9_]+) import(.*)$",
        repl_from,
        text,
        flags=re.MULTILINE,
    )

    def repl_ext(m: re.Match) -> str:
        quote, name = m.group(1), m.group(2)
        if name in MAP:
            return f"load_extension({quote}{MAP[name]}{quote}"
        return m.group(0)

    text = re.sub(r"load_extension\((['\"])([a-zA-Z0-9_]+)\1", repl_ext, text)

    return text


def fix_asset_roots() -> None:
    """Point asset paths at repo root after moves into bot/."""
    maps = ROOT / "bot" / "modules" / "valorant" / "valorant_maps.py"
    if maps.exists():
        text = maps.read_text(encoding="utf-8")
        old = "REPO_ROOT = Path(__file__).resolve().parent"
        new = "REPO_ROOT = Path(__file__).resolve().parents[3]  # bot/modules/valorant -> repo root"
        if old in text:
            maps.write_text(text.replace(old, new, 1), encoding="utf-8")
            print(f"Fixed asset root: {maps.relative_to(ROOT)}")
        else:
            print(f"WARN pattern not found in {maps.relative_to(ROOT)}")


def rewrite_all_py() -> int:
    count = 0
    for path in ROOT.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if path.name == "_reorg_bot.py":
            continue
        if "node_modules" in path.parts or ".venv" in path.parts or "venv" in path.parts:
            continue
        if "lookup-api" in path.parts and path.parts[-2:] == ("lookup-api", "app.py"):
            # Lookup stays isolated — no bot imports expected; still safe to scan
            pass
        original = path.read_text(encoding="utf-8")
        updated = rewrite_imports_in_text(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            count += 1
    return count


def write_thin_main() -> None:
    main = ROOT / "main.py"
    if not main.exists():
        return
    text = main.read_text(encoding="utf-8")
    if "Cheterin bot entrypoint" not in text:
        header = (
            '"""Cheterin bot entrypoint — Discord bot + embedded dashboard API."""\n\n'
        )
        text = header + text
        main.write_text(text, encoding="utf-8")


def verify_unmapped_root() -> list[str]:
    leftover = []
    for p in ROOT.glob("*.py"):
        if p.stem in SKIP_ROOT:
            continue
        if p.stem in MAP or p.name == "bot_config.py":
            leftover.append(p.name)
        else:
            leftover.append(p.name)
    return leftover


def main() -> None:
    print("=== Moving files ===")
    moved = move_files()
    for a, b in moved:
        print(f"  {a} -> {b}")
    print(f"Moved {len(moved)} entries")

    leftover = verify_unmapped_root()
    if leftover:
        print("UNMAPPED still at root:", leftover)

    print("=== Rewriting imports ===")
    n = rewrite_all_py()
    print(f"Updated {n} files")

    print("=== Fixing asset roots ===")
    fix_asset_roots()
    write_thin_main()

    print("=== Done ===")


if __name__ == "__main__":
    main()
