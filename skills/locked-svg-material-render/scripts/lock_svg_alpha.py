#!/usr/bin/env python3
"""Apply coverage to an eligible plate. This operation does NOT fix RGB geometry."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageColor
from color_management import convert_srgb


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--material", required=True, type=Path)
    parser.add_argument("--mask", required=True, type=Path)
    parser.add_argument("--output-transparent", required=True, type=Path)
    parser.add_argument("--output-background", type=Path)
    parser.add_argument("--fallback-color", default="#F85218")
    parser.add_argument("--background-color", default="#FFFFFF")
    parser.add_argument("--source-svg", required=True, type=Path)
    parser.add_argument("--provenance", required=True, type=Path, help="Locally authored plate origin record, bound to source SVG and material hashes")
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--assume-srgb", action="store_true")
    return parser.parse_args()


def rgba_color(value: str) -> tuple[int, int, int, int]:
    rgb = ImageColor.getrgb(value)
    return (rgb[0], rgb[1], rgb[2], 255)


def main() -> None:
    args = parse_args()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    provenance = json.loads(args.provenance.read_text())
    if provenance.get('kind') not in {'boundary_free_material', 'source_geometry_render'}:
        raise SystemExit('BLOCKED: full-logo generations, registration proposals and warped RGB plates cannot be alpha-locked into valid geometry')
    if provenance.get('material_sha256') != sha(args.material) or provenance.get('source_svg_sha256') != sha(args.source_svg):
        raise SystemExit('BLOCKED: stale or unrelated material provenance')
    if not provenance.get('notes'):
        raise SystemExit('BLOCKED: describe verified plate origin; metadata cannot authenticate it automatically')
    material, icc, color = convert_srgb(Image.open(args.material), args.assume_srgb)
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
    rgb_plate.save(args.output_transparent, icc_profile=icc)

    if args.output_background:
        background = Image.new("RGBA", mask.size, rgba_color(args.background_color))
        background.alpha_composite(rgb_plate)
        args.output_background.parent.mkdir(parents=True, exist_ok=True)
        background.convert("RGB").save(args.output_background, icc_profile=icc)

    if rgb_plate.getchannel("A").tobytes() != mask.tobytes():
        raise SystemExit("FAIL: output alpha is not byte-identical to mask")
    report = {'status': 'ALPHA_ONLY_PASS', 'delivery_ready': False,
              'visible_edges': 'NOT_EVALUATED', 'material': 'NOT_EVALUATED',
              'scope': 'coverage diagnostic; not final geometry validation',
              'source_svg_sha256': sha(args.source_svg), 'mask_sha256': sha(args.mask),
              'input_sha256': sha(args.material), 'frontface_sha256': sha(args.output_transparent),
              'provenance_sha256': sha(args.provenance), 'color': color}
    if args.output_background:
        report.update(final=str(args.output_background), final_sha256=sha(args.output_background))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print('ALPHA_ONLY_PASS; visible RGB geometry and material are unvalidated; delivery_ready=false')


if __name__ == "__main__":
    main()
