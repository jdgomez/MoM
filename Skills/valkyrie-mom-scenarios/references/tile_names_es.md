# Base-box tiles and monsters -- confirmed Spanish on-screen names

Confirmed by reading the real text of published base-box scenarios (not translated by me --
these are the names used by the community/FFG in the app). Use these names literally in the
pattern `Place the <Name> tile {MAD20} ...` -- don't translate or invent them. **The values in
the "Spanish name" column below are intentionally kept in Spanish**: they are the actual
on-screen/physical-box strings this project's scenarios reference (all scenarios in this
project ship with `defaultlanguage=Spanish`), not documentation prose to translate.

This list is NOT exhaustive (the base box has ~46 tiles; only the ones already used and
confirmed in this project are listed here). If you need one that isn't here:

1. Look up the internal name (`TileSideXxx`) in `content/MoM/base/tiles.ini` of the
   `NPBruce/valkyrie` repository (or the locally installed content pack, see
   `references/paths.md`) to confirm it exists and its exact name.
2. Translate the name reasonably (e.g. `Kitchen` -> "Cocina") and use it in the text.
3. **Explicitly tell the user in your reply that this Spanish name is not verified against
   the physical box** -- don't present it as confirmed, and don't add it to this table
   without the user confirming it first. Don't block delivering the scenario over this: the
   on-screen name is a table aid, not something Valkyrie validates.

## Tiles (side -> Spanish on-screen name)

| side (TileSideXxx)   | Spanish name         |
|-----------------------|-----------------------------|
| Bedroom1                | Dormitorio 1                 |
| Bedroom2                | Dormitorio 2                 |
| Study                     | Estudio                        |
| Office                     | Despacho                       |
| Hall2                       | Pasillo 2                        |
| EntryHall                     | Pasillo de entrada                |
| Lounge                          | Salon                                |
| DiningRoom                        | Comedor y Cocina                       |
| Library                             | Biblioteca                               |
| Alley1                                 | Callejon 1                                 |
| AlleyCorner1                             | Esquina de Callejon 1                        |
| AlleyCorner2                               | Esquina de callejon 2                          |
| StreetCorner3                                | Esquina de calle 3                               |

Real confirmed sizes (see `references/geometry.md` for the full formula):
Bedroom1 and Study each measure 7x3.5 squares -- do NOT assume all "small" tiles are 3.5x3.5,
always measure with `scripts/tile_size.py`.

## Base-box monsters (type -> Spanish name)

| type (MonsterXxx) | Spanish name   |
|---------------------|------------------------|
| Cultist                | Sectario                  |
| HuntingHorror            | Horrendo Cazador             |
| DeepOne                    | Profundo                        |
| StarSpawn                    | Semilla Estelar                    |

## Content-origin icons `{MADxx}`

Each icon indicates which box/pack the component named right before it in the text comes
from (useful when the player owns several mixed expansions):

| Code    | Origin                                              |
|----------|-------------------------------------------------------------|
| MAD20      | Mansions of Madness 2nd Edition base box                    |
| MAD01        | 1st edition conversion kit                                   |
| MAD06          | "Alquimia Prohibida" (Spanish product title kept as-is -- not verified against an official English title, don't guess one) |
| MAD09            | "La Llamada de lo Salvaje" (Spanish product title kept as-is -- not verified against an official English title, don't guess one) |
| MAD21-MAD27        | Other expansions (confirm which is which against the user's physical box if unsure) |
