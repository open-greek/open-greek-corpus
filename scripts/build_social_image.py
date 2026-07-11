#!/usr/bin/env python3
"""Build the GitHub social preview image.

Composes the Open Greek badge (assets/social/og_badge.png, rendered from the
seeded og_badge.svg) with the project title and tagline on a paper-tone field.
Upload the output at the repo's Settings -> Social preview.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BADGE = ROOT / "assets" / "social" / "og_badge.png"
DEFAULT_FONT = ROOT / "assets" / "fonts" / "NotoSansDisplay-wdth-wght.ttf"
DEFAULT_OUTPUT = ROOT / "assets" / "social" / "github-social.png"
TARGET_SIZE = (1280, 640)
TITLE = "Open Greek Corpus"
TAGLINE = "State-of-the-art OCR of public domain Greek texts"
MAX_BYTES = 1_000_000

# Palette of the org logo (see og_badge.svg header comment).
BACKGROUND = (247, 240, 227)  # warm paper
TITLE_COLOR = (62, 58, 117)  # navy #3E3A75
TAGLINE_COLOR = (180, 55, 43)  # brick #B4372B


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--badge", type=Path, default=DEFAULT_BADGE)
    parser.add_argument("--font", type=Path, default=DEFAULT_FONT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-bytes", type=int, default=MAX_BYTES)
    return parser.parse_args()


def load_font(path: Path, size: int, weight: int) -> ImageFont.FreeTypeFont:
    """Load the variable font at a given wght; the logo glyphs use wght=700."""
    font = ImageFont.truetype(str(path), size=size)
    try:
        axes = font.get_variation_axes()
    except OSError:  # static font, no variations
        return font
    values = [
        weight if bytes(axis["name"]).rstrip(b"\x00") == b"Weight" else axis["default"]
        for axis in axes
    ]
    font.set_variation_by_axes(values)
    return font


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    path: Path,
    weight: int,
    max_width: int,
    max_size: int,
) -> ImageFont.FreeTypeFont:
    """Largest font size (descending from max_size) whose text fits max_width."""
    for size in range(max_size, 15, -1):
        font = load_font(path, size, weight)
        if draw.textlength(text, font=font) <= max_width:
            return font
    return load_font(path, 16, weight)


def main() -> None:
    args = parse_args()
    image = Image.new("RGB", TARGET_SIZE, BACKGROUND)

    badge = Image.open(args.badge).convert("RGBA")
    badge_size = 344
    badge_x = 88
    badge = badge.resize((badge_size, badge_size), Image.Resampling.LANCZOS)
    image.paste(badge, (badge_x, (TARGET_SIZE[1] - badge_size) // 2), badge)

    draw = ImageDraw.Draw(image)
    text_x = badge_x + badge_size + 56
    max_width = TARGET_SIZE[0] - 88 - text_x
    title_font = fit_font(draw, TITLE, args.font, 700, max_width, max_size=88)
    tagline_font = fit_font(draw, TAGLINE, args.font, 500, max_width, max_size=40)

    title_box = draw.textbbox((0, 0), TITLE, font=title_font)
    tagline_box = draw.textbbox((0, 0), TAGLINE, font=tagline_font)
    gap = 36
    block_h = (title_box[3] - title_box[1]) + gap + (tagline_box[3] - tagline_box[1])
    title_y = (TARGET_SIZE[1] - block_h) // 2 - title_box[1]
    draw.text((text_x, title_y), TITLE, font=title_font, fill=TITLE_COLOR)
    tagline_y = title_y + title_box[1] + (title_box[3] - title_box[1]) + gap - tagline_box[1]
    draw.text((text_x, tagline_y), TAGLINE, font=tagline_font, fill=TAGLINE_COLOR)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output, optimize=True)

    size = args.output.stat().st_size
    if size > args.max_bytes:
        raise SystemExit(
            f"{args.output} is {size:,} bytes, above --max-bytes={args.max_bytes:,}"
        )
    print(f"Wrote {args.output} ({TARGET_SIZE[0]}x{TARGET_SIZE[1]}, {size:,} bytes)")


if __name__ == "__main__":
    main()
