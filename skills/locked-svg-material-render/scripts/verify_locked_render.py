#!/usr/bin/env python3
"""Verify that a transparent render preserves an authoritative mask exactly."""

import argparse
import json
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mask", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--threshold", type=int, default=128)
    return parser.parse_args()


def bbox(binary: np.ndarray) -> list[int] | None:
    ys, xs = np.where(binary)
    if not len(xs):
        return None
    return [int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1)]


def components(binary: np.ndarray) -> list[dict]:
    height, width = binary.shape
    seen = np.zeros_like(binary, dtype=bool)
    result = []
    for start_y, start_x in zip(*np.where(binary)):
        if seen[start_y, start_x]:
            continue
        queue = deque([(int(start_y), int(start_x))])
        seen[start_y, start_x] = True
        count = 0
        sum_x = 0
        sum_y = 0
        min_x = max_x = int(start_x)
        min_y = max_y = int(start_y)
        while queue:
            y, x = queue.popleft()
            count += 1
            sum_x += x
            sum_y += y
            min_x = min(min_x, x)
            max_x = max(max_x, x)
            min_y = min(min_y, y)
            max_y = max(max_y, y)
            for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if (
                    0 <= ny < height
                    and 0 <= nx < width
                    and binary[ny, nx]
                    and not seen[ny, nx]
                ):
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        result.append(
            {
                "area": count,
                "bbox": [min_x, min_y, max_x + 1, max_y + 1],
                "centroid": [sum_x / count, sum_y / count],
            }
        )
    return sorted(result, key=lambda item: item["area"], reverse=True)


def main() -> None:
    args = parse_args()
    reference_image = Image.open(args.mask).convert("L")
    candidate_image = Image.open(args.candidate).convert("RGBA")
    same_size = reference_image.size == candidate_image.size

    report = {
        "status": "FAIL",
        "mask": str(args.mask),
        "candidate": str(args.candidate),
        "reference_size": list(reference_image.size),
        "candidate_size": list(candidate_image.size),
        "same_size": same_size,
    }

    if same_size:
        reference = np.asarray(reference_image, dtype=np.int16)
        candidate = np.asarray(candidate_image.getchannel("A"), dtype=np.int16)
        delta = np.abs(reference - candidate)
        reference_binary = reference >= args.threshold
        candidate_binary = candidate >= args.threshold
        alpha_equal = bool(np.array_equal(reference, candidate))
        report.update(
            {
                "alpha_byte_equal": alpha_equal,
                "differing_alpha_pixels": int(np.count_nonzero(delta)),
                "max_alpha_delta": int(delta.max()),
                "reference_bbox": bbox(reference_binary),
                "candidate_bbox": bbox(candidate_binary),
                "reference_components": components(reference_binary),
                "candidate_components": components(candidate_binary),
            }
        )
        if alpha_equal:
            report["status"] = "PASS"

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if report["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
