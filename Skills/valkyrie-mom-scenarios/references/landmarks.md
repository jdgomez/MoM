# Furniture/decor landmarks per tile

Why this exists: `references/doors.md` catalogues whether a tile's four outer EDGES are open
or closed, so doors/walls can be placed correctly. It says nothing about what's drawn
*inside* a tile -- sofas, desks, bookshelves, fireplaces. A door or explore token placed at a
geometrically-correct edge position can still land visually on top of a piece of furniture,
which reads as broken even though the underlying math is fine (confirmed happening in
`casa_ashworth`'s first draft: a door token landed on a small table/lamp between two
armchairs in the Lounge, and another on top of the Study's writing desk).

`references/landmarks.json` is the fix: a global, reusable catalog (shared across scenarios,
same idea as `doors.md`) of the notable furniture/decor on each tile, in the same coordinate
system as everything else in this skill.

## Format

```json
{
  "TileSideLounge": [
    {"name": "floral sofa (east wall)", "box": [5.3, 7, -3.6, -1.9], "note": "..."}
  ]
}
```

- Top-level keys are the `side=` value from `tiles.ini` (same keys as `tile_sizes.json`).
- `box` is `[xmin, xmax, ymin, ymax]` in squares, in **local, unrotated** coordinates -- the
  `.dds` image as-is, top-left corner = origin, tile occupies `x in [0,width]`,
  `y in [-height,0]`. Same convention as `references/geometry.md` and `tile_box()` in
  `scripts/validate_scenario.py`. `validate_scenario.py` rotates these boxes for you using
  the placed tile's actual `rotation=` before comparing -- you never need to pre-rotate
  a landmark's box yourself.
- `name` is a short human tag. `note` is optional context (why it matters, or why overlapping
  it on purpose might be fine).
- Boxes are deliberately generous and eyeballed from a `tile_door_preview.py` grid image, not
  pixel-measured. Only catalogue clearly chunky furniture/fixtures (armchairs, sofas, desks,
  bookshelves, fireplaces, big rugs with a centerpiece). Skip thin wall trim, baseboards, and
  small hanging picture frames unless they were big/relevant enough to actually change a
  placement decision -- cataloguing every prop in every tile isn't the goal, avoiding the
  obvious collisions is.

## Workflow: when to catalogue a tile

Do this at the same time as the door/wall analysis in step 5 of `SKILL.md` -- you're already
looking at the `tile_door_preview.py` grid image for edge openness, so read the interior for
furniture in the same pass instead of a separate step:

1. Generate the grid preview if you haven't already: `python3 scripts/tile_door_preview.py
   <path.dds>`.
2. Look at the image (`Read`). Identify the clearly chunky furniture/fixtures and their
   approximate grid-square bounding boxes.
3. Add an entry per landmark to `references/landmarks.json` under that tile's `side=` key.
   If the tile isn't in the catalog yet, add a new top-level key.
4. Before finalizing a door/token/monster position (step 6 of `SKILL.md`), check it against
   this catalog yourself, and also run `scripts/validate_scenario.py` -- it cross-checks
   automatically and prints a non-blocking warning for any overlap it finds.

## Reading the validator's warning

`scripts/validate_scenario.py` reads `references/landmarks.json` automatically (it's next to
the skill, not per-scenario) and warns -- but does NOT fail validation or change the exit
code -- when a token/spawn's position falls inside a catalogued landmark's (rotated) box.
Tokens with `display=false` are skipped (they're never rendered, so they can't visually
collide with anything).

This is intentionally a warning, not an error, for two reasons:
- The catalog is eyeballed, not pixel-exact -- treat a warning as "go look at the preview
  image yourself," not as proof something is actually wrong.
- Overlap is sometimes exactly what you want. A monster spawned on top of a
  "sheet-covered armchair" landmark (something erupting from under it) is good flavor, not a
  bug. Doors and explore tokens landing on furniture, on the other hand, almost always look
  broken -- move those.

## Precision limits, be honest about them

These boxes come from looking at a static preview image and estimating grid-square ranges by
eye -- there is no pixel-level collision detection here. Tight gaps (less than ~0.5 squares
between two landmarks) usually aren't reliably usable for a token, since a placed icon is
roughly 0.95 squares wide itself. When a tile is densely decorated on every relevant edge
(this happened with `TileSideHallStairs`'s west wall while building `casa_ashworth`), the
best you can do is pick the position that avoids the single most visually prominent object
(a window or a big piece of furniture beats a small leaning picture frame) and say so plainly
to the user instead of presenting a guess as pixel-perfect.
