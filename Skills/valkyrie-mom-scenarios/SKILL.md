---
name: valkyrie-mom-scenarios
description: >
  Build, edit, and fix custom Mansions of Madness (2nd Edition) scenarios for the Valkyrie
  companion app (.valkyrie files / quest.ini format). Use this skill whenever the user asks
  to create a scenario, quest, escenario, mansion, partida personalizada, or homebrew content
  for "Mansions of Madness", "Mansiones de la Locura", or "Valkyrie" -- including requests to
  add rooms/tiles/losetas, place monsters/enemies, write event text, connect tiles, position
  doors, fix token placement, rotate a room, or package/export a .valkyrie file. Also use it
  when the user mentions files like quest.ini, tiles.ini, tokens.ini, events.ini, spawns.ini,
  or paths under the user's Valkyrie or MoM project folders -- even if they don't say
  "Valkyrie" explicitly, since these filenames are unique to this workflow. The user may
  address you in Spanish; the Spanish trigger phrases above are literal words to match, not
  content to translate.
compatibility: Windows host with Valkyrie installed. Needs bash (python3, with the `pillow`
  package installed -- `pip install pillow` -- for `tile_door_preview.py`) and, for placing
  files into the live Valkyrie app or reading tile artwork, File Explorer via computer-use as
  a fallback (direct Bash access has worked so far, see `references/paths.md`).
---

# Mansions of Madness scenarios in Valkyrie

This skill packages everything learned building and debugging real scenarios for Valkyrie
(the custom-scenario editor/player for Mansions of Madness 2nd Edition). It covers everything
from hand-writing `quest.ini` to computing the exact position of every tile, token, and door
-- without needing to open the visual editor to check.

## Why this isn't "just filling in an ini"

Valkyrie places everything (tiles, tokens, monsters, doors) with numeric square coordinates.
The visual editor turns clicks into those numbers for you; without it, you have to compute
them by hand. Two things that are NOT obvious and that this skill already solved for you:

1. **The real size of a tile can't be guessed from its name or its "small"/"medium" trait.**
   Two "small" tiles can measure 3.5x3.5 or 7x3.5 squares. The only reliable data is the pixel
   size of its imported `.dds` image. See `references/geometry.md`.
2. **A tile's rotation spins counter-clockwise around its top-left corner**, confirmed by
   reading the Valkyrie source code (not by trial and error). Full table in
   `references/geometry.md`.

Jumping straight to inventing coordinates (as happened the first time in this project)
produces scenarios that "work" mechanically but with tokens floating outside their tiles.
Follow the workflow below to avoid that.

## Project paths (Juan's setup)

