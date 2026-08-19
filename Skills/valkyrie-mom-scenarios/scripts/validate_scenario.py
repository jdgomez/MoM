#!/usr/bin/env python3
"""Validates a Valkyrie scenario (uncompressed folder with quest.ini and friends).

Checks:
  1. That quest.ini exists and has a [Quest] section.
  2. That every file listed in [QuestData] and [QuestText] exists.
  3. That cross-references (add=, remove=, event1=, event2=..., trigger=Defeated<X>)
     point to sections that actually exist in some .ini file in the folder.
  4. That every section with buttons>0 (and display!=false) has its <section>.text
     and <section>.buttonN in the default-language localization file.
  5. (Optional) That tokens/spawns/doors fall inside the box of some tile, using
     the sizes from tile_sizes.json (see below) and the rotation formula documented
     in references/geometry.md.
  6. (Optional, non-blocking) Whether any visible token/spawn overlaps a catalogued
     furniture/decor landmark on the tile it's sitting on -- see references/landmarks.json
     and references/landmarks.md. This is a WARNING, not an error: it doesn't affect the
     exit code, since overlapping a landmark on purpose (e.g. a monster under a
     sheet-covered chair) is often good, and the catalog is eyeballed, not pixel-exact.

tile_sizes.json (optional, at the root of the scenario folder):
    {
      "TileSideBedroom1": [7, 3.5],
      "TileSideStudy": [7, 3.5]
    }
Keys are the "side=" value used in tiles.ini, values are [width, height] in squares,
computed with tile_size.py on each tile's real .dds image. Without this file, step 5
is skipped with a warning (not an error: the other checks still run).

landmarks.json is NOT scenario-specific -- it's read automatically from
references/landmarks.json next to this skill (see references/landmarks.md for the format
and how to extend it). Pass --landmarks to point at a different file instead.

Usage:
    python3 validate_scenario.py <scenario-folder> [--tile-sizes path.json] [--landmarks path.json]
"""
import csv
import json
import re
import sys
from pathlib import Path

GLOBAL_TRIGGERS = {
    "EventStart", "EndRound", "StartRound", "NoMorale", "Eliminated",
    "Mythos", "EndInvestigatorTurn", "BeforeMonsterActivation",
}

SPECIAL_REMOVALS = {
    "#boardcomponents", "#monsters", "#shop", "#uicomponents",
    "#doors", "#tiles", "#tokens", "#qitems",
}


def parse_ini(path):
    """Tolerant parser: supports 'key=value' lines and bare lines (file lists
    under [QuestData]/[QuestText])."""
    sections = {}
    order = []
    cur = None
    with open(path, encoding="utf-8-sig") as f:
        for raw in f:
            line = raw.rstrip("\n").rstrip("\r")
            stripped = line.strip()
            if not stripped or stripped.startswith(";"):
                continue
            m = re.match(r"^\[(.+)\]$", stripped)
            if m:
                cur = m.group(1)
                sections.setdefault(cur, {})
                order.append(cur)
                continue
            if cur is None:
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                sections[cur][k.strip()] = v.strip()
            else:
                sections[cur].setdefault("_lines", []).append(stripped)
    return sections, order


def load_all_ini(folder):
    """Loads quest.ini and every file referenced in [QuestData], plus any loose
    .ini files in the folder in case some aren't listed."""
    folder = Path(folder)
    quest_ini = folder / "quest.ini"
    if not quest_ini.exists():
        raise SystemExit(f"ERROR: quest.ini not found in {folder}")

    all_sections = {}
    section_origin = {}
    files_loaded = []

    def load_file(fp):
        if not fp.exists():
            print(f"ERROR: referenced file is missing: {fp.name}")
            return
        secs, _ = parse_ini(fp)
        files_loaded.append(fp.name)
        for name, kv in secs.items():
            if name in all_sections:
                print(f"ERROR: duplicate section [{name}] in {fp.name} and {section_origin[name]}")
            all_sections[name] = kv
            section_origin[name] = fp.name

    load_file(quest_ini)

    quest_data_files = all_sections.get("QuestData", {}).get("_lines", [])
    quest_text_files = all_sections.get("QuestText", {}).get("_lines", [])

    for fname in quest_data_files:
        fp = folder / fname
        if fp.name not in files_loaded:
            load_file(fp)

    # Also load any loose .ini not explicitly referenced, so we don't depend on
    # the author having listed everything under QuestData.
    for fp in sorted(folder.glob("*.ini")):
        if fp.name not in files_loaded and fp.name != "quest.ini":
            load_file(fp)

    return all_sections, section_origin, quest_text_files


def load_localization(folder, quest_text_files):
    """Returns the set of localization keys from the FIRST file listed in
    QuestText (by convention, the default language)."""
    if not quest_text_files:
        print("WARNING: [QuestText] doesn't list any localization file.")
        return set()
    folder = Path(folder)
    default_file = folder / quest_text_files[0]
    if not default_file.exists():
        print(f"ERROR: default localization file is missing: {default_file.name}")
        return set()
    keys = set()
    with open(default_file, encoding="utf-8-sig", newline="") as f:
        for row in csv.reader(f):
            if row:
                keys.add(row[0])
    return keys


