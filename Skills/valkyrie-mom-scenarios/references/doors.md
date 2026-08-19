# Doors and walls: connecting tiles correctly

## PENDING for next session (casa_ashworth, confirmed playable 2026-08-19, polish left)

Playtested and confirmed working (icons land where they should). Three follow-ups the user
asked to defer, don't lose track of them:

1. **Cover unused real doors with a wall token.** `TileSideHall2` has a real door at
   `col=1,row=2` (south wall) that nothing in `casa_ashworth` uses -- only `col=4,row=2`
   connects to the Lounge (see `references/doors.json`). Cover the unused one with
   `TokenWallInside` (same position math as a door: art `col,row` -> `scripts/door_position.py`
   -> `xposition`/`yposition`, `display=false`, `buttons=0`, `clickeffect=false`) so it doesn't
   read as an interactive door that goes nowhere. Check whether any other tile in the scenario
   has an unused real door too (re-check `doors.json` entries against what `tokens.ini` actually
   uses).
2. **Finish adding door icons wherever a wall still needs one.** Continue the same
   `doors.json`-first, `TokenDoorInside`-fallback workflow (step 5 in `SKILL.md`) for any
   connection not yet finalized -- in particular, `TileSideLounge`'s other 3 walls and
   `TileSideAttic`'s other 3 walls have not been checked for real doors yet (only Lounge-north
   and Attic-west have been catalogued so far, see the `_note` fields in `doors.json`).
3. **Try rotating the Attic to avoid the decorative door token entirely.** The
   HallStairs<->Attic connection currently uses a `TokenDoorInside` (`TokenPuertaAtico`)
   because Attic's WEST wall has no real door. Attic's other 3 walls haven't been checked --
   if one of them has a real door, placing Attic with `rotation=90/180/270` so that door lands
   on the HallStairs-facing edge would let this connection drop the decorative token too, the
   same way the Study connection did. Check with `tile_door_preview.py` first, then work out
   the anchor with `door_position.py` the same way `TileEstudio` was aligned (see its comment
   in `casa_ashworth/tiles.ini`).

## The key idea

This document resolves a real problem that came up while building "casa_de_prueba" (the
project's first test scenario): tiles fit together perfectly on the board (correct
geometry), but the door/explore tokens didn't line up with any door painted in the artwork --
because on many tiles, that wall simply has no door painted on it.

## The key idea

Valkyrie does NOT require a connection between tiles to match a door already drawn. Each
tile's artwork is largely decorative; the actual connection is defined by the scenario itself
placing tokens on top of it. There are three distinct situations for each tile edge you want
to use as a connection:

1. **Edge already open in the artwork** (corridors that only connect through their two short
   ends, exterior tiles like garden/street with a whole side with no wall). Here do NOT place
   any door/wall token -- just the exploration token (`TokenExplore`) for the reveal event.
   Adding a decorative door on top of an already-open gap looks like a door floating in
   midair.
2. **Solid wall with no painted door** (the most common case: most base-box rooms are boxes
   closed on all four sides in their artwork). Here you DO need to add a `TokenDoorInside`
   (interior-interior) or `TokenDoorOutside` (if one side is an exterior tile) token to
   "paint" a door on top of the wall. See the format below.
3. **Door already explicitly painted** (rare; confirmed example: the golden double door of the
   Entry Hall / EntryHall, on its west wall). Here it's enough to place the `TokenExplore`
   aligned with that door -- adding a `TokenDoorInside` on top would cover the existing
   pretty artwork with the generic icon.

To tell these three cases apart, use `scripts/tile_door_preview.py` (generates a
grid-overlaid image) and inspect the tile visually -- don't guess. Save what you confirm in
`references/doors.json` (see "Two grids" and "The doors.json catalog" below) to avoid
repeating the analysis for the next scenario.

## Two grids (important, confirmed 2026-08-19)

Valkyrie uses two DIFFERENT pixel-per-unit constants, for two different purposes, and mixing
them up is exactly what caused doors to land on top of furniture in earlier drafts of
`casa_ashworth`:

- **Engine grid** -- `1024/3.5` px/square (`scripts/tile_size.py`). This is what Valkyrie
  itself uses for a tile's footprint/adjacency: `xposition`/`yposition`, `tile_box()`
  rotation, how two tiles' edges touch. **Keep using this one for tile placement.** It's
  verified against the engine source (`GameType.cs`, `MoMGameType.TilePixelPerSquare()`) and
  against real gameplay (`casa_ashworth` is playable with tiles placed this way).
