#!/usr/bin/env python3
"""Register an approved full-image reference to the locked Matters front face.

This script never repaints or regenerates the source. It applies one affine
transform to the complete image, preserves permitted depth/effect overflow,
and creates an exact-alpha front-face proof plus an opaque overlay.
"""

from __future__ import annotations

import argparse
import hashlib
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageCms


BUNDLE = Path(__file__).resolve().parents[1]
REPO = BUNDLE.parents[1]
DEFAULT_MASK = BUNDLE / "assets/matters-svg-exact-mask.png"
DEFAULT_SVG = BUNDLE / "assets/matters.svg"
SRGB_PROFILE = BUNDLE / "assets/sRGB.icc"
VERIFIER = REPO / "skills/locked-svg-material-render/scripts/verify_locked_render.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--mask", type=Path, default=DEFAULT_MASK)
    parser.add_argument("--svg", type=Path, default=DEFAULT_SVG)
    parser.add_argument("--output-dir", type=Path, default=BUNDLE / "outputs")
    parser.add_argument("--proof-dir", type=Path, default=BUNDLE / "proofs")
    parser.add_argument("--support-kernel", type=int, default=111)
    parser.add_argument("--erode-kernel", type=int, default=61)
    parser.add_argument("--highres", type=int, default=0)
    return parser.parse_args()


def contour(mask: np.ndarray, width: int = 2) -> np.ndarray:
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (width * 2 + 1, width * 2 + 1)
    )
    return cv2.subtract(cv2.dilate(mask, kernel), cv2.erode(mask, kernel))


def bbox(mask: np.ndarray) -> tuple[int, int, int, int]:
    ys, xs = np.where(mask > 0)
    return int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)


def fill_outer(mark: np.ndarray) -> np.ndarray:
    flood = cv2.copyMakeBorder(mark, 1, 1, 1, 1, cv2.BORDER_CONSTANT, value=0)
    cv2.floodFill(flood, None, (0, 0), 255)
    return cv2.bitwise_or(mark, cv2.bitwise_not(flood)[1:-1, 1:-1])


def segment_outer(
    image: np.ndarray,
    exact_outer: np.ndarray,
    support_kernel: int,
    erode_kernel: int,
) -> np.ndarray:
    labels = np.full(exact_outer.shape, cv2.GC_BGD, dtype=np.uint8)
    support = cv2.dilate(
        exact_outer,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (support_kernel, support_kernel)),
    ) > 0
    certain_fg = cv2.erode(
        exact_outer,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (erode_kernel, erode_kernel)),
    ) > 0
    labels[support] = cv2.GC_PR_BGD
    labels[exact_outer > 0] = cv2.GC_PR_FGD
    labels[certain_fg] = cv2.GC_FGD

    bg_model = np.zeros((1, 65), np.float64)
    fg_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(image, labels, None, bg_model, fg_model, 7, cv2.GC_INIT_WITH_MASK)
    selected = np.uint8(
        (labels == cv2.GC_FGD) | (labels == cv2.GC_PR_FGD)
    ) * 255
    count, components, stats, _ = cv2.connectedComponentsWithStats(selected, 8)
    center_label = int(components[512, 512])
    if center_label == 0:
        center_label = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return fill_outer(np.uint8(components == center_label) * 255)