def check_references(all_sections):
    errors = []
    for name, kv in all_sections.items():
        for key, val in kv.items():
            if key in ("add", "remove"):
                for tok in val.split():
                    if tok in SPECIAL_REMOVALS:
                        continue
                    if tok not in all_sections:
                        errors.append(f"[{name}] {key}= references '{tok}' which doesn't exist")
            elif re.match(r"^event\d+$", key):
                for tok in val.split():
                    if not tok:
                        continue
                    if "/" in tok or "\\" in tok or tok.endswith(".ini"):
                        continue  # links to another external quest.ini, not validated here
                    if tok not in all_sections:
                        errors.append(f"[{name}] {key}= references '{tok}' which doesn't exist")
            elif key == "trigger":
                if val in GLOBAL_TRIGGERS or val.startswith("Var"):
                    continue
                if val.startswith("DefeatedUnique"):
                    target = val[len("DefeatedUnique"):]
                elif val.startswith("Defeated"):
                    target = val[len("Defeated"):]
                else:
                    continue
                if target not in all_sections and not target.startswith("Monster") and not target.startswith("CustomMonster"):
                    errors.append(f"[{name}] trigger={val} references '{target}' which doesn't exist")
    return errors


def check_text_keys(all_sections, loc_keys):
    if not loc_keys:
        return []
    errors = []
    for name, kv in all_sections.items():
        if kv.get("display", "true").lower() == "false":
            continue
        try:
            buttons = int(kv.get("buttons", "0") or 0)
        except ValueError:
            buttons = 0
        if buttons <= 0:
            continue
        text_key = f"{name}.text"
        if text_key not in loc_keys:
            errors.append(f"missing text key '{text_key}' in the localization file")
        for i in range(1, buttons + 1):
            btn_key = f"{name}.button{i}"
            if btn_key not in loc_keys:
                errors.append(f"missing button key '{btn_key}' in the localization file")
    return errors


ROTATIONS = {
    0: lambda dx, dy: (dx, dy),
    90: lambda dx, dy: (-dy, dx),
    180: lambda dx, dy: (-dx, -dy),
    270: lambda dx, dy: (dy, -dx),
}


def tile_box(x0, y0, width, height, rotation):
    """Axis-aligned box (xmin,xmax,ymin,ymax) of a tile with anchor (x0,y0),
    unrotated size (width,height) and rotation in {0,90,180,270}."""
    rot = ROTATIONS.get(int(rotation) % 360)
    if rot is None:
        return None
    corners_local = [(0, 0), (width, 0), (0, -height), (width, -height)]
    xs, ys = [], []
    for dx, dy in corners_local:
        rdx, rdy = rot(dx, dy)
        xs.append(x0 + rdx)
        ys.append(y0 + rdy)
    return min(xs), max(xs), min(ys), max(ys)


def check_geometry(all_sections, tile_sizes):
    if not tile_sizes:
        print("WARNING: no tile_sizes.json, skipping the geometry check.")
        return []

    tiles = {}
    for name, kv in all_sections.items():
        if "side" not in kv:
            continue
        side = kv["side"]
        if side not in tile_sizes:
            print(f"WARNING: no known size for side={side} (tile [{name}]), skipped in geometry check.")
            continue
        try:
            x0 = float(kv.get("xposition", 0))
            y0 = float(kv.get("yposition", 0))
        except ValueError:
            continue
        rotation = kv.get("rotation", 0)
        width, height = tile_sizes[side]
        box = tile_box(x0, y0, width, height, rotation)
        if box:
            tiles[name] = box

    if not tiles:
        print("WARNING: no tile has a known size, skipping the geometry check.")
        return []

    errors = []
    for name, kv in all_sections.items():
        if "xposition" not in kv or "yposition" not in kv:
            continue
        if "side" in kv:
            continue  # this is the tile itself, not something that must fall INSIDE a tile
        try:
            x = float(kv["xposition"])
            y = float(kv["yposition"])
        except ValueError:
            continue
        inside_any = False
        best_margin = None
        for tname, (xmin, xmax, ymin, ymax) in tiles.items():
            if xmin <= x <= xmax and ymin <= y <= ymax:
                inside_any = True
                break
            margin = max(xmin - x, x - xmax, ymin - y, y - ymax, 0)
            if best_margin is None or margin < best_margin[0]:
                best_margin = (margin, tname)
        if not inside_any and best_margin:
            errors.append(
                f"[{name}] at ({x},{y}) doesn't fall inside any tile "
                f"(closest is [{best_margin[1]}], off by {best_margin[0]:.2f} squares)"
            )
    return errors


