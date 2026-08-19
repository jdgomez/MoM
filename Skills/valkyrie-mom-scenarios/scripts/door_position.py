#!/usr/bin/env python3
"""Converts a catalogued door's ART-grid cell (col,row) -- see references/doors.json --
into the actual engine xposition/yposition to write into tokens.ini, for a tile placed at
a given anchor and rotation.

Why two grids: the ENGINE grid (1 square = 1024/3.5 px, see tile_size.py) is what Valkyrie
uses for a tile's footprint/adjacency. The ART grid (1 unit = 1024/3 px, see
tile_door_preview.py) is what the artwork -- and therefore door positions -- actually lines
up with (confirmed 2026-08-19 against real annotated screenshots: door centers land almost
exactly on integer ART-grid cell centers, not on the ENGINE grid). Full story in
references/doors.md ("Two grids" section).

The conversion is a straight unit conversion through a shared pixel fraction (both grids
describe the same full image, just divided into a different number of units), followed by
the SAME rotation table already verified for tiles and landmarks (references/geometry.md,
also implemented in validate_scenario.py's tile_box/rotate_box):

    dx_local = (col + 0.5) / art_cols * engine_width
    dy_local = -(row + 0.5) / art_rows * engine_height
    (dx, dy) = rotate(dx_local, dy_local, rotation)     # table in references/geometry.md
    (x, y)   = (anchor_x + dx, anchor_y + dy)

`wall` in doors.json is a label for the door's position in the tile's ORIGINAL, unrotated
artwork ONLY -- this script never reads it for the math, only col/row matter. After rotating,
a "north" door can easily end up on what is, absolutely, the east or west side of the placed
tile; that's expected, not a bug (see references/doors.md).

Usage:
    python3 door_position.py <side> <anchor_x> <anchor_y> [rotation] [--doors path.json]
        [--tile-sizes path.json]

Example:
    python3 door_position.py TileSideHall2 7 0 0
    python3 door_position.py TileSideHall2 7 0 90   # same tile, forced rotation
"""
import json
import sys
from pathlib import Path

ROTATIONS = {
    0: lambda dx, dy: (dx, dy),
    90: lambda dx, dy: (-dy, dx),
    180: lambda dx, dy: (-dx, -dy),
    270: lambda dx, dy: (dy, -dx),
}


def door_engine_position(col, row, art_cols, art_rows, engine_w, engine_h, anchor_x, anchor_y, rotation):
    dx_local = (col + 0.5) / art_cols * engine_w
    dy_local = -(row + 0.5) / art_rows * engine_h
    rot = ROTATIONS.get(int(rotation) % 360)
    if rot is None:
        raise ValueError(f"rotation must be 0/90/180/270, got {rotation}")
    dx, dy = rot(dx_local, dy_local)
    return anchor_x + dx, anchor_y + dy


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 3:
        print(__doc__)
        sys.exit(1)
    side = args[0]
    anchor_x = float(args[1])
    anchor_y = float(args[2])
    rotation = int(args[3]) if len(args) > 3 else 0

    here = Path(__file__).resolve().parent.parent / "references"
    doors_path = here / "doors.json"
    if "--doors" in sys.argv:
        doors_path = Path(sys.argv[sys.argv.index("--doors") + 1])
    tile_sizes_path_default = None
    if "--tile-sizes" in sys.argv:
        tile_sizes_path_default = Path(sys.argv[sys.argv.index("--tile-sizes") + 1])

    with open(doors_path, encoding="utf-8") as f:
        catalog = json.load(f)
    if side not in catalog:
        raise SystemExit(f"ERROR: {side} not in {doors_path}")
    entry = catalog[side]
    art_cols, art_rows = entry["artGrid"]

    engine_w = engine_h = None
    if tile_sizes_path_default and tile_sizes_path_default.exists():
        with open(tile_sizes_path_default, encoding="utf-8") as f:
            sizes = json.load(f)
        if side in sizes:
            engine_w, engine_h = sizes[side]
    if engine_w is None:
        raise SystemExit(
            f"ERROR: need the engine size (width,height) for {side} -- pass "
            f"--tile-sizes pointing at a tile_sizes.json that has it (see scripts/tile_size.py)"
        )

    print(f"{side}  artGrid={art_cols}x{art_rows}  engine={engine_w}x{engine_h}  "
          f"anchor=({anchor_x},{anchor_y})  rotation={rotation}")
    for d in entry["doors"]:
        x, y = door_engine_position(d["col"], d["row"], art_cols, art_rows,
                                     engine_w, engine_h, anchor_x, anchor_y, rotation)
        print(f"  col={d['col']} row={d['row']} (drawn wall: {d['wall']})  ->  "
              f"xposition={x:.4f} yposition={y:.4f}")


if __name__ == "__main__":
    main()
