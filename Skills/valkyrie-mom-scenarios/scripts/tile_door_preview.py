#!/usr/bin/env python3
"""Generates a preview image of a .dds tile with an ART-GRID overlay (NOT the engine
placement grid) so you can visually locate where each door is painted, in coordinates
that actually line up with the artwork.

Two different grids, on purpose (confirmed 2026-08-19 against real annotated screenshots
of Hall2's three doors -- see references/doors.md "Two grids" section):
  - The ENGINE grid (1 square = 1024/3.5 px, computed by tile_size.py) is what Valkyrie
    uses for a tile's footprint/adjacency -- xposition/yposition math, tile_box() rotation,
    connecting two tiles. Keep using that for placement. Don't change it.
  - The ART grid (1 unit = 1024/3 px, used ONLY by this script) is what the artwork was
    actually drawn on. Door positions marked by a human on a screenshot land almost exactly
    on integer art-grid cell centers; they land awkwardly between cells on the engine grid.
    This script exists to read door positions off the art grid; converting an art-grid
    (col,row) to an actual engine xposition/yposition is a separate step (see
    references/doors.md and scripts/door_position.py), not something this script does.

Why this script exists at all: Valkyrie does NOT store where each tile's door is in any
.ini -- scenario authors place it by hand in the visual editor by looking at the artwork.
This script lets you look at the image without opening Valkyrie: it generates a PNG with
a grid that can be inspected (e.g. with the Read tool) to read directly which cell each
door falls on, column (x) and row (y) from the top-left corner of the unrotated tile.

Usage:
    python3 tile_door_preview.py <path.dds> [output.png] [--max-width 1400]

The resulting image has vertical red lines numbered with the art-grid column (x, 0 = left
edge) and horizontal cyan lines numbered with the art-grid row (y, 0 = top edge, growing
downward). A door whose center lands inside "column 1, row 0" belongs there regardless of
the tile's real engine width in squares.
"""
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw
except ImportError:
    print("This script needs Pillow: pip install pillow --break-system-packages")
    sys.exit(1)

PPS_ENGINE = 1024 / 3.5  # engine px/square -- placement/footprint, NOT used for the grid drawn here
PPS_ART = 1024 / 3       # art px/unit -- what this script actually draws and labels


def make_preview(path_in, path_out, max_width=1400):
    im = Image.open(path_in).convert("RGBA")
    # DDS row 0, as Pillow decodes it, is the BOTTOM of the image as Valkyrie actually
    # renders it in-game (confirmed 2026-08-19 against a real screenshot of Hall2: a
    # flipped preview lined up with the game, the unflipped one didn't). Likely a Unity
    # texture V-coordinate convention baked into how these .dds files were extracted from
    # the app, not a Pillow bug. Flip here so row 0 in this preview = the north edge =
    # y=0, matching xposition/yposition, geometry.md, and the rest of this skill.
    im = im.transpose(Image.FLIP_TOP_BOTTOM)
    w, h = im.size
    draw = ImageDraw.Draw(im)

    x, col = 0.0, 0
    while x <= w:
        draw.line([(x, 0), (x, h)], fill=(255, 0, 0, 255), width=3)
        draw.text((x + 4, 4), str(col), fill=(255, 255, 0, 255))
        x += PPS_ART
        col += 1

    y, row = 0.0, 0
    while y <= h:
        draw.line([(0, y), (w, y)], fill=(0, 255, 255, 255), width=3)
        draw.text((4, y + 4), str(row), fill=(0, 255, 0, 255))
        y += PPS_ART
        row += 1

    scale = min(1.0, max_width / w)
    if scale < 1.0:
        im = im.resize((int(w * scale), int(h * scale)))
    im.save(path_out)
    return im.size, (w, h)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    src = Path(args[0])
    out = Path(args[1]) if len(args) > 1 else src.with_suffix(".preview.png")
    max_w = 1400
    if "--max-width" in sys.argv:
        max_w = int(sys.argv[sys.argv.index("--max-width") + 1])
    preview_size, orig_size = make_preview(src, out, max_w)
    art_cols, art_rows = orig_size[0] / PPS_ART, orig_size[1] / PPS_ART
    eng_w, eng_h = orig_size[0] / PPS_ENGINE, orig_size[1] / PPS_ENGINE
    print(f"{out}  preview={preview_size}  original_px={orig_size}")
    print(f"  art grid (this image): {art_cols:.2f} x {art_rows:.2f} units")
    print(f"  engine footprint (xposition/yposition, unchanged): {eng_w:.2f} x {eng_h:.2f} squares")