- **Working project (connected folder):** `C:\Users\V\Desktop\Programar\MoM`
  - `Scenarios\` -- scenarios in progress (uncompressed folders, one subdirectory per scenario)
  - `Sources\img\` -- local copy of every `.dds` image imported by Valkyrie (tiles, tokens,
    counters). If a file isn't here, copy it from the source (see next point).
- **Original images imported by Valkyrie:** `%APPDATA%\Valkyrie\MoM\import\img\` --
  accessible with `Bash` using the absolute path (confirmed 2026-08-19), no computer-use
  needed. If `Sources\img` doesn't have the tile you need, copy it from there with `cp`.
- **Folder read by Valkyrie's visual editor:** `%APPDATA%\Valkyrie\MoM\Editor\<name>\` -- a
  scenario must live here (uncompressed) to show up in "Quest Editor" inside the app.
  Accessible with `Bash` (`cp -r`/`rm -rf` with absolute path), no computer-use.
- **Playable scenarios folder:** `%APPDATA%\Valkyrie\Download\` -- packaged `.valkyrie`
  (zip) files ready to play go here. Accessible with direct `Bash`.

If at any point you don't have access to one of these paths, ask Juan to connect the folder
(`request_cowork_directory`) or grant File Explorer access (`computer-use`) -- don't assume
it's impossible, direct Bash access has worked so far even where the docs originally said it
wouldn't (see `references/paths.md`).

## Workflow

### 1. Clarify scope before writing anything

Before generating files, confirm with the user (if not already stated):
- Theme/setting and tone of the scenario.
- Language of the text (default Spanish -- this is the project's convention: every scenario
  built here ships with `defaultlanguage=Spanish`, even though this skill's own documentation
  is in English).
- Allowed content: base box only, or expansions Juan owns. This decides which
  `TileSide`/`Monster` you can use -- see `references/quest_format.md` on `packs=`.
- Approximate size (number of rooms, fights, playtime) -- no more detail than that is needed
  to start; the rest gets adjusted while iterating.

### 2. Choose tiles and monsters

- For base-box content (`type=MoM`, no `packs=`), use the names already confirmed in
  `references/tile_names_es.md` (tile -> confirmed Spanish on-screen name, plus a list of
  base monsters with their Spanish name). This saves you from having to guess translations.
- If you need a tile or monster from an expansion, or any that isn't in that reference,
  confirm the exact internal name (`TileSideXxx`, `MonsterXxx`) before using it -- an invented
  name breaks loading the scenario in Valkyrie. The fastest way is to `Grep` the REAL content
  packs already installed with the app, at
  `C:\Program Files (x86)\Valkyrie\valkyrie_Data\StreamingAssets\content\MoM\<pack>\tiles.ini`
  / `monsters.ini` (see `references/paths.md`) -- **the base-box pack is called `base`**
  (`content\MoM\base\tiles.ini`), not `MoM` or `MAD20` -- that `MAD20` is just the image
  filename suffix, not the folder name. If that folder doesn't exist on the machine, clone
  `NPBruce/valkyrie` from GitHub as a fallback and check
  `unity/Assets/StreamingAssets/content/MoM/<pack>/`.
- The repository/content-pack files only have internal English names (`TileSideXxx`) and
  `{ffg:...}` keys, not the real Spanish text on the physical card/tile. If a tile or monster
  isn't in `references/tile_names_es.md`, translate it yourself reasonably and **tell the
  user explicitly in your reply that this name isn't verified against the physical box** --
  don't present it as confirmed or add it to the reference without the user confirming it.

### 3. Compute the real size of each tile

Run `scripts/tile_size.py` on the `.dds` of every tile you're going to use (look for it first
in `Sources\img\`; if it's not there, copy it with `Bash`/`cp` from
`%APPDATA%\Valkyrie\MoM\import\img\`, see `references/paths.md`):

```
python3 scripts/tile_size.py "C:\Users\V\Desktop\Programar\MoM\Sources\img\Tile_Bedroom_1_MAD20.dds"
```

This gives you the exact width/height in squares. **Save every value in `tile_sizes.json`**
inside the scenario folder (format and rationale in `references/geometry.md` section 1) --
`validate_scenario.py` needs it in step 6 to check geometry; without it, that step is
silently skipped and a misplaced token could pass as "validated" by mistake. There's no
shortcut: without this data, any position you compute is a guess.

### 4. Design the layout with the geometry formula

Read `references/geometry.md` for the full table, but in short:

- Unrotated, a tile anchored at `(X,Y)` occupies `x in [X, X+width]`, `y in [Y-height, Y]`.
- With `rotation=90/180/270`, apply the table in `references/geometry.md` to the local offset
  `(dx,dy)` before adding it to the anchor -- don't negate the angle or swap axes, the formula
  is already verified against Valkyrie's source code.
- To connect two tiles, choose the anchor of the second one so an edge of its box exactly
  matches an edge of the first (or leave a small, intentional gap if the user asks for one).
- Place the door/exploration token at the midpoint of the shared border segment.
- Place investigator and monster tokens with a small offset (0.5-1.5 squares) toward the
  interior of the tile from its anchor, never right on the edge or outside the box.

Use `scripts/validate_scenario.py` (step 6) to check geometry automatically instead of doing
it by eye.

### 5. Decide where each door goes

Don't assume two adjacent tiles already have a door painted where you're connecting them --
most base-box tiles are boxes closed on all four sides in their artwork, and where a door IS
already painted, it won't be positioned where a naive engine-grid guess would put it (see
below). Before writing the connection tokens:

1. Generate a grid-overlaid view of every tile you're going to use:
   `python3 scripts/tile_door_preview.py <path.dds>` (look for the image in `Sources/img/`,
   see step 3). **This grid is the ART grid (1 unit = 1024/3 px), not the engine placement
   grid (1 square = 1024/3.5 px, still used for `xposition`/`yposition`/tile footprint) --
   they're deliberately different, see `references/doors.md` "Two grids".** Look at the image
   (with `Read`) for every edge you want to use as a connection.
2. Classify that edge as open (the artwork already shows the gap with no wall -- typical of
   the short ends of corridors, or of a whole side on exterior/garden tiles -- just place a
   `TokenExplore`, no door token), a REAL door already painted (common -- catalogue it in
   `references/doors.json` as `{col, row, wall}` on the art grid if it isn't there yet, then
   use `python3 scripts/door_position.py <side> <anchor_x> <anchor_y> [rotation]
   --tile-sizes <scenario>/tile_sizes.json` to get the exact engine `xposition`/`yposition`
   for the `TokenExplore` -- no `TokenDoorInside` needed, and if only one side of a connection
   has a real door, you may need to shift the OTHER tile's anchor so nothing collides with its
   furniture; see `casa_ashworth`'s Study tile for a worked example), or a solid wall with no
   door (the most common case, and the default if a wall has no entry in `doors.json`).
3. If it's closed and you still want to connect through it, add a
   `TokenDoorInside`/`TokenDoorOutside` token (creates a new door painted over the wall) at
   the SAME position as the `TokenExplore` for that connection. **List the decorative token
   FIRST and the `TokenExplore` LAST in that event's `add=`, and give the decorative token
   `clickeffect=false`** -- otherwise whichever one ends up on top swallows the click meant
   for the other (root cause and fix confirmed against Valkyrie's source, see
   `references/doors.md`). If an edge is open in the artwork and you do NOT want it to be
   passable, close it with `TokenWallInside`/`TokenWallOutside` (same `clickeffect=false`
   rule applies, though it has no `TokenExplore` counterpart to conflict with). Exact format,
   rotation depending on wall orientation: `references/doors.md`.

Save any new tile you catalogue in `references/doors.json` (real doors) and
`references/doors.md` (open/closed edges) -- it avoids repeating the visual analysis in the
next scenario. Furniture/decor cataloguing (`references/landmarks.json`) is paused for now by
explicit decision -- still eyeball the image for obvious collisions, but don't block on
formally cataloguing it.

### 6. Write the scenario files

Follow `references/quest_format.md` for the exact syntax of each section (`Quest`, `Tile`,
`Token`, `Event`, `Spawn`, `QuestText`) and for event triggers (`EventStart`,
`Defeated<SpawnName>`, etc.). Points we missed the first time and that broke the play
experience:

- **When an event adds a new tile, the text MUST name it explicitly** with the pattern
  `Place the <Name> tile {MAD20} ...` (or "the module") -- otherwise the player doesn't know
  which physical piece to grab from the box. `{MAD20}` is the icon meaning "base box"; use
  `{MAD01}`, `{MAD06}`, etc. for specific expansion content if applicable (see
  `references/quest_format.md`).
- Every section with `buttons>0` needs its `<section>.text` and `<section>.buttonN` in the
  localization file -- use `validate_scenario.py` to catch missing keys. Decorative door/wall
  tokens (`TokenDoorInside` and similar, see step 5) have `buttons=0` and do NOT need text.
- Use consistent, descriptive section names (`TileRoom1`, `SpawnCultist1`,
  `EventEnterRoom2`...); it makes debugging easier and lets `validate_scenario.py` itself
  cross-reference things.

Create the scenario as an uncompressed folder inside
`C:\Users\V\Desktop\Programar\MoM\Scenarios\<name>\`.

### 7. Validate before showing it

```
python3 scripts/validate_scenario.py "C:\Users\V\Desktop\Programar\MoM\Scenarios\<name>"
```

Checks (and tell the user if something fails, don't hide it):
- Every reference (`event1=`, `add=`, `remove=`, `trigger=Defeated...`) points to a section
  that exists.
- Every text/button referenced exists in the localization file.
- Every token, spawn, and door falls inside the box of some tile (using the real size
  computed in step 3 and the rotation formula from step 4) -- if something falls outside, the
  script tells you which one and by how much, fix it before continuing.
- (Non-blocking) Whether any visible token/spawn overlaps a catalogued furniture/decor
  landmark (step 5, `references/landmarks.json`) -- a warning, not a hard failure, since
  overlap is sometimes intentional (a monster spawned under a sheet-covered chair is good
  flavor). Doors/explore tokens overlapping furniture, though, almost always look broken --
  treat those warnings as things to fix.

### 8. Deliver the result

Ask the user what they need (you can offer all three options, don't assume):
- **Packaged to play**: `python3 scripts/package_valkyrie.py <scenario-folder>` generates the
  `.valkyrie` (zip). Copy it to `%APPDATA%\Valkyrie\Download\` (normally already a connected
  folder, or reachable with direct `Bash`).
- **Editable in the app**: copy the uncompressed folder to
  `%APPDATA%\Valkyrie\MoM\Editor\<name>\` (normally with direct `Bash`, see
  `references/paths.md`) so it shows up in Valkyrie's Quest Editor and the user can tweak it
  by hand.
- **Both** is usually the most useful: that way the user can test it by playing and also
  adjust it visually if something isn't quite right.

### 9. If the user rotates or moves something by hand and shows you

When the user edits in the visual editor and asks you to continue from there, read the
updated `quest.ini` (it may be in the `Download` copy, or ask for it) and recalculate whatever
depends on that tile (tokens, doors, neighboring tiles) with the same formula from step 4 --
don't move the tile the user already placed by hand, respect their choice and adapt the rest
around it.

## Reference files

- `references/quest_format.md` -- full syntax of quest.ini/tiles.ini/tokens.ini/events.ini/
  spawns.ini, event triggers, special symbols, `.valkyrie` zip structure.
- `references/geometry.md` -- tile-size formula (with the pixels-per-square constant) and
  rotation table, with the reasoning and source (Valkyrie's code).
- `references/tile_names_es.md` -- base-box tiles and monsters with their confirmed Spanish
  name, so you don't have to guess translations.
- `references/paths.md` -- full map of Valkyrie's Windows folders and what's needed (normal
  mount vs. computer-use) to reach each one.
- `references/doors.md` -- how to tell whether a wall has a door painted on it or not, the
  ART grid vs ENGINE grid distinction (important, read this before placing any door), how to
  create a new decorative door (`TokenDoorInside`/`TokenDoorOutside`) or close an unwanted gap
  (`TokenWallInside`/`TokenWallOutside`), and an already-catalogued table of base-box tiles
  (open/closed edges -- North/South entries predating 2026-08-19 may be unreliable, see the
  caution note in that file).
- `references/doors.json` -- the authoritative catalog of REAL painted doors per tile, as
  art-grid `{col,row,wall}` cells. Convert to engine coordinates with `scripts/door_position.py`.
- `references/landmarks.md` / `references/landmarks.json` -- catalog of furniture/decor drawn
  inside each tile. Paused/unreliable as of 2026-08-19 (built before the art-grid fix) -- read
  `references/doors.md` "Two grids" before trusting it.

## Scripts

- `scripts/tile_size.py <path.dds> [more paths...]` -- exact size in squares of a tile image.
- `scripts/validate_scenario.py <scenario-folder>` -- validates cross-references, text keys,
  and geometry of a whole scenario.
- `scripts/package_valkyrie.py <scenario-folder> [output-folder]` -- zips the folder into a
  ready-to-play `.valkyrie`.
- `scripts/tile_door_preview.py <path.dds> [output.png] [--max-width N]` -- generates an
  ART-grid-overlaid image of a tile to visually inspect where its doors are painted (or
  whether an edge is already open). See `references/doors.md` "Two grids".
- `scripts/door_position.py <side> <anchor_x> <anchor_y> [rotation] [--tile-sizes path.json]`
  -- converts every catalogued door in `references/doors.json` for that tile into the actual
  engine `xposition`/`yposition`, applying rotation correctly. See `references/doors.md`.
