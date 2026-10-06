#!/usr/bin/env python3
"""Render a prepared portrait as an animated terminal-style SVG."""
import argparse
import html
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

BG = "#0d1117"
FRAME = "#30363d"
MUTED = "#7d8590"
TEXT = "#c9d1d9"
GREEN = "#39d353"
NAME = "Júlia Danieli Romera Lage"
USER = "juliaromeira"
RAMP = "  ..,:;irsXA253hMHGS#9B&@"


def render(source: Path, destination: Path) -> None:
    image = Image.open(source).convert("RGB")
    # Account for the narrow proportions of monospace glyphs.
    image = ImageOps.fit(image, (160, 86), method=Image.Resampling.LANCZOS)
    gray = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)
    gray = cv2.createCLAHE(clipLimit=1.7, tileGridSize=(8, 8)).apply(gray)
    gray = cv2.GaussianBlur(gray, (3, 3), 0.35)

    rows = []
    ramp_size = len(RAMP) - 1
    for row in gray:
        chars = []
        for value in row:
            # Slight gamma lift preserves eyes, hair, and other mid-tone detail.
            normalized = (float(value) / 255.0) ** 0.82
            index = max(0, min(ramp_size, round(normalized * ramp_size)))
            chars.append(RAMP[index])
        rows.append("".join(chars))

    width, height = 840, 880
    pad, top, line_height = 20, 48, 8.6
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,monospace">',
        '<style>@keyframes row{from{opacity:0}to{opacity:1}}.r{opacity:0;animation:row .1s linear both}@media(prefers-reduced-motion:reduce){.r{opacity:1!important;animation:none!important}}</style>',
        f'<rect width="{width}" height="{height}" rx="12" fill="{BG}"/><rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    ]
    for i, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        out.append(f'<circle cx="{20 + i*16}" cy="16" r="5" fill="{color}"/>')
    out.append(f'<text x="{width/2}" y="20" text-anchor="middle" fill="{MUTED}" font-size="12">{USER}@github: ~$ ./portrait.sh</text>')
    for i, line in enumerate(rows):
        delay = i * 0.045
        out.append(
            f'<text class="r" style="animation-delay:{delay:.3f}s" x="{pad}" y="{top+i*line_height:.1f}" '
            f'fill="{TEXT}" font-size="7.1" textLength="{width-pad*2}" lengthAdjust="spacing">{html.escape(line)}</text>'
        )
    out.append(
        f'<line x1="0" y1="820" x2="{width}" y2="820" stroke="{FRAME}"/>'
        f'<text x="{pad}" y="851" fill="{MUTED}" font-size="18">{USER}@github:~$ whoami '
        f'<tspan fill="{TEXT}">{html.escape(NAME)}</tspan></text></svg>'
    )
    destination.write_text("".join(out), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    render(args.source, args.destination)


if __name__ == "__main__":
    main()
