# Map of Valkyrie folders on Windows (Juan's machine)

**Updated 2026-08-19: all of these paths turned out to be directly accessible from `Bash`**
(`ls`/`cp`/`rm`/etc.), no computer-use needed. An earlier version of this document said
`MoM\Editor` and `MoM\import` could only be touched via screen control -- retested with a
real scenario (`prueba_herramientas`) and it wasn't necessary: `Bash` reaches absolute paths
outside the connected working directory without issue. The computer-use section further down
is kept as a plan B in case another machine/session turns out to be restricted.

| Folder                                                    | Contains                                                     | How to access it |
|--------------------------------------------------------------|----------------------------------------------------------------------|-------------------|
| `C:\Users\V\Desktop\Programar\MoM`                              | Working project (git repo). `Scenarios\` = scenarios in progress, `Sources\img\` = local copy of `.dds` images | Normal connected folder (Read/Write/Edit/bash direct) |
| `C:\Users\V\AppData\Roaming\Valkyrie\Download`                    | Packaged `.valkyrie` scenarios, ready to play                  | Direct Bash (`cp`/`rm`) |
| `%APPDATA%\Valkyrie\MoM\Editor\<name>\`                            | Uncompressed scenario that the app's Quest Editor detects and lists    | Direct Bash (`cp -r`/`rm -rf`) |
| `%APPDATA%\Valkyrie\MoM\import\img\`                                    | Original `.dds` images imported by Valkyrie from the official FFG app (every expansion the user owns) | Direct Bash (`ls`/`cp`) |
| `%APPDATA%\Valkyrie\MoM\import\text\`, `\audio\`, `\fonts\`                | Other imported assets (official text, audio, fonts)                  | Direct Bash |
| `C:\Program Files (x86)\Valkyrie\valkyrie_Data\StreamingAssets\content\MoM\<pack>\` | REAL content packs installed with the app (`tiles.ini`, `monsters.ini`, `tokens.ini`... for `base` and every expansion Juan has installed) | Normal connected folder (Read/Grep direct) |

`%APPDATA%` on this machine is `C:\Users\V\AppData\Roaming`. If `Bash` ever errors out with a
permission issue on one of these paths, then fall back to the computer-use plan B described
in the "Copying something into a folder that isn't connected" section below.

## Verifying internal names (`TileSideXxx`, `MonsterXxx`) without cloning GitHub

Valkyrie itself, once installed, ships with the real content packs at
`C:\Program Files (x86)\Valkyrie\valkyrie_Data\StreamingAssets\content\MoM\`. The base box is
at `base\tiles.ini` / `base\monsters.ini`. Use `Grep` there directly to confirm a
`side=`/`monster=` before using it -- it's faster and more reliable than cloning
`NPBruce/valkyrie` from GitHub (which may also be out of date relative to the installed
version). Only fall back to the GitHub repo if this folder doesn't exist on the machine.

## Why the visual editor doesn't see a scenario in Download

Valkyrie's code (`QuestLoader.cs`, method `GetUserUnpackedQuests`) only lists as "editable"
what it finds uncompressed inside `%APPDATA%\Valkyrie\MoM\Editor\`. The `Download` folder is
used to PLAY already-packaged scenarios (`.valkyrie` = zip), not to edit them visually. If
you want the user to be able to tweak something by hand in the app, the uncompressed folder
needs to live in `Editor\`, not `Download\`.

## Copying something into a folder that isn't connected (plan B, computer-use)

If `Bash` ever can't reach `MoM\Editor` or `MoM\import` directly (see the note at the top --
this hasn't happened so far, but keep this as a fallback), these folders are not normal
working folders -- they can only be reached via screen control:

1. `request_access` for "File Explorer" (or whatever exact name appears in the list of
   installed apps).
2. Open File Explorer, navigate by clicking or via the address bar -- **careful**: the `type`
   tool for typing a path uses the clipboard internally, so if you type a path AFTER having
   copied files (Ctrl+C), you lose what was copied with no warning. To avoid this, navigate
   through the address bar's dropdown history (the little arrow on the right) or by
   double-clicking folders, never by typing, between a Ctrl+C and its matching Ctrl+V.
3. Select the source file/folder, Ctrl+C, navigate to the destination (without typing paths
   along the way), Ctrl+V. If a file with the same name already exists, a "Replace or skip
   files" dialog appears -- choose "Replace the files in the destination".
4. Verify with a screenshot that the content/modified date changed; if Ctrl+V doesn't show any
   conflict dialog and the dates don't change, the clipboard was probably lost for the reason
   in point 2 -- repeat the copy.

## Tile images: from import\img to Sources\img

`Sources\img\` (inside the connected project) is a working copy meant so you can read images
directly with `Read`/`bash` without depending on computer-use every time. If you need a tile
that isn't there:

1. Copy the whole `%APPDATA%\Valkyrie\MoM\import\img\` folder to `Sources\img\` the first time
   (a few hundred MB, but this way you cover every expansion at once and don't need to repeat
   this), or copy just the specific `.dds` files you need.
2. From there, `scripts/tile_size.py` and any image reading work without computer-use.