def to_srgb(source: Image.Image) -> tuple[Image.Image, bytes, str]:
    srgb = ImageCms.ImageCmsProfile(str(SRGB_PROFILE))
    embedded = source.info.get("icc_profile")
    if embedded:
        profile = ImageCms.ImageCmsProfile(BytesIO(embedded))
        name = ImageCms.getProfileDescription(profile).strip()
        converted = ImageCms.profileToProfile(
            source.convert("RGB"),
            profile,
            srgb,
            outputMode="RGB",
            renderingIntent=0,
        )
        return converted, srgb.tobytes(), f"{name} -> sRGB"
    return source.convert("RGB"), srgb.tobytes(), "untagged/sRGB-chunk -> embedded sRGB"


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.proof_dir.mkdir(parents=True, exist_ok=True)

    source_image = Image.open(args.source)
    source_srgb, export_icc, color_conversion = to_srgb(source_image)
    source = np.array(source_srgb, dtype=np.uint8)
    preview = cv2.resize(source, (1024, 1024), interpolation=cv2.INTER_AREA)

    exact = np.array(Image.open(args.mask).convert("L"), dtype=np.uint8)
    exact_binary = np.uint8(exact >= 128) * 255
    exact_outer = fill_outer(exact_binary)
    source_outer = segment_outer(
        preview, exact_outer, args.support_kernel, args.erode_kernel
    )
    sx0, sy0, sx1, sy1 = bbox(source_outer)
    scale_x = 768.0 / (sx1 - sx0)
    scale_y = 768.0 / (sy1 - sy0)
    matrix_1024 = np.array(
        [
            [scale_x, 0.0, 128.0 - sx0 * scale_x],
            [0.0, scale_y, 128.0 - sy0 * scale_y],
        ],
        dtype=np.float32,
    )

    input_matrix = matrix_1024.copy()
    input_matrix[0, 0] *= 1024.0 / source.shape[1]
    input_matrix[1, 1] *= 1024.0 / source.shape[0]
    final = cv2.warpAffine(
        source,
        input_matrix,
        (1024, 1024),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_REFLECT_101,
    )
    registered_outer = cv2.warpAffine(
        source_outer,
        matrix_1024,
        (1024, 1024),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
    )

    final_path = args.output_dir / f"{args.slug}-final-1024.png"
    Image.fromarray(final, "RGB").save(final_path, icc_profile=export_icc)
    high_path = None
    if args.highres:
        high_matrix = matrix_1024.copy()
        high_matrix[0, 0] *= args.highres / source.shape[1]
        high_matrix[1, 1] *= args.highres / source.shape[0]
        high_matrix[:, 2] *= args.highres / 1024.0
        high = cv2.warpAffine(
            source,
            high_matrix,
            (args.highres, args.highres),
            flags=cv2.INTER_LANCZOS4,
            borderMode=cv2.BORDER_REFLECT_101,
        )
        high_path = args.output_dir / f"{args.slug}-final-{args.highres}.png"
        Image.fromarray(high, "RGB").save(high_path, icc_profile=export_icc)

    overlay = final.copy()
    overlay[contour(registered_outer, 1) > 0] = (255, 210, 0)
    overlay[contour(exact_outer, 2) > 0] = (0, 190, 255)
    overlay[contour(exact_binary, 1) > 0] = (255, 20, 85)
    overlay_path = args.proof_dir / f"{args.slug}-model-overlay.png"
    Image.fromarray(overlay, "RGB").save(overlay_path, icc_profile=export_icc)

    frontface_path = args.proof_dir / f"{args.slug}-frontface-pass.png"
    Image.fromarray(np.dstack([final, exact]), "RGBA").save(
        frontface_path, icc_profile=export_icc
    )
    alpha_report_path = args.proof_dir / f"{args.slug}-frontface-alpha-validation.json"
    subprocess.run(
        [
            sys.executable,
            str(VERIFIER),
            "--mask",
            str(args.mask),
            "--candidate",
            str(frontface_path),
            "--report",
            str(alpha_report_path),
        ],
        check=True,
    )
    alpha_report = json.loads(alpha_report_path.read_text())
    intersection = np.count_nonzero((registered_outer > 0) & (exact_outer > 0))
    union = np.count_nonzero((registered_outer > 0) | (exact_outer > 0))

    report = {
        "geometry_authority": str(args.svg),
        "appearance_authority": str(args.source),
        "method": "one whole-image affine registration; no repainting, inpainting, feature relocation, or material regeneration",
        "color_conversion": color_conversion,
        "source_outer_bbox_1024": [sx0, sy0, sx1, sy1],
        "target_front_face_bbox_1024": [128, 128, 896, 896],
        "affine_matrix_1024": matrix_1024.tolist(),
        "registered_outer_bbox_1024": list(bbox(registered_outer)),
        "outer_mask_iou": float(intersection / union),
        "front_face_alpha_verdict": alpha_report.get("status"),
        "front_face_alpha_differing_pixels": alpha_report.get(
            "differing_alpha_pixels"
        ),
        "allowed_overflow": "side thickness, bevel, material grains, contact shadow, and background",
        "final": final_path.name,
        "final_sha256": hashlib.sha256(final_path.read_bytes()).hexdigest(),
        "highres_final": high_path.name if high_path else None,
        "overlay": overlay_path.name,
    }
    report_path = args.proof_dir / f"{args.slug}-registration-report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
