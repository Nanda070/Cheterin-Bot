"""Standard VALORANT plant/defuse maps and splash images.

Images live in ``assets/maps/`` (downloaded from valorant-api.com / Riot CDN).
If a local file is missing, the public splash URL is used as a fallback.
"""

from __future__ import annotations

import random
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
MAPS_DIR = REPO_ROOT / "assets" / "maps"

# Standard / custom plant-defuse pool (tacticalDescription set on valorant-api.com).
# TDM / Range / Skirmish maps are excluded.
MAPS: tuple[dict[str, str], ...] = (
    {
        "id": "abyss",
        "name": "Abyss",
        "uuid": "224b0a95-48b9-f703-1bd8-67aca101a61f",
        "splash_url": "https://media.valorant-api.com/maps/224b0a95-48b9-f703-1bd8-67aca101a61f/splash.png",
    },
    {
        "id": "ascent",
        "name": "Ascent",
        "uuid": "7eaecc1b-4337-bbf6-6ab9-04b8f06b3319",
        "splash_url": "https://media.valorant-api.com/maps/7eaecc1b-4337-bbf6-6ab9-04b8f06b3319/splash.png",
    },
    {
        "id": "bind",
        "name": "Bind",
        "uuid": "2c9d57ec-4431-9c5e-2939-8f9ef6dd5cba",
        "splash_url": "https://media.valorant-api.com/maps/2c9d57ec-4431-9c5e-2939-8f9ef6dd5cba/splash.png",
    },
    {
        "id": "breeze",
        "name": "Breeze",
        "uuid": "2fb9a4fd-47b8-4e7d-a969-74b4046ebd53",
        "splash_url": "https://media.valorant-api.com/maps/2fb9a4fd-47b8-4e7d-a969-74b4046ebd53/splash.png",
    },
    {
        "id": "corrode",
        "name": "Corrode",
        "uuid": "1c18ab1f-420d-0d8b-71d0-77ad3c439115",
        "splash_url": "https://media.valorant-api.com/maps/1c18ab1f-420d-0d8b-71d0-77ad3c439115/splash.png",
    },
    {
        "id": "fracture",
        "name": "Fracture",
        "uuid": "b529448b-4d60-346e-e89e-00a4c527a405",
        "splash_url": "https://media.valorant-api.com/maps/b529448b-4d60-346e-e89e-00a4c527a405/splash.png",
    },
    {
        "id": "haven",
        "name": "Haven",
        "uuid": "2bee0dc9-4ffe-519b-1cbd-7fbe763a6047",
        "splash_url": "https://media.valorant-api.com/maps/2bee0dc9-4ffe-519b-1cbd-7fbe763a6047/splash.png",
    },
    {
        "id": "icebox",
        "name": "Icebox",
        "uuid": "e2ad5c54-4114-a870-9641-8ea21279579a",
        "splash_url": "https://media.valorant-api.com/maps/e2ad5c54-4114-a870-9641-8ea21279579a/splash.png",
    },
    {
        "id": "lotus",
        "name": "Lotus",
        "uuid": "2fe4ed3a-450a-948b-6d6b-e89a78e680a9",
        "splash_url": "https://media.valorant-api.com/maps/2fe4ed3a-450a-948b-6d6b-e89a78e680a9/splash.png",
    },
    {
        "id": "pearl",
        "name": "Pearl",
        "uuid": "fd267378-4d1d-484f-ff52-77821ed10dc2",
        "splash_url": "https://media.valorant-api.com/maps/fd267378-4d1d-484f-ff52-77821ed10dc2/splash.png",
    },
    {
        "id": "split",
        "name": "Split",
        "uuid": "d960549e-485c-e861-8d71-aa9d1aed12a2",
        "splash_url": "https://media.valorant-api.com/maps/d960549e-485c-e861-8d71-aa9d1aed12a2/splash.png",
    },
    {
        "id": "summit",
        "name": "Summit",
        "uuid": "756da597-416b-c0f2-f47b-afbdf28670bc",
        "splash_url": "https://media.valorant-api.com/maps/756da597-416b-c0f2-f47b-afbdf28670bc/splash.png",
    },
    {
        "id": "sunset",
        "name": "Sunset",
        "uuid": "92584fbe-486a-b1b2-9faa-39b0f486b498",
        "splash_url": "https://media.valorant-api.com/maps/92584fbe-486a-b1b2-9faa-39b0f486b498/splash.png",
    },
)


def local_image(map_info: dict[str, str]) -> Path | None:
    """Return the first existing local splash (png or jpg)."""
    slug = map_info["id"]
    for suffix in (".jpg", ".png", ".webp"):
        path = MAPS_DIR / f"{slug}{suffix}"
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def pick_random() -> dict[str, str]:
    return random.choice(MAPS)


def embed_image(map_info: dict[str, str]) -> tuple[Path | None, str]:
    """``(local_path_or_None, embed_image_url)`` — attachment:// or CDN splash."""
    path = local_image(map_info)
    if path is not None:
        return path, f"attachment://{path.name}"
    return None, map_info["splash_url"]
