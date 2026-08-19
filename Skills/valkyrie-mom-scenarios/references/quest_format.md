# Valkyrie scenario format (quest.ini and friends)

A scenario is a folder with `quest.ini` plus other `.ini` files and a localization `.txt`.
Packaged, it is exactly that folder zipped with the `.valkyrie` extension
(`scripts/package_valkyrie.py` does this). All text visible to the player lives in the
localization file(s), not in the structural `.ini` files.

## Minimal quest.ini

```ini
[Quest]
format=21
hidden=False
type=MoM
defaultlanguage=Spanish
defaultmusicon=True
minhero=1
maxhero=4
difficulty=0.5
lengthmin=60
lengthmax=120
version=<any long hex string works as a unique hash, e.g. generated with
  python3 -c "import secrets; print('-'.join(f'{b:02X}' for b in secrets.token_bytes(32)))">

[QuestText]
Localization.Spanish.txt

[QuestData]
tiles.ini
tokens.ini
events.ini
spawns.ini
```

- `packs=` (optional): space-separated list of required expansion IDs. If omitted, the
  scenario only requires the base box. Do NOT use `RN` or `SM` for MoM 1st edition -- use
  `MoM1E`/`CotW`/`FA` (see the `QuestIniQuest` wiki page).
- `minhero`/`maxhero`: default to 2 and 5 if omitted.
- The file names in `[QuestText]`/`[QuestData]` are literal, relative to the scenario folder.

## Content sections

Every section lives in whichever of the `.ini` files is listed in `[QuestData]` (it doesn't
matter which one, but grouping by type is convenient: `tiles.ini`, `tokens.ini`,
`events.ini`, `spawns.ini`). Section names must be unique across the ENTIRE scenario.

### `[Tile<name>]`
```ini
[TileRoom1]
xposition=0
yposition=0
side=TileSideBedroom1
rotation=90    ; optional, defaults to 0
```
`side` must be a valid `TileSideXxx` from the allowed content pack (base box or an expansion
listed in `packs=`). See `references/tile_names_es.md` for the already-confirmed base-box
ones, or the `NPBruce/valkyrie` repo for the rest. Full geometry in
`references/geometry.md`.

### `[Token<name>]`
```ini
[TokenDoorRoom2]
xposition=6.813
yposition=-1.706
buttons=1
event1=EventEnterRoom2
type=TokenExplore   ; defaults to TokenSearch if omitted
```
Common types: `TokenExplore` (exploration token), `TokenSearch`, `TokenInteract`,
`TokenInvestigators` (starting-position marker, usually with `display=false`),
`TokenDoorInside`/`TokenWallInside` (decorative interior wall/door).

`clickeffect=false` (optional, defaults to `true`) disables the token's click handler
entirely -- it does NOT default to `false` just because `buttons=0`. Always set it explicitly
on purely decorative tokens (`TokenDoorInside`/`TokenWallInside` and friends) that share a
position with a real interactive token, otherwise whichever one was added last in `add=`
silently steals every click at that position. See `references/doors.md` for the full,
source-verified explanation.

### `[Event<name>]`
```ini
[EventExample]
xposition=0          ; optional: moves the camera here when the event fires
yposition=0
buttons=1
event1=OtherEvent     ; what happens when button 1 is pressed (can be empty = nothing else)
add=TileX TokenY       ; components that appear on the board
remove=TokenZ            ; components that disappear
trigger=EventStart       ; optional, see the trigger table below
operations=Var,=,1        ; optional, modifies state variables
vartests=Var,==,1          ; optional, condition for the event to fire
audio=AudioName
music=Track1 Track2
```
The text (`<name>.text`, `<name>.button1`, `<name>.button2`...) lives in the localization
file, never here.

### `[Spawn<name>]`
Same as an Event, but it also places a monster on the board:
```ini
[SpawnCultist1]
xposition=1.5
yposition=-1.5
buttons=1
event1=               ; what happens after the appearance dialog (usually empty)
monster=MonsterCultist
uniquehealthhero=1     ; optional, extra health per hero
```
`monster` must be a valid `MonsterXxx` for the allowed content (base box or expansions in
`packs=`). Combat itself is NOT scripted -- once the monster appears on the board, the MoM
engine itself handles attacks; the scenario only reacts when the monster is defeated (see
triggers).

## Event triggers (`trigger=`)

- `EventStart` -- when the game starts. Use it for the first event in the chain.
- `Defeated<SpawnName>` -- when that specific Spawn section's monster is defeated. The name
  is literally the section name, e.g. `trigger=DefeatedSpawnCultist1` for `[SpawnCultist1]`.
- `DefeatedUnique<...>` -- same but also counts defeating just the "unique" of the group.
- `EndRound` / `StartRound` -- at the end/start of each round.
- `NoMorale` -- the group's morale drops below 0.
- `Eliminated` -- an investigator is eliminated.
- `Mythos` / `EndInvestigatorTurn` / `BeforeMonsterActivation` -- round phases.
- `Var<name>` -- fires when another event sets the `@name` variable to 1 (rare, avoid if
  there's a more direct alternative).

## Localization (`Localization.<Language>.txt`)

CSV format (comma-separated, values with commas or line breaks go in quotes):
```csv
.,Spanish
quest.name,Scenario name
quest.description,"Description. Can have \n escaped line breaks."
EventExample.text,"Text the player sees. {MAD20} inserts a base-box icon."
EventExample.button1,Continue
```
- The first line is always `.,<Language>`.
- `quest.name` and `quest.description` are mandatory.
- Every section with `buttons>0` (and without `display=false`) needs its `<section>.text`
  and one `<section>.buttonN` per button -- `scripts/validate_scenario.py` checks this.
- Useful symbols in the text: `{action}`, `{observation}`, `{will}`, `{strength}`,
  `{agility}`, `{lore}`, `{influence}`, `{clue}`, `{success}`, and the content-origin icons
  `{MAD01}`, `{MAD06}`, `{MAD09}`, `{MAD20}`-`{MAD27}` (MAD20 = base box).
  **Whenever an event places a new tile, name the tile explicitly in the text** with the
  pattern `Place the <Name> tile {MAD20} ...` (or "the module") -- otherwise the player
  doesn't know which physical piece to grab from the box. Confirmed Spanish on-screen names
  are in `references/tile_names_es.md` -- this project's scenarios ship in Spanish
  (`defaultlanguage=Spanish`), so the text the player actually reads stays in Spanish even
  though this reference documentation is in English.
- `{rnd:hero}`, `{var:<Var>}`, `{c:<SelectedComponent>}` insert dynamic values.

## Structure of the `.valkyrie` file

It's a normal zip with the `.valkyrie` extension, with the scenario's own `.ini`/`.txt`/images
at the root (no intermediate subfolders). `scripts/package_valkyrie.py` generates it from the
scenario folder.
