#!/usr/bin/env python3
"""Write sample Discord guild banner bytes and print metadata.

Usage (from repo root):
  python scripts/selftest_discord_banner.py
  python scripts/selftest_discord_banner.py --out /tmp
"""

from __future__ import annotations

import argparse
import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

import bot.cards.dynamic_banner as dynamic_banner# noqa: E402
from bot.cards.discord_banner_bytes import (  # noqa: E402
    BANNER_H,
    BANNER_W,
    describe_image_bytes,
    ensure_discord_banner_bytes,
    image_to_discord_jpeg,
    image_to_discord_png,
)


def _print(label: str, data: bytes, path: Path) -> None:
    path.write_bytes(data)
    meta = describe_image_bytes(data)
    print(f"=== {label} ===")
    print(f"  path={path}")
    for key, value in meta.items():
        print(f"  {key}={value}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    out = args.out or (Path(tempfile.gettempdir()) / "cheterin_banner_selftest")
    out.mkdir(parents=True, exist_ok=True)

    solid = Image.new("RGB", (BANNER_W, BANNER_H), (40, 10, 18))
    _print("solid_png", image_to_discord_png(solid), out / "solid_960x540.png")
    _print("solid_jpeg", image_to_discord_jpeg(solid), out / "solid_960x540.jpg")

    buf = io.BytesIO()
    Image.new("RGBA", (1920, 1080), (200, 40, 80, 180)).save(buf, format="PNG")
    _print("ensure_png", ensure_discord_banner_bytes(buf.getvalue(), prefer="png"), out / "ensure.png")
    _print("ensure_jpeg", ensure_discord_banner_bytes(buf.getvalue(), prefer="jpeg"), out / "ensure.jpg")

    dynamic = dynamic_banner.render_dynamic_banner(
        display_name="SelfTest",
        avatar_bytes=None,
        member_count=1337,
        voice_count=4,
        guild_name="Cheterin",
        lang="ru",
    )
    _print("dynamic", dynamic, out / "dynamic_banner.png")
    print(f"OK — samples written under {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
