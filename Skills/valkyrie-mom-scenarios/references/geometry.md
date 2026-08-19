# Tile geometry in Valkyrie (Mansions of Madness)

Everything in this document has been verified twice: once against real `.dds` images (size)
and once by reading the Valkyrie source code directly on GitHub, `NPBruce/valkyrie`, file
`unity/Assets/Scripts/Quest/Quest.cs` (class `Tile`) and `unity/Assets/Scripts/GameType.cs`
(method `TilePixelPerSquare`). It is not an approximation.

## 1. Real size of a tile

The `small`/`medium` traits in the content pack (`tiles.ini` in the repository) do NOT give
the exact size -- they are only a category label. Real data has confirmed that two "small"
tiles can have different sizes from each other.

The real size is encoded in the pixel dimensions of the imported `.dds` image:

```
1 square = 1024 / 3.5 px = 292.5714... px   (constant for MoM, non-Android)

width_in_squares  = width_px  / (1024/3.5)
height_in_squares = height_px / (1024/3.5)
```

Use `scripts/tile_size.py` on the real `.dds` file -- don't calculate this by hand or guess
it from the trait.

**Save every size you compute in `tile_sizes.json`, at the root of the scenario folder**
(next to `quest.ini`). `scripts/validate_scenario.py` reads it automatically to check
geometry in step 6 of the workflow -- if the file doesn't exist, the script still runs but
silently skips that check (it only prints a warning), so a scenario with tokens outside
their tiles could show "validation OK" by mistake if you forget to create it. Format:

```json
{
  "TileSideBedroom1": [7, 3.5],
  "TileSideStudy": [7, 3.5]
}
```

Keys are the `side=` value used in `tiles.ini`, values are `[width, height]` in squares (the
result of `tile_size.py`). It is not packaged in the final `.valkyrie` --
`scripts/package_valkyrie.py` already excludes it automatically.

Examples already confirmed in this project:

| Tile (side)          | Image                          | Real size          |
|-----------------------|---------------------------------|---------------------|
| TileSideBedroom1        | Tile_Bedroom_1_MAD20.dds      | 7 x 3.5 squares    |
| TileSideStudy            | Tile_Study_MAD20.dds          | 7 x 3.5 squares    |
| TileSideEntryHall          | Tile_Entry_Hall_MAD20.dds   | 7 x 3.5 squares    |
| TileSideHall2                | Tile_Hall_2_MAD20.dds     | 7 x 3.5 squares    |

(all "small" per their trait, yet NOT 3.5x3.5 -- hence the importance of measuring the real
image instead of trusting the trait.)

Technical note: the conversion formula assumes the tile has no `top=`, `left=`, `pps=`, or
`aspect=` overrides in its content-pack definition (the vast majority of base-box MoM tiles
don't have them; if a specific tile DOES have them, check its block in the content pack's
`tiles.ini` -- `pps=` replaces the 1024/3.5 constant with the given value).

## 2. Unrotated coordinates

A tile with `rotation=0` (or unspecified) and anchor `(X, Y)` (its `xposition`/`yposition`
fields) occupies, in squares:

```
x in [X, X + width]
y in [Y - height, Y]
```

That is, the anchor is the top-left corner (X = left edge, Y = top edge) and the tile extends
toward +X (right) and -Y (down).

## 3. Rotation

`rotation` spins the tile **counter-clockwise around its own anchor** (the top-left corner,
BEFORE rotating), with no sign flip -- it is literally the `.ini` value passed to
`RotateAround(pivot, Vector3.forward, rotation)` in Unity, and in the coordinate system used
by Valkyrie (x-right, y-up) that is counter-clockwise.

Take the unrotated local offset `(dx, dy)` of any point relative to the anchor (for example a
corner of the tile, or where you want to place a token) and apply this table BEFORE adding it
to the anchor:

| rotation | (dx, dy) -> (dx', dy') |
|----------|--------------------------|
| 0        | (dx, dy)                 |
| 90       | (-dy, dx)                |
| 180      | (-dx, -dy)               |
| 270      | (dy, -dx)                |

Final position = `(X + dx', Y + dy')`.

### Bounding box of an already-rotated tile

Applying the table to the four unrotated corners (`(0,0)`, `(width,0)`, `(0,-height)`,
`(width,-height)`) and taking the bounding rectangle, for `rotation=90` or `270` width and
height swap:

- `rotation=0` or `180`: the box measures `width x height` (same as unrotated).
- `rotation=90` or `270`: the box measures `height x width` (swapped).

For 90 degrees specifically, the resulting box (in absolute coordinates) is:
`x in [X, X+height]`, `y in [Y, Y+width]` -- i.e. it now grows toward +Y (up), not -Y. Don't
assume it always grows downward just because that was the case with `rotation=0`.

`scripts/validate_scenario.py` implements exactly this table (function `tile_box`) -- use it
instead of recalculating by hand each time, it's easy to get a sign wrong.

## 4. Connecting two tiles and placing a door

1. Compute the box (xmin,xmax,ymin,ymax) of each tile with the formula above.
2. Choose the anchor of the second tile so that one edge of its box exactly matches an edge
   of the first (same x value for a horizontal connection, or y for a vertical one). If you
   want a gap/corridor between them, offset that edge on purpose and say so in the event text.
3. The door/explore token goes at the midpoint of the shared border segment (the overlap
   between the ranges of the other axis).
4. Investigator, item, and monster tokens: place them with an offset of 0.5 to 1.5 squares
   toward the interior from the anchor of THEIR OWN tile (not another tile's anchor), using
   the same rotation table if that tile is rotated.

## 5. When the user moves something by hand in the editor

If the user rotates or moves a tile with the visual editor and everything else (tokens,
doors, neighboring tiles) is left with the old coordinates, those coordinates almost
certainly no longer fall inside the tile -- this is not a bug on your part, it's expected.
Re-read the updated `quest.ini`, and recalculate ONLY what depended on that tile using the
formula above; don't touch the tile the user already placed by hand.