- **Art grid** -- `1024/3` px/unit (`scripts/tile_door_preview.py`, updated 2026-08-19). This
  is what the artwork was actually drawn on. Confirmed by measuring real annotated
  screenshots pixel-by-pixel: door centers land almost exactly on integer ART-grid cell
  centers (e.g. x=1.55 out of a cell centered at 1.5), but land awkwardly between cells on the
  ENGINE grid (e.g. x=1.81, matching no cell center). For `TileSideHall2` specifically this
  means 6 columns x 3 rows on the art grid, vs. 7x3.5 on the engine grid -- same image, same
  full pixel dimensions, just divided into a different number of units.

**Do not change the engine grid or tile_sizes.json.** Use the art grid only to identify WHERE
on a tile a door is drawn (as a `col,row` cell), then convert that to an actual engine
`xposition`/`yposition` with `scripts/door_position.py`, which chains three already-verified
steps: art cell -> local unrotated engine offset (simple fraction-of-width/height scaling,
both grids describe the same full image) -> rotate using the table in `references/geometry.md`
-> add the tile's anchor. This is the same three-step pipeline `validate_scenario.py` already
uses for tile corners and landmark boxes, just with a different source for the local offset.

**A caught mistake worth knowing about:** `tile_door_preview.py` used to generate its preview
VERTICALLY FLIPPED relative to how Valkyrie actually renders the tile in-game (a DDS/Unity
texture V-coordinate quirk, not a deliberate choice -- confirmed against a real screenshot of
Hall2, fixed 2026-08-19). Every door/landmark judgment made before that fix has north and
south swapped. `references/landmarks.json` was built before the fix and before the art-grid
switch -- treat its north/south labels and continuous boxes as unreliable until it's
recatalogued (deliberately out of scope for now, see the "landmarks paused" note below).
`references/doors.json`, rebuilt from scratch after both fixes for `Hall2`/`Study`/
`HallStairs`, is the reliable one.

## The doors.json catalog

`references/doors.json` replaces hand-eyeballed continuous door positions with a small,
global, reusable catalog: for each `side=`, the art-grid size and a list of
`{col, row, wall}` cells where a REAL door is already painted. `wall` (north/south/east/west)
is a **documentary label only**, describing the door's position in the tile's original,
UNROTATED artwork -- it is derived from row/col (row 0 = north, last row = south, col 0 =
west, last col = east) once, when cataloguing, and placement code never reads it to decide
where the door ends up. If the tile is placed with `rotation != 0`, run col/row through
`scripts/door_position.py` (which applies the same rotation table as everything else in this
skill) -- a "north" door can absolutely end up on the placed tile's east or west edge, and
that's correct, not a bug.

