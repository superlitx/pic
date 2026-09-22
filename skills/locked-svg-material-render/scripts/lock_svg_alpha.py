#!/usr/bin/env python3
"""Replace a material plate's geometry with an authoritative SVG alpha mask."""

import argparse
from pathlib import Path

from PIL import Image, ImageColor


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--material", required=True, type=Path)
    parser.add_argument("--mask", required=True, type=Path)
    parser.add_argument("--output-transparent", required=True, type=Path)
    parser.add_argument("--output-background", type=Path)
    parser.add_argument("--fallback-color", default="#F85218")
    parser.add_argument("--background-color", default="#FFFFFF")
    return parser.parse_args()


def rgba_color(value: str) -> tuple[int, int, int, int]:
    rgb = ImageColor.getrgb(value)
    return (rgb[0], rgb[1], rgb[2], 255)


def main() -> None:
    args = parse_args()
    material = Image.open(args.material).convert("RGBA")
    mask = Image.open(args.mask).convert("L")
    if material.size != mask.size:
        raise SystemExit(
            f"FAIL: material canvas {material.size} != mask canvas {mask.size}; "
            "resize explicitly before geometry locking"
        )

    fallback = Image.new("RGBA", mask.size, rgba_color(args.fallback_color))
    rgb_plate = Image.alpha_composite(fallback, material)
    rgb_plate.putalpha(mask)

    args.output_transparent.parent.mkdir(parents=True, exist_ok=True)
    rgb_plate.save(args.output_transparent)

    if args.output_background:
        background = Image.new("RGBA", mask.size, rgba_color(args.background_color))
        background.alpha_composite(rgb_plate)
        args.output_background.parent.mkdir(parents=True, exist_ok=True)
        background.convert("RGB").save(args.output_background)

    if rgb_plate.getchannel("A").tobytes() != mask.tobytes():
        raise SystemExit("FAIL: output alpha is not byte-identical to mask")
    print("PASS: output alpha is byte-identical to mask")


if __name__ == "__main__":
    main()

