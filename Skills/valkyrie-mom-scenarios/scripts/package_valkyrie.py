#!/usr/bin/env python3
"""Packages a Valkyrie scenario folder into a .valkyrie (zip) file.

Usage:
    python3 package_valkyrie.py <scenario-folder> [output-folder]

If no output folder is given, the .valkyrie is created next to the scenario
folder, with the same name. Excludes tile_sizes.json (internal metadata for this
skill, not something Valkyrie needs) and any hidden folder.
"""
import sys
import zipfile
from pathlib import Path

EXCLUDE_NAMES = {"tile_sizes.json", ".DS_Store"}


def package(scenario_dir, out_dir=None):
    scenario_dir = Path(scenario_dir).resolve()
    if not scenario_dir.is_dir():
        raise SystemExit(f"ERROR: {scenario_dir} is not a folder")
    if not (scenario_dir / "quest.ini").exists():
        raise SystemExit(f"ERROR: {scenario_dir} doesn't contain quest.ini")

    out_dir = Path(out_dir).resolve() if out_dir else scenario_dir.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{scenario_dir.name}.valkyrie"

    files = [p for p in scenario_dir.rglob("*") if p.is_file() and p.name not in EXCLUDE_NAMES]
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in files:
            zf.write(p, p.relative_to(scenario_dir))

    print(f"OK: {out_path} ({len(files)} files)")
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    package(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