If a wall you want to connect through has no entry in `doors.json` for that tile, it has no
real door -- follow case 2 above (`TokenDoorInside`/`TokenDoorOutside`, `clickeffect=false`,
listed before the `TokenExplore` in `add=`, see below). Catalogue what you find (even "no door
here") so the next scenario doesn't repeat the analysis.

**Landmarks paused (2026-08-19):** by explicit decision, furniture/decor cataloguing
(`references/landmarks.json`, `references/landmarks.md`) is on hold while this door system
gets solid -- focus on doors only for now. When placing a door/token, still LOOK at the
`tile_door_preview.py` image yourself and avoid obvious furniture collisions by eye; just
don't block on formally cataloguing every landmark until landmarks.json itself gets
recatalogued under the fixed/art-grid images.

## How to create a door where there isn't one: TokenDoorInside / TokenDoorOutside

These are normal tokens (they go in `tokens.ini`), but purely decorative -- they paint a
small "wall with door" icon at the given position, covering whatever was underneath (solid
wall, window, whatever):

```ini
[TokenDoorRoomX]
xposition=<same x as the TokenExplore for this connection>
yposition=<same y as the TokenExplore for this connection>
display=false
buttons=0
type=TokenDoorInside
rotation=0    ; 0 (or optionally 180) for a horizontal wall (north/south edge, y=const)
              ; 90 (or optionally 270) for a vertical wall (east/west edge, x=const)
```

Important points, confirmed by reading the base box's `tokens.ini` and real published
scenarios:

- `buttons=0` and `display=false`: the token itself is not interactive, it only draws the
  icon. The interaction (revealing the next tile) is given by a normal `TokenExplore` placed
  at the SAME position (identical xposition/yposition) with its own `event1=`.
- Place both (the decorative `TokenDoorInside` and the interactive `TokenExplore`) in the
  same `add=` of the event that reveals the tile with that wall -- they must appear together.
- The `TokenDoorInside` does NOT need to be removed once the door is opened (unlike
  `TokenExplore`, which IS removed with `remove=` after use) -- the door drawing stays as a
  permanent part of the board.
- The position doesn't need to be pixel-perfect against any hidden artwork -- the token
  itself draws its door there. Keep using the midpoint of the shared border between the two
  tiles (formula in `references/geometry.md`), avoiding overlap with large furniture already
  painted on the tile where possible.
- These tokens have their own `pps` (pixels per square) in their content definition,
  different from the tiles' constant -- it doesn't affect how you position them
  (xposition/yposition are still normal squares), only their on-screen size.

## How to block an opening you don't want to use: TokenWallInside / TokenWallOutside

Same mechanism but reversed: if two tiles end up adjacent along an edge that IS open in the
artwork (or a connection you don't want to exist), place a `TokenWallInside`/
`TokenWallOutside` (or the purely cosmetic `...Green` variants) there to visually "close" that
gap. Same format as `TokenDoorInside` (buttons=0, display=false, rotation according to wall
orientation).

## Available types (confirmed in `content/MoM/base/tokens.ini`)

| type                  | Use                                              |
|------------------------|----------------------------------------------------|
| TokenDoorInside          | Creates an interior-interior door in a solid wall |
| TokenDoorOutside          | Creates an interior-exterior door                        |
| TokenWallInside             | Closes a gap between two interior tiles                |
| TokenWallOutside              | Closes a gap toward an exterior tile                       |
| TokenWallInsideGreen             | Cosmetic (green) variant of TokenWallInside                    |
| TokenWallOutsideGreen               | Cosmetic (green) variant of TokenWallOutside                     |
| TokenBarricadeInside                  | Barricade (thematic block, not simple decoration)                     |
| TokenBarricadeOutside                    | Same, exterior face                                                       |
| TokenSecretInside / TokenSecretOutside      | Secret door/passage                                                          |

## Already catalogued tiles (open vs. closed edges, unrotated)

**Caution (2026-08-19): the North/South columns below were catalogued BEFORE the vertical-flip
bug in `tile_door_preview.py` was found and fixed (see "Two grids" above) -- they may well be
swapped.** East/West aren't affected by that specific bug (a vertical flip doesn't swap left
and right), so those columns are probably still fine. Also, "Closed" here only ever meant "no
open gap in the art" -- it did NOT reliably distinguish a plain wall from a wall with a real
door already painted on it (that distinction is what `references/doors.json` now tracks
explicitly). `Hall2` and `Study` have been fully redone under the fixed tool and now live in
`doors.json` with confirmed real doors on walls this table calls merely "Closed" -- trust
`doors.json` over this row for those two. Treat every other row's North/South as unverified
until it's rechecked the same way. "Open" = no door token needed, just a TokenExplore.
"Closed" = a TokenDoorInside/Outside is needed if you want to connect through it (or check
`doors.json` first -- there may be a real door). Empty rows = not checked yet, don't assume.

| side (TileSideXxx) | North (y=0, top) | South (y=-height, bottom) | West (x=0) | East (x=width) |
|----------------------|------------------------|--------------------------|----------------|--------------------|
| EntryHall               | Closed (solid wall)    | Closed (solid wall)      | **Door already painted** (golden double door, rows ~1-2) | Open (the hallway continues, no wall) |
| Hall1                      | Closed (wall + decorative pictures) | Closed (same)                | Open (end of the corridor) | Open (end of the corridor) |
| Hall2                         | Closed                                  | Closed                            | Open                           | Open                              |
| Lounge                           | Closed (decorative notch, not a door)  | Closed (fireplace)                    | Closed (windows with curtains)      | Open (the parquet floor continues, no wall) |
| DiningRoom                          | Closed                                       | Closed                                  | Closed                                  | Closed                                     |
| Study                                  | Closed (fireplace)                               | Closed                                     | Closed (window)                           | Closed                                        |
| Library                                   | Closed (decorative notch)                          | Closed                                        | Closed (bookshelves)                          | Closed (window)                                 |
| Bedroom1                                     | Closed                                                 | Closed (decorative notch)                        | Closed                                           | Ambiguous (dark gap rows ~1-2, inspect more closely before using as a connection) |
| Bedroom2                                        | Closed (decorative notch)                                | Closed                                               | Closed                                              | Closed                                                                          |
| HallCorner1                                        | Closed (wall+pictures, local north)                          | Open (local west, corridor continues)               | see rotation note below                                 | Open toward area with furniture (local east, likely connects to another room)          |
| BilliardsRoom                                         | Closed                                                            | Closed                                                    | Closed                                                     | Ambiguous (dark gap rows ~1-2, inspect more closely)                                       |
| Attic                                                     | Closed for most of it; there's an internal gap of its own between two zones of the same tile (not an outer edge) | Closed | Closed | Closed (window) |

**Note on HallCorner1**: its "open" sides are described in LOCAL coordinates (the `.dds`
image as-is, unrotated). If you use this tile rotated (as in the early "casa_de_prueba" test
scenario, `rotation=90`), you have to run those local coordinates through the rotation
formula in `references/geometry.md` to know which ABSOLUTE edge each side corresponds to --
don't assume "local west" is still the board's west edge once rotated. In that test scenario,
after applying the rotation, both connections (to Hall2 and to BilliardsRoom) ended up
falling on walls marked "closed" in the table above, so both used `TokenDoorInside`.

When you use a tile that isn't in this table, catalogue its 4 edges with
`tile_door_preview.py` before deciding where to connect, and add a row here.


## RESOLVED: the TokenDoorInside/TokenExplore overlap bug -- root cause and fix

Originally logged as an unresolved issue after playtesting "casa_de_prueba": when
`TokenDoorInside` and its `TokenExplore` sit at the SAME `xposition`/`yposition`, one of them
would end up unclickable. **Root cause confirmed 2026-08-19 by reading Valkyrie's actual
source (`NPBruce/valkyrie`, `master` branch) -- not by trial and error:**

1. `Quest.cs`, method `Add(string[] names, ...)` (~line 1158): when an event's `add=` list is
   processed, tokens are instantiated **in the exact order they're listed**, one `Token`
   object per name, each doing `unityObject.transform.SetParent(game.tokenCanvas.transform)`.
   Unity appends new children at the end of the sibling list, so **whichever token is listed
   LAST in `add=` becomes the topmost sibling** in the canvas.
2. `Quest.cs`, class `Token` constructor (~line 1862): every token gets a plain
   `UnityEngine.UI.Image`, and Valkyrie never sets `raycastTarget = false` on it anywhere in
   the codebase -- so it defaults to `true`. Unity's click routing
   (`StandaloneInputModule`/`EventSystem`) only ever inspects the **single topmost**
   raycast-hit graphic and walks up *its own* parent chain for a click handler; it does NOT
   fall through to whatever sits underneath. So the topmost sibling always wins the click,
   whether or not it actually has a handler -- a token below a "dead" topmost token gets no
   click at all.
3. `QuestData.cs`, class `Token` (~line 385-439): `enableClick` (the flag that decides
   whether `TokenBoard.cs` adds a `UnityEngine.UI.Button`, see `TokenBoard.cs` ~line 43-73)
   defaults to `true` and is only set to `false` by an explicit `clickeffect=false` in the
   token's ini section -- it is NOT automatically tied to `buttons=0`. A purely decorative
   `TokenDoorInside` written the way this document used to recommend (no `clickeffect=`) is
   therefore just as clickable as a real `TokenExplore` as far as Unity is concerned; if it
   ends up on top, it silently swallows the click (its own `event1=` is empty, so nothing
   happens) instead of passing it through to the `TokenExplore` underneath.

**The fix** (both parts, apply both, they're cheap and each closes a different gap):

1. **Order matters**: in `add=`, always list the *interactive* token (`TokenExplore`, etc.)
   AFTER the decorative one, e.g. `add=TokenDoorSalaX TokenExploracionX`. This makes the
   explore token the last-instantiated, topmost sibling, so it wins the raycast and its
   `event1=` fires correctly. (Bonus: visually this is also what you want -- the small
   explore/magnifying-glass icon ends up rendered on top of the door art, which reads fine.)
2. **Belt and suspenders**: add `clickeffect=false` to every purely decorative token
   (`TokenDoorInside`, `TokenDoorOutside`, `TokenWallInside`, `TokenWallOutside`, and their
   `...Green` variants). It costs nothing, documents intent, and protects against a future
   edit accidentally reordering `add=` and silently reintroducing the bug.

Updated template:

```ini
[TokenDoorSalaX]
xposition=<same x as the TokenExplore for this connection>
yposition=<same y as the TokenExplore for this connection>
display=false
buttons=0
clickeffect=false
type=TokenDoorInside
rotation=0    ; 0 (or optionally 180) for a horizontal wall (north/south edge, y=const)
              ; 90 (or optionally 270) for a vertical wall (east/west edge, x=const)

[TokenExploreSalaX]
xposition=<same x as TokenDoorSalaX>
yposition=<same y as TokenDoorSalaX>
buttons=1
event1=EventEnterSalaX
type=TokenExplore
```

And in the event that reveals both: `add=TokenDoorSalaX TokenExploreSalaX` -- door first,
explore token last.

This also explains why the real published scenario referenced in the original investigation
(`TokenPuertaSalon` / `TokenExploracionApasilloPpal`, both at `(7,-8.75)`) worked: whichever
of the two was listed second in that scenario's `add=` was the one on top and clickable --
not a coincidence or an unrelated factor, just this same ordering rule.