def rotate_box(xmin, xmax, ymin, ymax, x0, y0, rotation):
    """Rotates an arbitrary local box (xmin,xmax,ymin,ymax, relative to a tile's own
    unrotated top-left anchor) by `rotation` and offsets it to absolute coordinates
    anchored at (x0,y0). Same rotation table as tile_box(), just applied to a
    sub-box instead of the tile's own four corners."""
    rot = ROTATIONS.get(int(rotation) % 360)
    if rot is None:
        return None
    corners_local = [(xmin, ymin), (xmax, ymin), (xmin, ymax), (xmax, ymax)]
    xs, ys = [], []
    for dx, dy in corners_local:
        rdx, rdy = rot(dx, dy)
        xs.append(x0 + rdx)
        ys.append(y0 + rdy)
    return min(xs), max(xs), min(ys), max(ys)


def check_landmarks(all_sections, landmarks_catalog):
    if not landmarks_catalog:
        return []

    # Collect every catalogued landmark, in absolute coordinates, for every placed tile
    # instance that has a matching entry (side is looked up directly by name).
    landmark_boxes = []  # (tile_section_name, landmark_name, xmin, xmax, ymin, ymax)
    for name, kv in all_sections.items():
        side = kv.get("side")
        if not side or side not in landmarks_catalog:
            continue
        try:
            x0 = float(kv.get("xposition", 0))
            y0 = float(kv.get("yposition", 0))
        except ValueError:
            continue
        rotation = kv.get("rotation", 0)
        for lm in landmarks_catalog[side]:
            xmin, xmax, ymin, ymax = lm["box"]
            box = rotate_box(xmin, xmax, ymin, ymax, x0, y0, rotation)
            if box:
                landmark_boxes.append((name, lm["name"], *box))

    if not landmark_boxes:
        return []

    warnings = []
    for name, kv in all_sections.items():
        if "xposition" not in kv or "yposition" not in kv:
            continue
        if "side" in kv:
            continue  # tiles themselves aren't placed against landmarks
        if "type" not in kv and "monster" not in kv:
            continue  # plain Event/UI sections: xposition/yposition only pans the camera,
                       # nothing is actually drawn there, so it can't visually collide
        if kv.get("display", "true").lower() == "false":
            continue  # never rendered, so it can't visually collide with anything
        try:
            x = float(kv["xposition"])
            y = float(kv["yposition"])
        except ValueError:
            continue
        for tname, lname, xmin, xmax, ymin, ymax in landmark_boxes:
            if xmin <= x <= xmax and ymin <= y <= ymax:
                kind = "monster spawn" if "monster" in kv else "token"
                warnings.append(
                    f"[{name}] ({kind}) at ({x},{y}) overlaps landmark '{lname}' "
                    f"on [{tname}] -- may render on top of drawn furniture/decor; "
                    f"check tile_door_preview.py's image before assuming it's fine "
                    f"(monsters overlapping a landmark on purpose is often good flavor, "
                    f"doors/explore tokens usually aren't)"
                )
    return warnings


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    folder = Path(args[0])

    tile_sizes_path = folder / "tile_sizes.json"
    if "--tile-sizes" in sys.argv:
        tile_sizes_path = Path(sys.argv[sys.argv.index("--tile-sizes") + 1])
    tile_sizes = {}
    if tile_sizes_path.exists():
        with open(tile_sizes_path, encoding="utf-8") as f:
            tile_sizes = json.load(f)

    # Global landmark catalog lives with the skill itself (shared across all scenarios,
    # same convention as doors.md), not inside the scenario folder.
    landmarks_path = Path(__file__).resolve().parent.parent / "references" / "landmarks.json"
    if "--landmarks" in sys.argv:
        landmarks_path = Path(sys.argv[sys.argv.index("--landmarks") + 1])
    landmarks_catalog = {}
    if landmarks_path.exists():
        with open(landmarks_path, encoding="utf-8") as f:
            landmarks_catalog = {k: v for k, v in json.load(f).items() if not k.startswith("_")}

    all_sections, origin, quest_text_files = load_all_ini(folder)
    loc_keys = load_localization(folder, quest_text_files)

    ref_errors = check_references(all_sections)
    text_errors = check_text_keys(all_sections, loc_keys)
    geo_errors = check_geometry(all_sections, tile_sizes)
    landmark_warnings = check_landmarks(all_sections, landmarks_catalog)

    total = len(ref_errors) + len(text_errors) + len(geo_errors)

    print(f"\n{len(all_sections)} sections loaded from {folder}")
    if ref_errors:
        print(f"\n-- Broken references ({len(ref_errors)}) --")
        for e in ref_errors:
            print(" ", e)
    if text_errors:
        print(f"\n-- Missing localization text ({len(text_errors)}) --")
        for e in text_errors:
            print(" ", e)
    if geo_errors:
        print(f"\n-- Geometry outside the tile ({len(geo_errors)}) --")
        for e in geo_errors:
            print(" ", e)
    if landmark_warnings:
        print(f"\n-- Landmark overlap warnings ({len(landmark_warnings)}, non-blocking) --")
        for w in landmark_warnings:
            print(" ", w)

    if total == 0:
        print("\nOK: no problems found.")
        sys.exit(0)
    else:
        print(f"\nTOTAL: {total} problem(s) found.")
        sys.exit(1)


if __name__ == "__main__":
    main()
