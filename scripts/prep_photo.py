#!/usr/bin/env python3
"""Prepare a square GitHub avatar for readable terminal-style ASCII rendering."""
import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prepare(source: Path, destination: Path) -> None:
    with Image.open(source) as image:
        rgba = image.convert("RGBA")
        cutout = remove(rgba)
        rgba = cutout.convert("RGBA")

    pixels = np.asarray(rgba)
    alpha = pixels[:, :, 3]
    ys, xs = np.where(alpha > 12)
    if len(xs):
        x0, x1 = int(xs.min()), int(xs.max()) + 1
        y0, y1 = int(ys.min()), int(ys.max()) + 1
        # Keep a little breathing room around the foreground subject.
        margin = max(8, int(max(x1 - x0, y1 - y0) * 0.055))
        x0, y0 = max(0, x0 - margin), max(0, y0 - margin)
        x1, y1 = min(rgba.width, x1 + margin), min(rgba.height, y1 + margin)
        rgba = rgba.crop((x0, y0, x1, y1))

    # Center the subject in a square canvas so the character portrait is balanced.
    side = max(rgba.width, rgba.height)
    square = Image.new("RGBA", (side, side), (13, 17, 23, 0))
    square.alpha_composite(rgba, ((side - rgba.width) // 2, (side - rgba.height) // 2))
    square = square.resize((480, 480), Image.Resampling.LANCZOS)

    rgb = np.asarray(square.convert("RGB"))
    alpha = np.asarray(square.getchannel("A"), dtype=np.float32) / 255.0
    # Bring back facial detail while keeping a restrained, high contrast range.
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    enhanced = cv2.cvtColor(cv2.merge((l_channel, a_channel, b_channel)), cv2.COLOR_LAB2RGB)
    blurred = cv2.GaussianBlur(enhanced, (0, 0), 1.15)
    enhanced = cv2.addWeighted(enhanced, 1.35, blurred, -0.35, 0)
    # Composite transparent pixels against the dashboard background; save RGB
    # because the next stage uses luminance to select ASCII characters.
    background = np.full_like(enhanced, (13, 17, 23))
    result = (enhanced * alpha[:, :, None] + background * (1.0 - alpha[:, :, None]))
    Image.fromarray(np.clip(result, 0, 255).astype(np.uint8), "RGB").save(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    prepare(args.source, args.destination)


if __name__ == "__main__":
    main()
